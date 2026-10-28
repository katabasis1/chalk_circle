"""Generates all game art (SVG + a few PNG) for Chalk Circle. Run: python3 tools/gen_art.py"""
import math, random, os
import numpy as np
from PIL import Image
random.seed(7)
OUT = 'assets/art'
def svg(w, h, body, defs=''):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs>{defs}</defs>{body}</svg>'
def save(name, s):
    with open(f'{OUT}/{name}', 'w') as f: f.write(s)
def rg(id, stops, cx='.5', cy='.5', r='.5', extra=''):
    st = ''.join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in stops)
    return f'<radialGradient id="{id}" cx="{cx}" cy="{cy}" r="{r}" {extra}>{st}</radialGradient>'
def lg(id, stops, x1=0, y1=0, x2=0, y2=1):
    st = ''.join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in stops)
    return f'<linearGradient id="{id}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{st}</linearGradient>'
def glow_eye(cx, cy, r, gid, core='#fff3c4'):
    return f'<circle cx="{cx}" cy="{cy}" r="{r*3}" fill="url(#{gid})"/><circle cx="{cx}" cy="{cy}" r="{r}" fill="{core}"/>'
EYE_W = rg('eyeW', [(0, '#fff6d0', 1), (.2, '#ffd25a', .9), (.55, '#ff7a1a', .35), (1, '#ff3b00', 0)])
EYE_R = rg('eyeR', [(0, '#ffd0c0', 1), (.2, '#ff3b2a', .9), (.55, '#c00000', .35), (1, '#800000', 0)])
EYE_C = rg('eyeC', [(0, '#ffffff', 1), (.2, '#bff3ff', .9), (.55, '#5fd0ff', .3), (1, '#2080ff', 0)])
BODY = rg('body', [(0, '#231820', 1), (.75, '#0d090c', 1), (1, '#050405', 1)], cy='.4', r='.65')
RIM = 'stroke="#5a2436" stroke-width="3" stroke-opacity=".85"'

# ---------- fractal dead tree ----------
def branch(x, y, ang, length, width, depth, out, bias):
    if depth == 0 or length < 6: return
    x2 = x + math.cos(ang) * length; y2 = y + math.sin(ang) * length
    mx = (x + x2) / 2 + random.uniform(-.18, .18) * length; my = (y + y2) / 2 + random.uniform(-.18, .18) * length
    out.append(f'<path d="M{x:.0f} {y:.0f}Q{mx:.0f} {my:.0f} {x2:.0f} {y2:.0f}" stroke-width="{width:.1f}"/>')
    n = 2 if random.random() < .8 else 3
    for i in range(n):
        da = random.uniform(.25, .7) * (1 if i % 2 else -1) + bias * .15
        branch(x2, y2, ang + da, length * random.uniform(.62, .8), width * .68, depth - 1, out, bias)

def tree(x, y, h, bias, color='#020303'):
    out = []; branch(x, y, -math.pi / 2 + bias * .25, h, h * .16, 7, out, bias)
    return f'<g fill="none" stroke="{color}" stroke-linecap="round">{"".join(out)}</g>'

def spruce_line(y0, hmin, hmax, step, color, x0=0, x1=2048):
    pts = [f'M{x0} 1280L{x0} {y0}']; x = x0
    while x < x1:
        h = random.uniform(hmin, hmax); w = step * random.uniform(.7, 1.3)
        pts.append(f'L{x + w * .5:.0f} {y0 - h:.0f}L{x + w:.0f} {y0 - random.uniform(0, 20):.0f}'); x += w
    pts.append(f'L{x1} 1280Z'); return f'<path d="{"".join(pts)}" fill="{color}"/>'

