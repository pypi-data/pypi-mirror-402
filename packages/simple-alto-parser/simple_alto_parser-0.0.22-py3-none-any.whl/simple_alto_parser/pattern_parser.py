import re

from simple_alto_parser import BaseParser
from simple_alto_parser.base_parser import ParserMatch


class AltoPatternParser(BaseParser):

    matches = []

    def __init__(self, parser):
        """The constructor of the class."""
        super().__init__(parser)

    def find(self, pattern):
        """Find a pattern in the text lines."""
        self.clear()

        fidx = 0
        for file in self.parser.get_alto_files():
            if self.is_in_batch(file):
                lidx = 0
                for line in file.get_text_lines():
                    match = re.search(pattern, line.get_text())
                    if match:
                        self.matches.append(PatternMatch(pattern, fidx, lidx, match))
                    lidx += 1
            else:
                print("Not in batch")

            fidx += 1

        return self

    def categorize(self, category):
        """Add the given category to all matches."""
        for match in self.matches:
            if type(category) == str:
                self.parser.get_alto_files()[match.file_id].get_text_lines()[match.line_id]\
                    .add_parser_data(category, match.match.group(1))
            if type(category) == list:
                c_id = 1
                for c in category:
                    self.parser.get_alto_files()[match.file_id].get_text_lines()[match.line_id]\
                        .add_parser_data(c, match.match.group(c_id))
                    c_id += 1
        return self

    def remove(self, replacement=''):
        """Remove all matched patterns from matching lines."""
        for match in self.matches:
            self.parser.get_alto_files()[match.file_id].get_text_lines()[match.line_id].set_text(
                re.sub(match.pattern, replacement,
                       self.parser.get_alto_files()[match.file_id].get_text_lines()[match.line_id].get_text()))
        return self

    def replace(self, replacement):
        self.remove(replacement)
        return self


class PatternMatch(ParserMatch):

    pattern = None

    def __init__(self, pattern, file_id, line_id, match):
        super().__init__(file_id, line_id, match)
        self.pattern = pattern
