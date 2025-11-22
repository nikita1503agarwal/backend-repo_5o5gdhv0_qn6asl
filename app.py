from __future__ import annotations
import os
from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from music_manager import MusicLibraryManager

app = Flask(__name__)
app.secret_key = os.environ.get("SONICWAVE_SECRET", "dev-secret-change-me")

manager = MusicLibraryManager(music_dir="static/music")


# ---------------- Pages ----------------
@app.route("/")
def index():
    initial = {
        "songs": [manager.song_to_dict(s) for s in manager.get_all_songs()],
        "genres": manager.get_all_genres(),
        "history": [manager.song_to_dict(s) for s in manager.get_history_list(20)],
        "queue": [manager.song_to_dict(s) for s in manager.get_queue_list()],
        "admin": bool(session.get("admin")),
    }
    return render_template("index.html", initial=initial)


@app.route("/admin")
def admin_page():
    if not session.get("admin"):
        return render_template("admin.html", logged_in=False, songs=[], message=None)
    return render_template(
        "admin.html",
        logged_in=True,
        songs=[manager.song_to_dict(s) for s in manager.get_all_songs()],
        message=None,
    )


# ---------------- Auth (simple) ----------------
@app.route("/admin/login", methods=["POST"])
def admin_login():
    password = request.form.get("password", "")
    if password == os.environ.get("SONICWAVE_ADMIN_PASSWORD", "sonicwave"):  # hardcoded default
        session["admin"] = True
        return redirect(url_for("admin_page"))
    return render_template("admin.html", logged_in=False, songs=[], message="Invalid password")


# ---------------- Admin actions ----------------
@app.route("/admin/songs/<int:song_id>/edit", methods=["POST"])
def admin_edit_song(song_id: int):
    if not session.get("admin"):
        return redirect(url_for("admin_page"))
    fields = {k: v for k, v in request.form.items() if k in {"title", "artist", "album", "genre", "year"}}
    if "year" in fields:
        try:
            fields["year"] = int(fields["year"]) if fields["year"] else 0
        except Exception:
            fields["year"] = 0
    manager.update_song(song_id, **fields)
    return redirect(url_for("admin_page"))


@app.route("/admin/songs/<int:song_id>/delete", methods=["POST"])
def admin_delete_song(song_id: int):
    if not session.get("admin"):
        return redirect(url_for("admin_page"))
    manager.delete_song(song_id)
    return redirect(url_for("admin_page"))


@app.route("/admin/rescan", methods=["POST"])
def admin_rescan():
    if not session.get("admin"):
        return redirect(url_for("admin_page"))
    manager.scan_and_build()
    return redirect(url_for("admin_page"))


# ---------------- API: Library ----------------
@app.route("/api/songs")
def api_songs():
    return jsonify([manager.song_to_dict(s) for s in manager.get_all_songs()])


@app.route("/api/songs/<int:song_id>")
def api_song(song_id: int):
    s = manager.get_song_by_id(song_id)
    if not s:
        return jsonify({"error": "Not found"}), 404
    return jsonify(manager.song_to_dict(s))


@app.route("/api/search")
def api_search():
    q = request.args.get("query", "").strip()
    if not q:
        return jsonify([])
    return jsonify([manager.song_to_dict(s) for s in manager.search_by_title(q)])


@app.route("/api/genres")
def api_genres():
    return jsonify(manager.get_all_genres())


@app.route("/api/genres/<genre>")
def api_genre_songs(genre: str):
    return jsonify([manager.song_to_dict(s) for s in manager.get_songs_by_genre(genre)])


@app.route("/api/history")
def api_history():
    return jsonify([manager.song_to_dict(s) for s in manager.get_history_list(50)])


@app.route("/api/queue")
def api_queue():
    return jsonify([manager.song_to_dict(s) for s in manager.get_queue_list()])


@app.route("/api/recommendations/<int:song_id>")
def api_recommendations(song_id: int):
    return jsonify(manager.get_similar_songs(song_id))


# ---------------- API: Favorites & Queue ----------------
@app.route("/api/songs/<int:song_id>/favorite", methods=["POST"])
def api_favorite(song_id: int):
    s = manager.get_song_by_id(song_id)
    if not s:
        return jsonify({"ok": False}), 404
    fav = request.json.get("is_favorite") if request.is_json else request.form.get("is_favorite")
    is_fav = str(fav).lower() in {"1", "true", "yes", "on"}
    manager.update_song(song_id, is_favorite=is_fav)
    return jsonify({"ok": True, "song": manager.song_to_dict(manager.get_song_by_id(song_id))})


@app.route("/api/queue/add/<int:song_id>", methods=["POST"])
def api_queue_add(song_id: int):
    ok = manager.enqueue_song(song_id)
    return jsonify({"ok": ok, "queue": [manager.song_to_dict(s) for s in manager.get_queue_list()]})


# ---------------- API: Playback ----------------
@app.route("/api/play/<int:song_id>", methods=["POST"])
def api_play(song_id: int):
    s = manager.get_song_by_id(song_id)
    if not s:
        return jsonify({"error": "Not found"}), 404
    manager.record_play(s)
    session["current_song_id"] = song_id
    session.setdefault("current_playlist_name", None)
    return jsonify({"ok": True, "song": manager.song_to_dict(s)})


@app.route("/api/next", methods=["POST"])
def api_next():
    cur_id = session.get("current_song_id")
    pl_name = session.get("current_playlist_name")
    s = manager.get_next_song(cur_id, pl_name)
    if not s:
        return jsonify({"ok": False})
    manager.record_play(s)
    session["current_song_id"] = s.song_id
    return jsonify({"ok": True, "song": manager.song_to_dict(s)})


@app.route("/api/prev", methods=["POST"])
def api_prev():
    cur_id = session.get("current_song_id")
    pl_name = session.get("current_playlist_name")
    s = manager.get_previous_song(cur_id, pl_name)
    if not s:
        return jsonify({"ok": False})
    session["current_song_id"] = s.song_id
    return jsonify({"ok": True, "song": manager.song_to_dict(s)})


# -------------- Run --------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
