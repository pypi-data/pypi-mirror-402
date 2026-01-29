import os

from tests.fixtures import Fixtures


class TestCase(Fixtures):

    def test_xmp_compare_no_xmps(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, d_file1
    ):
        scanner.scan(dir_path=master_dir_path)
        scanner.clean(dir_path=duplicate_dir_path, archive_to=archive_dir_path, check_xmp=True)
        assert len(os.listdir(master_dir_path)) == 1
        assert len(os.listdir(os.path.dirname(d_file1))) == 0
        assert len(os.listdir(archive_dir_path)) == 1

    def test_xmp_compare_no_dup_xmp1(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, m_file1_xmp1, d_file1
    ):
        scanner.scan(dir_path=master_dir_path)
        scanner.clean(dir_path=duplicate_dir_path, archive_to=archive_dir_path, check_xmp=True)
        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(os.path.dirname(d_file1))) == 1
        assert len(os.listdir(archive_dir_path)) == 0

    def test_xmp_compare_no_dup_xmp2(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, m_file1_xmp2, d_file1
    ):
        scanner.scan(dir_path=master_dir_path)
        scanner.clean(dir_path=duplicate_dir_path, archive_to=archive_dir_path, check_xmp=True)
        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(os.path.dirname(d_file1))) == 1
        assert len(os.listdir(archive_dir_path)) == 0

    def test_xmp_compare_no_dup_xmp3(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, m_file1_xmp3, d_file1
    ):
        scanner.scan(dir_path=master_dir_path)
        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(os.path.dirname(d_file1))) == 1
        assert len(os.listdir(archive_dir_path)) == 0
        scanner.clean(
            dir_path=duplicate_dir_path,
            archive_to=archive_dir_path,
            check_xmp=True
        )
        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(os.path.dirname(d_file1))) == 1
        assert len(os.listdir(archive_dir_path)) == 0

    def test_xmp_compare_no_dup_xmp4(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, m_file1_xmp4, d_file1
    ):
        scanner.scan(dir_path=master_dir_path)
        scanner.clean(dir_path=duplicate_dir_path, archive_to=archive_dir_path, check_xmp=True)
        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(os.path.dirname(d_file1))) == 1
        assert len(os.listdir(archive_dir_path)) == 0

    def test_xmp_compare_xmp1_dup_only(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, d_file1, d_file1_xmp1
    ):
        scanner.scan(dir_path=master_dir_path)
        scanner.clean(dir_path=duplicate_dir_path, archive_to=archive_dir_path, check_xmp=True)
        assert len(os.listdir(master_dir_path)) == 1
        assert len(os.listdir(os.path.dirname(d_file1))) == 2
        assert len(os.listdir(archive_dir_path)) == 0

    def test_xmp_compare_xmp2_dup_only(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, d_file1, d_file1_xmp2
    ):
        scanner.scan(dir_path=master_dir_path)
        scanner.clean(dir_path=duplicate_dir_path, archive_to=archive_dir_path, check_xmp=True)
        assert len(os.listdir(master_dir_path)) == 1
        assert len(os.listdir(os.path.dirname(d_file1))) == 2
        assert len(os.listdir(archive_dir_path)) == 0

    def test_xmp_compare_xmp3_dup_only(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, d_file1, d_file1_xmp3
    ):
        scanner.scan(dir_path=master_dir_path)
        scanner.clean(dir_path=duplicate_dir_path, archive_to=archive_dir_path, check_xmp=True)
        assert len(os.listdir(master_dir_path)) == 1
        assert len(os.listdir(os.path.dirname(d_file1))) == 2
        assert len(os.listdir(archive_dir_path)) == 0

    def test_xmp_compare_xmp4_dup_only(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, d_file1, d_file1_xmp4
    ):
        scanner.scan(dir_path=master_dir_path)
        scanner.clean(dir_path=duplicate_dir_path, archive_to=archive_dir_path, check_xmp=True)
        assert len(os.listdir(master_dir_path)) == 1
        assert len(os.listdir(os.path.dirname(d_file1))) == 2
        assert len(os.listdir(archive_dir_path)) == 0

    def test_xmp_compare_xmp1_xmp1(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, m_file1_xmp1, d_file1, d_file1_xmp1
    ):
        scanner.scan(dir_path=master_dir_path)
        scanner.clean(dir_path=duplicate_dir_path, archive_to=archive_dir_path, check_xmp=True, include=['jpg'])
        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(os.path.dirname(d_file1))) == 0
        assert len(os.listdir(os.path.join(archive_dir_path, 'subdir'))) == 2

    def test_xmp_compare_xmp2_xmp1(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, m_file1_xmp2, d_file1, d_file1_xmp1
    ):
        scanner.scan(dir_path=master_dir_path)
        scanner.clean(dir_path=duplicate_dir_path, archive_to=archive_dir_path, check_xmp=True, include=['jpg'])
        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(os.path.dirname(d_file1))) == 0
        assert len(os.listdir(os.path.join(archive_dir_path, 'subdir'))) == 2

    def test_xmp_compare_xmp3_xmp1(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, m_file1_xmp3, d_file1, d_file1_xmp1
    ):
        scanner.scan(dir_path=master_dir_path)
        scanner.clean(dir_path=duplicate_dir_path, archive_to=archive_dir_path, check_xmp=True, include=['jpg'])
        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(os.path.dirname(d_file1))) == 0
        assert len(os.listdir(os.path.join(archive_dir_path, 'subdir'))) == 2

    def test_xmp_compare_xmp4_xmp1(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, m_file1_xmp4, d_file1, d_file1_xmp1
    ):
        scanner.scan(dir_path=master_dir_path)
        scanner.clean(dir_path=duplicate_dir_path, archive_to=archive_dir_path, check_xmp=True, include=['jpg'])
        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(os.path.dirname(d_file1))) == 0
        assert len(os.listdir(os.path.join(archive_dir_path, 'subdir'))) == 2

    def test_xmp_compare_xmp1_xmp2(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, m_file1_xmp1, d_file1, d_file1_xmp2
    ):
        scanner.scan(dir_path=master_dir_path)
        scanner.clean(dir_path=duplicate_dir_path, archive_to=archive_dir_path, check_xmp=True, include=['jpg'])
        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(os.path.dirname(d_file1))) == 0
        assert len(os.listdir(os.path.join(archive_dir_path, 'subdir'))) == 2

    def test_xmp_compare_xmp2_xmp2(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, m_file1_xmp2, d_file1, d_file1_xmp2
    ):
        scanner.scan(dir_path=master_dir_path)
        scanner.clean(dir_path=duplicate_dir_path, archive_to=archive_dir_path, check_xmp=True, include=['jpg'])
        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(os.path.dirname(d_file1))) == 0
        assert len(os.listdir(os.path.join(archive_dir_path, 'subdir'))) == 2

    def test_xmp_compare_xmp3_xmp2(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, m_file1_xmp3, d_file1, d_file1_xmp2
    ):
        scanner.scan(dir_path=master_dir_path)
        scanner.clean(dir_path=duplicate_dir_path, archive_to=archive_dir_path, check_xmp=True, include=['jpg'])
        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(os.path.dirname(d_file1))) == 0
        assert len(os.listdir(os.path.join(archive_dir_path, 'subdir'))) == 2

    def test_xmp_compare_xmp4_xmp2(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, m_file1_xmp4, d_file1, d_file1_xmp2
    ):
        scanner.scan(dir_path=master_dir_path)
        scanner.clean(dir_path=duplicate_dir_path, archive_to=archive_dir_path, check_xmp=True, include=['jpg'])
        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(os.path.dirname(d_file1))) == 0
        assert len(os.listdir(os.path.join(archive_dir_path, 'subdir'))) == 2

    def test_xmp_compare_xmp1_xmp3(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, m_file1_xmp1, d_file1, d_file1_xmp3
    ):
        scanner.scan(dir_path=master_dir_path)
        scanner.clean(dir_path=duplicate_dir_path, archive_to=archive_dir_path, check_xmp=True, include=['jpg'])
        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(os.path.dirname(d_file1))) == 0
        assert len(os.listdir(os.path.join(archive_dir_path, 'subdir'))) == 2

    def test_xmp_compare_xmp2_xmp3(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, m_file1_xmp2, d_file1, d_file1_xmp3
    ):
        scanner.scan(dir_path=master_dir_path)
        scanner.clean(dir_path=duplicate_dir_path, archive_to=archive_dir_path, check_xmp=True, include=['jpg'])
        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(os.path.dirname(d_file1))) == 0
        assert len(os.listdir(os.path.join(archive_dir_path, 'subdir'))) == 2

    def test_xmp_compare_xmp3_xmp3(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, m_file1_xmp3, d_file1, d_file1_xmp3
    ):
        scanner.scan(dir_path=master_dir_path)
        scanner.clean(dir_path=duplicate_dir_path, archive_to=archive_dir_path, check_xmp=True, include=['jpg'])
        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(os.path.dirname(d_file1))) == 0
        assert len(os.listdir(os.path.join(archive_dir_path, 'subdir'))) == 2

    def test_xmp_compare_xmp4_xmp3(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, m_file1_xmp4, d_file1, d_file1_xmp3
    ):
        scanner.scan(dir_path=master_dir_path)
        scanner.clean(dir_path=duplicate_dir_path, archive_to=archive_dir_path, check_xmp=True, include=['jpg'])
        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(os.path.dirname(d_file1))) == 0
        assert len(os.listdir(os.path.join(archive_dir_path, 'subdir'))) == 2

    def test_xmp_compare_xmp1_xmp4(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, m_file1_xmp1, d_file1, d_file1_xmp4
    ):
        scanner.scan(dir_path=master_dir_path)
        scanner.clean(dir_path=duplicate_dir_path, archive_to=archive_dir_path, check_xmp=True, include=['jpg'])
        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(os.path.dirname(d_file1))) == 0
        assert len(os.listdir(os.path.join(archive_dir_path, 'subdir'))) == 2

    def test_xmp_compare_xmp2_xmp4(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, m_file1_xmp2, d_file1, d_file1_xmp4
    ):
        scanner.scan(dir_path=master_dir_path)
        scanner.clean(dir_path=duplicate_dir_path, archive_to=archive_dir_path, check_xmp=True, include=['jpg'])
        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(os.path.dirname(d_file1))) == 0
        assert len(os.listdir(os.path.join(archive_dir_path, 'subdir'))) == 2

    def test_xmp_compare_xmp3_xmp4(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, m_file1_xmp3, d_file1, d_file1_xmp4
    ):
        scanner.scan(dir_path=master_dir_path)
        scanner.clean(dir_path=duplicate_dir_path, archive_to=archive_dir_path, check_xmp=True, include=['jpg'])
        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(os.path.dirname(d_file1))) == 0
        assert len(os.listdir(os.path.join(archive_dir_path, 'subdir'))) == 2

    def test_xmp_compare_xmp4_xmp4(
            self,
            scanner,
            master_dir_path, duplicate_dir_path, archive_dir_path,
            m_file1, m_file1_xmp4, d_file1, d_file1_xmp4
    ):
        scanner.scan(dir_path=master_dir_path)
        scanner.clean(dir_path=duplicate_dir_path, archive_to=archive_dir_path, check_xmp=True, include=['jpg'])
        assert len(os.listdir(master_dir_path)) == 2
        assert len(os.listdir(os.path.dirname(d_file1))) == 0
        assert len(os.listdir(os.path.join(archive_dir_path, 'subdir'))) == 2
