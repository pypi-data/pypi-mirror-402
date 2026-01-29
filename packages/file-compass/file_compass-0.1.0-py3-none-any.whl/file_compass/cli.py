"""
File Compass - CLI Interface
Command-line tool for indexing and searching files.
"""

import argparse
import asyncio
import sys
from pathlib import Path
from datetime import datetime

from .indexer import FileIndex, get_index
from .scanner import FileScanner


def cmd_index(args):
    """Build or rebuild the file index."""
    async def run():
        index = FileIndex()

        directories = args.directories if args.directories else None

        print("=" * 50)
        print("File Compass - Building Index")
        print("=" * 50)

        stats = await index.build_index(
            directories=directories,
            show_progress=True
        )

        await index.close()
        return stats

    asyncio.run(run())


def cmd_search(args):
    """Search the index."""
    async def run():
        index = get_index()

        results = await index.search(
            query=args.query,
            top_k=args.top_k,
            file_types=args.types.split(",") if args.types else None,
            directory=args.directory,
            git_only=args.git_only,
            min_relevance=args.min_relevance
        )

        if not results:
            print("No results found.")
            return

        print(f"\nFound {len(results)} results for: {args.query}\n")
        print("-" * 60)

        for i, r in enumerate(results, 1):
            print(f"\n{i}. {r.relative_path}")
            print(f"   Type: {r.file_type} | Chunk: {r.chunk_type}")
            if r.chunk_name:
                print(f"   Name: {r.chunk_name}")
            print(f"   Lines: {r.line_start}-{r.line_end} | Relevance: {r.relevance:.1%}")
            print(f"   Git: {'tracked' if r.git_tracked else 'untracked'}")
            print(f"   Preview: {r.preview[:150]}...")

        await index.close()

    asyncio.run(run())


def cmd_status(args):
    """Show index status."""
    index = get_index()
    status = index.get_status()

    print("\n" + "=" * 50)
    print("File Compass - Index Status")
    print("=" * 50)

    print(f"\nFiles indexed:  {status['files_indexed']:,}")
    print(f"Chunks indexed: {status['chunks_indexed']:,}")
    print(f"Index size:     {status['index_size_mb']:.1f} MB")
    print(f"Last build:     {status['last_build'] or 'Never'}")

    if status['file_types']:
        print("\nFile types:")
        for ft, count in sorted(status['file_types'].items(), key=lambda x: -x[1]):
            print(f"  {ft}: {count}")


def cmd_scan(args):
    """Scan directories and show what would be indexed."""
    scanner = FileScanner(directories=args.directories if args.directories else None)

    print("Scanning files...")
    files = list(scanner.scan_all())

    print(f"\nFound {len(files)} files")

    if args.verbose:
        for f in files[:50]:
            tracked = "git" if f.is_git_tracked else "   "
            print(f"  [{tracked}] {f.relative_path} ({f.file_type})")

        if len(files) > 50:
            print(f"  ... and {len(files) - 50} more")

    # Summary by type
    from collections import Counter
    types = Counter(f.file_type for f in files)
    print("\nBy type:")
    for t, c in types.most_common(10):
        print(f"  {t}: {c}")


def main():
    parser = argparse.ArgumentParser(
        description="File Compass - Semantic file search for AI workstations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build index for F:/AI
  python -m file_compass.cli index -d "F:/AI"

  # Search for files about training
  python -m file_compass.cli search "training loop implementation"

  # Search only Python files
  python -m file_compass.cli search "embedding model" --types python

  # Show index status
  python -m file_compass.cli status
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # index command
    index_parser = subparsers.add_parser("index", help="Build or rebuild the index")
    index_parser.add_argument(
        "-d", "--directories",
        nargs="+",
        help="Directories to index (default: F:/AI)"
    )
    index_parser.set_defaults(func=cmd_index)

    # search command
    search_parser = subparsers.add_parser("search", help="Search the index")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "-k", "--top-k",
        type=int,
        default=10,
        help="Number of results (default: 10)"
    )
    search_parser.add_argument(
        "-t", "--types",
        help="Comma-separated file types (e.g., python,markdown)"
    )
    search_parser.add_argument(
        "-d", "--directory",
        help="Filter by directory prefix"
    )
    search_parser.add_argument(
        "--git-only",
        action="store_true",
        help="Only show git-tracked files"
    )
    search_parser.add_argument(
        "--min-relevance",
        type=float,
        default=0.3,
        help="Minimum relevance score (0-1, default: 0.3)"
    )
    search_parser.set_defaults(func=cmd_search)

    # status command
    status_parser = subparsers.add_parser("status", help="Show index status")
    status_parser.set_defaults(func=cmd_status)

    # scan command
    scan_parser = subparsers.add_parser("scan", help="Scan directories (dry run)")
    scan_parser.add_argument(
        "-d", "--directories",
        nargs="+",
        help="Directories to scan"
    )
    scan_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show individual files"
    )
    scan_parser.set_defaults(func=cmd_scan)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