def background():
    defs = (lg('sky', [(0, '#030406', 1), (.42, '#0a0f13', 1), (.66, '#17211e', 1), (1, '#060807', 1)])
            + rg('halo', [(0, '#d7e0c4', .45), (.2, '#9fb39a', .17), (1, '#0b1014', 0)], '1024', '250', '560', 'gradientUnits="userSpaceOnUse"')
            + rg('moon', [(0, '#f6f2de', 1), (.75, '#ddd6b9', 1), (1, '#b3ab8a', 1)], '.42', '.38', '.7')
            + rg('clear', [(0, '#26302b', .85), (.5, '#121815', .6), (1, '#050606', 0)], '1024', '960', '620', 'gradientUnits="userSpaceOnUse"')
            + lg('mist', [(0, '#9fb3a8', 0), (.5, '#9fb3a8', .13), (1, '#9fb3a8', 0)])
            + rg('win', [(0, '#ffcf7a', .9), (.3, '#ff9a2a', .35), (1, '#ff7a00', 0)]))
    b = ['<rect width="2048" height="1280" fill="url(#sky)"/>']
    for _ in range(160):
        x, y = random.uniform(0, 2048), random.uniform(0, 620); r = random.choice([.8, 1, 1.2, 1.6, 2.2])
        b.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#dfe8ff" opacity="{random.uniform(.15, .7):.2f}"/>')
    b.append('<circle cx="1024" cy="250" r="560" fill="url(#halo)"/><circle cx="1024" cy="250" r="104" fill="url(#moon)"/>')
    b.append('<g fill="#9c9474" opacity=".35"><circle cx="992" cy="226" r="19"/><circle cx="1052" cy="276" r="12"/><circle cx="1046" cy="206" r="8"/><circle cx="986" cy="286" r="10"/><circle cx="1070" cy="240" r="6"/></g>')
    b.append('<g fill="#06090c" opacity=".88"><path d="M640 292q160-30 330-10t360 2q120 4 230 18q-150 16-330 12t-350-8q-140-2-240-14z"/><path d="M820 196q120-18 240-6t220 0q-90 14-220 12t-240-6z" opacity=".7"/><path d="M500 360q200-20 420-6t520 4q-200 18-460 14t-480-12z" opacity=".6"/></g>')
    b.append(spruce_line(770, 50, 150, 46, '#0e1513'))
    b.append(f'<rect y="700" width="2048" height="140" fill="url(#mist)"/>')
    # izba with lit window
    b.append('<g fill="#070a09"><path d="M1196 790l0-62l46-40l46 40l0 62z"/><rect x="1236" y="660" width="10" height="34"/></g>'
             '<circle cx="1242" cy="748" r="40" fill="url(#win)"/><rect x="1234" y="740" width="16" height="16" fill="#ffc46a"/><path d="M1242 740v16M1234 748h16" stroke="#3a2010" stroke-width="2"/>')
    b.append(spruce_line(850, 90, 260, 70, '#070b0a'))
    b.append('<rect y="840" width="2048" height="440" fill="#040505"/><ellipse cx="1024" cy="960" rx="760" ry="230" fill="url(#clear)"/>')
    # fence with horse skulls
    f = []
    for i, x in enumerate(range(560, 1500, 64)):
        if 900 < x < 1150: continue
        lean = random.uniform(-6, 6); hgt = random.uniform(90, 130)
        f.append(f'<path d="M{x} 900L{x + lean:.0f} {900 - hgt:.0f}" stroke="#050606" stroke-width="12" stroke-linecap="round"/>')
        if i % 3 == 0:
            sx, sy = x + lean, 900 - hgt - 10
            f.append(f'<g transform="translate({sx:.0f} {sy:.0f})"><path d="M-9 -4q0-16 9-20q9 4 9 20l-3 26q-6 6-12 0z" fill="#b9b3a0"/><circle cx="-4" cy="-6" r="2.6" fill="#050505"/><circle cx="4" cy="-6" r="2.6" fill="#050505"/></g>')
    f.append('<path d="M560 840Q760 846 900 836M1150 836Q1300 846 1500 840" stroke="#050606" stroke-width="6" fill="none"/>')
    b.append(''.join(f))
    b.append(f'<rect y="980" width="2048" height="200" fill="url(#mist)" opacity=".8"/>')
    b.append(tree(470, 1300, 210, -.35)); b.append(tree(1578, 1300, 210, .35))
    b.append(tree(200, 1300, 270, .4)); b.append(tree(1848, 1300, 270, -.4))
    save('bg.svg', svg(2048, 1280, ''.join(b), defs))

def svecheed():
    d = BODY + EYE_C + lg('wax', [(0, '#efe6cc', 1), (1, '#a99c7a', 1)])
    b = [f'<path d="M110 505C140 440 160 370 168 300C175 240 205 206 256 204C307 206 337 240 344 300C352 370 372 440 402 505L380 490L362 512L340 486L318 510L296 484L276 508L256 482L236 508L216 484L194 510L172 486L150 512L132 490Z" fill="url(#body)" {RIM}/>',
         f'<path d="M188 252C150 300 122 340 94 400" stroke="#0d090c" stroke-width="16" stroke-linecap="round" fill="none"/>',
         '<g stroke="#0d090c" stroke-width="6" stroke-linecap="round"><path d="M94 400L66 446M94 400L80 456M94 400L98 460M94 400L114 452M94 400L60 420"/></g>',
         f'<path d="M324 252C362 290 380 320 394 356" stroke="#0d090c" stroke-width="16" stroke-linecap="round" fill="none"/>',
         '<rect x="384" y="290" width="24" height="76" rx="3" fill="url(#wax)"/><path d="M384 300q4 18 0 26M404 296q-3 22 2 30" stroke="#d8ceb2" stroke-width="5" fill="none"/>',
         '<path d="M396 290v-12" stroke="#111" stroke-width="3"/><path d="M396 278c-10-14 10-22 0-36s8-24-2-40" stroke="#8a8a8a" stroke-width="3" fill="none" opacity=".45"/>',
         '<g stroke="#0d090c" stroke-width="6" stroke-linecap="round"><path d="M394 356L382 342M394 356L386 330M394 356L404 334M394 356L414 346"/></g>',
         f'<ellipse cx="256" cy="150" rx="50" ry="80" fill="url(#body)" {RIM}/>',
         '<ellipse cx="256" cy="214" rx="11" ry="17" fill="#000"/><ellipse cx="256" cy="216" rx="5" ry="9" fill="#5fd0ff" opacity=".25"/>',
         glow_eye(234, 186, 7, 'eyeC', '#e8fbff'), glow_eye(278, 186, 7, 'eyeC', '#e8fbff'),
         '<path d="M206 140C206 80 230 66 256 66C282 66 306 80 306 140L304 150C300 150 298 175 294 178C290 176 290 150 284 148C280 160 279 200 272 202C266 200 268 160 262 152C258 156 256 170 250 172C244 170 246 150 240 150C236 162 236 186 228 188C222 186 224 156 218 152C214 156 213 170 208 170C204 168 206 150 206 140Z" fill="url(#wax)"/>',
         '<path d="M226 92q20-14 46-4" stroke="#fffaf0" stroke-width="5" fill="none" opacity=".55" stroke-linecap="round"/>',
         '<path d="M256 66v-16" stroke="#111" stroke-width="4"/><path d="M256 50c-12-14 12-22 0-36" stroke="#9a9a9a" stroke-width="3" fill="none" opacity=".4"/>']
    save('enemy_svecheed.svg', svg(512, 512, ''.join(b), d))

