"""
Custom node-based data structures used throughout SonicWave.
Each structure includes basic operations with typical time complexity notes.
"""
from __future__ import annotations
from typing import Optional, Any, Callable, Iterable, List, Dict
from dataclasses import dataclass

# -----------------------------
# Singly Linked List (SLL)
# -----------------------------

class SLLNode:
    def __init__(self, song: Any):
        self.song = song
        self.next: Optional[SLLNode] = None

class SinglyLinkedList:
    """Singly Linked List storing the master library.
    - insert_end: O(n) without tail pointer
    - delete_by_id: O(n)
    - traverse: O(n)
    - length: O(n)
    """
    def __init__(self):
        self.head: Optional[SLLNode] = None
        self.tail: Optional[SLLNode] = None
        self._length = 0

    def insert_end(self, song: Any) -> None:
        node = SLLNode(song)
        if not self.head:
            self.head = self.tail = node
        else:
            assert self.tail is not None
            self.tail.next = node
            self.tail = node
        self._length += 1

    def delete_by_song_id(self, song_id: int) -> bool:
        prev: Optional[SLLNode] = None
        cur = self.head
        while cur:
            if getattr(cur.song, 'song_id', None) == song_id:
                if prev:
                    prev.next = cur.next
                else:
                    self.head = cur.next
                if cur is self.tail:
                    self.tail = prev
                self._length -= 1
                return True
            prev = cur
            cur = cur.next
        return False

    def traverse(self) -> Iterable[Any]:
        cur = self.head
        while cur:
            yield cur.song
            cur = cur.next

    def __len__(self) -> int:
        return self._length


# -----------------------------
# Doubly Linked List (DLL)
# Used inside Playlist class in models.py; included here for completeness if needed.
# -----------------------------

class DLLNode:
    def __init__(self, song: Any):
        self.song = song
        self.prev: Optional[DLLNode] = None
        self.next: Optional[DLLNode] = None


# -----------------------------
# Stack (History)
# -----------------------------

class Stack:
    """LIFO Stack for listening history.
    - push: O(1)
    - pop: O(1)
    - peek: O(1)
    - to_list: O(n)
    """
    def __init__(self):
        self._items: List[Any] = []

    def push(self, item: Any) -> None:
        self._items.append(item)

    def pop(self) -> Optional[Any]:
        return self._items.pop() if self._items else None

    def peek(self) -> Optional[Any]:
        return self._items[-1] if self._items else None

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def to_list(self) -> List[Any]:
        return list(reversed(self._items))


# -----------------------------
# Queue (Up Next)
# -----------------------------

class Queue:
    """FIFO Queue for Up Next.
    - enqueue: O(1)
    - dequeue: O(1)
    - peek: O(1)
    - to_list: O(n)
    """
    def __init__(self):
        self._data: List[Any] = []
        self._head_idx = 0

    def enqueue(self, item: Any) -> None:
        self._data.append(item)

    def dequeue(self) -> Optional[Any]:
        if self._head_idx >= len(self._data):
            return None
        item = self._data[self._head_idx]
        self._head_idx += 1
        # Periodically compact list
        if self._head_idx > 32 and self._head_idx * 2 > len(self._data):
            self._data = self._data[self._head_idx:]
            self._head_idx = 0
        return item

    def peek(self) -> Optional[Any]:
        if self._head_idx >= len(self._data):
            return None
        return self._data[self._head_idx]

    def is_empty(self) -> bool:
        return self._head_idx >= len(self._data)

    def to_list(self) -> List[Any]:
        return self._data[self._head_idx:]


# -----------------------------
# Multi Linked List by Genre
# -----------------------------

class GenreSongNode:
    def __init__(self, song: Any):
        self.song = song
        self.next_song_in_genre: Optional[GenreSongNode] = None

class GenreHeader:
    def __init__(self, genre: str):
        self.genre = genre
        self.first_song: Optional[GenreSongNode] = None
        self.next_header: Optional[GenreHeader] = None

