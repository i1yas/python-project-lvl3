import os
import tempfile

from page_loader import download


def get_fixture_path(name):
    return os.path.join('tests/fixtures', name)


def test_page_loader(requests_mock):
    expected_path = get_fixture_path('expected.html')

    with (
        tempfile.TemporaryDirectory() as tmpdirname,
        open(expected_path) as expected_file
    ):
        url = 'https://test.com/file'
        filename = 'test-com-file'
        expected = expected_file.read()

        requests_mock.get(url, text=expected)

        download(url, tmpdirname)

        result_path = os.path.join(tmpdirname, filename)

        with open(result_path) as result_file:
            actual = result_file.read()
            assert expected == actual
