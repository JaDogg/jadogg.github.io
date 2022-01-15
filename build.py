import os.path
from docbox import conv


def main():
    # Create index.html
    conv(["-r", "--no-number", "-o", "docs/index.html"])


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
