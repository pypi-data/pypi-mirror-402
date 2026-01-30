# simple-alto-parser
This is a simple parser for ALTO XML files. It is designed to do three tasks separately:

## 1.	Extract the text from the ALTO XML file with the AltoTextParser class.
The simple alto parser facilitates the extraction of text from ALTO XML files, specifically tailored for retrieving OCR-recognized texts (e.g. through “Transkribus” https://readcoop.eu/de/transkribus/). Defined or manipulated by the user, the simple alto parser organizes the extracted text alongside its pertinent meta-information. Including for example the year of publication, page number, and pre-defined image sections etc. This structuring ensured that each part of the text is associated with its corresponding image and meta-information, facilitating precise retrieval and display at a later stage.

## 2.	Extract structured information from the text with different parsing methods.
There exist two fundamental parsing methods: 1. The extraction of relevant text segments through pattern recognition utilizing regular expressions (regex). 2. Matching based on predefined dictionaries. Whereby users can create their own dictionaries or utilize pre-existing ones (e.g. for country names etc.)
Text segments recognized through these methods can be systematically categorized within the same function and subsequently omitted from the parsing process. This framework facilitates a multi-stage parsing approach with a low entry threshold, wherein uncategorized text segments remain visible following each parsing iteration.
The simple alto parser also features a replace function, empowering the normalization of text segments during parsing. Simultaneously, irrelevant text segments can be removed from the structured text. A dedicated function for manual adjustments is also included, enabling modifications in cases where neither dictionary nor pattern matching proves sufficient.
Employing these parsing methods enables comprehensive structuring of the text while preserving readability and retaining all meta-information. To maintain transparency and traceability, the original text is consistently preserved, ensuring visibility of all manipulations performed.

## 3.	Export the structured text and information for further processing, analysis, publication etc.
The structured texts can be exported in various formats such as CSV, TSV, or JSON, with export parameters customizable to suit specific requirements. This allows tailored compilations of the structured texts. For example including all meta-information or solely the final structured texts. Allowing the data to be prepared directly for publication or for further analysis in the desired format and compilation.
Further JSON files are generated for the dictionaries created during the parsing process. These files can also be exported in a structured manner, facilitating publication or utilization elsewhere.


# Usage
```python
from simple_alto_parser import AltoFileParser, AltoPatternParser, AltoFileExporter

# Create a parser instance and supply your data directory
alto_parser = AltoFileParser('data')
alto_parser.parse()

# Find and categorize by patterns
pattern_parser = AltoPatternParser(alto_parser)
pattern_parser.find(r'(^.*\& Cie\.$)').categorize('company_name').remove()

# Other options are: look up in dictionaries, perform spacy NER

# Export the data
alto_exporter = AltoFileExporter(alto_parser)
alto_exporter.save_csv('output/alto_test.csv', delimiter=',')
```
