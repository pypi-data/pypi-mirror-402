import argparse
import logging

import json
from sysguard.audit import (
    collect_audit_data,
    get_disk_usage,
    get_cpu_usage,
    get_memory_usage,
)
from sysguard.logging import setup_logging
log = logging.getLogger(__name__)


def run_audit(json_output: bool = False):
    data = collect_audit_data()

    if json_output:
        print(json.dumps(data, indent=2))
    else:
        for section, values in data.items():
            log.info(section.upper())
            for k, v in values.items():
                log.info(f"  {k}: {v}")


def main():
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    parser = argparse.ArgumentParser(
        description="SysGuard – System Audit & Self-Healing Tool",
        parents=[common_parser],
    )

    subparsers = parser.add_subparsers(dest="command")

    audit_parser = subparsers.add_parser(
        "audit",
        help="Run system audit",
        parents=[common_parser],
    )
    audit_parser.add_argument(
        "--json", action="store_true", help="JSON Output")

    args = parser.parse_args()

    setup_logging(verbose=args.verbose)

    if args.command == "audit":
        run_audit(json_output=args.json)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
