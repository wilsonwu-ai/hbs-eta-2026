#!/usr/bin/env python3
"""Generate the HyperFrames project (index.html + compositions/chrome.html + compositions/s1..s8.html) from script.json,
build/timing.json (scene lengths from the real audio) and build/whisper.json (word cues).

Dubbs Capital video palette: navy #08243A, black #000000, white #FFFFFF only (muted text is navy at reduced opacity).
Type: Libre Franklin 400/700. Persistent chrome (watermark top-right, credit bottom-left) lives in compositions/chrome.html.
Numbers on screen come only from the brief and the research ledger (asserted by check_numbers.py). No em or en dashes.
"""
import json, os, re

here = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(here, 'script.json')))
T = json.load(open(os.path.join(here, 'build/timing.json')))
W = json.load(open(os.path.join(here, 'build/whisper.json')))
LEAD = 0.35
TIM = {x['id']: x for x in T['scenes']}
TOTAL = T['total']

# NUMBERS (brief + ledger, SOP 50 10 8.1): effective Oct 1 2026; equity injection 10%; own resources 5% (half of the 10%);
# seller note on full standby up to 5%; DSCR minimum 1.25x for initial acquisitions;
# illustrative $2,000,000 purchase: 90% loan $1,800,000, 5% buyer cash $100,000, 5% standby seller note $100,000.
price, loan, cash, note = 2000000, 1800000, 100000, 100000
assert loan == price * 0.90 and cash == price * 0.05 and note == price * 0.05

NAVY, BLACK, WHITE = '#08243A', '#000000', '#FFFFFF'
MUTED = 'rgba(8,36,58,0.74)'
FAINT = 'rgba(8,36,58,0.30)'


def nrm(w): return re.sub(r'[^a-z0-9]', '', w.lower())


def cue(sid, word, n=1, off=-0.10):
    """scene-relative start time (s) of the n-th spoken occurrence of `word`, plus an offset (visuals lead slightly)."""
    k = 0
    for (w, s, e) in W[sid]['words']:
        if nrm(w) == nrm(word):
            k += 1
            if k == n: return round(max(0.05, LEAD + s + off), 3)
    raise SystemExit('cue not found %s %s %d' % (sid, word, n))


FONT = "@import url('https://fonts.googleapis.com/css2?family=Libre+Franklin:wght@400;700&display=swap');"
CSS = f"""
#root {{ position:absolute; inset:0; font-family:'Libre Franklin',sans-serif; font-weight:700; color:{NAVY}; overflow:hidden; }}
#root .wrap {{ position:absolute; inset:0; }}
#root .t {{ position:absolute; font-weight:700; white-space:nowrap; line-height:1.1; }}
#root .m {{ font-weight:400; }}
#root .box {{ position:absolute; }}
#root .ttl {{ position:absolute; left:120px; top:92px; font-size:68px; font-weight:700; white-space:nowrap; line-height:1.1; letter-spacing:-0.01em; color:{NAVY}; }}
#root .stripe {{ position:absolute; box-sizing:border-box; border:4px solid {NAVY}; background:repeating-linear-gradient(135deg, {NAVY} 0 5px, {WHITE} 5px 16px); }}
#root .dots {{ position:absolute; box-sizing:border-box; border:4px solid {NAVY}; background-color:{WHITE}; background-image:radial-gradient({NAVY} 3.2px, transparent 3.8px); background-size:22px 22px; }}
#root .ghost {{ position:absolute; box-sizing:border-box; border:4px dashed {NAVY}; background:{WHITE}; }}
#root .solid {{ position:absolute; box-sizing:border-box; }}
#root .pill {{ position:absolute; box-sizing:border-box; white-space:nowrap; font-weight:700; text-align:center; }}
"""


def scene(sid, body, js, dur, fin=True, fout=True, extra_css=''):
    FIN = f"tl.fromTo('#{sid}-wrap', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.25, ease: 'power2.out' }}, 0);\n" if fin else ''
    FOUT = f"tl.to('#{sid}-wrap', {{ opacity: 0, duration: 0.2, ease: 'power2.in' }}, D - 0.2);\n" if fout else ''
    return f"""<template>
<style>{FONT}{CSS}{extra_css}</style>
<div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080">
<div class="wrap" id="{sid}-wrap">
{body}</div>
</div>
<script>
(function() {{
const tl = gsap.timeline({{ paused: true }});
const D = {dur};
{FIN}{FOUT}{js}window.__timelines['{sid}'] = tl;
}})();
</script>
</template>
"""


