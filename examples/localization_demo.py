"""Localization Demo - showcases multi-language support.

Demonstrates:
- Runtime language switching
- Translation loading from JSON
- String formatting
- Fallback to default language
"""
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import DirectButton, DirectLabel, DirectFrame
from panda3d.core import TextNode
from engine_modules.localization import init_localization, _, set_language
import sys

class LocalizationDemo(ShowBase):
    """Demo showcasing localization system."""
    
    def __init__(self):
        ShowBase.__init__(self)
        
        # Initialize localization
        self.loc = init_localization(locale_dir="./locales", default_language="en")
        
        # Setup camera
        self.camera.setPos(0, -20, 0)
        
        # Create UI
        self.setup_ui()
        
        # Controls
        self.accept("escape", sys.exit)
        
        print("Localization Demo")
        print(f"Available languages: {', '.join(self.loc.get_available_languages())}")
    
    def setup_ui(self):
        """Create user interface with translations."""
        # Language selection buttons
        y_pos = 0.8
        for lang_code in self.loc.get_available_languages():
            btn = DirectButton(
                text=lang_code.upper(),
                scale=0.1,
                pos=(-0.5 + self.loc.get_available_languages().index(lang_code) * 0.3, 0, y_pos),
                command=self.change_language,
                extraArgs=[lang_code]
            )
        
        # Title
        self.title_label = DirectLabel(
            text=_("editor.title"),
            scale=0.15,
            pos=(0, 0, 0.6),
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0)
        )
        
        # Menu labels
        self.file_label = DirectLabel(
            text=_("ui.menu.file"),
            scale=0.08,
            pos=(-0.6, 0, 0.4),
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0)
        )
        
        self.edit_label = DirectLabel(
            text=_("ui.menu.edit"),
            scale=0.08,
            pos=(-0.3, 0, 0.4),
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0)
        )
        
        self.view_label = DirectLabel(
            text=_("ui.menu.view"),
            scale=0.08,
            pos=(0, 0, 0.4),
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0)
        )
        
        self.help_label = DirectLabel(
            text=_("ui.menu.help"),
            scale=0.08,
            pos=(0.3, 0, 0.4),
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0)
        )
        
        # Buttons
        self.save_btn = DirectButton(
            text=_("ui.buttons.save"),
            scale=0.08,
            pos=(-0.4, 0, 0.1),
            command=self.show_message,
            extraArgs=["editor.messages.saved"]
        )
        
        self.load_btn = DirectButton(
            text=_("ui.buttons.load"),
            scale=0.08,
            pos=(0, 0, 0.1),
            command=self.show_message,
            extraArgs=["editor.messages.loaded"]
        )
        
        self.delete_btn = DirectButton(
            text=_("ui.buttons.delete"),
            scale=0.08,
            pos=(0.4, 0, 0.1),
            command=self.confirm_delete
        )
        
        # Game info with formatting
        self.score_label = DirectLabel(
            text=_("game.score", score=1234),
            scale=0.08,
            pos=(-0.4, 0, -0.2),
            text_fg=(1, 1, 0, 1),
            frameColor=(0, 0, 0, 0)
        )
        
        self.lives_label = DirectLabel(
            text=_("game.lives", lives=3),
            scale=0.08,
            pos=(0, 0, -0.2),
            text_fg=(1, 0, 0, 1),
            frameColor=(0, 0, 0, 0)
        )
        
        self.level_label = DirectLabel(
            text=_("game.level", level=5),
            scale=0.08,
            pos=(0.4, 0, -0.2),
            text_fg=(0, 1, 1, 1),
            frameColor=(0, 0, 0, 0)
        )
        
        # Message area
        self.message_label = DirectLabel(
            text="",
            scale=0.08,
            pos=(0, 0, -0.5),
            text_fg=(0, 1, 0, 1),
            frameColor=(0, 0, 0, 0)
        )
    
    def change_language(self, lang_code):
        """Change the active language."""
        if set_language(lang_code):
            print(f"Language changed to: {lang_code}")
            self.update_ui()
    
    def update_ui(self):
        """Update all UI text with current language."""
        self.title_label['text'] = _("editor.title")
        self.file_label['text'] = _("ui.menu.file")
        self.edit_label['text'] = _("ui.menu.edit")
        self.view_label['text'] = _("ui.menu.view")
        self.help_label['text'] = _("ui.menu.help")
        
        self.save_btn['text'] = _("ui.buttons.save")
        self.load_btn['text'] = _("ui.buttons.load")
        self.delete_btn['text'] = _("ui.buttons.delete")
        
        self.score_label['text'] = _("game.score", score=1234)
        self.lives_label['text'] = _("game.lives", lives=3)
        self.level_label['text'] = _("game.level", level=5)
    
    def show_message(self, message_key):
        """Show a translated message."""
        self.message_label['text'] = _(message_key)
    
    def confirm_delete(self):
        """Show confirmation dialog."""
        self.message_label['text'] = _("common.confirm")


if __name__ == "__main__":
    demo = LocalizationDemo()
    demo.run()
