import argparse
import html
import os.path
import re
import subprocess
from enum import Enum
from typing import List

import markdown

ROOT = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(ROOT, "input")
TEMPLATE_ROOT = os.path.join(ROOT, "template")
TEMPLATE_CELL = os.path.join(TEMPLATE_ROOT, "cell.html")
TEMPLATE_MAIN0 = os.path.join(TEMPLATE_ROOT, "main0.html")
TEMPLATE_MAIN1 = os.path.join(TEMPLATE_ROOT, "main1.html")
OUTPUT_FILE = os.path.join(ROOT, "index.html")
NEWLINE = '\n'  # Unix newline character
TITLE = html.escape("JaDogg's Website")
DESC = html.escape("JaDogg's Website -> I love programming in C++ and Python. This is my new website.")
NOT_ALLOWED = re.compile(r"[^a-z0-9]")
TWO_OR_MORE_DASHES = re.compile(r"[\-]+")
MINIFIER_COMMAND = "html-minifier --collapse-whitespace --remove-comments --remove-optional-tags " \
                   "--remove-redundant-attributes --remove-script-type-attributes " \
                   "--remove-tag-whitespace --use-short-doctype " \
                   "--minify-css true --minify-js true -o \"$OUT$\" \"$OUT$\""


class IdGen:
    def __init__(self):
        self._unique = set()

    def reset(self):
        self._unique = set()

    def generate(self, text: str):
        counter = 1
        result = TWO_OR_MORE_DASHES.sub("-", NOT_ALLOWED.sub("-", text.lower())).strip("-")
        if result and result not in self._unique:
            return result
        new_result = result + str(counter)
        while new_result in self._unique:
            counter += 1
            new_result = result + str(counter)
        return new_result


class TitleNumGen:
    def __init__(self):
        self._prev_level = -1
        self._counters = []

    def reset(self):
        self._prev_level = -1
        self._counters = []

    def generate(self, level):
        if self._prev_level < level:
            self._counters.append(0)
        elif self._prev_level > level and len(self._counters) >= 2:
            self._counters.pop()

        self._counters[-1] = self._counters[-1] + 1
        self._prev_level = level
        return self._conv()

    def _conv(self):
        return "[" + ".".join([str(x) for x in self._counters]) + "] "


class NullNumGen:
    def generate(self, _):
        return ""

    def reset(self):
        pass


ID_GEN = IdGen()
NUM_GEN = TitleNumGen()


# NOTE: All token type data should be html escaped see --> https://docs.python.org/3/library/html.html
# however, RAW_HTML & NOTE_RAW_HTML is written as it is
class TokenType(Enum):
    """
    Token types
    """
    RAW_HTML = 1  # Any line that starts with `!!` read all lines until another `!!`, whole thing is raw HTML section
    HEADER = 2  # Any line that starts with a `#` is <h1>, `##` is h2, `###` is h3, and so forth until h6.
    BULLET = 3  # Any line that starts with `*` is a bullet point, `**` is a bullet point inside a bullet point
    SEPARATOR = 4  # if line contains `---` only (otherwise it's a normal line), this separate notes
    NOTE = 5  # if a line starts with `;` it is a note, which we will add to same cell on right side
    NOTE_RAW_HTML = 6  # if a line starts with `;!` same as note but in raw HTML
    DEFAULT = 10  # Normal line


class Token:
    def __init__(self, token_type_: TokenType, data_: str, raw_data_: str, level_: int = 0):
        """
        Create a token object
        :param token_type_: type of the token
        :param data_: data for the token
        :param raw_data_: un processed data
        :param level_: level used for header and bullets (* is 1, ** is 2, # is 1 and ## is two)
        """
        self.token_type: TokenType = token_type_
        self.data: str = data_
        self.raw_data: str = raw_data_
        self.level: int = level_
        self.header_id: str = ""


def count_and_strip(text: str, char: str) -> (int, str):
    output = []
    count = 0
    counting = True
    for x in text:
        if counting and x == char:
            count += 1
            continue
        counting = False
        output.append(x)
    return count, "".join(output)


