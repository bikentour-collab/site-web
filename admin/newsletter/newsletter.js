(() => {
  const $ = (id) => document.getElementById(id);
  const form = $('form'), frame = $('preview'), msg = $('msg');
  const FIELDS = ['objet', 'apercu', 'titre', 'texte', 'image', 'bouton_texte', 'bouton_lien'];
  const KEY = 'bnt-newsletter-brouillon';
  const data = () => Object.fromEntries(FIELDS.map((f) => [f, $(f).value]));
  const say = (t, kind) => { msg.textContent = t || ''; msg.className = 'nl-msg' + (kind ? ' ' + kind : ''); };
  const post = (action, body) => fetch('/admin/api/newsletter/' + action, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), credentials: 'same-origin' });

  // brouillon conservé dans ce navigateur
  try { const d = JSON.parse(localStorage.getItem(KEY) || 'null'); if (d) FIELDS.forEach((f) => { if (d[f]) $(f).value = d[f]; }); } catch (e) { /* stockage indisponible */ }
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(data())); } catch (e) { /* rien */ } };

  let timer;
  async function refresh() {
    $('pv-objet').textContent = $('objet').value || "Objet de l'email";
    try {
      const r = await post('apercu', data());
      if (r.status === 401) { location.href = '/admin/login?next=/admin/newsletter/'; return; }
      frame.srcdoc = await r.text();
    } catch (e) { /* aperçu indisponible */ }
  }
  form.addEventListener('input', (e) => { if (e.target.getAttribute('aria-invalid')) e.target.removeAttribute('aria-invalid'); save(); clearTimeout(timer); timer = setTimeout(refresh, 350); });
  refresh();

  function valid() {
    const bad = ['objet', 'texte'].filter((f) => !$(f).value.trim());
    bad.forEach((f) => $(f).setAttribute('aria-invalid', 'true'));
    if (bad.length) { $(bad[0]).focus(); say("Renseignez l'objet et le texte.", 'err'); return false; }
    const link = $('bouton_lien').value.trim();
    if (link && !/^https?:\/\//.test(link)) { $('bouton_lien').setAttribute('aria-invalid', 'true'); $('bouton_lien').focus(); say('Le lien du bouton doit commencer par https://', 'err'); return false; }
    return true;
  }

  $('btn-test').addEventListener('click', async () => {
    if (!valid()) return;
    const b = $('btn-test'); b.disabled = true; say('Envoi du test…');
    try { const r = await post('test', { ...data(), email: $('email-test').value.trim() }); const j = await r.json(); say(j.message || (j.ok ? 'Test envoyé.' : "Le test n'est pas parti."), j.ok ? 'ok' : 'err'); }
    catch (e) { say("Le test n'est pas parti. Vérifiez votre connexion.", 'err'); }
    finally { b.disabled = false; }
  });

  const dlg = $('confirm'), cfInput = $('cf-input'), cfOk = $('cf-ok');
  cfInput.addEventListener('input', () => { cfOk.disabled = cfInput.value.trim().toUpperCase() !== 'ENVOYER'; });
  $('btn-send').addEventListener('click', () => {
    if (!valid()) return;
    $('cf-objet').textContent = $('objet').value; cfInput.value = ''; cfOk.disabled = true; dlg.showModal(); cfInput.focus();
  });
  dlg.addEventListener('close', async () => {
    if (dlg.returnValue !== 'ok') return;
    const b = $('btn-send'); b.disabled = true; say('Envoi en cours…');
    try {
      const r = await post('envoyer', { ...data(), confirmation: 'ENVOYER' }); const j = await r.json();
      say(j.message || (j.ok ? 'Newsletter envoyée.' : "L'envoi n'a pas abouti."), j.ok ? 'ok' : 'err');
      if (j.ok) { try { localStorage.removeItem(KEY); } catch (e) { /* rien */ } loadState(); }
    } catch (e) { say("L'envoi n'a pas abouti. Vérifiez votre connexion.", 'err'); }
    finally { b.disabled = false; }
  });

  const STATUS = { sent: 'Envoyée', queued: 'En cours', scheduled: 'Programmée', draft: 'Brouillon' };
  async function loadState() {
    try {
      const r = await fetch('/admin/api/newsletter/etat', { credentials: 'same-origin' });
      if (r.status === 401) { location.href = '/admin/login?next=/admin/newsletter/'; return; }
      const j = await r.json(); const st = $('etat');
      if (!j.resend) { st.textContent = "Resend n'est pas encore configuré : l'envoi est désactivé (variable RESEND_API_KEY)."; st.className = 'nl-state warn'; $('btn-test').disabled = $('btn-send').disabled = true; }
      else if (!j.segment) { st.textContent = 'Tests possibles. Pour envoyer à tous les abonnés, ajoutez la variable RESEND_SEGMENT_ID.'; st.className = 'nl-state warn'; $('btn-send').disabled = true; }
      else { st.textContent = 'Prêt : les envois partent vers tous les abonnés de la newsletter.'; st.className = 'nl-state ok'; }
      if (!$('email-test').value) $('email-test').placeholder = j.contact || '';
      const ul = $('history'); ul.textContent = '';
      if (!j.envois || !j.envois.length) { const li = document.createElement('li'); li.className = 'nl-hint'; li.textContent = j.erreur_historique ? "L'historique n'a pas pu être chargé." : 'Aucune newsletter envoyée pour le moment.'; ul.append(li); return; }
      j.envois.forEach((x) => {
        const li = document.createElement('li'); const n = document.createElement('span'); n.textContent = x.nom;
        const b = document.createElement('span'); b.className = 'nl-badge';
        const d = x.date ? new Date(x.date).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' }) : '';
        b.textContent = [STATUS[x.statut] || x.statut, d].filter(Boolean).join(' · ');
        li.append(n, b); ul.append(li);
      });
    } catch (e) { $('etat').textContent = 'Configuration non vérifiée (connexion).'; }
  }
  loadState();
})();
