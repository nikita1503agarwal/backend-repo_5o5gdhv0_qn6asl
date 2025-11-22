from __future__ import annotations
import os
import random
import re
from typing import Dict, List, Optional
from dataclasses import asdict

from models import Song, Playlist
from data_structures import (
    SinglyLinkedList,
    MultiLinkedListByGenre,
    BST,
    Stack,
    Queue,
    SongGraph,
)


class MusicLibraryManager:
    """
    Orchestrates ingestion and operations across all custom data structures.

    Responsibilities:
      - Scan static/music for audio files and build Song objects
      - Maintain SLL library, Genre multi list, BST (title), Stack (history), Queue (up next), Graph (similarity)
      - Provide high-level APIs used by Flask routes
    """

    def __init__(self, music_dir: str = "static/music") -> None:
        self.music_dir = music_dir
        self.sll = SinglyLinkedList()
        self.genre_mll = MultiLinkedListByGenre()
        self.title_bst = BST()
        self.history = Stack()
        self.up_next = Queue()
        self.graph = SongGraph()
        self.playlists: Dict[str, Playlist] = {}
        self._song_index: Dict[int, Song] = {}
        self._next_song_id = 1
        self.scan_and_build()

    # --------- helpers ---------
    @staticmethod
    def _infer_metadata_from_filename(filename: str) -> Dict:
        name = os.path.splitext(os.path.basename(filename))[0]
        # Try patterns like "Artist - Title" or "Title"
        if " - " in name:
            artist, title = name.split(" - ", 1)
        else:
            artist, title = "Unknown Artist", name
        genre = "Unknown"
        year = 0
        return {
            "title": title,
            "artist": artist,
            "album": "",
            "genre": genre,
            "year": year,
        }

    def _add_song(self, song: Song) -> None:
        self.sll.insert_end(song)
        self.genre_mll.add_song(song)
        self.title_bst.insert(song.title, song)
        self.graph.add_vertex(song.song_id)
        self._song_index[song.song_id] = song

    def _rebuild_graph(self) -> None:
        # Build similarity edges: same artist (strong), same genre, close year
        ids = list(self._song_index.keys())
        for i in range(len(ids)):
            a = self._song_index[ids[i]]
            for j in range(i + 1, len(ids)):
                b = self._song_index[ids[j]]
                score = 0
                if a.artist and b.artist and a.artist.lower() == b.artist.lower():
                    score += 2
                if a.genre and b.genre and a.genre.lower() == b.genre.lower():
                    score += 1
                if a.year and b.year and abs(a.year - b.year) <= 2:
                    score += 1
                if score >= 1:
                    self.graph.add_edge(a.song_id, b.song_id)

    # --------- build ---------
    def scan_and_build(self) -> None:
        self.sll = SinglyLinkedList()
        self.genre_mll = MultiLinkedListByGenre()
        self.title_bst = BST()
        self.graph = SongGraph()
        self._song_index.clear()
        self._next_song_id = 1

        if not os.path.isdir(self.music_dir):
            os.makedirs(self.music_dir, exist_ok=True)
        for fname in os.listdir(self.music_dir):
            if not fname.lower().endswith((".mp3", ".wav")):
                continue
            meta = self._infer_metadata_from_filename(fname)
            song = Song(
                song_id=self._next_song_id,
                title=meta["title"],
                artist=meta["artist"],
                album=meta["album"],
                genre=meta["genre"],
                year=meta["year"],
                duration_seconds=0,
                file_path=os.path.join(self.music_dir, fname).replace("\\", "/"),
                play_count=0,
                is_favorite=False,
            )
            self._add_song(song)
            self._next_song_id += 1
        self._rebuild_graph()

    # --------- library APIs ---------
    def get_all_songs(self) -> List[Song]:
        return list(self.sll.traverse())

    def get_song_by_id(self, song_id: int) -> Optional[Song]:
        return self._song_index.get(song_id)

    def update_song(self, song_id: int, **fields) -> bool:
        s = self._song_index.get(song_id)
        if not s:
            return False
        old_title = s.title
        old_genre = s.genre
        for k, v in fields.items():
            if hasattr(s, k):
                setattr(s, k, v)
        # Rebuild affected structures:
        if s.title != old_title:
            self.title_bst = BST()
            for song in self.get_all_songs():
                self.title_bst.insert(song.title, song)
        if s.genre != old_genre:
            # rebuild genre lists simply
            self.genre_mll = MultiLinkedListByGenre()
            for song in self.get_all_songs():
                self.genre_mll.add_song(song)
        self._rebuild_graph()
        return True

    def delete_song(self, song_id: int) -> bool:
        if song_id not in self._song_index:
            return False
        # Remove from SLL
        self.sll.delete_by_song_id(song_id)
        # Remove from genre structure
        self.genre_mll.remove_song(song_id)
        # Remove from playlists
        for pl in self.playlists.values():
            pl.remove(song_id)
        # Remove from queue
        self.up_next._data = [s for s in self.up_next.to_list() if getattr(s, 'song_id', None) != song_id]
        self.up_next._head_idx = 0
        # Remove from history
        self.history._items = [s for s in self.history._items if getattr(s, 'song_id', None) != song_id]
        # Remove from BST by rebuilding
        del self._song_index[song_id]
        self.title_bst = BST()
        for song in self.get_all_songs():
            self.title_bst.insert(song.title, song)
        # Remove from graph by rebuilding
        self.graph = SongGraph()
        for song in self.get_all_songs():
            self.graph.add_vertex(song.song_id)
        self._rebuild_graph()
        return True

    # --------- genres ---------
    def get_all_genres(self) -> List[str]:
        return self.genre_mll.get_all_genres()

    def get_songs_by_genre(self, genre: str) -> List[Song]:
        return self.genre_mll.get_songs_by_genre(genre)

    # --------- search ---------
    def search_by_title(self, query: str) -> List[Song]:
        exact = self.title_bst.search(query)
        if exact:
            return [exact]
        return self.title_bst.search_partial(query)

    # --------- playlists ---------
    def create_playlist(self, name: str) -> bool:
        if name in self.playlists:
            return False
        self.playlists[name] = Playlist(name)
        return True

    def delete_playlist(self, name: str) -> bool:
        return self.playlists.pop(name, None) is not None

    def add_song_to_playlist(self, name: str, song_id: int) -> bool:
        pl = self.playlists.get(name)
        s = self._song_index.get(song_id)
        if not pl or not s:
            return False
        pl.append(s)
        return True

    def remove_song_from_playlist(self, name: str, song_id: int) -> bool:
        pl = self.playlists.get(name)
        if not pl:
            return False
        return pl.remove(song_id)

    def get_playlist_songs(self, name: str) -> List[Song]:
        pl = self.playlists.get(name)
        return pl.to_list() if pl else []

    # --------- queue ---------
    def enqueue_song(self, song_id: int) -> bool:
        s = self._song_index.get(song_id)
        if not s:
            return False
        self.up_next.enqueue(s)
        return True

    def dequeue_song(self) -> Optional[Song]:
        return self.up_next.dequeue()

    def get_queue_list(self) -> List[Song]:
        return self.up_next.to_list()

    # --------- history ---------
    def record_play(self, song: Song) -> None:
        self.history.push(song)
        song.play_count += 1

    def get_history_list(self, limit: int = 20) -> List[Song]:
        return self.history.to_list()[:limit]

    # --------- graph ---------
    def get_similar_songs(self, song_id: int) -> List[int]:
        return self.graph.neighbors(song_id)

    def get_next_similar_song(self, song_id: int) -> Optional[Song]:
        neighbors = self.get_similar_songs(song_id)
        random.shuffle(neighbors)
        for nid in neighbors:
            s = self._song_index.get(nid)
            if s:
                return s
        # fallback random
        songs = self.get_all_songs()
        if not songs:
            return None
        return random.choice(songs)

    # --------- playback helpers ---------
    def get_next_song(self, current_song_id: Optional[int], current_playlist_name: Optional[str]) -> Optional[Song]:
        # playlist context
        if current_playlist_name and current_song_id:
            pl = self.playlists.get(current_playlist_name)
            if pl:
                node = pl.find_node(current_song_id)
                if node and node.next:
                    return node.next.song
        # queue
        q = self.dequeue_song()
        if q:
            return q
        # similarity
        if current_song_id:
            sim = self.get_next_similar_song(current_song_id)
            if sim:
                return sim
        # fallback
        songs = self.get_all_songs()
        return random.choice(songs) if songs else None

    def get_previous_song(self, current_song_id: Optional[int], current_playlist_name: Optional[str]) -> Optional[Song]:
        if current_playlist_name and current_song_id:
            pl = self.playlists.get(current_playlist_name)
            if pl:
                node = pl.find_node(current_song_id)
                if node and node.prev:
                    return node.prev.song
        # history (pop current then previous)
        if not self.history.is_empty():
            cur = self.history.pop()
            prev = self.history.peek()
            if prev:
                return prev
        return None

    # --------- serialization helpers ---------
    @staticmethod
    def song_to_dict(song: Song) -> Dict:
        d = asdict(song)
        d["audio_url"] = "/" + song.file_path if not song.file_path.startswith("/") else song.file_path
        return d
