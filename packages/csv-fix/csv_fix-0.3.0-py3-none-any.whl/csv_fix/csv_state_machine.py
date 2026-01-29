#!/usr/bin/env python
from logging import getLogger
from csv_fix.states import States

FILE_END = f"{0x00}"


class CSVStateMachine:
    def __init__(self, config, output):
        self.separator = config.separator
        self.qualifier = config.qualifier
        self.trim = config.trim
        self.skip_errors = config.skip_errors
        # self.timezone = config.timezone
        self.output = output
        self.state = States.NEW_FIELD
        # position of character done recognizing
        self.field = []
        self.fields = []
        self.logger = getLogger(__name__)

    def feed(self, line):
        for _, ch in enumerate(line):
            if ch == "\r":
                continue
            if self.state == States.NEW_FIELD:
                if ch == self.qualifier:
                    self.state = States.FIELD_IN_QUALIFIER
                elif ch == self.separator:
                    # State doesn't change, but it's the next field
                    self._push_field("")
                elif ch == "\n" or ch == FILE_END:
                    self._push_field("")
                    self._flush_fields()
                    self.state = States.NEW_FIELD
                else:
                    self.field.append(ch)
                    self.state = States.FIELD
                continue
            if self.state == States.FIELD:
                if ch == self.separator:
                    self._push_field("".join(self.field))
                    self.state = States.NEW_FIELD
                elif ch == "\n" or ch == FILE_END:
                    self._push_field("".join(self.field))
                    self._flush_fields()
                    self.state = States.NEW_FIELD
                else:
                    self.field.append(ch)
                continue
            if self.state == States.FIELD_IN_QUALIFIER:
                if ch == self.qualifier:
                    self.field.append(ch)
                    self.state = States.CANDIDATE_FIELD_END
                elif ch == FILE_END:
                    self._push_field("".join(self.field))
                    self._flush_fields()
                    self.state = States.NEW_FIELD
                else:
                    self.field.append(ch)
                continue
            if self.state == States.CANDIDATE_FIELD_END:
                if ch == self.qualifier:
                    self.field.append(ch)
                    self.state = States.CANDIDATE_ESCAPE
                elif ch == self.separator:
                    self.field.pop()  # Remove the qualifier
                    self._push_field("".join(self.field))
                    self.state = States.NEW_FIELD
                elif ch == "\n" or ch == FILE_END:
                    self.field.pop()  # Remove the qualifier
                    self._push_field("".join(self.field))
                    self._flush_fields()
                    self.state = States.FIELD_IN_QUALIFIER
                else:
                    self.field.append(self.qualifier)
                    self.field.append(ch)
                    self.state = States.FIELD_IN_QUALIFIER
                continue
            if self.state == States.CANDIDATE_ESCAPE:
                if ch == FILE_END:
                    self._push_field("".join(self.field))
                    self._flush_fields()
                    self.state = States.NEW_FIELD
                elif ch == self.qualifier:
                    self.field.append(ch)
                    self.state = States.CANDIDATE_FIELD_END
                else:
                    self.field.append(ch)
                    self.state = States.FIELD_IN_QUALIFIER
                continue

    def _push_field(self, field):
        # TODO: handle time convertion
        if self.trim:
            field = field.strip()
        if self.state in [States.NEW_FIELD, States.FIELD]:
            # Escape qualifiers in unqualified fields
            field = field.replace(self.qualifier, f"{self.qualifier}{self.qualifier}")
        # Always quote unqualified fields because some systems in certain situations may misinterpret them.
        self.fields.append(f"{self.qualifier}{field}{self.qualifier}")
        self.field = []

    def _flush_fields(self):
        line = self.separator.join(self.fields)
        if line != '""':
            # Empty lines are usually unexpected, skip them
            self.output.write(line + "\n")
        self.fields = []

    def _detect_time(self):
        raise NotImplementedError
