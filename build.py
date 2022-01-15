import os.path
from docbox import conv


def main():
    conv(["-r", "--no-number", "-o", "docs/index.html"])
    conv(["--all-headers-in-toc", "--input", "yaksha_docs", "-o", "docs/yaksha.html"])


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
