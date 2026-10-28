// Drifting ground fog over the background.
shader_type canvas_item;

uniform sampler2D noise_tex : repeat_enable, filter_linear;
uniform vec4 fog_color : source_color = vec4(0.55, 0.66, 0.62, 1.0);
uniform float density = 0.42;
uniform float speed = 0.015;

void fragment() {
	float aspect = SCREEN_PIXEL_SIZE.y / SCREEN_PIXEL_SIZE.x;
	vec2 p = vec2(UV.x * aspect, UV.y);
	float n1 = texture(noise_tex, p * 0.7 + vec2(TIME * speed, 0.0)).r;
	float n2 = texture(noise_tex, p * 1.5 + vec2(-TIME * speed * 1.8, TIME * speed * 0.4)).r;
	float n = n1 * 0.6 + n2 * 0.4;
	float band = smoothstep(0.3, 1.0, UV.y) * 0.85 + 0.15;
	float a = smoothstep(0.38, 0.9, n) * density * band;
	COLOR = vec4(fog_color.rgb, a);
}
