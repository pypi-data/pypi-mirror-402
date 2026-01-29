# frslint

Linter for FreeSWITCH XML configuration files. Checks code style, finds common errors, and can auto-fix most issues. Able to run debug mode to follow the evalution steps in your freeswitch to follow where what is happen in your configuration.

## About

This project is a hobby project. As I am tasked with maintaining some freeswitch systems and the freeswitch ecosystem was lacking any static analysis / debugging tools. It is not perfect, the code has its faults, not every case is covered yet, but I would like to continue improving this over time. Feel free to submit wishes / bug reports, so this tool can grow into something bigger.

## Installation

```bash
pip install frslint
```

Or install from source:

```bash
git clone https://github.com/zimmer-yan/frslint
cd frslint
pip install -e .
```

## Usage

### Lint (code style)

Check for style issues:

```bash
frslint lint /etc/freeswitch/freeswitch.xml
```

Auto-fix what can be fixed:

```bash
frslint lint /etc/freeswitch/freeswitch.xml --fix
```

Options:

```
--fix                 Auto-fix fixable issues
--indent-size N       Expected indent size (default: 2)
--max-line-length N   Max line length (default: 120)
--max-blank-lines N   Max consecutive blank lines (default: 2)
--allow-tabs          Allow tabs instead of spaces
-f, --format json     Output json formatted
-v, --verbose         Verbose output
```

### Analyze (static analysis)

Check for errors like undefined variables, invalid regex, etc:

```bash
frslint analyze /etc/freeswitch/freeswitch.xml
```

Options:

```
-f, --format json     Output json formatted
-v, --verbose         Verbose output
```

### Debug

Trace dialplan execution for a given destination number:

```bash
frslint debug /etc/freeswitch/freeswitch.xml 1234
frslint debug /etc/freeswitch/freeswitch.xml 1234 -c public
```

Options:

```
-n, --network-addr      Network address of the caller
-c, --context-name      Name of the context to run (default: public)
-v, --verbose           Verbose output
```

## What it checks

**Lint:**
- Trailing whitespace
- Tabs vs spaces
- Indentation depth
- Consecutive blank lines
- Missing newline at EOF
- Line length
- Mixed line endings (CRLF/LF)

**Analyze:**
- Undefined channel variables
- Invalid regex patterns
- Missing required attributes
- Unknown applications

## Exit codes

- `0` - No issues found
- `1` - Issues found (or unfixed issues when using `--fix`)