def sheptuha():
    d = BODY + EYE_R + rg('face', [(0, '#a39b8e', 1), (.7, '#5c564d', 1), (1, '#2c2925', 1)], cy='.42')
    strands = []
    for i in range(46):
        x0 = 256 + random.uniform(-70, 70); x1 = 256 + (x0 - 256) * 2.4 + random.uniform(-30, 30)
        strands.append(f'<path d="M{x0:.0f} {70 + abs(x0 - 256) * .6:.0f}Q{(x0 + x1) / 2 + random.uniform(-25, 25):.0f} 300 {x1:.0f} 512" stroke="#3a2c34" stroke-width="{random.uniform(1.5, 3.5):.1f}" fill="none" opacity="{random.uniform(.3, .7):.2f}"/>')
    b = [f'<path d="M256 58C190 58 150 110 140 190C128 290 120 400 92 512L420 512C392 400 384 290 372 190C362 110 322 58 256 58Z" fill="url(#body)" {RIM}/>',
         ''.join(strands),
         '<ellipse cx="256" cy="182" rx="44" ry="64" fill="url(#face)"/>',
         '<path d="M205 120C220 150 222 200 214 252L196 252C200 200 196 150 205 120ZM307 120C292 150 290 200 298 252L316 252C312 200 316 150 307 120Z" fill="#0b080a"/>',
         '<ellipse cx="238" cy="168" rx="16" ry="12" fill="#e9e1c9"/><circle cx="238" cy="168" r="8" fill="#b5150f"/><circle cx="238" cy="168" r="3.4" fill="#000"/>',
         '<circle cx="238" cy="168" r="30" fill="url(#eyeR)" opacity=".55"/>',
         '<path d="M262 168q14 5 28 0" stroke="#1a1214" stroke-width="3" fill="none"/><path d="M266 162l2 12M274 163l1 12M282 162l-1 12" stroke="#1a1214" stroke-width="2"/>',
         '<path d="M230 214q26 6 52 0" stroke="#140c0e" stroke-width="4" fill="none"/>',
         '<path d="M236 206l4 16M246 207l2 16M256 207v16M266 207l-2 16M276 206l-4 16" stroke="#3b2a24" stroke-width="2.4"/>',
         '<ellipse cx="206" cy="318" rx="26" ry="20" fill="#5a544b"/>',
         '<path d="M214 304L246 216" stroke="#5a544b" stroke-width="11" stroke-linecap="round"/><path d="M246 216l3-10" stroke="#120d0e" stroke-width="7" stroke-linecap="round"/>',
         '<path d="M196 300L218 236M188 310L200 252" stroke="#4d4840" stroke-width="9" stroke-linecap="round"/>']
    save('enemy_sheptuha.svg', svg(512, 512, ''.join(b), d))

