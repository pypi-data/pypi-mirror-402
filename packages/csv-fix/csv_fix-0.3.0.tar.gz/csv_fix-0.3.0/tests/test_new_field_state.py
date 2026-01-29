from io import StringIO
from csv_fix import CSVStateMachine, FILE_END

TEST_QUALIFIER = '"What\'s up?","He said ""Hello!"""'
TEST_SEPARATOR = ',"What\'s up?","He said ""Hello!"""'
TEST_OTHER = '"No qualifier here, just text"'
TEST_EMPTY = ""
TEST_EMPTY_2 = "\n"


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
    assert output.getvalue() == '"What\'s up?","He said ""Hello!"""\n'


def test_separator():
    output = StringIO()
    csv_machine = CSVStateMachine(config, output)
    csv_machine.feed(TEST_SEPARATOR)
    csv_machine.feed(FILE_END)
    assert output.getvalue() == '"","What\'s up?","He said ""Hello!"""\n'


def test_other():
    output = StringIO()
    csv_machine = CSVStateMachine(config, output)
    csv_machine.feed(TEST_OTHER)
    csv_machine.feed(FILE_END)
    assert output.getvalue() == '"No qualifier here, just text"\n'


def test_empty():
    output = StringIO()
    csv_machine = CSVStateMachine(config, output)
    csv_machine.feed(TEST_EMPTY)
    csv_machine.feed(FILE_END)
    assert output.getvalue() == ""


def test_empty_2():
    # breakpoint()
    output = StringIO()
    csv_machine = CSVStateMachine(config, output)
    csv_machine.feed(TEST_EMPTY_2)
    csv_machine.feed(FILE_END)
    assert output.getvalue() == ""
