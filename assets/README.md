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

Current seeded assets:
- UI themes at `images/ui/theme_default*.png` (sd/hd/uhd)
- UI kit: `panel_dark`, `button_primary`, icons (play/pause/close/settings)
- Procedural PBR packs: `metal_plate`, `wood_oak`, `concrete_brushed`, `fabric_canvas`, `emissive_grid`, `rock_slate`, `sand_dune`
- **Organic CC0 PBR packs (4K, from AmbientCG)**:
  - `pbr/organic/bark`: tree bark with grain patterns
  - `pbr/organic/fabric_cotton`: woven cotton fabric with realistic weave
  - `pbr/organic/leaf`: plant leaf texture with veins and translucency support
- Skyboxes: `clear_skies`, `sunset_glow`
- Audio: UI (click/hover/confirm/error/swoosh/ping) and ambience (wind/rain/city/forest), plus `sfx/footstep_soft`

All CC0 packs are licensed under CC0 (public domain) and sourced from https://ambientcg.com.

AssetManager highlights:
- Manifest-driven resolution with quality tier selection
- Dot-path loads for images/sounds/fonts/materials
- Procedural texture generator for rapid prototyping
- Graceful fallbacks for missing assets (placeholder visuals/silence)
