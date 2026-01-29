#!/usr/bin/env python3
"""
VERIFY PUBLISHER FLOW
=====================
Simulates the "Menu 5 -> Publish" action programmatically.
"""
import sys
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

# Importar el Singleton del Manager
from ailoos.data.dataset_manager import dataset_manager

console = Console()

def run_publisher_test():
    console.print(Panel("[bold cyan]🚀 TESTING DATAHUB PUBLISHER (MENU 5)[/bold cyan]"))
    
    project_root = Path(__file__).parent.parent
    inbox = project_root / "data" / "inbox"
    files = list(inbox.glob("*.txt"))
    
    if not files:
        console.print("[red]No files in inbox![/red]")
        return

    console.print(f"[info]Found {len(files)} files in inbox: {[f.name for f in files]}[/info]\n")
    
    for target in files:
        if target.name == "leyes_españa_v1.txt": continue # Skip the old one if needed, or process all

        console.print(f"[bold yellow]Processing: {target.name}[/bold yellow]")
        
        # Simulamos la metadata que pone la terminal
        meta = {
            "publisher": "TEST_SCRIPT_BOT",
            "source_node": "local_dev_node",
            "timestamp": time.time()
        }
        
        try:
            # LLAMADA AL SDK REAL
            start = time.time()
            result = dataset_manager.process_text_file(
                file_path=str(target),
                dataset_name=target.stem,
                shard_size_mb=1.0, 
                metadata=meta
            )
            duration = time.time() - start
            
            # Imprimir reporte como en la terminal
            console.print(Panel(f"""
[bold green]✅ Success![/bold green]
Dataset: {result['dataset_name']}
Shards: {result['num_shards']}
Size: {result['total_size_mb']:.5f} MB
PII Scrubbed: {result['pii_scrubbed']}
Quality: {result['quality_score']}
Duration: {duration:.3f}s
Root CIDs: {result['shard_cids']}
""", title="Supply Chain Report", border_style="green"))
            
        except Exception as e:
            console.print(f"[bold red]❌ Failed: {e}[/bold red]")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_publisher_test()