def pop(sel, t, dur=0.55, y=22, ease='power2.out'):
    return f"tl.fromTo('{sel}', {{ opacity: 0, y: {y} }}, {{ opacity: 1, y: 0, duration: {dur}, ease: '{ease}' }}, {t:.3f});\n"


def fade(sel, t, dur=0.4):
    return f"tl.fromTo('{sel}', {{ opacity: 0 }}, {{ opacity: 1, duration: {dur}, ease: 'power2.out' }}, {t:.3f});\n"


def growx(sel, t, dur=0.7, ease='power2.out'):
    return f"tl.fromTo('{sel}', {{ scaleX: 0 }}, {{ scaleX: 1, duration: {dur}, ease: '{ease}' }}, {t:.3f});\n"


def drop(sel, t, dur=0.6, y=-70):
    return f"tl.fromTo('{sel}', {{ opacity: 0, y: {y} }}, {{ opacity: 1, y: 0, duration: {dur}, ease: 'back.out(1.4)' }}, {t:.3f});\n"


def draw(sel, t, dur=0.5):
    return f"tl.fromTo('{sel}', {{ strokeDashoffset: 1100 }}, {{ strokeDashoffset: 0, duration: {dur}, ease: 'power2.out' }}, {t:.3f});\n"


def line(id_, d, w=6, color=NAVY, head=None):
    """an SVG path (drawn on) with an optional arrowhead polygon `head` (points string)."""
    s = (f'<svg class="box" id="{id_}-svg" style="left:0;top:0;" width="1920" height="1080" viewBox="0 0 1920 1080">'
         f'<path id="{id_}" d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round" '
         f'pathLength="1000" stroke-dasharray="1000 1200" stroke-dashoffset="1100"/>')
    if head: s += f'<polygon id="{id_}-h" points="{head}" fill="{color}" opacity="0"/>'
    return s + '</svg>\n'


def t(id_, text, x, y, size, color=NAVY, weight=None, extra=''):
    w = '' if weight is None else f'font-weight:{weight};'
    return f'<div class="t" id="{id_}" style="left:{x}px;top:{y}px;font-size:{size}px;color:{color};{w}{extra}">{text}</div>\n'


def box(id_, cls, x, y, w, h, extra=''):
    return f'<div class="{cls}" id="{id_}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;{extra}"></div>\n'


def centered(id_, text, x, y, w, size, color=NAVY, weight=700):
    return (f'<div class="t" id="{id_}" style="left:{x}px;top:{y}px;width:{w}px;text-align:center;font-size:{size}px;'
            f'color:{color};font-weight:{weight};">{text}</div>\n')


def dur_of(sid): return TIM[sid]['dur']


# ------------------------------------------------------------------ chrome (persistent watermark and credit)
def build_chrome():
    return f"""<template>
<style>{FONT}
#root {{ position:absolute; inset:0; font-family:'Libre Franklin',sans-serif; color:{NAVY}; overflow:hidden; }}
#root .wm {{ position:absolute; right:80px; top:44px; font-size:30px; font-weight:700; letter-spacing:0.34em; text-transform:uppercase; white-space:nowrap; color:{NAVY}; }}
#root .cr {{ position:absolute; left:80px; bottom:34px; font-size:30px; font-weight:400; white-space:nowrap; color:{NAVY}; }}
</style>
<div id="root" data-composition-id="chrome" data-width="1920" data-height="1080">
<div class="wm" id="chrome-wm">Dubbs Capital</div>
<div class="cr" id="chrome-cr">Notes from the HBS ETA Conference 2026</div>
</div>
<script>
(function() {{
const tl = gsap.timeline({{ paused: true }});
tl.set('#chrome-wm', {{ opacity: 1 }}, 0);
tl.set('#chrome-cr', {{ opacity: 1 }}, 0);
window.__timelines['chrome'] = tl;
}})();
</script>
</template>
"""


# ------------------------------------------------------------------ equity bar used by s3 to s6 (zoomed 10%)
BX, BW = 210, 1500          # bar left and width
HALF = BW // 2


