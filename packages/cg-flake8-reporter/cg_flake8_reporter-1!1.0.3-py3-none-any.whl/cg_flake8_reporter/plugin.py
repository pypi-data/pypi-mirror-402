"""Implementation of CodeGrade's formatter for flake8 reporting directly to
AutoTest v2.
"""

import argparse
import json
import os
import sys
import typing as t
from fractions import Fraction
from pathlib import Path

import flake8

# The message size limit for SQS messages is 256KB. We set it a little bit less
# here than 256KB to leave enough space for the wrapping message. Large
# structured output messages are stored on S3 so we don't have to stay with the
# WebSocket server message size limit of 128KB for these messages.
MESSAGE_SIZE_LIMIT = 250_000

# The set of known severity levels for CodeGrade's formatter.
# We use this to provide the user with a nice error message when a default severity
# is given.
KNOWN_SEVERITIES = {'error', 'warning', 'info', 'unknown'}


def json_dumps(obj: object) -> str:
    """Dump an object to JSON without any extra formatting."""
    # Make sure only ASCII characters are used so that the string length as
    # python's `len` function reports it is equal to the string's byte length.
    # Do not insert spaces after each separator.
    return json.dumps(obj, ensure_ascii=True, separators=(',', ':'))


class CustomFormatter(
    flake8.formatting.base.BaseFormatter  # type: ignore[misc]
):
    """
    Custom Formatter for flake8.
    Formats the errors/warnings as JSON objects.
    Also calculates a score based on severity of errors/warnings.
    """

    def __init__(self, options: argparse.Namespace) -> None:
        """
        Initialize buffer for comments, score, and points deducted for each severity level.
        """
        super().__init__(options)
        self._buffer: t.MutableMapping[str, t.Any] = {
            'tag': 'comments',
            'comments': {},
        }
        self._score = Fraction(1, 1)
        self._buffer_size = 0
        self._points_deducted = {
            severity: Fraction(0, 1) for severity in KNOWN_SEVERITIES
        }
        self._file = open(options.cg_flake8_fd, 'wb', buffering=0)

        self._default_severity = options.cg_default_severity
        self._base_path = Path(options.cg_base_path)

        if options.cg_points_deducted:
            for severity, points in (
                item.split(':', 1) for item in options.cg_points_deducted
            ):
                if severity not in KNOWN_SEVERITIES:
                    sys.stderr.writelines([
                        f'Not recognised severity: {severity},'
                        ' found in the cg_points_deducted option.\n'
                    ])
                    sys.exit(2)
                try:
                    self._points_deducted[severity] = Fraction(
                        int(points), 100
                    )
                except ValueError:
                    sys.stderr.writelines([
                        f'Could not create an integer percentage from: {points},'
                        ' found in the cg_points_deducted option.\n'
                    ])
                    sys.exit(2)

        self._code_prefix_mapping = {
            'F': 'error',
            'E': 'error',
            'W': 'warning',
            'C': 'info',
            'N8': 'info',
        }

        if options.cg_code_prefix_mapping:
            for code_prefix, severity in [
                item.split(':', 1) for item in options.cg_code_prefix_mapping
            ]:
                if severity not in KNOWN_SEVERITIES:
                    sys.stderr.writelines([
                        f'Not recognised severity: {severity},'
                        ' found in the cg_code_prefix_mapping option.\n'
                    ])
                    sys.exit(2)

                self._code_prefix_mapping[code_prefix] = severity

    @classmethod
    def add_options(cls, parser: flake8.options.manager.OptionManager) -> None:
        """Adds the `cg-points-deducted` option to flake8 to set the deduction
        percentages for each of the severity levels.
        Adds the `cg-flake8-fd` option to flake8 to set the file descriptor to
        which to output the reports.
        """
        parser.add_option(
            '--cg-points-deducted',
            dest='cg_points_deducted',
            action='store',
            type=str,
            comma_separated_list=True,
            parse_from_config=True,
            help="""
Points deducted for each severity level. Should be a string of
the form 'info:1,warning:5,error:10,unknown:0'.
            """,
        )
        parser.add_option(
            '--cg-code-prefix-mapping',
            dest='cg_code_prefix_mapping',
            action='store',
            type=str,
            comma_separated_list=True,
            parse_from_config=True,
            help="""
Map the prefixes of error codes to a severity level. Should be a string of
the form '_prefix_:_severity_,_prefix_2_:_severity_2_, ...'
For example: 'F:error,E:error,W:warning,C:info,N8:info'.
            """,
        )
        parser.add_option(
            '--cg-flake8-fd',
            dest='cg_flake8_fd',
            action='store',
            type=int,
            metavar='file descriptor',
            default=1,
            help='File descriptor to write the results to.',
        )
        parser.add_option(
            '--cg-default-severity',
            dest='cg_default_severity',
            action='store',
            type=str,
            choices=KNOWN_SEVERITIES,
            parse_from_config=True,
            metavar='default severity',
            default='unknown',
            help="""
What the default severity will be when there is none found in the standard
or given mapping (--cg-code-prefix-mapping).
            """,
        )
        parser.add_option(
            '--cg-base-path',
            dest='cg_base_path',
            action='store',
            type=str,
            default='/',
            help="""
The base path of the reported files. Files that are not children of this path
will not be reported.
            """,
        )

    def get_severity(self, error: flake8.violation.Violation) -> str | None:
        """Get the severity for the given error."""
        code = error.code

        # Return the severity based on the code prefix mapping.
        for prefix, severity in self._code_prefix_mapping.items():
            if code.startswith(prefix):
                return severity

        # Or use the default fallback of the default severity
        return self._default_severity

    def format(self, error: flake8.violation.Violation) -> None:
        """
        Format the error/warning and add to buffer.
        Also update the score based on error severity.
        """
        try:
            abs_path = os.path.abspath(error.filename)
            relative_path = Path(abs_path).relative_to(self._base_path)
        except ValueError:
            return

        severity = self.get_severity(error)

        if severity in self._points_deducted:
            self._score = max(
                self._score - self._points_deducted[severity], Fraction(0)
            )

        err_item = {
            'code': error.code,
            'loc': {
                'start': {
                    'line': error.line_number,
                    'column': error.column_number,
                },
                'end': {
                    'line': error.line_number,
                },
            },
            'msg': error.text,
        }

        if severity != 'unknown':
            err_item['severity'] = severity

        added_size = len(json_dumps(err_item))

        if self._buffer_size + added_size >= MESSAGE_SIZE_LIMIT:
            self.flush()

        file_comments = self._buffer['comments'].get(str(relative_path))
        if file_comments is None:
            file_comments = {
                'filename': str(relative_path),
                'origin': 'Flake8',
                'items': [],
            }
            added_size += len(json_dumps(file_comments))

        file_comments['items'].append(err_item)
        self._buffer['comments'][str(relative_path)] = file_comments
        self._buffer_size += added_size

    def flush(self) -> None:
        """
        Write the comments to file descriptor and clear the buffer.
        """
        self._buffer['comments'] = list(self._buffer['comments'].values())
        data = json_dumps(self._buffer) + '\n'

        self._file.write(data.encode('utf8'))
        self._buffer = {'tag': 'comments', 'comments': {}}
        self._buffer_size = len(json_dumps(self._buffer))

    def stop(self) -> None:
        """
        At the end, flush the remaining comments and write the score.
        """
        self.flush()
        data = json_dumps({'tag': 'points', 'points': str(self._score)})
        self._file.write(data.encode('utf8'))
