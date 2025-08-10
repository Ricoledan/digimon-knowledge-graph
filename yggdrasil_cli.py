#!/usr/bin/env python3
"""
Yggdrasil CLI - Command-line interface for the Digimon Knowledge Graph project.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.progress import track
from rich.table import Table

console = Console()

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from src.utils.config import config


class YggdrasilCLI:
    """Main CLI class for Yggdrasil project."""
    
    def __init__(self):
        """Initialize CLI."""
        self.data_dir = Path(config.get("paths.data_dir", "./data"))
        self.docker_compose_file = Path("docker-compose.yml")
        
    def check_docker(self) -> bool:
        """Check if Docker is available."""
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
            
    def check_neo4j_status(self) -> bool:
        """Check if Neo4j container is running."""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=neo4j", "--format", "{{.Names}}"],
                capture_output=True,
                text=True
            )
            return "neo4j" in result.stdout
        except:
            return False


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.version_option(version="1.0.0", prog_name="ygg")
def cli():
    """Yggdrasil - Digimon Knowledge Graph CLI.
    
    A comprehensive tool for building a knowledge graph from digimon.net/reference.
    This CLI provides commands to scrape, parse, translate, and analyze Digimon data.
    
    \b
    Quick Start:
      ygg start        # Start Neo4j database
      ygg status       # Check current progress
      ygg run          # Run data pipeline (no analysis)
    
    \b
    All Commands:
      ygg start        # Start Neo4j database
      ygg stop         # Stop Neo4j database
      ygg status       # Check pipeline status
      ygg scrape       # Scrape Digimon data
      ygg parse        # Parse HTML to JSON
      ygg translate    # Translate to English
      ygg load         # Load into Neo4j
      ygg analyze      # Run analysis
      ygg run          # Run data pipeline (scrape→parse→translate→load)
      ygg prune        # Clean up data files
      ygg prune --include-neo4j  # Clean everything including Neo4j
      ygg logs         # View Neo4j logs
      ygg db-status    # Check Neo4j status
    
    Use 'ygg COMMAND --help' for more information on a command.
    """
    pass


@cli.command()
@click.option("--check-only", is_flag=True, help="Only check status without running")
def status(check_only):
    """Check the status of the entire pipeline.
    
    Shows the current state of:
    - Scraped data (HTML files)
    - Parsed data (JSON files)  
    - Translated data
    - Neo4j database status
    - Analysis results
    
    \b
    Examples:
      ygg status              # Full status check
      ygg status --check-only # Quick status without running scripts
    """
    console.print("\n[bold]DIGIMON KNOWLEDGE GRAPH - PIPELINE STATUS[/bold]")
    console.print("-" * 60)
    
    # Run the status check script
    try:
        result = subprocess.run([sys.executable, "check_status.py"], capture_output=True, text=True)
        console.print(result.stdout)
    except Exception as e:
        console.print(f"[red]Error checking status: {e}[/red]")


@cli.command()
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.option("--keep-cache", is_flag=True, help="Keep translation cache")
@click.option("--keep-raw", is_flag=True, help="Keep raw HTML and images")
@click.option("--include-neo4j", is_flag=True, help="Also clear Neo4j database")
def prune(confirm, keep_cache, keep_raw, include_neo4j):
    """Prune collected data locally.
    
    Removes data files to free up disk space. By default, removes:
    - Raw HTML files
    - Downloaded images
    - Processed JSON files
    - Translated data
    - Cache files
    - Results and analysis outputs
    
    \b
    Examples:
      ygg prune                         # Interactive pruning
      ygg prune --confirm               # Skip confirmation
      ygg prune --keep-cache            # Keep translation cache
      ygg prune --keep-raw              # Keep HTML and images
      ygg prune --include-neo4j         # Also clear Neo4j database
      ygg prune --confirm --include-neo4j  # Clear everything including Neo4j
    """
    console.print("\n[bold]DATA PRUNING[/bold]")
    console.print("-" * 60)
    
    cli_instance = YggdrasilCLI()
    data_dir = cli_instance.data_dir
    
    # Calculate data sizes
    total_size = 0
    prune_targets = []
    
    if not keep_raw:
        raw_html = data_dir / "raw" / "html"
        raw_images = data_dir / "raw" / "images"
        if raw_html.exists():
            size = sum(f.stat().st_size for f in raw_html.rglob("*") if f.is_file())
            prune_targets.append(("Raw HTML files", raw_html, size))
            total_size += size
        if raw_images.exists():
            size = sum(f.stat().st_size for f in raw_images.rglob("*") if f.is_file())
            prune_targets.append(("Raw images", raw_images, size))
            total_size += size
    
    processed = data_dir / "processed"
    if processed.exists():
        size = sum(f.stat().st_size for f in processed.rglob("*") if f.is_file())
        prune_targets.append(("Processed data", processed, size))
        total_size += size
    
    translated = data_dir / "translated"
    if translated.exists():
        size = sum(f.stat().st_size for f in translated.rglob("*") if f.is_file())
        prune_targets.append(("Translated data", translated, size))
        total_size += size
    
    if not keep_cache:
        cache = data_dir / "cache"
        if cache.exists():
            size = sum(f.stat().st_size for f in cache.rglob("*") if f.is_file())
            prune_targets.append(("Cache files", cache, size))
            total_size += size
    
    # Add results directory
    results_dir = Path("results")
    if results_dir.exists():
        size = sum(f.stat().st_size for f in results_dir.rglob("*") if f.is_file())
        prune_targets.append(("Results and analysis", results_dir, size))
        total_size += size
    
    # Check if Neo4j should be included
    if include_neo4j:
        prune_targets.append(("Neo4j database", None, 0))
    
    # Display what will be pruned
    table = Table(title="Data to be pruned")
    table.add_column("Type", style="cyan", no_wrap=True)
    table.add_column("Path", style="magenta")
    table.add_column("Size", justify="right", style="green")
    
    for name, path, size in prune_targets:
        if name == "Neo4j database":
            table.add_row(name, "All nodes and relationships", "N/A")
        else:
            table.add_row(name, str(path), f"{size / 1024 / 1024:.2f} MB")
    
    if total_size > 0:
        table.add_row("", "", "")
        table.add_row("[bold]Total files", "[bold]", f"[bold]{total_size / 1024 / 1024:.2f} MB")
    
    console.print(table)
    
    if not prune_targets:
        console.print("\n[dim]No data to prune[/dim]")
        return
    
    # Confirm deletion
    if not confirm:
        if not click.confirm("\nDo you want to proceed with pruning?"):
            console.print("[yellow]Pruning cancelled.[/yellow]")
            return
    
    # Perform pruning
    console.print("\n[bold]Pruning data...[/bold]")
    for name, path, size in track(prune_targets, description="Pruning"):
        try:
            if name == "Neo4j database":
                # Clear Neo4j database
                if cli_instance.check_neo4j_status():
                    result = subprocess.run(
                        ["docker", "exec", "digimon-neo4j", "cypher-shell", 
                         "-u", "neo4j", "-p", "digimon123", 
                         "MATCH (n) DETACH DELETE n"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        console.print(f"[green]Cleared Neo4j database[/green]")
                    else:
                        console.print(f"[red]Failed to clear Neo4j: {result.stderr}[/red]")
                else:
                    console.print(f"[yellow]Neo4j not running, skipping database clear[/yellow]")
            elif path and path.is_dir():
                shutil.rmtree(path)
                console.print(f"[green]Removed {name}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to remove {name}: {e}[/red]")
    
    console.print("\n[green]Data pruning complete[/green]")


@cli.command()
@click.option("--detached", "-d", is_flag=True, help="Run in detached mode")
def start(detached):
    """Start Neo4j in Docker container.
    
    Starts the Neo4j graph database using Docker Compose.
    The database will be available at:
    - Browser: http://localhost:7474
    - Bolt: bolt://localhost:7687
    - Username: neo4j
    - Password: digimon123
    
    \b
    Examples:
      ygg neo4j start       # Start in foreground (see logs)
      ygg neo4j start -d    # Start in background (detached)
    """
    cli_instance = YggdrasilCLI()
    
    if not cli_instance.check_docker():
        console.print("[red]Docker is not installed or not running![/red]")
        console.print("Please install Docker: https://docs.docker.com/get-docker/")
        return
    
    console.print("\n[bold]Starting Neo4j...[/bold]")
    
    # Check if already running
    if cli_instance.check_neo4j_status():
        console.print("[yellow]Neo4j is already running![/yellow]")
        return
    
    # Start Neo4j using docker-compose
    cmd = ["docker-compose", "up"]
    if detached:
        cmd.append("-d")
    
    try:
        subprocess.run(cmd, check=True)
        console.print("\n[green]Neo4j started successfully[/green]")
        console.print(f"[cyan]Browser URL:[/cyan] http://localhost:7474")
        console.print(f"[cyan]Bolt URL:[/cyan] bolt://localhost:7687")
        console.print(f"[cyan]Username:[/cyan] neo4j")
        console.print(f"[cyan]Password:[/cyan] digimon123")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to start Neo4j: {e}[/red]")


@cli.command()
def stop():
    """Stop Neo4j Docker container.
    
    Gracefully stops the Neo4j database container.
    Data is preserved and will be available when you start again.
    
    \b
    Example:
      ygg neo4j stop
    """
    cli_instance = YggdrasilCLI()
    
    if not cli_instance.check_docker():
        console.print("[red]Docker is not installed or not running![/red]")
        return
    
    console.print("\n[bold]Stopping Neo4j...[/bold]")
    
    try:
        subprocess.run(["docker-compose", "down"], check=True)
        console.print("[green]Neo4j stopped successfully[/green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to stop Neo4j: {e}[/red]")


@cli.command(name='db-status')
def neo4j_status():
    """Check Neo4j container status.
    
    Shows whether Neo4j is running and displays container information.
    
    \b
    Example:
      ygg neo4j status
    """
    cli_instance = YggdrasilCLI()
    
    if not cli_instance.check_docker():
        console.print("[red]Docker is not installed or not running![/red]")
        return
    
    if cli_instance.check_neo4j_status():
        console.print("[green]Neo4j is running[/green]")
        
        # Get container details
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=neo4j", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True,
            text=True
        )
        console.print("\n" + result.stdout)
    else:
        console.print("[yellow]Neo4j is not running[/yellow]")


@cli.command()
def logs():
    """View Neo4j container logs.
    
    Streams the Neo4j container logs in real-time.
    Press Ctrl+C to stop viewing logs.
    
    \b
    Example:
      ygg neo4j logs
    """
    cli_instance = YggdrasilCLI()
    
    if not cli_instance.check_docker():
        console.print("[red]Docker is not installed or not running![/red]")
        return
    
    try:
        subprocess.run(["docker-compose", "logs", "-f", "neo4j"])
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped viewing logs[/yellow]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to view logs: {e}[/red]")


@cli.command()
@click.option("--fetch-api", is_flag=True, help="Fetch URLs via API first")
@click.option("--limit", type=int, help="Limit number of pages to scrape")
def scrape(fetch_api, limit):
    """Run the web scraper.
    
    Scrapes Digimon data from digimon.net/reference.
    By default, scrapes the index page to find URLs.
    With --fetch-api, uses the API to get a complete list first.
    
    \b
    Estimated time:
      - Full scrape: ~40-50 minutes (1,249 Digimon)
      - With --limit 10: ~1 minute (for testing)
    
    \b
    Examples:
      ygg pipeline scrape              # Scrape from index page
      ygg pipeline scrape --fetch-api  # Use API for URL list (recommended)
      ygg pipeline scrape --limit 10   # Scrape only 10 pages (testing)
    """
    console.print("\n[bold]STARTING SCRAPER[/bold]")
    
    cmd = [sys.executable, "-m", "src.scraper.main"]
    if fetch_api:
        cmd.append("--fetch-api-first")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        console.print("\n[yellow]Scraping interrupted by user[/yellow]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Scraping failed: {e}[/red]")


@cli.command()
def parse():
    """Parse HTML files to extract data.
    
    Extracts structured data from scraped HTML files:
    - Japanese and English names
    - Level, Type, and Attribute
    - Profile descriptions
    - Special moves
    - Related Digimon
    
    \b
    Estimated time: ~5 minutes for all files
    
    \b
    Example:
      ygg pipeline parse
    """
    console.print("\n[bold]STARTING PARSER[/bold]")
    
    try:
        subprocess.run([sys.executable, "-m", "src.parser.main"], check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Parsing failed: {e}[/red]")


@cli.command()
def translate():
    """Translate Japanese data to English.
    
    Translates all Japanese content using Google Translate:
    - Profile descriptions
    - Special move names
    - Static terms (levels, types, attributes)
    
    Uses intelligent caching to avoid re-translating.
    
    \b
    Estimated time: ~60-90 minutes (with caching)
    
    \b
    Example:
      ygg pipeline translate
    """
    console.print("\n[bold]STARTING TRANSLATOR[/bold]")
    
    try:
        subprocess.run([sys.executable, "-m", "src.processor.main"], check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Translation failed: {e}[/red]")


@cli.command()
def load():
    """Load data into Neo4j database.
    
    Creates nodes and relationships in Neo4j:
    - Digimon nodes with all properties
    - Level, Type, Attribute nodes
    - Relationships between Digimon
    - Special moves as separate nodes
    
    Automatically starts Neo4j if not running.
    
    \b
    Estimated time: ~5 minutes
    
    \b
    Example:
      ygg pipeline load
    """
    cli_instance = YggdrasilCLI()
    
    # Check if Neo4j is running
    if not cli_instance.check_neo4j_status():
        console.print("[yellow]Neo4j is not running. Starting it now...[/yellow]")
        subprocess.run(["docker-compose", "up", "-d"], check=True)
        console.print("[green]Neo4j started![/green]")
        console.print("Waiting for Neo4j to be ready...")
        import time
        time.sleep(10)
    
    console.print("\n[bold]LOADING DATA INTO NEO4J[/bold]")
    
    try:
        subprocess.run([sys.executable, "-m", "src.graph.loader"], check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Loading failed: {e}[/red]")


@cli.command()
def analyze():
    """Run analysis on the graph data.
    
    Performs network analysis on the knowledge graph:
    - Evolution chain analysis
    - Type and attribute distributions
    - Most connected Digimon
    - Community detection
    - Centrality measures
    
    Generates visualizations and reports.
    
    \b
    Example:
      ygg pipeline analyze
    """
    console.print("\n[bold]RUNNING ANALYSIS[/bold]")
    
    try:
        subprocess.run([sys.executable, "-m", "src.analysis.main"], check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Analysis failed: {e}[/red]")


@cli.command()
@click.option("--skip-scrape", is_flag=True, help="Skip scraping if data exists")
def run(skip_scrape):
    """Run the data pipeline (scrape → parse → translate → load).
    
    Executes the data collection and processing pipeline:
    1. Scrape data from digimon.net (40-50 min)
    2. Parse HTML files (5 min)
    3. Translate to English (60-90 min)
    4. Load into Neo4j (5 min)
    
    Note: Analysis is run separately with 'ygg analyze'
    
    \b
    Total estimated time: 2-3 hours
    
    \b
    Examples:
      ygg run               # Full data pipeline
      ygg run --skip-scrape # Skip scraping step
    """
    console.print("\n[bold]RUNNING DATA PIPELINE[/bold]")
    console.print("-" * 60)
    
    steps = [
        ("Scraping", [sys.executable, "-m", "src.scraper.main", "--fetch-api-first"], not skip_scrape),
        ("Parsing", [sys.executable, "-m", "src.parser.main"], True),
        ("Translating", [sys.executable, "-m", "src.processor.main"], True),
        ("Loading to Neo4j", [sys.executable, "-m", "src.graph.loader"], True),
    ]
    
    for step_name, cmd, should_run in steps:
        if should_run:
            console.print(f"\n[bold]{step_name}...[/bold]")
            try:
                subprocess.run(cmd, check=True)
                console.print(f"[green]{step_name} completed[/green]")
            except subprocess.CalledProcessError as e:
                console.print(f"[red]{step_name} failed: {e}[/red]")
                if click.confirm("Continue with next step?"):
                    continue
                else:
                    break
    
    console.print("\n[bold green]Pipeline execution complete[/bold green]")



@cli.command()
def interactive():
    """Start interactive menu (legacy run.sh replacement)."""
    console.print("\n[bold]DIGIMON KNOWLEDGE GRAPH - INTERACTIVE MENU[/bold]")
    console.print("-" * 60)
    console.print("\nThis interactive mode has been replaced by the new CLI commands.")
    console.print("\nAvailable commands:")
    console.print("  [cyan]ygg start[/cyan]     - Start Neo4j database")
    console.print("  [cyan]ygg status[/cyan]    - Check pipeline status")
    console.print("  [cyan]ygg run[/cyan]       - Run complete pipeline")
    console.print("  [cyan]ygg analyze[/cyan]   - Run analysis")
    console.print("  [cyan]ygg prune[/cyan]     - Clean up data files")
    console.print("\nRun [cyan]ygg --help[/cyan] for all commands")


if __name__ == "__main__":
    cli()