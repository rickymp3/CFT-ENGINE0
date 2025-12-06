"""Test suite for the CFT Panda3D 3D engine."""
import os
import pytest
from cft_panda3d_engine import load_translations, TRANSLATIONS


def test_load_translations_english():
    """Test loading English translations."""
    trans = load_translations("en")
    assert trans["title"] == "CFT AAA Engine"
    assert trans["prompt_start"] == "Press Enter to Start"
    assert trans["prompt_quit"] == "Press Escape to Quit"


def test_load_translations_spanish():
    """Test loading Spanish translations."""
    trans = load_translations("es")
    assert trans["title"] == "Motor AAA de CFT"
    assert "Intro" in trans["prompt_start"]


def test_load_translations_french():
    """Test loading French translations."""
    trans = load_translations("fr")
    assert trans["title"] == "Moteur AAA CFT"
    assert "Entrée" in trans["prompt_start"]


def test_load_translations_fallback():
    """Test fallback to English for unsupported language."""
    trans = load_translations("unsupported")
    assert trans["title"] == "CFT AAA Engine"


def test_translations_dict_structure():
    """Test that all languages have required keys."""
    required_keys = {"title", "prompt_start", "prompt_quit"}
    for lang_code, lang_dict in TRANSLATIONS.items():
        assert required_keys.issubset(lang_dict.keys()), \
            f"Language '{lang_code}' missing required keys"


def test_cft_game_import():
    """Test that CFTGame can be imported without errors."""
    from cft_panda3d_engine import CFTGame
    assert CFTGame is not None
    assert hasattr(CFTGame, 'setup_lights')
    assert hasattr(CFTGame, 'setup_environment')
    assert hasattr(CFTGame, 'load_game_scene')
