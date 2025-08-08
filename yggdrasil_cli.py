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


@click.group()
@click.version_option(version="1.0.0", prog_name="Yggdrasil CLI")
def cli():
    """Yggdrasil - Digimon Knowledge Graph CLI.
    
    A comprehensive tool for managing the Digimon Knowledge Graph pipeline.
    """
    pass


@cli.command()
@click.option("--check-only", is_flag=True, help="Only check status without running")
def status(check_only):
    """Check the status of the entire pipeline."""
    console.print("\n[bold cyan]🦖 DIGIMON KNOWLEDGE GRAPH - PIPELINE STATUS[/bold cyan]")
    console.print("=" * 60)
    
    # Run the status check script
    try:
        result = subprocess.run([sys.executable, "check_status.py"], capture_output=True, text=True)
        console.print(result.stdout)
    except Exception as e:
        console.print(f"[red]Error checking status: {e}[/red]")


@cli.group()
def data():
    """Data management commands."""
    pass


@data.command()
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.option("--keep-cache", is_flag=True, help="Keep translation cache")
@click.option("--keep-raw", is_flag=True, help="Keep raw HTML and images")
def prune(confirm, keep_cache, keep_raw):
    """Prune collected data locally."""
    console.print("\n[bold yellow]🗑️  DATA PRUNING[/bold yellow]")
    console.print("=" * 60)
    
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
    
    # Display what will be pruned
    table = Table(title="Data to be pruned")
    table.add_column("Type", style="cyan", no_wrap=True)
    table.add_column("Path", style="magenta")
    table.add_column("Size", justify="right", style="green")
    
    for name, path, size in prune_targets:
        table.add_row(name, str(path), f"{size / 1024 / 1024:.2f} MB")
    
    table.add_row("", "", "")
    table.add_row("[bold]Total", "[bold]", f"[bold]{total_size / 1024 / 1024:.2f} MB")
    
    console.print(table)
    
    if not prune_targets:
        console.print("\n[green]No data to prune![/green]")
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
            if path.is_dir():
                shutil.rmtree(path)
                console.print(f"[green]✓[/green] Removed {name}")
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to remove {name}: {e}")
    
    console.print("\n[green]Data pruning complete![/green]")


@cli.group()
def neo4j():
    """Neo4j database management commands."""
    pass


@neo4j.command()
@click.option("--detached", "-d", is_flag=True, help="Run in detached mode")
def start(detached):
    """Start Neo4j in Docker container."""
    cli_instance = YggdrasilCLI()
    
    if not cli_instance.check_docker():
        console.print("[red]Docker is not installed or not running![/red]")
        console.print("Please install Docker: https://docs.docker.com/get-docker/")
        return
    
    console.print("\n[bold cyan]🚀 Starting Neo4j...[/bold cyan]")
    
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
        console.print("\n[green]✓ Neo4j started successfully![/green]")
        console.print(f"[cyan]Browser URL:[/cyan] http://localhost:7474")
        console.print(f"[cyan]Bolt URL:[/cyan] bolt://localhost:7687")
        console.print(f"[cyan]Username:[/cyan] neo4j")
        console.print(f"[cyan]Password:[/cyan] digimon123")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to start Neo4j: {e}[/red]")


@neo4j.command()
def stop():
    """Stop Neo4j Docker container."""
    cli_instance = YggdrasilCLI()
    
    if not cli_instance.check_docker():
        console.print("[red]Docker is not installed or not running![/red]")
        return
    
    console.print("\n[bold cyan]🛑 Stopping Neo4j...[/bold cyan]")
    
    try:
        subprocess.run(["docker-compose", "down"], check=True)
        console.print("[green]✓ Neo4j stopped successfully![/green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to stop Neo4j: {e}[/red]")


@neo4j.command()
def status():
    """Check Neo4j container status."""
    cli_instance = YggdrasilCLI()
    
    if not cli_instance.check_docker():
        console.print("[red]Docker is not installed or not running![/red]")
        return
    
    if cli_instance.check_neo4j_status():
        console.print("[green]✓ Neo4j is running[/green]")
        
        # Get container details
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=neo4j", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True,
            text=True
        )
        console.print("\n" + result.stdout)
    else:
        console.print("[yellow]Neo4j is not running[/yellow]")


@neo4j.command()
def logs():
    """View Neo4j container logs."""
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


@cli.group()
def pipeline():
    """Pipeline execution commands."""
    pass


