import os
import sys
from urllib.parse import urlparse
import requests
import logging
from progress.bar import Bar
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


def is_local_path(path, url):
    return path.startswith('/')


def save_binary(url, path):
    res = requests.get(url, stream=True)

    if res.status_code >= 300:
        raise HTTPResponseException(res, path)

    with open(path, 'wb') as f:
        for chunk in res.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)


def get_resource_tags(soup):
    found_tags = []

    found_tags.extend(
        ('src', img) for img in soup.find_all('img')
    )
    found_tags.extend(
        ('href', link) for link in soup.find_all('link')
        if link.get('href')
    )
    found_tags.extend(
        ('src', script) for script in soup.find_all('script')
        if script.get('src')
    )

    return found_tags


def download(url, dir, logger=default_logger):
    basename = url_to_filename(url)
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

    tags = get_resource_tags(soup)

    def keep_tag(item):
        key, tag = item
        path = tag[key]
        if path.startswith('/'):
            return True
        parsed_main_url = urlparse(url)
        parsed_tag_url = urlparse(path)
        return parsed_main_url.hostname == parsed_tag_url.hostname

    tags_to_process = list(filter(keep_tag, tags))

    if len(tags_to_process) > 0:
        os.mkdir(files_dirpath)
    else:
        logger.warning(f'Found no resources to download in {url}')

    progress_bar = Bar('Loading resources', max=len(tags_to_process))
    for (key, tag) in tags_to_process:
        old_path = tag[key]

        tag_url_parsed = urlparse(old_path)
        base_url_parsed = urlparse(url)
        tag_url_parsed = tag_url_parsed._replace(
            scheme=base_url_parsed.scheme,
            netloc=base_url_parsed.netloc
        )

        tag_url_wo_ext, ext = os.path.splitext(
            tag_url_parsed.geturl()
        )

        new_full_filename = url_to_filename(
            tag_url_wo_ext.replace(tag_url_parsed.scheme + '://', '')
        ) + (ext or '.html')

        full_path = os.path.join(
            files_dirpath,
            new_full_filename
        )
        local_path = os.path.join(
            files_dirname,
            new_full_filename
        )

        tag[key] = local_path

        save_binary(
            url=tag_url_parsed.geturl(),
            path=full_path
        )
        progress_bar.next()

    progress_bar.finish()

    with open(filepath, 'w') as f:
        f.write(soup.prettify())

    return filepath
