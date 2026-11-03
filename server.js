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
  '.webp': 'image/webp', '.md': 'text/markdown; charset=utf-8', '.yml': 'text/yaml; charset=utf-8', '.ico': 'image/x-icon', '.woff2': 'font/woff2'
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
  if (!ADMIN_PASSWORD) return true; // protection désactivée tant que le mot de passe n'est pas défini
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
<img src="/assets/img/logo-horizontal.png" alt="Bike'N Tour" width="340" height="90">
<h1>Administration du site</h1><p>Connectez-vous pour modifier les textes, les tarifs, les photos et le blog.</p>
${error ? `<p class="err" role="alert">${esc(error)}</p>` : ''}
<label>Identifiant<input name="user" autocomplete="username" required autofocus></label>
<label>Mot de passe<input name="password" type="password" autocomplete="current-password" required></label>
<input type="hidden" name="next" value="${esc(next)}">
<button type="submit">Se connecter</button>
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
  const next = /^\/admin\//.test(form.get('next') || '') ? form.get('next') : '/admin/';
  if (ADMIN_PASSWORD && same(form.get('user') || '', ADMIN_USER) && same(form.get('password') || '', ADMIN_PASSWORD)) {
    failures.delete(ip);
    const exp = String(now + SESSION_DAYS * 86400 * 1000);
    res.writeHead(303, { Location: next, 'Cache-Control': 'no-store', ...SECURITY_HEADERS,
      'Set-Cookie': `bnt_admin=${exp}.${sign(exp)}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=${SESSION_DAYS * 86400}` });
    return res.end();
  }
  recent.push(now); failures.set(ip, recent);
  return loginPage(res, { status: 401, error: 'Identifiant ou mot de passe incorrect.', next });
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
      if (req.method === 'POST') return void handleLogin(req, res);
      return loginPage(res);
    }
    if (u.pathname === '/admin/logout') {
      res.writeHead(303, { Location: '/admin/login', ...SECURITY_HEADERS, 'Set-Cookie': 'bnt_admin=deleted; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=0' });
      return res.end();
    }
    if (u.pathname === '/cms/auth' || u.pathname === '/cms/callback') return void cmsAuth(req, res, u);
    if (u.pathname === '/admin' || u.pathname.startsWith('/admin/')) {
      if (!loggedIn(req)) {
        if (u.pathname === '/admin' || u.pathname === '/admin/' || u.pathname.endsWith('.html')) { res.writeHead(303, { Location: '/admin/login', 'Cache-Control': 'no-store', ...SECURITY_HEADERS }); return res.end(); }
        res.writeHead(401, { 'Cache-Control': 'no-store', ...SECURITY_HEADERS }); return res.end();
      }
      if (u.pathname === '/admin/config.yml') return adminConfig(res);
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
