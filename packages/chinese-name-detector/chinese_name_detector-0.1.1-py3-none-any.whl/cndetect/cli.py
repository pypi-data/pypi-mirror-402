import typer
import sys
import os
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
import pandas as pd
import yaml
from . import __version__, detect, detect_batch
from .config import settings, Settings
from .logger import logger, setup_logger

app = typer.Typer(help="Chinese Name Detection Tool", invoke_without_command=True)
console = Console()

@app.command()
def single(text: str):
    """检测单条文本"""
    res = detect(text)
    table = Table(title="Detection Result")
    table.add_column("Original Text", style="cyan")
    table.add_column("Has Chinese", style="magenta")
    table.add_column("Family Name", style="green")
    
    cn_status = "✅" if res.has_chinese else "❌"
    fn_status = res.family_name if res.family_name else "[dim]None[/dim]"
    
    table.add_row(res.text, cn_status, fn_status)
    console.print(table)

@app.command()
def batch(
    file: Path = typer.Argument(..., help="Path to Excel file", exists=True, file_okay=True, dir_okay=False, readable=True),
    column: str = typer.Option(None, "--column", "-c", help="Column name to scan"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output path")
):
    """批量扫描 Excel 指定列"""
    col_name = column or settings.excel.column
    
    try:
        df = pd.read_excel(file)
    except Exception as e:
        console.print(f"[red]❌ Error reading file: {e}[/red]")
        sys.exit(2)
        
    if col_name not in df.columns:
        console.print(f"[red]❌ Column '{col_name}' not found.[/red]")
        sys.exit(2)

    import time
    start_time = time.time()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task(f"Processing {file.name}...", total=len(df))
        
        # We use detect_batch logic but with progress update
        # To avoid overhead of apply on large data, we could chunk it if needed
        # For MVP, we'll just use a loop or apply with progress callback
        
        from .core import get_detector
        detector = get_detector()
        
        results = []
        for val in df[col_name]:
            res = detector.detect(str(val))
            results.append(res.text if res.has_chinese else None)
            progress.advance(task)
            
    df["Chinese"] = results
    
    # Save output
    if output:
        out_path = output
    else:
        suffix = settings.excel.output_suffix
        out_path = file.parent / f"{file.stem}{suffix}.xlsx"
        
    df.to_excel(out_path, index=False)
    
    elapsed = time.time() - start_time
    hit_count = df["Chinese"].notna().sum()
    
    console.print(f"\n[green]✅ Batch scan completed![/green]")
    console.print(f"Total rows: {len(df)}")
    console.print(f"Hits: {hit_count}")
    console.print(f"Saved to: [bold]{out_path}[/bold]")
    console.print(f"Time elapsed: {elapsed:.2f}s")

@app.command()
def config(output_dir: Path = typer.Option(".", "--output-dir", "-o", help="Directory to save template")):
    """生成配置模板"""
    template = {
        "family_name_path": None,
        "excel": {
            "paths": ["data.xlsx"],
            "column": "Name",
            "output_suffix": "_cn",
            "output_dir": "./result"
        },
        "log": {
            "level": "INFO",
            "file": "./logs/cndetect.log",
            "rotation": "1 MB",
            "retention": "7 days",
            "redact_names": True
        }
    }
    
    out_file = output_dir / "cndetect.yaml"
    with open(out_file, "w", encoding="utf-8") as f:
        yaml.dump(template, f, sort_keys=False)
        
    console.print(f"[green]✅ Config template generated at: {out_file}[/green]")

@app.command()
def run(config_path: Path = typer.Option(..., "--config", "-c", help="Path to YAML config")):
    """按 YAML 配置执行批量任务"""
    if not config_path.exists():
        console.print(f"[red]❌ Config file not found: {config_path}[/red]")
        sys.exit(2)
        
    cfg = Settings.load_settings(str(config_path))
    setup_logger(level=cfg.log.level, log_file=cfg.log.file)
    
    if not cfg.excel.paths:
        console.print("[yellow]⚠️ No paths specified in config.[/yellow]")
        return
        
    for p in cfg.excel.paths:
        path = Path(p)
        if not path.exists():
            console.print(f"[red]❌ File not found: {p}[/red]")
            continue
        
        # Reuse batch logic
        batch(file=path, column=cfg.excel.column)

@app.callback()
def main(version: bool = typer.Option(None, "--version", "-v", is_eager=True, help="Show version")):
    if version:
        console.print(f"cndetect version: {__version__}")
        raise typer.Exit()

if __name__ == "__main__":
    app()
