import sys
import os
import enum
import weakref
from typing import Any, Optional
from ctypes import (
    CDLL,
    c_void_p,
    c_size_t,
    c_char_p,
    c_double,
    c_int64,
    c_uint64,
    c_bool,
    c_int,
    cast,
)


LIB = None
if sys.platform == "win32":
    LIB = CDLL(os.path.join(os.path.dirname(__file__), "libjsonc.dll"))
elif sys.platform == "linux":
    LIB = CDLL(os.path.join(os.path.dirname(__file__), "libjsonc.so"))
elif sys.platform == "darwin":
    LIB = CDLL(os.path.join(os.path.dirname(__file__), "libjsonc.dylib"))
else:
    raise OSError("unsupported platform")

JsoncTypeVariantHandle = c_void_p
JsoncObjectHandle = c_void_p
JsoncArrayHandle = c_void_p


class ValueType(enum.IntEnum):
    NULL = 0
    BOOLEAN = 1
    SIGNED = 2
    UNSIGNED = 3
    FLOAT = 4
    STRING = 5
    OBJECT = 6
    ARRAY = 7


def _sig(restype, *argtypes):
    return {"argtypes": argtypes, "restype": restype}


_FUNCS = {
    "jsonc_parse_content": _sig(JsoncTypeVariantHandle, c_char_p, c_bool),
    "jsonc_free_type_variant": _sig(None, JsoncTypeVariantHandle),
    "jsonc_free_string": _sig(None, c_char_p),
    "jsonc_get_variant_type": _sig(c_int, JsoncTypeVariantHandle),
    "jsonc_variant_to_bool": _sig(c_bool, JsoncTypeVariantHandle),
    "jsonc_variant_to_signed": _sig(c_int64, JsoncTypeVariantHandle),
    "jsonc_variant_to_unsigned": _sig(c_uint64, JsoncTypeVariantHandle),
    "jsonc_variant_to_float": _sig(c_double, JsoncTypeVariantHandle),
    "jsonc_variant_as_string": _sig(c_char_p, JsoncTypeVariantHandle),
    "jsonc_variant_as_object": _sig(JsoncObjectHandle, JsoncTypeVariantHandle),
    "jsonc_variant_as_array": _sig(JsoncArrayHandle, JsoncTypeVariantHandle),
    "jsonc_variant_get_comments_before": _sig(c_void_p, JsoncTypeVariantHandle),
    "jsonc_variant_get_comments_after": _sig(c_void_p, JsoncTypeVariantHandle),
    "jsonc_variant_set_comments_before": _sig(None, JsoncTypeVariantHandle, c_char_p),
    "jsonc_variant_set_comments_after": _sig(None, JsoncTypeVariantHandle, c_char_p),
    "jsonc_variant_dump": _sig(c_void_p, JsoncTypeVariantHandle, c_int, c_bool, c_bool),
    "jsonc_object_contains": _sig(c_bool, JsoncObjectHandle, c_char_p),
    "jsonc_object_get_type": _sig(c_int, JsoncObjectHandle, c_char_p),
    "jsonc_object_get_bool": _sig(c_bool, JsoncObjectHandle, c_char_p),
    "jsonc_object_set_bool": _sig(None, JsoncObjectHandle, c_char_p, c_bool),
    "jsonc_object_get_signed": _sig(c_int64, JsoncObjectHandle, c_char_p),
    "jsonc_object_set_signed": _sig(None, JsoncObjectHandle, c_char_p, c_int64),
    "jsonc_object_get_unsigned": _sig(c_uint64, JsoncObjectHandle, c_char_p),
    "jsonc_object_set_unsigned": _sig(None, JsoncObjectHandle, c_char_p, c_uint64),
    "jsonc_object_get_float": _sig(c_double, JsoncObjectHandle, c_char_p),
    "jsonc_object_set_float": _sig(None, JsoncObjectHandle, c_char_p, c_double),
    "jsonc_object_get_string": _sig(c_char_p, JsoncObjectHandle, c_char_p),
    "jsonc_object_set_string": _sig(None, JsoncObjectHandle, c_char_p, c_char_p),
    "jsonc_object_get_object": _sig(JsoncObjectHandle, JsoncObjectHandle, c_char_p),
    "jsonc_object_add_new_object": _sig(JsoncObjectHandle, JsoncObjectHandle, c_char_p),
    "jsonc_object_set_object": _sig(
        None, JsoncObjectHandle, c_char_p, JsoncObjectHandle
    ),
    "jsonc_object_get_array": _sig(JsoncArrayHandle, JsoncObjectHandle, c_char_p),
    "jsonc_object_add_new_array": _sig(JsoncArrayHandle, JsoncObjectHandle, c_char_p),
    "jsonc_object_set_array": _sig(None, JsoncObjectHandle, c_char_p, JsoncArrayHandle),
    "jsonc_object_get_size": _sig(c_size_t, JsoncObjectHandle),
    "jsonc_object_get_key_at_index": _sig(c_char_p, JsoncObjectHandle, c_size_t),
    "jsonc_object_clear": _sig(None, JsoncObjectHandle),
    "jsonc_object_remove": _sig(c_bool, JsoncObjectHandle, c_char_p),
    "jsonc_object_dump": _sig(c_void_p, JsoncObjectHandle, c_int, c_bool, c_bool),
    "jsonc_object_get_key_comments_before": _sig(c_void_p, JsoncObjectHandle, c_char_p),
    "jsonc_object_get_key_comments_after": _sig(c_void_p, JsoncObjectHandle, c_char_p),
    "jsonc_object_get_value_comments_before": _sig(
        c_void_p, JsoncObjectHandle, c_char_p
    ),
    "jsonc_object_get_value_comments_after": _sig(
        c_void_p, JsoncObjectHandle, c_char_p
    ),
    "jsonc_object_set_key_comments_before": _sig(
        None, JsoncObjectHandle, c_char_p, c_char_p
    ),
    "jsonc_object_set_key_comments_after": _sig(
        None, JsoncObjectHandle, c_char_p, c_char_p
    ),
    "jsonc_object_set_value_comments_before": _sig(
        None, JsoncObjectHandle, c_char_p, c_char_p
    ),
    "jsonc_object_set_value_comments_after": _sig(
        None, JsoncObjectHandle, c_char_p, c_char_p
    ),
    "jsonc_object_equals": _sig(c_bool, JsoncObjectHandle, JsoncObjectHandle),
    "jsonc_array_get_size": _sig(c_size_t, JsoncArrayHandle),
    "jsonc_array_get_type": _sig(c_int, JsoncArrayHandle, c_size_t),
    "jsonc_array_get_bool": _sig(c_bool, JsoncArrayHandle, c_size_t),
    "jsonc_array_set_bool": _sig(None, JsoncArrayHandle, c_size_t, c_bool),
    "jsonc_array_add_bool": _sig(None, JsoncArrayHandle, c_bool),
    "jsonc_array_get_signed": _sig(c_int64, JsoncArrayHandle, c_size_t),
    "jsonc_array_set_signed": _sig(None, JsoncArrayHandle, c_size_t, c_int64),
    "jsonc_array_add_signed": _sig(None, JsoncArrayHandle, c_int64),
    "jsonc_array_get_unsigned": _sig(c_uint64, JsoncArrayHandle, c_size_t),
    "jsonc_array_set_unsigned": _sig(None, JsoncArrayHandle, c_size_t, c_uint64),
    "jsonc_array_add_unsigned": _sig(None, JsoncArrayHandle, c_uint64),
    "jsonc_array_get_float": _sig(c_double, JsoncArrayHandle, c_size_t),
    "jsonc_array_set_float": _sig(None, JsoncArrayHandle, c_size_t, c_double),
    "jsonc_array_add_float": _sig(None, JsoncArrayHandle, c_double),
    "jsonc_array_get_string": _sig(c_char_p, JsoncArrayHandle, c_size_t),
    "jsonc_array_set_string": _sig(None, JsoncArrayHandle, c_size_t, c_char_p),
    "jsonc_array_add_string": _sig(None, JsoncArrayHandle, c_char_p),
    "jsonc_array_get_object": _sig(JsoncObjectHandle, JsoncArrayHandle, c_size_t),
    "jsonc_array_set_object": _sig(None, JsoncArrayHandle, c_size_t, JsoncObjectHandle),
    "jsonc_array_add_new_object": _sig(JsoncObjectHandle, JsoncArrayHandle),
    "jsonc_array_get_array": _sig(JsoncArrayHandle, JsoncArrayHandle, c_size_t),
    "jsonc_array_set_array": _sig(None, JsoncArrayHandle, c_size_t, JsoncArrayHandle),
    "jsonc_array_add_new_array": _sig(JsoncArrayHandle, JsoncArrayHandle),
    "jsonc_array_clear": _sig(None, JsoncArrayHandle),
    "jsonc_array_remove": _sig(c_bool, JsoncArrayHandle, c_size_t),
    "jsonc_array_dump": _sig(c_void_p, JsoncArrayHandle, c_int, c_bool, c_bool),
    "jsonc_array_get_comments_before": _sig(c_void_p, JsoncArrayHandle, c_size_t),
    "jsonc_array_get_comments_after": _sig(c_void_p, JsoncArrayHandle, c_size_t),
    "jsonc_array_set_comments_before": _sig(None, JsoncArrayHandle, c_size_t, c_char_p),
    "jsonc_array_set_comments_after": _sig(None, JsoncArrayHandle, c_size_t, c_char_p),
    "jsonc_array_equals": _sig(c_bool, JsoncArrayHandle, JsoncArrayHandle),
    "jsonc_create_object": _sig(JsoncObjectHandle),
    "jsonc_create_array": _sig(JsoncArrayHandle),
    "jsonc_free_object": _sig(None, JsoncObjectHandle),
    "jsonc_free_array": _sig(None, JsoncArrayHandle),
}