@pipeline.command()
@click.option("--fetch-api", is_flag=True, help="Fetch URLs via API first")
@click.option("--limit", type=int, help="Limit number of pages to scrape")
def scrape(fetch_api, limit):
    """Run the web scraper."""
    console.print("\n[bold cyan]🕷️  STARTING SCRAPER[/bold cyan]")
    
    cmd = [sys.executable, "-m", "src.scraper.main"]
    if fetch_api:
        cmd.append("--fetch-api-first")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        console.print("\n[yellow]Scraping interrupted by user[/yellow]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Scraping failed: {e}[/red]")


@pipeline.command()
def parse():
    """Parse HTML files to extract data."""
    console.print("\n[bold cyan]📋 STARTING PARSER[/bold cyan]")
    
    try:
        subprocess.run([sys.executable, "-m", "src.parser.main"], check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Parsing failed: {e}[/red]")


@pipeline.command()
def translate():
    """Translate Japanese data to English."""
    console.print("\n[bold cyan]🌐 STARTING TRANSLATOR[/bold cyan]")
    
    try:
        subprocess.run([sys.executable, "-m", "src.processor.main"], check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Translation failed: {e}[/red]")


@pipeline.command()
def load():
    """Load data into Neo4j database."""
    cli_instance = YggdrasilCLI()
    
    # Check if Neo4j is running
    if not cli_instance.check_neo4j_status():
        console.print("[yellow]Neo4j is not running. Starting it now...[/yellow]")
        subprocess.run(["docker-compose", "up", "-d"], check=True)
        console.print("[green]Neo4j started![/green]")
        console.print("Waiting for Neo4j to be ready...")
        import time
        time.sleep(10)
    
    console.print("\n[bold cyan]💾 LOADING DATA INTO NEO4J[/bold cyan]")
    
    try:
        subprocess.run([sys.executable, "-m", "src.graph.loader"], check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Loading failed: {e}[/red]")


@pipeline.command()
def analyze():
    """Run analysis on the graph data."""
    console.print("\n[bold cyan]📊 RUNNING ANALYSIS[/bold cyan]")
    
    try:
        subprocess.run([sys.executable, "-m", "src.analysis.main"], check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Analysis failed: {e}[/red]")


@pipeline.command()
@click.option("--skip-scrape", is_flag=True, help="Skip scraping if data exists")
def run_all(skip_scrape):
    """Run the complete pipeline end-to-end."""
    console.print("\n[bold cyan]🚀 RUNNING COMPLETE PIPELINE[/bold cyan]")
    console.print("=" * 60)
    
    steps = [
        ("Scraping", [sys.executable, "-m", "src.scraper.main", "--fetch-api-first"], not skip_scrape),
        ("Parsing", [sys.executable, "-m", "src.parser.main"], True),
        ("Translating", [sys.executable, "-m", "src.processor.main"], True),
        ("Loading to Neo4j", [sys.executable, "-m", "src.graph.loader"], True),
        ("Running Analysis", [sys.executable, "-m", "src.analysis.main"], True),
    ]
    
    for step_name, cmd, should_run in steps:
        if should_run:
            console.print(f"\n[bold]{step_name}...[/bold]")
            try:
                subprocess.run(cmd, check=True)
                console.print(f"[green]✓ {step_name} completed![/green]")
            except subprocess.CalledProcessError as e:
                console.print(f"[red]✗ {step_name} failed: {e}[/red]")
                if click.confirm("Continue with next step?"):
                    continue
                else:
                    break
    
    console.print("\n[bold green]Pipeline execution complete![/bold green]")


@cli.command()
def interactive():
    """Start interactive menu (legacy run.sh replacement)."""
    console.print("\n[bold cyan]🦖 DIGIMON KNOWLEDGE GRAPH - INTERACTIVE MENU[/bold cyan]")
    console.print("=" * 60)
    console.print("\nThis interactive mode has been replaced by the new CLI commands.")
    console.print("\nAvailable commands:")
    console.print("  [cyan]yggdrasil status[/cyan]          - Check pipeline status")
    console.print("  [cyan]yggdrasil pipeline run-all[/cyan] - Run complete pipeline")
    console.print("  [cyan]yggdrasil neo4j start[/cyan]      - Start Neo4j database")
    console.print("  [cyan]yggdrasil data prune[/cyan]       - Clean up data files")
    console.print("\nRun [cyan]yggdrasil --help[/cyan] for all commands")


if __name__ == "__main__":
    cli()