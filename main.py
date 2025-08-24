import argparse
import csv
import json
import os

from dictionary_maker import get_dictionary, make_key_based_dictionary, get_merged_dicts
from downloader import download
from mod_tsv_maker import make_mod_tsv

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Minecraft Language Auto Fetch')
    parser.add_argument('--useCache', action='store_true', help='Use cached files if they exist')
    args = parser.parse_args()

    file_map = download(args.useCache)

    output_path = "output/"
    os.mkdir(output_path)

    # 生成以英文为基准的字典
    print("正在生成以英文为基准的字典...")
    dic = get_dictionary(file_map)
    sorted_dic = dict(sorted(dic.items()))
    with open(f"{output_path}output.json", "w", encoding="utf-8") as f:
        json.dump(sorted_dic, f, ensure_ascii=False, indent=4)

    # 生成以key为基准的字典
    print("正在生成以key为基准的字典...")
    merged_dicts = get_merged_dicts(file_map)
    key_based_dic = make_key_based_dictionary(merged_dicts)
    sorted_key_based_dic = dict(sorted(key_based_dic.items()))
    with open(f"{output_path}output_key_based.json", "w", encoding="utf-8") as f:
        json.dump(sorted_key_based_dic, f, ensure_ascii=False, indent=4)

    # 生成模组tsv
    print("正在生成模组tsv...")
    mod_tsv = make_mod_tsv()
    with open(f"{output_path}mod_tsv.tsv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(['英文', '中文', 'key', '模组', '来源'])
        for item in mod_tsv:
            writer.writerow([item['english'], item['chinese'], item['key'], item['mod'], item['source']])
