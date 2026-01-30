import csv
import json
import os


class AltoFileExporter:

    file_parser = None
    files = []

    def __init__(self, alto_file_parser):
        self.file_parser = alto_file_parser
        self.files = alto_file_parser.get_alto_files()

    def get_combined_csv_header(self):
        total_header = []
        for file in self.files:
            f_header = file.get_csv_header()
            for header in f_header:
                if header not in total_header:
                    total_header.append(header)
        print(total_header)
        return total_header

    def save_csv(self, file_name, **kwargs):
        self.assure_is_file(file_name)

        file_idx = 0
        csv_lines = [self.get_combined_csv_header(), ]
        for file in self.files:
            csv_lines.extend(file.get_csv_lines(add_header=False, static_header=csv_lines[0]))
            file_idx += 1

        csv_lines = self.reorder_csv_data(csv_lines)
        self.save_to_csv(file_name, csv_lines, **kwargs)

    def save_csvs(self, directory_name, **kwargs):
        self.assure_is_dir(directory_name)

        for file in self.files:
            if file.has_lines():
                csv_lines = file.get_csv_lines(add_header=True)
                file_name = os.path.join(directory_name, file.get_file_name(ftype='csv'))
                self.save_to_csv(file_name, csv_lines, **kwargs)
            else:
                pass

    def save_json(self, file_name):
        self.assure_is_file(file_name)

        json_objects = []
        for file in self.files:
            if self.file_parser.get_config_value('export', 'json', 'print_files', default=False):
                json_objects.append(file.get_standalone_json_object())
            else:
                json_objects.extend(file.get_json_objects())

        with open(file_name, 'w', encoding='utf-8') as outfile:
            json.dump(json_objects, outfile, indent=4, sort_keys=True)

    def save_jsons(self, directory_name):
        self.assure_is_dir(directory_name)

        for file in self.files:
            if file.has_lines():
                json_objects = file.get_json_objects()
                file_name = os.path.join(directory_name, file.get_file_name(ftype='json'))

                with open(file_name, 'w', encoding='utf-8') as f:
                    json.dump(json_objects, f, indent=4, sort_keys=True)
            else:
                pass

    @staticmethod
    def assure_is_file(file_path):
        """Assure that the given path is a file."""
        if not os.path.exists(file_path):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            return

        if not os.path.isfile(file_path):
            raise ValueError("The given path is not a file.")

    @staticmethod
    def assure_is_dir(file_path):
        """Assure that the given path is a directory."""

        if not os.path.exists(file_path):
            os.makedirs(file_path)

        if not os.path.isdir(file_path):
            raise ValueError("The given path is not a directory.")

    @staticmethod
    def save_to_csv(file_path, csv_lines, **kwargs):
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            csv_writer = csv.writer(f, delimiter=kwargs.get('delimiter', '\t'),
                                    quotechar=kwargs.get('quotechar', '"'),
                                    quoting=kwargs.get('quoting', csv.QUOTE_MINIMAL))
            for line in csv_lines:
                csv_writer.writerow(line)

    def reorder_csv_data(self, csv_lines):
        reorder_config = None
        try:
            reorder_config = self.file_parser.parser_config['export']['csv']['output_configuration']
        except KeyError:
            return csv_lines

        if reorder_config is not None:
            original_header = csv_lines[0]
            reordered_lines = []
            for line in csv_lines[1:]:
                reordered_line = []
                for key in reorder_config:
                    try:
                        reordered_line.append(line[original_header.index(key)])
                    except ValueError as e:
                        reordered_line.append('')
                reordered_lines.append(reordered_line)

            new_header = []
            for key in reorder_config:
                new_header.append(reorder_config[key])

            return [new_header] + reordered_lines
        else:
            return csv_lines
