import argparse

from downloader import download

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Minecraft Language Auto Fetch')
    parser.add_argument('--useCache', action='store_true', help='Use cached files if they exist')
    args = parser.parse_args()

    download(args.useCache)
