"""Build hook to download Lightweight Charts JS at package build time."""

from __future__ import annotations

import urllib.request
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

LWC_VERSION = "5.1.0"
LWC_URL = f"https://cdn.jsdelivr.net/npm/lightweight-charts@{LWC_VERSION}/dist/lightweight-charts.standalone.production.js"
JS_DIR = Path(__file__).parent / "src" / "litecharts" / "js"
JS_FILE = JS_DIR / "lightweight-charts.js"


class CustomBuildHook(BuildHookInterface):
    """Download Lightweight Charts JS during build."""

    def initialize(self, version: str, build_data: dict) -> None:
        """Download LWC JS if not already present."""
        JS_DIR.mkdir(parents=True, exist_ok=True)

        if not JS_FILE.exists():
            print(f"Downloading Lightweight Charts v{LWC_VERSION}...")
            urllib.request.urlretrieve(LWC_URL, JS_FILE)
            print(f"Downloaded to {JS_FILE}")
