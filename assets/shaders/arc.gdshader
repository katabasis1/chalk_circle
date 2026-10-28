// Ring section: glowing annular arc. Driven by Section (center/arc_size) and AnimationPlayer (grow/flash/alpha).
shader_type canvas_item;

uniform float center = 0.0;
uniform float arc_size = 0.5;
uniform float grow : hint_range(0.0, 1.0) = 1.0;
uniform float r_in = 0.70;
uniform float r_out = 0.84;
uniform vec4 color : source_color = vec4(0.94, 0.91, 0.84, 1.0);
uniform vec4 glow_color : source_color = vec4(1.0, 0.82, 0.48, 1.0);
uniform float flash : hint_range(0.0, 1.0) = 0.0;
uniform float alpha : hint_range(0.0, 1.0) = 1.0;
uniform float hot : hint_range(0.0, 1.0) = 0.0;
uniform float active : hint_range(0.0, 1.0) = 0.0;
// «Идеально» (2.2): полуширина зоны центра в радианах; 0 — не показывать (UI, Печать, дуги здоровья).
uniform float perfect_zone = 0.0;
// Замах нечисти (2.4): warn=1 — секция ещё «заряжается»: вместо дуги бегущий пунктирный контур
// и заливка, растущая от центра к краям по мере charge 0→1. Потом секция вспыхивает и становится обычной.
uniform float warn : hint_range(0.0, 1.0) = 0.0;
uniform float charge : hint_range(0.0, 1.0) = 0.0;
// Сила ореола вокруг дуги (2.7): след на дуге здоровья светит слабее, чтобы не засвечивать красную дугу над ним.
uniform float glow_amount : hint_range(0.0, 1.0) = 1.0;
uniform sampler2D noise_tex : repeat_enable, filter_linear;

void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float r = length(p);
	float a = atan(p.y, p.x);
	float d = abs(mod(a - center + PI, TAU) - PI);
	float hw = max(arc_size * grow * 0.5, 0.0);
	float n = texture(noise_tex, vec2(a / TAU * 4.0 + TIME * 0.03, r * 1.3 - TIME * 0.45 * hot)).r;
	float wob = (n - 0.5) * 0.045 * hot;
	float ang_sd = (hw - d) * r;
	float rad_sd = min(r - r_in, r_out - r) + wob;
	float sd = min(ang_sd, rad_sd);
	float aa = fwidth(sd) + 0.002;
	float body = smoothstep(-aa, aa, sd);
	float core = smoothstep(0.0, 0.05, sd);
	float glow = exp(-max(-sd, 0.0) * 26.0);
	vec3 col = mix(color.rgb * 0.8, color.rgb * 1.2, core);
	col += (n - 0.4) * 0.35 * hot * glow_color.rgb;
	float pz = 0.0;
	if (perfect_zone > 0.0) {
		pz = 1.0 - smoothstep(perfect_zone * 0.8, perfect_zone, d);
		col = mix(col, min(col * 1.3, vec3(1.0)), pz * core * 0.6);
	}
	col = mix(col, vec3(1.0), flash);
	float ga = glow * (0.5 + 0.3 * active + 0.7 * flash) * glow_amount * (1.0 - body);
	vec3 outc = mix(glow_color.rgb, col, body);
	float outa = max(body, ga);
	if (perfect_zone > 0.0) {
		// Риска центра: короткий светлый штрих наружу от дуги — «бей сюда».
		float tick = (1.0 - smoothstep(0.006, 0.006 + aa, d * r))
			* smoothstep(r_out - 0.01, r_out, r) * (1.0 - smoothstep(r_out + 0.03, r_out + 0.04, r)) * step(0.5, grow);
		outc = mix(outc, mix(glow_color.rgb, vec3(1.0), 0.5), tick);
		outa = max(outa, tick * 0.9);
	}
	if (warn > 0.0) {
		// Контур: тонкая линия по границе дуги, пунктир «бежит» по периметру — d·r вдоль дуги, r — по торцам.
		float line = 1.0 - smoothstep(0.004, 0.004 + aa, abs(sd));
		float dash = smoothstep(0.35, 0.45, fract((d * r + r) * 34.0 - TIME * 3.0));
		float blink = 0.65 + 0.35 * sin(TIME * 22.0);
		// Заливка растёт от центра секции к краям — видно, сколько осталось до удара.
		float fill_sd = min((hw * charge - d) * r, rad_sd);
		float fill = smoothstep(-aa, aa, fill_sd) * (0.22 + 0.33 * charge * charge);
		vec3 wc = mix(color.rgb, glow_color.rgb, 0.35);
		float wa = max(line * dash * blink, fill);
		outc = mix(outc, wc, warn);
		outa = mix(outa, wa, warn);
	}
	COLOR = vec4(outc, outa * alpha);
}
