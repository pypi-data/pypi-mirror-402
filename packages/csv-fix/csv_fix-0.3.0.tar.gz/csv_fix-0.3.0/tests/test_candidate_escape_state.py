from io import StringIO
from csv_fix import CSVStateMachine, FILE_END


TEST_QUALIFIER = '"Field with ""quotes"""'
TEST_OTHER = '"Field with ""quotes""!"'
TEST_LINE_END = '"Field with ""quotes""\n'


class config:
    separator = ","
    qualifier = '"'
    trim = False
    skip_errors = False


def test_candidate_escape_state():
    output = StringIO()
    csv_machine = CSVStateMachine(config, output)
    csv_machine.feed(TEST_QUALIFIER)
    csv_machine.feed(FILE_END)
    assert output.getvalue() == '"Field with ""quotes"""\n'


def test_candidate_escape_state_other():
    output = StringIO()
    csv_machine = CSVStateMachine(config, output)
    csv_machine.feed(TEST_OTHER)
    csv_machine.feed(FILE_END)
    assert output.getvalue() == '"Field with ""quotes""!"\n'


def test_candidate_escape_state_line_end():
    output = StringIO()
    csv_machine = CSVStateMachine(config, output)
    csv_machine.feed(TEST_LINE_END)
    csv_machine.feed(FILE_END)
    assert output.getvalue() == '"Field with ""quotes""\n"\n'
