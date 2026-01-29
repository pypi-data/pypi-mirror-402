import os
from typing import Any, List, Union, Literal
from .reflection import deserialize, serialize, make_annotated, is_reflectable_v, T

ANY_JSONC_TYPE = Union[type(None), bool, int, float, str, dict, list]


def annotated(val: T, comment: Union[None, str, List[str]] = None) -> T:
    return make_annotated(val, comment)


def loads_config(
    content: str,
    config: Any,
    key_format: Literal[
        "default", "snake_case", "upper_camel_case", "lower_camel_case"
    ] = "default",
    snake_case_split_char: str = "_",
) -> bool:
    res, info = is_reflectable_v(config)
    if not res:
        raise TypeError(info)
    return deserialize(content, config, key_format, snake_case_split_char)


def dumps_config(
    config: Any,
    *,
    comment: Union[None, str, List[str]] = None,
    key_format: Literal[
        "default", "snake_case", "upper_camel_case", "lower_camel_case"
    ] = "default",
    snake_case_split_char: str = "_",
) -> str:
    res, info = is_reflectable_v(config)
    if not res:
        raise TypeError(info)
    return serialize(config, comment, key_format, snake_case_split_char)


def load_config(
    path: os.PathLike,
    config: Any,
    *,
    overwrite: Literal["always", "error", "never"] = "error",
    comment: Union[None, str, List[str]] = None,
    key_format: Literal[
        "default", "snake_case", "upper_camel_case", "lower_camel_case"
    ] = "default",
    snake_case_split_char: str = "_",
) -> bool:
    result = False
    if os.path.exists(path):
        with open(path, encoding="utf-8") as file:
            if file:
                result = loads_config(
                    file.read(), config, key_format, snake_case_split_char
                )

    if overwrite == "always":
        save_config(
            path,
            config,
            comment=comment,
            key_format=key_format,
            snake_case_split_char=snake_case_split_char,
        )
    elif overwrite == "error":
        if not result:
            save_config(
                path,
                config,
                comment=comment,
                key_format=key_format,
                snake_case_split_char=snake_case_split_char,
            )

    return result


def save_config(
    path: os.PathLike,
    config: Any,
    *,
    comment: Union[None, str, List[str]] = None,
    key_format: Literal[
        "default", "snake_case", "upper_camel_case", "lower_camel_case"
    ] = "default",
    snake_case_split_char: str = "_",
) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        file.write(
            dumps_config(
                config,
                comment=comment,
                key_format=key_format,
                snake_case_split_char=snake_case_split_char,
            )
        )
