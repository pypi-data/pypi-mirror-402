"""Command-line interface for thinkpdf with rich progress and parallel batch."""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional

from .core.pipeline import pdf_to_markdown
from .core.models import Options
from .cache.cache_manager import CacheManager
from .logger import logger
from . import __version__

try:
    from rich.console import Console
    from rich.progress import (
        Progress,
        SpinnerColumn,
        TextColumn,
        BarColumn,
        TaskProgressColumn,
    )
    from rich.panel import Panel

    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    Console = None


console = Console() if HAS_RICH else None


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="thinkpdf",
        description="thinkpdf - PDF to Markdown Converter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  thinkpdf document.pdf                    # Convert single file
  thinkpdf document.pdf -o output.md       # Specify output path
  thinkpdf folder/ --batch                 # Convert all PDFs in folder
  thinkpdf folder/ --batch --workers 4     # Parallel batch with 4 workers
  thinkpdf setup                           # Configure MCP for Cursor/Antigravity
        """,
    )

    parser.add_argument(
        "input", nargs="?", help="PDF file or folder to convert (or 'setup' command)"
    )
    parser.add_argument(
        "-o", "--output", help="Output markdown file or folder", default=None
    )
    parser.add_argument(
        "--batch", action="store_true", help="Batch convert all PDFs in a folder"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of parallel workers for batch (default: 1)",
    )
    parser.add_argument(
        "--no-cache", action="store_true", help="Skip cache and force re-conversion"
    )
    parser.add_argument(
        "--ocr",
        choices=["off", "auto", "force"],
        default="auto",
        help="OCR mode (default: auto)",
    )
    parser.add_argument(
        "--export-images", action="store_true", help="Export images to _assets folder"
    )
    parser.add_argument("--password", help="Password for encrypted PDFs", default=None)
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--version", action="version", version=f"thinkpdf {__version__}")

    return parser


def setup_mcp() -> bool:
    """Show MCP configuration for Cursor and Antigravity."""
    import json

    mcp_config = {
        "thinkpdf": {"command": "python", "args": ["-m", "thinkpdf.mcp_server"]}
    }

    print("=" * 50)
    print("thinkpdf MCP Setup")
    print("=" * 50)
    print()
    print("Add this to your mcp.json file:")
    print()
    print("For Cursor:   ~/.cursor/mcp.json")
    print("For Antigravity: ~/.gemini/antigravity/mcp.json")
    print()
    print("-" * 50)
    print()
    print('Inside "mcpServers": { ... }, add:')
    print()
    print(json.dumps(mcp_config, indent=2))
    print()
    print("-" * 50)
    print()
    print("After adding, restart your IDE.")
    print()
    print("Available tools:")
    print("  - read_pdf: Read PDF content directly")
    print("  - convert_pdf: Convert PDF to markdown file")
    print("  - get_document_info: Get PDF metadata")
    print()
    return True


def convert_single_file(
    input_path: Path,
    output_path: Optional[Path],
    options: Options,
    use_cache: bool,
    password: Optional[str],
    verbose: bool,
    progress_callback=None,
) -> tuple[bool, str, int]:
    """Convert a single PDF file.

    Returns:
        Tuple of (success, message, word_count)
    """
    if output_path is None:
        output_path = input_path.with_suffix(".md")

    cache = CacheManager() if use_cache else None

    if cache:
        cached = cache.get_cached(input_path)
        if cached:
            output_path.write_text(cached, encoding="utf-8")
            return True, "cached", len(cached.split())

    try:

        def progress(done: int, total: int) -> None:
            if progress_callback:
                progress_callback(done, total)

        markdown = pdf_to_markdown(
            input_pdf=str(input_path),
            output_md=str(output_path),
            options=options,
            progress_cb=progress if verbose else None,
            pdf_password=password,
        )

        if cache:
            cache.cache(input_path, markdown)

        word_count = len(markdown.split())
        return True, "converted", word_count

    except Exception as e:
        logger.error(f"Failed to convert {input_path.name}: {e}")
        return False, str(e), 0


def convert_with_progress(
    input_path: Path,
    output_path: Optional[Path],
    options: Options,
    use_cache: bool,
    password: Optional[str],
    verbose: bool,
) -> bool:
    """Convert a single file with rich progress bar."""
    if HAS_RICH and console:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"Converting {input_path.name}", total=100)

            def update_progress(done: int, total: int):
                pct = (done * 100) // total if total > 0 else 0
                progress.update(task, completed=pct)

            success, msg, word_count = convert_single_file(
                input_path,
                output_path,
                options,
                use_cache,
                password,
                verbose,
                progress_callback=update_progress,
            )

            progress.update(task, completed=100)

        if success:
            if msg == "cached":
                console.print(
                    f"[green]OK[/green] {input_path.name} [dim](from cache)[/dim]"
                )
            else:
                console.print(
                    f"[green]OK[/green] {input_path.name} [dim]({word_count} words)[/dim]"
                )
        else:
            console.print(f"[red]FAIL[/red] {input_path.name} [red]{msg}[/red]")

        return success
    else:
        success, msg, word_count = convert_single_file(
            input_path,
            output_path,
            options,
            use_cache,
            password,
            verbose,
        )
        if success:
            logger.info(f"Converted -> {input_path.name} ({word_count} words)")
        else:
            logger.error(f"Failed: {msg}")
        return success


def convert_batch_parallel(
    input_dir: Path,
    output_dir: Optional[Path],
    options: Options,
    use_cache: bool,
    password: Optional[str],
    verbose: bool,
    workers: int = 1,
) -> int:
    """Convert all PDFs in a folder with parallel workers."""
    pdf_files = list(input_dir.glob("*.pdf"))

    if not pdf_files:
        logger.warning(f"No PDF files found in: {input_dir}")
        return 0

    if output_dir is None:
        output_dir = input_dir
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0

    if HAS_RICH and console:
        console.print(
            Panel(
                f"[bold]Batch Conversion[/bold]\n"
                f"Files: {len(pdf_files)} PDFs\n"
                f"Workers: {workers}\n"
                f"Source: {input_dir}",
                title="thinkpdf",
                expand=False,
            )
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[progress.percentage]{task.completed}/{task.total}"),
            console=console,
        ) as progress:
            main_task = progress.add_task("Converting...", total=len(pdf_files))

            def process_file(pdf_file: Path) -> tuple[Path, bool, str, int]:
                out = output_dir / pdf_file.with_suffix(".md").name
                success, msg, wc = convert_single_file(
                    pdf_file, out, options, use_cache, password, verbose
                )
                return pdf_file, success, msg, wc

            if workers > 1:
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    futures = {executor.submit(process_file, f): f for f in pdf_files}

                    for future in as_completed(futures):
                        pdf_file, success, msg, wc = future.result()
                        progress.update(main_task, advance=1)

                        if success:
                            success_count += 1
                            status = (
                                "[dim](cached)[/dim]"
                                if msg == "cached"
                                else f"[dim]({wc} words)[/dim]"
                            )
                            console.print(
                                f"  [green]OK[/green] {pdf_file.name} {status}"
                            )
                        else:
                            console.print(f"  [red]FAIL[/red] {pdf_file.name}")
            else:
                for pdf_file in pdf_files:
                    _, success, msg, wc = process_file(pdf_file)
                    progress.update(main_task, advance=1)

                    if success:
                        success_count += 1
                        status = (
                            "[dim](cached)[/dim]"
                            if msg == "cached"
                            else f"[dim]({wc} words)[/dim]"
                        )
                        console.print(f"  [green]OK[/green] {pdf_file.name} {status}")
                    else:
                        console.print(f"  [red]FAIL[/red] {pdf_file.name}")

        console.print(
            f"\n[bold green]Completed:[/bold green] {success_count}/{len(pdf_files)} files"
        )
    else:
        logger.info(f"Batch converting {len(pdf_files)} files from: {input_dir}")

        for pdf_file in pdf_files:
            out = output_dir / pdf_file.with_suffix(".md").name
            success, _, _ = convert_single_file(
                pdf_file, out, options, use_cache, password, verbose
            )
            if success:
                success_count += 1

        logger.info(f"Completed: {success_count}/{len(pdf_files)} files converted")

    return success_count


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point."""
    parser = create_parser()
    parsed = parser.parse_args(args)

    if parsed.input == "setup":
        return 0 if setup_mcp() else 1

    if not parsed.input:
        parser.print_help()
        return 0

    input_path = Path(parsed.input)

    if not input_path.exists():
        logger.error(f"Input not found: {input_path}")
        return 1

    options = Options(
        ocr_mode=parsed.ocr,
        export_images=parsed.export_images,
    )

    use_cache = not parsed.no_cache
    workers = max(1, parsed.workers)

    if input_path.is_dir() or parsed.batch:
        if not input_path.is_dir():
            logger.error("--batch requires a directory")
            return 1

        output_dir = Path(parsed.output) if parsed.output else None
        success = convert_batch_parallel(
            input_path,
            output_dir,
            options,
            use_cache,
            parsed.password,
            parsed.verbose,
            workers,
        )
        return 0 if success > 0 else 1
    else:
        output_path = Path(parsed.output) if parsed.output else None
        success = convert_with_progress(
            input_path,
            output_path,
            options,
            use_cache,
            parsed.password,
            parsed.verbose,
        )
        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
