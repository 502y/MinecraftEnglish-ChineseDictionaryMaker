from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict

from tqdm import tqdm

from util import generate_dict_from_path


def make_dict_from_mod(mod_path: Path) -> List[Dict[str, str]]:
    chinese_lang_path = next(mod_path.rglob("lang/zh_cn.lang", case_sensitive=False), None)
    english_lang_path = next(mod_path.rglob("lang/en_us.lang", case_sensitive=False), None)
    chinese_json_path = next(mod_path.rglob("lang/zh_cn.json", case_sensitive=False), None)
    english_json_path = next(mod_path.rglob("lang/en_us.json", case_sensitive=False), None)
    chinese_dict = {}
    english_dict = {}
    if chinese_lang_path and english_lang_path:
        chinese_dict = generate_dict_from_path(chinese_lang_path)
        english_dict = generate_dict_from_path(english_lang_path)
    elif chinese_json_path and english_json_path:
        chinese_dict = generate_dict_from_path(chinese_json_path)
        english_dict = generate_dict_from_path(english_json_path)
    # else:
    #     print(f"mod: {mod_path.name}")
    #     print(f"chinese_lang_path: {chinese_lang_path}")
    #     print(f"english_lang_path: {english_lang_path}")
    #     print(f"chinese_json_path: {chinese_json_path}")
    #     print(f"english_json_path: {english_json_path}")
    #     print("No match language file found")
    #     raise Exception("No match language file found")

    result: List[Dict[str, str]] = []
    for key, value in chinese_dict.items():
        if key in english_dict:
            result.append(
                {"english": english_dict[key], "chinese": value, "key": key, "mod": mod_path.name, "source": "i18n"})

    return result


def process_mod(mod_path: Path) -> List[Dict[str, str]]:
    """处理单个 mod，包括读取 JSON 并反序列化"""
    res = []
    if mod_path.name in ("0-modrinth-mod", "1UNKNOWN"):
        for unknown_mod in mod_path.iterdir():
            if unknown_mod.name == "0x_trans_fix":
                continue
            res.extend(make_dict_from_mod(unknown_mod))
    else:
        res.extend(make_dict_from_mod(mod_path))
    return res


def make_mod_tsv() -> List[Dict[str, str]]:
    version_assets_path = Path("./Minecraft-Mod-Language-Package/projects")
    result: List[Dict[str, str]] = []
    versions = [v for v in version_assets_path.iterdir() if v.name.startswith("1.")]

    for version in tqdm(versions, desc="正在处理版本", unit="versions", position=0):
        current_version_assets_path = version / "assets"
        mods = list(current_version_assets_path.iterdir())
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(process_mod, mod): mod for mod in mods}
            for f in tqdm(as_completed(futures), total=len(futures), desc="正在处理模组", position=1, leave=False):
                result.extend(f.result())

    return result
