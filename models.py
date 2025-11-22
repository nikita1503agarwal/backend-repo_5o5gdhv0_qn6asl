from dataclasses import dataclass
from typing import Optional


@dataclass
class Song:
    """
    Represents a single track in the library.

    Fields mirror project spec; file_path should be a URL/path the frontend can play.
    """
    song_id: int
    title: str
    artist: str
    album: str
    genre: str
    year: int
    duration_seconds: int
    file_path: str
    play_count: int = 0
    is_favorite: bool = False


class Playlist:
    """
    Playlist backed by a Doubly Linked List of songs to support O(1) next/prev once a node is known.
    Typical operations:
      - append: O(1)
      - remove by song_id: O(n)
      - traverse: O(n)
    """
    class DLLNode:
        def __init__(self, song: Song):
            self.song = song
            self.prev: Optional['Playlist.DLLNode'] = None
            self.next: Optional['Playlist.DLLNode'] = None

    def __init__(self, name: str):
        self.name = name
        self.head: Optional[Playlist.DLLNode] = None
        self.tail: Optional[Playlist.DLLNode] = None
        self._length = 0

    def append(self, song: Song) -> None:
        node = Playlist.DLLNode(song)
        if not self.head:
            self.head = self.tail = node
        else:
            assert self.tail is not None
            self.tail.next = node
            node.prev = self.tail
            self.tail = node
        self._length += 1

    def remove(self, song_id: int) -> bool:
        cur = self.head
        while cur:
            if cur.song.song_id == song_id:
                if cur.prev:
                    cur.prev.next = cur.next
                else:
                    self.head = cur.next
                if cur.next:
                    cur.next.prev = cur.prev
                else:
                    self.tail = cur.prev
                self._length -= 1
                return True
            cur = cur.next
        return False

    def find_node(self, song_id: int) -> Optional['Playlist.DLLNode']:
        cur = self.head
        while cur:
            if cur.song.song_id == song_id:
                return cur
            cur = cur.next
        return None

    def to_list(self) -> list[Song]:
        out = []
        cur = self.head
        while cur:
            out.append(cur.song)
            cur = cur.next
        return out

    def __len__(self) -> int:
        return self._length


class UserSessionState:
    """Holds ephemeral playback-related state for a user/session."""
    def __init__(self):
        self.current_song_id: Optional[int] = None
        self.current_playlist_name: Optional[str] = None
        # these are names/ids; the actual queue/history are managed by MusicLibraryManager
