import threading
from typing import Dict, List, Optional

from earthscope_sdk.client.dropoff._multipart_uploader import UploadStatus
from earthscope_sdk.client.dropoff.models import DropoffObject
from rich import print
from rich.console import Group
from rich.live import Live
from rich.progress import (
    BarColumn,
    DownloadColumn,
    MofNCompleteColumn,
    Progress,
    ProgressColumn,
    Task,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    filesize,
)
from rich.table import Column, Table
from rich.text import Text

from earthscope_cli.dropoff.util import safe_str


def _colorize_status(status: str) -> Text:
    s = (status or "").upper()
    if s == "RECEIVED":
        return Text("RECEIVED", style="cyan")
    if s == "VALIDATING":
        return Text("VALIDATING", style="yellow")
    if s == "VALIDATED":
        return Text("VALIDATED", style="green")
    if s == "AUTHORIZING":
        return Text("AUTHORIZING", style="yellow")
    if s == "AUTHORIZED":
        return Text("AUTHORIZED", style="green")
    if s == "ACCEPTED":
        return Text("ACCEPTED", style="green")
    if s == "FAILED":
        return Text("FAILED", style="red")
    if s == "INTERNAL_ERROR":
        return Text("INTERNAL_ERROR", style="red")
    return Text(f"{status or '-'}", style="dim")


def print_dropoff_objects_table(
    objects: List[DropoffObject],
    *,
    title: str,
    has_next: bool,
    next_offset: int,
):
    if has_next:
        caption = f"Use --offset {next_offset} to view more results."
    else:
        caption = "End of results."

    table = Table(
        title=title,
        show_header=True,
        title_style="bold magenta",
        header_style="bold magenta",
        caption=caption,
    )
    table.add_column("Name")
    table.add_column("Size", justify="right")
    table.add_column("Last Modified", justify="right")
    table.add_column("Status", justify="center")
    table.add_column("Message")

    for o in objects:
        table.add_row(
            safe_str(o.path),
            filesize.decimal(o.size),
            safe_str(o.received_at),
            _colorize_status(o.status),
            safe_str(o.status_message),
        )

    print()
    print(table)
    print()


class AggregateBytesColumn(ProgressColumn):
    """
    Custom column that shows aggregate bytes across all uploads.
    Reads total_bytes from task fields.
    """

    def __init__(self, table_column: Optional[Column] = None, *, field_name: str):
        super().__init__(table_column)
        self.field_name = field_name

    def render(self, task: Task) -> Text:
        """Render the aggregate bytes."""
        total_bytes = task.fields.get(self.field_name, 0)
        text_bytes = filesize.decimal(int(total_bytes))
        return Text(text_bytes, style="progress.filesize.total")


class AggregateThroughputColumn(ProgressColumn):
    """
    Custom column that shows aggregate throughput across all uploads.
    Reads total_bytes from task fields and divides by elapsed time.
    """

    def __init__(self, table_column: Optional[Column] = None, *, field_name: str):
        super().__init__(table_column)
        self.field_name = field_name

    def render(self, task: Task) -> Text:
        """Render the aggregate throughput."""
        total_bytes = task.fields.get(self.field_name, 0)
        elapsed = task.elapsed

        if elapsed is None or elapsed == 0:
            return Text("?", style="progress.data.speed")

        # Calculate throughput in bytes per second, format as human-readable
        speed = total_bytes / elapsed
        data_speed = filesize.decimal(int(speed))

        return Text(f"{data_speed}/s", style="progress.data.speed")


