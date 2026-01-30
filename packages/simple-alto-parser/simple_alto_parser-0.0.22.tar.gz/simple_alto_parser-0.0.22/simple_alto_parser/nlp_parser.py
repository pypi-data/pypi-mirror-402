import os
import webbrowser

from simple_alto_parser import BaseParser
from simple_alto_parser.base_parser import ParserMatch


class AltoNLPParser(BaseParser):

    model = None
    spacy_nlp = None
    last_parse_render = None

    def __init__(self, parser, model=None):
        super().__init__(parser)
        if model is None:
            model = "en_core_web_trf"
        self.model = model
        # self.spacy_nlp = spacy.load(self.model)
        self.last_parse_render = ''

    def parse(self, label=None):
        if type(label) is str:
            label = [label, ]

        html_render = ''
        file_id = 0
        for file in self.parser.get_alto_files():
            html_render += f'<h2>{file.file_path}</h2><br/>'
            line_id = 0
            for line in file.get_text_lines():
                doc = self.spacy_nlp(line.get_text())
                html_render += f'<strong><code>{line.get_text()}</code></strong><br/>'
                for word in doc.ents:
                    if label is None or word.label_ == label:
                        self.matches.append(NLPMatch(file_id, line_id, word))
                # html_render += displacy.render(doc, style="ent") + "<br><hr>"
                line_id += 1
            html_render += '<br/>'
            file_id += 1

        self.last_parse_render = html_render

    def print_matches(self):
        path = os.path.abspath('temp.html')
        url = 'file://' + path

        with open(path, 'w') as f:
            f.write(self.last_parse_render)
        webbrowser.open(url)


class NLPMatch(ParserMatch):

    def __init__(self, line_id, file_id, match):
        super().__init__(line_id, file_id, match)