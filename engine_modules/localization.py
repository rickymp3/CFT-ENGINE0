"""Localization system with externalized translation files.

Features:
- JSON/YAML translation files
- Runtime language switching
- Fallback to default language
- String formatting support
- Plural forms handling
"""
import json
import logging
from typing import Dict, Optional, Any
from pathlib import Path

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    logging.warning("pyyaml not installed for YAML support")

logger = logging.getLogger(__name__)


class Localization:
    """Localization manager for multi-language support."""
    
    def __init__(self, locale_dir: str = "./locales", default_language: str = "en"):
        """Initialize localization system.
        
        Args:
            locale_dir: Directory containing translation files
            default_language: Default language code (e.g., 'en', 'es', 'fr')
        """
        self.locale_dir = Path(locale_dir)
        self.locale_dir.mkdir(exist_ok=True)
        
        self.default_language = default_language
        self.current_language = default_language
        
        # Translation dictionaries by language
        self.translations: Dict[str, Dict[str, str]] = {}
        
        # Load all available translations
        self._load_translations()
        
        logger.info(f"Localization initialized (default: {default_language})")
    
    def _load_translations(self) -> None:
        """Load all translation files from locale directory."""
        # Look for JSON and YAML files
        for file_path in self.locale_dir.glob("*.json"):
            lang_code = file_path.stem
            self._load_json(lang_code, file_path)
        
        if YAML_AVAILABLE:
            for file_path in self.locale_dir.glob("*.yaml"):
                lang_code = file_path.stem
                self._load_yaml(lang_code, file_path)
            
            for file_path in self.locale_dir.glob("*.yml"):
                lang_code = file_path.stem
                self._load_yaml(lang_code, file_path)
        
        logger.info(f"Loaded translations for: {', '.join(self.translations.keys())}")
    
    def _load_json(self, lang_code: str, file_path: Path) -> bool:
        """Load JSON translation file.
        
        Args:
            lang_code: Language code
            file_path: Path to JSON file
            
        Returns:
            True if successful
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.translations[lang_code] = json.load(f)
            logger.debug(f"Loaded JSON translations: {lang_code}")
            return True
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            return False
    
    def _load_yaml(self, lang_code: str, file_path: Path) -> bool:
        """Load YAML translation file.
        
        Args:
            lang_code: Language code
            file_path: Path to YAML file
            
        Returns:
            True if successful
        """
        if not YAML_AVAILABLE:
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.translations[lang_code] = yaml.safe_load(f)
            logger.debug(f"Loaded YAML translations: {lang_code}")
            return True
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            return False
    
    def set_language(self, lang_code: str) -> bool:
        """Set the current language.
        
        Args:
            lang_code: Language code (e.g., 'en', 'es', 'fr')
            
        Returns:
            True if language is available
        """
        if lang_code in self.translations:
            self.current_language = lang_code
            logger.info(f"Language set to: {lang_code}")
            return True
        else:
            logger.warning(f"Language not available: {lang_code}")
            return False
    
    def get_language(self) -> str:
        """Get current language code.
        
        Returns:
            Current language code
        """
        return self.current_language
    
    def get_available_languages(self) -> list:
        """Get list of available language codes.
        
        Returns:
            List of language codes
        """
        return list(self.translations.keys())
    
    def translate(self, key: str, language: Optional[str] = None, **kwargs) -> str:
        """Translate a string key.
        
        Args:
            key: Translation key (e.g., 'ui.menu.file')
            language: Language code (uses current if None)
            **kwargs: Format arguments for string formatting
            
        Returns:
            Translated string or key if not found
        """
        lang = language or self.current_language
        
        # Try requested language
        if lang in self.translations:
            translation = self._get_nested_value(self.translations[lang], key)
            if translation:
                return self._format_string(translation, **kwargs)
        
        # Fallback to default language
        if lang != self.default_language and self.default_language in self.translations:
            translation = self._get_nested_value(self.translations[self.default_language], key)
            if translation:
                logger.debug(f"Using fallback translation for: {key}")
                return self._format_string(translation, **kwargs)
        
        # Return key if no translation found
        logger.warning(f"Translation not found: {key} ({lang})")
        return key
    
    def _get_nested_value(self, data: Dict, key: str) -> Optional[str]:
        """Get value from nested dictionary using dot notation.
        
        Args:
            data: Dictionary to search
            key: Dot-separated key (e.g., 'ui.menu.file')
            
        Returns:
            Value or None if not found
        """
        keys = key.split('.')
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        
        return str(current) if current is not None else None
    
    def _format_string(self, template: str, **kwargs) -> str:
        """Format string with arguments.
        
        Args:
            template: String template
            **kwargs: Format arguments
            
        Returns:
            Formatted string
        """
        if not kwargs:
            return template
        
        try:
            return template.format(**kwargs)
        except Exception as e:
            logger.error(f"String formatting error: {e}")
            return template
    
    def plural(self, key: str, count: int, language: Optional[str] = None) -> str:
        """Get plural form of a translation.
        
        Args:
            key: Translation key
            count: Count for plural form
            language: Language code (uses current if None)
            
        Returns:
            Appropriate plural form
        """
        lang = language or self.current_language
        
        # Try to get plural forms
        plural_key = f"{key}_plural"
        
        if count == 1:
            return self.translate(key, language, count=count)
        else:
            # Try plural form first
            translation = self.translate(plural_key, language, count=count)
            if translation != plural_key:
                return translation
            # Fallback to singular
            return self.translate(key, language, count=count)
    
    def add_translation(self, lang_code: str, key: str, value: str) -> None:
        """Add or update a translation at runtime.
        
        Args:
            lang_code: Language code
            key: Translation key
            value: Translation value
        """
        if lang_code not in self.translations:
            self.translations[lang_code] = {}
        
        # Handle nested keys
        keys = key.split('.')
        current = self.translations[lang_code]
        
        for i, k in enumerate(keys[:-1]):
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
        logger.debug(f"Added translation: {lang_code}.{key} = {value}")
    
    def save_language(self, lang_code: str, format: str = 'json') -> bool:
        """Save translations for a language to file.
        
        Args:
            lang_code: Language code
            format: File format ('json' or 'yaml')
            
        Returns:
            True if successful
        """
        if lang_code not in self.translations:
            logger.error(f"Language not loaded: {lang_code}")
            return False
        
        try:
            if format == 'json':
                file_path = self.locale_dir / f"{lang_code}.json"
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.translations[lang_code], f, indent=2, ensure_ascii=False)
            
            elif format == 'yaml':
                if not YAML_AVAILABLE:
                    logger.error("YAML not available")
                    return False
                
                file_path = self.locale_dir / f"{lang_code}.yaml"
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(self.translations[lang_code], f, allow_unicode=True, default_flow_style=False)
            
            else:
                logger.error(f"Unsupported format: {format}")
                return False
            
            logger.info(f"Saved translations: {lang_code} ({format})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save translations: {e}")
            return False
    
    def create_template(self, lang_code: str, keys: list) -> None:
        """Create a translation template with placeholder values.
        
        Args:
            lang_code: Language code
            keys: List of translation keys
        """
        if lang_code not in self.translations:
            self.translations[lang_code] = {}
        
        for key in keys:
            if not self._get_nested_value(self.translations[lang_code], key):
                self.add_translation(lang_code, key, f"[{key}]")
        
        logger.info(f"Created template for {lang_code} with {len(keys)} keys")


# Convenience functions

_localization_instance: Optional[Localization] = None


def init_localization(locale_dir: str = "./locales", default_language: str = "en") -> Localization:
    """Initialize global localization instance.
    
    Args:
        locale_dir: Directory containing translation files
        default_language: Default language code
        
    Returns:
        Localization instance
    """
    global _localization_instance
    _localization_instance = Localization(locale_dir, default_language)
    return _localization_instance


def get_localization() -> Optional[Localization]:
    """Get global localization instance.
    
    Returns:
        Localization instance or None
    """
    return _localization_instance


def _(key: str, **kwargs) -> str:
    """Shorthand for translate().
    
    Args:
        key: Translation key
        **kwargs: Format arguments
        
    Returns:
        Translated string
    """
    if _localization_instance:
        return _localization_instance.translate(key, **kwargs)
    return key


def set_language(lang_code: str) -> bool:
    """Set global language.
    
    Args:
        lang_code: Language code
        
    Returns:
        True if successful
    """
    if _localization_instance:
        return _localization_instance.set_language(lang_code)
    return False
