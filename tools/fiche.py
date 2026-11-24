"""Fiche PDF d'un itinéraire (A4, texte vectoriel sélectionnable), dans la langue de la page.
Tracé et profil d'altitude dessinés à partir de assets/gpx (gpx_export.py). Envoyée par email avec la trace GPX (server.js, Resend)
et téléchargeable depuis la page de l'itinéraire. Écrit assets/pdf/fiches/<id>-<langue>.pdf."""
import math, os
from reportlab import rl_config
rl_config.invariant = 1  # PDF identique d'une génération à l'autre (pas de date interne) : pas de faux changements dans Git
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, KeepTogether, Flowable
from reportlab.graphics.shapes import Drawing, PolyLine, Circle, String, Rect, Polygon
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics import renderPDF
from xml.sax.saxutils import escape as x_esc

import gpx_export

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
OUT = os.path.join(ROOT, 'assets', 'pdf', 'fiches')
FONT_DIR = os.path.join(TOOLS, 'og')
pdfmetrics.registerFont(TTFont('Mont', os.path.join(FONT_DIR, 'Montserrat-SemiBold.ttf')))
pdfmetrics.registerFont(TTFont('MontB', os.path.join(FONT_DIR, 'Montserrat-ExtraBold.ttf')))

NAVY, NAVY2, YELLOW, PAPER, LINE, MUTED, INK = (colors.HexColor(c) for c in ('#30336E', '#22245A', '#E7C14F', '#F7F5EE', '#E1E0D6', '#62647F', '#1D1F3F'))
ROUTE_COLORS = {'loire': '#3F87C2', 'velodyssee': '#D9962B', 'regalante': '#58895D', 'traversee': '#C9604F', 'canal': '#30336E', 'vignoble': '#8B4F9B'}

S = {
    'h1': ParagraphStyle('h1', fontName='MontB', fontSize=24, leading=28, textColor=NAVY, spaceAfter=4),
    'sub': ParagraphStyle('sub', fontName='Mont', fontSize=11.5, leading=15, textColor=MUTED, spaceAfter=10),
    'h2': ParagraphStyle('h2', fontName='MontB', fontSize=14, leading=18, textColor=NAVY, spaceBefore=12, spaceAfter=6, keepWithNext=1),
    'p': ParagraphStyle('p', fontName='Mont', fontSize=9.6, leading=14, textColor=INK, alignment=TA_LEFT),
    'small': ParagraphStyle('small', fontName='Mont', fontSize=8.2, leading=11.5, textColor=MUTED),
    'k': ParagraphStyle('k', fontName='Mont', fontSize=7.6, leading=10, textColor=MUTED),
    'v': ParagraphStyle('v', fontName='MontB', fontSize=10.5, leading=13, textColor=NAVY),
    'st': ParagraphStyle('st', fontName='MontB', fontSize=10.2, leading=13, textColor=NAVY),
    'white': ParagraphStyle('white', fontName='Mont', fontSize=9.4, leading=13.5, textColor=colors.white),
    'whiteb': ParagraphStyle('whiteb', fontName='MontB', fontSize=13, leading=16, textColor=colors.white),
}


def e(s):
    return x_esc(str(s or '').replace('→', '–'))


