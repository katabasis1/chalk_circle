"""Procedural SFX + music for Chalk Circle. Run from project root: python3 tools/gen_audio.py
Needs numpy, scipy, ffmpeg (libvorbis). Output: assets/audio/{sfx,music}/*.ogg"""
import numpy as np, subprocess, os, tempfile
from scipy import signal
from scipy.io import wavfile
SR = 44100
R = np.random.default_rng(13)

def T(d): return np.arange(int(SR * d)) / SR
def noise(d): return R.uniform(-1, 1, int(SR * d))
def filt(x, kind, f, o=2):
    f = np.atleast_1d(f) / (SR / 2)
    b, a = signal.butter(o, f if len(f) > 1 else f[0], kind)
    return signal.lfilter(b, a, x)
def lp(x, f, o=2): return filt(x, 'low', f, o)
def hp(x, f, o=2): return filt(x, 'high', f, o)
def bp(x, lo, hi, o=2): return filt(x, 'band', [lo, hi], o)
def phase(freq):  # freq: array (Hz per sample)
    return np.cumsum(freq) / SR
def sine_sweep(f0, f1, d, curve=3.0):
    t = T(d); f = f1 + (f0 - f1) * np.exp(-curve * t / d); return np.sin(2 * np.pi * phase(f))
def saw_f(freq): p = phase(freq); return 2 * (p % 1.0) - 1
def saw(f, d): return saw_f(np.full(int(SR * d), float(f)))
def dec(d, k): return np.exp(-T(d) * k)
def pad(x, n): return np.pad(x, (0, max(0, n - len(x))))[:n]
def mix(*xs):
    n = max(len(x) for x in xs); return sum(pad(x, n) for x in xs)
def at(buf, x, t0, gain=1.0):
    i = int(t0 * SR); j = min(len(buf), i + len(x)); buf[i:j] += x[:j - i] * gain
def norm(x, p=0.9): m = np.max(np.abs(x)) or 1; return x / m * p
def reverb(x, size=2.0, k=2.5, wet=0.3, circular=False, bright=3000):
    ir = lp(noise(size), bright) * dec(size, k); ir /= np.sqrt(np.sum(ir ** 2))
    if circular:
        n = len(x); y = np.real(np.fft.ifft(np.fft.fft(x) * np.fft.fft(pad(ir, n))))
        return x * (1 - wet) + y * wet
    y = signal.fftconvolve(x, ir)[: len(x) + int(SR * size * 0.6)]
    return pad(x, len(y)) * (1 - wet) + y * wet
def fade(x, a=0.003, r=0.03):
    x = x.copy(); na, nr = int(SR * a), int(SR * r)
    x[:na] *= np.linspace(0, 1, na); x[-nr:] *= np.linspace(1, 0, nr); return x
def bell(f, d, partials=((1, 1), (2.76, .5), (5.4, .25), (8.93, .12)), k=3.0):
    t = T(d); return sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * k * (1 + r * .4)) for r, a in partials)
def formant(x, freqs=(800, 1150, 2900), q=0.12):
    return sum(bp(x, f * (1 - q), f * (1 + q)) * g for f, g in zip(freqs, (1, .6, .25)))

def save(name, x, q=4):
    x = np.clip(x, -1, 1); fd, tmp = tempfile.mkstemp(suffix='.wav'); os.close(fd)
    wavfile.write(tmp, SR, (x * 32767).astype(np.int16))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', tmp, '-c:a', 'libvorbis', '-q:a', str(q), name], check=True)
    os.remove(tmp)

