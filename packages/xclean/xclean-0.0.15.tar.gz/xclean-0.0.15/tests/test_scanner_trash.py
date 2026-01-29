import os

from tests.fixtures import Fixtures


class TestCase(Fixtures):

    def test_trash_duplicates(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, d_file1, file_name_1
    ):
        scanner.scan(dir_path=master_dir_path)
        results = scanner.clean(dir_path=duplicate_dir_path, trash_dups=True)
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
        assert len(os.listdir(os.path.dirname(d_file1))) == 0
        assert len(os.listdir(archive_dir_path)) == 0
        if scanner.trash_directory() is not None:
            assert os.path.exists(os.path.join(scanner.trash_directory(), file_name_1))

    def test_no_trash_directory(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, d_file1, file_name_1
    ):
        scanner.trash_directory = lambda : None
        scanner.scan(dir_path=master_dir_path)
        results = scanner.clean(dir_path=duplicate_dir_path, trash_dups=True)
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
            'abort': True,
        }
        assert len(os.listdir(master_dir_path)) == 1
        assert len(os.listdir(os.path.dirname(d_file1))) == 1
        assert len(os.listdir(archive_dir_path)) == 0
