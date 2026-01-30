from lspinstaller.data.types import Source, ArchSpec
from dataclasses import dataclass
import enum
import os
import stat
import subprocess
import shutil
import platform
from loguru import logger
from lspinstaller.config import Config
from lspinstaller.constants import LSP_HOME
from lspinstaller.data import sources
from lspinstaller.resolver.arch import Arch, Arch, resolve_arch
from lspinstaller.resolver.arch import resolve_arch
from lspinstaller.resolver.util.github import default_version_parser, get_release_info
from lspinstaller.resolver.util.fetch import fetch

@dataclass
class Data:
    version: str
    os: str

def init_data(version: str):
    return Data(
        version=version,
        os=platform.system().lower()
    )

def parse_special(value, data: Data) -> str:
    if not isinstance(value, str):
        return value(data)
    else:
        # TODO: This will not scale well. Do not add more fields this way;
        # write a proper replacement engine instead.
        value = value.replace("${os}", data.os)
        value = value.replace("${version}", data.version)

        return value

def ensure_venv():
    if not os.path.exists(os.path.join(LSP_HOME, "env")):
        logger.info("venv not set up. Creating it now")
        logger.warning("This step may fail if you don't have python3-venv installed")
        subprocess.run(
            ["python3", "-m", "venv", "env"],
            cwd=LSP_HOME,
            check=True,
        )

def resolve(package_name, spec: Source, config: Config):
    assert spec is not None
    os.makedirs(
        os.path.join(LSP_HOME, "bin"),
        exist_ok=True
    )
    if spec.removed:
        logger.info(
            f"{package_name} has been removed, and will not be updated or installed"
        )
    elif spec.github:
        release = get_release_info(
            spec.github.fragment,
            spec.version_parser
        )
        binary = spec.binary
        assert binary is not None, \
            f"misconfigured binary object for {package_name}"

        if binary.url:
            url = binary.url
            url = parse_special(
                url,
                init_data(
                    release.tag_name
                )
            )
        else:
            pattern = binary.pattern
            assert pattern is not None
            data = init_data(
                release.tag_name
            )
            if isinstance(pattern, dict):
                pattern  = pattern[data.os]

            pattern = parse_special(
                pattern,
                data,
            )

            if spec.arch:
                arch_spec: ArchSpec = spec.arch
                arch: Arch = resolve_arch()
                if arch not in arch_spec.supported[data.os]:
                    raise RuntimeError(
                        f"{package_name} is not supported on {arch}. "
                        f"Supported: {arch_spec['supported']}"
                    )

                pattern = pattern.replace("${arch}", arch_spec.parser(arch))
            url = None
            if binary.pattern_is_url == False:
                for asset in release.assets:
                    if asset.name == pattern:
                        logger.info(f"Resolved asset URL to {asset.name}")
                        url = asset.url
                        break
                else:
                    logger.error(
                        f"Failed to resolve GitHub release asset for {package_name}"
                    )
                    raise RuntimeError(
                        f"Failed to resolve GH asset for {package_name}"
                    )
            else:
                # We've resolved the pattern to its full URL form. Since it's a
                # URL, it can be used verbatim from this point
                url = pattern

        # Should never throw, but required because url is str | None due to the
        # = None assignment in the previous if statement
        assert url is not None
        root = fetch(
            LSP_HOME,
            url,
            package_name,
            binary.archive,
            binary.is_nested
        )

        for (dest_name, src_path) in binary.link.items():

            full_src = os.path.join(root, src_path)
            full_dest = os.path.join(
                LSP_HOME,
                "bin",
                dest_name
            )
            if platform.system() != "Windows":
                logger.info("Chmoding...")
                os.chmod(
                    full_src,
                    mode=os.stat(full_src).st_mode | stat.S_IEXEC
                )
            # TODO: symlinking breaks clangd
            # print(f"Symlinking {full_src} -> {full_dest}")
            # if os.path.exists(full_dest):
                # os.remove(full_dest)
            # os.link(
                # full_src, full_dest
            # )


        config.update_package(package_name, release.tag_name)
        return release.tag_name
    elif spec.npm:
        args = [
            "npm",
            "install",
            spec.npm.package
        ]
        for dep in spec.npm.deps:
            args.append(dep)

        subprocess.run(
            args,
            cwd=LSP_HOME,
            check=True,
        )
        return None
    elif spec.pip:
        ensure_venv()
        args = [
            "./env/bin/python3",
            "-m",
            "pip", "install", spec.pip.package
        ]
        subprocess.run(
            args,
            cwd=LSP_HOME,
            check=True,
        )
        # We need to track the python-managed packages because they cannot be
        # updated otherwise
        config.update_package(package_name, "__python_managed__")
        return "__python_managed__"

def do_update(config: Config):
    logger.info("Updating npm packages...")
    if os.path.exists(
        os.path.join(
            LSP_HOME,
            "node_modules"
        )
    ):
        # Pretty sure this should just work:tm:, since npm install uses the ^
        # notation, which should work with npm update:
        # https://stackoverflow.com/a/19824154
        subprocess.run(
            ["npm", "update"],
            cwd=LSP_HOME
        )

    logger.info("Updating other packages...")
    for [name, package] in config.packages.items():
        logger.info(f"Updating {name}")
        try:
            if "__python_managed__" in package.version:
                logger.debug("Package is managed by pip; deferring to pip")
                args = [
                    "./env/bin/python3",
                    "-m",
                    "pip", "install", "--upgrade",
                    sources[name].pip.package
                ]
                subprocess.run(
                    args,
                    cwd=LSP_HOME
                )
            else:
                logger.debug("Package is binary; checking for updates")
                dest = os.path.join(
                    LSP_HOME,
                    name
                )

                # Nuke the existing tree just in case
                if os.path.exists(dest):
                    shutil.rmtree(
                        dest
                    )

                new_version = resolve(
                    name,
                    sources[name],
                    config
                )
                assert new_version is not None, \
                    "Developer error: resolve returned None for binary"
                package.version = new_version
        except Exception as e:
            logger.error(f"Failed to update {name}: {e}")
    config.commit()
