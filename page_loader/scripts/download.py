import os
import sys
import argparse

from page_loader import download, get_default_logger, HTTPResponseException


def main():
    parser = argparse.ArgumentParser(
        description="Downloads page with resources"
    )

    parser.add_argument('url', type=str)
    parser.add_argument('-o', '--output', dest='OUTPUT', type=str,
                        help='location for downloaded file')

    args = parser.parse_args()

    logger = get_default_logger()

    try:
        filepath = download(
            args.url,
            dir=args.OUTPUT or os.getcwd(),
            logger=logger
        )
        print(filepath)
        sys.exit(0)
    except HTTPResponseException as e:
        message = f'Reponse error. {e.message}'
        print(message)
    except FileNotFoundError as e:
        message = f'File or directory {e.filename} not found on the disk'
        logger.error(message)
    except FileExistsError as e:
        message = f'File or directory {e.filename} already exists'
        logger.error(message)
    except PermissionError:
        message = f'Can\'t access {args.OUTPUT}'
        logger.error(message)

    sys.exit(20)


if __name__ == '__main__':
    main()
