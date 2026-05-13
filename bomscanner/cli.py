import sys
import shutil
import subprocess
from pathlib import Path

# Use current working directory as project root so CLI runs from user's CWD
ROOT = Path.cwd()
PY = sys.executable

USAGE = """
Usage: bomscanner <command> [arg]

Commands:
  sync                Download and sync NVD data (runs sync_nvd.py)
  pom.xml             Scan using given pom.xml file (or 'pom.xml')
  requirements.txt    Scan using given requirements.txt file (or 'requirements.txt')
  help                Show this help
If no argument is provided, runs default scan against requirements.txt.
"""


def run_sync():
    script = ROOT / 'sync_nvd.py'
    # fallback to package scripts/sync.py
    if not script.exists():
        pkg_script = Path(__file__).resolve().parent / 'scripts' / 'sync.py'
        if pkg_script.exists():
            script = pkg_script
        else:
            print('sync_nvd.py not found in project root or package scripts')
            return 1
    return subprocess.call([PY, str(script)])


def run_scan(arg=None):
    script = ROOT / 'scan_nvd.py'
    # fallback to package scripts/scan.py
    if not script.exists():
        pkg_script = Path(__file__).resolve().parent / 'scripts' / 'scan.py'
        if pkg_script.exists():
            script = pkg_script
        else:
            print('scan_nvd.py not found in project root or package scripts')
            return 1
    cmd = [PY, str(script)]
    if arg:
        cmd.append(arg)
    return subprocess.call(cmd)


def print_last_scan_log():
    log_path = ROOT / 'nvd_log.json'
    if not log_path.exists():
        return
    try:
        import json
        with open(log_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(json.dumps(data, indent=2))
    except Exception:
        # fall back to raw print
        try:
            print(log_path.read_text(encoding='utf-8'))
        except Exception:
            pass


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        # If no arguments provided, show help (match `bomscanner help`).
        print(USAGE)
        return 0
    cmd = argv[0].lower()
    if cmd == 'help' or cmd in ('-h', '--help'):
        print(USAGE)
        return 0
    if cmd == 'sync':
        return run_sync()
    if cmd.endswith('.xml') or cmd == 'pom.xml':
        return run_scan(cmd)
    if cmd.endswith('.txt') or cmd == 'requirements.txt':
        return run_scan(cmd)
    # allow direct filename
    path = ROOT / cmd
    if path.exists() and path.suffix in ('.xml', '.txt'):
        rc = run_scan(str(path))
        if rc == 0:
            print_last_scan_log()
        return rc
    print('Unknown command or file:', cmd)
    print("Run 'bomscanner help' for usage.")
    return 2


if __name__ == '__main__':
    sys.exit(main())