# ------------------------------------------------------------------ s1: what a 7(a) loan is
def s1():
    sid = 's1'; D = dur_of(sid)
    body = t('s1-ttl', 'SBA 7(a) acquisition loan', 120, 92, 68, extra='letter-spacing:-0.01em;')
    # Bank (centre), Buyer (right), SBA (left)
    body += box('s1-bank', 'solid', 740, 360, 440, 150, f'background:{NAVY};border-radius:14px;')
    body += centered('s1-bank-t', 'Bank', 740, 410, 440, 56, WHITE)
    body += box('s1-buy', 'solid', 1360, 360, 440, 150, f'background:{WHITE};border:5px solid {NAVY};border-radius:14px;')
    body += centered('s1-buy-t', 'You, buying<br>a business', 1360, 385, 440, 46, NAVY)
    body += box('s1-sba', 'solid', 120, 360, 440, 150, f'background:{WHITE};border:5px solid {NAVY};border-radius:14px;')
    body += centered('s1-sba-t', 'U.S. Small Business<br>Administration', 120, 385, 440, 42, NAVY)
    body += line('s1-ar1', 'M 1186 435 L 1290 435', 7, NAVY, '1284,410 1340,435 1284,460')
    body += centered('s1-ar1-t', 'loan', 1180, 530, 180, 46, NAVY)
    body += line('s1-ar2', 'M 566 435 L 670 435', 7, NAVY, '664,410 720,435 664,460')
    body += centered('s1-ar2-t', 'partly<br>guarantees', 540, 530, 200, 40, NAVY)
    body += box('s1-chip', 'pill', 380, 760, 1160, 120, f'background:{NAVY};border-radius:60px;')
    body += centered('s1-chip-t', 'New rules effective October 1, 2026', 380, 791, 1160, 56, WHITE)
    body += centered('s1-sop', 'SBA SOP 50 10 8.1', 380, 910, 1160, 40, MUTED, 400)
    js = pop('#s1-ttl', 0.30, 0.7)
    js += fade('#s1-bank', cue(sid, 'bank', 1)); js += fade('#s1-bank-t', cue(sid, 'bank', 1) + 0.1)
    js += fade('#s1-buy', cue(sid, 'loan', 2) + 0.1); js += fade('#s1-buy-t', cue(sid, 'loan', 2) + 0.2)
    js += draw('#s1-ar1', cue(sid, 'loan', 2)); js += fade('#s1-ar1-h', cue(sid, 'loan', 2) + 0.35, 0.2)
    js += pop('#s1-ar1-t', cue(sid, 'loan', 2) + 0.25, 0.4, 10)
    js += fade('#s1-sba', cue(sid, 'U', 1)); js += fade('#s1-sba-t', cue(sid, 'U', 1) + 0.1)
    js += draw('#s1-ar2', cue(sid, 'partly', 1)); js += fade('#s1-ar2-h', cue(sid, 'partly', 1) + 0.35, 0.2)
    js += pop('#s1-ar2-t', cue(sid, 'partly', 1) + 0.1, 0.4, 10)
    js += pop('#s1-chip', cue(sid, 'rules', 1), 0.55, 24); js += pop('#s1-chip-t', cue(sid, 'rules', 1) + 0.1, 0.5, 14)
    js += pop('#s1-sop', cue(sid, 'October', 1) + 0.2, 0.5, 10)
    return scene(sid, body, js, D)


