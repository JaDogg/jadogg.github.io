import argparse
import html
import os.path
import re
import subprocess
from enum import Enum
from typing import List

import markdown
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.styles import get_style_by_name

NEWLINE = '\n'  # Unix newline character
NOT_ALLOWED = re.compile(r"[^a-z0-9]")
TWO_OR_MORE_DASHES = re.compile(r"[\-]+")
PYG_STYLE = get_style_by_name('rrt')
PYG_FORMATTER = HtmlFormatter(style=PYG_STYLE)


def pyg_highlight(code: str, lexer: str) -> str:
    if lexer:
        lex = get_lexer_by_name(lexer)
    else:
        lex = guess_lexer(code)
    return highlight(code, lex, PYG_FORMATTER)


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
    CODE = 7  # lines between two ```
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

    def __init__(self, file_path: str, num_gen, id_gen):
        self._file_path = file_path
        self._num_gen = num_gen
        self._id_gen = id_gen

    def parse(self) -> List[Token]:
        tokens: List[Token] = []
        mode = "any"
        html_lines = []
        code_lines = []
        possible_type = "python"
        with open(self._file_path, "r+", encoding="utf-8") as f:
            for line in f:
                # remove all spaces from left side of the line
                # as we do ignore those
                stripped_line = line.lstrip()
                if mode != "code" and not stripped_line:
                    continue
                if mode == "html":
                    if stripped_line.startswith("!!"):
                        tokens.append(Token(TokenType.RAW_HTML, NEWLINE.join(html_lines), NEWLINE.join(html_lines)))
                        mode = "any"
                        continue
                    html_lines.append(stripped_line)
                elif mode == "code":
                    if stripped_line.startswith("```"):
                        code = NEWLINE.join(code_lines)
                        tokens.append(Token(TokenType.RAW_HTML, pyg_highlight(code, possible_type), code))
                        mode = "any"
                        possible_type = "python"
                        continue
                    code_lines.append(line.rstrip())
                elif stripped_line.startswith("*"):
                    level, text = count_and_strip(stripped_line, "*")
                    tokens.append(Token(TokenType.BULLET, markdown.markdown(html.escape(text)), text, level))
                elif stripped_line.startswith("#"):
                    level, text = count_and_strip(stripped_line, "#")
                    num = self._num_gen.generate(level)
                    id_ = self._id_gen.generate(text)
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
                elif stripped_line.startswith("```"):
                    mode = "code"
                    if len(stripped_line) > 3:
                        type_ = stripped_line[3:].strip().lower()
                        if type_:
                            possible_type = type_
                    code_lines = []
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
    def __init__(self, files: List[DocBoxFile], target: str, template_cell: str, template_start: str,
                 template_end: str, minifier_command: str, title: str, desc: str, all_headers: bool):
        """
        Html Converter - convert set of docbox files to a single html
        :param files: list of DocBoxFile objects
        :param target: target file
        :param template_cell: how a single cell is converted to HTML
        :param template_start: start of template before we put all cells in target
        :param template_end: end of template
        :param minifier_command: shell command to minify html
        :param title: html title
        :param desc: html description
        :param all_headers: All headers in ToC?
        """
        self._files = files
        self._target = target
        with open(template_cell, "r+", encoding="utf-8") as h:
            self._cell_template = h.read()
        with open(template_start, "r+", encoding="utf-8") as h:
            self._main_template0 = h.read()
        with open(template_end, "r+", encoding="utf-8") as h:
            self._main_template1 = h.read()
        self._minifier_command = minifier_command
        self._title = title
        self._desc = desc
        self._all_headers = all_headers
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
                    if self._all_headers or section.level == 1:
                        toc.append(
                            "<div class=\"toc-item\"><a href=\"#{id_}\">{title}</a></div>".format(id_=section.header_id,
                                                                                                  title=section.data))
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
        subprocess.run(self._minifier_command, shell=True, check=True)

    def _fill_main_template(self, template_text: str):
        return template_text.replace("$TITLE$", self._title) \
            .replace("$DESCRIPTION$", self._desc).replace("$TOC$", self._toc) \
            .replace("$STYLES$", PYG_FORMATTER.get_style_defs('.highlight'))

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


