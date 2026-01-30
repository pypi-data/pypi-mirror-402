"""This module contains the class AltoTextParser, which is used to parse text from ALTO files."""
import logging
import os
import re
import sys
import xml.etree.ElementTree as ETree
from abc import ABC, abstractmethod

from simple_alto_parser.alto_file import AltoFile, AltoFileElement
from simple_alto_parser.utils import get_logger


class AbstractFileParser(ABC):
    """This class is used to parse text from ALTO files. It stores the files in a list of AltoFile objects."""

    logger = None
    """The logger of the class."""

    files = []

    def __init__(self, directory_path=None, parser_config=None):
        """The constructor of the class."""

        self.parser_config = {
            'line_type': 'TextLine',
            'file_ending': '.xml',
            'export': {                            # Options for exporting the parsed data.
                'csv': {
                    'print_manipulated': False,      # Print the manipulated text to the csv.
                    'print_filename': False,         # Print the filename to the csv.
                    'print_attributes': True,       # Print the attributes to the csv.
                    'print_parser_results': True,   # Print the parser results to the csv.
                    'print_file_meta_data': False,   # Print the file meta data to the csv.
                    'output_configuration': {}
                }
            },
            'batches': [],
            'logging': {
                'level': logging.DEBUG,
            }
        }

        if parser_config:
            self.parser_config.update(parser_config)

        self.logger = get_logger(self.parser_config['logging']['level'])

        self.logger.debug("Parser config: %s", self.parser_config)

        if directory_path:
            self.files = []
            self.add_files(directory_path, self.get_config_value('file_ending'))
        else:
            self.files = []

        if 'meta_data' in self.parser_config:
            for key, value in self.parser_config['meta_data'].items():
                self.add_meta_data_to_files(key, value)

        if 'file_name_structure' in self.parser_config:
            for file in self.files:
                match = re.search(self.parser_config['file_name_structure']["pattern"],
                                  os.path.basename(file.file_path))

                if match and len(match.groups()) == len(self.parser_config['file_name_structure']['value_names']):
                    idx = 1
                    for value_name in self.parser_config['file_name_structure']['value_names']:
                        file.add_file_meta_data(value_name, match.group(idx))
                        idx += 1
                else:
                    self.logger.warning("The file name structure does not match the file name of the file '%s'.",
                                        os.path.basename(file.file_path))

    def add_files(self, directory_path, file_ending='.xml'):
        """Add all files with the given file ending in the given directory to the list of files to be parsed."""

        if not os.path.isdir(directory_path):
            self.logger.error("The given path is not a directory.")
            sys.exit()

        sorting_config = self.get_config_value('sort_files', default={})
        if sorting_config.get('enabled', False):
            sort_key = sorting_config.get('sort_key', 'filename')
            reverse = sorting_config.get('reverse', False)

            if sort_key == 'filename':
                files = sorted(os.listdir(directory_path), key=lambda x: x, reverse=reverse)
            elif sort_key == 'date':
                files = sorted(
                    os.listdir(directory_path),
                    key=lambda x: os.path.getmtime(os.path.join(directory_path, x)),
                    reverse=reverse
                )
            elif sort_key == 'size':
                files = sorted(
                    os.listdir(directory_path),
                    key=lambda x: os.path.getsize(os.path.join(directory_path, x)),
                    reverse=reverse
                )
            else:
                # Default sorting by filename if an unknown sort_key is provided
                files = sorted(os.listdir(directory_path), key=lambda x: x, reverse=reverse)
        else: # No sorting configured
            files = os.listdir(directory_path)

        for file in files:
            if file.endswith(file_ending):
                self.add_file(os.path.join(directory_path, file))
        self.logger.info("Added %s files to the list of files to be parsed.", len(self.files))

    def add_file(self, file_path):
        """Add the given file to the list of files to be parsed."""

        alto_file = AltoFile(file_path, self)
        self.files.append(alto_file)
        self.logger.debug("Added file '%s' to the list of files to be parsed.", file_path)

    def parse(self):
        """Parse the text from all files in the list of files."""

        for alto_file in self.files:
            self.parse_file(alto_file)
        self.logger.info(f"Parsed text from {len(self.files)} files.")

    @abstractmethod
    def parse_file(self, alto_file):
        pass

    def _xml_parse_file(self, file_path, namespace):
        """ This function uses the Etree xml parser to parse an alto file. It should not be called from outside this
            class. The parse_file() method calls it."""

        try:
            xml_tree = ETree.parse(file_path)
        except ETree.ParseError as error:
            raise error

        if 'http://' in str(xml_tree.getroot().tag.split('}')[0].strip('{')):
            xmlns = xml_tree.getroot().tag.split('}')[0].strip('{')
        else:
            try:
                ns = xml_tree.getroot().attrib
                xmlns = str(ns).split(' ')[1].strip('}').strip("'")
            except IndexError as error:
                xmlns = ''
                self.logger.error(f"The given file '{file_path}' is not a valid alto file. {error}")
                sys.exit()

        if xmlns not in namespace.values():
            self.logger.error(f"The given file '{file_path}' is not a valid alto file.")
            sys.exit()

        return xml_tree, xmlns

    def get_alto_files(self):
        """Return the list of AltoFile objects."""
        return self.files

    @staticmethod
    def sanitize_text(text):
        """This function removes all line breaks, tabs and carriage returns from the text and removes leading and
        trailing whitespaces."""
        return text.replace("\n", "").replace("\r", "").replace("\t", "").replace("\ufeff", '').strip()

    def extract_meta_from_filenames(self, parameter_name, parameter_pattern):
        """Extract the given parameter from the filenames of the files in the list of files. This means that filenames
        that match the given pattern are searched for the given parameter. If the parameter is found, it is added to
        the metadata of the file."""

        for file in self.files:
            filename = os.path.basename(file.file_path)
            match = re.search(parameter_pattern, filename)
            if match:
                file.add_file_meta_data(parameter_name, match.group(1))

    def add_meta_data_to_files(self, parameter_name, static_value):
        """Add the given parameter with the given value to the metadata of all files in the list of files."""

        for file in self.files:
            file.add_file_meta_data(parameter_name, static_value)

    def get_config_value(self, *args, default=None):
        """Return the value of the given parameter from the parser config."""
        data = self.parser_config
        for key in args:
            if isinstance(data, dict):
                data = data.get(key, default)
            elif isinstance(data, (list, tuple)) and isinstance(key, int):
                try:
                    data = data[key]
                except IndexError:
                    return default
            else:
                return default
        return data

    def get_attributes(self, element, attributes_to_get, convert_attr_to_upper=False):
        """This function reads the attributes of the element and stores them in the element_data dictionary."""
        attrs = {}
        for attribute in attributes_to_get:
            try:
                att = attribute
                if convert_attr_to_upper:
                    att = attribute.upper()
                attrs[attribute] = element.attrib.get(att)
            except KeyError:
                # The attribute is not in the element. This is not a problem.
                self.logger.debug(f"The attribute '%s' is not in the element.", attribute)
                pass
        return attrs