# ------------------------------------------------------------------ s2: the 10% equity injection
def s2():
    sid = 's2'; D = dur_of(sid)
    eqw = BW // 10                              # 150 px = 10%
    lw = BW - eqw
    body = t('s2-ttl', 'The equity injection', 120, 92, 68)
    body += box('s2-loan', 'solid', BX, 470, lw, 150, f'background:{NAVY};border-radius:12px 0 0 12px;transform-origin:0% 50%;')
    body += centered('s2-loan-t', 'Bank loan  90%', BX, 515, lw, 56, WHITE)
    body += box('s2-eq', 'solid', BX + lw, 470, eqw, 150, f'background:{BLACK};border-radius:0 12px 12px 0;')
    body += line('s2-lead', f'M {BX + lw + eqw // 2} 456 L {BX + lw + eqw // 2} 392', 6, BLACK)
    body += f'<div class="t" id="s2-big" style="left:1100px;top:226px;width:{BX + BW - 1100}px;text-align:right;font-size:150px;line-height:1;letter-spacing:-0.02em;">10%</div>\n'
    body += f'<div class="t m" id="s2-big-l" style="left:900px;top:196px;width:{BX + BW - 900 - 360}px;text-align:right;font-size:52px;line-height:1.15;">equity<br>injection</div>\n'
    body += line('s2-brk', f'M {BX} 650 L {BX} 676 L {BX + BW} 676 L {BX + BW} 650', 5, NAVY)
    body += centered('s2-brk-t', 'Total project cost', BX, 696, BW, 48, NAVY, 400)
    body += box('s2-pill', 'pill', 360, 830, 1200, 104, f'background:{WHITE};border:5px solid {NAVY};border-radius:52px;')
    body += centered('s2-pill-t', 'Cannot be reduced or eliminated', 360, 856, 1200, 52, NAVY)
    body += centered('s2-pill-s', 'for a first acquisition', 360, 950, 1200, 38, MUTED, 400)
    js = pop('#s2-ttl', 0.25, 0.7)
    js += fade('#s2-eq', cue(sid, '10', 1)); js += pop('#s2-big', cue(sid, '10', 1), 0.5, 18)
    js += draw('#s2-lead', cue(sid, '10', 1) + 0.2, 0.4)
    js += fade('#s2-brk-svg', cue(sid, 'project', 1), 0.5); js += draw('#s2-brk', cue(sid, 'project', 1), 0.6)
    js += fade('#s2-brk-t', cue(sid, 'project', 1) + 0.2, 0.5)
    js += pop('#s2-big-l', cue(sid, 'equity', 2), 0.5, 12)
    js += growx('#s2-loan', cue(sid, 'alongside', 1), 0.8); js += fade('#s2-loan-t', cue(sid, 'alongside', 1) + 0.6, 0.5)
    js += pop('#s2-pill', cue(sid, 'reduced', 1) - 0.4, 0.5, 20); js += pop('#s2-pill-t', cue(sid, 'reduced', 1) - 0.3, 0.5, 12)
    js += pop('#s2-pill-s', cue(sid, 'first', 1), 0.5, 10)
    return scene(sid, body, js, D)


# ------------------------------------------------------------------ s3: half of it from your own resources
def s3():
    sid = 's3'; D = dur_of(sid)
    body = t('s3-ttl', 'Half must be your own', 120, 92, 68)
    body += centered('s3-cap', 'The 10% equity injection', BX, 300, BW, 50, MUTED, 400)
    body += box('s3-frame', 'solid', BX - 6, 404, BW + 12, 172, f'border:6px solid {NAVY};border-radius:18px;')
    body += box('s3-own', 'solid', BX, 410, HALF, 160, f'background:{BLACK};border-radius:12px 0 0 12px;transform-origin:0% 50%;')
    body += centered('s3-own-t', '5%', BX, 438, HALF, 100, WHITE)
    body += box('s3-oth', 'ghost', BX + HALF, 410, HALF, 160, 'border-radius:0 12px 12px 0;')
    body += centered('s3-oth-t', '5%', BX + HALF, 438, HALF, 100, FAINT)
    body += centered('s3-l1', 'Your own resources', BX, 640, HALF, 56, NAVY)
    body += centered('s3-l2', 'such as cash that isn\'t borrowed', BX, 716, HALF, 44, MUTED, 400)
    js = pop('#s3-ttl', 0.2, 0.7); js += fade('#s3-cap', 0.4); js += fade('#s3-frame', 0.4)
    js += growx('#s3-own', cue(sid, '5', 1), 0.7); js += fade('#s3-own-t', cue(sid, '5', 1) + 0.35, 0.4)
    js += fade('#s3-oth', cue(sid, 'half', 1), 0.5); js += fade('#s3-oth-t', cue(sid, 'half', 1) + 0.2, 0.5)
    js += pop('#s3-l1', cue(sid, 'resources', 1) - 0.6, 0.5, 14)
    js += pop('#s3-l2', cue(sid, 'cash', 1), 0.5, 12)
    return scene(sid, body, js, D)


