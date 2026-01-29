import io
import os

import pytest

from tests.fixtures import Fixtures
from xclean.scanner import Scanner


class TestCase(Fixtures):

    def test_clean_archive_newfiles_prompt(
            self,
            scanner_with_prompt,
            master_dir_path, duplicate_dir_path, newfiles_dir_path, newfiles_sub_dir_path,
            m_file1, m_file1_xmp1, m_file2, m_file2_xmp1,
            d_file3, d_file3_xmp1, d_file4, d_file4_xmp1,
            monkeypatch,
    ):
        monkeypatch.setattr('sys.stdin', io.StringIO('y\n y\n y\n y\n'))
        results = scanner_with_prompt.clean(
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
