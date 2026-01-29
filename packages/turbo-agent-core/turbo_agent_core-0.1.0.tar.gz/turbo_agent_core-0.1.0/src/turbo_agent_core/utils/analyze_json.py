from typing import Any, Dict

def analyze_json_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    深度遍历 JSON dict 结构，统计：
    - 总 key 数
    - 最大子节点（key）及其长度
    返回结果字典。
    """
    total_keys = 0
    max_subnode_key = None
    max_subnode_length = 0
    max_subnode_path = None
    max_value_length = 0
    max_value_path = None
    value_lengths = {}
    obj_size = 0

    def _traverse(obj: Any, path=None):
        nonlocal total_keys, max_subnode_key, max_subnode_length, max_subnode_path, max_value_length, max_value_path, obj_size
        if path is None:
            path = []
        if isinstance(obj, dict):
            keys_count = len(obj)
            total_keys += keys_count
            for k, v in obj.items():
                # 检查 value 是字符串的情况
                if isinstance(v, str):
                    str_len = len(v)
                    value_lengths[tuple(path + [k])] = str_len
                    obj_size += str_len  # 只加字符串长度
                    if str_len > max_value_length:
                        max_value_length = str_len
                        max_value_path = path + [k]
                elif isinstance(v, (dict, list)):
                    _traverse(v, path + [k])
                else:
                    # 其他类型（如数字、None等）按1计入obj_size
                    obj_size += 1
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                if isinstance(item, str):
                    str_len = len(item)
                    obj_size += str_len
                elif isinstance(item, (dict, list)):
                    _traverse(item, path + [f'[{idx}]'])
                else:
                    obj_size += 1

    _traverse(data)
    return {
        'total_keys': total_keys,
        'max_subnode_key': max_subnode_key,
        'max_subnode_length': max_subnode_length,
        'max_subnode_path': max_subnode_path,
        'max_value_length': max_value_length,
        'max_value_path': max_value_path,
        'value_lengths': value_lengths,
        'obj_size': obj_size
    }

# 示例用法：
if __name__ == "__main__":
    import json
    with open('/home/developerlmt/projects/turbo-agent/backend/sample.json', 'r') as f:
        sample_data = json.load(f)
    print(analyze_json_dict(sample_data))
    # sample = {"a": {"b": 1, "c": 2}, "d": [1, 2, {"e": 3, "f": 4, "g": 5}], "h": 6}
    # print(analyze_json_dict(sample))