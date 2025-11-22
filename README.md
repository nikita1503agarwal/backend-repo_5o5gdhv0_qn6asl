# SonicWave – Data Structures Player

A modern, dark, outer-space themed web music player showcasing fundamental data structures in Python.

## Tech Stack
- Backend: Python 3 + Flask, Jinja2 templates
- Frontend: HTML5, CSS, vanilla JavaScript (no SPA)

## Setup
1. Create a virtual environment (recommended) and activate it.
2. Install dependencies:
   pip install -r requirements.txt
3. Place your .mp3/.wav files into:
   static/music/
4. Run the server:
   python app.py
5. Open http://localhost:5000

## Features
- Discover page with animated, glassy UI and space background (stars, nebula, cursor glow, shooting star)
- Audio playback with player bar, progress and volume
- Search by title using a Binary Search Tree
- Browse by genre using a multi linked list
- Up Next queue using a Queue
- Listening history using a Stack
- Playlists powered by Doubly Linked Lists
- Master library stored in a Singly Linked List
- Song similarity graph (artist/genre/year) for recommendations
- Simple admin: rescan folder, edit metadata, delete songs
- Mascot Nayara with onboarding and reactive messages

## Data Structures and How They’re Used
- Singly Linked List (SLL): stores the master library of all songs. Operations: insert at end (O(1) amortized with tail), delete by id (O(n)), traverse (O(n)).
- Doubly Linked List (DLL): backs each Playlist for efficient next/prev navigation.
- Stack: maintains listening history for quick back navigation.
- Queue: powers the Up Next list in FIFO order.
- Multi Linked List by Genre: genre headers each point to their own song linked list. Enables quick genre browsing.
- Binary Search Tree (BST): indexed by song title (case-insensitive) for fast search and in-order listings.
- Graph (Adjacency List): song_id -> similar ids; edges added for same artist/genre/near year. Used for recommendations when not using a playlist or queue.

## Project Structure
- app.py – Flask entry, routes for pages and API
- data_structures.py – all custom DS implementations
- models.py – Song dataclass, Playlist (DLL under the hood), session holder
- music_manager.py – orchestrates everything, scans static/music, builds indexes
- templates/
  - base.html – layout, sidebar, player bar, backgrounds, Nayara
  - index.html – discover page and Spline cover
  - admin.html – admin tools
- static/css/style.css – dark space theme, glass UI, animations
- static/js/player.js – UI wiring, API calls, audio controls, animations
- static/music/ – drop your audio files here
- static/img/nayara.png – mascot (add manually)

## Notes
- Favorites are toggled via a simple flag in memory for runtime; for persistence, integrate a database.
- Durations are shown from the audio element as it loads; metadata inference uses filename patterns like "Artist - Title.mp3".