# ------------------------------------------------------------------ s4: the other 5%, a seller note on full standby
def s4():
    sid = 's4'; D = dur_of(sid)
    y0 = 230
    body = t('s4-ttl', 'The other 5%: a seller note', 120, 92, 68)
    body += box('s4-own', 'solid', BX, y0, HALF, 130, f'background:{BLACK};border-radius:12px 0 0 12px;')
    body += centered('s4-own-t', '5%', BX, y0 + 20, HALF, 90, WHITE)
    body += box('s4-note', 'stripe', BX + HALF, y0, HALF, 130, 'border-radius:0 12px 12px 0;')
    body += box('s4-note-chip', 'solid', BX + HALF + 250, y0 + 25, 250, 80, f'background:{WHITE};border-radius:10px;')
    body += centered('s4-note-t', '5%', BX + HALF + 250, y0 + 28, 250, 74, NAVY)
    body += centered('s4-own-l', 'Your own cash', BX, y0 + 150, HALF, 44, NAVY)
    body += centered('s4-note-l', 'Seller note', BX + HALF, y0 + 150, HALF, 44, NAVY)
    body += t('s4-head', 'Full standby for the life of the loan', BX, 520, 56)
    body += box('s4-loan', 'solid', BX, 610, 1240, 74, f'background:{NAVY};border-radius:10px;transform-origin:0% 50%;')
    body += t('s4-loan-t', 'Bank loan', BX + 24, 626, 40, WHITE)
    body += box('s4-sn', 'stripe', BX, 712, 1240, 74, 'border-radius:10px;transform-origin:0% 50%;')
    body += box('s4-sn-chip', 'solid', BX + 330, 724, 580, 50, f'background:{WHITE};border-radius:8px;')
    body += centered('s4-sn-t', 'No payments to the seller', BX + 330, 726, 580, 40, NAVY)
    body += f'<div class="box" id="s4-end" style="left:{BX + 1240}px;top:584px;width:6px;height:230px;background:{BLACK};"></div>\n'
    body += centered('s4-end-t', 'Bank loan repaid', BX + 1240 - 200, 824, 400, 40, NAVY)
    js = pop('#s4-ttl', 0.2, 0.7)
    js += growx('#s4-own', cue(sid, '5', 1), 0.6); js += fade('#s4-own-t', cue(sid, '5', 1) + 0.35, 0.4)
    js += pop('#s4-own-l', cue(sid, '5', 1) + 0.5, 0.4, 10)
    js += fade('#s4-note', cue(sid, 'seller', 1), 0.5); js += fade('#s4-note-chip', cue(sid, 'seller', 1) + 0.2, 0.4)
    js += fade('#s4-note-t', cue(sid, 'seller', 1) + 0.25, 0.4); js += pop('#s4-note-l', cue(sid, 'seller', 1) + 0.3, 0.4, 10)
    js += pop('#s4-head', cue(sid, 'full', 1), 0.55, 16)
    js += growx('#s4-loan', cue(sid, 'life', 1), 0.9); js += fade('#s4-loan-t', cue(sid, 'life', 1) + 0.3, 0.4)
    js += growx('#s4-sn', cue(sid, 'life', 1) + 0.25, 0.9)
    js += fade('#s4-sn-chip', cue(sid, 'no', 1), 0.4); js += fade('#s4-sn-t', cue(sid, 'no', 1) + 0.05, 0.4)
    js += fade('#s4-end', cue(sid, 'repaid', 1) - 0.8, 0.5); js += pop('#s4-end-t', cue(sid, 'repaid', 1) - 0.7, 0.5, 10)
    return scene(sid, body, js, D)


