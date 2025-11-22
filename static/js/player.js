// Basic client for SonicWave
const api = {
  songs: () => fetch('/api/songs').then(r=>r.json()),
  play: (id) => fetch(`/api/play/${id}`, {method:'POST'}).then(r=>r.json()),
  next: () => fetch('/api/next', {method:'POST'}).then(r=>r.json()),
  prev: () => fetch('/api/prev', {method:'POST'}).then(r=>r.json()),
  queueAdd: (id) => fetch(`/api/queue/add/${id}`, {method:'POST'}).then(r=>r.json()),
  search: (q) => fetch(`/api/search?query=${encodeURIComponent(q)}`).then(r=>r.json()),
  genres: () => fetch('/api/genres').then(r=>r.json()),
  genreSongs: (g) => fetch(`/api/genres/${encodeURIComponent(g)}`).then(r=>r.json()),
  favorite: (id, fav) => fetch(`/api/songs/${id}/favorite`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({is_favorite: fav})}).then(r=>r.json()),
};

const state = {
  songs: window.__INITIAL__?.songs || [],
  genres: window.__INITIAL__?.genres || [],
  history: window.__INITIAL__?.history || [],
  queue: window.__INITIAL__?.queue || [],
  activeId: null,
  repeat: false,
  shuffle: false,
};

const el = (sel) => document.querySelector(sel);
const grid = el('#songs-grid');
const recent = el('#recent');
const reco = el('#reco');
const genresEl = el('#genres');
const searchInput = el('#search');
const audio = el('#audio');
const nowTitle = el('#now-title');
const nowArtist = el('#now-artist');
const progress = el('#progress');
const volume = el('#volume');
const btnPlay = el('#btn-play');
const btnPrev = el('#btn-prev');
const btnNext = el('#btn-next');
const btnShuffle = el('#btn-shuffle');
const btnRepeat = el('#btn-repeat');
const nayara = el('#nayara-mascot');
const nayaraBubble = el('#nayara-bubble');
const cursorBlob = el('#cursor-blob');
const shootingStar = el('#shooting-star');

function fmtTime(s){
  s = Math.max(0, s|0);
  const m = Math.floor(s/60), ss = (s%60).toString().padStart(2,'0');
  return `${m}:${ss}`;
}

function cardHTML(s){
  return `<div class="card" data-id="${s.song_id}">
    <div class="thumb"></div>
    <div class="meta">
      <div class="title">${s.title}</div>
      <div class="sub">${s.artist || 'Unknown'} • ${s.genre || 'Unknown'} • ${s.year||''}</div>
    </div>
    <div class="actions">
      <button data-act="play">Play</button>
      <button data-act="queue">Queue</button>
      <button data-act="fav" class="${s.is_favorite?'active':''}">❤</button>
    </div>
  </div>`;
}

function render(){
  if(grid){ grid.innerHTML = state.songs.map(cardHTML).join(''); }
  if(recent){ recent.innerHTML = state.history.map(cardHTML).join(''); }
  if(genresEl){ genresEl.innerHTML = state.genres.map(g=>`<div class="chip" data-genre="${g}">${g}</div>`).join(''); }
  highlightActive();
}

function highlightActive(){
  document.querySelectorAll('.card').forEach(c=>c.classList.remove('active'));
  if(state.activeId){
    const active = document.querySelector(`.card[data-id="${state.activeId}"]`);
    if(active) active.classList.add('active');
  }
}

