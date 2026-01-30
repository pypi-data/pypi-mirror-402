import json
import re
import sys

from simple_alto_parser import BaseParser
from simple_alto_parser.base_parser import ParserMatch


class AltoDictionaryParser(BaseParser):
    """This class is used to find patterns in the text lines of an alto file."""

    dictionaries = []

    def __init__(self, parser):
        """The constructor of the class. It initializes the list of files.
        The lines are a list of AltoXMLElement objects."""
        super().__init__(parser)

    def load(self, dictionary_file):
        """Load a dictionary from a json file."""
        self.logger.info(f'Loading dictionary "{dictionary_file}"...')
        all_variants = []
        dictionary = json.load(open(dictionary_file, encoding='utf-8'))
        for entry in dictionary:
            if 'label' in entry:
                if 'variants' not in entry:
                    entry['variants'] = [entry['label']]
                if 'type' not in entry:
                    entry['type'] = 'undefined'

                entry['variants'] = [v.strip() for v in entry['variants']]
                entry['variants'] = sorted(entry['variants'], key=len, reverse=True)

                extended_variants = []
                for v in entry['variants']:
                    extended_variants.append((v, entry))
                all_variants.extend(extended_variants)
            else:
                self.logger.error(f'Dictionary Entry "{entry}" from dictionary "{dictionary_file}" has no label.')
                sys.exit()

        all_variants = sorted(all_variants, key=len, reverse=True)
        self.dictionaries.append(Dictionary(dictionary, all_variants))
        self.logger.info(f"Loaded dictionary: {dictionary_file}")

    def find(self, strict=True, restrict_to=None, multiple=True):
        """Find a pattern in the text lines."""
        self.clear()
        file_id = 0
        for file in self.parser.get_alto_files():
            line_id = 0

            for line in file.get_text_lines():
                match_on_line = False

                for dictionary in self.dictionaries:
                    for variant in dictionary.all_variants:
                        if restrict_to is not None and variant[1]['type'] != restrict_to:
                            continue
                        if strict:
                            match = variant[0].strip('.').lower() == line.get_text().strip().strip('.').lower()
                            if match:
                                match = variant[0]
                        else:
                            match = re.search(re.escape(variant[0]), line.get_text().strip())

                        if match:
                            if not multiple and match_on_line:
                                continue
                            self.logger.debug(f"Found dictionary match '{variant[0]}' in line '{line.get_text()}'")
                            self.matches.append(DictionaryMatch(file_id, line_id, match, variant[1]))
                            match_on_line = True

                line_id += 1
            file_id += 1
        return self

    def categorize(self):
        """Add the given category to all matches."""
        for match in self.matches:
            category = match.dict_entry['type']
            if type(match.match) == str:
                match_text = match.match
            else:
                match_text = match.match.group(0)
            self.parser.get_alto_files()[match.file_id].get_text_lines()[match.line_id].add_parser_data(category, match_text)
        return self

    def remove(self, replacement=''):
        """Remove all matched patterns from matching lines."""
        for match in self.matches:
            if type(match.match) == str:
                new_text = self.parser.get_alto_files()[match.file_id].get_text_lines()[match.line_id].get_text().replace(match.match, replacement)
            else:
                new_text = self.parser.get_alto_files()[match.file_id].get_text_lines()[match.line_id].get_text().replace(match.match.group(0), replacement)

            self.parser.get_alto_files()[match.file_id].get_text_lines()[match.line_id].set_text(new_text)
        return self

    def replace(self, replacement):
        self.remove(replacement)
        return self


class DictionaryMatch(ParserMatch):

    dict_entry = {}

    def __init__(self, file_id, line_id, match, dict_entry={}):
        super().__init__(file_id, line_id, match)
        self.dict_entry = dict_entry

    def __str__(self):
        return super().__str__()
        # return self.match.group(0)

class Dictionary:

    dictionary = []
    all_variants = []

    def __init__(self, dictionary, all_variants):
        self.dictionary = dictionary
        self.all_variants = all_variants