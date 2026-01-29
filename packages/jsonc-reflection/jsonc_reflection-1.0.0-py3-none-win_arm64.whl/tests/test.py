from typing import Dict, Optional, Union, List, Set, Tuple
from dataclasses import dataclass
from jsonc_reflection import load_config, annotated


@dataclass
class Config:
    test_key_1: int = annotated(234, "this is an inteager")
    test2: bool = False
    test3: Optional[str] = annotated("hsjanj", "qqqqqq\neddddddd")
    test4: Union[int, str, float] = 2345.3456

    @dataclass
    class SubConfig:
        sub1: int = 2345676543

    test5: Union[SubConfig, str] = annotated(
        SubConfig(), ["test struct", "second line"]
    )
    test6: List[Union[int, List[int]]] = annotated([1, 2, 3, 4, 5], "test list")
    test7: Union[Set[float], str] = annotated({2.0, 3.0, 4.0}, "test set")
    test8: Tuple[str, int, float] = annotated(("2", 3, 4.0), "test tuple")
    test9: Union[Dict[str, Union[Dict[str, Union[str, List[int]]], str, int]], str] = (
        annotated({"aaa": {"aaa": "3"}})
    )


config = Config()


def main():
    res = load_config(
        "./bin/config/config.jsonc",
        config,
        key_format="upper_camel_case",
        snake_case_split_char="-",
    )
    print(f"load: {res}")
    print(config.test_key_1)
    print(config.test2)
    print(config.test3)
    print(config.test4)
    print(config.test5.sub1)
    print(config.test6)
    print(config.test7)
    print(config.test8)
    print(config.test9)


if __name__ == "__main__":
    main()
