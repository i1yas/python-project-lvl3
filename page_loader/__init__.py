import os
from urllib.parse import urlparse
import requests


def url_to_filename(url):
    parsed_url = urlparse(url)
    schema = parsed_url.scheme + '://'
    url_without_schema = url.replace(schema, '')

    filename = url_without_schema \
        .replace('/', '-') \
        .replace('.', '-')

    return filename


def download(url, dir):
    filename = url_to_filename(url) + '.html'
    filepath = os.path.join(dir, filename)

    res = requests.get(url)

    with open(filepath, 'w') as f:
        f.write(res.text)

    return filepath