# ---------------- SFX ----------------
def sfx():
    S = {}
    d = .4
    S['hit'] = mix(sine_sweep(170, 45, d) * dec(d, 16), bp(noise(d), 1500, 5000) * dec(d, 70) * .8,
                   bp(noise(d), 3500, 9000) * dec(d, 30) * .25)
    d = .8
    x = mix(np.tanh(2.5 * sine_sweep(130, 32, d) * dec(d, 7)), bp(noise(d), 900, 4000) * dec(d, 35),
            lp(noise(d), 300) * dec(d, 9) * .8)
    S['hit_big'] = reverb(x, 1.2, 4, .3)
    d = .35; t = T(d); e = np.sin(np.pi * t / d) ** 2
    S['miss'] = mix(lp(noise(d), 700) * e * 1.4, np.sin(2 * np.pi * 70 * t) * e * .5)
    d = .9; t = T(d)
    beat = mix(sine_sweep(110, 40, .3) * dec(.3, 12), pad(np.zeros(int(SR * .17)), int(SR * .17)))
    dub = sine_sweep(120, 45, .3) * dec(.3, 14) * .7
    scream = np.tanh(3 * formant(saw_f(np.linspace(260, 90, len(t)) * (1 + .03 * np.sin(2 * np.pi * 9 * t))), (650, 1100, 2600))) * dec(d, 4)
    x = mix(beat, np.concatenate([np.zeros(int(SR * .17)), dub]), scream * .55, bp(noise(d), 200, 2000) * dec(d, 18) * .6)
    S['hurt'] = reverb(x, 1.0, 4, .25)
    d = .22; t = T(d)
    S['dodge'] = mix(hp(noise(d), 2500) * np.sin(np.pi * t / d) ** 3, bp(noise(d), 600, 1800) * dec(d, 60) * .4)
    d = .7; t = T(d); e = (t / d) ** 3 * (t < d * .85) + (t >= d * .85) * np.exp(-(t - d * .85) * 40)
    S['special'] = reverb(mix(hp(noise(d), 3500) * e, (np.sin(2 * np.pi * 440 * t) + np.sin(2 * np.pi * 466 * t)) * e * .3), .8, 5, .3)
    d = 1.0
    S['seal_appear'] = reverb(mix(bell(1320, d, k=4) * .6, bell(1980 * 1.01, d, k=5) * .4, bell(2640, d, k=6) * .3), 1.2, 3, .4)
    d = 1.8; t = T(d)
    gl = np.sin(2 * np.pi * phase(300 * 4 ** np.clip(t / .6, 0, 1))) * np.clip(1 - (t - .6) * 3, 0, 1) * (t < .9)
    choir = formant(sum(saw_f(np.full(len(t), f) * (1 + .004 * np.sin(2 * np.pi * (5 + i) * t))) for i, f in enumerate((220, 277.2, 329.6, 440))), (800, 1150, 2900)) * np.clip(t / .5, 0, 1) * np.exp(-np.clip(t - .7, 0, None) * 2.5)
    clink = np.concatenate([np.zeros(int(SR * .6)), bell(2100, d - .6, ((1, 1), (1.62, .7), (2.71, .5), (3.93, .3)), k=6)])
    S['seal'] = reverb(mix(gl * .5, choir * .5, clink * .7), 2.0, 2.5, .4)
    d = .55
    c = bell(2200, d, ((1, 1), (1.5, .6), (2.36, .5), (3.2, .3)), k=9)
    S['coin'] = reverb(mix(c, np.concatenate([np.zeros(int(SR * .06)), c * .6])), .6, 5, .2)
    d = 1.0
    S['buy'] = reverb(mix(S['coin'], bell(220, d, k=3) * .5, bell(330, d, k=3.5) * .3), 1.0, 3.5, .3)
    d = 1.1; t = T(d)
    f = np.interp(t, [0, .15, d], [500, 1100, 180]) * (1 + .05 * np.sin(2 * np.pi * 13 * t))
    x = np.tanh(3 * formant(saw_f(f), (900, 1400, 3100))) * np.clip(t / .03, 0, 1) * np.exp(-t * 2.5)
    S['enemy_die'] = reverb(mix(x, bp(noise(d), 1000, 6000) * dec(d, 6) * .4), 1.5, 3, .35)
    d = 1.2; t = T(d); e = np.sin(np.pi * t / d)
    g = lp(noise(d), 450) * (0.55 + .45 * np.sin(2 * np.pi * 27 * t)) * 2.5 + lp(saw_f(55 * (1 + .1 * np.sin(2 * np.pi * 3 * t)) * np.ones(len(t))), 300) * .8
    S['enemy_appear'] = reverb(np.tanh(1.5 * g) * e, 1.2, 3, .3)
    d = 1.0; t = T(d); e = np.sin(np.pi * np.clip(t / .7, 0, 1)) ** 2
    S['wipe'] = reverb(mix(bp(noise(d), 300, 3000) * e, np.concatenate([np.zeros(int(SR * .35)), sine_sweep(70, 28, .65) * dec(.65, 5) * 1.2])), 1.2, 3, .3)
    d = .09
    S['tick'] = mix(bp(noise(d), 700, 2200) * dec(d, 90), np.sin(2 * np.pi * 620 * T(d)) * dec(d, 70) * .5)
    d = .9
    lub = sine_sweep(95, 42, .25) * dec(.25, 13); dub2 = sine_sweep(105, 45, .25) * dec(.25, 15) * .7
    hb = np.zeros(int(SR * d)); at(hb, lub, 0); at(hb, dub2, .26)
    S['heartbeat'] = lp(hb, 400)
    d = .5; t = T(d)
    S['whiff'] = mix(hp(noise(d), 1200) * np.sin(np.pi * t / d) ** 2 * .6, np.sin(2 * np.pi * phase(np.linspace(300, 120, len(t)))) * dec(d, 8) * .3)
    for k, v in S.items(): save(f'assets/audio/sfx/{k}.ogg', fade(norm(v, .92)), 4)

