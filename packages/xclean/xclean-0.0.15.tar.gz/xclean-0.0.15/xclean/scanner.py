import os
import shutil
import sqlite3
import sys
from typing import Optional, List


class Scanner:
    """Scan the file system for duplicate files"""

    def __init__(
            self, *,
            db_path: str,
            clean=False,
            prompt=False,
            copy=False,
            ignore_existing=False,
            min_size=100,
    ):
        """
        Scanner for duplicate file detection
        :param db_path: Path to the sqlite3 database file
        :param clean: If true then delete any existing database file before starting
        :param prompt: If true then prompt for confirmation
        :param copy: If true then copy files instead of moving them
        :param ignore_existing: If true then ignore existing archive files
        :param min_size: The minimum size to clean
        """
        self.prompt = prompt
        self.copy = copy
        self.ignore_existing = ignore_existing
        self.min_size = min_size
        print('xclean: File de-duplication utility')
        print()
        if clean is True:
            if os.path.exists(db_path):
                os.remove(db_path)
        self._con = sqlite3.connect(db_path)
        self._cur = self._con.cursor()
        self._cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS DirInfo
            (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT
            ,path TEXT NOT NULL
            ,UNIQUE (path)
            )
            '''
        )
        self._con.commit()
        self._cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS FileInfo
            (file_size INTEGER NOT NULL
            ,dir_id INTEGER NOT NULL
            ,file_name TEXT NOT NULL
            ,PRIMARY KEY (dir_id, file_name)
            )
            '''
        )
        self._con.commit()
        self._cur.execute(
            '''
            CREATE INDEX IF NOT EXISTS FileSizeNdx ON FileInfo (file_size)
            '''
        )
        self._con.commit()
        self._cur.execute(
            'SELECT COALESCE(COUNT(*), 0) AS total FROM DirInfo'
        )
        total_dirs = int(self._cur.fetchone()[0])
        self._cur.execute(
            'SELECT COALESCE(COUNT(*), 0) AS total FROM FileInfo'
        )
        total_files = int(self._cur.fetchone()[0])
        print(f'{total_dirs} main directories, {total_files} main files')
        print()

    def scan(
            self, *,
            dir_path: str,
            include: Optional[List[str]]=None,
            exclude: Optional[List[str]]=None,
            exclude_dir: Optional[List[str]]=None,
    ):
        """
        Scan directory and subdirectories for main files
        :param dir_path: Path to directory to start the scan in
        :param include: Optional filename extensions to include in scan
        :param exclude: Optional filename extensions to exclude from scan
        :param exclude_dir: Optional directory names to exclude from scan
        """
        dir_path = os.path.realpath(dir_path)
        print(f'Scan {dir_path} for main files')
        file_count = 0
        total_size = 0
        for root_dir, dir_names, file_names in os.walk(dir_path):
            eligible_file_names = self._eligible_file_names(root_dir, file_names, include, exclude, exclude_dir)
            if len(eligible_file_names) > 0:
                dir_id = self._record_main_directory(root_dir)
                for file_name in eligible_file_names:
                    file_count += 1
                    file_size = self._record_new_file(dir_id, root_dir, file_name)
                    total_size += file_size
            self._con.commit()
        print()
        print(f'{file_count:,} files scanned with {total_size:,} bytes')
        print()
        return {
            'files': {
                'count': file_count,
                'size': total_size,
            }
        }

    def _record_new_file(self, dir_id, root_dir, file_name):
        file_path = os.path.join(root_dir, file_name)
        stat_info = os.stat(file_path)
        file_size = stat_info.st_size
        self._cur.execute(
            '''INSERT INTO FileInfo (file_size, dir_id, file_name) VALUES (?,?,?)''',
            (file_size, dir_id, file_name)
        )
        return file_size

    def _record_main_directory(self, root_dir: str) -> int:
        dir_id = self._create_directory_entry(root_dir)
        self._remove_old_directory_files(dir_id)
        return dir_id

    def _remove_old_directory_files(self, dir_id):
        self._cur.execute(
            '''DELETE FROM FileInfo WHERE dir_id = ?''',
            (dir_id,)
        )

    def _create_directory_entry(self, root_dir):
        self._cur.execute(
            '''INSERT OR IGNORE INTO DirInfo (path) VALUES (?)''',
            (root_dir,)
        )
        self._cur.execute(
            '''SELECT id FROM DirInfo WHERE path = ?''',
            (root_dir,)
        )
        dir_id = self._cur.fetchone()[0]
        return dir_id

    @staticmethod
    def _eligible_file_names(
            root_dir: str,
            file_names: List[str],
            include: Optional[List[str]],
            exclude: Optional[List[str]],
            exclude_dir: Optional[List[str]],
    ):
        if exclude_dir is not None:
            for dir_name in root_dir.split(os.path.sep):
                if dir_name in exclude_dir:
                    return []
        eligible_file_names = []
        for file_name in file_names:
            if include is not None:
                _f, _ext = os.path.splitext(file_name)
                if _ext.startswith('.'):
                    _ext = _ext[1:]
                if _ext.lower() not in include:
                    continue
            if exclude is not None:
                _f, _ext = os.path.splitext(file_name)
                if _ext.startswith('.'):
                    _ext = _ext[1:]
                if _ext.lower() in exclude:
                    continue
            file_path = os.path.join(root_dir, file_name)
            if os.path.islink(file_path):
                continue
            eligible_file_names.append(file_name)
        return eligible_file_names

    def clean(
            self, *,
            dir_path: str,
            include: Optional[List[str]]=None,
            exclude: Optional[List[str]]=None,
            exclude_dir: Optional[List[str]]=None,
            remove_dups=False,
            trash_dups=False,
            check_xmp=False,
            check_aae=False,
            archive_to: Optional[str]=None,
            archive_new: Optional[str]=None,
            import_new: Optional[str]=None,
            unprotect=False,
            new=False,
            dup=False,
            summary=False,
    ):
        """
        Scan directory and subdirectories for duplicate files
        :param dir_path: Path to directory to start the scan in
        :param include: Optional filename extensions to include in the scan
        :param exclude: Optional filename extensions to exclude from the scan
        :param exclude_dir: Optional directory names to exclude from scan
        :param remove_dups: If true then remove the duplicate files
        :param trash_dups: If true then send duplicates to the trash
        :param check_xmp: If true then check the xmp matches as well
        :param check_aae: If true then check the aae matches as well
        :param archive_to: Path to archive duplicate files to
        :param archive_new: Path to archive new files to
        :param import_new: Path to import new files into
        :param unprotect: If true then unprotect main files
        :param new: If true then report new files
        :param dup: If true then report duplicate files
        :param summary: If true then report summary of changes
        """
        dir_path = os.path.realpath(dir_path)
        print(f'Scan {dir_path} for duplicates')
        dups_count = 0
        dups_size = 0
        new_count = 0
        new_size = 0
        files_count = 0
        files_size = 0
        rollback = False
        abort = False
        for root_dir, dir_names, file_names in os.walk(dir_path, topdown=False):
            if abort:
                break
            self._cur.execute(
                '''SELECT di.id FROM DirInfo di WHERE di.path = ?''',
                (root_dir,)
            )
            row = self._cur.fetchone()
            if row is not None:
                if not unprotect:
                    continue  # do not clean main directories
                dir_id = int(row[0])
            else:
                dir_id = None
            eligible_file_names = self._eligible_file_names(root_dir, file_names, include, exclude, exclude_dir)
            if len(eligible_file_names) > 0:
                for file_name in eligible_file_names:
                    if abort:
                        break
                    files_count += 1
                    target_file_path = os.path.join(root_dir, file_name)
                    if not os.path.exists(target_file_path):
                        continue
                    stat_info = os.stat(target_file_path)
                    file_size = stat_info.st_size
                    if file_size <= self.min_size:
                        continue
                    files_size += file_size
                    self._cur.execute(
                        '''
                        SELECT di.path, fi.file_name 
                        FROM FileInfo fi 
                        JOIN DirInfo di ON di.id = fi.dir_id 
                        WHERE fi.file_size = ?
                        ''',
                        (file_size,)
                    )
                    main_files = self._cur.fetchall()
                    matched_with_main_file = False
                    for row in main_files:
                        if abort:
                            break
                        main_dir_path = str(row[0])
                        main_file_name = str(row[1])
                        if root_dir == main_dir_path:
                            if file_name == main_file_name:
                                matched_with_main_file = True
                                continue  # ignore if the scanned file is the main file
                        main_file_path = os.path.join(main_dir_path, main_file_name)
                        if self._files_are_the_same(target_file_path, main_file_path, check_xmp=check_xmp, check_aae=check_aae):
                            matched_with_main_file = True
                            dups_count += 1
                            dups_size += file_size
                            if not self._handle_duplicate_file(
                                dir_path=dir_path, dir_id=dir_id, file_name=file_name,
                                main_file_path=main_file_path,
                                target_file_path=target_file_path,
                                dups_count=dups_count, file_size=file_size,
                                archive_to=archive_to,
                                trash_dups=trash_dups,
                                remove_dups=remove_dups,
                                dup=dup,
                            ):
                                abort = True
                                break
                            if archive_to is None and trash_dups is not True and remove_dups is not True:
                                rollback = True
                            break
                    if not matched_with_main_file:
                        new_count += 1
                        new_size += file_size
                        if not self._handle_new_file(
                            target_file_path=target_file_path,
                            dir_path=dir_path,
                            archive_new=archive_new,
                            import_new=import_new,
                            new_count=new_count,
                            file_size=file_size,
                            new=new,
                        ):
                            abort = True
                            break
            if archive_new is not None:
                if root_dir != dir_path:
                    if len(os.listdir(root_dir)) == 0:
                        os.rmdir(root_dir)
        if summary:
            print()
            print(f'{dups_count:,} of {files_count:,} duplicate files occupying {dups_size:,} bytes')
            print(f'{new_count:,} of {files_count:,} new files occupying {new_size:,} bytes')
            print()
        if rollback:
            self._con.rollback()
        else:
            self._con.commit()
        return {
            'duplicates': {
                'count': dups_count,
                'size': dups_size,
            },
            'files': {
                'count': files_count,
                'size': files_size,
            },
            'new': {
                'count': new_count,
                'size': new_size,
            },
            'abort': abort
        }

    def _handle_new_file(
            self, *,
            target_file_path, dir_path, archive_new, import_new,
            new_count, file_size,
            new=False,
    ) -> bool:

        if new:
            print()
            print(f'  New  {target_file_path}')
            print(f'       {new_count:,} : (size {file_size:,})')

        if archive_new is not None:
            if not self._archive_file(
                    target_file_path, dir_path, archive_new,
                    archive_type='new',
            ):
                return False
            xmp_file_path = Scanner._find_xmp_file(target_file_path)
            if xmp_file_path is not None:
                if not self._archive_file(
                        xmp_file_path, dir_path, archive_new,
                        archive_type='new',
                ):
                    return False
            aae_file_path = Scanner._find_aae_file(target_file_path)
            if aae_file_path is not None:
                if not self._archive_file(
                        aae_file_path, dir_path, archive_new,
                        archive_type='new',
                ):
                    return False

        if import_new is not None:

            for target_file_path in [
                target_file_path,
                Scanner._find_xmp_file(target_file_path),
                Scanner._find_aae_file(target_file_path),
            ]:
                if target_file_path is None:
                    continue
                if not self._archive_file(
                        target_file_path, dir_path, import_new,
                        archive_type='new',
                ):
                    return False
                archive_file_path = self._archive_file_path(target_file_path, dir_path, import_new)
                import_new_parts = import_new.split('/')
                archive_file_parts = archive_file_path.split('/')
                dir_id = None
                root_dir = None
                for parts in range(len(import_new_parts), len(archive_file_parts)):
                    root_dir = '/'.join(archive_file_parts[0:parts])
                    dir_id = self._create_directory_entry(root_dir)
                file_name = archive_file_parts[-1]
                self._record_new_file(dir_id, root_dir, file_name)
            self._con.commit()

        return True

    def _handle_duplicate_file(
            self, *,
            dir_path, dir_id, file_name,
            main_file_path, target_file_path,
            dups_count, file_size,
            archive_to, trash_dups, remove_dups,
            dup=False,
    ) -> bool:
        if dup:
            print()
            print(f'  Main {main_file_path}')
            print(f'  Dup  {target_file_path}')
            print(f'       {dups_count:,} : (size {file_size:,})')
        if archive_to is not None:
            if not self._archive_file(
                    target_file_path, dir_path, archive_to,
            ):
                return False
            xmp_file_path = Scanner._find_xmp_file(target_file_path)
            if xmp_file_path is not None:
                if not self._archive_file(
                        xmp_file_path, dir_path, archive_to,
                ):
                    return False
            aae_file_path = Scanner._find_aae_file(target_file_path)
            if aae_file_path is not None:
                if not self._archive_file(
                        aae_file_path, dir_path, archive_to,
                ):
                    return False
        elif trash_dups is True:
            if not self._trash_file(target_file_path):
                return False
            xmp_file_path = Scanner._find_xmp_file(target_file_path)
            if xmp_file_path is not None:
                if not self._trash_file(xmp_file_path):
                    return False
            aae_file_path = Scanner._find_aae_file(target_file_path)
            if aae_file_path is not None:
                if not self._trash_file(aae_file_path):
                    return False
        elif remove_dups is True:
            if not self._remove_file(target_file_path):
                return False
            xmp_file_path = Scanner._find_xmp_file(target_file_path)
            if xmp_file_path is not None:
                if not self._remove_file(xmp_file_path):
                    return False
            aae_file_path = Scanner._find_aae_file(target_file_path)
            if aae_file_path is not None:
                if not self._remove_file(aae_file_path):
                    return False
        if dir_id is not None:
            self._cur.execute(
                'DELETE FROM FileInfo '
                'WHERE dir_id = ? '
                'AND file_name = ?',
                (dir_id, file_name)
            )
            xmp_file_path = Scanner._find_xmp_file(target_file_path)
            if xmp_file_path is not None:
                xmp_file_name = os.path.basename(xmp_file_path)
                self._cur.execute(
                    'DELETE FROM FileInfo '
                    'WHERE dir_id = ? '
                    'AND file_name = ?',
                    (dir_id, xmp_file_name)
                )
            aae_file_path = Scanner._find_aae_file(target_file_path)
            if aae_file_path is not None:
                aae_file_name = os.path.basename(aae_file_path)
                self._cur.execute(
                    'DELETE FROM FileInfo '
                    'WHERE dir_id = ? '
                    'AND file_name = ?',
                    (dir_id, aae_file_name)
                )
        return True

    def _remove_file(self, target_file_path) -> bool:
        print(f'  Remove duplicate file {target_file_path}')
        if not os.path.exists(target_file_path):
            print(f'Duplicate file {target_file_path} does not exist')
            return False
        if not self._prompted():
            return False
        os.remove(target_file_path)
        if os.path.exists(target_file_path):
            print(f'Failed to remove {target_file_path}')
            return False
        return True

    def _trash_file(self, target_file_path: str) -> bool:
        trash_files_path = self.trash_directory()
        if trash_files_path is None:
            print(f'No trash directory found')
            return False
        file_name = os.path.basename(target_file_path)
        trash_file_path = os.path.join(trash_files_path, file_name)
        print(f'  Trash duplicate file {target_file_path}')
        if not os.path.exists(target_file_path):
            print(f'Duplicate file {target_file_path} does not exist')
            return False
        if os.path.exists(trash_file_path):
            print(f'Trash file {trash_file_path} already exists')
            return False
        if not self._prompted():
            return False
        shutil.copy2(target_file_path, trash_file_path)
        if not os.path.exists(trash_file_path):
            print(f'Failed to trash file to {trash_file_path}')
            return False
        if os.stat(trash_file_path).st_size != os.stat(target_file_path).st_size:
            print(f'Failed to properly trash file to {trash_file_path}')
            return False
        os.remove(target_file_path)
        if os.path.exists(target_file_path):
            print(f'Failed to remove {target_file_path}')
            return False
        return True

    @staticmethod
    def trash_directory():
        home = os.getenv('HOME')
        local = os.path.join(home, '.local')
        share = os.path.join(local, 'share')
        trash = os.path.join(share, 'Trash')
        trash_files_path = os.path.join(trash, 'files')
        if os.path.exists(trash_files_path):
            return trash_files_path
        return None

    def _prompted(self) -> bool:
        if self.prompt:
            yesno = input('  Do you want to continue? [y/N/q] ')
            if yesno.strip().lower().startswith('y'):
                return True
            if yesno.strip().lower().startswith('q'):
                sys.exit(1)
            return False
        return True

    def _archive_file(
            self,
            target_file_path: str,
            dir_path: str,
            archive_to: str,
            archive_type='duplicate',
    ) -> bool:
        archive_file_path = self._archive_file_path(target_file_path, dir_path, archive_to)
        archive_dir_path = os.path.dirname(archive_file_path)
        print(f'  Archive {archive_type} file to {archive_file_path}')
        if not os.path.exists(target_file_path):
            print(f'Could not find {target_file_path}')
            return False
        if os.path.exists(archive_file_path):
            print(f'Archive file already exists {archive_file_path}')
            if self.ignore_existing:
                if os.stat(archive_file_path).st_size == os.stat(target_file_path).st_size:
                    return True
            return False
        if not self._prompted():
            return False
        if not os.path.exists(archive_dir_path):
            os.makedirs(archive_dir_path, mode=0o700, exist_ok=False)
            if not os.path.exists(archive_dir_path):
                print(f'Failed to create folder {archive_dir_path}')
                return False
        shutil.copy2(target_file_path, archive_file_path)
        if not os.path.exists(archive_file_path):
            print(f'Failed to copy {target_file_path} to {archive_file_path}')
            return False
        if os.stat(archive_file_path).st_size != os.stat(target_file_path).st_size:
            print(f'Failed to fully copy {target_file_path} to {archive_file_path}')
            return False
        if not self.copy:
            print(f'  Remove {target_file_path}')
            os.remove(target_file_path)
            if os.path.exists(target_file_path):
                print(f'Failed to remove {target_file_path}')
                return False
        return True

    def _archive_file_path(self, target_file_path: str, dir_path: str, archive_to: str) -> str:
        target_file_suffix = target_file_path[len(dir_path):]
        while target_file_suffix.startswith('/'):
            target_file_suffix = target_file_suffix[1:]
        archive_file_path = os.path.join(archive_to, target_file_suffix)
        return archive_file_path

    @staticmethod
    def _files_are_the_same(source_file_path: str, target_file_path: str, check_xmp=False, check_aae=False) -> bool:
        source_fp = os.open(source_file_path, os.O_RDONLY)
        target_fp = os.open(target_file_path, os.O_RDONLY)
        source_bytes = os.read(source_fp, 1000)
        target_bytes = os.read(target_fp, 1000)
        while source_bytes == target_bytes and len(source_bytes) > 0:
            source_bytes = os.read(source_fp, 1000)
            target_bytes = os.read(target_fp, 1000)
        os.close(source_fp)
        os.close(target_fp)
        if source_bytes != target_bytes:
            return False
        if check_xmp is True:
            if not Scanner._compare_xmp(source_file_path, target_file_path):
                return False
        if check_aae is True:
            if not Scanner._compare_aae(source_file_path, target_file_path):
                return False
        return True

    @staticmethod
    def _compare_xmp(source_file_path: str, target_file_path: str) -> bool:
        xmp_source_file_path = Scanner._find_xmp_file(source_file_path)
        xmp_target_file_path = Scanner._find_xmp_file(target_file_path)
        if xmp_source_file_path is None:
            if xmp_target_file_path is None:
                return True
            return False
        if xmp_target_file_path is None:
            return False
        return Scanner._files_are_the_same(xmp_source_file_path, xmp_target_file_path)

    @staticmethod
    def _compare_aae(source_file_path: str, target_file_path: str) -> bool:
        aae_source_file_path = Scanner._find_aae_file(source_file_path)
        aae_target_file_path = Scanner._find_aae_file(target_file_path)
        if aae_source_file_path is None:
            if aae_target_file_path is None:
                return True
            return False
        if aae_target_file_path is None:
            return False
        return Scanner._files_are_the_same(aae_source_file_path, aae_target_file_path)

    @staticmethod
    def _find_xmp_file(file_path: str) -> Optional[str]:
        return Scanner._find_file(file_path, 'xmp')

    @staticmethod
    def _find_aae_file(file_path: str) -> Optional[str]:
        return Scanner._find_file(file_path, 'aae')

    @staticmethod
    def _find_file(file_path: str, extn_lower: str):
        extn_lower = extn_lower.lower()
        extn_upper = extn_lower.upper()
        aae_file_path = f'{file_path}.{extn_lower}'
        if os.path.exists(aae_file_path):
            return aae_file_path
        aae_file_path = f'{file_path}.{extn_upper}'
        if os.path.exists(aae_file_path):
            return aae_file_path
        prefix, extn = os.path.splitext(file_path)
        aae_file_path = f'{prefix}.{extn_lower}'
        if os.path.exists(aae_file_path):
            return aae_file_path
        aae_file_path = f'{prefix}.{extn_upper}'
        if os.path.exists(aae_file_path):
            return aae_file_path
        return None