def motanka():
    d = (rg('linen', [(0, '#ddd4bb', 1), (.8, '#a99f84', 1), (1, '#7c735c', 1)], cy='.4')
         + lg('skirt', [(0, '#d6ccb2', 1), (1, '#8d846c', 1)]))
    red = '#8e1b1b'
    orn = []
    for y in (372, 420):
        pts = ' '.join(f'{x},{y + (8 if (x // 14) % 2 else -8)}' for x in range(180, 336, 14))
        orn.append(f'<polyline points="{pts}" stroke="{red}" stroke-width="5" fill="none"/>')
        orn.append(f'<path d="M172 {y + 16}H340M172 {y - 16}H340" stroke="{red}" stroke-width="3" opacity=".8"/>')
    fray = ''.join(f'<path d="M{x} 470l{random.uniform(-4, 4):.0f} {random.uniform(10, 24):.0f}" stroke="#8d846c" stroke-width="2"/>' for x in range(156, 360, 7))
    b = ['<path d="M256 0V92" stroke="#7a1414" stroke-width="2.5"/>',
         '<path d="M256 190C226 190 210 210 206 240C196 320 170 400 150 470L362 470C342 400 316 320 306 240C302 210 286 190 256 190Z" fill="url(#skirt)" stroke="#3a3326" stroke-width="2"/>',
         ''.join(orn), fray,
         f'<path d="M256 228l18 22l-18 22l-18-22z" fill="none" stroke="{red}" stroke-width="4"/><circle cx="256" cy="250" r="4" fill="{red}"/>',
         '<path d="M222 232L158 304M290 232L354 304" stroke="#c4bba2" stroke-width="24" stroke-linecap="round"/>',
         f'<path d="M166 294l-8 10M346 294l8 10" stroke="{red}" stroke-width="8"/>',
         ''.join(f'<path d="M{x0} {y0}l{dx} {random.uniform(26, 40):.0f}" stroke="#a99f84" stroke-width="2"/>' for x0, y0, dx in [(152, 308, -6), (158, 310, -2), (164, 310, 3), (346, 310, -3), (352, 310, 2), (358, 308, 6)]),
         '<circle cx="256" cy="140" r="52" fill="url(#linen)"/>',
         f'<path d="M222 106L290 174M290 106L222 174" stroke="{red}" stroke-width="8" stroke-linecap="round"/>',
         f'<path d="M210 126H302M206 150H306" stroke="{red}" stroke-width="2.5" opacity=".7"/>',
         '<path d="M256 140q3 20 0 40q-3 10 2 22" stroke="#5e0606" stroke-width="5" fill="none" stroke-linecap="round"/>',
         '<path d="M200 140C200 80 230 72 256 72C282 72 312 80 312 140C312 152 306 160 300 162C298 120 280 98 256 98C232 98 214 120 212 162C206 160 200 152 200 140Z" fill="#651315"/>',
         '<path d="M240 194l16 10l16-10l-6 26l-10-10l-10 10z" fill="#651315"/>',
         '<path d="M318 58L204 196" stroke="#c9ccd1" stroke-width="4" stroke-linecap="round"/><ellipse cx="314" cy="63" rx="4" ry="7" transform="rotate(40 314 63)" fill="none" stroke="#7d8086" stroke-width="2"/>',
         f'<path d="M316 60c30 10 40 40 20 70s10 60 30 70" stroke="{red}" stroke-width="2" fill="none"/>',
         '<g fill="#3a2a10" opacity=".25"><ellipse cx="236" cy="330" rx="18" ry="10"/><ellipse cx="290" cy="436" rx="22" ry="8"/><ellipse cx="276" cy="160" rx="10" ry="6"/></g>']
    save('enemy_motanka.svg', svg(512, 512, ''.join(b), d))

def podpolnik():
    d = (rg('skin', [(0, '#6c7462', 1), (.7, '#3a4034', 1), (1, '#1d211a', 1)], cy='.35')
         + lg('plank', [(0, '#2e2117', 1), (1, '#140e09', 1)]) + EYE_W
         + rg('hole', [(0, '#000', 1), (.7, '#050302', 1), (1, '#140e09', 1)]))
    planks = []
    for i, y in enumerate((420, 452, 484)):
        planks.append(f'<rect x="0" y="{y}" width="512" height="30" fill="url(#plank)"/>')
        planks.append(f'<path d="M0 {y + 15}Q120 {y + 10} 256 {y + 16}T512 {y + 13}" stroke="#3d2c1e" stroke-width="1.5" fill="none" opacity=".7"/>')
        for x in (90 + i * 40, 330 - i * 30): planks.append(f'<circle cx="{x}" cy="{y + 8}" r="2.5" fill="#6b6b6b"/>')
    teeth = ''.join(f'<path d="M{x} 384l5 {14 if k % 2 else 10}l5-{14 if k % 2 else 10}z" fill="#d8d0b0"/>' for k, x in enumerate(range(200, 312, 10)))
    arm = lambda s: (f'<path d="M{256 + s * 70} 432Q{256 + s * 150} 300 {256 + s * 170} 300Q{256 + s * 200} 330 {256 + s * 210} 420" stroke="#2f3429" stroke-width="15" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
                     + ''.join(f'<path d="M{256 + s * 210} 420l{s * dx} {dy}" stroke="#2f3429" stroke-width="6" stroke-linecap="round"/>' for dx, dy in [(-30, 6), (-14, 14), (6, 16), (24, 10), (36, 0)])
                     + f'<circle cx="{256 + s * 170}" cy="300" r="10" fill="#3a4034"/>')
    b = [''.join(planks),
         '<path d="M150 422L176 408L196 424L222 404L248 420L276 402L300 420L328 406L360 424L352 470L160 470Z" fill="url(#hole)"/>',
         '<path d="M166 430C166 300 205 248 256 248C307 248 346 300 346 430Z" fill="url(#skin)" stroke="#11140f" stroke-width="3"/>',
         '<path d="M196 300q20-14 40-4M276 296q20-10 40 4" stroke="#22261e" stroke-width="5" fill="none" stroke-linecap="round"/>',
         '<circle cx="222" cy="336" r="27" fill="#e7dcae"/><circle cx="290" cy="336" r="27" fill="#e7dcae"/>',
         '<path d="M200 330l12 4M208 352l10-6M312 330l-12 4M304 352l-10-6" stroke="#b83a2a" stroke-width="1.5"/>',
         '<circle cx="226" cy="340" r="5" fill="#000"/><circle cx="286" cy="340" r="5" fill="#000"/>',
         '<circle cx="222" cy="336" r="60" fill="url(#eyeW)" opacity=".25"/><circle cx="290" cy="336" r="60" fill="url(#eyeW)" opacity=".25"/>',
         '<path d="M190 380Q256 420 322 380Q256 404 190 380Z" fill="#1c0405"/>', teeth,
         arm(-1), arm(1)]
    save('enemy_podpolnik.svg', svg(512, 512, ''.join(b), d))

