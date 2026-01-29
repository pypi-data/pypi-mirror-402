from io import StringIO
from csv_fix import CSVStateMachine, FILE_END

TEST_QUALIFIER = '"Field with ""quotes""","FIELD with \n"quotes"!\n"'
TEST_FILE_END = '"Field unexpected end'


class config:
    separator = ","
    qualifier = '"'
    trim = False
    skip_errors = False


def test_qualifier():
    output = StringIO()
    csv_machine = CSVStateMachine(config, output)
    csv_machine.feed(TEST_QUALIFIER)
    csv_machine.feed(FILE_END)
    assert output.getvalue() == '"Field with ""quotes""","FIELD with \n""quotes""!\n"\n'


def test_file_end():
    output = StringIO()
    csv_machine = CSVStateMachine(config, output)
    csv_machine.feed(TEST_FILE_END)
    csv_machine.feed(FILE_END)
    assert output.getvalue() == '"Field unexpected end"\n'
