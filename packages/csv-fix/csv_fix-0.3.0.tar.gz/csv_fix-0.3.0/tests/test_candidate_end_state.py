from io import StringIO
from csv_fix import CSVStateMachine, FILE_END

TEST_QUALIFIER = '"Field with ""quotes"""'
TEST_SEPARATOR = '"Field with , comma",Field without qualifier'
TEST_LINE_END = '"Field with line\nbreak",Another field'
TEST_FILE_END = '"Field unexpected end"'
TEST_OTHER = '"Wrong field with "quote" inside"'


class config:
    separator = ","
    qualifier = '"'
    trim = True
    skip_errors = False


def test_qualifier():
    output = StringIO()
    csv_machine = CSVStateMachine(config, output)
    csv_machine.feed(TEST_QUALIFIER)
    csv_machine.feed(FILE_END)
    assert output.getvalue() == '"Field with ""quotes"""\n'


def test_separator():
    output = StringIO()
    csv_machine = CSVStateMachine(config, output)
    csv_machine.feed(TEST_SEPARATOR)
    csv_machine.feed(FILE_END)
    assert output.getvalue() == '"Field with , comma","Field without qualifier"\n'


def test_line_end():
    output = StringIO()
    csv_machine = CSVStateMachine(config, output)
    csv_machine.feed(TEST_LINE_END)
    csv_machine.feed(FILE_END)
    assert output.getvalue() == '"Field with line\nbreak","Another field"\n'


def test_file_end():
    output = StringIO()
    csv_machine = CSVStateMachine(config, output)
    csv_machine.feed(TEST_FILE_END)
    csv_machine.feed(FILE_END)
    assert output.getvalue() == '"Field unexpected end"\n'


def test_other():
    output = StringIO()
    csv_machine = CSVStateMachine(config, output)
    csv_machine.feed(TEST_OTHER)
    csv_machine.feed(FILE_END)
    assert output.getvalue() == '"Wrong field with ""quote"" inside"\n'