class AltoFileParser(AbstractFileParser):

    LINE_TYPES = ['TextLine', 'TextBlock']

    attributes_to_get = ["id", "baseline", "hpos", "vpos", "width", "height"]
    """A list of the attributes that should be stored in the element_data dictionary."""

    def __init__(self, directory_path=None, parser_config=None):
        """The constructor of the class."""
        super().__init__(directory_path, parser_config)

    def parse_file(self, alto_file):
        """This function parses the alto file and stores the data in the class."""
        namespace = {'alto-1': 'http://schema.ccs-gmbh.com/ALTO',
                     'alto-2': 'http://www.loc.gov/standards/alto/ns-v2#',
                     'alto-3': 'http://www.loc.gov/standards/alto/ns-v3#',
                     'alto-4': 'http://www.loc.gov/standards/alto/ns-v4#'}

        xml_tree, xmlns = self._xml_parse_file(alto_file.file_path, namespace)
        if xml_tree is None:
            raise ValueError("The given file is not a valid xml file.")

        for text_block in xml_tree.iterfind('.//{%s}TextBlock' % xmlns):
            block_content = ""
            for text_line in text_block.iterfind('.//{%s}TextLine' % xmlns):
                line_content = ""
                for text_bit in text_line.findall('{%s}String' % xmlns):
                    bit_content = text_bit.attrib.get('CONTENT')
                    line_content += " " + bit_content

                if self.get_config_value('line_type') == 'TextLine':
                    element = AltoFileElement(self.sanitize_text(line_content))
                    element.set_attributes(self.get_attributes(text_line, self.attributes_to_get,
                                                               convert_attr_to_upper=True))
                    alto_file.file_elements.append(element)

                block_content += " " + line_content

            if self.get_config_value('line_type') == 'TextBlock':
                element = AltoFileElement(self.sanitize_text(block_content))
                element.set_attributes(self.get_attributes(text_block, self.attributes_to_get,
                                                           convert_attr_to_upper=True))
                alto_file.file_elements.append(element)


