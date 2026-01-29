from typing import Final
from pathlib import Path
from instaui_shiki import __version__

STATIC_DIR: Final = Path(__file__).parent / "static"
THEME_DIR: Final = STATIC_DIR / "themes"
LANG_DIR: Final = STATIC_DIR / "langs"
SHIKI_TRANSFORMERS_FILE: Final = STATIC_DIR / "shiki-transformers.js"
SHIKI_STYLE_FILE: Final = STATIC_DIR / "shiki-style.css"


LANGS_IMPORT_NAME: Final = "@shiki/langs/"
THEMES_IMPORT_NAME: Final = "@shiki/themes/"
SHIKI_CODE_LOGIC_IMPORT_NAME: Final = "@/shiki-code-logic"
SHIKI_ENGINE_FILE: Final = STATIC_DIR / "shiki-engine.js"


# cdn
SHIKI_CODE_LOGIC_CDN: Final = f"https://cdn.jsdelivr.net/gh/instaui-python/instaui-shiki@v{__version__}/shiki-dist/shiki_code_logic.js"


IMPORT_MAPS = {
    "@shiki/transformers": SHIKI_TRANSFORMERS_FILE,
    "@/shiki-engine": SHIKI_ENGINE_FILE,
    SHIKI_CODE_LOGIC_IMPORT_NAME: STATIC_DIR / "shiki-code-logic.js",
    LANGS_IMPORT_NAME: LANG_DIR,
    THEMES_IMPORT_NAME: THEME_DIR,
}

ZERO_IMPORT_MAPS = {
    "@shiki/transformers": SHIKI_TRANSFORMERS_FILE,
    SHIKI_CODE_LOGIC_IMPORT_NAME: STATIC_DIR / "shiki-code-logic.js",
    f"{LANGS_IMPORT_NAME}python.mjs": LANG_DIR / "python.mjs",
    f"{THEMES_IMPORT_NAME}vitesse-light.mjs": THEME_DIR / "vitesse-light.mjs",
    f"{THEMES_IMPORT_NAME}vitesse-dark.mjs": THEME_DIR / "vitesse-dark.mjs",
}
