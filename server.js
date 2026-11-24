// Serveur statique minimal pour Railway (aucune dépendance).
const http = require('http');
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

const ROOT = __dirname;
const PORT = process.env.PORT || 3000;
const TYPES = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json', '.webmanifest': 'application/manifest+json', '.xml': 'application/xml; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.webp': 'image/webp', '.md': 'text/markdown; charset=utf-8', '.yml': 'text/yaml; charset=utf-8', '.ico': 'image/x-icon', '.woff2': 'font/woff2', '.pdf': 'application/pdf'
};
const COMPRESS = new Set(['.md', '.html', '.css', '.js', '.json', '.xml', '.txt', '.svg', '.webmanifest']);
const HIDDEN = new Set(['server.js', 'package.json', 'package-lock.json', 'README.md', 'redirects.json']);
// Redirections 301 (anciennes adresses → nouvelles)
const load = f => fs.existsSync(path.join(ROOT, f)) ? JSON.parse(fs.readFileSync(path.join(ROOT, f), 'utf8')) : {};
const REDIRECTS = load('redirects.json');


// Politique de sécurité du contenu (pages publiques ; l'admin Sveltia en est exclue)
function buildCsp() {
  const hash = require('crypto').createHash('sha256').update("document.documentElement.classList.add('js')").digest('base64');
  let matomo = '';
  try { const cfg = JSON.parse(fs.readFileSync(path.join(ROOT, 'content', 'fr', 'site.json'), 'utf8')); matomo = cfg.matomo_url ? new URL(cfg.matomo_url).origin : ''; } catch (e) { /* facultatif */ }
  const ga = 'https://www.googletagmanager.com https://*.google-analytics.com https://*.analytics.google.com';
  return [
    "default-src 'self'", `script-src 'self' 'sha256-${hash}' https://www.googletagmanager.com ${matomo}`.trim(),
    "style-src 'self'", `img-src 'self' data: ${ga} ${matomo}`.trim(), "font-src 'self'", `connect-src 'self' ${ga} ${matomo}`.trim(),
    "frame-ancestors 'self'", "base-uri 'self'", "object-src 'none'", "form-action 'self' mailto:", 'upgrade-insecure-requests'
  ].join('; ');
}
const CSP = buildCsp();

const PROD_HOSTS = (process.env.PROD_HOSTS || 'www.bikentour.com,bikentour.com,localhost').split(',').map(h => h.trim().toLowerCase());
const SECURITY_HEADERS = {
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'X-Frame-Options': 'SAMEORIGIN',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
};

function resolve(urlPath) {
  let p = decodeURIComponent(urlPath.split('?')[0]);
  if (p.endsWith('/')) p += 'index.html';
  const file = path.normalize(path.join(ROOT, p));
  if (!file.startsWith(ROOT)) return null;
  if (fs.existsSync(file) && fs.statSync(file).isFile()) return file;
  if (fs.existsSync(file + '.html')) return file + '.html';
  if (fs.existsSync(path.join(file, 'index.html'))) return path.join(file, 'index.html');
  return null;
}