# ------------------------------------------------------------------ s5: a bigger seller note is tested by DSCR
def s5():
    sid = 's5'; D = dur_of(sid)
    base, ch, ph, sh = 900, 520, 330, 86      # baseline y, cash flow height, payment height, seller-note stripe height (ratio 520/416 = 1.25)
    assert abs(ch / (ph + sh) - 1.25) < 1e-9
    body = t('s5-ttl', 'A bigger seller note: the DSCR test', 120, 92, 68)
    body += box('s5-cf', 'solid', 220, base - ch, 260, ch, f'background:{NAVY};border-radius:10px 10px 0 0;transform-origin:50% 100%;')
    body += centered('s5-cf-l', 'Cash flow', 120, base + 20, 460, 46, NAVY)
    body += box('s5-pay', 'solid', 640, base - ph, 260, ph, f'background:{BLACK};transform-origin:50% 100%;')
    body += box('s5-sn', 'stripe', 640, base - ph - sh, 260, sh, 'border-radius:10px 10px 0 0;')
    body += centered('s5-pay-l', 'Loan payments', 540, base + 20, 460, 46, NAVY)
    body += centered('s5-sn-l', 'seller note counts here', 520, base - ph - sh - 62, 500, 38, NAVY, 400)
    body += box('s5-base', 'box', 160, base, 800, 5, f'background:{NAVY};')
    body += t('s5-dscr', 'DSCR', 1150, 232, 130, extra='letter-spacing:-0.02em;line-height:1;')
    body += t('s5-dscr-l', 'debt service coverage ratio', 1150, 372, 48, MUTED, 400)
    body += centered('s5-f1', 'Cash flow', 1150, 478, 620, 62, NAVY)
    body += box('s5-rule', 'box', 1150, 560, 620, 7, f'background:{NAVY};transform-origin:0% 50%;')
    body += centered('s5-f2', 'Loan payments', 1150, 584, 620, 62, NAVY)
    body += t('s5-min', 'at least', 1150, 726, 46, MUTED, 400)
    body += t('s5-min-n', '1.25x', 1150, 780, 150, extra='letter-spacing:-0.02em;line-height:1;')
    js = pop('#s5-ttl', 0.2, 0.7)
    js += fade('#s5-base', 0.5, 0.4)
    js += fade('#s5-pay', cue(sid, 'seller', 1), 0.4); js += fade('#s5-pay-l', cue(sid, 'seller', 1), 0.4)
    js += drop('#s5-sn', cue(sid, 'not', 1) - 0.1, 0.6, -80); js += pop('#s5-sn-l', cue(sid, 'not', 1) + 0.4, 0.4, 10)
    js += f"tl.fromTo('#s5-cf', {{ scaleY: 0 }}, {{ scaleY: 1, duration: 0.8, ease: 'power2.out' }}, {cue(sid, 'cash', 1):.3f});\n"
    js += fade('#s5-cf-l', cue(sid, 'cash', 1) + 0.2, 0.4)
    js += pop('#s5-dscr', cue(sid, 'DSCR', 1), 0.55, 18)
    js += pop('#s5-dscr-l', cue(sid, 'debt', 1), 0.55, 12)
    js += pop('#s5-f1', cue(sid, 'cash', 2) - 0.1, 0.5, 12)
    js += growx('#s5-rule', cue(sid, 'divided', 1), 0.5); js += pop('#s5-f2', cue(sid, 'payments', 1) - 0.4, 0.5, 12)
    js += pop('#s5-min', cue(sid, 'least', 1) - 0.1, 0.4, 10); js += pop('#s5-min-n', cue(sid, 'least', 1) + 0.15, 0.6, 18)
    return scene(sid, body, js, D)


# ------------------------------------------------------------------ s6: investors can fund part of the 10%
def s6():
    sid = 's6'; D = dur_of(sid)
    body = t('s6-ttl', 'Investors can fund part of it', 120, 92, 68)
    body += centered('s6-cap', 'The 10% equity injection', BX, 300, BW, 50, MUTED, 400)
    body += box('s6-frame', 'solid', BX - 6, 404, BW + 12, 172, f'border:6px solid {NAVY};border-radius:18px;')
    body += box('s6-own', 'solid', BX, 410, HALF, 160, f'background:{BLACK};border-radius:12px 0 0 12px;')
    body += centered('s6-own-t', '5%', BX, 438, HALF, 100, WHITE)
    body += box('s6-inv', 'dots', BX + HALF, 410, HALF, 160, 'border-radius:0 12px 12px 0;')
    body += box('s6-inv-chip', 'solid', BX + HALF + 250, 436, 250, 108, f'background:{WHITE};border-radius:10px;')
    body += centered('s6-inv-t', 'Investors', BX + HALF + 250, 462, 250, 52, NAVY)
    body += centered('s6-own-l', 'Your own resources', BX, 610, HALF, 48, NAVY)
    body += centered('s6-inv-l', 'Investor equity', BX + HALF, 610, HALF, 48, NAVY)
    body += box('s6-c1', 'pill', 300, 740, 560, 110, f'background:{WHITE};border:5px solid {NAVY};border-radius:55px;')
    body += centered('s6-c1-t', 'Minority owners', 300, 770, 560, 52, NAVY)
    body += box('s6-c2', 'pill', 910, 740, 880, 110, f'background:{NAVY};border-radius:55px;')
    body += centered('s6-c2-t', 'Tax distributions only until repaid', 910, 772, 880, 48, WHITE)
    js = pop('#s6-ttl', 0.2, 0.7); js += fade('#s6-cap', 0.4); js += fade('#s6-frame', 0.4)
    js += fade('#s6-own', 0.5, 0.5); js += fade('#s6-own-t', 0.6, 0.4); js += pop('#s6-own-l', 0.8, 0.4, 10)
    js += fade('#s6-inv', cue(sid, 'Investors', 1), 0.6); js += fade('#s6-inv-chip', cue(sid, 'Investors', 1) + 0.2, 0.4)
    js += fade('#s6-inv-t', cue(sid, 'Investors', 1) + 0.25, 0.4); js += pop('#s6-inv-l', cue(sid, 'Investors', 1) + 0.3, 0.4, 10)
    js += pop('#s6-c1', cue(sid, 'minority', 1) - 0.1, 0.5, 18); js += pop('#s6-c1-t', cue(sid, 'minority', 1), 0.5, 12)
    js += pop('#s6-c2', cue(sid, 'only', 1) - 0.5, 0.5, 18); js += pop('#s6-c2-t', cue(sid, 'only', 1) - 0.4, 0.5, 12)
    return scene(sid, body, js, D)


