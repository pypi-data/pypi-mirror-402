from typing import TypedDict
import ast


class Context(TypedDict):
    lines: list[str]
    tree:  ast.Module
    file:  str


class Dict(TypedDict):
    file: str
    line: int
    col:  int
    code: str
    msg:  str
