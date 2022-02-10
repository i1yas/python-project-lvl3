import os
import sys
from urllib.parse import urlparse, urljoin
import requests
import logging
from bs4 import BeautifulSoup


def get_default_logger():
    Logger = logging.getLoggerClass()
    logger = Logger('page loader')

    logger.setLevel('INFO')

    handler = logging.StreamHandler(sys.stderr)
    log_format = '%(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


default_logger = get_default_logger()


class HTTPResponseException(Exception):
    def __init__(self, response, path):
        self.response = response
        self.path = path
        self.message = self.get_message()
        super().__init__(self.message)

    def get_message(self):
        code = self.response.status_code
        path = self.path

        mapping = {
            401: f'Authorization needed for {path}',
            403: f'Access to {path} is forbidden',
            404: f'Not found {path}',
            '3xx': f'Redirect on {path}',
            '4xx': f'Wrong request to {path}',
            '5xx': f'Server can\'t handle request to {path}'
        }

        known_error = mapping.get(code)

        if known_error:
            return known_error
        if code < 400:
            return mapping['3xx']
        if code < 500:
            return mapping['4xx']
        if code >= 500:
            return mapping['5xx']

        return f'Unknown http error code {code}'


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

    if res.status_code >= 300:
        raise HTTPResponseException(res, path)

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

    if res.status_code >= 300:
        raise HTTPResponseException(res, url)

    content = res.text
    soup = parse(content)
    logger.info('HTML file parsed')

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