class PageFileParser(AbstractFileParser):

    LINE_TYPES = ['TextLine', 'TextRegion']

    attributes_to_get = ["id", "custom"]
    """A list of the attributes that should be stored in the element_data dictionary."""

    ignored_keys = ['readingOrder']
    """A list of keys that should be ignored when parsing the custom tags."""

    def __init__(self, directory_path=None, parser_config=None):
        """The constructor of the class."""
        super().__init__(directory_path, parser_config)

    def parse_file(self, alto_file):
        """Parses a Transkribus Page XML file."""
        namespace = {'page': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}
        xml_tree, xmlns = self._xml_parse_file(alto_file.file_path, namespace)

        if xml_tree is None:
            raise ValueError("The given file is not a valid xml file.")

        # Extract Metadata
        self.parse_metadata(xml_tree, xmlns, alto_file)

        page_block = xml_tree.find('.//{%s}Page' % xmlns)

        for text_block in page_block.iterfind('.//{%s}TextRegion' % xmlns):
            block_content = ""
            block_custom_tags = []
            block_text_lines = []
            for text_line in text_block.iterfind('.//{%s}TextLine' % xmlns):
                line_content = ""

                line_custom_tag = text_line.attrib.get('custom')
                block_custom_tags.append(line_custom_tag)

                for text_bit in text_line.findall('{%s}TextEquiv' % xmlns):
                    bit_content = text_bit.find('{%s}Unicode' % xmlns).text
                    if bit_content is not None and bit_content.strip() != "":
                        line_content += " " + bit_content
                    else:
                        self.logger.debug(f"The text content of the line is empty. ({alto_file.file_path})")

                # LINE TYPE: TextLine
                if self.get_config_value('line_type') == 'TextLine':
                    element = AltoFileElement(self.sanitize_text(line_content))
                    coords = text_block.find('{%s}Coords' % xmlns).attrib.get('points')
                    coords = self.clean_coords(coords)
                    bbox = self.get_bbox_from_coords(coords)
                    element.set_attribute('coords', coords)
                    element.set_attribute('bbox', bbox)
                    page_iiif_id = alto_file.file_meta_data['transkribus_iiif_id']
                    anno_iiif_url = f"https://files.transkribus.eu/iiif/2/{page_iiif_id}/{','.join([str(i) for i in bbox])}/full/0/default.jpg"
                    element.set_attribute('iiif_url', anno_iiif_url)
                    collection_id = self.get_config_value('static_info', 'transkribus_collection',
                                                          default='no_collection')
                    element.set_attribute('composed_id',
                                          f"{collection_id}-{alto_file.file_meta_data['docId']}-{element.get_attribute('id')}")
                    element.set_attributes(self.get_attributes(text_block, self.attributes_to_get))
                    alto_file.file_elements.append(element)

                block_content += " " + line_content
                block_text_lines.append(line_content)

            # LINE TYPE: TextRegion
            if self.get_config_value('line_type') == 'TextRegion':
                element = AltoFileElement(self.sanitize_text(block_content))

                coords = text_block.find('{%s}Coords' % xmlns).attrib.get('points')
                coords = self.clean_coords(coords)
                bbox = self.get_bbox_from_coords(coords)
                custom_structure = self.parse_custom_tag(text_block.attrib.get('custom'))
                custom_structure = self.remove_unused_keys(custom_structure)
                parsed_tags = self.extract_tags_of_region(block_custom_tags, block_text_lines, alto_file)

                element.set_attributes(self.get_attributes(text_block, self.attributes_to_get))
                element.set_attribute('custom_structure', custom_structure)
                element.set_attribute('coords', coords)
                element.set_attribute('bbox', bbox)
                element.set_attribute('custom_list', block_custom_tags)
                element.set_attribute('text_lines', block_text_lines)
                element.set_attribute('custom_list_structure', parsed_tags)

                # Generate the IIIF URL for this region
                page_iiif_id = alto_file.file_meta_data['transkribus_iiif_id']
                anno_iiif_url = f"https://files.transkribus.eu/iiif/2/{page_iiif_id}/{','.join([str(i) for i in bbox])}/full/0/default.jpg"
                element.set_attribute('iiif_url', anno_iiif_url)

                # Get the reading order of the region
                match = re.search(r"index:(\d+);", element.get_attribute('custom'))
                if match:
                    index = int(match.group(1))
                else:
                    self.logger.warning(f"The reading order of the region could not be extracted. ({alto_file.file_path})")
                    index = 0

                # Create an id for the region
                collection_id = self.get_config_value('static_info', 'transkribus_collection', default='')
                element.set_attribute('composed_id',
                                     f"{collection_id}-{alto_file.file_meta_data['docId']}-{element.get_attribute('id')}-{index}")

                alto_file.file_elements.append(element)

    @staticmethod
    def get_bbox_from_coords(coords):
        # Split the string into individual points
        point_pairs = coords.split()

        # Process each pair of points
        x_coords = []
        y_coords = []
        for pair in point_pairs:
            x, y = pair.split(',')
            x_coords.append(int(float(x)))
            y_coords.append(int(float(y)))

        min_x = min(x_coords)
        min_y = min(y_coords)
        max_x = max(x_coords)
        max_y = max(y_coords)

        width = max_x - min_x
        height = max_y - min_y

        return [min_x, min_y, width, height]

    @staticmethod
    def clean_coords(coords):
        # Split the string into individual points
        point_pairs = coords.split()

        # Process each pair of points
        integer_points = []
        for pair in point_pairs:
            x, y = pair.split(',')
            x_int = int(float(x))
            y_int = int(float(y))
            integer_points.append(f"{x_int},{y_int}")

        # Join the processed points back into a string
        integer_points_str = " ".join(integer_points)

        return integer_points_str

    def parse_metadata(self, xml_tree, xmlns, alto_file):
        """This function extracts the metadata from the xml tree and adds it to the file metadata."""
        metadata_block = xml_tree.find('.//{%s}Metadata' % xmlns)
        if metadata_block is not None:
            creator = metadata_block.find('{%s}Creator' % xmlns)
            if creator is not None:
                creator = creator.text
            else:
                self.logger.warning(f"The creator is not set. ({alto_file.file_path})")

            created = metadata_block.find('{%s}Created' % xmlns)
            if created is not None:
                created = created.text
            else:
                self.logger.warning(f"The creation date is not set. ({alto_file.file_path})")

            last_change = metadata_block.find('{%s}LastChange' % xmlns)
            if last_change is not None:
                last_change = last_change.text
            else:
                self.logger.warning(f"The last change date is not set. ({alto_file.file_path})")

            alto_file.add_file_meta_data('creator', creator)
            alto_file.add_file_meta_data('created', created)
            alto_file.add_file_meta_data('last_change', last_change)

            # Now we need to extract the metadata from the TranskribusMetadata block
            tk_metadata_block = metadata_block.find('{%s}TranskribusMetadata' % xmlns)
            if tk_metadata_block is not None:
                # Extract the properties. They might or might not be there.
                for t_property in tk_metadata_block.iterfind('.//{%s}Property' % xmlns):
                    key = t_property.attrib.get('key')
                    value = t_property.attrib.get('value')
                    alto_file.add_file_meta_data(key, value)

                    # Handle special keys
                    self.handle_special_metadata_key(key, value, alto_file)

                for attrib in tk_metadata_block.attrib:
                    alto_file.add_file_meta_data(attrib, tk_metadata_block.attrib[attrib])

                    # Handle special keys
                    self.handle_special_metadata_key(attrib, tk_metadata_block.attrib[attrib], alto_file)
            else:
                self.logger.warning(f"The TK-metadata block is empty. ({alto_file.file_path})")
        else:
            self.logger.warning(f"The metadata block is empty. ({alto_file.file_path})")

    @staticmethod
    def handle_special_metadata_key(key, value, alto_file):
        """This function handles special keys that need to be processed in a special way.
        The Transkribus TranskribusMetadata block contains some metadate which can be used to derive
        additional information. This function processes these keys and adds the derived information to the file metadata."""

        if key == 'status':
            alto_file.add_file_meta_data('file_status', value)
        if key == 'imgUrl':
            id_part = value.split('id=')[-1]
            clean_id = id_part.split('&')[0]
            alto_file.add_file_meta_data('transkribus_iiif_id', clean_id)
            alto_file.add_file_meta_data('transkribus_iiif_url',
                                         f"https://files.transkribus.eu/iiif/2/{clean_id}/full/full/0/default.jpg")

    def extract_tags_of_region(self, input_list, text_lines, alto_file):
        """Extract tags from region with line tracking and position preservation.

        This function extracts tags from PAGE XML custom attributes and preserves:
        - offset: Character position within the line
        - length: Length of the tagged text
        - line_index: Which line in the region (0-based)
        - line_text: The actual text of that line

        Args:
            input_list: List of custom attribute strings from TextLine elements
            text_lines: List of Unicode text from TextLine elements
            alto_file: The AltoFile object being processed

        Returns:
            List of tag dicts with preserved positional information
        """
        parsed_data = []

        # Parse each line's custom tags and add line tracking
        for line_idx, item in enumerate(input_list):
            # Creates a dict from the custom tag string
            item_dict = self.parse_custom_tag(item)

            # Remove the unused keys from the dict
            item_dict = self.remove_unused_keys(item_dict)

            # Extract the text from the text lines and add it to the data
            item_dict = self.add_text_to_tags(item_dict, text_lines[line_idx])

            # Add line index to each tag so we know which line it came from
            for tag_dict_item in item_dict.values():
                if isinstance(tag_dict_item, dict):
                    tag_dict_item['line_index'] = line_idx
                elif isinstance(tag_dict_item, list):
                    for tag in tag_dict_item:
                        tag['line_index'] = line_idx

            parsed_data.append(item_dict)

        preliminary_tags_of_region = []
        for item in parsed_data:
            for tag_name in item:
                if isinstance(item[tag_name], dict):
                    data = {"type": self.get_tag_type(tag_name)}
                    data.update(item[tag_name])
                    preliminary_tags_of_region.append(data)
                if isinstance(item[tag_name], list):
                    for tag in item[tag_name]:
                        data = {"type": self.get_tag_type(tag_name)}
                        data.update(tag)
                        preliminary_tags_of_region.append(data)

        # This is a flat list of tags. Now we need to merge the tags that are continued over several lines.
        current_tag = None
        tags = []
        for tag in preliminary_tags_of_region:
            # Keep offset and length - they're essential for positioning!
            # Only remove line_length (internal calculation artifact)
            if "line_length" in tag:
                del tag["line_length"]

            # A new tag starts
            if "starts_tag" in tag:
                current_tag = tag
            # An open tag is continued
            elif "continues_tag" in tag:
                if current_tag:
                    current_tag["text"] += " " + tag["text"]
                else:
                    current_tag = tag
                    self.logger.debug(f"A full-line-tag is continued but no tag is open. Started new Tag {tag} ({alto_file.file_path})")
            # An open tag is ended
            elif "ends_tag" in tag:
                if current_tag:
                    current_tag["text"] += " " + tag["text"]
                    if "ends_tag" in current_tag:
                        del current_tag["ends_tag"]
                    tags.append(current_tag)
                    current_tag = None
                else:
                    self.logger.warning(f"A tag is ended but no tag is open. {tag} {alto_file.file_path}")
            else:
                tags.append(tag)

        return tags

    def add_text_to_tags(self, item_dict, text_line):
        """Extract text from line and add line context to each tag.

        Args:
            item_dict: Dictionary of tags from one line
            text_line: The Unicode text of that line

        Returns:
            Updated item_dict with 'line_text' added to each tag
        """
        for d_item in item_dict:
            if isinstance(item_dict[d_item], dict):
                item_dict[d_item] = self.extract_from_textline(item_dict[d_item], text_line)
                # Add the full line text for context
                item_dict[d_item]['line_text'] = text_line
            else:
                new_items = []
                for item in item_dict[d_item]:
                    item = self.extract_from_textline(item, text_line)
                    # Add the full line text for context
                    item['line_text'] = text_line
                    new_items.append(item)
                item_dict[d_item] = new_items

        return item_dict

    def extract_from_textline(self, item, text_line):
        if "length" in item and "offset" in item:
            length = item["length"] = int(item["length"])
            offset = item["offset"] = int(item["offset"])

            item["text"] = text_line[offset+1:offset+length+1]
            item["line_length"] = len(text_line)

            line_starter = (offset == 0)
            line_ender = (offset + length + 1 == len(text_line))
            continued = ("continued" in item)

            if continued:
                del item["continued"]
                if line_ender and not line_starter:
                    item["starts_tag"] = True
                elif line_starter and line_ender:
                    item["continues_tag"] = True
                elif line_starter and not line_ender:
                    item["ends_tag"] = True
                else:
                    self.logger.warning("The tag is continued over several lines, "
                                        "but the line does not start or end the tag.")

        return item

    def remove_unused_keys(self, item_dict):
        """Delete all the unused keys from the extracted data"""

        for key in self.ignored_keys:
            if key in item_dict:
                del item_dict[key]
        return item_dict

    def parse_custom_tag(self, custom_tag):
        # Regex to find key-value pairs within curly braces
        pattern = r'(\w+)\s*\{([^}]*)\}'

        # Find all pattern matches in the current string
        matches = re.findall(pattern, custom_tag)

        # Dictionary to store data for the current string
        item_dict = {}

        for match in matches:
            key, values = match
            # Further split the values by semicolon
            value_dict = {}
            for value in values.split(';'):
                if value.strip():
                    k, v = value.strip().split(':')
                    value_dict[k.strip()] = v.strip()

            # Check if the key already exists, indicating multiple entries of the same type
            if key in item_dict:
                # If already a list, append to it
                if isinstance(item_dict[key], list):
                    item_dict[key].append(value_dict)
                else:
                    # Make it a list with previous and new entry
                    item_dict[key] = [item_dict[key], value_dict]
            else:
                item_dict[key] = value_dict

        return item_dict

    def get_tag_type(self, tag_name):
        return tag_name.lower()