# ------------------------------------------------------------------ s7: the illustrative $2,000,000 capital stack
def s7():
    sid = 's7'; D = dur_of(sid)
    sx, sw, top, H = 170, 470, 250, 700           # stack: x, width, top y, total height (= $2,000,000)
    hl, hc, hn = H * 0.90, H * 0.05, H * 0.05     # 630 / 35 / 35
    yn, yc, yl = top, top + hn, top + hn + hc
    body = t('s7-ttl', 'An illustrative $2,000,000 purchase', 120, 92, 68)
    body += box('s7-loan', 'solid', sx, yl, sw, hl, f'background:{NAVY};border-radius:0 0 10px 10px;')
    body += box('s7-cash', 'solid', sx, yc, sw, hc, f'background:{BLACK};border-top:3px solid {WHITE};')
    body += box('s7-note', 'stripe', sx, yn, sw, hn, 'border-radius:10px 10px 0 0;')
    # right-hand rows: name, percent, amount
    rx, px, ax = 790, 1230, 1440
    def row(k, name, pct, amt, y, color):
        r = f'<div class="t" id="s7-{k}-n" style="left:{rx}px;top:{y + 14}px;font-size:44px;color:{color};">{name}</div>\n'
        r += f'<div class="t" id="s7-{k}-p" style="left:{px}px;top:{y}px;font-size:68px;color:{color};line-height:1;">{pct}</div>\n'
        r += f'<div class="t" id="s7-{k}-a" style="left:{ax}px;top:{y}px;font-size:68px;color:{color};line-height:1;letter-spacing:-0.02em;">{amt}</div>\n'
        return r
    body += row('note', 'Standby seller note', '5%', '$100,000', 222, NAVY)
    body += row('cash', 'Your own cash', '5%', '$100,000', 350, NAVY)
    body += row('loan', 'Bank loan', '90%', '$1,800,000', 590, NAVY)
    body += line('s7-ln', f'M {sx + sw + 10} {yn + hn / 2} L {rx - 20} 262', 4, NAVY)
    body += line('s7-lc', f'M {sx + sw + 10} {yc + hc / 2} L {rx - 20} 390', 4, NAVY)
    body += line('s7-ll', f'M {sx + sw + 10} {yl + hl / 2} L {rx - 20} 628', 4, NAVY)
    body += t('s7-tot', 'SBA 7(a) loan', rx, 676, 40, MUTED, 400)
    body += box('s7-chip', 'pill', 1290, 800, 440, 80, f'background:{NAVY};border-radius:40px;')
    body += centered('s7-chip-t', 'Illustrative', 1290, 818, 440, 44, WHITE)
    js = pop('#s7-ttl', 0.2, 0.7)
    js += pop('#s7-chip', cue(sid, 'illustrative', 1), 0.5, 14); js += pop('#s7-chip-t', cue(sid, 'illustrative', 1) + 0.05, 0.5, 8)
    js += f"tl.fromTo('#s7-loan', {{ opacity: 0, y: -90 }}, {{ opacity: 1, y: 0, duration: 0.7, ease: 'back.out(1.2)' }}, {cue(sid, 'loan', 1):.3f});\n"
    js += draw('#s7-ll', cue(sid, 'loan', 1) + 0.5, 0.4)
    js += pop('#s7-loan-n', cue(sid, 'loan', 1) + 0.5, 0.4, 10); js += pop('#s7-loan-p', cue(sid, '90', 1) - 0.05, 0.45, 12)
    js += pop('#s7-loan-a', cue(sid, '1', 1) - 0.05, 0.5, 12)
    js += fade('#s7-tot', cue(sid, '1', 1) + 0.4, 0.4)
    js += drop('#s7-cash', cue(sid, 'cash', 1) - 0.2, 0.55, -90); js += draw('#s7-lc', cue(sid, 'cash', 1) + 0.2, 0.4)
    js += pop('#s7-cash-n', cue(sid, 'cash', 1) + 0.15, 0.4, 10); js += pop('#s7-cash-p', cue(sid, '5', 1) - 0.05, 0.45, 12)
    js += pop('#s7-cash-a', cue(sid, '100', 1) - 0.05, 0.5, 12)
    js += drop('#s7-note', cue(sid, 'standby', 1) - 0.2, 0.55, -90); js += draw('#s7-ln', cue(sid, 'standby', 1) + 0.2, 0.4)
    js += pop('#s7-note-n', cue(sid, 'standby', 1) + 0.15, 0.4, 10); js += pop('#s7-note-p', cue(sid, '5', 2) - 0.05, 0.45, 12)
    js += pop('#s7-note-a', cue(sid, '100', 2) - 0.05, 0.5, 12)
    return scene(sid, body, js, D)