class Map(Flowable):
    """Tracé de l'itinéraire, points de vue numérotés et profil d'altitude."""
    def __init__(self, rid, pts_view, w, h, labels):
        super().__init__()
        self.rid, self.pv, self.w, self.h, self.labels = rid, pts_view, w, h, labels

    def wrap(self, *a):
        return self.w, self.h

    def draw(self):
        c = self.canv
        pts = gpx_export.points(self.rid)
        col = colors.HexColor(ROUTE_COLORS.get(self.rid, '#30336E'))
        mh = self.h - 30 * mm  # carte ; profil en dessous
        c.setFillColor(PAPER); c.setStrokeColor(LINE); c.roundRect(0, 30 * mm, self.w, mh, 10, fill=1, stroke=1)
        lons = [p[0] for p in pts] + [p['lon'] for p in self.pv]
        lats = [p[1] for p in pts] + [p['lat'] for p in self.pv]
        k = math.cos(math.radians(sum(lats) / len(lats)))
        x0, x1, y0, y1 = min(lons), max(lons), min(lats), max(lats)
        pad = 12 * mm
        sx = (self.w - 2 * pad) / max((x1 - x0) * k, 1e-6)
        sy = (mh - 2 * pad) / max(y1 - y0, 1e-6)
        s = min(sx, sy)
        ox = (self.w - (x1 - x0) * k * s) / 2
        oy = 30 * mm + (mh - (y1 - y0) * s) / 2
        P = lambda lon, lat: (ox + (lon - x0) * k * s, oy + (lat - y0) * s)
        d = Drawing(self.w, self.h)
        xy = []
        for lon, lat, _ in pts:
            xy += list(P(lon, lat))
        d.add(PolyLine(xy, strokeColor=colors.white, strokeWidth=6, strokeLineCap=1, strokeLineJoin=1))
        d.add(PolyLine(xy, strokeColor=col, strokeWidth=3.2, strokeLineCap=1, strokeLineJoin=1))
        for i, p in enumerate(self.pv):
            x, y = P(p['lon'], p['lat'])
            d.add(Circle(x, y, 7, fillColor=colors.white, strokeColor=NAVY, strokeWidth=1.4))
            d.add(String(x, y - 3, str(i + 1), fontName='MontB', fontSize=7.5, fillColor=NAVY, textAnchor='middle'))
        sxp, syp = P(*pts[0][:2])
        d.add(Circle(sxp, syp, 8.5, fillColor=YELLOW, strokeColor=NAVY, strokeWidth=2))
        d.add(String(sxp + 12, syp - 3.5, self.labels['start'], fontName='MontB', fontSize=8.5, fillColor=NAVY))
        if gpx_export.hav(pts[0], pts[-1]) > 3:
            exp, eyp = P(*pts[-1][:2])
            d.add(Circle(exp, eyp, 6, fillColor=NAVY, strokeColor=colors.white, strokeWidth=2))
            if self.labels.get('end'):
                right = exp < self.w * 0.7
                d.add(String(exp + (10 if right else -10), eyp - 3.5, self.labels['end'], fontName='MontB', fontSize=8.5, fillColor=NAVY, textAnchor='start' if right else 'end'))
        # profil d'altitude
        dist = [0.0]
        for i in range(1, len(pts)):
            dist.append(dist[-1] + gpx_export.hav(pts[i - 1], pts[i]))
        ele = [p[2] for p in pts]
        lo, hi = min(ele), max(ele)
        ph = 20 * mm
        poly = [0, 2 * mm]
        for dd, ee in zip(dist, ele):
            poly += [dd / dist[-1] * self.w, 2 * mm + (ee - lo) / max(hi - lo, 1) * ph]
        poly += [self.w, 2 * mm]
        d.add(Polygon(poly, fillColor=colors.HexColor('#DCEBD9'), strokeColor=colors.HexColor('#58895D'), strokeWidth=1))
        d.add(String(0, 2 * mm + ph + 4, self.labels['profile'].format(lo=round(lo), hi=round(hi), km=round(dist[-1])), fontName='Mont', fontSize=7.5, fillColor=MUTED))
        renderPDF.draw(d, c, 0, 0)