class CompositeProgressBarColumn(ProgressColumn):
    """
    Custom progress column that shows both buffer and upload progress on one bar.

    Bar visualization:
    - Green: Uploaded to S3 (bytes_done)
    - Blue: Buffered but not uploaded (bytes_buffered - bytes_done)
    - Grey: Not yet read (total - bytes_buffered)
    """

    def __init__(self, bar_width: int = 40):
        self.bar_width = bar_width
        super().__init__()

    def render(self, task: Task) -> Text:
        """Render the composite progress bar."""
        bytes_done = task.completed
        bytes_buffered = task.fields.get("bytes_buffered", bytes_done)
        total = task.total or 0

        if total == 0:
            return Text("─" * self.bar_width, style="bar.back")

        # Calculate widths for each section
        upload_pct = min(bytes_done / total, 1.0)
        buffer_pct = min(bytes_buffered / total, 1.0)

        upload_width = int(self.bar_width * upload_pct)
        buffer_width = int(self.bar_width * buffer_pct) - upload_width
        empty_width = self.bar_width - upload_width - buffer_width

        # Build the composite bar
        result = Text()

        # Green section (uploaded)
        if upload_width > 0:
            if upload_pct >= 1.0:
                result.append("━" * upload_width, style="green")
            else:
                result.append(
                    "━" * (upload_width - 1) if upload_width > 1 else "", style="green"
                )
                result.append("╸", style="green")

        # Blue section (buffered but not uploaded)
        if buffer_width > 0:
            result.append("━" * buffer_width, style="cyan")

        # Grey section (not yet buffered)
        if empty_width > 0:
            result.append("─" * empty_width, style="bar.back")

        return result