# ---------------- MUSIC (seamless loops) ----------------
def loop_buffer(L): return np.zeros(int(SR * (L + 6)))
def finish(buf, L, rev=(2.5, 1.6, .35)):
    n = int(SR * L); out = buf[:n].copy(); tail = buf[n:]; out[:len(tail)] += tail[:n]
    return reverb(out, *rev, circular=True)

def m_menu():
    L = 32.0; b = loop_buffer(L); t = T(L)
    drone = sum(saw_f(np.full(len(t), f * (1 + dt))) for f in (55, 82.41, 110) for dt in (-.003, 0, .004))
    lfo = 300 + 250 * (0.5 + 0.5 * np.sin(2 * np.pi * t / L * 2))
    drone = lp(drone, 380) * .25 * (0.7 + .3 * np.sin(2 * np.pi * t / L * 4))
    wind = bp(noise(L), 250, 1300) * (0.3 + 0.7 * (0.5 + 0.5 * np.sin(2 * np.pi * t / L * 3 + 1))) * .35
    b[:len(t)] += drone + wind
    for i, (tt, f) in enumerate([(1, 220), (9, 261.6), (17, 207.7), (25, 196)]):
        at(b, bell(f, 6, k=.9) * .35, tt); at(b, bell(f * 1.5, 5, k=1.2) * .12, tt + .02)
    return finish(b, L, (3.0, 1.2, .45))

def m_fight():
    bpm = 120; beat = 60 / bpm; L = 64 * beat; b = loop_buffer(L)
    kick = sine_sweep(110, 40, .35) * dec(.35, 11)
    tick = bp(noise(.05), 2000, 6000) * dec(.05, 120)
    bassn = [73.42, 77.78, 73.42, 55.0]
    for bar in range(16):
        t0 = bar * 4 * beat
        for k in (0, .75, 2, 2.75): at(b, kick, t0 + k * beat, .9 if k in (0, 2) else .6)
        for e in range(8): at(b, tick, t0 + e * beat / 2, .12 if e % 2 else .2)
        for h in range(2):
            f = bassn[(bar * 2 + h) % 4]; d = 2 * beat
            n = lp(saw(f, d) + .5 * saw(f * 1.005, d), 260) * np.clip(T(d) / .02, 0, 1) * np.exp(-T(d) * 1.2)
            at(b, n, t0 + h * 2 * beat, .5)
        if bar % 4 == 0:
            d = 8 * beat; tt = T(d); sw = np.sin(np.pi * tt / d) ** 2
            cl = sum(saw_f(np.full(len(tt), f) * (1 + .006 * np.sin(2 * np.pi * 5.5 * tt + i))) for i, f in enumerate((146.8, 155.6, 220, 311.1)))
            at(b, lp(cl, 1400) * sw * .18, t0)
        if bar % 2 == 1: at(b, bell(587.3 if bar % 4 == 1 else 554.4, 3, k=2) * .15, t0 + 3.5 * beat)
    return finish(b, L, (1.8, 2.0, .3))