def moshkara():
    d = EYE_R + rg('haze', [(0, '#1a1416', .85), (.7, '#0b090a', .5), (1, '#000', 0)])
    holes = [((206, 220), 34), ((306, 220), 34), ((256, 318), 42), ((256, 270), 12)]
    flies = []
    while len(flies) < 520:
        x = random.gauss(256, 92); y = random.gauss(250, 105)
        if ((x - 256) / 150) ** 2 + ((y - 250) / 175) ** 2 > 1: continue
        if any((x - hx) ** 2 + (y - hy) ** 2 < r * r for (hx, hy), r in holes): continue
        a = random.uniform(0, 180); s = random.uniform(.7, 1.4)
        f = f'<g transform="translate({x:.0f} {y:.0f}) rotate({a:.0f}) scale({s:.2f})"><ellipse rx="4" ry="2.4" fill="#070607"/>'
        if random.random() < .35: f += '<ellipse cx="-1" cy="-3" rx="3" ry="1.6" fill="#a9b4b8" opacity=".35"/>'
        flies.append(f + '</g>')
    b = ['<ellipse cx="256" cy="256" rx="200" ry="230" fill="url(#haze)"/>', ''.join(flies),
         glow_eye(206, 220, 9, 'eyeR', '#ffd8c8'), glow_eye(306, 220, 9, 'eyeR', '#ffd8c8'),
         '<ellipse cx="256" cy="318" rx="30" ry="34" fill="#5a0606" opacity=".35"/>']
    save('enemy_moshkara.svg', svg(512, 512, ''.join(b), d))

def hozyaika():
    d = (lg('wood', [(0, '#2b1910', 1), (1, '#100905', 1)], 0, 0, 1, 0) + lg('dress', [(0, '#ece6d6', 1), (1, '#8e8778', 1)])
         + rg('pale', [(0, '#f1ece0', 1), (.8, '#bdb6a6', 1), (1, '#8a8476', 1)], cy='.4') + EYE_R
         + rg('aura', [(0, '#c9d6d0', .35), (.6, '#7d9a92', .1), (1, '#000', 0)]))
    hair = ''.join(f'<path d="M{300 + s * random.uniform(10, 34):.0f} 96Q{300 + s * random.uniform(80, 140):.0f} {random.uniform(180, 260):.0f} {300 + s * random.uniform(110, 190):.0f} {random.uniform(380, 470):.0f}" stroke="#050405" stroke-width="{random.uniform(5, 12):.0f}" fill="none" stroke-linecap="round"/>' for s in (-1, 1) for _ in range(14))
    fingers = lambda x, y, s: ''.join(f'<path d="M{x} {y}l{s * dx} {dy}" stroke="#a69f90" stroke-width="5" stroke-linecap="round"/><path d="M{x + s * dx} {y + dy}l{s * dx * .3:.0f} {dy * .3:.0f}" stroke="#0a0a0a" stroke-width="4" stroke-linecap="round"/>' for dx, dy in [(30, -14), (36, -2), (34, 10), (26, 20)])
    b = ['<ellipse cx="300" cy="300" rx="300" ry="300" fill="url(#aura)"/>',
         '<path d="M240 18L360 18L438 120L392 592L208 592L162 120Z" fill="url(#wood)" stroke="#3d2618" stroke-width="5"/>',
         '<path d="M252 40L348 40L410 126L370 570L230 570L190 126Z" fill="#2a1416"/>',
         '<g fill="#7a6a50">' + ''.join(f'<circle cx="{x}" cy="{y}" r="3.5"/>' for x, y in [(244, 28), (356, 28), (170, 124), (430, 124), (212, 584), (388, 584)]) + '</g>',
         hair,
         '<path d="M300 168C262 170 250 200 246 236C236 330 214 450 190 590L410 590C386 450 364 330 354 236C350 200 338 170 300 168Z" fill="url(#dress)"/>',
         '<path d="M276 260Q268 420 240 588M324 260Q332 420 360 588M300 250V588" stroke="#7d7668" stroke-width="3" fill="none" opacity=".6"/>',
         '<path d="M262 206L108 262L112 286L268 238ZM338 206L492 262L488 286L332 238Z" fill="url(#dress)"/>',
         '<path d="M108 262l-10 8l8 4l-6 10l12-2M492 262l10 8l-8 4l6 10l-12-2" fill="#cfc8b8"/>',
         fingers(100, 274, -1), fingers(500, 274, 1),
         '<ellipse cx="300" cy="128" rx="38" ry="50" fill="url(#pale)"/>',
         '<path d="M262 104C266 70 334 70 338 104C330 92 270 92 262 104Z" fill="#050405"/>',
         '<g fill="#3b2a3a">' + ''.join(f'<circle cx="{300 + 40 * math.cos(a):.0f}" cy="{86 + 14 * math.sin(a):.0f}" r="6"/>' for a in np.linspace(math.pi, 2 * math.pi, 9)) + '</g>',
         '<ellipse cx="284" cy="124" rx="11" ry="14" fill="#060505"/><ellipse cx="316" cy="124" rx="11" ry="14" fill="#060505"/>',
         glow_eye(284, 126, 3, 'eyeR', '#ffb0a0'), glow_eye(316, 126, 3, 'eyeR', '#ffb0a0'),
         '<path d="M276 146q8 4 12 0M312 146q8 4 12 0" stroke="#8a8476" stroke-width="2" fill="none"/>',
         '<path d="M288 160q12 3 24 0" stroke="#2a1a1a" stroke-width="3" fill="none"/><path d="M304 161q2 16-2 26" stroke="#5e0606" stroke-width="3" fill="none"/>']
    save('boss_hozyaika.svg', svg(600, 600, ''.join(b), d))

