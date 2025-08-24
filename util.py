import json5
import orjson
import re
import zipfile
from pathlib import Path


def clean_text(text: str) -> str:
    """清理文本中的控制字符和文件头的zwnbsp等不可见字符"""
    # 移除zwnbsp (Zero Width No-Break Space) 和其他不可见字符
    text = re.sub(r'[\uFEFF\u200B-\u200D\u2060]', '', text)
    # 移除控制字符
    return re.sub(r'[\r\n\t\b\f\v]', '', text)


def clean_json(content: str) -> str:
    return re.sub(r'"="', '":"', content)


def generate_dict_from_lang(content: str) -> dict[str, str]:
    return {
        clean_text(line.split("=", 1)[0]): clean_text(line.split("=", 1)[1])
        for line in content.split("\n")
        if line.strip() and not line.isspace() and "=" in line
    }


def generate_dict_from_json(content: str) -> dict[str, str]:
    content = clean_json(content)
    if content.__contains__("//"):
        data = json5.loads(content)
    else:
        data = orjson.loads(content)
    return {clean_text(k): clean_text(v) for k, v in data.items() if k is str and v is str}


def generate_dict_from_path(path: str | Path) -> dict[str, str]:
    path_obj = Path(path)
    # 使用 utf-8-sig 编码来自动处理 BOM
    with open(path_obj, "r", encoding="utf-8-sig") as f:
        return generate_dict_from_json(f.read()) if path_obj.suffix == ".json" else generate_dict_from_lang(f.read())


def extract_dict_from_jar(jar_path: str) -> dict[str, str]:
    with zipfile.ZipFile(jar_path, 'r') as jar:
        lang_files = [name for name in jar.namelist() if
                      name.startswith("assets/minecraft/lang/") and
                      name.endswith((".lang", ".json")) and
                      not name.__contains__("deprecated")]
        with jar.open(lang_files[0]) as f:
            return generate_dict_from_json(f.read().decode('utf-8')) if lang_files[0].endswith(
                ".json") else generate_dict_from_lang(f.read().decode('utf-8'))