class DocBoxFile:
    """
    A DocBox file object
    * This reads and breaks a file to tokens that HtmlConverter can write as HTML
    """

    def __init__(self, file_path: str):
        self.file_path = file_path

    def parse(self) -> List[Token]:
        tokens: List[Token] = []
        mode = "any"
        html_lines = []
        with open(self.file_path, "r+", encoding="utf-8") as f:
            for line in f:
                # remove all spaces from left side of the line
                # as we do ignore those
                stripped_line = line.lstrip()
                if not stripped_line:
                    continue
                if mode == "html":
                    if stripped_line.startswith("!!"):
                        tokens.append(Token(TokenType.RAW_HTML, NEWLINE.join(html_lines), NEWLINE.join(html_lines)))
                        mode = "any"
                        continue
                    html_lines.append(stripped_line)
                elif stripped_line.startswith("*"):
                    level, text = count_and_strip(stripped_line, "*")
                    tokens.append(Token(TokenType.BULLET, markdown.markdown(html.escape(text)), text, level))
                elif stripped_line.startswith("#"):
                    level, text = count_and_strip(stripped_line, "#")
                    num = NUM_GEN.generate(level)
                    id_ = ID_GEN.generate(text)
                    text = num + text
                    # Title just uses HTML escape, no need for fancy markdown for titles
                    token = Token(TokenType.HEADER, html.escape(text), text, level)
                    token.header_id = id_
                    tokens.append(token)
                elif stripped_line.startswith(";!"):
                    tokens.append(Token(TokenType.NOTE_RAW_HTML, stripped_line[2:], stripped_line[2:]))
                elif stripped_line.startswith(";"):
                    tokens.append(
                        Token(TokenType.NOTE, markdown.markdown(html.escape(stripped_line[1:])), stripped_line[1:]))
                elif stripped_line.startswith("!!"):
                    mode = "html"  # TokenType.RAW_HTML
                    html_lines = []  # this clears our temporary buffer
                elif stripped_line.rstrip() == "---":
                    tokens.append(Token(TokenType.SEPARATOR, "", ""))
                else:
                    tokens.append(
                        Token(TokenType.DEFAULT, markdown.markdown(html.escape(stripped_line)), stripped_line))
        return tokens


# Output HTML file format
# -------------------------
# We should basically just replace $TITLE$ with TITLE
#   and $BOXES$ with outcome of our HTML generation
# Each section of the document should be written as below
# Table of contents can be generated from headers and should go to $TOC$
"""
  ┌─────────────┬──────────────────────────┬─────────────────┐
  │             │                          │                 │
  │             │    Cell     1 content    │    Notes for    │
  │             │                          │    Cell    1    │
  │ Table of    ├──────────────────────────┼─────────────────┤
  │  Contents   │                          │                 │
  │             │                          │                 │
  │             │    Cell      2 content   │   Notes for     │
  │             │                          │   Cell     2    │
  │             │                          │                 │
  │             │                          │                 │
  │             │                          │                 │
  │             ├──────────────────────────┼─────────────────┤
  │             │                          │                 │
  │             │                          │                 │
  │             │                          │                 │
  │             │                          │                 │
  │             │                          │                 │
  │             │                          │                 │
  │             │                          │                 │
  │             ├──────────────────────────┼─────────────────┤
  │             │                          │                 │
  │             │                          │                 │
  │             │                          │                 │
  │             │                          │                 │
  │             │                          │                 │
  │             │                          │                 │
  │             │                          │                 │
  │             │                          │                 │
  │             │                          │                 │
  │             │                          │                 │
  │             │                          │                 │
  │             │                          │                 │
  │             │                          │                 │
  │             │                          │                 │
  │             │                          │                 │
  │             ├──────────────────────────┼─────────────────┤
  │             │                          │                 │
  │             │                          │                 │
  │             │                          │                 │
  │             │                          │                 │
  │             │                          │                 │
  │             │                          │                 │
  │             │                          │                 │
  └─────────────┴──────────────────────────┴─────────────────┘

"""


class Cell:
    def __init__(self, content_: str, note_: str):
        """
        Constructor for cell object
        :param content_: content html
        :param note_: note html
        """
        self.content = content_
        self.note = note_