def domovoy():
    d = (rg('fur', [(0, '#4a3526', 1), (.8, '#22170f', 1), (1, '#120b07', 1)], cy='.4')
         + lg('beard', [(0, '#c9c1b0', 1), (1, '#6f675b', 1)])
         + rg('lamp', [(0, '#fff2c0', 1), (.25, '#ffc65a', .9), (.6, '#ff9a2a', .3), (1, '#ff7a00', 0)])
         + rg('eyeA', [(0, '#fff7d6', 1), (.4, '#ffbf3a', 1), (1, '#b86a00', 1)]))
    pts = []
    for i in range(90):
        a = i / 90 * 2 * math.pi; r = 124 + (16 if i % 2 else -6) + random.uniform(-6, 6)
        pts.append(f'{200 + math.cos(a) * r * 1.05:.0f},{220 + math.sin(a) * r:.0f}')
    bp_ = []
    for i in range(23):
        x = 130 + i * 6.4; y = 360 + (30 if i % 2 else 0) + random.uniform(-6, 8) - abs(i - 11) * 3
        bp_.append(f'{x:.0f},{y:.0f}')
    beard = 'M120 230 ' + ' '.join('L' + p for p in bp_) + ' L280 230 Q200 280 120 230Z'
    b = ['<ellipse cx="200" cy="384" rx="120" ry="14" fill="#000" opacity=".5"/>',
         f'<polygon points="{" ".join(pts)}" fill="url(#fur)" stroke="#5a4230" stroke-width="2"/>',
         f'<path d="{beard}" fill="url(#beard)"/>',
         '<path d="M140 176q30-26 56-4M204 172q30-22 56 4" stroke="#8f8676" stroke-width="12" fill="none" stroke-linecap="round"/>',
         '<circle cx="168" cy="206" r="25" fill="#120b07"/><circle cx="232" cy="206" r="25" fill="#120b07"/>',
         '<circle cx="168" cy="208" r="18" fill="url(#eyeA)"/><circle cx="232" cy="208" r="18" fill="url(#eyeA)"/>',
         '<circle cx="171" cy="210" r="7" fill="#1a0e04"/><circle cx="235" cy="210" r="7" fill="#1a0e04"/><circle cx="164" cy="202" r="4" fill="#fff"/><circle cx="228" cy="202" r="4" fill="#fff"/>',
         '<ellipse cx="200" cy="244" rx="17" ry="14" fill="#8a5a44"/><ellipse cx="195" cy="240" rx="5" ry="4" fill="#c58b70"/>',
         '<circle cx="318" cy="320" r="90" fill="url(#lamp)" opacity=".75"/>',
         '<path d="M300 268h36l-4 10h-28z" fill="#1d150e"/><path d="M318 268v-16q0-10 10-10" stroke="#1d150e" stroke-width="4" fill="none"/>',
         '<rect x="302" y="278" width="32" height="44" rx="4" fill="#ffd27a" stroke="#1d150e" stroke-width="4"/><path d="M318 278v44" stroke="#1d150e" stroke-width="3"/><ellipse cx="318" cy="302" rx="6" ry="10" fill="#fff7e0"/>',
         '<path d="M298 322h40l-6 8h-28z" fill="#1d150e"/>',
         '<ellipse cx="292" cy="290" rx="18" ry="14" fill="#2b1d13"/>',
         '<ellipse cx="160" cy="380" rx="26" ry="12" fill="#a08850"/><ellipse cx="240" cy="380" rx="26" ry="12" fill="#a08850"/><path d="M140 378h40M220 378h40" stroke="#6a5530" stroke-width="2"/>']
    save('domovoy.svg', svg(400, 400, ''.join(b), d))

