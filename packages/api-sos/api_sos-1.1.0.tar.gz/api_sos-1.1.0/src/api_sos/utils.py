import asyncio
import json
import string
from functools import update_wrapper, wraps
from pathlib import Path
from random import choice
from typing import Any, Awaitable, Callable

import ruamel.yaml
from jinja2 import Environment

yaml = ruamel.yaml.YAML()
yaml.preserve_quotes = True


def coro[**P, R](f: Callable[P, Awaitable[R]]) -> Callable[P, R]:
    @wraps(f)
    def wrapper(*args: P.args, **kwargs: P.kwargs):
        return asyncio.run(f(*args, **kwargs))  # type: ignore

    return update_wrapper(wrapper, f)


def auto_reader(path: str) -> dict:
    p = Path(path)
    content = p.read_text()

    match p.suffix.lower():
        case ".json":
            return json.loads(content)
        case ".yaml" | ".yml":
            return yaml.load(content)
        case _:
            raise Exception(f"File {path} is not a valid format or not supported yet.")


def gen_string(length=8):
    return "".join(choice(string.ascii_uppercase + string.digits) for _ in range(length))


def to_jsonify_dict(o: Any):
    if isinstance(o, dict):
        return {k: to_jsonify_dict(v) for k, v in o.items()}
    elif isinstance(o, list):
        return [to_jsonify_dict(v) for v in o]
    elif isinstance(o, (str, int, float, bool)):
        return o
    # is enum, to value
    elif hasattr(o, "value"):
        return o.value
    else:
        raise Exception(f"Type {type(o)} is not supported yet")
