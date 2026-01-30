from simple_alto_parser.utils import get_logger


class BaseParser:

    logger = None
    matches = []
    batch_conditions = []

    def __init__(self, parser):
        """The constructor of the class. It initializes the list of files.
        The lines are a list of AltoXMLElement objects."""
        self.logger = get_logger()
        self.parser = parser
        self.matches = []

    def mark(self, name, value):
        """Add the given category to all matches."""
        for match in self.matches:
            self.parser.get_alto_files()[match.file_id].get_text_lines()[match.line_id].add_parser_data(name, value)
        return self

    def clear(self):
        self.matches = []
        return self

    def print_matches(self):
        """Print all matches."""
        for match in self.matches:
            print("Found pattern '%s' in line '%s'." %
                  (match,
                   self.parser.get_alto_files()[match.file_id].get_text_lines()[match.line_id].get_text()))
        return self

    def get_unmatched(self):
        """Return all unmatched lines."""
        match_ids = []
        for match in self.matches:
            match_ids.append((match.file_id, match.line_id))

        unmatched = []
        file_id = 0
        for file in self.parser.get_alto_files():
            line_id = 0
            for line in file.get_text_lines():
                if (file_id, line_id) not in match_ids:
                    unmatched.append(line.get_text())
                line_id += 1
            file_id += 1
        return unmatched

    def batch(self, name):
        self.batch_conditions = []

        name_found = False
        for batch in self.parser.parser_config['batches']:
            if batch['name'] == name:
                name_found = True
                batch_config = batch
                break

        # Find name in parser config
        if name_found:
            print("Config Found")
            for cond in batch_config['conditions']:
                self.batch_conditions.append((cond['key'], "in", self.get_page_list(cond['values'])))
        else:
            raise Exception("Batch name not found in parser config.")

        # If name exists, get batch config
        # Set variables according to batch config

        print("BC", self.batch_conditions)

        return self

    def all(self):
        self.batch_conditions = []
        return self

    def is_in_batch(self, file):
        if len(self.batch_conditions) == 0:
            return True

        conditions_met = True
        for cond in self.batch_conditions:
            if int(file.file_meta_data[cond[0]]) not in cond[2]:
                conditions_met = False
                break

        return conditions_met

    def get_page_list(self, pages):
        if pages == "__all__":
            return [int(file.file_meta_data['page']) for file in self.files]
        else:
            parts = pages.split(",")
            page_list = []
            for part in parts:
                if "-" in part:
                    start, end = part.split("-")
                    page_list += [i for i in range(int(start), int(end) + 1)]
                else:
                    page_list.append(int(part))
            return sorted(page_list)


class ParserMatch:

    def __init__(self, file_id, line_id, match):
        self.file_id = file_id
        self.line_id = line_id
        self.match = match
