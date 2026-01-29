import os

from tests.fixtures import Fixtures


class TestCase(Fixtures):

    def test_archive_ignore_existing_duplicates(
            self,
            scanner_ignore_existing,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, d_file1, a_file1,
    ):
        assert len(os.listdir(master_dir_path)) == 1
        assert len(os.listdir(os.path.dirname(d_file1))) == 1
        assert len(os.listdir(archive_dir_path)) == 1
        scanner_ignore_existing.scan(dir_path=master_dir_path)
        results = scanner_ignore_existing.clean(dir_path=duplicate_dir_path, archive_to=archive_dir_path)
        assert results == {
            'duplicates': {
                'count': 1,
                'size': 1500,
            },
            'files': {
                'count': 1,
                'size': 1500,
            },
            'new': {
                'count': 0,
                'size': 0,
            },
            'abort': False,
        }
        assert len(os.listdir(master_dir_path)) == 1
        assert len(os.listdir(os.path.dirname(d_file1))) == 1
        assert len(os.listdir(archive_dir_path)) == 1
