// The chalk circle: rough grainy line + faint inner line + dust halo.
// Раны (2.5): трещины на черте. Каждая — рваный косой разрыв с тлеющим красным швом, волосяные трещины
// вдоль мела от обоих концов, сколы по краям и крошки мела рядом (больше внутрь — нечисть ломилась снаружи).
// Лечение — золотое свечение, разрыв затягивается. Данные трещин шлёт scenes/ring/ring.gd (_update_cracks).
// Превью без Godot: numpy-порт в tools/preview_chalk_ring.py (держи в синхроне с этим файлом).
shader_type canvas_item;

const int MAX_CRACKS = 16;

uniform sampler2D noise_tex : repeat_enable, filter_linear;
uniform vec4 chalk : source_color = vec4(0.92, 0.9, 0.83, 1.0);
uniform float radius = 0.714;
uniform float width = 0.03;
uniform float pulse : hint_range(0.0, 1.0) = 0.0;
uniform float danger : hint_range(0.0, 1.0) = 0.0;
// Трещины: заполнены первые crack_count. Угол (рад), раскрытие 0..1, вспышка раны 0..1, свечение лечения 0..1.
uniform int crack_count = 0;
uniform float crack_angle[16];
uniform float crack_open[16];
uniform float crack_hot[16];
uniform float crack_heal[16];

float h11(float x) {
	return fract(sin(x * 127.1) * 43758.5453);
}

void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float r = length(p);
	float a = atan(p.y, p.x);
	float n1 = texture(noise_tex, vec2(a / TAU * 5.0, r * 1.5)).r;
	float n2 = texture(noise_tex, p * 3.3 + vec2(0.37, 0.11)).r;
	float wob = (n1 - 0.5) * 0.024;
	float d = abs(r - radius + wob);
	float line = smoothstep(width, width * 0.35, d);
	float grain = smoothstep(0.3, 0.72, n2 + (1.0 - line) * 0.25);
	float ca = line * mix(0.45, 1.0, grain);
	float d2 = abs(r - radius * 0.885 + wob * 0.5);
	float inner = smoothstep(0.007, 0.002, d2) * 0.4 * grain;

	float cut = 0.0;
	float bits = 0.0;
	float ember = 0.0;
	float gold = 0.0;
	float halo_k = 1.0;
	// Радиальное смещение от середины (волнистой) черты: трещины идут вместе с ней.
	float t = r - radius + wob;
	if (crack_count > 0 && abs(t) < 0.12) {
		for (int i = 0; i < MAX_CRACKS; i++) {
			if (i >= crack_count) {
				break;
			}
			float ang = crack_angle[i];
			float da = mod(a - ang + PI, TAU) - PI;
			if (abs(da) > 0.4) {
				continue;
			}
			float amt = crack_open[i];
			float sd = h11(ang + float(i) * 0.731);
			float s = da * radius;
			float side = s < 0.0 ? -1.0 : 1.0;
			// Разрыв косой (slant) и рваный: ширина гуляет поперёк черты (шум + зубцы).
			float slant = (h11(sd + 5.0) - 0.5) * 1.2;
			float sp = s - t * slant;
			float jag = textureLod(noise_tex, vec2(sd * 7.0 + side * 0.29, t * 14.0 + sd), 0.0).r;
			float zig = abs(fract(t * 38.0 + sd * 3.0 + side * 0.5) - 0.5) * 2.0;
			float gw = amt * (0.019 + 0.03 * jag + 0.01 * zig);
			float band = smoothstep(0.05, 0.03, abs(t));
			float gap = (1.0 - smoothstep(gw * 0.7, gw + 0.0025, abs(sp))) * band;
			// Волосяные трещины вдоль мела от концов разрыва + ответвление.
			float L = amt * (0.11 + 0.08 * sd);
			float along = abs(sp) - gw;
			float fis = 0.0;
			if (along > 0.0 && along < L) {
				float k = along / L;
				float w1 = textureLod(noise_tex, vec2(sd * 3.0 + side * 0.41, along * 6.0), 0.0).r - 0.5;
				float fr = w1 * width * 2.6 * (0.4 + k);
				fis = smoothstep(0.005, 0.0014, abs(t - fr)) * (1.0 - k * k);
				float fr2 = fr + side * (h11(sd + 3.0) - 0.5) * 2.0 * width * 1.8 * smoothstep(0.2, 1.0, k);
				fis = max(fis, smoothstep(0.0035, 0.001, abs(t - fr2)) * smoothstep(0.15, 0.3, k) * (1.0 - k));
			}
			// Сколы по краям черты возле разрыва.
			float bite_n = textureLod(noise_tex, vec2(sp * 7.0 + sd * 5.0, t * 7.0 + sd), 0.0).r;
			float bite = smoothstep(0.55, 0.6, bite_n) * smoothstep(L * 0.8 + gw, gw, abs(sp)) * smoothstep(0.002, 0.008, abs(t)) * amt;
			cut = max(cut, max(gap, max(fis, bite)));
			// Крошки мела: четыре внутрь круга, две наружу. Разлетаются по мере раскрытия.
			for (int j = 0; j < 6; j++) {
				float hh1 = h11(sd * 13.0 + float(j) * 1.7);
				float hh2 = h11(sd * 29.0 + float(j) * 2.3);
				vec2 c = vec2((hh1 - 0.5) * 0.1, j >= 4 ? 0.016 + hh2 * 0.03 : -0.016 - hh2 * 0.05) * amt;
				float sz = (0.0035 + 0.004 * h11(hh1 * 7.0)) * min(amt * 2.0, 1.0);
				bits = max(bits, smoothstep(sz, sz * 0.35, length(vec2(s, t) - c)));
			}
			// Тлеющий шов в щели (зигзаг), вспышка в миг раны, золото при лечении.
			float sc = (textureLod(noise_tex, vec2(sd * 5.0 + 0.5, t * 20.0), 0.0).r - 0.5) * gw * 1.1;
			float seam = abs(sp - sc);
			float flick = 0.75 + 0.25 * sin(TIME * 2.7 + sd * 31.0);
			ember += (smoothstep(0.0055, 0.001, seam) * 0.95 + exp(-seam * 80.0) * 0.35) * smoothstep(0.032, 0.012, abs(t)) * amt * flick;
			float dist = length(vec2(s * 0.7, t));
			ember += crack_hot[i] * exp(-dist * 28.0) * 1.4;
			gold += crack_heal[i] * exp(-dist * 22.0) * 1.3;
			float q = sp / (gw + 0.012);
			float soft = exp(-q * q) * amt;
			halo_k = min(halo_k, 1.0 - soft * 0.75);
		}
	}
	ca *= 1.0 - cut;
	ca = max(ca, max(inner, bits * 0.8 * mix(0.55, 1.0, grain)));
	float halo = exp(-d * 16.0) * (0.16 + pulse * 0.5) * halo_k;
	vec3 col = mix(chalk.rgb, vec3(1.0, 0.22, 0.18), danger * 0.65);
	float base = clamp(ca + halo, 0.0, 1.0);
	ember = clamp(ember, 0.0, 1.0);
	gold = clamp(gold, 0.0, 1.0);
	vec3 glow = vec3(1.0, 0.28, 0.1) * ember + vec3(1.0, 0.85, 0.45) * gold;
	float alpha = clamp(base + ember * 0.7 + gold, 0.0, 1.0);
	vec3 rgb = (col * base + glow) / max(alpha, 0.001);
	COLOR = vec4(min(rgb, vec3(1.0)), alpha * COLOR.a);
}
