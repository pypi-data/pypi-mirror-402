import os

from tests.fixtures import Fixtures


class TestCase(Fixtures):

    def test_scan_master(
            self,
            scanner,
            master_dir_path,
            m_file1, m_file2
    ):
        results = scanner.scan(dir_path=str(master_dir_path))
        assert results == {
            'files': {
                'count': 2,
                'size': 3100,
            }
        }
        assert len(os.listdir(master_dir_path)) == 2

    def test_scan_master_with_extension(
            self,
            scanner,
            master_dir_path,
            m_file1, m_file4
    ):
        results = scanner.scan(dir_path=str(master_dir_path), include=['jpg'])
        assert results == {
            'files': {
                'count': 1,
                'size': 1500,
            }
        }
        assert len(os.listdir(master_dir_path)) == 2

    def test_scan_master_exclude_extension(
            self,
            scanner,
            master_dir_path,
            m_file1, m_file4
    ):
        results = scanner.scan(dir_path=str(master_dir_path), exclude=['jpg'])
        assert results == {
            'files': {
                'count': 1,
                'size': 1800,
            }
        }
        assert len(os.listdir(master_dir_path)) == 2

    def test_scan_master_ignore_link(
            self,
            scanner,
            master_dir_path,
            m_file1, m_file1_link
    ):
        results = scanner.scan(dir_path=str(master_dir_path), include=['jpg'])
        assert results == {
            'files': {
                'count': 1,
                'size': 1500,
            }
        }
        assert len(os.listdir(master_dir_path)) == 2

    def test_scan_master_no_match(
            self,
            scanner,
            master_dir_path,
            m_file3, m_file4
    ):
        results = scanner.scan(dir_path=str(master_dir_path), include=['txt'])
        assert results == {
            'files': {
                'count': 0,
                'size': 0,
            }
        }
        assert len(os.listdir(master_dir_path)) == 2

    def test_scan_master_no_file_extension(
            self,
            scanner,
            master_dir_path,
            m_file5
    ):
        results = scanner.scan(dir_path=str(master_dir_path), include=['txt'])
        assert results == {
            'files': {
                'count': 0,
                'size': 0,
            }
        }
        assert len(os.listdir(master_dir_path)) == 1