class HtmlConverter:
    def __init__(self, files: List[DocBoxFile], target: str):
        """
        Html Converter - convert set of docbox files to a single html
        :param files: list of DocBoxFile objects
        """
        self._files = files
        self._target = target
        with open(TEMPLATE_CELL, "r+", encoding="utf-8") as h:
            self._cell_template = h.read()
        with open(TEMPLATE_MAIN0, "r+", encoding="utf-8") as h:
            self._main_template0 = h.read()
        with open(TEMPLATE_MAIN1, "r+", encoding="utf-8") as h:
            self._main_template1 = h.read()
        self._toc = ""

    def convert(self):
        """
        Capture tokens to cells with content and notes
        write cells to html format
        """
        cells: List[Cell] = []
        content: List[str] = []
        note: List[str] = []
        toc: List[str] = []
        prev_bullet = -1
        for section in self._get_sections():
            if section.token_type == TokenType.BULLET:
                # depend on level place bullet points
                # see below example
                #
                # [[input]]
                #
                # * banana 1
                # * banana 2
                # ** this is a special banana
                # ** very special indeed
                # * banana 3
                # * banana 4
                #
                # [[output]]
                #
                # <ul>
                # <li>banana 1</li>
                # <li>banana 2
                #     <ul>
                #         <li>this is a special banana</li>
                #         <li>very special indeed</li>
                #     </ul>
                # </li>
                # <li>banana 3</li>
                # <li>banana 4</li>
                # </ul>
                #
                if prev_bullet == -1:
                    content.append("<ul>")
                elif prev_bullet > section.level:
                    content.append("</ul>")
                elif prev_bullet < section.level:
                    content.append("<ul>")
                else:
                    content.append("</li>")
                content.append("<li>{0}".format(section.data))
                prev_bullet = section.level
            else:
                if prev_bullet != -1:
                    content.append("</li></ul>")
                prev_bullet = -1
                if section.token_type == TokenType.NOTE or section.token_type == TokenType.NOTE_RAW_HTML:
                    note.append(section.data)
                elif section.token_type == TokenType.RAW_HTML:
                    content.append(section.data)
                elif section.token_type == TokenType.HEADER:
                    if section.level == 1:
                        toc.append(
                            "<div class=\"toc-item\"><a href=\"#{id_}\">{title}</a></div>".format(id_=section.header_id, title=section.data))
                    content.append(
                        "<h{level} id=\"{id_}\">{title}</h{level}>".format(id_=section.header_id, title=section.data,
                                                                           level=section.level + 1))
                elif section.token_type == TokenType.SEPARATOR:
                    # You can create a cell now with acquired content and note stuffs
                    cells.append(Cell(NEWLINE.join(content), NEWLINE.join(note)))
                    content = []
                    note = []
                else:  # SectionType.DEFAULT
                    content.append(section.data)
        self._toc = NEWLINE.join(toc)
        self._write_html(cells)

    def _write_html(self, cells: List[Cell]):
        with open(self._target, "w+", encoding="utf-8") as h:
            h.write(self._fill_main_template(self._main_template0))
            for cell in self._put_cell_in_template(cells):
                h.write(cell)
            h.write(self._fill_main_template(self._main_template1))
        subprocess.run(MINIFIER_COMMAND, shell=True, check=True)

    def _fill_main_template(self, template_text: str):
        return template_text.replace("$TITLE$", TITLE) \
            .replace("$DESCRIPTION$", DESC).replace("$TOC$", self._toc)

    def _put_cell_in_template(self, cells):
        for cell in cells:
            yield self._cell_template.replace("$CONTENT$", cell.content) \
                .replace("$NOTE$", cell.note)

    def _get_sections(self):
        for doc in self._files:
            for section in doc.parse():
                yield section
            yield Token(TokenType.RAW_HTML, "<hr />", "<hr />")
            yield Token(TokenType.NOTE_RAW_HTML, "<hr />", "<hr />")


def _convert(reversed_=False):
    docs = [x for x in os.listdir(INPUT_DIR) if x.endswith(".docbox")]
    if reversed_:
        docs = sorted(docs, key=lambda x: -int(x[:4]))
    else:
        docs = sorted(docs, key=lambda x: int(x[:4]))
    docs = [os.path.join(INPUT_DIR, x) for x in docs]
    HtmlConverter([DocBoxFile(x) for x in docs], OUTPUT_FILE).convert()


def conv(arguments=None):
    global INPUT_DIR
    global OUTPUT_FILE
    global TITLE
    global DESC
    global TEMPLATE_ROOT
    global TEMPLATE_CELL
    global TEMPLATE_MAIN0
    global TEMPLATE_MAIN1
    global MINIFIER_COMMAND
    global NUM_GEN
    global ID_GEN
    parser = argparse.ArgumentParser("docbox", description="Docbox HTML Generator")
    parser.add_argument("-o,--output", dest="out", type=str, default=OUTPUT_FILE, help="Output file")
    parser.add_argument("--input", dest="inp", type=str, default=INPUT_DIR, help="Input dir")
    parser.add_argument("--template", dest="template", type=str, default=TEMPLATE_ROOT,
                        help="Use a different template directory")
    parser.add_argument("--title", dest="title", type=str, default="JaDogg's Website", help="Set a title")
    parser.add_argument("--desc", dest="desc", type=str,
                        default="JaDogg's Website -> I love programming in C++ and Python. This is my new website.",
                        help="Set a description")
    parser.add_argument("-r,--reverse", dest="r", default=False, action="store_true",
                        help="Create output using input files in reverse order")
    parser.add_argument("--no-number", dest="nonum", default=False, action="store_true",
                        help="Do not put numbers in titles")
    if arguments:
        result = parser.parse_args(arguments)
    else:
        result = parser.parse_args()
    INPUT_DIR = result.inp
    OUTPUT_FILE = result.out
    MINIFIER_COMMAND = MINIFIER_COMMAND.replace("$OUT$", OUTPUT_FILE)
    TITLE = html.escape(result.title)
    DESC = html.escape(result.title)
    TEMPLATE_ROOT = result.template
    if result.nonum:
        NUM_GEN = NullNumGen()
    TEMPLATE_CELL = os.path.join(TEMPLATE_ROOT, "cell.html")
    TEMPLATE_MAIN0 = os.path.join(TEMPLATE_ROOT, "main0.html")
    TEMPLATE_MAIN1 = os.path.join(TEMPLATE_ROOT, "main1.html")
    ID_GEN.reset()
    NUM_GEN.reset()
    _convert(result.r)


if __name__ == '__main__':
    conv()
