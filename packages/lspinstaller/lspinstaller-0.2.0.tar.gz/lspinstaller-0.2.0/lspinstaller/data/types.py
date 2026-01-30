from lspinstaller.resolver.util.github import default_version_parser
from lspinstaller.resolver.arch import Arch
from typing import Optional, Callable
from dataclasses import dataclass, field

@dataclass
class ArchSpec:
    supported: dict[str, list[Arch]]
    parser: Callable[[Arch], str]

@dataclass
class GitHubSpec:
    fragment: str

@dataclass
class BinarySpec:
    link: dict[str, str]
    pattern: str | dict[str, str] | None = None
    url: str | None = None
    archive: str = "auto"
    is_nested: bool = False
    pattern_is_url: bool = False

@dataclass
class NpmSpec:
    package: str
    bin: str
    deps: list[str] = field(
        default_factory=list
    )

@dataclass
class PipSpec:
    package: str
    bin: str

@dataclass
class Source:
    github: Optional[GitHubSpec] = None
    binary: Optional[BinarySpec] = None
    npm: Optional[NpmSpec] = None
    pip: Optional[PipSpec] = None
    arch: Optional[ArchSpec] = None
    version_parser: Callable[[str], str] = default_version_parser

    removed: bool = False
