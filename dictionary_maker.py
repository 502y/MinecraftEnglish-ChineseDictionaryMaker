import json
import re
import zipfile
from typing import Dict, Any

from version import Version


def clean_text(text: str) -> str:
    """清理文本中的控制字符"""
    return re.sub(r'[\r\n\t\b\f\v]', '', text)


def generate_dict_from_lang(content: str) -> dict[str, str]:
    return {
        clean_text(line.split("=")[0]): clean_text(line.split("=")[1])
        for line in content.split("\n")
        if line.strip() and not line.isspace()  # and "=" in line
    }


def generate_dict_from_json(content: str) -> dict[str, str]:
    data = json.loads(content)
    return {clean_text(k): clean_text(v) for k, v in data.items()}


def generate_dict_from_path(path: str) -> dict[str, str]:
    with open(path, "r", encoding="utf-8") as f:
        return generate_dict_from_json(f.read()) if path.endswith(".json") else generate_dict_from_lang(f.read())


def extract_dict_from_jar(jar_path: str) -> dict[str, str]:
    with zipfile.ZipFile(jar_path, 'r') as jar:
        lang_files = [name for name in jar.namelist() if
                      name.startswith("assets/minecraft/lang/") and
                      name.endswith((".lang", ".json")) and
                      not name.__contains__("deprecated")]
        with jar.open(lang_files[0]) as f:
            return generate_dict_from_json(f.read().decode('utf-8')) if lang_files[0].endswith(
                ".json") else generate_dict_from_lang(f.read().decode('utf-8'))


# 修改merge_dict函数以实现key传递
def merge_dict(chinese_dict: dict[str, str], english_dict: dict[str, str]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for key, value in chinese_dict.items():
        if key in english_dict:
            result[english_dict[key]] = {"chinese": value, "key": key}

    return result


def make_dictionary(langs: dict[str, dict[str, dict[str, str]]]) -> dict[str, list[dict[str, Any]]]:
    # 收集所有唯一的英文键
    all_english_keys = set()
    for version_dict in langs.values():
        all_english_keys.update(version_dict.keys())

    # 预先创建版本对象映射并排序
    version_objects_map = {version_str: Version(version_str) for version_str in langs.keys()}
    sorted_version_strings = sorted(langs.keys(), key=lambda v: Version(v))

    # 结果字典
    dictionaries: dict[str, list[dict[str, Any]]] = {}

    # 对每个英文键处理
    for english_key in all_english_keys:
        # 收集该英文键在所有版本中的中文翻译及版本信息
        translations = {}  # {chinese_value: [versions, key_data]}
        
        for version_str in sorted_version_strings:
            lang_dict = langs[version_str]
            if english_key in lang_dict:
                chinese_value = lang_dict[english_key]["chinese"]
                original_key = lang_dict[english_key]["key"]
                version_obj = version_objects_map[version_str]
                
                if chinese_value not in translations:
                    translations[chinese_value] = {
                        'versions': [],
                        'key_data': {}  # {key: [versions]}
                    }
                
                translations[chinese_value]['versions'].append(version_obj)
                
                # 跟踪每个键的版本
                if original_key not in translations[chinese_value]['key_data']:
                    translations[chinese_value]['key_data'][original_key] = []
                translations[chinese_value]['key_data'][original_key].append(version_obj)

        # 为每个不同的中文翻译创建条目
        dictionaries[english_key] = []
        for chinese_value, data in translations.items():
            versions = data['versions']
            # versions已经按版本顺序添加，只需要获取首尾元素
            keys_info = []
            for key, key_versions in data['key_data'].items():
                # key_versions已经按版本顺序添加，只需要获取首尾元素
                keys_info.append({
                    "key": key,
                    "maximumVersion": str(key_versions[-1]),
                    "minimalVersion": str(key_versions[0])
                })

            dictionaries[english_key].append({
                "chinese": chinese_value,
                "maximumVersion": str(versions[-1]),
                "minimalVersion": str(versions[0]),
                "keys": keys_info  # 现在包含每个键的版本信息
            })

    return dictionaries


def make_key_based_dictionary(langs: dict[str, dict[str, dict[str, str]]]) -> dict[str, list[dict[str, Any]]]:
    """
    创建以key为基准的字典
    """
    # 收集所有唯一的键
    all_keys = set()
    for version_dict in langs.values():
        for english_value in version_dict.values():
            all_keys.add(english_value["key"])

    # 预先创建版本对象映射并排序
    version_objects_map = {version_str: Version(version_str) for version_str in langs.keys()}
    sorted_version_strings = sorted(langs.keys(), key=lambda v: Version(v))

    # 结果字典
    dictionaries: dict[str, list[dict[str, Any]]] = {}

    # 对每个键处理
    for key in all_keys:
        # 收集该键在所有版本中的英文和中文翻译及版本信息
        translations = {}  # {chinese_value: {english_value: [versions]}}
        
        for version_str in sorted_version_strings:
            lang_dict = langs[version_str]
            for english_value, key_data in lang_dict.items():
                if key_data["key"] == key:
                    chinese_value = key_data["chinese"]
                    version_obj = version_objects_map[version_str]
                    
                    if chinese_value not in translations:
                        translations[chinese_value] = {
                            'english_values': {}  # {english_value: [versions]}
                        }
                    
                    # 跟踪每个英文值的版本
                    if english_value not in translations[chinese_value]['english_values']:
                        translations[chinese_value]['english_values'][english_value] = []
                    translations[chinese_value]['english_values'][english_value].append(version_obj)

        # 为每个不同的中文翻译创建条目
        dictionaries[key] = []
        for chinese_value, data in translations.items():
            # 处理英文值数据，为每个英文值计算最大和最小版本
            english_info = []
            for english_value, english_versions in data['english_values'].items():
                # english_versions已经按版本顺序添加，只需要获取首尾元素
                english_info.append({
                    "english": english_value,
                    "maximumVersion": str(english_versions[-1]),
                    "minimalVersion": str(english_versions[0])
                })

            # 计算这个中文翻译的整体版本范围
            all_versions = []
            for english_versions in data['english_values'].values():
                all_versions.extend(english_versions)
            all_versions = list(set(all_versions))  # 使用set去重
            # 对去重后的版本进行排序
            all_versions.sort()
            
            dictionaries[key].append({
                "chinese": chinese_value,
                "maximumVersion": str(all_versions[-1]) if all_versions else "",
                "minimalVersion": str(all_versions[0]) if all_versions else "",
                "english": english_info
            })

    return dictionaries


def _process_file_map(file_map: dict[str, dict[str, str]]) -> dict[str, dict[str, dict[str, str]]]:
    """处理文件映射的通用函数"""
    merged_dicts: dict[str, dict[str, dict[str, str]]] = {}

    for version, file_list in file_map.items():
        chinese_dict_path = file_list["lang"]
        chinese_dict = generate_dict_from_path(chinese_dict_path)

        english_dict = extract_dict_from_jar(file_list["client"])

        merged_dict = merge_dict(chinese_dict, english_dict)

        merged_dicts[version] = merged_dict

    return merged_dicts


def get_dictionary(file_map: dict[str, dict[str, str]]) -> dict[str, list[dict[str, Any]]]:
    merged_dicts = _process_file_map(file_map)
    dic = make_dictionary(merged_dicts)
    return dic


def get_merged_dicts(file_map: dict[str, dict[str, str]]) -> dict[str, dict[str, dict[str, str]]]:
    return _process_file_map(file_map)
