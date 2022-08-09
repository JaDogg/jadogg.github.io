import os.path
import subprocess

from docbox import docbox


def main():
    path = os.path.abspath(".")
    subprocess.run("css-minify -d ./css/ -o ./docs/assets", shell=True)
    docbox.conv(["-r", "--no-number", "-o", "docs/index.html", "--posts=posts"], root=path)
    docbox.conv(["--all-headers-in-toc", "--input", "system_design", "-o", "docs/sdt.html"], root=path)
    # DocBox documentation
    docbox.DocBoxApp(root=path).convert_text(["--all-headers-in-toc", "-o",
                                              "docs/docbox.html"], docbox.__doc__)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
