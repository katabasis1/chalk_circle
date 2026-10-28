// Creatures: hit flash, burn-dissolve, swirl (sealing), sway, glowing eyes, eye flare before an attack (2.4).
shader_type canvas_item;

uniform float flash : hint_range(0.0, 1.0) = 0.0;
uniform vec4 flash_color : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform float dissolve : hint_range(0.0, 1.0) = 0.0;
uniform vec4 burn_color : source_color = vec4(1.0, 0.42, 0.08, 1.0);
uniform float swirl : hint_range(0.0, 1.0) = 0.0;
uniform float wobble = 0.006;
uniform float eye_glow = 1.4;
// Замах (2.4): блик-«звёздочка» в глазах. Точки — в UV картинки (NpcData.eyes), размер — доля высоты.
uniform float eye_flash : hint_range(0.0, 1.0) = 0.0;
uniform vec4 eye_color : source_color = vec4(1.0, 0.3, 0.25, 1.0);
uniform int eye_count = 0;
uniform vec2 eye_a = vec2(0.4, 0.4);
uniform vec2 eye_b = vec2(0.6, 0.4);
uniform float eye_size = 0.02;
uniform sampler2D noise_tex : repeat_enable, filter_linear;

varying vec4 vcol;

void vertex() {
	vcol = COLOR;
}

// Блик одного глаза: белое ядро + цветной ореол + длинный горизонтальный и короткий вертикальный лучи.
// q — смещение от глаза в долях высоты картинки (уже с поправкой на соотношение сторон).
vec2 glint(vec2 q, float s) {
	float core = exp(-dot(q, q) / (s * s));
	float halo = exp(-length(q) / (s * 2.4)) * 0.55;
	float ray_h = exp(-abs(q.y) / (s * 0.2)) * exp(-abs(q.x) / (s * 7.0));
	float ray_v = exp(-abs(q.x) / (s * 0.2)) * exp(-abs(q.y) / (s * 3.5)) * 0.7;
	return vec2(core, halo + ray_h + ray_v);
}

void fragment() {
	vec2 uv = UV;
	uv.x += sin(TIME * 2.1 + uv.y * 8.0) * wobble * (1.0 - uv.y);
	vec2 c = uv - 0.5;
	float ang = swirl * 10.0 * (1.0 - clamp(length(c) * 1.4, 0.0, 1.0));
	float s = sin(ang);
	float co = cos(ang);
	c = mat2(vec2(co, -s), vec2(s, co)) * c;
	c *= 1.0 + swirl * 1.6;
	uv = c + 0.5;
	vec4 col = texture(TEXTURE, uv);
	float inside = step(0.0, uv.x) * step(uv.x, 1.0) * step(0.0, uv.y) * step(uv.y, 1.0);
	col.a *= inside;
	float lum = dot(col.rgb, vec3(0.299, 0.587, 0.114));
	float hot = smoothstep(0.62, 0.95, lum) * (0.8 + 0.2 * sin(TIME * 5.0));
	col.rgb += col.rgb * hot * (eye_glow - 1.0);
	float n = texture(noise_tex, UV * 1.7).r;
	float edge = smoothstep(dissolve - 0.09, dissolve, n);
	col.rgb = mix(burn_color.rgb * 2.2, col.rgb, edge);
	col.a *= dissolve > 0.001 ? step(dissolve, n) : 1.0;
	if (eye_flash > 0.001 && eye_count > 0) {
		vec2 asp = vec2(TEXTURE_PIXEL_SIZE.y / TEXTURE_PIXEL_SIZE.x, 1.0);
		vec2 g = glint((uv - eye_a) * asp, eye_size);
		if (eye_count > 1) {
			g += glint((uv - eye_b) * asp, eye_size);
		}
		float k = eye_flash * (0.88 + 0.12 * sin(TIME * 41.0)) * inside * (1.0 - dissolve);
		float core = clamp(g.x, 0.0, 1.0);
		vec3 light = mix(eye_color.rgb, vec3(1.0), core) * (g.x + g.y) * k;
		float la = clamp((core + g.y) * k, 0.0, 1.0);
		// Свет поверх спрайта: складываем «предумноженно», чтобы блик светился и на прозрачном фоне вокруг глаза.
		float out_a = max(col.a, la);
		col.rgb = min((col.rgb * col.a + light) / max(out_a, 0.001), vec3(1.6));
		col.a = out_a;
		// И сама нечисть чуть наливается цветом глаз.
		col.rgb = mix(col.rgb, eye_color.rgb, eye_flash * 0.08 * col.a);
	}
	col.rgb = mix(col.rgb, flash_color.rgb, flash * col.a);
	col.rgb = mix(col.rgb, vec3(1.0, 0.86, 0.45), swirl * 0.7);
	COLOR = col * vcol;
}
