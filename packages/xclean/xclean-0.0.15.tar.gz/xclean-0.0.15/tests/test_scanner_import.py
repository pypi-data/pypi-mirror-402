import os

from tests.fixtures import Fixtures


class TestCase(Fixtures):

    def test_import_new(
            self,
            scanner,
            master_dir_path,
            master_sub_dir_path,
            duplicate_dir_path,
            duplicate_sub_dir_path,
            m_file1, d_file2,
    ):

        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(master_sub_dir_path)) == 0
        assert len(os.listdir(duplicate_dir_path)) == 1
        assert len(os.listdir(duplicate_sub_dir_path)) == 1

        scanner.scan(dir_path=master_dir_path)
        results = scanner.clean(
            dir_path=duplicate_dir_path,
            import_new=master_dir_path)
        assert results == {
            'duplicates': {
                'count': 0,
                'size': 0,
            },
            'files': {
                'count': 1,
                'size': 1600,
            },
            'new': {
                'count': 1,
                'size': 1600,
            },
            'abort': False,
        }

        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(master_sub_dir_path)) == 1
        assert len(os.listdir(duplicate_dir_path)) == 1
        assert len(os.listdir(duplicate_sub_dir_path)) == 0

    def test_import_new_with_copy(
            self,
            scanner_with_copy,
            master_dir_path,
            master_sub_dir_path,
            duplicate_dir_path,
            duplicate_sub_dir_path,
            m_file1, d_file2,
    ):

        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(master_sub_dir_path)) == 0
        assert len(os.listdir(duplicate_dir_path)) == 1
        assert len(os.listdir(duplicate_sub_dir_path)) == 1

        scanner_with_copy.scan(dir_path=master_dir_path)
        results = scanner_with_copy.clean(
            dir_path=duplicate_dir_path,
            import_new=master_dir_path)
        assert results == {
            'duplicates': {
                'count': 0,
                'size': 0,
            },
            'files': {
                'count': 1,
                'size': 1600,
            },
            'new': {
                'count': 1,
                'size': 1600,
            },
            'abort': False,
        }

        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(master_sub_dir_path)) == 1
        assert len(os.listdir(duplicate_dir_path)) == 1
        assert len(os.listdir(duplicate_sub_dir_path)) == 1
