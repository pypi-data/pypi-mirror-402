import os
from argparse import ArgumentParser
from xclean.scanner import Scanner


def main():
    parser = ArgumentParser(description='File de-duplication utility v0.0.15')
    parser.add_argument('--main', help='Directory where main files reside')
    parser.add_argument('--target', help='Directory where duplicate files may reside')
    parser.add_argument('--archive-to', help='Archive duplicates to directory')
    parser.add_argument('--archive-new', help='Archive new files to directory')
    parser.add_argument('--import-new', help='Directory where to import new main files into')
    parser.add_argument('-i', '--include', nargs='*', help='Include Extensions')
    parser.add_argument('-x', '--exclude', nargs='*', help='Exclude Extensions')
    parser.add_argument('--exclude-dir', nargs='*', help='Exclude directories')
    parser.add_argument('--unprotect', default=False, action='store_true', help='Unprotect main files')
    parser.add_argument('--remove', default=False, action='store_true', help='Remove duplicate files')
    parser.add_argument('--trash', default=False, action='store_true', help='Trash duplicate files')
    parser.add_argument('--clean', default=False, action='store_true', help='Clean database')
    parser.add_argument('--xmp', default=False, action='store_true', help='Include xmp files when checking for duplicates')
    parser.add_argument('--aae', default=False, action='store_true', help='Include aae files when checking for duplicates')
    parser.add_argument('--prompt', default=False, action='store_true', help='Prompt before making changes')
    parser.add_argument('--new', default=False, action='store_true', help='Report new files')
    parser.add_argument('--dup', default=False, action='store_true', help='Report duplicate files')
    parser.add_argument('--summary', default=False, action='store_true', help='Report summary of changes')
    parser.add_argument('--copy', default=False, action='store_true', help='Copy files instead of moving')
    parser.add_argument('--ignore-existing', default=False, action='store_true', help='Ignore existing archive files')
    parser.add_argument('--minsize', default=100, help='Minimum size to clean')
    args = parser.parse_args()
    home_dir = os.environ.get('HOME')
    if home_dir is None:
        db_path = 'xclean.sqlite'
    else:
        db_path = os.path.join(home_dir, 'xclean.sqlite')
    xclean = Scanner(
        db_path=db_path,
        clean=args.clean,
        prompt=args.prompt,
        copy=args.copy,
        ignore_existing=args.ignore_existing,
        min_size=args.minsize,
    )
    if args.main is not None:
        xclean.scan(
            dir_path=args.main,
            include=args.include,
            exclude=args.exclude,
            exclude_dir=args.exclude_dir,
        )
    if args.target is not None:
        xclean.clean(
            dir_path=args.target,
            include=args.include,
            exclude=args.exclude,
            exclude_dir=args.exclude_dir,
            remove_dups=args.remove,
            trash_dups=args.trash,
            check_xmp=args.xmp,
            check_aae=args.aae,
            archive_to=args.archive_to,
            archive_new=args.archive_new,
            import_new=args.import_new,
            unprotect=args.unprotect,
            new=args.new,
            dup=args.dup,
            summary=args.summary,
        )