function bindEvents(){
  document.body.addEventListener('click', async (e)=>{
    const card = e.target.closest('.card');
    if(card){
      const id = Number(card.dataset.id);
      const act = e.target.getAttribute('data-act');
      if(act === 'play'){
        const res = await api.play(id);
        if(res?.ok){
          onPlay(res.song);
        }
      } else if(act === 'queue'){
        await api.queueAdd(id);
      } else if(act === 'fav'){
        const toggled = !card.querySelector('[data-act=fav]').classList.contains('active');
        const res = await api.favorite(id, toggled);
        if(res?.ok){
          card.querySelector('[data-act=fav]').classList.toggle('active', toggled);
          const idx = state.songs.findIndex(s=>s.song_id===id);
          if(idx>-1) state.songs[idx].is_favorite = toggled;
        }
      }
    }
  });

  if(searchInput){
    let t;
    searchInput.addEventListener('input', ()=>{
      clearTimeout(t);
      t = setTimeout(async ()=>{
        const q = searchInput.value.trim();
        if(!q){ render(); return; }
        const results = await api.search(q);
        grid.innerHTML = results.map(cardHTML).join('');
      }, 220);
    });
  }

  genresEl?.addEventListener('click', async (e)=>{
    const chip = e.target.closest('.chip');
    if(!chip) return;
    const g = chip.dataset.genre;
    const songs = await api.genreSongs(g);
    grid.innerHTML = songs.map(cardHTML).join('');
  });

  btnPlay?.addEventListener('click', ()=>{
    if(audio.paused){ audio.play(); btnPlay.textContent = '⏸'; } else { audio.pause(); btnPlay.textContent = '▶️'; }
  });
  btnNext?.addEventListener('click', async ()=>{ const res = await api.next(); if(res?.ok) onPlay(res.song); });
  btnPrev?.addEventListener('click', async ()=>{ const res = await api.prev(); if(res?.ok) onPlay(res.song); });

  audio.addEventListener('timeupdate', ()=>{
    const p = audio.duration? (audio.currentTime / audio.duration) * 100 : 0;
    progress.value = p|0;
    el('#cur-time').textContent = fmtTime(audio.currentTime);
    el('#dur-time').textContent = fmtTime(audio.duration||0);
  });
  progress.addEventListener('input', ()=>{
    if(!audio.duration) return;
    audio.currentTime = (progress.value/100) * audio.duration;
  });
  volume.addEventListener('input', ()=>{ audio.volume = Number(volume.value); });
}

function onPlay(song){
  state.activeId = song.song_id;
  highlightActive();
  nowTitle.textContent = song.title;
  nowArtist.textContent = song.artist || '';
  audio.src = song.audio_url;
  audio.play();
  btnPlay.textContent = '⏸';
  // Nayara reaction
  nayaraBubble.textContent = `Now playing: ${song.title}`;
  nayara.style.transition = 'transform .6s ease';
  const playerBar = document.getElementById('player-bar');
  const rect = playerBar.getBoundingClientRect();
  nayara.style.transform = `translate(-${rect.width/2 - 120}px, -40px)`;
  setTimeout(()=>{ nayara.style.transform = ''; }, 1200);
}

// Cursor blob follow
window.addEventListener('pointermove', (e)=>{
  cursorBlob.style.transform = `translate(${e.clientX}px, ${e.clientY}px)`;
});
window.addEventListener('pointerleave', ()=>{
  cursorBlob.style.opacity = .2;
});
window.addEventListener('pointerenter', ()=>{
  cursorBlob.style.opacity = .5;
});

// Shooting star interval
setInterval(()=>{
  if(!shootingStar) return;
  shootingStar.classList.remove('active');
  const y = Math.random()*window.innerHeight*0.4 + 20;
  shootingStar.style.top = `${y}px`;
  shootingStar.style.left = `${-200 - Math.random()*200}px`;
  void shootingStar.offsetWidth; // reflow
  shootingStar.classList.add('active');
}, 10000);

// Onboarding
(function(){
  const seen = localStorage.getItem('nayaraOnboardingSeen');
  const ob = document.getElementById('onboard');
  if(!seen && ob){
    ob.classList.remove('hidden');
    document.getElementById('onboard-close').addEventListener('click', ()=>{
      localStorage.setItem('nayaraOnboardingSeen', '1');
      ob.classList.add('hidden');
    });
  }
})();

// Initial render
render();
