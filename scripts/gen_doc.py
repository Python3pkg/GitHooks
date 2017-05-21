"""Generate piece of documentation based on checkers_spec."""
from collections import namedtuple
from string import Template
from inspect import getdoc
from docutils import core, nodes, writers, utils

from codechecker.checkers_spec import (FILE_CHECKERS,
                                             PROJECT_CHECKERS)
from codechecker.checkers_spec import (DEFAULTCONFIG,
                                             COMMAND_OPTIONS,
                                             RESULT_CREATOR)
from codechecker.checker.task import create_result_by_returncode


ConfigOptionDoc = namedtuple('ConfigOptionDoc', 'defaultvalue description')


def gen_doc():
    all_checkers_docdata = {}
    all_checkers = {}
    all_checkers.update(PROJECT_CHECKERS)
    all_checkers.update(FILE_CHECKERS)
    # 1. Collect checkers data
    for eachchecker_name in all_checkers:
        # 1.1 Collect checker base data
        eachchecker_spec = all_checkers[eachchecker_name]
        each_executable = eachchecker_name
        if COMMAND_OPTIONS in eachchecker_spec:
            eachchecker_commandoptions = eachchecker_spec[COMMAND_OPTIONS]
        else:
            eachchecker_commandoptions = {}
        if DEFAULTCONFIG in eachchecker_spec:
            eachchecker_defaultconfig = eachchecker_spec[DEFAULTCONFIG]
        else:
            eachchecker_defaultconfig = {}
        if RESULT_CREATOR in eachchecker_spec:
            result_creator = eachchecker_spec[RESULT_CREATOR]
        else:
            result_creator = create_result_by_returncode
        # 1.2 Prepare rst code of table which contains result statuses description
        eachchecker_statusses_table = extract_statuses_table(
            getdoc(result_creator)
        )
        eachchecker_doc = {
            'options': {},
            'statusses_table': eachchecker_statusses_table
        }
        # 1.3 For each checker build config option description
        for eachoption_name in eachchecker_defaultconfig:
            eachoption_default = eachchecker_defaultconfig[eachoption_name]
            if eachoption_default is None:
                eachoption_default = 'null'
            if eachoption_name == 'executable':
                eachoption_description = \
                    'Set {} executable path.'.format(eachchecker_name)
            elif eachoption_name in eachchecker_commandoptions:
                eachoption_command_pattern = \
                    Template(eachchecker_commandoptions[eachoption_name])
                eachoption_description = \
                    'If not null, pass {} to {} command.'.format(
                        eachoption_command_pattern.substitute(
                            value='<value>'
                        ),
                        each_executable
                    )
            else:
                eachoption_description = None
            eachoption_doc = ConfigOptionDoc(eachoption_default,
                                             eachoption_description)
            eachchecker_doc['options'][eachoption_name] = eachoption_doc
        all_checkers_docdata[eachchecker_name] = eachchecker_doc
    # 2. Use collected data to describe checkers in rst format
    for each_checkername in all_checkers_docdata:
        checker_spec = all_checkers_docdata[each_checkername]
        print(each_checkername)
        print(('#' * len(each_checkername)))
        print()
        print((checker_spec['statusses_table']))
        print()
        tablegen = RSTTableGenerator()
        tablegen.set_caption('Default config')
        tablegen.start_header() \
            .start_row() \
                .add_field('Option') \
                .add_field('Default')\
                .add_field('Description')
        tablegen.start_body()
        for eachoption_name in checker_spec['options']:
            each_option = checker_spec['options'][eachoption_name]
            tablegen.start_row() \
                .add_field(eachoption_name) \
                .add_field(each_option.defaultvalue) \
                .add_field(each_option.description)
        print((tablegen.generate_rst()))
        print()