for name, sig in _FUNCS.items():
    f = getattr(LIB, name)
    f.argtypes = sig["argtypes"]
    f.restype = sig["restype"]


def to_cstr(content: str):
    return c_char_p(content.encode("utf-8"))


def from_cstr(cstr: c_void_p) -> str:
    char_p = cast(cstr, c_char_p)
    result = char_p.value.decode("utf-8")
    LIB.jsonc_free_string(char_p)
    return result


def from_cstr_optional(cstr: c_void_p) -> Optional[str]:
    if cstr:
        return from_cstr(cstr)
    return None


class TypeVariant:
    handle: Any

    def __init__(self, handle):
        self.handle = handle
        self._finalizer = weakref.finalize(
            self, LIB.jsonc_free_type_variant, self.handle
        )


class Object:
    handle: Any

    def __init__(self, handle, parent=None):
        self.handle = handle
        if parent:
            self._parent = parent
        else:
            self._finalizer = weakref.finalize(self, LIB.jsonc_free_object, self.handle)


class Array:
    handle: Any

    def __init__(self, handle, parent=None):
        self.handle = handle
        if parent:
            self._parent = parent
        else:
            self._finalizer = weakref.finalize(self, LIB.jsonc_free_array, self.handle)


def parse_content(content: str, allow_trailing_comma: bool) -> Optional[TypeVariant]:
    result = LIB.jsonc_parse_content(to_cstr(content), allow_trailing_comma)
    if result:
        return TypeVariant(result)
    return None


