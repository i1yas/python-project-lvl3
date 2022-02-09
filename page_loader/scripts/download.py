import os
import argparse

from page_loader import download


def main():
    parser = argparse.ArgumentParser(description="Generate diff")

    parser.add_argument('url', type=str)
    parser.add_argument('--output', dest='OUTPUT', type=str,
                        help='location for downloaded file')

    args = parser.parse_args()
    filepath = download(
        args.url,
        args.OUTPUT or os.getcwd()
    )
    print(filepath)


if __name__ == '__main__':
    main()
