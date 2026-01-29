# cg-flake8-reporter

A Flake8 reporter plugin for CodeGrade AutoTest v2.

This plugin writes messages to CodeGrade AutoTest v2's structured output channel.
For each violation Flake8 reports, a `comments` message is written as described
in CodeGrade's documentation. When Flake8 finishes its analysis, a final message
is written with the amount of points that were achieved in the code quality run.

## Configuration

In order to use the custom reporter, make sure you have installed both Flake8
and this package:

```bash
python3 -m pip install flake8==6.0.0
python3 -m pip install cg-flake8-reporter
```

This reporter is registered with Flake8 as `cg-flake8-reporter`, to use it run
flake with the option `--format=cg-flake8-reporter`.

The custom reporter adds a few new options to Flake8: `cg-points-deducted`,
`cg-flake8-fd` and `cg-base-path`.

### cg-points-deducted

The `cg-points-deducted` option makes it possible to configure the amount of
points (in percentage) that each violation deducts from the total points.

The `cg-points-deducted` expectes a string in the following format as input:

```bash
'info:<percentage>,warning:<percentage>,error:<percentage>'
```

Each of the violation levels must be present in the provided string. The
percentage provided should be an integer number **without** the `%` symbol.

If you wish for a violation level to not deduct points, simply set it to `0`.

### cg-flake8-fd

The `cg-flake8-fd` option makes it possible to configure where the reporter
will write its output. By default, the value is `1`, which means the reporter
will write to `stdout`. Within AutoTest v2 it is recommended to use file
descriptor `3` so that the comments will be visible in CodeGrade's UI. The
_Flake8_ step will already set this up for you.

### cg-base-path

The `cg-base-path` allows you to restrict which files the reporter will report.
For example, if you only want files to be reported within the `server` directory
of the student, you may want to set `--cg-base-path=~/student/server/`. Beware,
the _Flake8_ step always sets `cg-base-path` to the root of the student's
workspace. If you want to customize this, you should use a _Custom Test_ step
instead.

### cg-code-prefix-mapping

The `cg-code-prefix-mapping` options allows you to create a custom mapping
between error code prefixes and severities. The code prefixes are groups of errors.
The option expects a string in the following format:
```bash
'_prefix_:_severity_,_prefix_2_:_severity_2_,...'
```

The normal mapping can be represented as follows:
```bash
'F:error,E:error,W:warning:C:info,N8:info'
```

The standard mapping will always be set, however you can overwrite existing
keys with new values should you want this.

This mapping also allows you to use libraries that introduce new error types,
which will use a different, unknown code prefix.

### cg-default-severity

The `cg-default-severity` option will set provide a fallback severity, when we
have checked the default mapping, (plus your supplied mapping,) and could not
find any set severity for the code prefix.

For example, when we install a library that adds error codes in the form of
`D...`, where the dots are the actual error code numbers. We will search for
an entry in the severity mapping, and fallback to the default if we cannot find
anything.

The default value for this option is: 'unset', which means that there can be
no deduction for this type of code, and will not get flagged as categorised
errors.


## Usage

To run Flake8 with the custom reporter:

```bash
python3 -m flake8 \
    --format=cg-flake8-reporter \
    --cg-points-deducted='info:1,warning:3,error:5,unknown:0' \
    --cg-flake8-fd=1 \
    ./
```

To run flake8 when having a library installed that adds error codes with prefix `D`
and assign the `info` severity to each error starting with a `D`:

```bash
python3 -m flake8 \
    --format=cg-flake8-reporter \
    --cg-points-deducted='info:1,warning:3,error:5,unknown:0' \
    --cg-code-prefix-mapping='D:info' \
    --cg-flake8-fd=1 \
    ./
```