def get_variant_type(handle: TypeVariant) -> ValueType:
    return LIB.jsonc_get_variant_type(handle.handle)


def variant_to_bool(handle: TypeVariant) -> bool:
    return LIB.jsonc_variant_to_bool(handle.handle)


def variant_to_signed(handle: TypeVariant) -> int:
    return LIB.jsonc_variant_to_signed(handle.handle)


def variant_to_unsigned(handle: TypeVariant) -> int:
    return LIB.jsonc_variant_to_unsigned(handle.handle)


def variant_to_float(handle: TypeVariant) -> float:
    return LIB.jsonc_variant_to_float(handle.handle)


def variant_as_string(handle: TypeVariant) -> str:
    return LIB.jsonc_variant_to_string(handle.handle).decode("utf-8")


def variant_as_object(handle: TypeVariant):
    return Object(LIB.jsonc_variant_as_object(handle.handle), handle)


def variant_as_array(handle: TypeVariant):
    return Array(LIB.jsonc_variant_as_array(handle.handle), handle)


def variant_get_comments_before(handle: TypeVariant) -> Optional[str]:
    return from_cstr_optional(LIB.jsonc_variant_get_comments_before(handle.handle))


def variant_get_comments_after(handle: TypeVariant) -> Optional[str]:
    return from_cstr_optional(LIB.jsonc_variant_get_comments_after(handle.handle))


