"""Package source, measured results, and compiled report for Overleaf."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def main():
    root = Path(__file__).resolve().parents[1]
    files = [root / name for name in [
        'main.tex', 'README.md', '.gitignore', 'pyproject.toml',
        '.python-version', 'uv.lock']]
    extensions = {'.py', '.tex', '.bib', '.md', '.txt', '.csv', '.json', '.pdf', '.swift'}
    for directory in ['src', 'tests', 'results', 'report', 'provenance', 'tools', '.vscode']:
        files.extend(path for path in (root / directory).rglob('*')
                     if path.is_file() and '__pycache__' not in path.parts
                     and path.suffix in extensions)
    archive = root / 'aoa_project_2_overleaf.zip'
    with ZipFile(archive, 'w', ZIP_DEFLATED) as output:
        for path in sorted(files):
            output.write(path, path.relative_to(root).as_posix())
    with ZipFile(archive) as output:
        assert output.testzip() is None
        assert 'main.tex' in output.namelist()
        assert 'report/main.pdf' in output.namelist()
    print(f'Archive verified: {len(files)} files, {archive.stat().st_size:,} bytes')


if __name__ == '__main__':
    main()
