import re
from dataclasses import is_dataclass, fields, field
from typing import (
    TypeVar,
    get_origin,
    get_args,
    Union,
    List,
    Dict,
    Set,
    Tuple,
    Any,
    Optional,
    Literal,
)
import jsonc_reflection.__internal.native_lib as jsonc

T = TypeVar("T")


def _to_snake_case(s: str, c: str) -> str:
    s = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", s)
    s = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s)
    return s.lower().replace("_", c)


def _to_upper_camel_case(s: str) -> str:
    return "".join(w[:1].upper() + w[1:] for w in _to_snake_case(s, "_").split("_"))


def _to_lower_camel_case(s: str) -> str:
    s = _to_upper_camel_case(s)
    return s[:1].lower() + s[1:] if s else s


def _get_key_name(
    f: Literal["default", "snake_case", "upper_camel_case", "lower_camel_case"],
    s: str,
    c: str,
):
    if f == "snake_case":
        return _to_snake_case(s, c)
    if f == "upper_camel_case":
        return _to_upper_camel_case(s)
    if f == "lower_camel_case":
        return _to_lower_camel_case(s)
    return s


def _object_get_comments(obj: jsonc.Object, key: str):
    result = ""
    kbc = jsonc.object_get_key_comments_before(obj, key)
    if kbc is not None:
        result += f"{kbc}\n"
    kac = jsonc.object_get_key_comments_after(obj, key)
    if kac is not None:
        result += f"{kac}\n"
    vbc = jsonc.object_get_value_comments_before(obj, key)
    if vbc is not None:
        result += f"{vbc}\n"
    vac = jsonc.object_get_value_comments_after(obj, key)
    if vac is not None:
        result += f"{vac}\n"
    return result


def _is_compatible_value(value: Any, tp: Any) -> bool:
    if tp is Any:
        return True

    origin = get_origin(tp)
    if origin is Union:
        return any(_is_compatible_value(value, arg) for arg in get_args(tp))

    if origin is not None:
        args = get_args(tp)
        if origin in (list, List):
            if not isinstance(value, list):
                return False
            (et,) = args
            return all(_is_compatible_value(elem, et) for elem in value)
        if origin in (dict, Dict):
            if not isinstance(value, dict):
                return False
            kt, vt = args
            return all(
                _is_compatible_value(k, kt) and _is_compatible_value(v, vt)
                for k, v in value.items()
            )
        if origin in (set, Set):
            if not isinstance(value, set):
                return False
            (et,) = args
            return all(_is_compatible_value(elem, et) for elem in value)
        if origin in (tuple, Tuple):
            if not isinstance(value, tuple):
                return False
            if len(value) != len(args):
                return False
            return all(_is_compatible_value(v, a) for v, a in zip(value, args))
        return isinstance(value, origin)

    if tp is int:
        return isinstance(value, int) and not isinstance(value, bool)
    elif tp is float:
        return isinstance(value, (float, int))
    return isinstance(value, tp)


def _is_reflectable_value(tp: Any, info: str) -> Tuple[bool, str]:
    if is_dataclass(tp):
        return True, info

    if tp is Any:
        info += f"{tp} is not serializable, do NOT use typing.Any, please use jsonc_reflection.ANY_JSONC_TYPE instead.\n"
        return False, info

    origin = get_origin(tp)
    if origin is Union:
        return any(_is_reflectable_value(arg, info)[0] for arg in get_args(tp)), info

    if origin is not None:
        args = get_args(tp)
        if origin in (list, List, set, Set):
            (et,) = args
            return _is_reflectable_value(et, info)
        if origin in (tuple, Tuple):
            return all(_is_reflectable_value(arg, info)[0] for arg in args), info
        if origin in (dict, Dict):
            kt, vt = args
            if kt is not str:
                info += (
                    f"{kt} is not valid jsonc key type, jsonc key type must be str\n"
                )
                return False, info
            return _is_reflectable_value(vt, info)
        info += f"{tp} is not serializable\n"
        return False, info

    res = tp in (bool, int, float, str)
    if not res:
        info += f"{tp} is not serializable\n"
    return res, info


def _is_optional_field(tp: Any) -> bool:
    origin = get_origin(tp)
    if origin is Union:
        return type(None) in get_args(tp)
    return False


def _get_object_type(tp: Any) -> Any:
    origin = get_origin(tp)
    if origin in (dict, Dict):
        return tp
    if origin is Union:
        for t in get_args(tp):
            if get_origin(t) in (dict, Dict):
                return t
    return None


def _get_array_type(tp: Any) -> Any:
    origin = get_origin(tp)
    if origin in (list, List, set, Set, tuple, Tuple):
        return tp
    if origin is Union:
        for t in get_args(tp):
            if get_origin(t) in (list, List, set, Set, tuple, Tuple):
                return t
    return None