# ------------------------------------------------------------------ s8: end card
def s8():
    sid = 's8'; D = dur_of(sid)
    x0, w = 170, 270
    body = box('s8-loan', 'solid', x0, 330, w, 500, f'background:{NAVY};border-radius:0 0 10px 10px;transform-origin:50% 100%;')
    body += box('s8-cash', 'solid', x0, 300, w, 30, f'background:{BLACK};border-top:3px solid {WHITE};')
    body += box('s8-note', 'stripe', x0, 270, w, 30, 'border-radius:10px 10px 0 0;')
    body += t('s8-t1', 'The new SBA rules', 560, 250, 112, extra='letter-spacing:-0.02em;')
    body += t('s8-t2', 'for buying a business', 560, 382, 112, extra='letter-spacing:-0.02em;')
    body += box('s8-rule', 'box', 564, 540, 520, 8, f'background:{NAVY};border-radius:4px;transform-origin:0% 50%;')
    body += t('s8-d1', 'Confirm with your lender.', 560, 590, 64)
    body += t('s8-d2', 'Illustrative example. Not advice.', 560, 684, 48, MUTED, 400)
    body += t('s8-url', 'Dubbs Capital · wilsonwu-ai.github.io/hbs-eta-2026', 170, 880, 58)
    js = growx('#s8-loan', 0.2, 0.8).replace("scaleX", "scaleY")
    js += drop('#s8-cash', 0.85, 0.45, -40) + drop('#s8-note', 1.05, 0.45, -40)
    js += pop('#s8-t1', cue(sid, 'new', 1) - 0.2, 0.7, 20); js += pop('#s8-t2', cue(sid, 'rules', 1) + 0.1, 0.7, 20)
    js += growx('#s8-rule', cue(sid, 'business', 1) - 0.3, 0.6)
    js += pop('#s8-d1', cue(sid, 'confirm', 1) - 0.1, 0.6, 14); js += pop('#s8-d2', cue(sid, 'confirm', 1) + 0.6, 0.55, 12)
    js += pop('#s8-url', cue(sid, 'business', 1) - 0.2, 0.6, 14)
    return scene(sid, body, js, D, fout=False)


# ------------------------------------------------------------------ assemble
os.makedirs(os.path.join(here, 'compositions'), exist_ok=True)
for sid, fn in [('s1', s1), ('s2', s2), ('s3', s3), ('s4', s4), ('s5', s5), ('s6', s6), ('s7', s7), ('s8', s8)]:
    open(os.path.join(here, 'compositions', sid + '.html'), 'w').write(fn())
open(os.path.join(here, 'compositions', 'chrome.html'), 'w').write(build_chrome())

rows = ''
for sc in T['scenes']:
    sid = sc['id']
    rows += (f'<div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{sc["start"]}" '
             f'data-duration="{sc["dur"]}" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080"></div>\n')
index = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1920, height=1080" />
<script src="assets/gsap.min.js"></script>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1920px; height:1080px; overflow:hidden; background:#FFFFFF; }}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080">
{rows}<div id="chrome" data-composition-id="chrome" data-composition-src="compositions/chrome.html" data-start="0" data-duration="{TOTAL}" data-track-index="3" data-track-kind="graphics" data-width="1920" data-height="1080"></div>
<audio id="narration" src="assets/narration.wav" data-start="0" data-duration="{TOTAL}" data-track-index="2" data-volume="1"></audio>
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
window.__timelines['main'] = tl;
</script>
</body>
</html>
"""
open(os.path.join(here, 'index.html'), 'w').write(index)
for f in os.listdir(os.path.join(here, 'compositions')):
    s = open(os.path.join(here, 'compositions', f)).read() + index
    assert '—' not in s and '–' not in s, f
print('built', TOTAL)