def m_shop():
    bpm = 96; beat = 60 / bpm; L = 48 * beat; b = loop_buffer(L)  # 16 bars of 3/4
    A = 440.0; st = lambda s: A * 2 ** (s / 12)
    mel = [0, 3, 7, 8, 7, 3, 2, 3, 5, 3, 2, -1, 0, 3, 7, 12, 11, 8, 7, 8, 7, 3, 2, 0]
    for i, s in enumerate(mel):
        t0 = i * 2 * beat; f = st(s) * (1 + R.uniform(-.006, .006))
        at(b, bell(f, 2.5, ((1, 1), (2, .25), (3.01, .12), (4.2, .05)), k=2.4) * .35, t0)
        if i % 2: at(b, bell(st(s + 7), 1.5, k=3) * .08, t0 + beat)
    bass = [-24, -24, -19, -17, -24, -24, -21, -17]
    for bar in range(16):
        at(b, bell(st(bass[bar % 8]), 2.5, ((1, 1), (2, .3), (3, .1)), k=1.6) * .3, bar * 3 * beat)
    n = int(SR * L); crack = np.zeros(n); idx = R.integers(0, n, 700); crack[idx] = R.uniform(-.6, .6, 700)
    b[:n] += hp(crack, 1500) * .5 + hp(lp(noise(L), 6000), 2000) * .015
    # warped tape wobble
    out = finish(b, L, (2.2, 1.8, .4))
    return out

def m_boss():
    bpm = 150; s16 = 60 / bpm / 4; L = 20 * 16 * s16; b = loop_buffer(L)
    tom = np.tanh(2 * sine_sweep(140, 45, .4) * dec(.4, 9))
    snare = mix(bp(noise(.25), 800, 6000) * dec(.25, 18), sine_sweep(220, 160, .1) * dec(.1, 30) * .5)
    for bar in range(20):
        t0 = bar * 16 * s16
        for k in (0, 3, 6, 8, 11, 14): at(b, tom, t0 + k * s16, .8)
        for k in (4, 12): at(b, snare, t0 + k * s16, .45)
        for k in (0, 8):
            d = 6 * s16; n = lp(saw(69.3, d) + saw(103.8, d) + saw(69.3 * 1.01, d), 500) * np.exp(-T(d) * 3)
            at(b, np.tanh(2 * n) * .35, t0 + k * s16)
        at(b, bell([554.4, 523.3, 493.9, 466.2][bar % 4], 1.6, k=2.5) * .18, t0 + 2 * s16)
        if bar % 4 == 0:
            d = 16 * 4 * s16; tt = T(d); sw = np.sin(np.pi * tt / d) ** 1.5
            ch = sum(saw_f(np.full(len(tt), f) * (1 + .005 * np.sin(2 * np.pi * (4.5 + i * .7) * tt))) for i, f in enumerate((138.6, 164.8, 207.7, 277.2)))
            at(b, formant(ch, (750, 1150, 2800)) * sw * .5, t0)
    return finish(b, L, (1.6, 2.2, .28))