def _deserialize_object(obj: jsonc.Object, data: dict, tp: Any) -> bool:
    result = True
    size = jsonc.object_get_size(obj)
    (_, vt) = get_args(_get_object_type(tp))
    for index in range(size):
        name = jsonc.object_get_key_at_index(obj, index)
        vtype = jsonc.object_get_type(obj, name)
        if vtype == jsonc.ValueType.NULL:
            if _is_compatible_value(None, vt):
                data[name] = None
            else:
                result = False
        elif vtype == jsonc.ValueType.BOOLEAN:
            val = jsonc.object_get_bool(obj, name)
            if _is_compatible_value(val, vt):
                data[name] = val
            else:
                result = False
        elif vtype == jsonc.ValueType.SIGNED:
            val = jsonc.object_get_signed(obj, name)
            if _is_compatible_value(val, vt):
                data[name] = val
            else:
                result = False
        elif vtype == jsonc.ValueType.UNSIGNED:
            val = jsonc.object_get_unsigned(obj, name)
            if _is_compatible_value(val, vt):
                data[name] = val
            else:
                result = False
        elif vtype == jsonc.ValueType.FLOAT:
            val = jsonc.object_get_float(obj, name)
            if _is_compatible_value(val, vt):
                data[name] = val
            else:
                result = False
        elif vtype == jsonc.ValueType.STRING:
            val = jsonc.object_get_string(obj, name)
            if _is_compatible_value(val, vt):
                data[name] = val
            else:
                result = False
        elif vtype == jsonc.ValueType.OBJECT:
            subobj = jsonc.object_get_object(obj, name)
            subdict = {}
            subvt = _get_object_type(vt)
            if subvt is not None:
                if not _deserialize_object(subobj, subdict, subvt):
                    result = False
                data[name] = subdict
            else:
                result = False
        elif vtype == jsonc.ValueType.ARRAY:
            subarr = jsonc.object_get_array(obj, name)
            sublist = []
            subvt = _get_array_type(vt)
            if subvt is not None:
                if not _deserialize_array(subarr, sublist, subvt):
                    result = False
                data[name] = sublist
            else:
                result = False
    return result


def _deserialize_array(arr: jsonc.Array, data: list, tp: Any) -> bool:
    result = True
    size = jsonc.array_get_size(arr)
    data.clear()
    (vt,) = get_args(tp)

    def push_element(e: Any):
        if _is_compatible_value(e, vt):
            data.append(e)
            return True
        return False

    for index in range(size):
        vtype = jsonc.array_get_type(arr, index)
        if vtype == jsonc.ValueType.NULL:
            if not push_element(None):
                result = False
        elif vtype == jsonc.ValueType.BOOLEAN:
            if not push_element(jsonc.array_get_bool(arr, index)):
                result = False
        elif vtype == jsonc.ValueType.SIGNED:
            if not push_element(jsonc.array_get_signed(arr, index)):
                result = False
        elif vtype == jsonc.ValueType.UNSIGNED:
            if not push_element(jsonc.array_get_unsigned(arr, index)):
                result = False
        elif vtype == jsonc.ValueType.FLOAT:
            if not push_element(jsonc.array_get_float(arr, index)):
                result = False
        elif vtype == jsonc.ValueType.STRING:
            if not push_element(jsonc.array_get_string(arr, index)):
                result = False
        elif vtype == jsonc.ValueType.OBJECT:
            subobj = jsonc.array_get_object(arr, index)
            subdict = {}
            if not _deserialize_object(subobj, subdict, _get_object_type(vt)):
                result = False
            if not push_element(subdict):
                result = False
        elif vtype == jsonc.ValueType.ARRAY:
            subarr = jsonc.array_get_array(arr, index)
            sublist = []
            if not _deserialize_array(subarr, sublist, _get_array_type(vt)):
                result = False
            if not push_element(sublist):
                result = False

    return result