def make(r, x, lang, T, contact, page_url):
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, f"{r['id']}-{lang}.pdf")
    pv = [p for p in (r.get('points') or []) if p.get('lat') not in (None, '') and p.get('lon') not in (None, '')]
    pv = [{**p, 'lat': float(p['lat']), 'lon': float(p['lon'])} for p in pv]
    W, H = A4
    M = 16 * mm

    def first(c, doc):
        c.saveState()
        c.setFillColor(NAVY); c.rect(0, H - 26 * mm, W, 26 * mm, fill=1, stroke=0)
        logo = os.path.join(FONT_DIR, 'logo-blanc.png')
        if os.path.exists(logo):
            c.drawImage(logo, M, H - 19 * mm, width=48 * mm, height=12 * mm, mask='auto', preserveAspectRatio=True, anchor='w')
        c.setFont('MontB', 9); c.setFillColor(YELLOW)
        c.drawRightString(W - M, H - 14.5 * mm, T("Fiche itinéraire").upper())
        footer(c)
        c.restoreState()

    def later(c, doc):
        c.saveState()
        c.setFillColor(NAVY); c.rect(0, H - 9 * mm, W, 9 * mm, fill=1, stroke=0)
        c.setFont('MontB', 8); c.setFillColor(colors.white); c.drawString(M, H - 6 * mm, f"Bike'N Tour · {r['name']}")
        footer(c)
        c.restoreState()

    def footer(c):
        c.setFont('Mont', 7.2); c.setFillColor(MUTED)
        c.drawString(M, 9 * mm, f"Bike'N Tour · {contact['address']} · {contact['phone']} · {contact['email']} · www.bikentour.com")
        c.drawRightString(W - M, 9 * mm, str(c.getPageNumber()))

    doc = BaseDocTemplate(out, pagesize=A4, leftMargin=M, rightMargin=M, topMargin=34 * mm, bottomMargin=18 * mm,
                          title=f"{r['name']} – {T('Fiche itinéraire')} | Bike'N Tour", author="Bike'N Tour", subject=x.get('intro', ''), lang=lang)
    fw = W - 2 * M
    doc.addPageTemplates([PageTemplate('first', [Frame(M, 18 * mm, fw, H - 34 * mm - 18 * mm, id='f1')], onPage=first),
                          PageTemplate('later', [Frame(M, 18 * mm, fw, H - 16 * mm - 18 * mm, id='f2')], onPage=later)])
    from reportlab.platypus import NextPageTemplate
    story = [NextPageTemplate('later'), Paragraph(e(x.get('h1') or r['name']), S['h1']), Paragraph(e(r.get('short') or ''), S['sub'])]

    facts = [(T('Distance'), r['dist']), (T('Durée conseillée'), r['days']), (T('Niveau'), T(r['level'])),
             (T('Aller simple'), T('Oui, sur demande') if r['oneway'] else T('Boucle'))]
    cells = [[Paragraph(e(k), S['k']) for k, _ in facts], [Paragraph(e(v), S['v']) for _, v in facts]]
    t = Table(cells, colWidths=[fw / 4] * 4)
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), PAPER), ('BOX', (0, 0), (-1, -1), 0.6, LINE), ('LINEAFTER', (0, 0), (-2, -1), 0.6, LINE),
                           ('TOPPADDING', (0, 0), (-1, 0), 7), ('BOTTOMPADDING', (0, -1), (-1, -1), 8), ('LEFTPADDING', (0, 0), (-1, -1), 9)]))
    story += [t, Spacer(1, 8)]
    labels = {'start': T("Départ : boutique Bike'N Tour, Nantes"), 'end': (r.get('steps') or [''])[-1] if r.get('oneway') else '', 'profile': T("Profil · altitude de {lo} à {hi} m · {km} km")}
    story += [Map(r['id'], pv, fw, 118 * mm, labels), Spacer(1, 6)]
    story += [Paragraph(e(x.get('intro')), S['p'])]

    if x.get('stages'):
        story.append(Paragraph(e(T('Étapes conseillées')), S['h2']))
        for i, (a, b) in enumerate(x['stages']):
            story.append(KeepTogether([Table([[Paragraph(f'<font color="#30336E">{i + 1}</font>', S['st']), [Paragraph(e(a), S['st']), Paragraph(e(b), S['p'])]]],
                                             colWidths=[9 * mm, fw - 9 * mm], style=[('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)])]))
    if x.get('highlights'):
        story.append(Paragraph(e(T('À ne pas manquer')), S['h2']))
        story += [Paragraph('•&nbsp;&nbsp;' + e(h), S['p']) for h in x['highlights']]
    if pv:
        story.append(Paragraph(e(T('Points de vue sur le parcours')), S['h2']))
        for i, p in enumerate(pv):
            story.append(Paragraph(f'<font name="MontB" color="#30336E">{i + 1}. {e(p.get("nom"))}</font> – {e(p.get("texte"))}', S['p']))
    if x.get('back'):
        story += [Paragraph(e(T('Le retour')), S['h2']), Paragraph(e(x['back']), S['p'])]

    # encadré contact + QR code vers la page de l'itinéraire
    qr = QrCodeWidget(page_url); qr.barWidth = qr.barHeight = 28 * mm
    qd = Drawing(28 * mm, 28 * mm); qd.add(Rect(0, 0, 28 * mm, 28 * mm, fillColor=colors.white, strokeColor=None)); qd.add(qr)
    info = [Paragraph(e(T('Votre vélo vous attend à la boutique')), S['whiteb']), Spacer(1, 4),
            Paragraph(e(contact['address']), S['white']),
            Paragraph(e(f"{T('Téléphone')} {contact['phone']} · WhatsApp {contact['phone']}"), S['white']),
            Paragraph(e(contact['email']), S['white']),
            Paragraph(e(T('Réservation en ligne')) + ' : ' + e(contact['booking'].replace('https://', '')), S['white']),
            Spacer(1, 3), Paragraph(e(T('Trace GPX et carte interactive : scannez le code.')), S['white'])]
    box = Table([[info, qd]], colWidths=[fw - 36 * mm, 36 * mm])
    box.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), NAVY), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('LEFTPADDING', (0, 0), (0, -1), 14),
                             ('TOPPADDING', (0, 0), (-1, -1), 12), ('BOTTOMPADDING', (0, 0), (-1, -1), 12), ('ROUNDEDCORNERS', [10, 10, 10, 10])]))
    story += [Spacer(1, 14), KeepTogether([box])]
    doc.build(story)
    return out
