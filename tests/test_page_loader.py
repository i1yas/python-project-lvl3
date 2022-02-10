import os
import tempfile
import pytest

from page_loader import download


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
        requests_mock.get('https://test.com/files/picture.jpg', text='jpg file')
        requests_mock.get('https://test.com/files/picture.png', text='png file')
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


def test_paths_changed():
    with tempfile.TemporaryDirectory() as tmpdirname:
        result_path = download(url, tmpdirname)

        with open(result_path) as result_file:
            actual = result_file.read()
            assert '"test-com-document_files/picture.jpg"' in actual
            assert '"test-com-document_files/picture.png"' in actual


def test_files_loaded():
    with tempfile.TemporaryDirectory() as tmpdirname:
        download(url, tmpdirname)

        dirpath = os.path.join(tmpdirname, files_dirname)
        assert set(["picture.jpg", "picture.png"]) == set(os.listdir(dirpath))
