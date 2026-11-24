"""Icônes Lucide (licence ISC, lucide.dev), en ligne dans les pages : icon('phone')."""
ICONS = {
    'map-pin': '<path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/> <circle cx="12" cy="10" r="3"/>',
    'navigation': '<polygon points="3 11 22 2 13 21 11 13 3 11"/>',
    'phone': '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>',
    'mail': '<rect width="20" height="16" x="2" y="4" rx="2"/> <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
    'message-circle': '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>',
    'clock': '<circle cx="12" cy="12" r="10"/> <polyline points="12 6 12 12 16 14"/>',
    'send': '<path d="M14.536 21.686a.5.5 0 0 0 .937-.024l6.5-19a.496.496 0 0 0-.635-.635l-19 6.5a.5.5 0 0 0-.024.937l7.93 3.18a2 2 0 0 1 1.112 1.11z"/> <path d="m21.854 2.147-10.94 10.939"/>',
    'paperclip': '<path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/>',
    'search': '<circle cx="11" cy="11" r="8"/> <path d="m21 21-4.3-4.3"/>',
    'instagram': '<rect width="20" height="20" x="2" y="2" rx="5" ry="5"/> <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/> <line x1="17.5" x2="17.51" y1="6.5" y2="6.5"/>',
    'facebook': '<path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>',
    'linkedin': '<path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/> <rect width="4" height="12" x="2" y="9"/> <circle cx="4" cy="4" r="2"/>',
    'tram-front': '<rect width="16" height="16" x="4" y="3" rx="2"/> <path d="M4 11h16"/> <path d="M12 3v8"/> <path d="m8 19-2 3"/> <path d="m18 22-2-3"/> <path d="M8 15h.01"/> <path d="M16 15h.01"/>',
    'briefcase': '<path d="M16 20V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/> <rect width="20" height="14" x="2" y="6" rx="2"/>',
    'newspaper': '<path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"/> <path d="M18 14h-8"/> <path d="M15 18h-5"/> <path d="M10 6h8v4h-8V6Z"/>',
    'radio': '<path d="M4.9 19.1C1 15.2 1 8.8 4.9 4.9"/> <path d="M7.8 16.2c-2.3-2.3-2.3-6.1 0-8.5"/> <circle cx="12" cy="12" r="2"/> <path d="M16.2 7.8c2.3 2.3 2.3 6.1 0 8.5"/> <path d="M19.1 4.9C23 8.8 23 15.1 19.1 19"/>',
    'download': '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/> <polyline points="7 10 12 15 17 10"/> <line x1="12" x2="12" y1="15" y2="3"/>',
    'circle-help': '<circle cx="12" cy="12" r="10"/> <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/> <path d="M12 17h.01"/>',
    'arrow-right': '<path d="M5 12h14"/> <path d="m12 5 7 7-7 7"/>',
}


def icon(name, cls="ic"):
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">{ICONS[name]}</svg>'
