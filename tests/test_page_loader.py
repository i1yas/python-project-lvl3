import os
import tempfile
import pytest

from page_loader import download, HTTPResponseException


def get_fixture_path(name):
    return os.path.join('tests/fixtures', name)


url = 'https://test.com/document'
output_filename = 'test-com-document.html'
files_dirname = 'test-com-document_files'
expected_path = get_fixture_path('expected.html')


@pytest.fixture(autouse=True)
def setup(requests_mock):
    file_path = get_fixture_path('file.html')

    with open(file_path) as original_file:
        original = original_file.read()
        requests_mock.get(url, text=original)
        requests_mock.get('https://test.com/about', text=original)

    files_to_mock = [
        ('picture.jpg', 'jpg picture'),
        ('picture.png', 'png picture'),
        ('style.css', 'css file'),
        ('script.js', 'console.log("test")')
    ]

    for filename, content in files_to_mock:
        requests_mock.get(
            f'https://test.com/files/{filename}',
            text=content
        )
    yield


def test_page_loaded():
    with (
        tempfile.TemporaryDirectory() as tmpdirname,
        open(expected_path) as expected_file
    ):
        expected = expected_file.read()
        result_path = download(url, tmpdirname)

        assert result_path == os.path.join(tmpdirname, output_filename)

        with open(result_path) as result_file:
            actual = result_file.read()
            assert expected == actual


def test_files_loaded():
    with tempfile.TemporaryDirectory() as tmpdirname:
        download(url, tmpdirname)

        dirpath = os.path.join(tmpdirname, files_dirname)
        assert set([
            "test-com-files-picture.jpg",
            "test-com-files-picture.png",
            "test-com-files-script.js",
            "test-com-files-style.css",
            "test-com-about.html",
        ]) == set(os.listdir(dirpath))


def test_bad_path():
    with pytest.raises(FileNotFoundError):
        download(url, '/undefined')


def test_bad_filemod():
    with tempfile.TemporaryDirectory() as tmpdirname:
        os.chmod(tmpdirname, 111)
        with pytest.raises(PermissionError):
            download(url, tmpdirname)


def test_bad_http_request(requests_mock):
    requests_mock.get('http://401.com', status_code=401)
    requests_mock.get('http://404.com', status_code=404)
    requests_mock.get('http://5xx.com', status_code=501)
    requests_mock.get('https://test.com/files/picture.jpg', status_code=404)

    with tempfile.TemporaryDirectory() as tmpdirname:
        with pytest.raises(HTTPResponseException) as e:
            download('http://401.com', tmpdirname)
        assert 'Authorization needed for http://401.com' == str(e.value)

        with pytest.raises(HTTPResponseException) as e:
            download('http://404.com', tmpdirname)
        assert 'Not found http://404.com' == str(e.value)

        with pytest.raises(HTTPResponseException) as e:
            download('http://5xx.com', tmpdirname)
        assert 'Server can\'t handle request to http://5xx.com' == str(e.value)

        with pytest.raises(HTTPResponseException) as e:
            download(url, tmpdirname)
        resourse_path = os.path.join(
            tmpdirname,
            'test-com-document_files',
            'test-com-files-picture.jpg'
        )
        assert f'Not found {resourse_path}' == str(e.value)
