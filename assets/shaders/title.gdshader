// Twitchy title text.
shader_type canvas_item;

uniform float jitter = 1.6;

void vertex() {
	float t = floor(TIME * 10.0);
	VERTEX.x += (fract(sin(t * 12.9898 + VERTEX.y * 0.071) * 43758.5453) - 0.5) * jitter;
	VERTEX.y += (fract(sin(t * 78.233 + VERTEX.x * 0.053) * 12543.123) - 0.5) * jitter * 0.6;
}
