from pathlib import Path
from textwrap import dedent
from typing import Annotated

import typer
from earthscope_sdk import EarthScopeClient
from earthscope_sdk.client.dropoff.models import DropoffCategory
from earthscope_sdk.client.dropoff.validation import Validator
from rich import print
from typer_di import Depends, TyperDI

from earthscope_cli.common import get_sdk_refreshed
from earthscope_cli.dropoff.render import (
    ConcurrentUploadProgressDisplay,
    print_dropoff_objects_table,
)
from earthscope_cli.dropoff.util import (
    DropoffOptions,
    collect_files,
    get_category,
    get_dropoff_options,
)

app = TyperDI()


@app.command(name="get-object-history")
def get_object_history(
    sdk: Annotated[EarthScopeClient, Depends(get_sdk_refreshed)],
    options: Annotated[DropoffOptions, Depends(get_dropoff_options)],
    key: Annotated[
        str,
        typer.Option(
            "--key",
            "-k",
            help="The dropoff object key (path) to get history for.",
            prompt="Object key",
        ),
    ],
):
    """
    Retrieve the upload history for a specific object key.

    When the same object key is uploaded to multiple times, this command
    retrieves the upload history for that object key.

    es dropoff get-object-history -c <type> -k <key>
    es dropoff get-object-history -c miniseed -k demo/SAML.IU.2025.303
    es dropoff get-object-history -c miniseed -k demo/SAML.IU.2025.303 --offset 100 --limit 100
    """
    result = sdk.dropoff.get_object_history(
        category=options.category.value,
        key=key,
        offset=options.offset,
        limit=options.limit,
    )

    if result.items:
        return print_dropoff_objects_table(
            result.items,
            title=f"History for: {key}",
            has_next=result.has_next,
            next_offset=result.offset + result.limit,
        )

    cat_str = options.category.value
    print(f"[yellow]No history found for category '{cat_str}' with key '{key}'")


@app.command(name="list-objects")
def list_objects(
    sdk: Annotated[EarthScopeClient, Depends(get_sdk_refreshed)],
    options: Annotated[DropoffOptions, Depends(get_dropoff_options)],
    prefix: Annotated[
        str,
        typer.Option(help="Filter by object prefix"),
    ] = "",
):
    """
    List objects in your dropoff space.

    es dropoff list-objects -c <type> --prefix <prefix>
    es dropoff list-objects -c miniseed
    es dropoff list-objects -c miniseed --prefix demo/
    es dropoff list-objects -c miniseed --offset 100 --limit 100
    """
    result = sdk.dropoff.list_objects(
        category=options.category.value,
        prefix=prefix,
        offset=options.offset,
        limit=options.limit,
    )

    suffix = ""
    if prefix:
        suffix = f" - prefix: '{prefix}'"

    cat_str = options.category.value
    if result.items:
        return print_dropoff_objects_table(
            result.items,
            title=f"{cat_str} objects{suffix}",
            has_next=result.has_next,
            next_offset=result.offset + result.limit,
        )

    print(f"[yellow]No objects found for category '{cat_str}'{suffix}")


@app.command(name="upload")
def upload(
    sdk: Annotated[EarthScopeClient, Depends(get_sdk_refreshed)],
    category: Annotated[DropoffCategory, Depends(get_category)],
    paths: Annotated[
        list[Path],
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=True,
            resolve_path=True,
            help=dedent(
                """
                The local path of a file or directory to upload.

                The path must include a directory e.g. 2026-01-01/file1 or 2025-01-01/
                """
            ),
        ),
    ],
    object_concurrency: Annotated[
        int,
        typer.Option(
            "--object-concurrency",
            help="Maximum concurrent files to upload concurrently",
        ),
    ] = 3,
    part_concurrency: Annotated[
        int,
        typer.Option(
            "--part-concurrency",
            help="Maximum concurrent parts across all uploads",
        ),
    ] = 8,
    part_size: Annotated[
        int,
        typer.Option(
            "--part-size",
            help="Size of each upload part",
        ),
    ] = 10 * 1024**2,
):
    """
    Upload files or directories to EarthScope's dropoff system.

    Examples:
        es dropoff upload -c miniseed file.mseed
        es dropoff upload -c miniseed mydata/
        es dropoff upload -c miniseed project1/data.mseed project2/data.mseed

    How S3 keys are generated:

    - For individual files: The parent directory name is included in the S3 key
      to provide context and prevent collisions.
      Example: uploading 'project1/data.mseed' creates key 'project1/data.mseed'

    - For directories: All files maintain their relative paths from the directory,
      with the directory name as a prefix.
      Example: uploading 'mydata/' containing 'subdir/file.mseed' creates
      key 'mydata/subdir/file.mseed'

    - Multiple files: Each file preserves its parent directory context.
      Example: uploading 'proj1/data.mseed' and 'proj2/data.mseed' creates
      distinct keys 'proj1/data.mseed' and 'proj2/data.mseed'

    This behavior ensures files with the same name from different locations
    don't overwrite each other and maintains meaningful organization in S3.
    """
    # Parse the input path to get a list of files
    files: list[tuple[Path, str]] = []
    for p, k in collect_files(paths):
        try:
            Validator(p, category=category).validate_all()
        except Exception as e:
            print(f"[red]{e}")
            raise typer.Exit(code=1)
        else:
            files.append((p, k))

    if not files:
        print(f"[red]No files found in paths: {paths}")
        raise typer.Exit(code=1)

    try:
        with ConcurrentUploadProgressDisplay(len(files)) as display:
            sdk.dropoff.put_objects(
                objects=files,
                category=category,
                object_concurrency=object_concurrency,
                part_concurrency=part_concurrency,
                part_size=part_size,
                progress_cb=display.callback,
            )
    except KeyboardInterrupt:
        print()
        print("[yellow]Upload interrupted. Use the same command to resume the upload.")