class ConcurrentUploadProgressDisplay:
    """
    Rich progress display for concurrent file uploads.

    Shows:
    - Overall progress of files completed
    - Individual progress bar for each active upload
    - Human-readable bytes, transfer rate, and percent complete

    For large numbers of files, completed progress bars are automatically
    hidden to keep the display clean and focused on active uploads.

    Usage:
        display = ConcurrentUploadProgressDisplay(num_files=10)
        with display:
            sdk.dropoff.put_dropoff_files(
                files=file_list,
                category="miniseed",
                progress_cb=display.callback,
            )
    """

    def __init__(
        self,
        num_files: int,
        hide_completed_threshold: int = 10,
        hide_delay_seconds: float = 1.5,
    ):
        """
        Initialize the progress display.

        Args:
            num_files: Total number of files to upload
            hide_completed_threshold: Threshold for hiding completed progress bars
            hide_delay_seconds: Delay in seconds before hiding completed progress bars
        """
        self.hide_completed_threshold = hide_completed_threshold
        self.hide_delay_seconds = hide_delay_seconds
        self.num_files = num_files
        self.files_completed = 0
        self.upload_started = False  # Track if we've received any bytes yet

        # Overall progress (files completed, plus aggregate throughput)
        self.overall_progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("•"),
            AggregateBytesColumn(field_name="visual_bytes"),
            TextColumn("•"),
            AggregateThroughputColumn(field_name="throughput_bytes"),
            TextColumn("•"),
            TimeElapsedColumn(),
        )

        # Individual file upload progress (composite bar: green=uploaded, blue=buffered, grey=pending)
        self.file_progress = Progress(
            TextColumn("  {task.description}"),
            CompositeProgressBarColumn(bar_width=40),
            DownloadColumn(),
            TextColumn("•"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        )

        # Track active tasks and completed files
        self.file_tasks: Dict[str, TaskID] = {}
        self.file_bytes_done: Dict[str, int] = {}  # Track current bytes_done per file
        self.file_bytes_resumed: Dict[str, int] = {}  # Track bytes resumed per file
        self.overall_task: Optional[TaskID] = None
        self.completed_files: set[str] = set()
        self.live: Optional[Live] = None
        self.hide_timers: Dict[str, threading.Timer] = {}

    def __enter__(self):
        """Start the live progress display."""
        # Create overall progress task tracking files completed
        # (visual_bytes shows total progress, throughput_bytes for speed calculation)
        # Don't start the timer yet - wait for first byte update
        self.overall_task = self.overall_progress.add_task(
            f"[bold]Uploading {self.num_files} files...",
            total=self.num_files,
            visual_bytes=0,
            throughput_bytes=0,
            start=False,
        )

        # Create progress group
        progress_group = Group(
            self.overall_progress,
            self.file_progress,
        )

        # Start live display
        self.live = Live(progress_group, refresh_per_second=4)
        self.live.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the live progress display and clean up timers."""
        # Cancel any pending hide timers
        for timer in self.hide_timers.values():
            timer.cancel()
        self.hide_timers.clear()

        if self.live:
            # Update final status
            if exc_type is None and self.overall_task is not None:
                self.overall_progress.update(
                    self.overall_task,
                    description=f"[bold green]✓ Completed {self.num_files} uploads",
                )

                # Hide all individual file progress bars when complete
                for task_id in self.file_tasks.values():
                    self.file_progress.stop_task(task_id)
                    self.file_progress.update(task_id, visible=False)

            self.live.__exit__(exc_type, exc_val, exc_tb)
        return False

    def _hide_completed_task(self, task_id: TaskID, key: str):
        """
        Hide a completed task from the display.

        Args:
            task_id: The task ID to hide
            key: The file key (for cleanup)
        """
        self.file_progress.stop_task(task_id)
        self.file_progress.update(task_id, visible=False)
        # Clean up timer reference
        self.hide_timers.pop(key, None)

    def callback(self, status: UploadStatus) -> None:
        """
        Get a progress callback function for the SDK.

        Returns:
            Callback function that handles UploadStatus updates
        """

        # Start the timer on first byte update (excludes setup time)
        if not self.upload_started and self.overall_task is not None:
            self.overall_progress.start_task(self.overall_task)
            self.upload_started = True

        # Track current bytes_done for this file
        self.file_bytes_done[status.key] = status.bytes_done

        # Track bytes resumed for this file (stays constant after first callback)
        if status.key not in self.file_bytes_resumed:
            self.file_bytes_resumed[status.key] = status.bytes_resumed

        # Calculate aggregate bytes excluding resumed bytes
        # - visual_bytes: total bytes done across all files (including resumed) for display
        # - throughput_bytes: only bytes uploaded in this session (for speed calculation)
        aggregate_bytes = sum(self.file_bytes_done.values())
        resumed_bytes = sum(self.file_bytes_resumed.values())
        aggregate_bytes_in_session = aggregate_bytes - resumed_bytes

        # Update overall progress with both values
        if self.overall_task is not None:
            self.overall_progress.update(
                self.overall_task,
                visual_bytes=aggregate_bytes,  # Visual progress counter (total including resumed)
                throughput_bytes=aggregate_bytes_in_session,  # For speed calculation (new bytes only)
            )

        # Get or create task for this file
        task_id = self.file_tasks.get(status.key)
        if task_id is None:
            # First progress update - create the task
            task_id = self.file_progress.add_task(
                description=f"[cyan]{status.key}",
                total=status.total_bytes or 0,
                completed=status.bytes_done,
                bytes_buffered=status.bytes_buffered,
                start=True,
            )
            self.file_tasks[status.key] = task_id
        else:
            # Update both upload and buffer progress
            self.file_progress.update(
                task_id,
                completed=status.bytes_done,
                bytes_buffered=status.bytes_buffered,
            )

        # Check if file completed (100% done)
        if status.complete and status.key not in self.completed_files:
            self.completed_files.add(status.key)

            # Mark task as complete with green checkmark
            self.file_progress.update(
                task_id,
                description=f"[green]{status.key}",
            )

            # Update overall progress (advance by 1 file)
            if self.overall_task is not None:
                self.overall_progress.advance(self.overall_task, 1)

                # If all files are complete, stop the timer to freeze throughput
                if len(self.completed_files) == self.num_files:
                    self.overall_progress.stop_task(self.overall_task)

            # For large uploads, hide completed progress bars after a delay
            if self.num_files > self.hide_completed_threshold:
                # Schedule hiding the task after a delay
                timer = threading.Timer(
                    self.hide_delay_seconds,
                    self._hide_completed_task,
                    args=(task_id, status.key),
                )
                timer.daemon = True
                timer.start()
                self.hide_timers[status.key] = timer
