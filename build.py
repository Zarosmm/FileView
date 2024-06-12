import sys
from pathlib import Path
from PyInstaller.__main__ import run

if __name__ == '__main__':
    filename = 'main.py'  # 替换为你的 Python 脚本文件名
    spec_file = f'{filename[:-3]}.spec'
    sys.argv = ["pyinstaller", "--onefile", "--noconsole", "--specpath", str(Path('build') / 'spec'), "--distpath", str(Path('build') / 'dist'), "--workpath", str(Path('build') / 'build'), filename]
    run()
