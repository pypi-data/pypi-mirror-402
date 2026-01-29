from io import StringIO
from csv_fix import CSVStateMachine, FILE_END

TEST_TRIM = ' red,	yellow,green ,"red	"'


class config:
    separator = ","
    qualifier = '"'
    trim = True
    skip_errors = False


def test_trim_handling():
    output = StringIO()
    csv_machine = CSVStateMachine(config, output)
    csv_machine.feed(TEST_TRIM)
    csv_machine.feed(FILE_END)
    assert output.getvalue() == '"red","yellow","green","red"\n'


def test_no_trim_handling():
    config.trim = False
    output = StringIO()
    csv_machine = CSVStateMachine(config, output)
    csv_machine.feed(TEST_TRIM)
    csv_machine.feed(FILE_END)
    assert output.getvalue() == '" red","	yellow","green ","red	"\n'
