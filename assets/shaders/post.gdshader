// Full-screen post FX: chromatic aberration, vignette, film grain, hurt/low-hp/gold pulses.
shader_type canvas_item;

uniform sampler2D screen_tex : hint_screen_texture, filter_linear;
uniform sampler2D noise_tex : repeat_enable, filter_nearest;
uniform float vignette = 0.6;
uniform float aberration = 0.0012;
uniform float hurt : hint_range(0.0, 1.0) = 0.0;
uniform float gold : hint_range(0.0, 1.0) = 0.0;
uniform float low_hp : hint_range(0.0, 1.0) = 0.0;
uniform float grain = 0.055;
uniform float desaturate : hint_range(0.0, 1.0) = 0.0;
uniform float shock : hint_range(0.0, 1.0) = 0.0;
uniform float dark : hint_range(0.0, 1.0) = 0.0;

void fragment() {
	vec2 uv = SCREEN_UV;
	vec2 c = uv - 0.5;
	float d = length(c);
	float ab = aberration + hurt * 0.009 + gold * 0.004 + shock * 0.012;
	vec3 col;
	col.r = texture(screen_tex, uv + c * ab * 2.0).r;
	col.g = texture(screen_tex, uv).g;
	col.b = texture(screen_tex, uv - c * ab * 2.0).b;
	float g = dot(col, vec3(0.299, 0.587, 0.114));
	col = mix(col, vec3(g), desaturate);
	float vig = smoothstep(0.9, 0.18, d * (1.0 + vignette));
	col *= mix(1.0, vig, 0.85);
	col *= 1.0 - dark * smoothstep(0.05, 0.55, d) * 0.85;
	float pulse = 0.5 + 0.5 * sin(TIME * 6.0);
	float edge = smoothstep(0.22, 0.75, d);
	col = mix(col, vec3(0.7, 0.02, 0.03), edge * clamp(hurt * 0.9 + low_hp * 0.4 * pulse, 0.0, 1.0));
	col = mix(col, vec3(1.0, 0.86, 0.45), clamp(edge * gold * 0.75 + gold * 0.12, 0.0, 1.0));
	float n = texture(noise_tex, uv * vec2(3.7, 2.1) + fract(vec2(TIME * 13.1, TIME * 7.3))).r;
	col += (n - 0.5) * grain;
	COLOR = vec4(col, 1.0);
}
