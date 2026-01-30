# ConsolePy

JS-like console logging for Python with colors, styles, and CLI.

## Features

- Styled console output with colors, bold, underline, strike, markdown parsing
- Logging levels: DEBUG, INFO, SUCCESS, WARN, ERROR
- Automatic timestamp support
- JSON logs and file logging (`out.log`, `err.log`)
- JS-like methods: `console.print`, `console.debug`, `console.info`, `console.warn`, `console.error`, `console.success`, `console.exception`
- CLI: run Python scripts with consolepy fully configured
- Configurable via `.consolepy.toml`
- Automatic log rotation

## Using CLI
consolepy run myscript.py

## Installation

```bash
# Local development
git clone <repo>
cd consolepy
pip install -e .
```

## Usage
```py
from consolepy import console

console.print("[green+bold:**Success!**] __All done__")
console.debug("Debug info")
console.info("Information")
console.warn("Warning!")
console.error("Error!")
console.success("Operation succeeded")
console.exception("Exception caught", context=True)
```

## Config via `.consolepy.toml`
level = "DEBUG"
json = true
no_timestamp = false
log_rotation = true
out_file = "out.log"
err_file = "err.log"

## CLI Flags Override
consolepy run myscript.py --level INFO --no-timestamp --json
