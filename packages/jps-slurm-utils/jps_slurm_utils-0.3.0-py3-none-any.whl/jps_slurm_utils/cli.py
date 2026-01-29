"""CLI interface for jps-slurm-job-audit using Typer."""

import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from jps_slurm_utils import __version__
from jps_slurm_utils.audit import AuditEngine
from jps_slurm_utils.config import AuditConfig
from jps_slurm_utils.logger import setup_logger

app = typer.Typer(
    name="jps-slurm-job-audit",
    help="Audit SLURM HPC jobs from static artifacts (stdout/stderr/logs)",
    add_completion=False,
)

console = Console()


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"jps-slurm-job-audit version: {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """Main callback for shared options."""
    pass


@app.command()
def single(
    job_dir: Path = typer.Option(
        ...,
        "--job-dir",
        "-j",
        help="Directory containing job artifacts",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
    ),
    outdir: Optional[Path] = typer.Option(
        None,
        "--outdir",
        "-o",
        help="Output directory for reports (default: /tmp/<user>/jps-slurm-job-audit/<timestamp>)",
    ),
    logfile: Optional[Path] = typer.Option(
        None,
        "--logfile",
        "-l",
        help="Log file path (default: <outdir>/audit.log)",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress console output",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Enable verbose logging",
    ),
    glob_pattern: Optional[str] = typer.Option(
        None,
        "--glob",
        help="Glob pattern to filter files (e.g., '*.out')",
    ),
    include_pattern: Optional[str] = typer.Option(
        None,
        "--include",
        help="Regex pattern for files to include",
    ),
    exclude_pattern: Optional[str] = typer.Option(
        None,
        "--exclude",
        help="Regex pattern for files to exclude",
    ),
    rules: Optional[List[Path]] = typer.Option(
        None,
        "--rules",
        "-r",
        help="Path to rule pack YAML file(s). Can be specified multiple times.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
) -> None:
    """Audit a single SLURM job directory."""
    # Setup output directory
    if outdir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        import getpass

        user = getpass.getuser()
        outdir = Path(f"/tmp/{user}/jps-slurm-job-audit/{timestamp}")

    outdir.mkdir(parents=True, exist_ok=True)

    # Setup logging
    if logfile is None:
        logfile = outdir / "audit.log"

    logger = setup_logger(logfile, verbose=verbose, quiet=quiet)
    logger.info(f"Starting audit of job directory: {job_dir}")
    logger.info(f"Output directory: {outdir}")

    # Create configuration
    config = AuditConfig(
        job_dir=job_dir,
        outdir=outdir,
        glob_pattern=glob_pattern,
        include_pattern=include_pattern,
        exclude_pattern=exclude_pattern,
        rule_paths=rules or [],
    )

    # Run audit
    engine = AuditEngine(config, logger)
    try:
        report = engine.audit_single()

        # Save report
        report_path = outdir / "report.json"
        report.save_json(report_path)

        if not quiet:
            console.print(f"\n[green]✓[/green] Audit complete!")
            console.print(f"[blue]Report saved to:[/blue] {report_path}")
            _display_summary(report)

        # Exit code based on status
        if report.final_status == "FAIL":
            sys.exit(2)
        elif report.final_status == "WARN":
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        logger.error(f"Audit failed: {e}", exc_info=True)
        if not quiet:
            console.print(f"[red]✗[/red] Audit failed: {e}")
        sys.exit(3)


@app.command()
def batch(
    path_list: Path = typer.Option(
        ...,
        "--path-list",
        "-p",
        help="File containing list of job directories (one per line)",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    outdir: Optional[Path] = typer.Option(
        None,
        "--outdir",
        "-o",
        help="Output directory for reports (default: /tmp/<user>/jps-slurm-job-audit/<timestamp>)",
    ),
    logfile: Optional[Path] = typer.Option(
        None,
        "--logfile",
        "-l",
        help="Log file path (default: <outdir>/audit.log)",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress console output",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Enable verbose logging",
    ),
    only_status: Optional[str] = typer.Option(
        None,
        "--only",
        help="Filter results by status (OK/WARN/FAIL)",
    ),
) -> None:
    """Audit multiple SLURM job directories in batch."""
    # Setup output directory
    if outdir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        import getpass

        user = getpass.getuser()
        outdir = Path(f"/tmp/{user}/jps-slurm-job-audit/{timestamp}")

    outdir.mkdir(parents=True, exist_ok=True)

    # Setup logging
    if logfile is None:
        logfile = outdir / "audit.log"

    logger = setup_logger(logfile, verbose=verbose, quiet=quiet)
    logger.info(f"Starting batch audit from path list: {path_list}")
    logger.info(f"Output directory: {outdir}")

    # Read job directories
    with open(path_list, "r") as f:
        job_dirs = [Path(line.strip()) for line in f if line.strip()]

    logger.info(f"Found {len(job_dirs)} job directories to audit")

    # Run batch audit
    reports = []
    for idx, job_dir in enumerate(job_dirs, 1):
        if not quiet:
            console.print(f"[cyan]Processing {idx}/{len(job_dirs)}:[/cyan] {job_dir}")

        config = AuditConfig(job_dir=job_dir, outdir=outdir)
        engine = AuditEngine(config, logger)

        try:
            report = engine.audit_single()
            reports.append(report)

            # Save individual report
            job_report_path = outdir / f"report_{idx}.json"
            report.save_json(job_report_path)

        except Exception as e:
            logger.error(f"Failed to audit {job_dir}: {e}")
            if not quiet:
                console.print(f"[red]✗[/red] Failed: {e}")

    # Generate summary
    if reports:
        summary_path = outdir / "summary.json"
        _save_batch_summary(reports, summary_path, only_status)

        if not quiet:
            console.print(f"\n[green]✓[/green] Batch audit complete!")
            console.print(f"[blue]Summary saved to:[/blue] {summary_path}")
            _display_batch_summary(reports, only_status)

    sys.exit(0)


def _display_summary(report) -> None:
    """Display a summary of the audit report."""
    table = Table(title="Audit Summary")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Job ID", report.job_metadata.job_id or "Unknown")
    table.add_row("Job Name", report.job_metadata.job_name or "Unknown")
    table.add_row("Status", _status_style(report.final_status))
    table.add_row("Findings", str(len(report.findings)))
    table.add_row("Files Scanned", str(len(report.discovered_files)))

    console.print(table)

    if report.findings:
        console.print("\n[yellow]Findings:[/yellow]")
        for finding in report.findings[:5]:  # Show top 5
            console.print(
                f"  • [{_severity_color(finding.severity)}]{finding.category}[/]: {finding.message}"
            )
        if len(report.findings) > 5:
            console.print(f"  ... and {len(report.findings) - 5} more")


def _display_batch_summary(reports, only_status: Optional[str] = None) -> None:
    """Display a summary of batch audit results."""
    filtered = reports
    if only_status:
        filtered = [r for r in reports if r.final_status == only_status.upper()]

    status_counts = {}
    for report in reports:
        status_counts[report.final_status] = status_counts.get(report.final_status, 0) + 1

    console.print(f"\n[cyan]Total jobs audited:[/cyan] {len(reports)}")
    for status, count in sorted(status_counts.items()):
        console.print(f"  {_status_style(status)}: {count}")

    if only_status and filtered:
        console.print(f"\n[cyan]Filtered results ({only_status}):[/cyan] {len(filtered)} jobs")


def _save_batch_summary(reports, path: Path, only_status: Optional[str] = None) -> None:
    """Save batch summary to JSON."""
    import json

    filtered = reports
    if only_status:
        filtered = [r for r in reports if r.final_status == only_status.upper()]

    summary = {
        "total_jobs": len(reports),
        "status_counts": {},
        "jobs": [
            {
                "job_id": r.job_metadata.job_id,
                "job_name": r.job_metadata.job_name,
                "status": r.final_status,
                "findings_count": len(r.findings),
            }
            for r in filtered
        ],
    }

    for report in reports:
        status = report.final_status
        summary["status_counts"][status] = summary["status_counts"].get(status, 0) + 1

    with open(path, "w") as f:
        json.dump(summary, f, indent=2)


def _status_style(status: str) -> str:
    """Return styled status string."""
    styles = {
        "OK": "[green]OK[/green]",
        "WARN": "[yellow]WARN[/yellow]",
        "FAIL": "[red]FAIL[/red]",
    }
    return styles.get(status, status)


def _severity_color(severity: str) -> str:
    """Return color for severity."""
    colors = {
        "INFO": "blue",
        "WARN": "yellow",
        "ERROR": "orange1",
        "FATAL": "red",
    }
    return colors.get(severity, "white")


# Rules management commands
rules_app = typer.Typer(help="Manage and test rule packs")
app.add_typer(rules_app, name="rules")


@rules_app.command("list")
def rules_list(
    rules: Optional[List[Path]] = typer.Option(
        None,
        "--rules",
        "-r",
        help="Path to rule pack YAML file(s). Can be specified multiple times.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
) -> None:
    """List all rules from loaded rule packs."""
    import logging
    from jps_slurm_utils.rule_engine import RuleEngine

    logger = logging.getLogger("rules")
    engine = RuleEngine(logger)

    if not rules:
        console.print("[yellow]No rule packs specified. Use --rules to load rule packs.[/yellow]")
        console.print("\nExample:")
        console.print("  jps-slurm-job-audit rules list --rules examples/rules/builtin.yaml")
        raise typer.Exit(1)

    # Load rule packs
    for rule_path in rules:
        try:
            engine.load_rule_pack(rule_path)
        except Exception as e:
            console.print(f"[red]Error loading {rule_path}:[/red] {e}")
            raise typer.Exit(1)

    # Display rules
    all_rules = engine.get_all_rules()
    if not all_rules:
        console.print("[yellow]No rules loaded.[/yellow]")
        raise typer.Exit(0)

    console.print(f"\n[cyan]Loaded {len(all_rules)} rules from {len(engine.get_rule_packs())} pack(s):[/cyan]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", width=15)
    table.add_column("Category", style="blue", width=12)
    table.add_column("Severity", width=10)
    table.add_column("Description", width=50)

    for rule in all_rules:
        severity_style = _severity_color(rule.severity)
        table.add_row(
            rule.id,
            rule.category,
            f"[{severity_style}]{rule.severity}[/{severity_style}]",
            rule.description,
        )

    console.print(table)

    # Show rule pack summary
    console.print("\n[cyan]Rule Packs:[/cyan]")
    for pack in engine.get_rule_packs():
        console.print(f"  • {pack.name} (v{pack.version}): {len(pack.rules)} rules")
        if pack.description:
            console.print(f"    {pack.description}")


@rules_app.command("test")
def rules_test(
    rules: List[Path] = typer.Option(
        ...,
        "--rules",
        "-r",
        help="Path to rule pack YAML file(s). Can be specified multiple times.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    input_file: Path = typer.Option(
        ...,
        "--input",
        "-i",
        help="Input file to test rules against",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed match information",
    ),
) -> None:
    """Test rule packs against a sample input file."""
    import logging
    from jps_slurm_utils.rule_engine import RuleEngine

    logger = logging.getLogger("rules")
    engine = RuleEngine(logger)

    # Load rule packs
    console.print(f"[cyan]Loading rule packs...[/cyan]")
    for rule_path in rules:
        try:
            pack = engine.load_rule_pack(rule_path)
            console.print(f"  ✓ {pack.name}: {len(pack.rules)} rules")
        except Exception as e:
            console.print(f"[red]Error loading {rule_path}:[/red] {e}")
            raise typer.Exit(1)

    # Apply rules to input file
    console.print(f"\n[cyan]Testing against:[/cyan] {input_file}")
    findings = engine.apply_rules([input_file])

    if not findings:
        console.print("\n[green]✓ No issues detected.[/green]")
        raise typer.Exit(0)

    # Display findings
    console.print(f"\n[yellow]Found {len(findings)} issue(s):[/yellow]\n")

    for i, finding in enumerate(findings, 1):
        severity_style = _severity_color(finding.severity)
        console.print(f"{i}. [{severity_style}]{finding.severity}[/{severity_style}] - {finding.id}: {finding.message}")
        
        if finding.evidence:
            evidence = finding.evidence[0]
            console.print(f"   File: {evidence.file} (line {evidence.line_start})")
            console.print(f"   Match: {evidence.excerpt[:100]}...")
            
            if verbose and finding.remediation:
                console.print(f"\n   [cyan]Remediation:[/cyan]")
                for line in finding.remediation.strip().split('\n'):
                    console.print(f"   {line}")
        
        console.print()

    raise typer.Exit(1 if any(f.severity in ["ERROR", "FATAL"] for f in findings) else 0)


if __name__ == "__main__":
    app()
