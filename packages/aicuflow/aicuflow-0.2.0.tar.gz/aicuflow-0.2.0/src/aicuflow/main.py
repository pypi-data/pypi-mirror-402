import argparse
import webbrowser
from importlib.metadata import version, PackageNotFoundError


BASE_URL = "https://aicuflow.com"

COMMAND_URLS = {
    "docs": f"{BASE_URL}/docs",
    "flows": f"{BASE_URL}/flows",
    "flow": f"{BASE_URL}/flows",
    "tools": f"{BASE_URL}/tools",
    "signin": f"{BASE_URL}/signin",
    "blog": f"{BASE_URL}/blog",
    "vecs": "https://projector.tensorflow.org/",
}


def get_version() -> str:
    try:
        return version("aicuflow")
    except PackageNotFoundError:
        return "unknown (not installed)"


def open_url(name: str) -> None:
    webbrowser.open(COMMAND_URLS[name])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aicuflow",
        description="AICUFlow CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
    )

    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        required=True,
    )

    for cmd in COMMAND_URLS:
        subparsers.add_parser(
            cmd,
            help=f"Open {cmd} in browser",
        )

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    open_url(args.command)

#if __name__ == "__main__":
#    main()