def variant_set_comments_before(handle: TypeVariant, comments: str) -> None:
    LIB.jsonc_variant_set_comments_before(handle.handle, to_cstr(comments))


def variant_set_comments_after(handle: TypeVariant, comments: str) -> None:
    LIB.jsonc_variant_set_comments_after(handle.handle, to_cstr(comments))


def variant_dump(
    handle: TypeVariant,
    indent: int,
    ensure_ascii: bool,
    ignore_comments: bool,
) -> str:
    return from_cstr(
        LIB.jsonc_variant_dump(handle.handle, indent, ensure_ascii, ignore_comments)
    )


def object_contains(handle: Object, key: str) -> bool:
    return LIB.jsonc_object_contains(handle.handle, to_cstr(key))


def object_get_type(handle: Object, key: str) -> ValueType:
    return ValueType(LIB.jsonc_object_get_type(handle.handle, to_cstr(key)))


def object_get_bool(handle: Object, key: str) -> bool:
    return LIB.jsonc_object_get_bool(handle.handle, to_cstr(key))


def object_set_bool(handle: Object, key: str, value: bool) -> None:
    LIB.jsonc_object_set_bool(handle.handle, to_cstr(key), value)


def object_get_signed(handle: Object, key: str) -> int:
    return LIB.jsonc_object_get_signed(handle.handle, to_cstr(key))


def object_set_signed(handle: Object, key: str, value: int) -> None:
    LIB.jsonc_object_set_signed(handle.handle, to_cstr(key), value)


def object_get_unsigned(handle: Object, key: str) -> int:
    return LIB.jsonc_object_get_unsigned(handle.handle, to_cstr(key))


def object_set_unsigned(handle: Object, key: str, value: int) -> None:
    LIB.jsonc_object_set_unsigned(handle.handle, to_cstr(key), value)


def object_get_float(handle: Object, key: str) -> float:
    return LIB.jsonc_object_get_float(handle.handle, to_cstr(key))


def object_set_float(handle: Object, key: str, value: float) -> None:
    LIB.jsonc_object_set_float(handle.handle, to_cstr(key), value)


def object_get_string(handle: Object, key: str) -> str:
    return LIB.jsonc_object_get_string(handle.handle, to_cstr(key)).decode("utf-8")


def object_set_string(handle: Object, key: str, value: str) -> None:
    LIB.jsonc_object_set_string(handle.handle, to_cstr(key), to_cstr(value))


def object_get_object(handle: Object, key: str) -> Object:
    return Object(LIB.jsonc_object_get_object(handle.handle, to_cstr(key)), handle)