class RSTTableGenerator:
    def __init__(self):
        self.columns_widths = []
        self.current_column_index = -1
        self.current_rowentries = []
        self.caption = None
        self.rows = []
        self.header_rows = []
        self.body_rows = []

    def set_caption(self, text):
        self.caption = text

    def start_header(self):
        self.rows = self.header_rows
        return self

    def start_body(self):
        self.rows = self.body_rows
        return self

    def start_row(self):
        self.current_column_index = -1
        self.current_rowentries = []
        self.rows.append(self.current_rowentries)
        return self

    def add_field(self, text):
        if text is None:
            text = ''
        text = str(text)
        self.current_column_index += 1
        if len(self.columns_widths)-1 < self.current_column_index:
            self.columns_widths.append(len(text))
        elif self.columns_widths[self.current_column_index] < len(text):
            self.columns_widths[self.current_column_index] = len(text)
        self.current_rowentries.append(text)
        return self

    def generate_rst(self):
        def center(text, width):
            return text.center(width)
        def ljust(text, width):
            return text.ljust(width)
        def indent_line(line, line_indent):
            return ''.join((line_indent, line))

        def update_lines_with_rows(lines, rows, row_indent, just=center):
            for each_row in rows:
                current_row_fields = []
                for width, each_entry in zip(self.columns_widths, each_row):
                    current_row_fields.append(just(each_entry, width))
                current_linecontents = ' '.join(current_row_fields)
                lines.append(indent_line(current_linecontents, row_indent))

        tablelines = []
        indentation = ''
        if self.caption:
            indentation = '   '
            tablelines.append('.. table:: {}'.format(self.caption))
            tablelines.append('')
        border_columns = []
        for each_width in self.columns_widths:
            border_columns.append('=' * each_width)
        border = indent_line(' '.join(border_columns), indentation)
        tablelines.append(border)
        if self.header_rows:
            update_lines_with_rows(tablelines, self.header_rows, indentation)
            tablelines.append(border)
        update_lines_with_rows(tablelines, self.body_rows, indentation, ljust)
        tablelines.append(border)
        return '\n'.join(tablelines)


class Writer(writers.Writer):
    def translate(self):
        self.visitor = visitor = Translator(self.document)
        self.document.walkabout(visitor)
        self.output = visitor.get_contents()


class Translator(nodes.NodeVisitor):

    def __init__(self, document):
        nodes.NodeVisitor.__init__(self, document)
        self.lines = []
        self.current_line = []
        self.is_topleft_entry = False
        self.tablegenerator = RSTTableGenerator()
        self.set_text = self.tablegenerator.set_caption

    def get_contents(self):
        return self.tablegenerator.generate_rst()

    def visit_Text(self, node):
        self.set_text(node.astext())

    def visit_thead(self, node):
        self.tablegenerator.start_header()
        self.set_text = self.tablegenerator.add_field

    def visit_row(self, node):
        self.tablegenerator.start_row()

    def visit_tbody(self, node):
        self.tablegenerator.start_body()

    def ignore(self, node):
        pass

    depart_tbody = ignore
    visit_document = ignore
    depart_document = ignore
    visit_table = ignore
    depart_table = ignore
    visit_title = ignore
    depart_title = ignore
    depart_Text = ignore
    depart_thead = ignore
    visit_tgroup = ignore
    depart_tgroup = ignore
    visit_colspec = ignore
    depart_colspec = ignore
    depart_row = ignore
    visit_entry = ignore
    depart_entry = ignore
    visit_paragraph = ignore
    depart_paragraph = ignore


def _find_element(doc_tree, element_type):
    for element in doc_tree:
        if isinstance(element, element_type):
            return element
    raise LookupError('Statuses table not found')


def extract_statuses_table(docstring):
    """Extract statuses table from passed docstring.

    Doc string should be written in rst. Should contain table with title "Result status".
    Result is rst code of first table which match to this description.
    """
    try:
        doc_tree = core.publish_doctree(docstring)
        table = _find_element(doc_tree, nodes.table)
        title = _find_element(table, nodes.title)
        if title[0] == 'Result status':
            document = utils.new_document('<string>')
            document += table
        else:
            raise LookupError('Statuses table not found')
    except IndexError:
        raise LookupError('Statuses table not found')
    return core.publish_from_doctree(document, writer=Writer()).decode()


if __name__ == '__main__':
    gen_doc()
