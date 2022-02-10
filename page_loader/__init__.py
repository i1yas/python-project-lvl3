import os
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup


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


def save_binary(url, path):
    res = requests.get(url, stream=True)
    with open(path, 'wb') as f:
        for chunk in res.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)


def download(url, dir):
    basename = url_to_filename(url)
    base_url, _ = os.path.split(url)
    filename = basename + '.html'
    filepath = os.path.join(dir, filename)

    res = requests.get(url)
    content = res.text
    soup = parse(content)
    images = soup.find_all("img")
    files_dirname = f'{basename}_files'
    files_dirpath = os.path.join(dir, files_dirname)

    if len(images) > 0:
        os.mkdir(files_dirpath)

    for img in images:
        old_src = img['src']
        img_url = urlparse(old_src)
        _, filename = os.path.split(img_url.path)
        new_src = os.path.join(files_dirname, filename)
        img['src'] = new_src

        img_path = os.path.join(dir, new_src)
        save_binary(
            url=urljoin(base_url, old_src),
            path=img_path
        )

    with open(filepath, 'w') as f:
        f.write(soup.prettify())

    return filepath