# ---------------- КОМБО (пункт 2.1) ----------------
# Свой генератор случайных чисел: добавление этих звуков не меняет остальные (R13 не трогаем).
def sfx_combo():
    Rc = np.random.default_rng(2101)
    def nz(d): return Rc.uniform(-1, 1, int(SR * d))
    S = {}
    # «Динь» мела по черте. Высоту в игре задаёт pitch_scale (пентатоника вверх с каждым попаданием),
    # поэтому основной тон низковат (E5 ≈ 659 Гц): на вершине комбо (+2 октавы) не режет ухо.
    d = .4
    ting = bell(659.3, d, ((1, 1), (2.0, .35), (3.01, .18), (4.17, .08)), k=7)
    tap = hp(nz(.03), 3500) * dec(.03, 160) * .5
    S['combo'] = reverb(mix(ting, tap), .5, 6, .18)
    # Ступень комбо (5 / 10): быстрое арпеджио вверх + «искры».
    d = 1.3; b = np.zeros(int(SR * d))
    for i, f in enumerate((659.3, 830.6, 987.8, 1318.5)):
        at(b, bell(f, d - i * .06, k=3.2) * (.55 + i * .1), i * .06)
    sparkle = hp(nz(d), 6000) * np.exp(-T(d) * 5) * (0.5 + 0.5 * np.sin(2 * np.pi * 23 * T(d))) * .12
    S['combo_up'] = reverb(mix(b, sparkle), 1.4, 3, .38)
    # Комбо сорвано: мел крошится + глухое «вниз».
    d = .7; t = T(d)
    crumble = np.zeros(int(SR * d))
    for k in range(9):
        g = bp(nz(.04), 1200, 4500) * dec(.04, 90)
        at(crumble, g, .02 + k * .045 + Rc.uniform(0, .02), .9 - k * .08)
    fall = np.sin(2 * np.pi * phase(np.interp(t, [0, d], [520, 150]))) * np.exp(-t * 5) * .45
    S['combo_break'] = reverb(mix(crumble, fall, lp(nz(d), 250) * dec(d, 14) * .4), .8, 4, .25)
    for k, v in S.items(): save(f'assets/audio/sfx/{k}.ogg', fade(norm(v, .92)), 4)

# ---------------- «ИДЕАЛЬНО» (пункт 2.2) ----------------
def sfx_perfect():
    Rp = np.random.default_rng(2202)
    d = .9; t = T(d)
    # Хрустальный «дзинь» (две высокие колокольные ноты, квинта) + взлетающий блик + мягкий удар снизу.
    glass = mix(bell(1760, d, ((1, 1), (2.0, .3), (2.76, .25), (4.07, .1)), k=4.5) * .7,
                bell(2637, d, ((1, 1), (2.0, .2), (3.0, .1)), k=5.5) * .45)
    glint = np.sin(2 * np.pi * phase(np.interp(t, [0, .12, d], [1200, 3600, 3600]))) * np.exp(-t * 22) * .25
    thump = sine_sweep(160, 60, .25) * dec(.25, 18) * .5
    air = hp(Rp.uniform(-1, 1, int(SR * d)), 7000) * np.exp(-t * 12) * .08
    x = reverb(mix(glass, glint, thump, air), 1.1, 3.5, .35)
    save('assets/audio/sfx/perfect.ogg', fade(norm(x, .92)), 4)

# ---------------- СНАРЯД (пункт 2.3) ----------------
def sfx_bolt():
    Rb = np.random.default_rng(2303)
    def nz(d): return Rb.uniform(-1, 1, int(SR * d))
    # «Вжух» мела: щелчок-чирк о черту + короткий свист, уходящий вверх (снаряд срывается с круга).
    d = .26; t = T(d)
    flick = bp(nz(.035), 2500, 7000) * dec(.035, 120) * .9
    swish = bp(nz(d), 900, 5200) * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2 * np.exp(-t * 6) * .55
    whistle = np.sin(2 * np.pi * phase(np.interp(t, [0, d], [700, 1900]))) * np.sin(np.pi * t / d) ** 3 * .12
    x = reverb(mix(flick, swish, whistle), .4, 7, .12)
    save('assets/audio/sfx/cast.ogg', fade(norm(x, .9)), 4)

