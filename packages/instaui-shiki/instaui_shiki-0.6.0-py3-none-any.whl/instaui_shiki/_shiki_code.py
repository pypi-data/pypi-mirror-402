from __future__ import annotations
from typing import Dict, List, Optional
from instaui import ui, custom
from . import resources, types
from ._decorations import DecorationTypedDict
from .zero_ext_resolver import ZeroExtensionResolver


class Code(
    custom.element,
    esm="./static/shiki-code.js",
    externals=resources.IMPORT_MAPS,
    css=[resources.SHIKI_STYLE_FILE],
    zero_externals=resources.ZERO_IMPORT_MAPS,
    zero_css=[resources.SHIKI_STYLE_FILE],
):
    __zero_extension_resolver__ = ZeroExtensionResolver()

    def __init__(
        self,
        code: str,
        *,
        language: Optional[str] = None,
        theme: Optional[str] = None,
        themes: Optional[Dict[str, str]] = None,
        transformers: Optional[List[types.TTransformerNames]] = None,
        line_numbers: Optional[bool] = None,
        decorations: Optional[list[DecorationTypedDict]] = None,
    ):
        super().__init__()
        self.props({"code": code, "useDark": custom.convert_reference(ui.use_dark())})

        self.props(
            {
                "language": language,
                "theme": theme,
                "themes": themes,
                "transformers": transformers,
                "lineNumbers": line_numbers,
                "decorations": decorations,
            }
        )

        if custom.app_mode() == custom.RuntimeMode.ZERO:

            @custom.page_once
            def add_shiki_engine():
                ui.add_js_code(
                    resources.SHIKI_ENGINE_FILE.read_text(encoding="utf-8"),
                    script_attrs={"type": "module"},
                )

    @staticmethod
    def use_language_in_zero(*languages: str):
        custom.register_component_extension(
            target=Code, kind="langs", values=list(languages)
        )
