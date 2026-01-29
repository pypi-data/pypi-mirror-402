from io import StringIO
from csv_fix import CSVStateMachine, FILE_END

TEST_QUALIFIER = 'Field with "quotes"'
TEST_SEPARATOR = "Field with,comma,Field without qualifier"
TEST_LINE_END = '"Field with line\r\nbreak",Another field'


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
    assert output.getvalue() == '"Field with","comma","Field without qualifier"\n'


def test_line_end():
    output = StringIO()
    csv_machine = CSVStateMachine(config, output)
    csv_machine.feed(TEST_LINE_END)
    csv_machine.feed(FILE_END)
    assert output.getvalue() == '"Field with line\nbreak","Another field"\n'
