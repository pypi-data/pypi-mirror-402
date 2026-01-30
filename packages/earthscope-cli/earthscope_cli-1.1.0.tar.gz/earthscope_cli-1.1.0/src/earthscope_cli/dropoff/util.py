import enum
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Annotated, Iterable, Optional, Union

import click
import typer
from earthscope_sdk.client.dropoff.models import DropoffCategory
from typer_di import Depends

from earthscope_cli.common import get_sdk


@dataclass
class PaginationOptions:
    offset: int
    limit: int


@dataclass
class DropoffOptions(PaginationOptions):
    category: DropoffCategory


def collect_files(src: list[Path]) -> Iterable[tuple[Path, str]]:
    """
    Collect all files and their keys from a list of paths.

    Args:
        src: List of paths to collect files from.

    Returns:
        Iterable of tuples containing (file, key) pairs.
    """

    def _gen():
        for p in src:
            if p.is_file():
                yield (p, key_from_path(p))

            elif p.is_dir():
                yield from (
                    (f, key_from_path(f, p)) for f in p.rglob("*") if f.is_file()
                )

    ux = set()
    for f in _gen():
        if f not in ux:
            ux.add(f)
            yield f


def get_category(
    sdk=Depends(get_sdk),
    category: Annotated[
        Optional[DropoffCategory],
        typer.Option(
            "--category",
            "-c",
            help=(
                "Filter by category. If a category is set in the SDK settings, "
                "it will be used when no category is provided."
            ),
        ),
    ] = None,
):
    """
    Obtain the dropoff category in the following order:
    - Command line argument
    - SDK settings
    - User prompt
    """
    if category:
        return category

    if sdk.ctx.settings.dropoff.category:
        return sdk.ctx.settings.dropoff.category

    # Prompt user to choose a category
    cat_str: str = typer.prompt(
        "Choose a dropoff category",
        type=click.Choice(DropoffCategory._value2member_map_.keys()),
    )

    return DropoffCategory(cat_str)


def get_dropoff_options(
    category: Annotated[DropoffCategory, Depends(get_category)],
    offset: Annotated[
        int,
        typer.Option("--offset", help="Pagination offset", min=0),
    ] = 0,
    limit: Annotated[
        int,
        typer.Option("--limit", help="Number of items per page", min=1, max=100),
    ] = 100,
):
    return DropoffOptions(
        category=category,
        offset=offset,
        limit=limit,
    )


def key_from_path(
    file_path: Union[Path, str],
    relative_to: Union[Path, str, None] = None,
) -> str:
    """
    Build the S3 object key from a file path relative to a base path:
    - If the base path is a directory, prefix with that directory's name.
    - If the file path is a single file, ensure at least one directory segment
        by prefixing with the file's parent directory name.
    """
    file_path = Path(file_path).expanduser().resolve()
    if relative_to:
        relative_to = Path(relative_to).expanduser().resolve()
    else:
        relative_to = file_path.parent

    # Anchor is the input directory (if dir is passed) else file's parent.
    base = relative_to if relative_to.is_dir() else relative_to.parent

    # Try make file_path relative to base;
    # if unrelated, just use the file name.
    try:
        rel = file_path.relative_to(base)
    except ValueError:
        rel = Path(file_path.name)

    # Always prefix w/ anchor directory's name & keep at least 1 segment.
    return str(Path(base.name) / rel)


def safe_str(value):
    """Convert any value into a string safe for Rich tables."""
    if value is None:
        return "-"

    if isinstance(value, datetime):
        result = value.isoformat(timespec="seconds")
        if result.endswith("+00:00"):
            result = result[:-6] + "Z"

        return result

    if isinstance(value, enum.Enum):
        return value.value

    return str(value)
