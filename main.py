import argparse
import json
from dictionary_maker import get_dictionary

from downloader import download

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Minecraft Language Auto Fetch')
    parser.add_argument('--useCache', action='store_true', help='Use cached files if they exist')
    args = parser.parse_args()

    file_map = download(args.useCache)

    dic = get_dictionary(file_map)
    with open("output.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(dic, ensure_ascii=False))
