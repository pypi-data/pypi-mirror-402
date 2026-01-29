from typing import Union
def find_common_keys(a: Union[dict, set], b: Union[dict, set]):
    # 获取两个字典的键集合
    keys_a = set(a.keys()) if isinstance(a, dict) else a
    keys_b = set(b.keys()) if isinstance(b, dict) else b

    # 判断两个字典是否有相同的键
    common_keys = keys_a.intersection(keys_b)
    return common_keys
find_common_keys({1:1, 2:2}, {2:2, 3:3})