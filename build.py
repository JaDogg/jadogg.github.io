import os.path
import subprocess

import docbox


def main():
    subprocess.run("css-minify -d ./css/ -o ./docs/assets", shell=True)
    docbox.conv(["-r", "--no-number", "-o", "docs/index.html"])
    docbox.conv(["--all-headers-in-toc", "--input", "yaksha_docs", "-o", "docs/yaksha.html"])
    # DocBox documentation
    docbox.DocBoxApp().convert_text(["--all-headers-in-toc", "-o",
                                     "docs/docbox.html"], docbox.__doc__)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