def _deserialize_struct(
    obj: jsonc.Object,
    config: Any,
    key_format: Literal[
        "default", "snake_case", "upper_camel_case", "lower_camel_case"
    ],
    snake_case_split_char: str,
) -> bool:
    result = True
    optional_count = 0
    for f in fields(config):
        name = _get_key_name(key_format, f.name, snake_case_split_char)
        if not jsonc.object_contains(obj, name):
            if not _is_optional_field(f.type):
                result = False
            else:
                setattr(config, f.name, None)
                optional_count += 1
            continue
        vtype = jsonc.object_get_type(obj, name)
        value = None
        if vtype == jsonc.ValueType.BOOLEAN:
            value = jsonc.object_get_bool(obj, name)
        elif vtype == jsonc.ValueType.SIGNED:
            value = jsonc.object_get_signed(obj, name)
        elif vtype == jsonc.ValueType.UNSIGNED:
            value = jsonc.object_get_unsigned(obj, name)
        elif vtype == jsonc.ValueType.FLOAT:
            value = jsonc.object_get_float(obj, name)
        elif vtype == jsonc.ValueType.STRING:
            value = jsonc.object_get_string(obj, name)
        if _is_compatible_value(value, f.type):
            setattr(config, f.name, value)
        elif vtype == jsonc.ValueType.OBJECT:
            value = jsonc.object_get_object(obj, name)
            data = f.default_factory()
            ori = get_origin(f.type)
            if is_dataclass(f.type):
                if not _deserialize_struct(
                    value, data, key_format, snake_case_split_char
                ):
                    result = False
            elif ori in (dict, Dict):
                data = {}
                if not _deserialize_object(value, data, f.type):
                    result = False
            elif ori is Union:
                tps = get_args(f.type)
                if any(is_dataclass(t) for t in tps):
                    if not _deserialize_struct(
                        value, data, key_format, snake_case_split_char
                    ):
                        result = False
                else:
                    objt = _get_object_type(f.type)
                    if objt is not None:
                        data = {}
                        if not _deserialize_object(value, data, objt):
                            result = False
            else:
                result = False
            setattr(config, f.name, data)
        elif vtype == jsonc.ValueType.ARRAY:
            value = jsonc.object_get_array(obj, name)
            arrt = _get_array_type(f.type)
            if arrt is not None:
                arrc = get_origin(arrt)
                data = []
                if arrc in (tuple, Tuple):
                    vts = get_args(arrt)
                    size = len(vts)
                    if jsonc.array_get_size(value) != size:
                        result = False
                    if not _deserialize_array(value, data, List[Union[vts]]):
                        result = False
                    data = tuple(data)
                    if not _is_compatible_value(data, arrt):
                        result = False
                    if result:
                        setattr(config, f.name, data)
                else:
                    if not _deserialize_array(value, data, arrt):
                        result = False
                    setattr(config, f.name, arrc(data))
            else:
                result = False
        else:
            result = False

        comment = _object_get_comments(obj, name)
        newmeta = dict(f.metadata)
        if comment:
            newmeta["comment"] = comment
        else:
            newmeta.pop("comment", None)
        f.metadata = newmeta

    if len(fields(config)) != jsonc.object_get_size(obj) + optional_count:
        result = False

    return result


def _serialize_struct(
    obj: jsonc.Object,
    val: Any,
    key_format: Literal[
        "default", "snake_case", "upper_camel_case", "lower_camel_case"
    ],
    snake_case_split_char: str,
) -> None:
    for f in fields(val):
        name = _get_key_name(key_format, f.name, snake_case_split_char)
        _serialize_value(
            name,
            obj,
            getattr(val, f.name),
            f.metadata.get("comment"),
            key_format,
            snake_case_split_char,
        )


def _serialize_object(
    obj: jsonc.Object,
    val: Any,
    key_format: Literal[
        "default", "snake_case", "upper_camel_case", "lower_camel_case"
    ],
    snake_case_split_char: str,
) -> None:
    for k, v in val.items():
        if isinstance(v, bool):
            jsonc.object_set_bool(obj, k, v)
        elif isinstance(v, int):
            if v > 0:
                jsonc.object_set_unsigned(obj, k, v)
            else:
                jsonc.object_set_signed(obj, k, v)
        elif isinstance(v, float):
            jsonc.object_set_float(obj, k, v)
        elif isinstance(v, str):
            jsonc.object_set_string(obj, k, v)
        elif is_dataclass(v):
            newobj = jsonc.object_add_new_object(obj, k)
            _serialize_struct(newobj, v, key_format, snake_case_split_char)
        elif isinstance(v, (list, set, tuple)):
            newarr = jsonc.object_add_new_array(obj, k)
            _serialize_array(newarr, v, key_format, snake_case_split_char)
        elif isinstance(v, dict):
            newobj = jsonc.object_add_new_object(obj, k)
            _serialize_object(newobj, v, key_format, snake_case_split_char)


