import tomllib  # Python 3.11+ ou use tomli para <=3.10
import os
import sys
import runpy
import argparse
from consolepy import console


def main():
    parser = argparse.ArgumentParser(
        prog="consolepy",
        description="ConsolePy CLI"
    )

    sub = parser.add_subparsers(dest="command")
    run_cmd = sub.add_parser("run", help="Executar script com ConsolePy")
    run_cmd.add_argument("script", help="Arquivo .py para executar")
    run_cmd.add_argument("--level", default=None)
    run_cmd.add_argument("--json", action="store_true")
    run_cmd.add_argument("--no-timestamp", action="store_true")

    args, unknown = parser.parse_known_args()

    if args.command != "run":
        parser.print_help()
        sys.exit(1)

    # ===== LÊ .consolepy.toml =====
    config = {}
    config_file = os.path.join(os.getcwd(), ".consolepy.toml")
    if os.path.exists(config_file):
        with open(config_file, "rb") as f:
            config = tomllib.load(f)

    # ===== CONFIG CONSOLE =====
    level = args.level or config.get("level", "INFO")
    console.set_level(level)

    show_ts = not args.no_timestamp
    if "no_timestamp" in config:
        show_ts = not config.get("no_timestamp", False)
    console.show_timestamp = show_ts

    json_logs = args.json or config.get("json", False)
    console.enable_json_logs(json_logs)

    console.set_log_rotation(config.get("log_rotation", False))

    out_file = config.get("out_file", None)
    err_file = config.get("err_file", None)
    console.set_log_files(out_file, err_file)

    console.bind_logging(exclusive=False)

    # ===== EXECUTA SCRIPT =====
    sys.argv = [args.script] + unknown
    try:
        runpy.run_path(args.script, run_name="__main__")
    except Exception:
        console.exception("Erro não tratado", context=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