# ---------------- ЗАМАХ НЕЧИСТИ (пункт 2.4) ----------------
def sfx_windup():
    Rw = np.random.default_rng(2404)
    def nz(d): return Rw.uniform(-1, 1, int(SR * d))
    # windup: втягивание воздуха — шипение нарастает и поднимается, под ним низкий рык,
    # в конце холодный «дзынь» блика в глазах. Длина ≈ заряд секции (0.35–0.5 с).
    d = .5; t = T(d)
    rise = np.clip(t / d, 0, 1)
    hiss = bp(nz(d), 1800, 6500) * rise ** 2.2 * .5
    breath = bp(nz(d), 300, 1400) * np.sin(np.pi * np.clip(t / (d * 1.1), 0, 1)) * rise * .35
    growl_f = np.interp(t, [0, d], [62, 88])
    growl = lp(saw_f(growl_f) * (1 + .35 * np.sin(2 * np.pi * 23 * t)), 420) * rise ** 1.5 * .32
    glint = np.zeros_like(t)
    at(glint, bell(2794, .25, ((1, 1), (2.4, .35), (4.1, .12)), k=12) * .3, .36)
    x = reverb(mix(hiss, breath, growl, glint), .7, 5, .2)
    save('assets/audio/sfx/windup.ogg', fade(norm(x, .85), .01, .02), 4)
    # ignite: атака вспыхнула на круге — короткий меловой «фух» с хлопком пламени.
    d = .3; t = T(d)
    puff = bp(nz(d), 500, 3800) * np.exp(-t * 14) * .7
    snap = hp(nz(.02), 3000) * dec(.02, 160) * .6
    body = sine_sweep(140, 55, .2) * dec(.2, 16) * .55
    x = reverb(mix(puff, snap, body), .5, 6, .15)
    save('assets/audio/sfx/ignite.ogg', fade(norm(x, .88)), 4)

# ---------------- РАНЫ (пункт 2.5) ----------------
def sfx_wound():
    Rn = np.random.default_rng(2505)
    def nz(d): return Rn.uniform(-1, 1, int(SR * d))
    # crack: черта лопается — сухой щелчок, трещина «бежит» (серия мелких щелчков), глухой удар и осыпь крошек.
    d = .75; t = T(d)
    snap = mix(hp(nz(.025), 2500) * dec(.025, 150), bp(nz(.05), 900, 3200) * dec(.05, 70) * .7)
    run = np.zeros(int(SR * d))
    for k in range(7):
        at(run, bp(nz(.012), 2500, 8000) * dec(.012, 300), .012 + k * .016 + Rn.uniform(0, .008), .75 - k * .08)
    thud = sine_sweep(110, 38, .3) * dec(.3, 13) * .7
    grit = np.zeros(int(SR * d))
    for k in range(14):
        at(grit, bp(nz(.02), 1500, 6000) * dec(.02, 140), .13 + Rn.uniform(0, .5) * (k / 14) ** .6, .45 * (1 - k / 16))
    x = reverb(mix(snap, run, thud, grit), .7, 5, .2)
    save('assets/audio/sfx/crack.ogg', fade(norm(x, .9)), 4)
    # redraw: Домовой проводит мелом по черте — шорох-чирканье с дрожью, в конце тёплый «дзинь» (рана затянулась).
    d = 1.0; t = T(d)
    stroke_e = np.sin(np.pi * np.clip(t / .5, 0, 1)) ** 1.5
    chatter = .55 + .45 * np.sin(2 * np.pi * phase(np.interp(t, [0, .5], [38, 60])))
    scratch = bp(nz(d), 1400, 5200) * stroke_e * chatter * .7
    squeak = np.sin(2 * np.pi * phase(np.interp(t, [0, .5], [2100, 2500]) * (1 + .01 * np.sin(2 * np.pi * 9 * t)))) * stroke_e ** 3 * .05
    seal = np.zeros(int(SR * d))
    at(seal, bell(880, .55, ((1, 1), (2.0, .3), (3.0, .12)), k=5) * .45, .42)
    at(seal, bell(1318.5, .5, ((1, 1), (2.0, .25)), k=6) * .3, .47)
    x = reverb(mix(scratch, squeak, seal), 1.0, 3.5, .3)
    save('assets/audio/sfx/redraw.ogg', fade(norm(x, .85)), 4)