def reader():
    d = (rg('page', [(0, '#fff6d8', 1), (.5, '#ffd27a', .6), (1, '#ff9a2a', 0)])
         + lg('cloak', [(0, '#1d1a22', 1), (1, '#09080b', 1)]))
    b = ['<ellipse cx="100" cy="176" rx="70" ry="12" fill="#000" opacity=".6"/>',
         '<path d="M100 26C70 26 58 52 56 80C52 110 40 140 26 176L174 176C160 140 148 110 144 80C142 52 130 26 100 26Z" fill="url(#cloak)" stroke="#3a3346" stroke-width="2"/>',
         '<path d="M100 40C82 40 74 58 74 76C74 90 86 98 100 98C114 98 126 90 126 76C126 58 118 40 100 40Z" fill="#030304"/>',
         '<circle cx="100" cy="132" r="56" fill="url(#page)" opacity=".7"/>',
         '<path d="M70 118L100 128L130 118L130 146L100 156L70 146Z" fill="#efe4c4"/><path d="M100 128V156" stroke="#8a7a5a" stroke-width="2"/>',
         '<path d="M78 128l16 5M78 136l16 5M106 133l16-5M106 141l16-5" stroke="#6a5a3a" stroke-width="1.5"/>',
         '<path d="M86 88q14 6 28 0" stroke="#ffc65a" stroke-width="2" fill="none" opacity=".5"/>']
    save('reader.svg', svg(200, 200, ''.join(b), d))

def icons():
    save('heart.svg', svg(64, 64, '<path d="M32 58C10 42 4 30 6 20C8 10 18 6 26 10C29 12 31 14 32 17C33 14 35 12 38 10C46 6 56 10 58 20C60 30 54 42 32 58Z" fill="url(#h)" stroke="#2a0204" stroke-width="2"/><path d="M24 6v10M32 4v12M40 6v10" stroke="#7a0a0e" stroke-width="4" stroke-linecap="round"/><path d="M14 20q2-6 8-7" stroke="#ff9a8a" stroke-width="3" fill="none" stroke-linecap="round" opacity=".8"/>',
                              rg('h', [(0, '#ff4a3a', 1), (.7, '#a8070d', 1), (1, '#5a0206', 1)], cx='.4', cy='.35')))
    save('coin.svg', svg(64, 64, '<circle cx="32" cy="32" r="28" fill="url(#c)" stroke="#4a2408" stroke-width="3"/><circle cx="32" cy="32" r="20" fill="none" stroke="#7a4518" stroke-width="2" opacity=".8"/><rect x="25" y="25" width="14" height="14" fill="#1a0c04" stroke="#4a2408" stroke-width="2"/><path d="M14 22q6-10 16-12" stroke="#ffd9a0" stroke-width="3" fill="none" stroke-linecap="round" opacity=".7"/>',
                             rg('c', [(0, '#f0a860', 1), (.7, '#b0642a', 1), (1, '#6e3a17', 1)], cx='.38', cy='.35')))
    save('jar.svg', svg(96, 112, '<rect x="30" y="4" width="36" height="16" rx="4" fill="#7a5230" stroke="#3a2410" stroke-width="2"/><path d="M28 22h40l4 8q12 8 12 24v42q0 12-12 12H24q-12 0-12-12V54q0-16 12-24z" fill="#a8d0d8" fill-opacity=".1" stroke="#cfe6ea" stroke-opacity=".75" stroke-width="3"/><path d="M22 52v40" stroke="#ffffff" stroke-opacity=".4" stroke-width="4" stroke-linecap="round"/><path d="M26 30h44" stroke="#cfe6ea" stroke-opacity=".5" stroke-width="2"/>'))
    save('ember.svg', svg(64, 96, '<path d="M32 4C40 26 56 40 56 62C56 80 45 92 32 92C19 92 8 80 8 62C8 46 20 36 22 20C26 30 30 32 32 4Z" fill="url(#f)"/><path d="M32 40C36 52 44 58 44 70C44 80 38 86 32 86C26 86 20 80 20 70C20 60 28 54 32 40Z" fill="url(#g)"/>',
                              rg('f', [(0, '#ffe08a', 1), (.6, '#ff8a1a', .95), (1, '#c02800', .9)], cy='.7', r='.6') + rg('g', [(0, '#ffffff', 1), (1, '#fff0b0', 1)], cy='.7')))
    save('candle.svg', svg(48, 128, '<rect x="10" y="22" width="28" height="104" rx="3" fill="url(#w)"/><path d="M10 30q0 18 4 26q4-8 2-26M30 26q-2 24 3 36q4-14 1-36" fill="#efe6cc"/><ellipse cx="24" cy="23" rx="14" ry="4" fill="#f5eedb"/><path d="M24 22v-10" stroke="#111" stroke-width="3"/>',
                               lg('w', [(0, '#a99c7a', 1), (.45, '#efe6cc', 1), (1, '#8e8266', 1)], 0, 0, 1, 0)))
    s = ['<circle cx="64" cy="64" r="56" fill="none" stroke="#ffd36a" stroke-width="5"/><circle cx="64" cy="64" r="46" fill="none" stroke="#ffd36a" stroke-width="2"/>']
    s.append('<path d="M64 20L108 64L64 108L20 64Z" fill="none" stroke="#ffd36a" stroke-width="4" stroke-linejoin="round"/>')
    s.append('<path d="M64 36L92 64L64 92L36 64Z" fill="none" stroke="#ffd36a" stroke-width="2.5"/><path d="M64 36V92M36 64H92" stroke="#ffd36a" stroke-width="2"/>')
    s.append(''.join(f'<circle cx="{x}" cy="{y}" r="4" fill="#ffd36a"/>' for x, y in [(57, 57), (71, 57), (57, 71), (71, 71)]))
    for i in range(12):
        a = i * math.pi / 6; s.append(f'<path d="M{64 + 51 * math.cos(a):.1f} {64 + 51 * math.sin(a):.1f}l{6 * math.cos(a + 1):.1f} {6 * math.sin(a + 1):.1f}" stroke="#ffd36a" stroke-width="3"/>')
    save('seal.svg', svg(128, 128, ''.join(s)))
    # runes ring (inside chalk circle), 560x560, radius 158
    G = ['M0-12V12M0-12L8-4M0-2L8 6', 'M-6 12V-12L6-2L-6 6', 'M-5-12V12M-5-6L5 0L-5 6', 'M0-12V12M-7-5L7 5M7-5L-7 5', 'M-6 12L0-12L6 12M-3 2H3',
         'M0-12V12M0-4L-7-11M0-4L7-11', 'M-6-12L6 12M6-12L-6 12', 'M-6-12V12M6-12V12M-6 0L6-6', 'M0-12L7 0L0 12L-7 0Z', 'M-6-12V12M-6-12L6-4L-6 4', 'M0-12V12M-6-6L0 0L6-6', 'M-7 12L0-12L7 12']
    r = []
    for i in range(24):
        a = i / 24 * 360; g = random.choice(G)
        r.append(f'<g transform="rotate({a:.1f} 280 280) translate(280 {280 - 158})"><path d="{g}"/></g>')
    r.append('<circle cx="280" cy="280" r="136" fill="none" stroke-dasharray="3 9"/><circle cx="280" cy="280" r="180" fill="none" stroke-dasharray="40 14 4 14"/>')
    save('runes.svg', svg(560, 560, f'<g fill="none" stroke="#e8e2d0" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">{"".join(r)}</g>'))

