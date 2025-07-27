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

    # 创建版本对象列表并排序
    version_objects = [Version(code) for code in langs.keys()]
    version_objects.sort()

    # 结果字典
    dictionaries: dict[str, list[dict[str, Any]]] = {}

    # 对每个英文键处理
    for english_key in all_english_keys:
        # 收集该英文键在所有版本中的中文翻译及版本信息
        translations = {}  # {chinese_value: [versions, key_data]}
        
        for version_str, lang_dict in langs.items():
            if english_key in lang_dict:
                chinese_value = lang_dict[english_key]["chinese"]
                original_key = lang_dict[english_key]["key"]
                version_obj = Version(version_str)
                
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
            versions.sort()
            
            # 处理键数据，为每个键计算最大和最小版本
            keys_info = []
            for key, key_versions in data['key_data'].items():
                key_versions.sort()
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


def get_dictionary(file_map: dict[str, dict[str, str]]) -> dict[str, list[dict[str, Any]]]:
    merged_dicts: dict[str, dict[str, dict[str, str]]] = {}

    for version, file_list in file_map.items():
        chinese_dict_path = file_list["lang"]
        chinese_dict = generate_dict_from_path(chinese_dict_path)

        english_dict = extract_dict_from_jar(file_list["client"])

        merged_dict = merge_dict(chinese_dict, english_dict)

        merged_dicts[version] = merged_dict

    dic = make_dictionary(merged_dicts)
    return dic
