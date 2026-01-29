from io import StringIO
from csv_fix import CSVStateMachine, FILE_END

TEST_SEPARATER = '"hello"|"This is a test"|"This should be good.|""|""'


class config:
    separator = "|"
    qualifier = '"'
    trim = True
    skip_errors = False


def test_separater_handling():
    output = StringIO()
    csv_machine = CSVStateMachine(config, output)
    csv_machine.feed(TEST_SEPARATER)
    csv_machine.feed(FILE_END)
    assert (
        output.getvalue() == '"hello"|"This is a test"|"This should be good.|""|"""\n'
    )