def pngs():
    # seamless fbm value noise 256x256
    n = 256; acc = np.zeros((n, n)); amp = 1.0; tot = 0
    rs = np.random.default_rng(3)
    for oct_ in range(5):
        cells = 4 * 2 ** oct_; grid = rs.random((cells, cells))
        xs = np.arange(n) * cells / n; i0 = np.floor(xs).astype(int); f = xs - i0; f = f * f * (3 - 2 * f); i1 = (i0 + 1) % cells
        g00 = grid[np.ix_(i0, i0)]; g10 = grid[np.ix_(i1, i0)]; g01 = grid[np.ix_(i0, i1)]; g11 = grid[np.ix_(i1, i1)]
        fy = f[:, None]; fx = f[None, :]
        acc += amp * ((g00 * (1 - fx) + g01 * fx) * (1 - fy) + (g10 * (1 - fx) + g11 * fx) * fy); tot += amp; amp *= .5
    acc = (acc / tot - acc.min() / tot); acc /= acc.max()
    Image.fromarray((acc * 255).astype(np.uint8), 'L').convert('RGB').save(f'{OUT}/noise.png')
    y, x = np.mgrid[0:128, 0:128]; d = np.sqrt((x - 63.5) ** 2 + (y - 63.5) ** 2) / 64
    a = np.clip(1 - d, 0, 1) ** 2.2
    img = np.zeros((128, 128, 4), np.uint8); img[..., :3] = 255; img[..., 3] = (a * 255).astype(np.uint8)
    Image.fromarray(img, 'RGBA').save(f'{OUT}/glow.png')

# ---------- скол мела (пункт 2.5): частица scenes/fx/chips ----------
def chip():
    # Свой генератор: добавление не меняет остальной арт (random.seed(7) выше не трогаем).
    rc = random.Random(2505)
    pts = []
    for i in range(7):
        a = i / 7 * 2 * math.pi + rc.uniform(-.25, .25)
        r = rc.uniform(8, 15) * (1.25 if i % 3 == 0 else 1)
        pts.append(f'{24 + math.cos(a) * r:.1f} {24 + math.sin(a) * r * .72:.1f}')
    body = (f'<path d="M{"L".join(pts)}Z" fill="#efe6d2" stroke="#b9ae96" stroke-width="2" stroke-linejoin="round"/>'
            '<path d="M15 21l9-4 8 3" stroke="#ffffff" stroke-width="2.5" fill="none" stroke-linecap="round" opacity=".8"/>')
    save('chip.svg', svg(48, 48, body))

# python3 tools/gen_art.py chip — только эти группы, остальной арт не трогаем
GROUPS = {'chip': chip}

if __name__ == '__main__':
    import sys
    os.makedirs(OUT, exist_ok=True)
    only = set(sys.argv[1:])
    unknown = only - set(GROUPS)
    if unknown:
        sys.exit(f'неизвестные группы: {", ".join(sorted(unknown))}; есть: {", ".join(GROUPS)}')
    if not only:
        background(); svecheed(); sheptuha(); motanka(); podpolnik(); moshkara(); hozyaika(); domovoy(); reader(); icons(); pngs()
    for name, fn in GROUPS.items():
        if not only or name in only:
            fn()
    print('art done')
