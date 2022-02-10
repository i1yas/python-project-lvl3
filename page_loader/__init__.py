import os
from urllib.parse import urlparse, urljoin
import requests
import logging
from bs4 import BeautifulSoup


Logger = logging.getLoggerClass()
default_logger = Logger(name='default_logger', level=logging.DEBUG)


def parse(file_or_content):
    return BeautifulSoup(file_or_content, 'html.parser')


def url_to_filename(url):
    parsed_url = urlparse(url)
    schema = parsed_url.scheme + '://'
    url_without_schema = url.replace(schema, '')

    filename = url_without_schema \
        .replace('/', '-') \
        .replace('.', '-')

    return filename


def is_local_path(path):
    return path.startswith('/')


def save_binary(url, path):
    res = requests.get(url, stream=True)
    with open(path, 'wb') as f:
        for chunk in res.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)


def download(url, dir, logger=default_logger):
    basename = url_to_filename(url)
    base_url, _ = os.path.split(url)
    filename = basename + '.html'
    filepath = os.path.join(dir, filename)

    res = requests.get(url)
    content = res.text
    soup = parse(content)
    logger.info(f'File {filename} parsed')

    files_dirname = f'{basename}_files'
    files_dirpath = os.path.join(dir, files_dirname)

    elements_to_load = []

    elements_to_load.extend(
        ('src', img) for img in soup.find_all('img')
    )
    elements_to_load.extend(
        ('href', link) for link in soup.find_all('link')
        if link.get('href')
    )
    elements_to_load.extend(
        ('src', script) for script in soup.find_all('script')
        if script.get('src')
    )

    if len(elements_to_load) > 0:
        os.mkdir(files_dirpath)
    else:
        logger.warning(f'Found no resources to download in {url}')

    for (key, element) in elements_to_load:
        old_path = element[key]

        if not is_local_path(old_path):
            continue

        element_url = urlparse(old_path)
        _, filename = os.path.split(element_url.path)
        new_path = os.path.join(files_dirname, filename)
        element[key] = new_path

        local_path = os.path.join(dir, new_path)
        save_binary(
            url=urljoin(base_url, old_path),
            path=local_path
        )
        logger.info(f'Loaded resource {old_path}')

    with open(filepath, 'w') as f:
        f.write(soup.prettify())

    return filepath