def sfx_finisher():
    Rn = np.random.default_rng(2606)
    def nz(d): return Rn.uniform(-1, 1, int(SR * d))
    # finisher: добивающий удар — сухой хлёсткий щелчок мела, тяжёлый низкий удар, а за ними «время тянется»:
    # шорох уходит вниз по высоте, гул и мерцающий колокол долго тают в большом эхе.
    d = 1.7; t = T(d)
    snap = mix(hp(nz(.03), 3000) * dec(.03, 120), bp(nz(.06), 700, 2600) * dec(.06, 55) * .8)
    body = sine_sweep(150, 30, .9, 2.0) * dec(.9, 4.5) * 1.1
    stretch = np.zeros(int(SR * d))
    ws = 1.2; wt = T(ws)
    sweep = bp(nz(ws), 250, 5000) * np.sin(np.pi * np.clip(wt / ws, 0, 1)) ** 1.5
    # Полосу шороха ведём вниз: смешиваем светлую и тёмную полосы с уходящим весом.
    dark = lp(nz(ws), 600) * np.sin(np.pi * np.clip(wt / ws, 0, 1)) ** 1.5
    wgt = np.clip(wt / ws, 0, 1)
    at(stretch, (hp(sweep, 1800) * (1 - wgt) + dark * wgt * 1.4) * .45, .05)
    drone = lp(saw_f(np.interp(t, [0, d], [58, 46])), 220) * np.clip(t / .05, 0, 1) * np.exp(-t * 2.2) * .5
    shimmer = mix(bell(220, d, ((1, 1), (2.01, .4), (3.0, .15)), k=1.6) * .3, bell(221.5, d, ((1, 1), (2.0, .3)), k=1.8) * .25)
    x = reverb(mix(snap, body, stretch, drone, shimmer), 2.2, 2.2, .4)
    save('assets/audio/sfx/finisher.ogg', fade(norm(x, .9)), 4)
    # coin_drop: монетка влетает в счётчик — короткий звонкий «тинь» (высоту поднимает Hud по нотам).
    d = .28
    tink = bell(2637, d, ((1, 1), (2.0, .35), (3.01, .18), (4.2, .08)), k=18)
    click = pad(hp(nz(.006), 4000) * dec(.006, 600) * .5, int(SR * d))
    x = reverb(mix(tink, click), .4, 6, .18)
    save('assets/audio/sfx/coin_drop.ogg', fade(norm(x, .8)), 4)

GROUPS = {'combo': sfx_combo, 'perfect': sfx_perfect, 'bolt': sfx_bolt, 'windup': sfx_windup, 'wound': sfx_wound,
          'finisher': sfx_finisher}

if __name__ == '__main__':
    import sys
    os.makedirs('assets/audio/sfx', exist_ok=True); os.makedirs('assets/audio/music', exist_ok=True)
    # python3 tools/gen_audio.py combo perfect — только эти группы звуков, остальные файлы не трогаем
    only = set(sys.argv[1:])
    unknown = only - set(GROUPS)
    if unknown:
        sys.exit(f'неизвестные группы: {", ".join(sorted(unknown))}; есть: {", ".join(GROUPS)}')
    if not only:
        sfx()
        for name, fn in (('menu', m_menu), ('fight', m_fight), ('shop', m_shop), ('boss', m_boss)):
            save(f'assets/audio/music/{name}.ogg', norm(fn(), .85), 3)
    for name, fn in GROUPS.items():
        if not only or name in only:
            fn()
    print('audio done')
