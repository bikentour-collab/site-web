/* Bike'N Tour — proposition 3 : carte interactive, menus (sans dépendance) */
(() => {
  'use strict';

  const header = document.querySelector('[data-header]');
  const toggle = document.querySelector('[data-menu-toggle]');
  const menu = document.getElementById('menu');

  // Menu mobile
  if (toggle && menu && header) {
    const place = () => menu.style.setProperty('--menu-top', `${Math.round(header.getBoundingClientRect().bottom)}px`);
    const setOpen = (open) => {
      place();
      toggle.setAttribute('aria-expanded', String(open));
      toggle.querySelector('.sr-only').textContent = open ? 'Fermer le menu' : 'Ouvrir le menu';
      menu.classList.toggle('is-open', open);
      document.body.style.overflow = open ? 'hidden' : '';
    };
    toggle.addEventListener('click', () => setOpen(toggle.getAttribute('aria-expanded') !== 'true'));
    menu.addEventListener('click', (e) => { if (e.target.closest('a')) setOpen(false); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') setOpen(false); });
    window.addEventListener('resize', place, { passive: true });
  }

  // Sous-menus et langue
  const drops = document.querySelectorAll('.drop');
  const closeAll = (except) => drops.forEach((d) => {
    if (d === except) return;
    d.classList.remove('is-open');
    const b = d.querySelector(':scope > .drop-btn');
    if (b) b.setAttribute('aria-expanded', 'false');
  });
  drops.forEach((d) => {
    const btn = d.querySelector(':scope > .drop-btn');
    if (!btn) return;
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const open = !d.classList.contains('is-open');
      closeAll(d);
      d.classList.toggle('is-open', open);
      btn.setAttribute('aria-expanded', String(open));
    });
  });
  document.addEventListener('click', (e) => { if (!e.target.closest('.drop')) closeAll(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeAll(); });

  // ---------- Carte interactive ----------
  const initExplorer = (explorer) => {
    const svg = explorer.querySelector('.map-svg');
    const paths = explorer.querySelectorAll('.route');
    const buttons = explorer.querySelectorAll('.route-btn');
    const cards = explorer.querySelectorAll('[data-card]');
    const panelL = explorer.querySelector('.panel-intro');
    const panelR = explorer.querySelector('.panel-detail');
    const rider = svg.querySelector('.rider');
    const pinEnd = svg.querySelector('.pin-end');
    const calm = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const ext = svg.dataset.extent.split(' ').map(Number);
    const BASE_W = 1000;
    const initial = explorer.dataset.route || 'loire';
    const single = explorer.hasAttribute('data-single');
    let current = initial;
    let view = [0, 0, 1000, 742];
    let target = null;
    let anim = 0;

    const overlay = () => !!(panelR && panelL) && window.getComputedStyle(panelR).position === 'absolute';

    // zone libre de la carte (entre les panneaux), en pixels
    const freeArea = () => {
      const r = svg.getBoundingClientRect();
      let a = 16, b = r.width - 16, t = 16, btm = r.height - (overlay() ? 70 : 60);
      if (overlay()) {
        const L = panelL.getBoundingClientRect(), R = panelR.getBoundingClientRect();
        a = L.right - r.left + 24;
        b = R.left - r.left - 24;
        if (b - a < 200) { a = 16; b = r.width - 16; }
      }
      return { a, b, t, btm, W: r.width, H: r.height };
    };

    const fitBox = (bx, by, bw, bh, pad = 1.32) => {
      const f = freeArea();
      const s = Math.max((bw * pad) / (f.b - f.a), (bh * pad) / (f.btm - f.t), 190 / f.W);
      let x0 = bx + bw / 2 - ((f.a + f.b) / 2) * s;
      let y0 = by + bh / 2 - ((f.t + f.btm) / 2) * s;
      const vw = f.W * s, vh = f.H * s;
      x0 = Math.max(ext[0], Math.min(x0, ext[2] - vw));
      y0 = Math.max(ext[1], Math.min(y0, ext[3] - vh));
      return [x0, y0, vw, vh];
    };

    const unionBox = (ids) => {
      let x1 = Infinity, y1 = Infinity, x2 = -Infinity, y2 = -Infinity;
      ids.forEach((id) => {
        const g = svg.querySelector(`.route[data-route="${id}"] .route-line`);
        const bb = g.getBBox();
        x1 = Math.min(x1, bb.x); y1 = Math.min(y1, bb.y); x2 = Math.max(x2, bb.x + bb.width); y2 = Math.max(y2, bb.y + bb.height);
      });
      return [x1, y1, x2 - x1, y2 - y1];
    };

    const visibleIds = () => [...explorer.querySelectorAll('[data-route-list] li:not([hidden]) .route-btn')].map((b) => b.dataset.route);

    // étiquettes des points de vue : placées à droite, sinon à gauche, sinon masquées (visibles au survol)
    let declutterT = 0;
    const declutter = () => {
      const s = parseFloat(svg.style.getPropertyValue('--s')) || 1;
      const act = svg.dataset.active;
      const visible = [...svg.querySelectorAll('.poi')].filter((g) => (g.dataset.routes || '').split(' ').includes(act));
      const boxes = [...svg.querySelectorAll('.town text, .town circle:not(.pulse), .pin-end circle')].map((t) => t.getBBox())
        .concat(visible.map((g) => g.querySelector('.poi-halo').getBBox()));
      const hit = (b) => boxes.some((o) => b.x < o.x + o.width && b.x + b.width > o.x && b.y < o.y + o.height && b.y + b.height > o.y);
      svg.querySelectorAll('.poi').forEach((g) => {
        const t = g.querySelector('text'), c = g.querySelector('.poi-dot');
        if (!t || !visible.includes(g)) return;
        const cx = +c.getAttribute('cx'), cy = +c.getAttribute('cy'), d = 9 * s;
        t.classList.remove('is-off');
        const place = (anchor, dx, dy) => { t.setAttribute('text-anchor', anchor); t.setAttribute('x', (cx + dx).toFixed(1)); t.setAttribute('y', (cy + dy).toFixed(1)); return t.getBBox(); };
        let b = place('start', d, -d * .4);
        if (hit(b)) b = place('end', -d, -d * .4);
        if (hit(b)) b = place('start', d * .6, d * 1.6);
        if (hit(b)) { t.classList.add('is-off'); return; }
        boxes.push(b);
      });
    };

    const basemap = svg.querySelector('.basemap');
    // fond de carte chargé seulement à l'ouverture de la carte (ne ralentit pas le haut de page)
    if (basemap && basemap.dataset.src) { basemap.setAttribute('href', basemap.dataset.src); delete basemap.dataset.src; }
    const EXT_W = +(svg.dataset.extent || '0 0 1000').split(' ')[2] || 1000;
    const setView = (v) => {
      view = v;
      svg.setAttribute('viewBox', v.map((n) => n.toFixed(2)).join(' '));
      const px = svg.getBoundingClientRect().width || BASE_W;
      const s = v[2] / px; // unités SVG par pixel
      svg.style.setProperty('--s', s.toFixed(4));
      // fond de carte léger (2048 px) ; version HD chargée seulement quand on zoome
      if (basemap && basemap.dataset.hd && devicePixelRatio / s > 1.3 * 2048 / EXT_W) {
        const hd = basemap.dataset.hd; delete basemap.dataset.hd;
        const im = new Image(); im.onload = () => basemap.setAttribute('href', hd); im.src = hd;
      }
      svg.querySelectorAll('.town circle, .poi circle').forEach((c) => {
        if (!c.dataset.r) c.dataset.r = c.getAttribute('r');
        c.setAttribute('r', (c.dataset.r * s * 1.05).toFixed(2));
      });
      clearTimeout(declutterT); declutterT = setTimeout(declutter, 120);
      [...rider.querySelectorAll('circle'), ...pinEnd.querySelectorAll('circle')].forEach((c) => {
        if (!c.dataset.r) c.dataset.r = c.getAttribute('r');
        c.setAttribute('r', (c.dataset.r * s * .9).toFixed(2));
      });
    };

    const zoomTo = (v, instant = false) => {
      target = v;
      cancelAnimationFrame(anim);
      if (calm || instant) { setView(v); return; }
      const from = view.slice();
      const t0 = performance.now();
      const step = (now) => {
        const k = Math.min(1, (now - t0) / 900);
        const e = k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
        setView(from.map((f, i) => f + (v[i] - f) * e));
        if (k < 1) anim = requestAnimationFrame(step);
      };
      anim = requestAnimationFrame(step);
    };

    // petit cycliste qui parcourt l'itinéraire actif
    let rideRaf = 0;
    const ride = (id) => {
      cancelAnimationFrame(rideRaf);
      const line = svg.querySelector(`.route[data-route="${id}"] .route-line`);
      if (!line || calm) { rider.classList.remove('is-on'); return; }
      const len = line.getTotalLength();
      const dur = Math.min(14000, Math.max(6000, len * 8));
      let t0 = null;
      const loop = (now) => {
        if (t0 === null) t0 = now + 1500; // attend la fin du tracé
        const k = Math.max(0, ((now - t0) % dur) / dur);
        const p = line.getPointAtLength(k * len);
        rider.setAttribute('transform', `translate(${p.x.toFixed(1)} ${p.y.toFixed(1)})`);
        rider.classList.toggle('is-on', now > t0);
        rideRaf = requestAnimationFrame(loop);
      };
      rideRaf = requestAnimationFrame(loop);
    };

    const select = (id, { zoom = true, scroll = false } = {}) => {
      current = id;
      svg.dataset.active = id; // affiche les points de vue de l'itinéraire choisi
      setTimeout(declutter, 60);
      paths.forEach((g) => {
        const on = g.dataset.route === id;
        g.classList.toggle('is-active', on);
        g.classList.toggle('is-dim', !on);
        if (on) {
          const line = g.querySelector('.route-line');
          line.style.animation = 'none';
          void line.getBoundingClientRect();
          line.style.animation = '';
          g.parentNode.insertBefore(g, svg.querySelector('.pois') || rider); // l'itinéraire actif passe sous les points de vue
          const L = line.getTotalLength();
          const end = line.getPointAtLength(id === 'vignoble' ? L * .45 : L);
          pinEnd.setAttribute('transform', `translate(${end.x.toFixed(1)} ${end.y.toFixed(1)})`);
          pinEnd.style.display = id === 'vignoble' ? 'none' : '';
        }
      });
      buttons.forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.route === id)));
      cards.forEach((c) => { c.hidden = c.dataset.card !== id; });
      if (panelR) panelR.scrollTop = 0;
      if (zoom) zoomTo(fitBox(...unionBox([id])));
      ride(id);
      if (scroll && !overlay()) explorer.querySelector('.map-wrap').scrollIntoView({ behavior: calm ? 'auto' : 'smooth', block: 'start' });
    };

    const overview = (instant = false) => zoomTo(fitBox(...unionBox(visibleIds().length ? visibleIds() : ['loire']), 1.08), instant);

    buttons.forEach((b) => b.addEventListener('click', () => select(b.dataset.route)));
    paths.forEach((g) => {
      g.addEventListener('click', () => { if (!dragged) select(g.dataset.route); });
      g.addEventListener('mouseenter', () => { if (g.dataset.route !== current) g.classList.remove('is-dim'); });
      g.addEventListener('mouseleave', () => { if (g.dataset.route !== current) g.classList.add('is-dim'); });
    });
    explorer.querySelector('[data-map-reset]')?.addEventListener('click', () => overview());
    explorer.querySelectorAll('[data-zoom]').forEach((b) => b.addEventListener('click', () => {
      const f = b.dataset.zoom === 'in' ? .6 : 1.6;
      const r = svg.getBoundingClientRect();
      let w = Math.min(ext[2] - ext[0], Math.max(190 / r.width * r.width, view[2] * f));
      let h = w * view[3] / view[2];
      if (h > ext[3] - ext[1]) { h = ext[3] - ext[1]; w = h * view[2] / view[3]; }
      let x = view[0] + view[2] / 2 - w / 2, y = view[1] + view[3] / 2 - h / 2;
      x = Math.max(ext[0], Math.min(x, ext[2] - w));
      y = Math.max(ext[1], Math.min(y, ext[3] - h));
      zoomTo([x, y, w, h]);
    }));

    document.querySelectorAll('[data-goto]').forEach((b) => b.addEventListener('click', () => {
      explorer.scrollIntoView({ behavior: calm ? 'auto' : 'smooth', block: 'start' });
      setTimeout(() => select(b.dataset.goto), calm ? 0 : 450);
    }));

    // filtres
    const filters = explorer.querySelector('[data-filters]');
    filters?.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-filter]');
      if (!btn) return;
      const v = btn.dataset.filter;
      filters.querySelectorAll('[data-filter]').forEach((f) => {
        const on = f === btn;
        f.classList.toggle('is-on', on);
        f.setAttribute('aria-pressed', String(on));
      });
      explorer.querySelectorAll('[data-route-list] li').forEach((li) => {
        const ok = v === 'all' || li.dataset.duration.split(' ').includes(v);
        li.hidden = !ok;
        svg.querySelector(`.route[data-route="${li.querySelector('.route-btn').dataset.route}"]`).classList.toggle('is-out', !ok);
      });
      const ids = visibleIds();
      if (ids.length && !ids.includes(current)) select(ids[0], { zoom: false });
      overview();
    });

    // glisser pour déplacer la carte (souris)
    let drag = null, dragged = false;
    svg.addEventListener('pointerdown', (e) => {
      if (e.pointerType !== 'mouse' || e.button !== 0) return;
      drag = { x: e.clientX, y: e.clientY, v: view.slice() };
      dragged = false;
    });
    window.addEventListener('pointermove', (e) => {
      if (!drag) return;
      const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
      if (Math.abs(dx) + Math.abs(dy) > 4) { dragged = true; svg.style.cursor = 'grabbing'; }
      if (!dragged) return;
      const s = drag.v[2] / svg.getBoundingClientRect().width;
      let x0 = drag.v[0] - dx * s, y0 = drag.v[1] - dy * s;
      x0 = Math.max(ext[0], Math.min(x0, ext[2] - drag.v[2]));
      y0 = Math.max(ext[1], Math.min(y0, ext[3] - drag.v[3]));
      cancelAnimationFrame(anim);
      setView([x0, y0, drag.v[2], drag.v[3]]);
    });
    window.addEventListener('pointerup', () => { drag = null; svg.style.cursor = ''; setTimeout(() => { dragged = false; }, 0); });

    let rt = 0;
    window.addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(() => zoomTo(fitBox(...unionBox([current])), true), 150); }, { passive: true });

    select(initial, { zoom: false });
    if (single) {
      zoomTo(fitBox(...unionBox([initial]), 1.25), true);
    } else {
      overview(true);
      // après un court instant, on zoome sur l'itinéraire par défaut
      setTimeout(() => zoomTo(fitBox(...unionBox([initial]))), calm ? 0 : 1200);
    }
  };
  // la carte (calculs lourds) ne s'initialise qu'à l'approche de l'écran : affichage initial plus rapide
  const explorer = document.querySelector('[data-explorer]');
  if (explorer && 'IntersectionObserver' in window) {
    new IntersectionObserver((en) => explorer.classList.toggle('is-offscreen', !en[0].isIntersecting)).observe(explorer);
  }
  if (explorer) {
    let done = false;
    const go = () => { if (!done) { done = true; initExplorer(explorer); } };
    if (explorer.hasAttribute('data-single') || !('IntersectionObserver' in window)) go();
    else {
      const io = new IntersectionObserver((en) => { if (en.some((x) => x.isIntersecting)) { io.disconnect(); go(); } }, { rootMargin: '80px 0px' });
      io.observe(explorer);
      explorer.addEventListener('pointerdown', go, { once: true });
      explorer.addEventListener('focusin', go, { once: true });
    }
  }

  // Formulaires sans serveur : ouverture d'un email pré-rempli
  document.querySelectorAll('form[data-mailto]').forEach((form) => {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const email = form.querySelector('input[type="email"]');
      if (!email.checkValidity()) { email.reportValidity(); return; }
      const status = form.querySelector('.form-status');
      const mailto = () => {
        const body = (form.dataset.body || '').replace('{email}', email.value).replace(/\|/g, '\n');
        window.location.href = `mailto:${form.dataset.mailto}?subject=${encodeURIComponent(form.dataset.subject)}&body=${encodeURIComponent(body)}`;
        if (status) status.textContent = form.dataset.msg || '';
      };
      if (!form.dataset.api || !window.fetch) return mailto();
      // envoi direct par le serveur (Brevo) ; repli sur la messagerie si le service n'est pas configuré
      const data = new URLSearchParams(new FormData(form));
      data.set('lang', document.documentElement.lang || 'fr');
      const btn = form.querySelector('button');
      if (btn) btn.disabled = true;
      fetch(form.dataset.api, { method: 'POST', body: data })
        .then((r) => {
          if (!r.ok) throw new Error(String(r.status));
          if (status) status.textContent = form.dataset.ok || '';
          form.reset();
        })
        .catch(mailto)
        .finally(() => { if (btn) btn.disabled = false; });
    });
  });

  // Apparition au défilement
  const reveals = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const io = new IntersectionObserver((entries) => entries.forEach((en) => {
      if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); }
    }), { rootMargin: '0px 0px -10% 0px' });
    reveals.forEach((el) => io.observe(el));
  } else {
    reveals.forEach((el) => el.classList.add('is-in'));
  }

  // ---------- Barre de réservation mobile : visible après le premier écran ----------
  const mcta = document.querySelector('[data-mcta]');
  if (mcta) {
    const toggle = () => document.body.classList.toggle('has-mcta', window.scrollY > window.innerHeight * 0.6);
    window.addEventListener('scroll', toggle, { passive: true }); toggle();
  }

  // ---------- Cookies (CNIL) : rien n'est chargé sans accord ----------
  const cc = document.getElementById('cookies');
  if (cc) {
    const KEY = 'bnt_consent', MAX_AGE = 182 * 24 * 3600; // choix conservé 6 mois
    const ga4 = cc.dataset.ga4, mUrl = cc.dataset.matomoUrl, mId = cc.dataset.matomoId;
    const tracked = Boolean(ga4 || (mUrl && mId));
    const read = () => { const m = document.cookie.match(/(?:^|; )bnt_consent=([^;]+)/); try { return m ? JSON.parse(decodeURIComponent(m[1])) : null; } catch (e) { return null; } };
    const write = (v) => { document.cookie = `${KEY}=${encodeURIComponent(JSON.stringify(v))}; Max-Age=${MAX_AGE}; Path=/; SameSite=Lax${location.protocol === 'https:' ? '; Secure' : ''}`; };
    const load = (src, attrs = {}) => { const s = document.createElement('script'); s.async = true; s.src = src; Object.assign(s.dataset, attrs); document.head.appendChild(s); };
    let started = false;
    const start = () => {
      if (started) return; started = true;
      if (ga4) {
        window.dataLayer = window.dataLayer || []; window.gtag = function () { window.dataLayer.push(arguments); };
        window.gtag('js', new Date()); window.gtag('config', ga4, { anonymize_ip: true });
        load('https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(ga4));
      }
      if (mUrl && mId) {
        const u = mUrl.replace(/\/?$/, '/'); window._paq = window._paq || [];
        window._paq.push(['trackPageView'], ['enableLinkTracking'], ['setTrackerUrl', u + 'matomo.php'], ['setSiteId', mId]);
        load(u + 'matomo.js');
      }
    };
    const prefs = cc.querySelector('.cc-prefs'), box = cc.querySelector('input[name=analytics]');
    const show = () => { const c = read(); if (box) box.checked = Boolean(c && c.analytics); cc.hidden = false; };
    const decide = (analytics) => { write({ analytics, date: new Date().toISOString().slice(0, 10) }); cc.hidden = true; if (analytics) start(); };
    cc.addEventListener('click', (e) => {
      const b = e.target.closest('[data-cc]'); if (!b) return;
      const a = b.dataset.cc;
      if (a === 'accept') decide(true);
      if (a === 'refuse') decide(false);
      if (a === 'save') decide(Boolean(box && box.checked));
      if (a === 'custom') { prefs.hidden = false; b.hidden = true; cc.querySelector('[data-cc=save]').hidden = false; }
    });
    document.querySelectorAll('[data-cc-open]').forEach((b) => b.addEventListener('click', show));
    const c = read();
    if (c && c.analytics) start();
    else if (!c && tracked) show(); // la bannière n'apparaît que si un outil de mesure est configuré
  }
})();