def object_add_new_object(handle: Object, key: str) -> Object:
    return Object(LIB.jsonc_object_add_new_object(handle.handle, to_cstr(key)), handle)


def object_set_object(handle: Object, key: str, value: Object) -> None:
    LIB.jsonc_object_set_object(handle.handle, to_cstr(key), value.handle)


def object_get_array(handle: Object, key: str) -> Array:
    return Array(LIB.jsonc_object_get_array(handle.handle, to_cstr(key)), handle)


def object_add_new_array(handle: Object, key: str) -> Array:
    return Array(LIB.jsonc_object_add_new_array(handle.handle, to_cstr(key)), handle)


def object_set_array(handle: Object, key: str, value: Array) -> None:
    LIB.jsonc_object_set_array(handle.handle, to_cstr(key), value.handle)


def object_get_size(handle: Object) -> int:
    return LIB.jsonc_object_get_size(handle.handle)


def object_get_key_at_index(handle: Object, index: int) -> str:
    return LIB.jsonc_object_get_key_at_index(handle.handle, index).decode("utf-8")


def object_clear(handle: Object) -> None:
    LIB.jsonc_object_clear(handle.handle)


def object_remove(handle: Object, key: str) -> bool:
    return LIB.jsonc_object_remove(handle.handle, to_cstr(key))


def object_dump(
    handle: Object, indent: int, ensure_ascii: bool, ignore_comments: bool
) -> str:
    return from_cstr(
        LIB.jsonc_object_dump(handle.handle, indent, ensure_ascii, ignore_comments)
    )


def object_get_key_comments_before(handle: Object, key: str) -> Optional[str]:
    return from_cstr_optional(
        LIB.jsonc_object_get_key_comments_before(handle.handle, to_cstr(key))
    )


def object_get_key_comments_after(handle: Object, key: str) -> Optional[str]:
    return from_cstr_optional(
        LIB.jsonc_object_get_key_comments_after(handle.handle, to_cstr(key))
    )


def object_get_value_comments_before(handle: Object, key: str) -> Optional[str]:
    return from_cstr_optional(
        LIB.jsonc_object_get_value_comments_before(handle.handle, to_cstr(key))
    )


def object_get_value_comments_after(handle: Object, key: str) -> Optional[str]:
    return from_cstr_optional(
        LIB.jsonc_object_get_value_comments_after(handle.handle, to_cstr(key))
    )


def object_set_key_comments_before(handle: Object, key: str, comments: str) -> None:
    LIB.jsonc_object_set_key_comments_before(
        handle.handle, to_cstr(key), to_cstr(comments)
    )


def object_set_key_comments_after(handle: Object, key: str, comments: str) -> None:
    LIB.jsonc_object_set_key_comments_after(
        handle.handle, to_cstr(key), to_cstr(comments)
    )


def object_set_value_comments_before(handle: Object, key: str, comments: str) -> None:
    LIB.jsonc_object_set_value_comments_before(
        handle.handle, to_cstr(key), to_cstr(comments)
    )


def object_set_value_comments_after(handle: Object, key: str, comments: str) -> None:
    LIB.jsonc_object_set_value_comments_after(
        handle.handle, to_cstr(key), to_cstr(comments)
    )


def object_equals(lhs: Object, rhs: Object):
    return LIB.jsonc_object_equals(lhs.handle, rhs.handle)


def array_get_type(handle: Array, index: int) -> ValueType:
    return ValueType(LIB.jsonc_array_get_type(handle.handle, index))


def array_get_bool(handle: Array, index: int) -> bool:
    return LIB.jsonc_array_get_bool(handle.handle, index)


def array_set_bool(handle: Array, index: int, value: bool) -> None:
    LIB.jsonc_array_set_bool(handle.handle, index, value)


def array_add_bool(handle: Array, value: bool) -> None:
    LIB.jsonc_array_add_bool(handle.handle, value)


def array_get_signed(handle: Array, index: int) -> int:
    return LIB.jsonc_array_get_signed(handle.handle, index)


