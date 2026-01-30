import json

# from deepdiff import DeepDiff


def compare_lists(temp1, temp2, check_key=["completedCount"], all_key=False, num=1):
    """对比两个list中字典，a中字典对应的键值+num等于b字典中键值
    ab值示例：
    a = [{"123": {"a": 1, "b": 2}}, {"456": {"a": 5, "b": 6}}]
    b = [{"123": {"a": 2, "b": 2}}, {"456": {"a": 6, "b": 6}}]
    """
    error = []
    # 同时遍历两个列表中的字典
    for temp1_a, temp2_b in zip(temp1, temp2):
        # 遍历每个字典的键
        for outer_key in temp1_a:
            # 确保 temp2 对应的字典中也有相同的外层键
            if outer_key in temp2_b:
                # 获取内层字典
                inner_dict_a = temp1_a[outer_key]
                inner_dict_b = temp2_b[outer_key]
                # 提取内层字典key并存入list中
                inner_dict_a_keys = list(inner_dict_a)
                if all_key is False:
                    inner_dict_a_keys = check_key
                # 遍历内层字典的键
                for inner_key in inner_dict_a_keys:
                    # 确保 temp2 对应的内层字典中也有相同的键
                    if inner_key in inner_dict_a.keys():
                        # 检查是否满足条件
                        if inner_dict_a[inner_key] + num != inner_dict_b[inner_key]:
                            error.append({
                                outer_key: {
                                    f"{inner_key}_in_a": inner_dict_a[inner_key],
                                    f"{inner_key}_in_b": inner_dict_b[inner_key]
                                }
                            })
    return error


def contrast_dict(actual_dict, expected_dict, **kwargs):
    """对比两个字典相同key的值"""
    result = DeepDiff(expected_dict, actual_dict)
    print("字典对比后结果:", result)
    if kwargs.get("only_values_changed", True):
        return [False, result["values_changed"]] \
            if "values_changed" in result.keys() else [True, "校验正常"]
    else:
        return [True, "校验正常"] if not result else [False, result]


def json_to_dict(json_data=None):
    if json_data is None:
        with open("/Users/SL/project/python/smartpush_autotest/smartpush/test.json", "r", encoding="utf-8") as file:
            json_result = json.load(file)
    return json_result


def all_in_list(list_a, list_b):
    """
    判断元素是否都在list_b中
    :param list_a:
    :param list_b:
    :return:
    """
    if isinstance(list_a, str):
        print(f"判断字符串【{list_a}】在 {list_b}")
        return list_a in list_b
    else:
        # 支持列表、元组、集合等可迭代类型
        print(f"判断对象【{list_a}】在 {list_b}")
        return set(list_a).issubset(set(list_b))


def check_values_in_list_set(a, b):
    """
    使用集合检查列表a中的所有值是否都在列表b中（效率更高）
    """
    set_b = set(b)
    missing_values = [x for x in a if x not in set_b]

    if not missing_values:
        return [True, "匹配成功"]
    else:
        return [False, "匹配失败，不匹配数据" + str(missing_values)]


def is_json_equal(a, b, exclude_fields=None):
    """
    递归比较两段JSON（字典/列表/基础类型）是否一致，排除指定字段

    :param a: 第一段JSON数据（dict/list/str/int/float/bool/None）
    :param b: 第二段JSON数据（dict/list/str/int/float/bool/None）
    :param exclude_fields: 需要排除的字段列表（如["id", "updateTime"]）
    :return: bool - 一致返回True，不一致返回False
    """
    # 初始化排除字段列表（默认空）
    exclude_fields = exclude_fields or []

    # 1. 类型不同直接判定不一致
    if type(a) != type(b):
        return False

    # 2. 处理字典类型：排除指定字段后比较键值对
    if isinstance(a, dict):
        # 获取排除字段后的键集合
        keys_a = {k for k in a.keys() if k not in exclude_fields}
        keys_b = {k for k in b.keys() if k not in exclude_fields}

        # 键集合不同则不一致
        if keys_a != keys_b:
            return False

        # 递归比较每个键对应的值
        for key in keys_a:
            if not is_json_equal(a[key], b[key], exclude_fields):
                return False
        return True

    # 3. 处理列表类型：按顺序递归比较每个元素
    elif isinstance(a, list):
        # 列表长度不同则不一致
        if len(a) != len(b):
            return False

        # 逐个比较列表元素
        for item_a, item_b in zip(a, b):
            if not is_json_equal(item_a, item_b, exclude_fields):
                return False
        return True

    # 4. 处理基础类型（str/int/float/bool/None）：直接比较值
    else:
        # 特殊处理浮点数精度问题（可选，根据需求开启）
        # if isinstance(a, float) and isinstance(b, float):
        #     return abs(a - b) < 1e-9
        return a == b
