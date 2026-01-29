"""
KaggleRun CLI - Execute Python on Kaggle GPUs from your terminal.

Usage:
    kagglerun --url <jupyter-url> "print('Hello GPU!')"
    kagglerun --url <jupyter-url> script.py
    kagglerun --url <jupyter-url> --gpu-info
    kagglerun --url <jupyter-url> --list-files
"""

import argparse
import sys
import os
from typing import Optional

from . import __version__
from .executor import KaggleExecutor


def get_url_from_env() -> Optional[str]:
    """Get Kaggle URL from environment variable."""
    return os.environ.get('KAGGLE_JUPYTER_URL')


def main(args: Optional[list] = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='kagglerun',
        description='Execute Python on Kaggle\'s FREE GPUs from your terminal.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  kagglerun --url <URL> "print('Hello from Kaggle GPU!')"
  kagglerun --url <URL> script.py
  kagglerun --url <URL> --gpu-info
  kagglerun --url <URL> --upload local.py --as remote.py
  kagglerun --url <URL> --download results.csv

Environment:
  KAGGLE_JUPYTER_URL    Default Jupyter URL (so you don't need --url)

Get your URL:
  1. Open Kaggle notebook with GPU
  2. Click "..." menu -> "Copy VS Code Server URL"
  3. Add "/proxy" to the end of the URL
'''
    )

    parser.add_argument('code', nargs='?', help='Python code or .py file to execute')
    parser.add_argument('--url', '-u', help='Kaggle Jupyter URL (or set KAGGLE_JUPYTER_URL)')
    parser.add_argument('--version', '-v', action='version', version=f'kagglerun {__version__}')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress status messages')
    parser.add_argument('--timeout', '-t', type=int, default=120, help='Execution timeout (default: 120s)')

    # Info commands
    parser.add_argument('--gpu-info', action='store_true', help='Show GPU information')
    parser.add_argument('--system-info', action='store_true', help='Show system information')
    parser.add_argument('--list-files', '-l', action='store_true', help='List files in /kaggle/working/')
    parser.add_argument('--test', action='store_true', help='Test connection only')

    # File operations
    parser.add_argument('--upload', help='Upload a local file to /kaggle/working/')
    parser.add_argument('--as', dest='remote_name', help='Remote filename for upload')
    parser.add_argument('--download', help='Download a file from /kaggle/working/')
    parser.add_argument('--output', '-o', help='Local path for downloaded file')
    parser.add_argument('--read', help='Read and print a remote file')

    parsed = parser.parse_args(args)

    # Get URL
    url = parsed.url or get_url_from_env()
    if not url:
        print("Error: No Kaggle URL provided.", file=sys.stderr)
        print("Use --url or set KAGGLE_JUPYTER_URL environment variable.", file=sys.stderr)
        print("\nTo get your URL:", file=sys.stderr)
        print("  1. Open Kaggle notebook with GPU enabled", file=sys.stderr)
        print("  2. Click '...' menu -> 'Copy VS Code Server URL'", file=sys.stderr)
        print("  3. Add '/proxy' to the end", file=sys.stderr)
        return 1

    # Only add /proxy for path-based URLs (not query parameter format)
    if '?token=' not in url and not url.endswith('/proxy'):
        if url.endswith('/'):
            url = url + 'proxy'
        else:
            url = url + '/proxy'

    # Create executor
    verbose = not parsed.quiet
    executor = KaggleExecutor(url, verbose=verbose, timeout=parsed.timeout)

    # Test connection
    if not executor.test_connection():
        print("Error: Failed to connect to Kaggle Jupyter.", file=sys.stderr)
        print("Check your URL and ensure the notebook is running.", file=sys.stderr)
        return 1

    if parsed.test:
        print("Connection successful!")
        return 0

    # Handle commands
    if parsed.gpu_info:
        result = executor.get_gpu_info()
        return 0 if result['success'] else 1

    if parsed.system_info:
        result = executor.get_system_info()
        return 0 if result['success'] else 1

    if parsed.list_files:
        result = executor.list_files()
        return 0 if result['success'] else 1

    if parsed.upload:
        remote_name = parsed.remote_name or os.path.basename(parsed.upload)
        result = executor.upload_file(parsed.upload, remote_name)
        return 0 if result['success'] else 1

    if parsed.download:
        data = executor.download_file(parsed.download)
        if data is None:
            print(f"Error: Failed to download {parsed.download}", file=sys.stderr)
            return 1

        output_path = parsed.output or os.path.basename(parsed.download)
        with open(output_path, 'wb') as f:
            f.write(data)
        print(f"Downloaded: {output_path} ({len(data)} bytes)")
        return 0

    if parsed.read:
        result = executor.read_file(parsed.read)
        if not result['success']:
            print(f"Error: Failed to read {parsed.read}", file=sys.stderr)
            return 1
        return 0

    # Execute code
    if not parsed.code:
        parser.print_help()
        return 0

    # Check if it's a file
    if parsed.code.endswith('.py') and os.path.isfile(parsed.code):
        result = executor.run_file(parsed.code, timeout=parsed.timeout)
    else:
        result = executor.execute(parsed.code, timeout=parsed.timeout)

    if result['errors']:
        for err in result['errors']:
            print(f"Error: {err}", file=sys.stderr)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
