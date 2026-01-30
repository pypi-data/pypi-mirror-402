## SysGuard

SysGuard is a small Python command-line tool for basic system auditing (and, later, “self-healing” actions).

Right now, the project is a working CLI skeleton with an `audit` subcommand that prints a placeholder message. It’s ready to be extended with real checks.

## Requirements

- Python 3.9+ (3.10+ recommended)
- Dependencies: `psutil`

## Install

1) Create and activate a virtual environment (recommended):

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows (cmd):

```bat
python -m venv .venv
.\.venv\Scripts\activate.bat
```

2) Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Show help:

```bash
python sysguard.py --help
```

Run the (placeholder) audit command:

```bash
python sysguard.py audit
```

Expected output (currently):

```text
Running system audit...
```

## Project layout

- `sysguard.py`: CLI entry point (argument parsing + command routing)
- `requirements.txt`: runtime dependency list

## Extending SysGuard

SysGuard uses `argparse` subcommands. To add a new command:

1) Add another parser via `subparsers.add_parser("<command>")`
2) Check `args.command` and run your code for that command

Example ideas for an `audit` implementation using `psutil`:

- CPU usage and load
- Memory usage and swap
- Disk usage per partition
- Top processes by CPU/RAM

## Development

- Run from source: `python sysguard.py audit`
- Keep changes small and test from the command line after edits.

## License

No license file is included yet. If you plan to publish this project, add a LICENSE file (for example: MIT, Apache-2.0, GPL-3.0).
