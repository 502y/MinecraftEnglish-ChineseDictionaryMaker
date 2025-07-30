import argparse
import json
from dictionary_maker import get_dictionary, make_key_based_dictionary, get_merged_dicts

from downloader import download

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Minecraft Language Auto Fetch')
    parser.add_argument('--useCache', action='store_true', help='Use cached files if they exist')
    args = parser.parse_args()

    file_map = download(args.useCache)

    # 生成以英文为基准的字典
    print("正在生成以英文为基准的字典...")
    dic = get_dictionary(file_map)
    sorted_dic = dict(sorted(dic.items()))
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(sorted_dic, f, ensure_ascii=False, indent=4)

    # 生成以key为基准的字典
    print("正在生成以key为基准的字典...")
    merged_dicts = get_merged_dicts(file_map)
    key_based_dic = make_key_based_dictionary(merged_dicts)
    sorted_key_based_dic = dict(sorted(key_based_dic.items()))
    with open("output_key_based.json", "w", encoding="utf-8") as f:
        json.dump(sorted_key_based_dic, f, ensure_ascii=False, indent=4)