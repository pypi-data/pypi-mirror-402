"""This module contains the AltoFile class. It is used to parse an alto file and to store the data in a structured
way. The class is used by the AltoTextParser class."""
import os.path


class AltoFile:
    """This class represents an alto file. It is used to parse an alto file and to store the data.
    The class stores TextBlocks or TextLines, depending on the configuration of the parser in the
    file_elements list. Items in this list get treated as text lines by the parser."""

    file_path = None
    """The path to the file."""

    file_elements = []
    """A list of the text elements in the alto file. These can be TextBlocks or TextLines, depending on the
    configuration of the parser."""

    parser = None
    """The parser that is used to parse the file."""

    def __init__(self, file_path, parser):
        """The constructor of the class. It takes the path to the file as a parameter."""

        if not os.path.isfile(file_path):
            raise ValueError("The given path is not a file.")

        self.file_path = file_path
        self.file_meta_data = {}
        self.parser = parser
        self.file_elements = []

    def has_lines(self):
        """This function returns True if the file has lines, otherwise it returns False."""
        return len(self.file_elements) > 0

    def get_text_lines(self):
        """This function returns the text lines of the alto file."""
        return self.file_elements

    def add_file_meta_data(self, parameter_name, parameter_value):
        """This function adds metadata to the file. It takes the parameter name and the parameter value as parameters.
        The parameter name should be a string and the parameter value can be any type."""
        self.file_meta_data[parameter_name] = parameter_value

    def get_parser_result_keys(self):
        parser_keys = []
        for file_element in self.file_elements:
            for key, value in file_element.parser_data.items():
                parser_keys.append(key)
        parser_keys = list(set(parser_keys))
        return parser_keys

    def get_csv_header(self):
        if self.has_lines():
            """This function returns the header of a single csv file. It is used by the export_to_csv() function."""

            print_manipulated = self.parser.get_config_value('export', 'csv', 'print_manipulated', default=False)
            print_filename = self.parser.get_config_value('export', 'csv', 'print_filename', default=False)
            print_attributes = self.parser.get_config_value('export', 'csv', 'print_attributes', default=False)
            print_parser_results = self.parser.get_config_value('export', 'csv', 'print_parser_results', default=False)
            print_file_meta_data = self.parser.get_config_value('export', 'csv', 'print_file_meta_data', default=False)

            csv_title_line = ['original_text']
            if print_manipulated:
                csv_title_line.append('manipulated_text')
            if print_filename:
                csv_title_line.append('file')
            if print_attributes:
                for key, value in self.file_elements[0].element_data.items():
                    csv_title_line.append(key)
            if print_parser_results:
                # Create a list of all parser keys
                csv_title_line += self.get_parser_result_keys()

            if print_file_meta_data:
                for key, value in self.file_meta_data.items():
                    csv_title_line.append(key)

            return csv_title_line
        else:
            return []

    def get_csv_lines(self, add_header=True, static_header=None):
        if self.has_lines():
            if static_header:
                header = static_header
            else:
                header = self.get_csv_header()

            if add_header:
                csv_lines = [header, ]
            else:
                csv_lines = []

            lines = self.get_text_lines()

            if len(lines) == 0:
                raise ValueError("No lines have been found in the file.")

            print_manipulated = self.parser.get_config_value('export', 'csv', 'print_manipulated', default=False)
            print_attributes = self.parser.get_config_value('export', 'csv', 'print_attributes', default=False)
            print_parser_results = self.parser.get_config_value('export', 'csv', 'print_parser_results', default=False)
            print_filename = self.parser.get_config_value('export', 'csv', 'print_filename', default=False)
            print_file_meta_data = self.parser.get_config_value('export', 'csv', 'print_file_meta_data', default=False)

            for line in lines:
                csv_line = []
                for item in header:
                    csv_line.append("")

                csv_line[header.index("original_text")] = line.get_original_text()
                if print_manipulated:
                    csv_line[header.index("manipulated_text")] = line.get_text()

                if print_filename:
                    csv_line[header.index("file")] = self.file_path

                if print_attributes:
                    for key, value in line.element_data.items():
                        try:
                            csv_line[header.index(key)] = value
                        except ValueError:
                            pass

                if print_parser_results:
                    for parser_val in self.get_parser_result_keys():
                        csv_line[header.index(parser_val)] = line.parser_data.get(parser_val, '')

                if print_file_meta_data:
                    for key, value in self.file_meta_data.items():
                        try:
                            csv_line[header.index(key)] = value
                        except ValueError:
                            pass

                csv_lines.append(csv_line)

            return csv_lines
        else:
            return []

    def get_standalone_json_object(self):
        json_object = {
            "file": self.file_meta_data,
            "elements": self.get_json_objects()
        }

        return json_object

    def get_json_objects(self):
        lines = self.get_text_lines()

        json_objects = []
        for line in lines:
            d_line = line.to_dict()
            if self.parser.get_config_value('export', 'json', 'print_file_meta_data', default=False):
                d_line['file_meta_data'] = self.file_meta_data
                if self.parser.get_config_value('export', 'json', 'print_filename', default=False):
                    d_line['file_meta_data']['file'] = self.file_path
            json_objects.append(d_line)

        return json_objects

    def get_file_name(self, ftype='plain'):
        if ftype not in ['plain', 'csv', 'json']:
            raise ValueError("The given type is not valid.")

        print(os.path.split(self.file_path)[-1])

        if ftype == 'plain':
            return os.path.split(self.file_path)[-1]
        else:
            return os.path.split(self.file_path)[-1].split('.')[0] + '.' + ftype

    def __str__(self):
        """This function returns a string representation of the class."""
        return self.file_path


class AltoFileElement:
    """This class represents a text element in an alto file. It is used to store the data of a text element."""

    text = ""
    original_text = ""
    element_data = {}
    meta_data = {}
    parser_data = {}

    def __init__(self, text):
        self.text = text
        self.original_text = text
        self.element_data = {}
        self.parser_data = {}

    def get_original_text(self, clean=True):
        """This function returns the original text of the element."""
        if clean:
            return self.original_text.replace('\n', ' ').replace('\r', '').strip()
        else:
            return self.original_text

    def get_text(self):
        """This function returns the text of the element."""
        return self.text

    def set_text(self, text):
        """This function returns the text of the element."""
        self.text = text

    def to_dict(self):
        d = {'text': self.text}
        if self.text != self.original_text:
            d['original_text'] = self.original_text

        d['element_data'] = self.element_data
        if self.meta_data != {}:
            d['meta_data'] = self.meta_data
        if self.parser_data != {}:
            d['parser_data'] = self.parser_data

        return d

    def add_meta_data(self, key, value):
        """This function adds a key-value pair to the element_data dictionary."""
        self.meta_data[key] = value

    def set_attribute(self, key, value):
        """This function adds a key-value pair to the element_data dictionary."""
        self.element_data[key] = value

    def get_attribute(self, key):
        """This function adds a key-value pair to the element_data dictionary."""
        return self.element_data.get(key, '')

    def set_attributes(self, dict):
        """This function adds a key-value pair to the element_data dictionary."""
        self.element_data = dict

    def add_parser_data(self, key, value):
        """This function adds a key-value pair to the element_data dictionary."""
        if key in self.parser_data.keys():
            if type(self.parser_data[key]) == list:
                self.parser_data[key].append(value)
            else:
                self.parser_data[key] = [self.parser_data[key], value]
        else:
            self.parser_data[key] = [value]
