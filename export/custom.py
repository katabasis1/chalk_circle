# SCons-профиль лёгкого web-шаблона экспорта для «Мелового круга».
# Игра: только 2D, рендер GL Compatibility, GDScript, звук .ogg, шрифты TTF, без потоков и GDExtension.
# Использование (из папки исходников Godot 4.7-stable):
#   scons profile=<путь>/export/custom.py [build_profile=<путь>/export/chalk.gdbuild]
# Неизвестные этой версии Godot переменные SCons просто проигнорирует с предупреждением — это безопасно.

platform = "web"
target = "template_release"
production = "yes"
debug_symbols = "no"
optimize = "size_extra"     # если версия ругается — замени на "size"
lto = "full"

# Яндекс Игры не дают SharedArrayBuffer (нет COOP/COEP) → однопоточная сборка. В export_presets: variant/thread_support=false.
threads = "no"
# Без GDExtension (variant/extensions_support=false) — меньше JS-обвязки.
dlink_enabled = "no"

# ---- крупные подсистемы, которые игре не нужны ----
disable_3d = "yes"
# Убирает «тяжёлые» Control-ы (RichTextLabel, TextEdit, CodeEdit, GraphEdit, Tree, FileDialog, ColorPicker…).
# Label, Button, TextureRect и контейнеры остаются. Если позже понадобится RichTextLabel — поставь "no".
disable_advanced_gui = "yes"
disable_physics_3d = "yes"      # Godot 4.5+
disable_navigation_3d = "yes"   # Godot 4.5+
disable_navigation_2d = "yes"   # Godot 4.5+ (навигация не используется)
disable_xr = "yes"              # Godot 4.5+
deprecated = "no"
minizip = "no"
brotli = "no"
vulkan = "no"
opengl3 = "yes"                 # GL Compatibility = WebGL2
openxr = "no"
use_volk = "no"

# ---- модули ----
# Текст: «запасной» сервер без ICU/HarfBuzz. Кириллица, латиница и турецкий работают; арабский/хинди — нет (нам не нужны).
module_text_server_adv_enabled = "no"
module_text_server_fb_enabled = "yes"
module_freetype_enabled = "yes"
module_msdfgen_enabled = "no"   # MSDF-шрифты не используются

# Нужно: GDScript, OGG Vorbis (музыка и звуки), WebP (Godot хранит текстуры «Lossless» в WebP), PNG — в ядре.
module_gdscript_enabled = "yes"
module_ogg_enabled = "yes"
module_vorbis_enabled = "yes"
module_webp_enabled = "yes"
module_interactive_music_enabled = "yes"   # слоистая музыка этапа 3 (AudioStreamInteractive / Synchronized)
module_bcdec_enabled = "yes"               # распаковка VRAM-текстур, если браузер не умеет S3TC/BPTC
module_godot_physics_2d_enabled = "yes"    # 2D-физика не используется, но сервер нужен движку; модуль маленький

# Не нужно игре:
module_gltf_enabled = "no"
module_fbx_enabled = "no"
module_csg_enabled = "no"
module_gridmap_enabled = "no"
module_navigation_2d_enabled = "no"
module_navigation_3d_enabled = "no"
module_godot_physics_3d_enabled = "no"
module_jolt_physics_enabled = "no"
module_openxr_enabled = "no"
module_mobile_vr_enabled = "no"
module_webxr_enabled = "no"
module_raycast_enabled = "no"
module_lightmapper_rd_enabled = "no"
module_xatlas_unwrap_enabled = "no"
module_meshoptimizer_enabled = "no"
module_vhacd_enabled = "no"
module_denoise_enabled = "no"
module_noise_enabled = "no"
module_theora_enabled = "no"
module_minimp3_enabled = "no"
module_mbedtls_enabled = "no"
module_websocket_enabled = "no"
module_webrtc_enabled = "no"
module_enet_enabled = "no"
module_multiplayer_enabled = "no"
module_upnp_enabled = "no"
module_jsonrpc_enabled = "no"
module_regex_enabled = "no"
module_camera_enabled = "no"
module_svg_enabled = "no"       # SVG импортируются в редакторе; в рантайме не нужны
module_tga_enabled = "no"
module_hdr_enabled = "no"
module_jpg_enabled = "no"
module_bmp_enabled = "no"
module_dds_enabled = "no"
module_ktx_enabled = "no"
module_basis_universal_enabled = "no"
module_astcenc_enabled = "no"
module_etcpak_enabled = "no"
module_cvtt_enabled = "no"
module_squish_enabled = "no"
module_glslang_enabled = "no"
module_mono_enabled = "no"
module_zip_enabled = "no"
