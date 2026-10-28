// Ink-blot screen transition. progress: 0 clear -> 1 fully covered -> 2 clear again (opens from center).
shader_type canvas_item;

uniform sampler2D noise_tex : repeat_enable, filter_linear;
uniform float progress : hint_range(0.0, 2.0) = 0.0;
uniform vec4 ink : source_color = vec4(0.02, 0.012, 0.016, 1.0);
uniform vec4 rim : source_color = vec4(0.5, 0.03, 0.05, 1.0);

void fragment() {
	float aspect = SCREEN_PIXEL_SIZE.y / SCREEN_PIXEL_SIZE.x;
	vec2 p = (UV - 0.5) * vec2(aspect, 1.0);
	float n = texture(noise_tex, UV * vec2(aspect, 1.0) * 1.2).r;
	float field = length(p) / max(aspect, 1.0) * 1.1 + (n - 0.5) * 0.5;
	float cover = progress <= 1.0 ? progress : 2.0 - progress;
	float th = mix(1.2, -0.4, cover);
	float a = smoothstep(th - 0.012, th + 0.012, field);
	float inner = smoothstep(th, th + 0.07, field);
	COLOR = vec4(mix(rim.rgb, ink.rgb, inner), a * ink.a);
}