class MultiLinkedListByGenre:
    """Keeps songs grouped by genre using a linked list of genre headers,
    each pointing to a linked list of songs in that genre.
    Ops:
      - add_song: O(g + s) where g is genres count to find/insert header, s to append
      - get_songs_by_genre: O(s)
      - get_all_genres: O(g)
    """
    def __init__(self):
        self.head: Optional[GenreHeader] = None

    def _find_or_create_header(self, genre: str) -> GenreHeader:
        if not self.head:
            self.head = GenreHeader(genre)
            return self.head
        # search
        cur = self.head
        prev = None
        while cur:
            if cur.genre.lower() == genre.lower():
                return cur
            prev = cur
            cur = cur.next_header
        # not found, append new header
        new_header = GenreHeader(genre)
        assert prev is not None
        prev.next_header = new_header
        return new_header

    def add_song(self, song: Any) -> None:
        header = self._find_or_create_header(getattr(song, 'genre', 'Unknown'))
        node = GenreSongNode(song)
        if not header.first_song:
            header.first_song = node
        else:
            cur = header.first_song
            while cur.next_song_in_genre:
                cur = cur.next_song_in_genre
            cur.next_song_in_genre = node

    def remove_song(self, song_id: int) -> None:
        prev_header = None
        header = self.head
        while header:
            prev_song = None
            song_node = header.first_song
            while song_node:
                if getattr(song_node.song, 'song_id', None) == song_id:
                    # delete song node
                    if prev_song:
                        prev_song.next_song_in_genre = song_node.next_song_in_genre
                    else:
                        header.first_song = song_node.next_song_in_genre
                    break
                prev_song = song_node
                song_node = song_node.next_song_in_genre
            # clean empty header
            if header.first_song is None:
                if prev_header:
                    prev_header.next_header = header.next_header
                else:
                    self.head = header.next_header
                header = header.next_header
                continue
            prev_header = header
            header = header.next_header

    def get_songs_by_genre(self, genre: str) -> List[Any]:
        cur = self.head
        while cur:
            if cur.genre.lower() == genre.lower():
                out = []
                s = cur.first_song
                while s:
                    out.append(s.song)
                    s = s.next_song_in_genre
                return out
            cur = cur.next_header
        return []

    def get_all_genres(self) -> List[str]:
        out = []
        cur = self.head
        while cur:
            out.append(cur.genre)
            cur = cur.next_header
        return out


# -----------------------------
# Binary Search Tree (BST) by title (case-insensitive)
# -----------------------------

class BSTNode:
    def __init__(self, key: str, song: Any):
        self.key = key.lower()
        self.song = song
        self.left: Optional[BSTNode] = None
        self.right: Optional[BSTNode] = None

class BST:
    """Binary Search Tree keyed by song title (lowercased).
    - insert: O(h)
    - search exact: O(h)
    - inorder: O(n)
    """
    def __init__(self):
        self.root: Optional[BSTNode] = None

    def insert(self, key: str, song: Any) -> None:
        node = BSTNode(key, song)
        if not self.root:
            self.root = node
            return
        cur = self.root
        while True:
            if node.key < cur.key:
                if cur.left:
                    cur = cur.left
                else:
                    cur.left = node
                    return
            else:
                if cur.right:
                    cur = cur.right
                else:
                    cur.right = node
                    return

    def search(self, key: str) -> Optional[Any]:
        key = key.lower()
        cur = self.root
        while cur:
            if key == cur.key:
                return cur.song
            elif key < cur.key:
                cur = cur.left
            else:
                cur = cur.right
        return None

    def inorder(self) -> List[Any]:
        out: List[Any] = []
        def _in(node: Optional[BSTNode]):
            if not node:
                return
            _in(node.left)
            out.append(node.song)
            _in(node.right)
        _in(self.root)
        return out

    def search_partial(self, query: str) -> List[Any]:
        q = query.lower()
        return [s for s in self.inorder() if q in getattr(s, 'title', '').lower()]


# -----------------------------
# Graph (Adjacency List)
# -----------------------------

class SongGraph:
    """Graph represented as adjacency list mapping song_id -> list of neighbor song_ids.
    Adding edges based on similarity features.
    Typical ops:
      - add_vertex: O(1)
      - add_edge: O(1)
      - neighbors: O(k)
    """
    def __init__(self):
        self.adj: Dict[int, List[int]] = {}

    def add_vertex(self, v: int) -> None:
        if v not in self.adj:
            self.adj[v] = []

    def add_edge(self, a: int, b: int) -> None:
        if a == b:
            return
        self.add_vertex(a)
        self.add_vertex(b)
        if b not in self.adj[a]:
            self.adj[a].append(b)
        if a not in self.adj[b]:
            self.adj[b].append(a)

    def neighbors(self, v: int) -> List[int]:
        return self.adj.get(v, [])