class DocBoxApp:
    def __init__(self):
        self._root = os.path.dirname(os.path.abspath(__file__))
        self._input_dir = os.path.join(self._root, "posts")
        self._template_root = os.path.join(self._root, "template")
        self._template_cell = os.path.join(self._template_root, "cell.html")
        self._template_main0 = os.path.join(self._template_root, "main0.html")
        self._template_main1 = os.path.join(self._template_root, "main1.html")
        self._output_file = os.path.join(self._root, "docs", "index.html")
        self._title = html.escape("JaDogg's Website")
        self._desc = html.escape("JaDogg's Website -> I love programming in C++ and Python. This is my new website.")
        self._minifier_command = "html-minifier --collapse-whitespace --remove-comments --remove-optional-tags " \
                                 "--remove-redundant-attributes --remove-script-type-attributes " \
                                 "--remove-tag-whitespace --use-short-doctype " \
                                 "--minify-css true --minify-js true -o \"$OUT$\" \"$OUT$\""
        self._id_gen = IdGen()
        self._num_gen = TitleNumGen()

    def convert(self, arguments):
        parsed_args = self._parse_arguments(arguments)
        self._use_args(parsed_args)
        self._convert(parsed_args.r, parsed_args.allheaders)

    def _parse_arguments(self, arguments):
        parser = argparse.ArgumentParser("docbox", description="Docbox HTML Generator")
        parser.add_argument("-o,--output", dest="out", type=str, default=self._output_file, help="Output file")
        parser.add_argument("--input", dest="inp", type=str, default=self._input_dir, help="Input dir")
        parser.add_argument("--template", dest="template", type=str, default=self._template_root,
                            help="Use a different template directory")
        parser.add_argument("--title", dest="title", type=str, default="JaDogg's Website", help="Set a title")
        parser.add_argument("--desc", dest="desc", type=str,
                            default="JaDogg's Website -> I love programming in C++ and Python. This is my new website.",
                            help="Set a description")
        parser.add_argument("-r,--reverse", dest="r", default=False, action="store_true",
                            help="Create output using input files in reverse order")
        parser.add_argument("--no-number", dest="nonum", default=False, action="store_true",
                            help="Do not put numbers in titles")
        parser.add_argument("--all-headers-in-toc", dest="allheaders", default=False, action="store_true",
                            help="All headers in ToC")
        if arguments:
            result = parser.parse_args(arguments)
        else:
            result = parser.parse_args()
        return result

    def _use_args(self, result):
        self._input_dir = result.inp
        self._output_file = result.out
        self._minifier_command = self._minifier_command.replace("$OUT$", self._output_file)
        self._title = html.escape(result.title)
        self._desc = html.escape(result.title)
        self._template_root = result.template
        if result.nonum:
            self._num_gen = NullNumGen()
        self._template_cell = os.path.join(self._template_root, "cell.html")
        self._template_main0 = os.path.join(self._template_root, "main0.html")
        self._template_main1 = os.path.join(self._template_root, "main1.html")
        self._id_gen.reset()
        self._num_gen.reset()

    def _convert(self, reversed_=False, all_headers=False):
        docs = [x for x in os.listdir(self._input_dir) if x.endswith(".docbox")]
        if reversed_:
            docs = sorted(docs, key=lambda x: -int(x[:4]))
        else:
            docs = sorted(docs, key=lambda x: int(x[:4]))
        docs = [os.path.join(self._input_dir, x) for x in docs]
        doc_objects = [DocBoxFile(x, self._num_gen, self._id_gen) for x in docs]
        HtmlConverter(doc_objects, self._output_file, self._template_cell,
                      self._template_main0, self._template_main1,
                      self._minifier_command, self._title, self._desc, all_headers).convert()


def conv(arguments=None):
    DocBoxApp().convert(arguments)


if __name__ == '__main__':
    conv()
