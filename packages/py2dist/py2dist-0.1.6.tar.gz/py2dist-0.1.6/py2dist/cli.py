import argparse
import os
import sys

from .compiler import CompileOptions, Compiler, find_ccache, get_files_in_dir
from . import __version__


def parse_exclude_files(value: str, root_dir: str) -> list:
    exclude = []
    for path in value.split(","):
        path = path.strip()
        if not path:
            continue
        if path.endswith('/') or path.endswith('\\'):
            dir_path = path.rstrip('/').rstrip('\\')
            full_dir = os.path.join(root_dir, dir_path)
            if os.path.isdir(full_dir):
                for f in get_files_in_dir(full_dir, True, 1):
                    exclude.append(os.path.join(dir_path, f))
        else:
            exclude.append(path)
    return exclude


def main():
    parser = argparse.ArgumentParser(
        prog="py2dist",
        description="Compile Python files to .so/.pyd using Cython"
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-f", "--file", dest="source_file", help="Single .py file to compile")
    parser.add_argument("-d", "--directory", dest="source_dir", help="Directory to compile")
    parser.add_argument("-o", "--output", dest="output_dir", default="dist", help="Output directory (default: dist)")
    parser.add_argument("-m", "--maintain", dest="exclude", default="", help="Files/dirs to exclude (comma-separated)")
    parser.add_argument("-p", "--python", dest="python_version", default="", help="Python version (e.g., 3)")
    parser.add_argument("-x", "--nthread", type=int, default=1, help="Number of parallel threads")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode")
    parser.add_argument("-r", "--release", action="store_true", help="Release mode (clean tmp files)")
    parser.add_argument("-c", "--ccache", dest="ccache", nargs="?", const="auto", default=None, help="Use ccache (auto-detect or specify path)")

    args = parser.parse_args()

    if not args.source_file and not args.source_dir:
        parser.print_help()
        sys.exit(1)

    if args.source_file and args.source_dir:
        print("Error: Cannot use both -f and -d")
        sys.exit(1)

    exclude_files = []
    if args.exclude and args.source_dir:
        exclude_files = parse_exclude_files(args.exclude, args.source_dir.rstrip('/'))

    ccache_path = None
    if args.ccache:
        if args.ccache == "auto":
            ccache_path = find_ccache()
            if not ccache_path and not args.quiet:
                print("Warning: ccache not found, compiling without it")
        else:
            if os.path.isfile(args.ccache) and os.access(args.ccache, os.X_OK):
                ccache_path = args.ccache
            else:
                print(f"Error: ccache not found at {args.ccache}")
                sys.exit(1)

    try:
        opts = CompileOptions(
            python_version=args.python_version,
            source_file=args.source_file,
            source_dir=args.source_dir.rstrip('/') if args.source_dir else None,
            exclude_files=exclude_files,
            nthread=args.nthread,
            quiet=args.quiet,
            release=args.release,
            output_dir=args.output_dir,
            ccache=ccache_path
        )
        compiler = Compiler(opts)
        output = compiler.compile()
        if not args.quiet:
            print(f"Compiled successfully to: {output}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
