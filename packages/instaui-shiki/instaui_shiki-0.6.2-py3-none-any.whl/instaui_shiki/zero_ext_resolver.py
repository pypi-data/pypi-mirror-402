from pathlib import Path
from instaui.internal.assets import AssetsDeclaration
from . import consts, resources

ROOT = Path(__file__).parent


class ZeroExtensionResolver:
    def resolve_zero_extensions(
        self,
        extensions: dict[str, set[str]],
        assets: AssetsDeclaration,
    ):
        langs = extensions.get(consts.COMP_EX_LANG_KEY, set())
        for lang in langs:
            name = f"{resources.LANGS_IMPORT_NAME}{lang}.mjs"
            path = resources.LANG_DIR / f"{lang}.mjs"
            assets.import_maps[name] = path