def array_set_signed(handle: Array, index: int, value: int) -> None:
    LIB.jsonc_array_set_signed(handle.handle, index, value)


def array_add_signed(handle: Array, value: int) -> None:
    LIB.jsonc_array_add_signed(handle.handle, value)


def array_get_unsigned(handle: Array, index: int) -> int:
    return LIB.jsonc_array_get_unsigned(handle.handle, index)


def array_set_unsigned(handle: Array, index: int, value: int) -> None:
    LIB.jsonc_array_set_unsigned(handle.handle, index, value)


def array_add_unsigned(handle: Array, value: int) -> None:
    LIB.jsonc_array_add_unsigned(handle.handle, value)


def array_get_float(handle: Array, index: int) -> float:
    return LIB.jsonc_array_get_float(handle.handle, index)


def array_set_float(handle: Array, index: int, value: float) -> None:
    LIB.jsonc_array_set_float(handle.handle, index, value)


def array_add_float(handle: Array, value: float) -> None:
    LIB.jsonc_array_add_float(handle.handle, value)


def array_get_string(handle: Array, index: int) -> str:
    return LIB.jsonc_array_get_string(handle.handle, index).decode("utf-8")


def array_set_string(handle: Array, index: int, value: str) -> None:
    LIB.jsonc_array_set_string(handle.handle, index, to_cstr(value))


def array_add_string(handle: Array, value: str) -> None:
    LIB.jsonc_array_add_string(handle.handle, to_cstr(value))


def array_get_object(handle: Array, index: int) -> Object:
    return Object(LIB.jsonc_array_get_object(handle.handle, index), handle)


def array_add_new_object(handle: Array) -> Object:
    return Object(LIB.jsonc_array_add_new_object(handle.handle), handle)


def array_set_object(handle: Array, index: int, value: Object) -> None:
    LIB.jsonc_array_set_object(handle.handle, index, value.handle)


def array_get_array(handle: Array, index: int) -> Array:
    return Array(LIB.jsonc_array_get_array(handle.handle, index), handle)


def array_add_new_array(handle: Array) -> Array:
    return Array(LIB.jsonc_array_add_new_array(handle.handle), handle)


def array_set_array(handle: Array, index: int, value: Array) -> None:
    LIB.jsonc_array_set_array(handle.handle, index, value.handle)


def array_get_size(handle: Array) -> int:
    return LIB.jsonc_array_get_size(handle.handle)


def array_clear(handle: Array) -> None:
    LIB.jsonc_array_clear(handle.handle)


def array_remove(handle: Array, index: int) -> bool:
    return LIB.jsonc_array_remove(handle.handle, index)


def array_dump(
    handle: Array, indent: int, ensure_ascii: bool, ignore_comments: bool
) -> str:
    return from_cstr(
        LIB.jsonc_array_dump(handle.handle, indent, ensure_ascii, ignore_comments)
    )


def array_get_comments_before(handle: Array, index: int) -> Optional[str]:
    return from_cstr_optional(LIB.jsonc_array_get_comments_before(handle.handle, index))


def array_get_comments_after(handle: Array, index: int) -> Optional[str]:
    return from_cstr_optional(LIB.jsonc_array_get_comments_after(handle.handle, index))


def array_set_comments_before(handle: Array, index: int, comments: str) -> None:
    LIB.jsonc_array_set_comments_before(handle.handle, index, to_cstr(comments))


def array_set_comments_after(handle: Array, index: int, comments: str) -> None:
    LIB.jsonc_array_set_comments_after(handle.handle, index, to_cstr(comments))


def array_equals(lhs: Array, rhs: Array):
    return LIB.jsonc_array_equals(lhs.handle, rhs.handle)


def create_object() -> Object:
    return Object(LIB.jsonc_create_object())


def create_array() -> Array:
    return Array(LIB.jsonc_create_array())
