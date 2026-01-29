import os

from tests.fixtures import Fixtures
from xclean.scanner import Scanner


class TestCase(Fixtures):

    def test_clean_database_not_needed(
            self,
            db_file
    ):
        if os.path.exists(db_file):
            os.remove(db_file)
        Scanner(db_path=db_file, clean=True)
        stats = os.stat(db_file)
        assert stats.st_size != 100

    def test_clean_database(
            self,
            db_file
    ):
        with open(db_file, 'w') as fp:
            fp.write('a'*100)
        Scanner(db_path=db_file, clean=True)
        stats = os.stat(db_file)
        assert stats.st_size != 100

    def test_clean_match(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, duplicate_sub_dir_path,
            m_file1, m_file2, d_file3_1, d_file4_2
    ):
        scanner.scan(dir_path=str(master_dir_path))
        results = scanner.clean(dir_path=str(duplicate_dir_path))
        assert results == {
            'duplicates': {
                'count': 2,
                'size': 3100,
            },
            'files': {
                'count': 2,
                'size': 3100,
            },
            'new': {
                'count': 0,
                'size': 0,
            },
            'abort': False,
        }
        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(duplicate_dir_path)) == 1
        assert len(os.listdir(duplicate_sub_dir_path)) == 2

    def test_clean_extension(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, duplicate_sub_dir_path,
            m_file1, m_file2, d_file1, d_file4,
    ):
        scanner.scan(dir_path=str(master_dir_path))
        results = scanner.clean(dir_path=str(duplicate_dir_path), include=['jpg'])
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
        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(duplicate_dir_path)) == 1
        assert len(os.listdir(duplicate_sub_dir_path)) == 2

    def test_clean_no_dups(
            self, scanner,
            master_dir_path, duplicate_dir_path, duplicate_sub_dir_path,
            m_file1, m_file2, d_file3, d_file4,
    ):
        results = scanner.clean(dir_path=str(duplicate_dir_path))
        assert results == {
            'duplicates': {
                'count': 0,
                'size': 0,
            },
            'files': {
                'count': 2,
                'size': 3500,
            },
            'new': {
                'count': 2,
                'size': 3500,
            },
            'abort': False,
        }
        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(duplicate_dir_path)) == 1
        assert len(os.listdir(duplicate_sub_dir_path)) == 2

    def test_clean_archive_newfiles(
            self,
            scanner, master_dir_path, duplicate_dir_path, newfiles_dir_path, newfiles_sub_dir_path,
            m_file1, m_file1_xmp1, m_file2, m_file2_xmp1,
            d_file3, d_file3_xmp1, d_file4, d_file4_xmp1,
    ):
        results = scanner.clean(
            dir_path=str(duplicate_dir_path),
            archive_new=str(newfiles_dir_path),
            include=['jpg', 'png'],
        )
        assert results == {
            'duplicates': {
                'count': 0,
                'size': 0,
            },
            'files': {
                'count': 2,
                'size': 3500,
            },
            'new': {
                'count': 2,
                'size': 3500,
            },
            'abort': False,
        }
        assert len(os.listdir(master_dir_path)) == 4
        assert len(os.listdir(duplicate_dir_path)) == 0
        assert len(os.listdir(newfiles_dir_path)) == 1
        assert len(os.listdir(newfiles_sub_dir_path)) == 4

    def test_clean_no_match(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, duplicate_sub_dir_path,
            m_file1, m_file2, d_file3, d_file4,
    ):
        results = scanner.clean(dir_path=str(duplicate_dir_path), include=['txt'])
        assert results == {
            'duplicates': {
                'count': 0,
                'size': 0,
            },
            'files': {
                'count': 0,
                'size': 0,
            },
            'new': {
                'count': 0,
                'size': 0,
            },
            'abort': False,
        }
        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(duplicate_dir_path)) == 1
        assert len(os.listdir(duplicate_sub_dir_path)) == 2

    def test_clean_masters_does_nothing(
            self,
            scanner,
            master_dir_path,
            m_file1, m_file2, m_file3, m_file4
    ):
        scanner.scan(dir_path=str(master_dir_path))
        results = scanner.clean(dir_path=str(master_dir_path))
        assert results == {
            'duplicates': {
                'count': 0,
                'size': 0,
            },
            'files': {
                'count': 0,
                'size': 0,
            },
            'new': {
                'count': 0,
                'size': 0,
            },
            'abort': False,
        }
        assert len(os.listdir(master_dir_path)) == 4