// ------------------------------------------------------------------ administration (Sveltia CMS)
// Connexion GitHub : même protocole que le service officiel sveltia-cms-auth.
// Variables Railway : GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET (application OAuth GitHub), GITHUB_REPO (ex. compte/bikentour)
const crypto = require('crypto');
const SITE_URL = process.env.SITE_URL || 'https://www.bikentour.com';
const ALLOWED_HOSTS = (process.env.ALLOWED_DOMAINS || 'www.bikentour.com,bikentour.com,localhost')
  .split(',').map(s => new RegExp('^' + s.trim().replace(/[.+?^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '.+') + '$'));
const SCOPES = ['repo', 'public_repo', 'user'];

function authPage(res, provider, content, ok) {
  const state = ok ? 'success' : 'error';
  const msg = JSON.stringify(`authorization:${provider}:${state}:${JSON.stringify(content)}`).replace(/</g, '\\u003c');
  const hosts = JSON.stringify(ALLOWED_HOSTS.map(r => r.source));
  res.writeHead(200, { 'Content-Type': TYPES['.html'], 'Cache-Control': 'no-store',
    'Set-Cookie': 'cms-state=deleted; HttpOnly; Max-Age=0; Path=/cms; SameSite=Lax; Secure', ...SECURITY_HEADERS });
  res.end(`<!doctype html><html><body><script>(() => {
    const trusted = ${hosts}.map(s => new RegExp(s));
    const ok = ${ok ? 'true' : 'false'};
    window.addEventListener('message', ({ data, origin }) => {
      if (data !== 'authorizing:${provider}') return;
      try { if (ok && !trusted.some(r => r.test(new URL(origin).hostname))) return; } catch (e) { return; }
      window.opener && window.opener.postMessage(${msg}, origin);
    });
    window.opener && window.opener.postMessage('authorizing:${provider}', '*');
  })();</script></body></html>`);
}

async function cmsAuth(req, res, url) {
  const id = process.env.GITHUB_CLIENT_ID, secret = process.env.GITHUB_CLIENT_SECRET;
  if (!loggedIn(req)) return authPage(res, 'github', { provider: 'github', error: 'Session expirée : rechargez la page et reconnectez-vous.', errorCode: 'UNAUTHORIZED' }, false);
  // Mode simple : jeton GitHub du dépôt fourni par le serveur après connexion par mot de passe
  if (url.pathname === '/cms/auth' && process.env.GITHUB_TOKEN && ADMIN_PASSWORD) {
    return authPage(res, 'github', { provider: 'github', token: process.env.GITHUB_TOKEN }, true);
  }
  if (url.pathname === '/cms/auth') {
    if (!id || !secret) return authPage(res, 'github', { provider: 'github', error: 'Connexion GitHub non configurée (GITHUB_CLIENT_ID / GITHUB_CLIENT_SECRET).', errorCode: 'MISCONFIGURED_CLIENT' }, false);
    const asked = (url.searchParams.get('scope') || '').split(/[\s,]+/).filter(Boolean);
    const scope = asked.length && asked.every(s => SCOPES.includes(s)) ? asked.join(',') : 'repo,user';
    const state = crypto.randomBytes(16).toString('hex');
    const params = new URLSearchParams({ client_id: id, scope, state, redirect_uri: `${SITE_URL}/cms/callback` });
    res.writeHead(302, { Location: `https://github.com/login/oauth/authorize?${params}`, 'Cache-Control': 'no-store',
      'Set-Cookie': `cms-state=${state}; HttpOnly; Max-Age=600; Path=/cms; SameSite=Lax; Secure`, ...SECURITY_HEADERS });
    return res.end();
  }
  // /cms/callback
  const code = url.searchParams.get('code'), state = url.searchParams.get('state');
  const cookie = ((req.headers.cookie || '').match(/\bcms-state=([0-9a-f]{32})\b/) || [])[1];
  if (!code || !state || state !== cookie) {
    return authPage(res, 'github', { provider: 'github', error: 'Échec de la connexion : veuillez réessayer.', errorCode: 'CSRF_DETECTED' }, false);
  }
  try {
    const r = await fetch('https://github.com/login/oauth/access_token', {
      method: 'POST', headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: JSON.stringify({ client_id: id, client_secret: secret, code })
    });
    const data = await r.json();
    if (!data.access_token) throw new Error(data.error_description || data.error || 'pas de jeton');
    return authPage(res, 'github', { provider: 'github', token: data.access_token }, true);
  } catch (e) {
    return authPage(res, 'github', { provider: 'github', error: 'GitHub n\'a pas renvoyé de jeton : ' + e.message, errorCode: 'TOKEN_REQUEST_FAILED' }, false);
  }
}

// ------------------------------------------------------------------ connexion admin (identifiant / mot de passe Railway)
// ADMIN_USER + ADMIN_PASSWORD : protègent /admin et /cms. SESSION_SECRET (facultatif) : clé de signature des sessions.
// GITHUB_TOKEN (facultatif) : jeton GitHub limité au dépôt ; l'admin s'en sert après la connexion, sans compte GitHub personnel.
const ADMIN_USER = process.env.ADMIN_USER || '';
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || '';
const SECRET = process.env.SESSION_SECRET || crypto.createHash('sha256').update('bnt:' + ADMIN_USER + ':' + ADMIN_PASSWORD).digest('hex');
const SESSION_DAYS = 7;
const failures = new Map(); // ip -> [horodatages des échecs]

const sign = v => crypto.createHmac('sha256', SECRET).update(v).digest('hex');
const same = (a, b) => { const x = Buffer.from(String(a)), y = Buffer.from(String(b)); return x.length === y.length && crypto.timingSafeEqual(x, y); };
const clientIp = req => (req.headers['x-forwarded-for'] || '').split(',')[0].trim() || req.socket.remoteAddress;

function loggedIn(req) {
  if (!ADMIN_PASSWORD) return false; // sans mot de passe défini, l'administration reste fermée
  const c = ((req.headers.cookie || '').match(/\bbnt_admin=(\d+)\.([0-9a-f]{64})\b/) || []);
  return c[1] && Number(c[1]) > Date.now() && same(c[2], sign(c[1]));
}

function loginPage(res, { error = '', status = 200, next = '/admin/' } = {}) {
  res.writeHead(status, { 'Content-Type': TYPES['.html'], 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex, nofollow', ...SECURITY_HEADERS });
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  res.end(`<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow"><title>Connexion | Administration Bike'N Tour</title><link rel="icon" href="/favicon.ico">
<style>
:root{--navy:#30336E;--olive:#437048;--paper:#F7F5EE;--line:#E1E0D6;--muted:#62647F}
*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;background:var(--paper);font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--navy)}
form{width:min(380px,calc(100vw - 32px));background:#fff;border:1px solid var(--line);border-radius:20px;padding:32px 28px;box-shadow:0 10px 30px rgba(48,51,110,.08);display:grid;gap:14px}
img{width:170px;height:auto;margin:0 auto 6px}h1{font-size:1.25rem;margin:0;text-align:center}p{margin:0;color:var(--muted);font-size:14px;text-align:center}
label{display:grid;gap:6px;font-weight:600;font-size:14px}input{font:inherit;padding:12px 14px;border:1px solid var(--line);border-radius:12px}
input:focus{outline:2px solid var(--navy);outline-offset:1px}button{font:inherit;font-weight:700;padding:13px;border:0;border-radius:12px;background:var(--navy);color:#fff;cursor:pointer}
.err{color:#A3261B;background:#FBEAE8;border-radius:10px;padding:10px 12px;text-align:left}
</style></head><body>
<form method="post" action="/admin/login">
<img src="/assets/img/logo-texte.png" alt="Bike'N Tour" width="652" height="120">
<h1>Administration du site</h1><p>Connectez-vous pour modifier les textes, les tarifs, les photos et le blog.</p>
${error ? `<p class="err" role="alert">${esc(error)}</p>` : ''}
<label>Identifiant<input name="user" autocomplete="username" required autofocus></label>
<label>Mot de passe<input name="password" type="password" autocomplete="current-password" required></label>
<input type="hidden" name="next" value="${esc(next)}">
<button type="submit">Se connecter</button>
<p><a href="/admin/guide/">Revoir le tutoriel de l'administration</a> · <a href="/admin/newsletter/">Écrire une newsletter</a></p>
</form></body></html>`);
}

function readBody(req) {
  return new Promise(resolve => {
    let data = '';
    req.on('data', c => { data += c; if (data.length > 10000) req.destroy(); });
    req.on('end', () => resolve(new URLSearchParams(data)));
  });
}

async function handleLogin(req, res) {
  const ip = clientIp(req), now = Date.now();
  const recent = (failures.get(ip) || []).filter(t => now - t < 15 * 60 * 1000);
  if (recent.length >= 5) return loginPage(res, { status: 429, error: 'Trop de tentatives. Réessayez dans 15 minutes.' });
  const form = await readBody(req);
  let next = /^\/admin\//.test(form.get('next') || '') ? form.get('next') : '/admin/';
  // Première connexion sur cet appareil : on commence par le tutoriel
  const firstTime = !/(?:^|;\s*)bnt_guide=1/.test(req.headers.cookie || '');
  if (firstTime && next === '/admin/') next = '/admin/guide/?bienvenue=1';
  if (ADMIN_PASSWORD && same(form.get('user') || '', ADMIN_USER) && same(form.get('password') || '', ADMIN_PASSWORD)) {
    failures.delete(ip);
    const exp = String(now + SESSION_DAYS * 86400 * 1000);
    res.writeHead(303, { Location: next, 'Cache-Control': 'no-store', ...SECURITY_HEADERS,
      'Set-Cookie': [`bnt_admin=${exp}.${sign(exp)}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=${SESSION_DAYS * 86400}`,
        'bnt_guide=1; Secure; SameSite=Lax; Path=/admin; Max-Age=31536000'] });
    return res.end();
  }
  recent.push(now); failures.set(ip, recent);
  return loginPage(res, { status: 401, error: 'Identifiant ou mot de passe incorrect.', next });
}

// ---------- Demande de fiche / trace GPX (formulaire des pages itinéraires) ----------
// Envoi par Resend (variable RESEND_API_KEY) : le visiteur reçoit tout de suite la fiche PDF et la trace GPX en pièces jointes,
// dans sa langue ; Antoine reçoit la demande (répondre = écrire au visiteur). Sans clé, le navigateur ouvre la messagerie.
const CONTACT_EMAIL = process.env.CONTACT_EMAIL || 'contact@bikentour.com';
const SENDER = process.env.SENDER_EMAIL || `Bike'N Tour <${CONTACT_EMAIL}>`;
const ROUTE_IDS = ['loire', 'velodyssee', 'regalante', 'traversee', 'canal', 'vignoble'];
const LANGS = ['fr', 'en', 'nl', 'de', 'es'];
const gpxHits = new Map();
async function resendSend(payload) {
  const r = await fetch((process.env.RESEND_API_URL || 'https://api.resend.com') + '/emails', {
    method: 'POST', headers: { Authorization: `Bearer ${process.env.RESEND_API_KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error('resend ' + r.status + ' ' + (await r.text()).slice(0, 200));
  return r.json();
}
function attachment(file, filename) {
  try { return { filename, content: fs.readFileSync(path.join(ROOT, file)).toString('base64') }; } catch (e) { return null; }
}
const MAIL = {
  fr: { subject: 'Votre fiche et trace GPX : {route}', hello: 'Bonjour,', body: "Merci pour votre demande ! Vous trouverez en pièces jointes la fiche de l'itinéraire « {route} » (PDF) et sa trace GPX, à importer dans votre GPS ou dans une application comme Komoot.", tip: 'Une question sur le parcours, le choix du vélo ou un aller simple ? Répondez simplement à cet email, ou appelez-nous.', cta: 'Réserver mes vélos', bye: "À bientôt à la boutique,\nL'équipe Bike'N Tour" },
  en: { subject: 'Your route sheet and GPX track: {route}', hello: 'Hello,', body: 'Thank you for your request! Attached you will find the route sheet for "{route}" (PDF) and its GPX track, ready to import into your GPS or an app such as Komoot.', tip: 'Any question about the route, choosing a bike or a one-way hire? Just reply to this email or give us a call.', cta: 'Book my bikes', bye: "See you soon at the shop,\nThe Bike'N Tour team" },
  nl: { subject: 'Uw routekaart en GPX-track: {route}', hello: 'Hallo,', body: 'Bedankt voor uw aanvraag! In de bijlagen vindt u de routekaart van "{route}" (pdf) en de GPX-track, klaar om te importeren in uw gps of een app zoals Komoot.', tip: 'Een vraag over de route, de keuze van de fiets of een enkele reis? Beantwoord gewoon deze e-mail of bel ons.', cta: 'Mijn fietsen reserveren', bye: "Tot snel in de winkel,\nHet team van Bike'N Tour" },
  de: { subject: 'Ihr Routenblatt und GPX-Track: {route}', hello: 'Hallo,', body: 'vielen Dank für Ihre Anfrage! Im Anhang finden Sie das Routenblatt für „{route}“ (PDF) und den GPX-Track zum Import in Ihr GPS-Gerät oder eine App wie Komoot.', tip: 'Fragen zur Strecke, zur Radwahl oder zur Einwegmiete? Antworten Sie einfach auf diese E-Mail oder rufen Sie uns an.', cta: 'Räder buchen', bye: "Bis bald im Laden,\nIhr Bike'N Tour-Team" },
  es: { subject: 'Su ficha y track GPX: {route}', hello: 'Hola:', body: 'Gracias por su solicitud. Adjuntamos la ficha de la ruta «{route}» (PDF) y su track GPX, listo para importar en su GPS o en una aplicación como Komoot.', tip: '¿Alguna pregunta sobre la ruta, la elección de la bicicleta o el alquiler solo de ida? Responda a este correo o llámenos.', cta: 'Reservar mis bicis', bye: "Hasta pronto en la tienda,\nEl equipo de Bike'N Tour" },
};
function mailHtml(t, route, booking) {
  const h = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const p = s => `<p style="margin:0 0 14px;font:15px/1.6 Arial,Helvetica,sans-serif;color:#1d1f3f">${h(s).replace(/\n/g, '<br>')}</p>`;
  return `<!doctype html><html><body style="margin:0;background:#F7F5EE;padding:24px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;margin:0 auto;background:#fff;border-radius:14px;overflow:hidden">
<tr><td style="background:#30336E;padding:20px 28px;font:800 22px Arial,Helvetica,sans-serif;color:#90C78E;letter-spacing:.5px">BIKE'N TOUR <span style="font:600 12px Arial;color:#fff;letter-spacing:1px">NANTES</span></td></tr>
<tr><td style="padding:28px">${p(t.hello)}${p(t.body.replace('{route}', route))}${p(t.tip)}
<p style="margin:22px 0"><a href="${h(booking)}" style="display:inline-block;background:#E7C14F;color:#22245A;font:700 15px Arial,Helvetica,sans-serif;text-decoration:none;padding:13px 22px;border-radius:10px">${h(t.cta)}</a></p>
${p(t.bye)}</td></tr>
<tr><td style="background:#F7F5EE;padding:16px 28px;font:12px/1.6 Arial,Helvetica,sans-serif;color:#62647F">Bike'N Tour · 27 quai de Versailles, 44000 Nantes<br>06 52 62 94 64 · WhatsApp 06 52 62 94 64 · <a href="mailto:${CONTACT_EMAIL}" style="color:#30336E">${CONTACT_EMAIL}</a> · <a href="https://www.bikentour.com" style="color:#30336E">www.bikentour.com</a></td></tr>
</table></body></html>`;
}
async function handleGpx(req, res) {
  const json = (code, obj) => { res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', ...SECURITY_HEADERS }); res.end(JSON.stringify(obj)); };
  if (!process.env.RESEND_API_KEY) return json(501, { ok: false });
  const ip = clientIp(req), now = Date.now();
  const recent = (gpxHits.get(ip) || []).filter(t => now - t < 60 * 60 * 1000);
  if (recent.length >= 5) return json(429, { ok: false });
  recent.push(now); gpxHits.set(ip, recent);
  const form = await readBody(req);
  const email = (form.get('email') || '').trim().slice(0, 200);
  const route = (form.get('route') || '').replace(/[^\p{L}\p{N} '’–-]/gu, '').slice(0, 80);
  const rid = ROUTE_IDS.includes(form.get('route_id')) ? form.get('route_id') : '';
  const lang = LANGS.includes((form.get('lang') || 'fr').slice(0, 2)) ? (form.get('lang') || 'fr').slice(0, 2) : 'fr';
  if (form.get('site')) return json(200, { ok: true }); // champ piège anti-robots
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return json(400, { ok: false });
  const t = MAIL[lang];
  const files = rid ? [attachment(`assets/pdf/fiches/${rid}-${lang}.pdf`, `bikentour-${rid}-${lang}.pdf`) || attachment(`assets/pdf/fiches/${rid}-fr.pdf`, `bikentour-${rid}.pdf`),
    attachment(`assets/gpx/bikentour-${rid}.gpx`, `bikentour-${rid}.gpx`)].filter(Boolean) : [];
  const booking = (() => { try { return JSON.parse(fs.readFileSync(path.join(ROOT, 'content', 'fr', 'site.json'), 'utf8')).reservation; } catch (e) { return 'https://www.bikentour.com'; } })();
  try {
    await resendSend({ from: SENDER, to: [email], reply_to: CONTACT_EMAIL, subject: t.subject.replace('{route}', route),
      html: mailHtml(t, route, booking), text: `${t.hello}\n\n${t.body.replace('{route}', route)}\n\n${t.tip}\n\n${t.cta} : ${booking}\n\n${t.bye}\n\nBike'N Tour · 27 quai de Versailles, 44000 Nantes · 06 52 62 94 64 · ${CONTACT_EMAIL}`,
      attachments: files });
  } catch (e) {
    console.error('Envoi de la fiche impossible :', e.message);
    return json(502, { ok: false });
  }
  // copie pour Antoine (un contact à rappeler) ; un échec ici ne gêne pas le visiteur
  resendSend({ from: SENDER, to: [CONTACT_EMAIL], reply_to: email, subject: `Nouvelle demande de fiche : ${route} (${lang.toUpperCase()}) – ${email}`,
    text: `Un visiteur a reçu la fiche et la trace GPX de « ${route} » (langue : ${lang}).\nEmail : ${email}\n\nRépondez à ce message pour lui écrire directement.` }).catch(e => console.error('Copie interne non envoyée :', e.message));
  return json(200, { ok: true });
}

// ---------- Formulaires Contact et Recrutement (pages Contact et Nous rejoindre) ----------
// POST /api/contact (JSON). Envoi par Resend à CONTACT_EMAIL (ou JOBS_EMAIL pour les candidatures), CV en pièce jointe,
// et accusé de réception au visiteur. Sans RESEND_API_KEY : 501, le navigateur ouvre la messagerie.
const formHits = new Map();
const FILE_TYPES = { pdf: 'application/pdf', doc: 'application/msword', docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', odt: 'application/vnd.oasis.opendocument.text', jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png' };
function readJson(req, max) {
  return new Promise(resolve => {
    let size = 0; const chunks = [];
    req.on('data', c => { size += c.length; if (size > max) { req.destroy(); resolve(null); } else chunks.push(c); });
    req.on('end', () => { try { resolve(JSON.parse(Buffer.concat(chunks).toString('utf8'))); } catch (e) { resolve(null); } });
  });
}
const ACK = {
  contact: {
    fr: ['Nous avons bien reçu votre message', "Bonjour {nom},\n\nMerci pour votre message, nous l'avons bien reçu. Nous vous répondons rapidement, en général dans la journée pendant la saison.\n\nBesoin d'une réponse immédiate ? Appelez-nous au 06 52 62 94 64 ou écrivez-nous sur WhatsApp.\n\nÀ bientôt,\nL'équipe Bike'N Tour"],
    en: ['We have received your message', "Hello {nom},\n\nThank you for your message. We will get back to you shortly, usually within the day during the season.\n\nNeed an answer right away? Call us on +33 6 52 62 94 64 or message us on WhatsApp.\n\nSee you soon,\nThe Bike'N Tour team"],
    nl: ['We hebben uw bericht ontvangen', "Hallo {nom},\n\nBedankt voor uw bericht. We antwoorden snel, tijdens het seizoen meestal dezelfde dag.\n\nMeteen een antwoord nodig? Bel ons op +33 6 52 62 94 64 of stuur een WhatsApp-bericht.\n\nTot snel,\nHet team van Bike'N Tour"],
    de: ['Wir haben Ihre Nachricht erhalten', "Hallo {nom},\n\nvielen Dank für Ihre Nachricht. Wir melden uns schnell, in der Saison meist noch am selben Tag.\n\nSie brauchen sofort eine Antwort? Rufen Sie uns an unter +33 6 52 62 94 64 oder schreiben Sie uns per WhatsApp.\n\nBis bald,\nIhr Bike'N Tour-Team"],
    es: ['Hemos recibido su mensaje', "Hola, {nom}:\n\nGracias por su mensaje. Le responderemos enseguida, normalmente en el mismo día durante la temporada.\n\n¿Necesita una respuesta inmediata? Llámenos al +33 6 52 62 94 64 o escríbanos por WhatsApp.\n\nHasta pronto,\nEl equipo de Bike'N Tour"],
  },
  candidature: { fr: ['Votre candidature chez Bike\'N Tour', "Bonjour {nom},\n\nMerci pour votre candidature, nous l'avons bien reçue. Nous la lisons avec attention et revenons vers vous rapidement.\n\nÀ bientôt,\nAntoine et l'équipe Bike'N Tour"] },
};
async function handleForm(req, res) {
  const json = (code, obj) => { res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', ...SECURITY_HEADERS }); res.end(JSON.stringify(obj)); };
  if (!process.env.RESEND_API_KEY) return json(501, { ok: false });
  const ip = clientIp(req), now = Date.now();
  const recent = (formHits.get(ip) || []).filter(t => now - t < 60 * 60 * 1000);
  if (recent.length >= 5) return json(429, { ok: false });
  const d = await readJson(req, 8 * 1024 * 1024);
  if (!d) return json(413, { ok: false });
  if (d.site) return json(200, { ok: true }); // champ piège anti-robots
  recent.push(now); formHits.set(ip, recent);
  const clean = (v, n) => String(v || '').replace(/[\u0000-\u0008\u000b-\u001f]/g, '').trim().slice(0, n);
  const kind = ['candidature', 'newsletter'].includes(d.kind) ? d.kind : 'contact';
  const lang = LANGS.includes(d.lang) ? d.lang : 'fr';
  if (kind === 'newsletter') return handleNewsletter(json, clean(d.email, 200), lang);
  const f = { nom: clean(d.nom, 120), email: clean(d.email, 200), tel: clean(d.tel, 40), sujet: clean(d.sujet, 120), dates: clean(d.dates, 120), poste: clean(d.poste, 120), message: clean(d.message, 5000) };
  if (!f.nom || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.email) || (kind === 'contact' && f.message.length < 2)) return json(400, { ok: false });
  const attachments = [];
  if (kind === 'candidature' && d.file && d.file.data) {
    const ext = String(d.file.name || '').split('.').pop().toLowerCase();
    const buf = Buffer.from(String(d.file.data), 'base64');
    if (!FILE_TYPES[ext] || buf.length > 5 * 1024 * 1024) return json(415, { ok: false });
    attachments.push({ filename: `CV-${f.nom.replace(/[^\p{L}\p{N}]+/gu, '-')}.${ext}`.slice(0, 100), content: buf.toString('base64') });
  }
  const to = kind === 'candidature' ? (process.env.JOBS_EMAIL || CONTACT_EMAIL) : CONTACT_EMAIL;
  const subject = kind === 'candidature' ? `Candidature : ${f.poste || 'spontanée'} – ${f.nom}` : `Message du site : ${f.sujet || 'contact'} – ${f.nom}`;
  const lines = [`${kind === 'candidature' ? 'Nouvelle candidature' : 'Nouveau message'} depuis le site (langue : ${lang})`, '',
    `Nom : ${f.nom}`, `Email : ${f.email}`, f.tel && `Téléphone : ${f.tel}`, f.sujet && `Sujet : ${f.sujet}`, f.dates && `Dates : ${f.dates}`, f.poste && `Poste : ${f.poste}`,
    attachments.length ? 'CV : en pièce jointe' : (kind === 'candidature' ? 'CV : non joint' : false), '', f.message, '', '— Répondez à ce message pour écrire directement à cette personne.'].filter(x => x !== false && x !== undefined);
  try {
    await resendSend({ from: SENDER, to: [to], reply_to: f.email, subject, text: lines.join('\n'), attachments });
  } catch (e) {
    console.error('Formulaire non envoyé :', e.message);
    return json(502, { ok: false });
  }
  const ack = (ACK[kind][lang] || ACK[kind].fr);
  resendSend({ from: SENDER, to: [f.email], reply_to: to, subject: ack[0], text: ack[1].replace('{nom}', f.nom.split(' ')[0]) + `\n\nBike'N Tour · 27 quai de Versailles, 44000 Nantes · 06 52 62 94 64 · ${CONTACT_EMAIL}` })
    .catch(e => console.error('Accusé de réception non envoyé :', e.message));
  return json(200, { ok: true });
}

// Newsletter (pied de page) : l'adresse est enregistrée comme contact Resend (Contacts), puis ajoutée au segment
// RESEND_SEGMENT_ID (ou RESEND_AUDIENCE_ID, ancien nom) s'il est défini. Antoine envoie ensuite ses newsletters depuis
// Resend → Broadcasts (lien de désinscription géré par Resend). Si la clé n'a pas le droit de gérer les contacts,
// l'inscription est envoyée par email à CONTACT_EMAIL pour ne rien perdre.
async function handleNewsletter(json, email, lang) {
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return json(400, { ok: false });
  const api = process.env.RESEND_API_URL || 'https://api.resend.com';
  const headers = { Authorization: `Bearer ${process.env.RESEND_API_KEY}`, 'Content-Type': 'application/json' };
  const segment = process.env.RESEND_SEGMENT_ID || process.env.RESEND_AUDIENCE_ID;
  try {
    const c = await fetch(api + '/contacts', { method: 'POST', headers, body: JSON.stringify({ email, unsubscribed: false }) });
    // contact déjà existant : on continue (ajout au segment)
    if (!c.ok && c.status !== 409 && c.status !== 422) throw new Error('contacts ' + c.status + ' ' + (await c.text()).slice(0, 200));
    if (segment) {
      const s = await fetch(`${api}/contacts/${encodeURIComponent(email)}/segments/${encodeURIComponent(segment)}`, { method: 'POST', headers });
      if (!s.ok) throw new Error('segment ' + s.status + ' ' + (await s.text()).slice(0, 200));
    }
    return json(200, { ok: true });
  } catch (e) {
    console.error('Inscription newsletter non enregistrée dans Resend, envoi par email :', e.message);
  }
  try {
    await resendSend({ from: SENDER, to: [CONTACT_EMAIL], reply_to: email, subject: `Inscription newsletter – ${email}`,
      text: `Nouvelle inscription à la newsletter depuis le site (langue : ${lang}) :\n\n${email}\n\nLa personne a coché le consentement. Elle n'a pas pu être ajoutée automatiquement aux contacts Resend : ajoutez-la à la main (Resend → Audience → Contacts).` });
  } catch (e) {
    console.error('Inscription newsletter non envoyée :', e.message);
    return json(502, { ok: false });
  }
  return json(200, { ok: true });
}

// ---------- Newsletter : rédaction et envoi depuis l'admin (/admin/newsletter/) ----------
// Les inscrits du pied de page sont des contacts Resend (segment RESEND_SEGMENT_ID). L'envoi crée une diffusion
// (Resend Broadcasts) vers ce segment ; Resend ajoute la désinscription et respecte les désinscrits.
const NL_SEGMENT = () => process.env.RESEND_SEGMENT_ID || process.env.RESEND_AUDIENCE_ID || '';
const escHtml = v => String(v || '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const safeUrl = u => /^https?:\/\/[^\s"'<>]+$/i.test(String(u || '').trim()) ? String(u).trim() : '';
function nlText(t) {
  const inline = x => escHtml(x)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, (m, a, u) => `<a href="${u}" style="color:#30336E;font-weight:700">${a}</a>`);
  // intertitres « ## » sur leur propre bloc, puis listes et paragraphes séparés à l'intérieur d'un bloc
  const src = String(t || '').replace(/\r/g, '').replace(/^(##\s+.*)$/gm, '\n$1\n');
  const out = [];
  for (const block of src.split(/\n{2,}/).map(x => x.trim()).filter(Boolean)) {
    if (/^##\s+/.test(block)) { out.push(`<h2 style="margin:26px 0 10px;font-size:19px;line-height:1.3;color:#30336E">${inline(block.replace(/^##\s+/, ''))}</h2>`); continue; }
    let run = [], isList = null;
    const flush = () => {
      if (!run.length) return;
      out.push(isList
        ? '<ul style="margin:0 0 18px;padding-left:20px">' + run.map(l => `<li style="margin:0 0 6px">${inline(l.replace(/^\s*[-•]\s+/, ''))}</li>`).join('') + '</ul>'
        : `<p style="margin:0 0 18px">${run.map(inline).join('<br>')}</p>`);
      run = [];
    };
    for (const line of block.split('\n')) {
      const li = /^\s*[-•]\s+/.test(line);
      if (isList !== null && li !== isList) flush();
      isList = li; run.push(line);
    }
    flush();
  }
  return out.join('\n');
}
function nlRender(d, base, test) {
  const img = safeUrl(d.image) || (d.image && /^\/assets\//.test(d.image) ? base + d.image : '');
  const btn = safeUrl(d.bouton_lien) && d.bouton_texte
    ? `<table role="presentation" cellpadding="0" cellspacing="0" style="margin:8px 0 26px"><tr><td style="background:#E7C14F;border-radius:999px"><a href="${escHtml(safeUrl(d.bouton_lien))}" style="display:inline-block;padding:14px 28px;font-weight:700;color:#30336E;text-decoration:none;font-size:16px">${escHtml(d.bouton_texte)}</a></td></tr></table>` : '';
  const unsub = test ? '#' : '{{{RESEND_UNSUBSCRIBE_URL}}}';
  return `<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escHtml(d.objet)}</title></head>
<body style="margin:0;background:#F4F1EA;font-family:Helvetica,Arial,sans-serif;color:#2E2D45">
<div style="display:none;max-height:0;overflow:hidden">${escHtml(d.apercu || '')}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F4F1EA"><tr><td align="center" style="padding:28px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:18px;overflow:hidden">
<tr><td style="padding:26px 32px 18px;border-bottom:1px solid #EEE9DD"><a href="${base}/fr"><img src="${base}/assets/img/logo-texte.png" alt="Bike'N Tour Nantes" width="170" style="display:block;border:0;width:170px;height:auto"></a></td></tr>
${img ? `<tr><td><img src="${escHtml(img)}" alt="" width="600" style="display:block;width:100%;max-width:600px;height:auto;border:0"></td></tr>` : ''}
<tr><td style="padding:30px 32px 8px;font-size:16px;line-height:1.6">
${d.titre ? `<h1 style="margin:0 0 18px;font-size:26px;line-height:1.2;color:#30336E">${escHtml(d.titre)}</h1>` : ''}
${nlText(d.texte)}
${btn}
<p style="margin:0 0 26px">À bientôt sur la route,<br><strong>Antoine et l'équipe Bike'N Tour</strong></p>
</td></tr>
<tr><td style="background:#30336E;color:#D8D7EA;padding:22px 32px;font-size:13px;line-height:1.6">
Bike'N Tour · 27 quai de Versailles, 44000 Nantes · <a href="tel:+33652629464" style="color:#ffffff">06 52 62 94 64</a><br>
Vous recevez cet email car vous vous êtes inscrit à la newsletter sur bikentour.com. <a href="${unsub}" style="color:#E7C14F">Se désinscrire</a>
</td></tr></table></td></tr></table></body></html>`;
}
async function resendApi(method, p, body) {
  const r = await fetch((process.env.RESEND_API_URL || 'https://api.resend.com') + p, {
    method, headers: { Authorization: `Bearer ${process.env.RESEND_API_KEY}`, 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  const txt = await r.text();
  if (!r.ok) throw new Error(`resend ${r.status} ${txt.slice(0, 200)}`);
  try { return JSON.parse(txt); } catch (e) { return {}; }
}
async function handleNewsletterAdmin(req, res, u) {
  const json = (code, obj) => { res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', ...SECURITY_HEADERS }); res.end(JSON.stringify(obj)); };
  const host = req.headers['x-forwarded-host'] || req.headers.host || 'www.bikentour.com';
  const proto = (req.headers['x-forwarded-proto'] || (/^(localhost|127\.)/.test(host) ? 'http' : 'https')).split(',')[0];
  const base = `${proto}://${host}`;
  const action = u.pathname.split('/').pop();
  if (req.method === 'GET' && action === 'etat') {
    const out = { resend: !!process.env.RESEND_API_KEY, segment: !!NL_SEGMENT(), contact: CONTACT_EMAIL, envois: [] };
    if (out.resend) {
      try {
        const b = await resendApi('GET', '/broadcasts');
        out.envois = (b.data || []).filter(x => !NL_SEGMENT() || [x.segment_id, x.audience_id].includes(NL_SEGMENT())).slice(0, 12)
          .map(x => ({ nom: x.name || '', statut: x.status || '', date: x.sent_at || x.scheduled_at || x.created_at || '' }));
      } catch (e) { out.erreur_historique = true; }
    }
    return json(200, out);
  }
  if (req.method !== 'POST') return json(405, { ok: false });
  // protection CSRF : requêtes JSON du même site uniquement
  const origin = req.headers.origin || '';
  if (!/application\/json/.test(req.headers['content-type'] || '') || (origin && new URL(origin).host !== host)) return json(403, { ok: false });
  const d = await readJson(req, 200 * 1024);
  if (!d) return json(400, { ok: false });
  const clip = (v, n) => String(v || '').slice(0, n);
  const n = { objet: clip(d.objet, 150), apercu: clip(d.apercu, 200), titre: clip(d.titre, 150), texte: clip(d.texte, 20000), image: clip(d.image, 500), bouton_texte: clip(d.bouton_texte, 60), bouton_lien: clip(d.bouton_lien, 500) };
  if (action === 'apercu') { res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store', ...SECURITY_HEADERS }); return res.end(nlRender(n, base, true)); }
  if (!n.objet || !n.texte.trim()) return json(400, { ok: false, message: "L'objet et le texte sont obligatoires." });
  if (!process.env.RESEND_API_KEY) return json(501, { ok: false, message: 'Resend n\'est pas configuré (variable RESEND_API_KEY).' });
  try {
    if (action === 'test') {
      const to = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(d.email || '') ? d.email : CONTACT_EMAIL;
      await resendSend({ from: SENDER, to: [to], subject: '[TEST] ' + n.objet, html: nlRender(n, base, true) });
      return json(200, { ok: true, message: `Test envoyé à ${to}.` });
    }
    if (action === 'envoyer') {
      if (!NL_SEGMENT()) return json(400, { ok: false, message: 'Ajoutez la variable RESEND_SEGMENT_ID dans Railway pour envoyer à tous les abonnés.' });
      if (d.confirmation !== 'ENVOYER') return json(400, { ok: false, message: 'Confirmation manquante.' });
      const date = new Date().toLocaleDateString('fr-FR', { timeZone: 'Europe/Paris' });
      const b = await resendApi('POST', '/broadcasts', { segment_id: NL_SEGMENT(), from: SENDER, reply_to: CONTACT_EMAIL, subject: n.objet, html: nlRender(n, base, false), name: `${n.objet} (${date})` });
      await resendApi('POST', `/broadcasts/${encodeURIComponent(b.id)}/send`, {});
      return json(200, { ok: true, message: 'Newsletter envoyée à tous les abonnés. Resend la distribue dans les minutes qui viennent.' });
    }
  } catch (e) {
    console.error('Newsletter :', e.message);
    return json(502, { ok: false, message: "L'envoi n'a pas abouti (Resend). Réessayez dans un instant ; si cela continue, vérifiez la clé et le domaine dans Resend." });
  }
  return json(404, { ok: false });
}

// Connexion en une étape : avec GITHUB_TOKEN, la session Sveltia est préparée dans le navigateur après le mot de passe
// (même format que lorsque Sveltia enregistre une connexion par jeton). En cas d'échec, l'écran de connexion habituel s'affiche.
let ghUser = null, ghUserAt = 0;
async function githubUser() {
  if (ghUser && Date.now() - ghUserAt < 3600 * 1000) return ghUser;
  const r = await fetch((process.env.GITHUB_API_URL || 'https://api.github.com') + '/user', { headers: { Authorization: `token ${process.env.GITHUB_TOKEN}`, 'User-Agent': 'bikentour-admin', Accept: 'application/vnd.github+json' } });
  if (!r.ok) throw new Error('github ' + r.status);
  const a = await r.json();
  ghUser = { backendName: 'github', id: a.id, name: a.name || a.login, login: a.login, email: a.email || '', avatarURL: a.avatar_url, profileURL: a.html_url };
  ghUserAt = Date.now();
  return ghUser;
}
// Traduction automatique (bouton « Traduire » de l'admin) : TRANSLATE_API_KEY (+ TRANSLATE_SERVICE, par défaut google-ai = Gemini).
// La clé est déposée dans les préférences Sveltia du navigateur après la connexion par mot de passe : rien à saisir pour Antoine.
const TRANSLATE_SERVICES = ['google-ai', 'anthropic', 'openai', 'google', 'mistral', 'deepseek'];
async function adminIndex(res) {
  let html = fs.readFileSync(path.join(ROOT, 'admin', 'index.html'), 'utf8');
  const parts = [];
  if (process.env.GITHUB_TOKEN) {
    try {
      const account = { ...(await githubUser()), token: process.env.GITHUB_TOKEN };
      parts.push(`var k='sveltia-cms.user',a=${JSON.stringify(account)},c=JSON.parse(localStorage.getItem(k)||'null');if(!c||c.token!==a.token)localStorage.setItem(k,JSON.stringify(a));`);
    } catch (e) { console.error('Connexion GitHub automatique indisponible :', e.message); }
  }
  if (process.env.TRANSLATE_API_KEY) {
    const service = TRANSLATE_SERVICES.includes(process.env.TRANSLATE_SERVICE) ? process.env.TRANSLATE_SERVICE : 'google-ai';
    parts.push(`var p='sveltia-cms.prefs',q=JSON.parse(localStorage.getItem(p)||'{}')||{};q.apiKeys=q.apiKeys||{};q.apiKeys[${JSON.stringify(service)}]=${JSON.stringify(process.env.TRANSLATE_API_KEY)};q.defaultTranslationService=${JSON.stringify(service)};localStorage.setItem(p,JSON.stringify(q));`);
  }
  if (parts.length) {
    const js = parts.map(x => `try{${x}}catch(e){}`).join('').replace(/</g, '\\u003c');
    html = html.replace('<script src="/admin/sveltia-cms.js">', `<script>${js}</script>\n<script src="/admin/sveltia-cms.js">`);
  }
  res.writeHead(200, { 'Content-Type': TYPES['.html'], 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex, nofollow', ...SECURITY_HEADERS });
  res.end(html);
}

function adminConfig(res) {
  const yml = fs.readFileSync(path.join(ROOT, 'admin', 'config.yml'), 'utf8')
    .replace('__GITHUB_REPO__', process.env.GITHUB_REPO || 'compte/bikentour')
    .replace('__SITE_URL__', SITE_URL);
  res.writeHead(200, { 'Content-Type': TYPES['.yml'], 'Cache-Control': 'no-cache', 'X-Robots-Tag': 'noindex', ...SECURITY_HEADERS });
  res.end(yml);
}

http.createServer((req, res) => {
  {
    const u = new URL(req.url, 'http://localhost');
    if (u.pathname === '/admin/login') {
      if (!ADMIN_PASSWORD) return loginPage(res, { status: 503, error: "Administration fermée : ajoutez les variables ADMIN_USER et ADMIN_PASSWORD dans Railway (Variables), puis redéployez." });
      if (req.method === 'POST') return void handleLogin(req, res);
      return loginPage(res, { next: /^\/admin\//.test(u.searchParams.get('next') || '') ? u.searchParams.get('next') : '/admin/' });
    }
    if (u.pathname === '/admin/logout') {
      res.writeHead(303, { Location: '/admin/login', ...SECURITY_HEADERS, 'Set-Cookie': 'bnt_admin=deleted; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=0' });
      return res.end();
    }
    if (u.pathname === '/cms/auth' || u.pathname === '/cms/callback') return void cmsAuth(req, res, u);
    if (u.pathname === '/api/gpx' && req.method === 'POST') return void handleGpx(req, res);
    if (u.pathname === '/api/contact' && req.method === 'POST') return void handleForm(req, res);
    if (u.pathname === '/admin' || u.pathname.startsWith('/admin/')) {
      if (!loggedIn(req)) {
        if (u.pathname === '/admin' || u.pathname.endsWith('/') || u.pathname.endsWith('.html')) {
          const back = u.pathname.startsWith('/admin/guide') ? '?next=' + encodeURIComponent('/admin/guide/') : u.pathname.startsWith('/admin/newsletter') ? '?next=' + encodeURIComponent('/admin/newsletter/') : '';
          res.writeHead(303, { Location: '/admin/login' + back, 'Cache-Control': 'no-store', ...SECURITY_HEADERS }); return res.end();
        }
        res.writeHead(401, { 'Cache-Control': 'no-store', ...SECURITY_HEADERS }); return res.end();
      }
      if (u.pathname.startsWith('/admin/api/newsletter/')) return void handleNewsletterAdmin(req, res, u);
      if (u.pathname === '/admin/config.yml') return adminConfig(res);
      if ((u.pathname === '/admin/' || u.pathname === '/admin/index.html') && (process.env.GITHUB_TOKEN || process.env.TRANSLATE_API_KEY)) return void adminIndex(res);
      if (u.pathname === '/admin') { res.writeHead(301, { Location: '/admin/', ...SECURITY_HEADERS }); return res.end(); }
    }
  }
  const [rawPath, query] = req.url.split('?');
  // dossiers techniques jamais servis
  if (/^\/(tools|content|docs|\.git|\.github|node_modules)(\/|$)/.test(rawPath)) { res.writeHead(404, SECURITY_HEADERS); return res.end(); }
  // redirections déclarées, puis suppression du slash final (une seule URL par page)
  const target = REDIRECTS[rawPath] || (rawPath.length > 1 && rawPath.endsWith('/') && rawPath !== '/admin/' ? rawPath.slice(0, -1) : null)
    || (rawPath.endsWith('.html') && rawPath !== '/404.html' ? rawPath.replace(/(index)?\.html$/, '') || '/' : null);
  if (target && target !== rawPath) {
    res.writeHead(301, { Location: target + (query ? '?' + query : ''), ...SECURITY_HEADERS });
    return res.end();
  }
  const file = resolve(req.url);
  if (!file || HIDDEN.has(path.basename(file)) || path.basename(file).startsWith('.')) {
    const notFound = path.join(ROOT, '404.html');
    res.writeHead(404, { 'Content-Type': TYPES['.html'], ...SECURITY_HEADERS });
    return fs.existsSync(notFound) ? fs.createReadStream(notFound).pipe(res) : res.end('Page introuvable');
  }
  const ext = path.extname(file).toLowerCase();
  const headers = {
    'Content-Type': TYPES[ext] || 'application/octet-stream',
    // HTML toujours revalidé ; CSS/JS versionnés (?v=) et images/polices : cache long
    'Cache-Control': ext === '.html' ? 'no-cache'
      : ((ext === '.css' || ext === '.js') && !/[?&]v=/.test(req.url)) ? 'public, max-age=3600'
      : 'public, max-age=31536000, immutable',
    ...SECURITY_HEADERS
  };
  if (ext === '.html' && !rawPath.startsWith('/admin')) headers['Content-Security-Policy'] = CSP;
  // adresse de test (…up.railway.app) : pas d'indexation, pour ne pas concurrencer www.bikentour.com
  if (!PROD_HOSTS.includes((req.headers.host || '').split(':')[0].toLowerCase())) headers['X-Robots-Tag'] = 'noindex, nofollow';
  if (rawPath.startsWith('/admin/')) { headers['X-Robots-Tag'] = 'noindex, nofollow'; headers['Cache-Control'] = ext === '.html' ? 'no-cache' : 'public, max-age=86400'; }
  // versions Markdown (pour les assistants IA) : la page HTML reste l'URL de référence
  if (ext === '.md') {
    const rel = '/' + path.relative(ROOT, file).replace(/\\/g, '/').replace(/(index)?\.md$/, '');
    headers.Link = `<https://www.bikentour.com${rel === '/' ? '/' : rel.replace(/\/$/, '')}>; rel="canonical"`;
    headers['Cache-Control'] = 'no-cache';
  }
  const stream = fs.createReadStream(file);
  if (COMPRESS.has(ext) && /\bbr\b/.test(req.headers['accept-encoding'] || '')) {
    res.writeHead(200, { ...headers, 'Content-Encoding': 'br', Vary: 'Accept-Encoding' });
    return stream.pipe(zlib.createBrotliCompress()).pipe(res);
  }
  if (COMPRESS.has(ext) && /\bgzip\b/.test(req.headers['accept-encoding'] || '')) {
    res.writeHead(200, { ...headers, 'Content-Encoding': 'gzip', Vary: 'Accept-Encoding' });
    return stream.pipe(zlib.createGzip()).pipe(res);
  }
  res.writeHead(200, headers);
  stream.pipe(res);
}).listen(PORT, () => console.log(`Bike'N Tour sur http://localhost:${PORT}`));
