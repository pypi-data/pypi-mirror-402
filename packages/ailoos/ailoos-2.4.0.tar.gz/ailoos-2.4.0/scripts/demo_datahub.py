#!/usr/bin/env python3
"""
DEMO: FEDERATED NUTRITION (DATAHUB)
===================================
Este script demuestra el funcionamiento del Módulo 8 (DataHub) sin necesidad de abrir el terminal interactivo.
Simula el ciclo completo: Descubrimiento -> Ingesta (IPFS) -> Digestión (Trainer) -> Recompensa.
"""

import asyncio
import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from ailoos.datahub.nutrition_client import NutritionClient

# Configurar logs para que se vean bonitos
logging.basicConfig(level=logging.ERROR) # Ocultar logs internos ruidosos para la demo
logger = logging.getLogger("ailoos.datahub")
logger.setLevel(logging.INFO)

console = Console()

async def run_demo():
    console.print(Panel("[bold green]🧬 AILOOS FEDERATED NUTRITION DEMO[/bold green]", subtitle="v2.2.24"))
    
    # 1. Inicializar Cliente
    console.print("[info]⚙️  Inicializando NutritionClient (conectando a DHT simulada)...[/info]")
    client = NutritionClient()
    await asyncio.sleep(1) # Drama pause
    
    # 2. Listar Dietas
    console.print("\n[bold cyan]📋 Paso 1: Descubriendo Misiones de Datos (Diets)[/bold cyan]")
    diets = await client.list_available_diets()
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Mission ID")
    table.add_column("Nombre")
    table.add_column("Tipo")
    table.add_column("Recompensa")
    table.add_column("Shards Disp.")
    
    for diet in diets:
        table.add_row(
            diet.mission_id,
            diet.name,
            diet.data_type,
            f"{diet.reward_per_shard} DR",
            str(diet.total_shards)
        )
    console.print(table)
    
    # 3. Comer (Consumir Shard)
    target_diet = diets[0] # Elegimos la primera (Legal)
    console.print(f"\n[bold cyan]🍽️  Paso 2: Consumiendo '{target_diet.name}'[/bold cyan]")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            
            task = progress.add_task("[green]Procesando Ciclo de Nutrición...", total=100)
            
            # Simulamos el progreso visualmente mientras el cliente hace el trabajo real por debajo
            # Como client.consume_shard es atómico, lo lanzamos y actualizamos la barra fake
            # para dar feedback visual de los pasos internos (Descarga -> Train -> Encrypt)
            
            nutrition_task = asyncio.create_task(client.consume_shard(target_diet))
            
            while not nutrition_task.done():
                await asyncio.sleep(0.1)
                progress.update(task, advance=2)
                
            result = await nutrition_task
            progress.update(task, completed=100)
            
        # 4. Resultados
        console.print(Panel(f"""
[bold green]✅ Digestión Exitosa![/bold green]

📦 [bold]Shard ID:[/bold] {result['shard_cid']}
🧠 [bold]Entrenamiento:[/bold] Session {result['training_session']}
📉 [bold]Mejora Loss:[/bold] {result['loss_improvement']:.4f}
💰 [bold]Recompensa:[/bold] {result['reward_earned']} DRACMA
🔗 [bold]Proof-of-Nutrition:[/bold] {result['tx_hash']}
""", title="Reporte de Nutrición", border_style="green"))

    except Exception as e:
        console.print(f"[bold red]❌ Error en la demo: {e}[/bold red]")

if __name__ == "__main__":
    asyncio.run(run_demo())
