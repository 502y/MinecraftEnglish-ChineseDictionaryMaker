import shutil
import urllib.request
import json
import os
from typing import Dict, Optional

from version import Version


def fetch_versions_manifest() -> Optional[Dict[str, any]]:
    _url = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
    try:
        # 使用 urllib.request 获取数据
        with urllib.request.urlopen(_url) as response:
            data = response.read()
            # 解析 JSON 数据
            _manifest = json.loads(data.decode('utf-8'))
            return _manifest
    except Exception as e:
        print(f"获取数据时出错: {e}")
        return None


def get_assets_urls(manifest) -> Dict[str, str]:
    _assets_urls: dict[str, str] = {}
    version_1_6_1 = Version("1.6.1")

    _assets_urls: dict[str, str] = {
        version['id']: version['url']
        for version in manifest['versions']
        if version['type'] == 'release' and Version(version['id']) >= version_1_6_1
    }
    # TODO 我们需要1.6.1-吗……
    print(f"共有{len(_assets_urls)} 个有效正式版本")

    return _assets_urls


def get_assets_indexes(_assets_urls: dict[str, str]) -> Dict[str, Dict[str, str]]:
    indexes: Dict[str, any] = {}
    for version, url in _assets_urls.items():
        try:
            with urllib.request.urlopen(url) as response:
                data = response.read()
                data = json.loads(data.decode('utf-8'))
                indexes[version] = {"assets": data["assetIndex"]["url"], "client": data["downloads"]["client"]["url"]}
        except Exception as e:
            print(f"获取{version}数据时出错: {e}")
    print(f"获取了{len(indexes)}个索引")
    return indexes


def download_file(url: str, filepath: str):
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        urllib.request.urlretrieve(url, filepath)
        print(f"已下载: {filepath}")
    except Exception as e:
        print(f"下载 {url} 失败: {e}")

def download_if_not_exist(url: str, filepath: str):
    if os.path.exists(filepath):
        print(f"{filepath}已存在，跳过下载")
    else:
        download_file(url, filepath)


def get_lang_hash_from_asset(objects):
    lang_files = [
        "minecraft/lang/zh_CN.lang",
        "minecraft/lang/zh_cn.lang",
        "minecraft/lang/zh_CN.json",
        "minecraft/lang/zh_cn.json",
        "lang/zh_CN.lang",
        "lang/zh_cn.lang",
        "lang/zh_CN.json",
        "lang/zh_cn.json"
    ]

    for lang_file in lang_files:
        if lang_file in objects:
            return [lang_file,objects[lang_file]["hash"]]

    return None

def download_all_files(indexes: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    """下载所有assets和client文件"""
    file_dict: Dict[str, Dict[str, str]] = {}
    # 创建下载目录
    assets_path = "download/assets"
    clients_path = "download/clients"
    langs_path = "download/langs"
    hash_file_base_url = "https://resources.download.minecraft.net"

    os.makedirs(assets_path, exist_ok=True)
    os.makedirs(clients_path, exist_ok=True)
    os.makedirs(langs_path, exist_ok=True)

    for version, urls in indexes.items():
        # 下载assets文件
        assets_url = urls["assets"]
        # 从URL中提取文件名
        assets_filename = assets_url.split("/")[-1]
        assets_filepath = f"{assets_path}/{assets_filename}"
        download_if_not_exist(assets_url, assets_filepath)

        # 下载client文件
        client_url = urls["client"]
        # 使用版本名作为文件名
        client_filepath = f"{clients_path}/{version}.jar"
        download_if_not_exist(client_url, client_filepath)

        # 下载语言文件
        with open(assets_filepath, 'r', encoding='utf-8') as f:
            content = json.load(f)
            lang_tuple = get_lang_hash_from_asset(content["objects"])
            langs_filepath = f"{langs_path}/{version}.{lang_tuple[0].split('.')[-1]}"
            lang_file_url = f"{hash_file_base_url}/{lang_tuple[1][:2]}/{lang_tuple[1]}"

            download_if_not_exist(lang_file_url, langs_filepath)

        file_dict[version] = {
            "assets": assets_filepath,
            "client": client_filepath,
            "lang": langs_filepath,
        }

    return file_dict


def extract_lang_file_hash(objects) -> str:
    """
    从JSON内容中提取中文语言文件的路径
    """
    lang_files = [
        "minecraft/lang/zh_CN.lang",
        "minecraft/lang/zh_cn.lang",
        "minecraft/lang/zh_CN.json",
        "minecraft/lang/zh_cn.json",
        "lang/zh_CN.lang",
        "lang/zh_cn.lang",
        "lang/zh_CN.json",
        "lang/zh_cn.json"
    ]

    for lang_file in lang_files:
        if lang_file in objects:
            return objects[lang_file]["hash"]

    return None

def download(use_cache: bool):
    if not use_cache and os.path.exists("download/"):
        shutil.rmtree("download/")
        print("已删除缓存")
    print("正在获取 Minecraft 版本清单...")
    manifests = fetch_versions_manifest()
    if manifests:
        print("成功获取版本清单!")
        print(f"最新版本: {manifests['latest']['release']}")
        print(f"共有 {len(manifests['versions'])} 个版本记录")
    else:
        print("获取版本清单失败")
        exit(-1)
    assets_urls = get_assets_urls(manifests)
    indexes_url = get_assets_indexes(assets_urls)
    files_map = download_all_files(indexes_url)
    return files_map
