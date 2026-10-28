extends Node
## Звук: пул SFX-плееров (узлы в audio.tscn, без создания в коде) + две музыкальные дорожки с кроссфейдом.

const SFX: Dictionary = {
    &"buy": preload("res://assets/audio/sfx/buy.ogg"),
    &"coin": preload("res://assets/audio/sfx/coin.ogg"),
    &"cast": preload("res://assets/audio/sfx/cast.ogg"),
    &"perfect": preload("res://assets/audio/sfx/perfect.ogg"),
    &"combo": preload("res://assets/audio/sfx/combo.ogg"),
    &"combo_break": preload("res://assets/audio/sfx/combo_break.ogg"),
    &"combo_up": preload("res://assets/audio/sfx/combo_up.ogg"),
    &"dodge": preload("res://assets/audio/sfx/dodge.ogg"),
    &"enemy_appear": preload("res://assets/audio/sfx/enemy_appear.ogg"),
    &"enemy_die": preload("res://assets/audio/sfx/enemy_die.ogg"),
    &"heartbeat": preload("res://assets/audio/sfx/heartbeat.ogg"),
    &"hit": preload("res://assets/audio/sfx/hit.ogg"),
    &"hit_big": preload("res://assets/audio/sfx/hit_big.ogg"),
    &"hurt": preload("res://assets/audio/sfx/hurt.ogg"),
    &"miss": preload("res://assets/audio/sfx/miss.ogg"),
    &"seal": preload("res://assets/audio/sfx/seal.ogg"),
    &"seal_appear": preload("res://assets/audio/sfx/seal_appear.ogg"),
    &"special": preload("res://assets/audio/sfx/special.ogg"),
    &"tick": preload("res://assets/audio/sfx/tick.ogg"),
    &"whiff": preload("res://assets/audio/sfx/whiff.ogg"),
    &"windup": preload("res://assets/audio/sfx/windup.ogg"),
    &"ignite": preload("res://assets/audio/sfx/ignite.ogg"),
    &"wipe": preload("res://assets/audio/sfx/wipe.ogg"),
    &"crack": preload("res://assets/audio/sfx/crack.ogg"),
    &"redraw": preload("res://assets/audio/sfx/redraw.ogg"),
    &"finisher": preload("res://assets/audio/sfx/finisher.ogg"),
    &"coin_drop": preload("res://assets/audio/sfx/coin_drop.ogg"),
}

const MUSIC: Dictionary = {
    &"menu": preload("res://assets/audio/music/menu.ogg"),
    &"fight": preload("res://assets/audio/music/fight.ogg"),
    &"shop": preload("res://assets/audio/music/shop.ogg"),
    &"boss": preload("res://assets/audio/music/boss.ogg"),
}

const SILENT_DB: float = -40.0

@onready var _music_a: AudioStreamPlayer = $MusicA
@onready var _music_b: AudioStreamPlayer = $MusicB
@onready var _pool: Array[Node] = $Sfx.get_children()

var _current: AudioStreamPlayer
var _music_name: StringName = &""
var _next: int = 0
var _tween: Tween
var _mute_reasons: Dictionary = {}
var _music_bus: int = -1

func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS
    _current = _music_a
    _music_bus = AudioServer.get_bus_index(&"Music")
    set_sound_enabled(bool(Save.data.get("sound", true)))

## pitch — точная высота (1.0 = как записано; комбо поднимает её нотами), pitch_jitter — случайный разброс вокруг неё.
func sfx(sound: StringName, volume_db: float = 0.0, pitch_jitter: float = 0.06, pitch: float = 1.0) -> void:
    var stream: AudioStream = SFX.get(sound)
    if stream == null:
        push_warning("Audio: unknown sfx %s" % sound)
        return
    var p: AudioStreamPlayer = _pick()
    p.stream = stream
    p.volume_db = volume_db
    p.pitch_scale = maxf(pitch * (1.0 + randf_range(-pitch_jitter, pitch_jitter)), 0.05)
    p.play()

func _pick() -> AudioStreamPlayer:
    var n: int = _pool.size()
    for i in n:
        var p: AudioStreamPlayer = _pool[(_next + i) % n]
        if not p.playing:
            _next = (_next + i + 1) % n
            return p
    var oldest: AudioStreamPlayer = _pool[_next]
    _next = (_next + 1) % n
    return oldest

## Сменить музыку с кроссфейдом. &"" — тишина.
func music(track: StringName, fade: float = 0.8, from_position: float = 0.0) -> void:
    if track == _music_name:
        return
    _music_name = track
    if _tween:
        _tween.kill()
    var old: AudioStreamPlayer = _current
    _tween = create_tween().set_parallel()
    _tween.tween_property(old, "volume_db", SILENT_DB, fade)
    if track != &"":
        var nxt: AudioStreamPlayer = _music_b if _current == _music_a else _music_a
        var stream: AudioStream = MUSIC.get(track)
        if stream is AudioStreamOggVorbis:
            (stream as AudioStreamOggVorbis).loop = true
        nxt.stream = stream
        nxt.volume_db = SILENT_DB
        nxt.play(from_position)
        _tween.tween_property(nxt, "volume_db", 0.0, fade)
        _current = nxt
    _tween.chain().tween_callback(old.stop)

## Глухая музыка (низкое здоровье / ослепление).
func set_muffled(on: bool) -> void:
    if _music_bus >= 0 and AudioServer.get_bus_effect_count(_music_bus) > 0:
        AudioServer.set_bus_effect_enabled(_music_bus, 0, on)

func set_muted(reason: StringName, on: bool) -> void:
    if on:
        _mute_reasons[reason] = true
    else:
        _mute_reasons.erase(reason)
    AudioServer.set_bus_mute(0, not _mute_reasons.is_empty())

func set_sound_enabled(on: bool) -> void:
    set_muted(&"user", not on)

func is_sound_enabled() -> bool:
    return not _mute_reasons.has(&"user")
