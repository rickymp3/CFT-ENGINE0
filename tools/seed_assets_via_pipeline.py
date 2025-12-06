"""Seed local assets into the AssetPipeline cache.

Usage (local import):
    python tools/seed_assets_via_pipeline.py

If you have cloud storage credentials, set DROPBOX_TOKEN or BOX_TOKEN and
add remote paths to SOURCE_ASSETS. The script will import locally by default.
"""
from pathlib import Path
import os

from engine_modules.asset_pipeline import AssetPipeline

BASE = Path(__file__).resolve().parent.parent
ASSETS = BASE / "assets"

# Local sources to import (relative to repo root)
SOURCE_ASSETS = [
    ASSETS / "images/pbr/metal_plate_albedo.png",
    ASSETS / "images/pbr/wood_oak_albedo.png",
    ASSETS / "images/pbr/rock_slate_albedo.png",
    ASSETS / "images/pbr/sand_dune_albedo.png",
    ASSETS / "images/skybox/clear_skies/clear_skies_px.png",
    ASSETS / "images/skybox/sunset_glow/sunset_glow_px.png",
    ASSETS / "sounds/ui/click.wav",
    ASSETS / "sounds/ui/ping.wav",
    ASSETS / "sounds/ambience/forest_birds.wav",
]


def main():
    pipe = AssetPipeline(cache_dir=str(BASE / "asset_cache"))

    # Optional cloud registration (no-op if tokens missing)
    dropbox_token = os.getenv("DROPBOX_TOKEN")
    if dropbox_token:
        try:
            pipe.register_dropbox(dropbox_token)
        except Exception as exc:
            print(f"Dropbox registration skipped: {exc}")

    for src in SOURCE_ASSETS:
        if not src.exists():
            print(f"Skip missing: {src}")
            continue
        asset_id = pipe.import_asset(str(src), asset_type="texture", name=src.stem, tags=["seeded"])
        print(f"Imported {src} -> {asset_id}")


if __name__ == "__main__":
    main()
