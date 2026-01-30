import csv
import json


class AltoDictionaryCreator:

    @staticmethod
    def from_file(input_filename, output_filename, type='undefined'):
        with open(input_filename, encoding='utf-8') as f:
            entries = []
            for line in f:
                entry = {
                    "label": line.strip(),
                    "variants": [line.strip()],
                    "type": type
                }
                entries.append(entry)

        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(json.dumps(entries, indent=4, sort_keys=True))

    def from_geonames(self, csv_file_path):
        # Open Tsv
        with open(csv_file_path, encoding='utf-8') as f:
            csv_reader = csv.reader(f, delimiter='\t')
            row_id = 0
            for row in csv_reader:
                if row[6] == 'P':
                    print(
                        row[0],  # geonames_id
                        row[1],  # name
                        row[2],  # asciiname
                        row[3],  # alternatenames
                        row[4],  # latitude
                        row[5],  # longitude
                        row[6],  # feature_class
                        row[7],  # feature_code
                        row[8],  # country_code
                        row[9],  # cc2
                        row[10],  # admin1_code
                        row[11],  # admin2_code
                        row[12],  # admin3_code
                        row[13],  # admin4_code
                        row[14],  # population
                        row[15],  # elevation
                        row[16],  # dem
                        row[17],  # timezone
                        row[18]  # modification_date
                    )


                row_id += 1
                if row_id > 20:
                    break

# from_file('../assets/dicts/titles.csv', type="title")

