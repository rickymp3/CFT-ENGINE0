# Asset directories for CFT-ENGINE0

Place your game assets in these directories (AAA-ready scaffold):

## /images
- UI skins, sprite sheets, backgrounds, PBR texture maps
- Subfolders: `ui/`, `pbr/`, `fx/`
- Formats: PNG (preferred), JPG, HDR for skyboxes

## /materials
- JSON descriptors for PBR packs (albedo/normal/metallic/roughness/ao)
- Reference texture paths relative to this folder

## /sounds
- `ui/` for clicks/menus, `ambience/` for loops, `sfx/` for spot FX
- Formats: WAV (lossless), OGG (compressed)

## /fonts
- TTF/OTF primary and fallback families for UI and in-world text

## /music
- Background music tracks (loop-ready)

## Manifest
- `assets/manifest.yaml` registers canonical asset IDs, tags, and quality tiers (sd/hd/uhd)
- Variants may point to higher-res versions per ID

Current seeded placeholders (safe to replace):
- UI themes at `images/ui/theme_default*.png` (sd/hd/uhd)
- UI kit: `panel_dark`, `button_primary`, icons (play/pause/close/settings)
- PBR packs: `metal_plate`, `wood_oak`, `concrete_brushed`, `fabric_canvas`, `emissive_grid`, `rock_slate`, `sand_dune`
- Skyboxes: `clear_skies`, `sunset_glow`
- Audio: UI (click/hover/confirm/error/swoosh/ping) and ambience (wind/rain/city/forest), plus `sfx/footstep_soft`

AssetManager highlights:
- Manifest-driven resolution with quality tier selection
- Dot-path loads for images/sounds/fonts/materials
- Procedural texture generator for rapid prototyping
- Graceful fallbacks for missing assets (placeholder visuals/silence)
