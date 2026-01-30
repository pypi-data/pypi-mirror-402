import argparse
from dataclasses import dataclass
import os
import shutil
import time

from loguru import logger

from lspinstaller.config import load_config
from lspinstaller.constants import LSP_HOME
from lspinstaller.resolver.resolver import resolve, do_update
from .data import sources

class Arguments(argparse.Namespace):
    package: str | None
    packages: list[str] | None

def run_list(_args):
    print(f"There are {len(sources)} available servers.")
    print()
    print('   {0:<30} How installed'.format("Name in lspinstaller"))
    for (name, data) in sources.items():
        builder = f" * {name:<30} "
        if (data.github is not None):
            if data.binary and data.binary.pattern_is_url:
                builder += f"via URL: {data.binary.pattern}"
            else:
                builder += f"via GitHub: {data.github.fragment}"
        elif (data.npm):
            builder += f"via npm: {data.npm.package}"
        elif (data.pip):
            builder += f"via pip: {data.pip.package}"
        else:
            builder += "Unknown source. Someone added a type without " \
                "updating the list command"
        print(builder)

def run_install(args):
    assert args.packages is not None
    logger.info(f"Installing: {', '.join(args.packages)}")

    config = load_config()

    for package in args.packages:
        if not package in sources:
            logger.error(
                f"{package} is not a known lsp. See lspinstaller list for the available LSPs"
            )
            exit(-1)
        elif package in config.packages:
            logger.error(
                f"{package} has already been installed. Use update instead"
            )
            exit(-1)

    # This is not inlined into the previous for loop intentionally. 
    # The previous loop is just validation, and gives much more rapid feedback
    # than a unified loop would be able to do.
    for package in args.packages:
        spec = sources[package]

        if spec.binary:
            output_path = os.path.join(
                LSP_HOME,
                package
            )
            if os.path.exists(
                output_path
            ):
                logger.warning(f"{output_path} already exists.")
                logger.warning("This is likely a weird state artefact. The folder will now be removed before the install is attempted")
                logger.warning("If this is a mistake, press CTRL-C to abort NOW!")

                time.sleep(10)

                shutil.rmtree(
                    output_path
                )

        resolve(package, spec, config)
    config.commit()


def run_update(_args):
    config = load_config()
    do_update(config)

def find_package(args):
    package = args.package
    assert package is not None
    assert isinstance(package, list)
    package = package[0]

    if package not in sources:
        exit(-2)

    spec = sources[package]

    expected_path: str
    if spec.npm:
        expected_path = os.path.join(
            LSP_HOME,
            "node_modules",
            ".bin",
            spec.npm.bin
        )
    elif spec.binary:
        expected_path = os.path.join(
            LSP_HOME,
            package,
            list(spec.binary.link.values())[0]
        )
    elif spec.pip:
        expected_path = os.path.join(
            LSP_HOME,
            "env", "bin",
            package
        )
    else:
        exit(-3)

    if not os.path.exists(expected_path):
        exit(-1)
    print(expected_path)



def start_cli():
    parser = argparse.ArgumentParser(
        prog="lspinstaller",
        description="""Installs (some) LSP servers.

Some special identifiers:
* QUIET: Indicates a CLI that will not change in any way, and
  that's explicitly intended for use with scripts.
  Note that commands not labelled as STABLE can still be used with CLI use, but
  because that isn't the explicit intent, they'll have a lot more output.

  Stable CLIs are guaranteed to work with $(lspinstaller command ...args) in shell
  without needing any additional tweaking.
""",
        epilog="lspinstaller is licensed under the MIT license: https://codeberg.org/LunarWatcher/lspinstaller/src/branch/master/LICENSE",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subs = parser.add_subparsers(required=True)
    cmd_list = subs.add_parser(
        "list",
        help="List the available LSP servers"
    )
    cmd_list.set_defaults(func=run_list)

    cmd_install = subs.add_parser(
        "install",
        help="Install an LSP server"
    )
    cmd_install.add_argument(
        "packages",
        nargs="+",
        help="The packages to install",
    )
    cmd_install.set_defaults(func=run_install)

    cmd_update = subs.add_parser(
        "update",
        help="Updates all LSP servers"
    )
    cmd_update.set_defaults(func=run_update)

    cmd_find = subs.add_parser(
        "find",
        help="QUIET: Returns the path of an LSP server. This CLI is guaranteed to "
        "never change, as it's intended for scripting purposes. For example, "
        "$(lspinstaller find luals) will always return the absolute path to luals, "
        "or exit with -1 if luals is not installed."
    )
    cmd_find.add_argument(
        "package",
        nargs=1,
        help="The package to find",
    )
    cmd_find.set_defaults(func=find_package)

    cmd_home = subs.add_parser(
        "home",
        help="QUIET: Prints the path to the lsp root dir."
    )
    cmd_home.set_defaults(func=lambda _: print(LSP_HOME))


    args: Arguments = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    start_cli()
