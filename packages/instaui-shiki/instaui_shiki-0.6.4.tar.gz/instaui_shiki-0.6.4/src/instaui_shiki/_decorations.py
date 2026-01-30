from typing import Union
from typing_extensions import TypedDict


class PositionTypedDict(TypedDict):
    line: int
    character: int


class DecorationTypedDict(TypedDict):
    start: Union[PositionTypedDict, int]
    end: Union[PositionTypedDict, int]
    properties: dict


def decoration(
    start: Union[PositionTypedDict, int],
    end: Union[PositionTypedDict, int],
    properties: dict,
) -> DecorationTypedDict:
    """
    Creates a decoration object for syntax highlighting ranges in code.

    Args:
        start (Union[PositionTypedDict, int]): Starting position of the decoration.
            Can be a PositionTypedDict with line and character, or a line number.
        end (Union[PositionTypedDict, int]): Ending position of the decoration.
            Can be a PositionTypedDict with line and character, or a line number.
        properties (dict): CSS properties and classes to apply to the decorated range.

    Returns:
        DecorationTypedDict: A dictionary containing start, end positions and styling properties.

    Example:
    .. code-block:: python
        from instaui_shiki import shiki, decorations

        # Decorate a specific code range with custom CSS class
        shiki(
            code,
            decorations=[
                decorations.decoration(
                    start={"line": 1, "character": 0},
                    end={"line": 1, "character": 11},
                    properties={"class": "my-mark"}
                )
            ],
        )


        # Using helper functions for position creation
        shiki(
            code,
            decorations=[
                decorations.decoration(
                    start=decorations.start(line=1, character=0),
                    end=decorations.end(line=1, character=11),
                    properties={"class": "highlighted-code"}
                )
            ],
        )

    """
    return {
        "start": start,
        "end": end,
        "properties": properties,
    }


def start(line: int, character: int) -> PositionTypedDict:
    return {"line": line, "character": character}


def end(line: int, character: int) -> PositionTypedDict:
    return {"line": line, "character": character}
