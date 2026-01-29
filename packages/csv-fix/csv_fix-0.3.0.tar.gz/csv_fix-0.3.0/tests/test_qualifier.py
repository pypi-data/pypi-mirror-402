from io import StringIO
from csv_fix import CSVStateMachine, FILE_END

TEST_QUALIFIER = "'What's up?','He said ''Hello!'''"


class config:
    separator = ","
    qualifier = "'"
    trim = True
    skip_errors = False


def test_qualifier_handling():
    output = StringIO()
    csv_machine = CSVStateMachine(config, output)
    csv_machine.feed(TEST_QUALIFIER)
    csv_machine.feed(FILE_END)
    assert output.getvalue() == "'What''s up?','He said ''Hello!'''\n"