def _serialize_array(
    obj: jsonc.Array,
    val: Any,
    key_format: Literal[
        "default", "snake_case", "upper_camel_case", "lower_camel_case"
    ],
    snake_case_split_char: str,
) -> None:
    for v in val:
        if isinstance(v, bool):
            jsonc.array_add_bool(obj, v)
        elif isinstance(v, int):
            if v > 0:
                jsonc.array_add_unsigned(obj, v)
            else:
                jsonc.array_add_signed(obj, v)
        elif isinstance(v, float):
            jsonc.array_add_float(obj, v)
        elif isinstance(v, str):
            jsonc.array_add_string(obj, v)
        elif is_dataclass(v):
            newobj = jsonc.array_add_new_object(obj)
            _serialize_struct(newobj, v, key_format, snake_case_split_char)
        elif isinstance(v, (list, set)):
            newarr = jsonc.array_add_new_array(obj)
            _serialize_array(newarr, v, key_format, snake_case_split_char)
        elif isinstance(v, dict):
            newobj = jsonc.array_add_new_object(obj)
            _serialize_object(newobj, v, key_format, snake_case_split_char)


def _serialize_value(
    name: str,
    obj: jsonc.Object,
    data: Any,
    comment: Optional[str],
    key_format: Literal[
        "default", "snake_case", "upper_camel_case", "lower_camel_case"
    ],
    snake_case_split_char: str,
) -> None:
    if isinstance(data, bool):
        jsonc.object_set_bool(obj, name, data)
    elif isinstance(data, int):
        if data > 0:
            jsonc.object_set_unsigned(obj, name, data)
        else:
            jsonc.object_set_signed(obj, name, data)
    elif isinstance(data, float):
        jsonc.object_set_float(obj, name, data)
    elif isinstance(data, str):
        jsonc.object_set_string(obj, name, data)
    elif is_dataclass(data):
        newobj = jsonc.object_add_new_object(obj, name)
        _serialize_struct(newobj, data, key_format, snake_case_split_char)
    elif isinstance(data, (list, set, tuple)):
        newarr = jsonc.object_add_new_array(obj, name)
        _serialize_array(newarr, data, key_format, snake_case_split_char)
    elif isinstance(data, dict):
        newobj = jsonc.object_add_new_object(obj, name)
        _serialize_object(newobj, data, key_format, snake_case_split_char)

    if comment:
        jsonc.object_set_key_comments_before(obj, name, comment)


def _serialize_comment(comment: Union[None, str, List[str]]) -> Optional[str]:
    if isinstance(comment, list):
        comment = "\n".join(comment)
    if comment is not None:
        comments = comment.splitlines()
        if len(comments) == 0:
            return None
        if len(comments) == 1:
            return f"// {comments[0]}\n"
        res = "\n * ".join(comments)
        return f"/*\n * {res}\n */\n"
    return None


def deserialize(
    content: str,
    config: Any,
    key_format: Literal[
        "default", "snake_case", "upper_camel_case", "lower_camel_case"
    ],
    snake_case_split_char: str,
) -> bool:
    handle = jsonc.parse_content(content, True)
    if handle:
        if jsonc.get_variant_type(handle) == jsonc.ValueType.OBJECT:
            comments = []
            cb = jsonc.variant_get_comments_before(handle)
            if cb:
                comments += cb.splitlines()
            ca = jsonc.variant_get_comments_after(handle)
            if ca:
                comments += ca.splitlines()
            setattr(config, "__comments", _serialize_comment(comments))
            return _deserialize_struct(
                jsonc.variant_as_object(handle),
                config,
                key_format,
                snake_case_split_char,
            )
    return False


def serialize(
    config: Any,
    comment: Union[None, str, List[str]],
    key_format: Literal[
        "default", "snake_case", "upper_camel_case", "lower_camel_case"
    ],
    snake_case_split_char: str,
) -> str:
    obj = jsonc.create_object()
    _serialize_struct(obj, config, key_format, snake_case_split_char)
    result = jsonc.object_dump(obj, 4, False, False)
    if not hasattr(config, "__comments"):
        setattr(config, "__comments", _serialize_comment(comment))
    comments = getattr(config, "__comments")
    return result if not comments else comments + result


def make_annotated(val: T, comment: Union[None, str, List[str]] = None) -> T:
    if isinstance(comment, list):
        comment = "\n".join(comment)
    # pylint:disable=invalid-field-call
    if isinstance(val, (bool, int, float, str)):
        return field(default=val, metadata={"comment": comment})
    return field(default_factory=lambda: val, metadata={"comment": comment})


def is_reflectable_v(config: Any) -> Tuple[bool, str]:
    if not is_dataclass(config):
        return False, f"{type(config)} is not serializable, type must be a dataclass"
    res = True
    info = ""
    for f in fields(config):
        _res, _info = _is_reflectable_value(f.type, info)
        res = _res
        info += _info
        if not res:
            return res, info
    if not hasattr(config, "__defalut_check"):
        res = True
        for f in fields(config):
            v = getattr(config, f.name)
            res = _is_compatible_value(v, f.type)
            if not res:
                info += f"Default value check failed: {v} is not {f.type}\n"
                return res, info
        setattr(config, "__defalut_check", True)
    return res, info
