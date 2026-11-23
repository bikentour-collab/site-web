(function () {
  'use strict';
  var G = window.GUIDE, app = document.getElementById('app'), W = G.w, H = G.h;
  var KEY = 'bnt-guide-vu';
  function load() { try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { return {}; } }
  function save(d) { try { localStorage.setItem(KEY, JSON.stringify(d)); } catch (e) { /* stockage indisponible */ } }
  var seen = load();
  function el(tag, attrs, html) {
    var e = document.createElement(tag);
    for (var k in (attrs || {})) { if (k === 'text') e.textContent = attrs[k]; else e.setAttribute(k, attrs[k]); }
    if (html != null) e.innerHTML = html;
    return e;
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function md(s) { return esc(s).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>'); }
  function progress() {
    var n = G.chapters.filter(function (c) { return seen[c.id]; }).length;
    document.getElementById('progTxt').textContent = n + ' / ' + G.chapters.length + ' chapitres vus';
  }
  function route() {
    var h = location.hash.replace('#', '').split('/');
    var c = G.chapters.findIndex(function (x) { return x.id === h[0]; });
    if (c < 0) return home();
    player(c, Math.max(0, Math.min(parseInt(h[1] || '1', 10) - 1, (G.chapters[c].steps || [1]).length - 1)));
  }
  function go(c, s) { location.hash = G.chapters[c].id + (s ? '/' + (s + 1) : ''); }

  function home() {
    progress();
    app.innerHTML = '';
    var wrap = el('section', { class: 'g-home' });
    var welcome = /bienvenue/.test(location.search);
    wrap.appendChild(el('div', { class: 'g-hello' },
      '<h1>' + (welcome ? 'Bienvenue dans votre administration' : 'Tutoriel de l\'administration') + '</h1>' +
      '<p>Des démonstrations pas à pas sur les vrais écrans de votre administration. Cliquez sur la zone en surbrillance ou sur « Suivant » pour avancer. Comptez 10 minutes pour tout voir ; vous pouvez revenir ici à tout moment (rubrique « Tutoriel et bonnes pratiques » de l\'administration).</p>'));
    if (welcome) {
      var w = el('div', { class: 'g-welcome' }, '<p><b>Première connexion ?</b> Commencez par « Se repérer dans l\'administration », puis « Changer un prix » : en 3 minutes, vous saurez tout faire.</p>');
      var b = el('button', { class: 'g-btn g-btn-yellow', type: 'button' }, 'Commencer le tutoriel →');
      b.onclick = function () { go(0, 0); };
      w.appendChild(b); wrap.appendChild(w);
    }
    var grid = el('div', { class: 'g-cards' });
    G.chapters.forEach(function (c, i) {
      var card = el('button', { class: 'g-card' + (c.tips ? ' g-card-tips' : ''), type: 'button' });
      var img = el('div', { class: 'g-card-img', 'aria-hidden': 'true' });
      if (c.steps) { var s = c.steps[Math.min(1, c.steps.length - 1)]; img.style.backgroundImage = 'url(/admin/guide/img/' + s.img + ')'; } else img.textContent = '★';
      card.appendChild(img);
      card.appendChild(el('div', { class: 'g-card-body' },
        '<span class="g-card-num">' + (c.tips ? 'À garder en tête' : 'Démonstration ' + (i + 1)) + '</span><h2>' + esc(c.title) + '</h2><p>' + esc(c.intro) + '</p>' +
        '<span class="g-card-meta">' + (c.steps ? c.steps.length + ' étapes · ' + Math.max(1, Math.round(c.steps.length * 0.4)) + ' min' : c.tips.length + ' conseils') + '</span>'));
      if (seen[c.id]) card.appendChild(el('span', { class: 'g-done' }, '✓ Vu'));
      card.onclick = function () { go(i, 0); };
      grid.appendChild(card);
    });
    wrap.appendChild(grid);
    app.appendChild(wrap);
    window.scrollTo(0, 0);
  }

  function sidebar(ci) {
    var side = el('nav', { class: 'g-side', 'aria-label': 'Chapitres' });
    side.appendChild(el('h3', {}, 'Chapitres'));
    var hb = el('button', { type: 'button' }, '<span class="n">⌂</span><span>Tous les chapitres</span>');
    hb.onclick = function () { location.hash = ''; };
    side.appendChild(hb);
    G.chapters.forEach(function (c, i) {
      var b = el('button', { type: 'button', class: (i === ci ? 'is-on ' : '') + (seen[c.id] ? 'is-done' : '') },
        '<span class="n">' + (seen[c.id] && i !== ci ? '✓' : (c.tips ? '★' : i + 1)) + '</span><span>' + esc(c.title) + '</span>');
      b.onclick = function () { go(i, 0); };
      side.appendChild(b);
    });
    return side;
  }

  function finishChapter(ci) { seen[G.chapters[ci].id] = 1; save(seen); }

  function player(ci, si) {
    progress();
    var c = G.chapters[ci];
    app.innerHTML = '';
    var wrapper = el('div', { class: 'g-player' });
    wrapper.appendChild(sidebar(ci));
    var stage = el('section', { class: 'g-stage' });
    wrapper.appendChild(stage);
    app.appendChild(wrapper);
    var nextChap = ci + 1 < G.chapters.length ? ci + 1 : -1;

    if (c.tips) {
      finishChapter(ci); progress();
      stage.appendChild(el('div', { class: 'g-head' }, '<h1>' + esc(c.title) + '</h1><span class="g-count">' + esc(c.intro) + '</span>'));
      var t = el('div', { class: 'g-tips' });
      c.tips.forEach(function (x, i) { t.appendChild(el('article', { class: 'g-tipcard' }, '<span class="k">' + (i + 1) + '</span><b>' + esc(x[0]) + '</b><span>' + md(x[1]) + '</span>')); });
      stage.appendChild(t);
      var end = el('div', { class: 'g-end' }, '<p><b>C\'est tout !</b> Vous savez tout ce qu\'il faut pour faire vivre le site. Ce tutoriel reste disponible dans l\'administration.</p>');
      end.appendChild(el('a', { class: 'g-btn g-btn-primary', href: '/admin/' }, 'Ouvrir l\'administration →'));
      stage.appendChild(end);
      return;
    }

    var s = c.steps[si], last = si === c.steps.length - 1;
    stage.appendChild(el('div', { class: 'g-head' }, '<h1>' + esc(c.title) + '</h1><span class="g-count">Étape ' + (si + 1) + ' sur ' + c.steps.length + '</span>'));
    var bar = el('div', { class: 'g-bar', role: 'progressbar', 'aria-valuemin': '0', 'aria-valuemax': String(c.steps.length), 'aria-valuenow': String(si + 1) });
    var fill = el('i'); fill.style.width = ((si + 1) / c.steps.length * 100) + '%'; bar.appendChild(fill);
    stage.appendChild(bar);

    var frame = el('div', { class: 'g-frame' });
    var img = el('img', { src: '/admin/guide/img/' + s.img, alt: 'Capture de l\'administration : ' + s.title, width: String(W), height: String(H) });
    frame.appendChild(img);
    var tip = el('div', { class: 'g-tip', role: 'dialog', 'aria-label': s.title });
    tip.innerHTML = '<span class="g-step">Étape ' + (si + 1) + ' / ' + c.steps.length + '</span><h2>' + esc(s.title) + '</h2><p>' + md(s.text) + '</p>';
    var acts = el('div', { class: 'g-tip-actions' });
    var prev = el('button', { class: 'g-btn', type: 'button' }, '← Précédent');
    prev.disabled = si === 0 && ci === 0;
    prev.onclick = back;
    var nxt = el('button', { class: 'g-btn g-btn-primary', type: 'button' }, last ? (nextChap >= 0 ? 'Chapitre suivant →' : 'Terminer ✓') : 'Suivant →');
    nxt.onclick = forward;
    acts.appendChild(prev); acts.appendChild(nxt); tip.appendChild(acts);

    if (s.box) {
      var pad = 6, b = s.box;
      var spot = el('button', { class: 'g-spot', type: 'button', 'aria-label': 'Zone à cliquer : ' + s.title });
      spot.style.left = ((b.x - pad) / W * 100) + '%'; spot.style.top = ((b.y - pad) / H * 100) + '%';
      spot.style.width = ((b.w + 2 * pad) / W * 100) + '%'; spot.style.height = ((b.h + 2 * pad) / H * 100) + '%';
      spot.onclick = forward;
      frame.appendChild(spot);
      // bulle à côté de la zone : à droite si la zone est à gauche, sinon à gauche ; sous/au-dessus si la zone est très large
      var cx = b.x + b.w / 2, wide = b.w > W * 0.42;
      if (wide) {
        var below = b.y + b.h + 24 < H * 0.62;
        tip.style.left = Math.max(2, Math.min(52, (b.x / W * 100))) + '%';
        if (below) tip.style.top = ((b.y + b.h + 22) / H * 100) + '%'; else tip.style.bottom = ((H - b.y + 22) / H * 100) + '%';
      } else {
        var top = Math.max(2, Math.min(60, ((b.y + b.h / 2) / H * 100) - 12));
        tip.style.top = top + '%';
        if (cx < W / 2) tip.style.left = Math.min(52, ((b.x + b.w + 28) / W * 100)) + '%';
        else tip.style.right = Math.min(52, ((W - b.x + 28) / W * 100)) + '%';
      }
    } else {
      frame.appendChild(el('div', { class: 'g-dim' }));
      tip.classList.add('g-tip-center');
    }
    stage.appendChild(frame);
    if (window.matchMedia('(max-width: 980px)').matches) stage.appendChild(tip); else frame.appendChild(tip);

    var ctr = el('div', { class: 'g-controls' });
    var dots = el('div', { class: 'g-dots' });
    c.steps.forEach(function (_, i) {
      var d = el('button', { type: 'button', class: i === si ? 'is-on' : '', 'aria-label': 'Étape ' + (i + 1) });
      d.onclick = function () { go(ci, i); };
      dots.appendChild(d);
    });
    ctr.appendChild(dots);
    ctr.appendChild(el('span', { class: 'g-hint' }, 'Astuce : flèches ← → du clavier pour avancer, Échap pour revenir aux chapitres.'));
    stage.appendChild(ctr);
    // précharger l'image suivante
    if (!last) { var pre = new Image(); pre.src = '/admin/guide/img/' + c.steps[si + 1].img; }
    window.scrollTo(0, 0);

    function forward() {
      if (!last) return go(ci, si + 1);
      finishChapter(ci);
      if (nextChap >= 0) go(nextChap, 0); else location.hash = '';
    }
    function back() {
      if (si > 0) return go(ci, si - 1);
      if (ci > 0) { var pc = G.chapters[ci - 1]; go(ci - 1, pc.steps ? pc.steps.length - 1 : 0); }
    }
    document.onkeydown = function (e) {
      if (e.key === 'ArrowRight') forward();
      else if (e.key === 'ArrowLeft') back();
      else if (e.key === 'Escape') location.hash = '';
    };
  }
  window.addEventListener('hashchange', function () { document.onkeydown = null; route(); });
  route();
})();
