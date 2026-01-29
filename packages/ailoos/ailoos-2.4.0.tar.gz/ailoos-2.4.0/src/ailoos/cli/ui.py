import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.prompt import Prompt, Confirm, IntPrompt
    from rich.columns import Columns
    from rich.align import Align
    from rich.layout import Layout
    from rich.live import Live
    import inquirer
except ImportError:
    # Fallback básico si no está rich
    class Console:
        def print(self, *args, **kwargs): print(*args)
        def clear(self): os.system('clear' if os.name == 'posix' else 'cls')

    class Table:
        def __init__(self, title=""): pass
        def add_column(self, *args, **kwargs): pass
        def add_row(self, *args): pass

    class Panel:
        def __init__(self, content, **kwargs): self.content = content

    class Text:
        def __init__(self, text, **kwargs): self.plain = text

    Prompt = input
    Confirm = lambda x: input(x + " (y/n): ").lower().startswith('y')
    IntPrompt = int

    inquirer = None


class AILOOSUI:
    """Interfaz de usuario para el CLI de AILOOS usando Rich."""

    def __init__(self):
        self.console = Console()
        self.use_rich = 'rich' in globals()

    def clear_screen(self):
        """Limpia la pantalla."""
        if self.use_rich:
            self.console.clear()
        else:
            os.system('clear' if os.name == 'posix' else 'cls')

    def show_logo(self):
        """Muestra el logo de AILOOS."""
        logo_text = """
 █████╗ ██╗██╗      ██████╗  ██████╗ ███████╗███████╗
██╔══██╗██║██║     ██╔═══██╗██╔═══██╗██╔════╝██╔════╝
███████║██║██║     ██║   ██║██║   ██║███████╗███████╗
██╔══██║██║██║     ██║   ██║██║   ██║╚════██║╚════██║
██║  ██║██║███████╗╚██████╔╝╚██████╔╝███████║███████║
╚═╝  ╚═╝╚═╝╚══════╝ ╚═════╝  ╚═════╝ ╚══════╝╚══════╝

NEURAL LINK TERMINAL v2.2.2 - DECENTRALIZED AI COMMAND CENTER
═══════════════════════════════════════════════════════════════
EmpoorioLM: Liquid Neural Swarm LLM - Sovereign AI Ecosystem
═══════════════════════════════════════════════════════════════
        """
        if self.use_rich:
            self.console.print(Panel.fit(logo_text, border_style="cyan"))
        else:
            print(logo_text)

    def show_system_status(self, hardware: Dict[str, Any], system: Dict[str, Any]):
        """Muestra el estado del sistema."""
        if self.use_rich:
            table = Table(title="📊 SYSTEM STATUS")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            # OS Info
            sys_info = hardware.get('system', {})
            os_name = sys_info.get('os', 'Unknown')
            os_version = sys_info.get('os_version', 'Unknown')
            table.add_row("OS", f"{os_name} {os_version}")

            # CPU
            cpu_info = hardware.get('cpu', {})
            cpu_name = cpu_info.get('name', 'Unknown CPU')
            cpu_usage = cpu_info.get('usage_percent', 0)
            cpu_cores = cpu_info.get('cores', 0)
            cpu_physical = cpu_info.get('physical_cores', 0)
            table.add_row("CPU", f"{cpu_name}")
            table.add_row("CPU Usage", f"{cpu_usage:.1f}% ({cpu_cores} cores, {cpu_physical} physical)")

            # RAM
            mem_info = hardware.get('memory', {})
            mem_used = mem_info.get('used_gb', 0)
            mem_total = mem_info.get('total_gb', 0)
            mem_percent = mem_info.get('usage_percent', 0)
            table.add_row("RAM", f"{mem_used:.1f}/{mem_total:.1f} GB ({mem_percent:.1f}%)")

            # Disk
            disk_info = hardware.get('disk', {})
            disk_used = disk_info.get('used_gb', 0)
            disk_total = disk_info.get('total_gb', 0)
            disk_free = disk_info.get('free_gb', 0)
            disk_percent = disk_info.get('usage_percent', 0)
            table.add_row("Disk", f"{disk_free:.1f} GB free / {disk_total:.1f} GB total ({disk_percent:.1f}% used)")

            # GPU
            gpu_info = hardware.get('gpu', {})
            gpu_name = gpu_info.get('name', 'No GPU detected')
            if gpu_name != 'No GPU detected':
                gpu_memory = gpu_info.get('memory_total_mb', 0)
                gpu_usage = gpu_info.get('usage_percent', 0)
                table.add_row("GPU", f"{gpu_name} ({gpu_memory}MB, {gpu_usage:.1f}% used)")
            else:
                table.add_row("GPU", gpu_name)

            # Uptime
            uptime = sys_info.get('uptime_formatted', 'Unknown')
            table.add_row("Uptime", uptime)

            # Network
            network_status = system.get('network', {}).get('status', 'Unknown')
            peers = system.get('peers', 0)
            total_nodes = system.get('total_nodes', 9826)  # Example total
            table.add_row("Network", f"Online - {network_status}")
            table.add_row("Peers", f"{peers}/{total_nodes}")

            self.console.print(table)
        else:
            print("📊 SYSTEM STATUS")
            sys_info = hardware.get('system', {})
            cpu_info = hardware.get('cpu', {})
            mem_info = hardware.get('memory', {})
            disk_info = hardware.get('disk', {})
            gpu_info = hardware.get('gpu', {})

            print(f"OS: {sys_info.get('os', 'Unknown')} {sys_info.get('os_version', '')}")
            print(f"CPU: {cpu_info.get('name', 'Unknown CPU')}")
            print(f"CPU Usage: {cpu_info.get('usage_percent', 0):.1f}% ({cpu_info.get('cores', 0)} cores)")
            print(f"RAM: {mem_info.get('used_gb', 0):.1f}/{mem_info.get('total_gb', 0):.1f} GB ({mem_info.get('usage_percent', 0):.1f}%)")
            print(f"Disk: {disk_info.get('free_gb', 0):.1f} GB free / {disk_info.get('total_gb', 0):.1f} GB total")
            print(f"GPU: {gpu_info.get('name', 'No GPU detected')}")
            print(f"Uptime: {sys_info.get('uptime_formatted', 'Unknown')}")
            peers = system.get('peers', 0)
            total_nodes = system.get('total_nodes', 9826)
            print(f"Peers: {peers}/{total_nodes}")

    def show_wallet_status(self, wallet_info: Dict[str, Any]):
        """Muestra el estado de la wallet."""
        balance = wallet_info.get('balance', 0.0)
        staked = wallet_info.get('staked', 0.0)
        apy = 15.5  # Default APY

        wallet_content = f"""Balance: {balance:.2f} DRACMA
Staked: {staked:.2f} DRACMA
APY: {apy}%"""

        if self.use_rich:
            self.console.print(Panel.fit(wallet_content, title="💳 WALLET STATUS", border_style="yellow"))
        else:
            print("💳 WALLET STATUS")
            print(wallet_content)

    def show_node_stats(self, node_info: Dict[str, Any], stats: Dict[str, Any]):
        """Muestra estadísticas del nodo."""
        node_id = node_info.get('id', 'Unknown')
        role = node_info.get('role', 'Unknown')
        level = node_info.get('level', 1)
        reputation = node_info.get('reputation', 0)
        total_earned = stats.get('total_earned', 0.0)

        node_content = f"""Node: {node_id}
Role: {role} (Level {level})
Reputation: {reputation}/1000
Earned: {total_earned:.2f} DRACMA"""

        if self.use_rich:
            self.console.print(Panel.fit(node_content, title="⛓ NODE STATUS", border_style="green"))
        else:
            print("⛓ NODE STATUS")
            print(node_content)

    def show_main_menu(self) -> str:
        """Muestra el menú principal y retorna la selección."""
        if inquirer and self.use_rich:
            questions = [
                inquirer.List('action',
                    message="🌟 AILOOS COMMAND CENTER",
                    choices=[
                                ('MISSIONS & TRAINING (Earn DRACMA)', 'missions'),
                                ('VALIDATION & AUDIT (Secure Network)', 'validation'),
                                ('GOVERNANCE & DAO (Vote & Decide)', 'governance'),
                                ('ECONOMY & STAKING (Manage Tokens)', 'economy'),
                                ('DATASETS & MODELS (Manage Assets)', 'assets'),
                                ('MONITORING & STATS (System Health)', 'monitoring'),
                                ('SETTINGS & CONFIG (Node Setup)', 'settings'),
                                ('─────────────────────────', 'separator'),
                                ('BACK / EXIT', 'back')
                            ],
                    carousel=True
                )
            ]
            answers = inquirer.prompt(questions)
            return answers['action'] if answers else 'back'
        else:
            # Fallback básico
            print("\nAILOOS COMMAND CENTER")
            print("1. MISSIONS & TRAINING")
            print("2. VALIDATION & AUDIT")
            print("3. GOVERNANCE & DAO")
            print("4. ECONOMY & STAKING")
            print("5. DATASETS & MODELS")
            print("6. MONITORING & STATS")
            print("7. SETTINGS & CONFIG")
            print("8. BACK / EXIT")

            choice = input("\nSelecciona una opción (1-8): ").strip()
            options = {
                '1': 'missions', '2': 'validation', '3': 'governance',
                '4': 'economy', '5': 'assets', '6': 'monitoring',
                '7': 'settings', '8': 'back'
            }
            return options.get(choice, 'back')

    def show_missions_menu(self, missions: List[Dict[str, Any]]) -> Optional[str]:
        """Muestra menú de misiones."""
        if not missions:
            missions = [
                {'id': 'LEGAL-TRAIN-001', 'name': 'Legal Expert Training', 'reward': 50, 'difficulty': 'Medium', 'status': 'Available'},
                {'id': 'GRADIENT-VALIDATION-001', 'name': 'Gradient Validation', 'reward': 25, 'difficulty': 'Easy', 'status': 'Available'}
            ]

        if inquirer and self.use_rich:
            choices = [(f"{m['name']} | {m['reward']} DracmaS | {m['difficulty']} | {m['status']}", m['id']) for m in missions]
            choices.append(('Back to Main Menu', 'back'))

            questions = [inquirer.List('mission', message='Available missions:', choices=choices)]
            answers = inquirer.prompt(questions)
            return answers['mission'] if answers else None
        else:
            print("\nMISSIONS & TRAINING CENTER")
            for i, mission in enumerate(missions, 1):
                print(f"{i}. {mission['name']} | {mission['reward']} DracmaS | {mission['difficulty']}")
            print(f"{len(missions)+1}. Back to Main Menu")

            choice = input(f"\nSelecciona misión (1-{len(missions)+1}): ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(missions):
                    return missions[idx]['id']
                elif idx == len(missions):
                    return 'back'
            return None

    def show_loading_spinner(self, message: str, duration: float = 2.0):
        """Muestra un spinner de carga."""
        if self.use_rich:
            from rich.spinner import Spinner
            from rich.live import Live
            import time

            spinner = Spinner("dots", text=message)
            with Live(spinner, refresh_per_second=10):
                time.sleep(duration)
        else:
            print(f"{message}...")
            import time
            time.sleep(duration)
            print("Completado!")

    def show_success(self, message: str):
        """Muestra mensaje de éxito."""
        if self.use_rich:
            self.console.print(f"[green]{message}[/green]")
        else:
            print(f"SUCCESS: {message}")

    def show_error(self, message: str):
        """Muestra mensaje de error."""
        if self.use_rich:
            self.console.print(f"[red]{message}[/red]")
        else:
            print(f"ERROR: {message}")

    def show_info(self, message: str):
        """Muestra mensaje informativo."""
        if self.use_rich:
            self.console.print(f"[blue]{message}[/blue]")
        else:
            print(f"INFO: {message}")

    def prompt_confirmation(self, message: str) -> bool:
        """Pide confirmación al usuario."""
        if self.use_rich:
            return Confirm.ask(message)
        else:
            response = input(f"{message} (y/n): ").strip().lower()
            return response in ['y', 'yes', 's', 'si']

    def prompt_number(self, message: str, min_val: Optional[int] = None, max_val: Optional[int] = None) -> Optional[float]:
        """Pide un número al usuario."""
        try:
            if self.use_rich:
                return IntPrompt.ask(message, min_value=min_val, max_value=max_val)
            else:
                value = float(input(message + ": "))
                if min_val is not None and value < min_val:
                    raise ValueError
                if max_val is not None and value > max_val:
                    raise ValueError
                return value
        except (ValueError, KeyboardInterrupt):
            return None

    def show_transaction_history(self, transactions: List[Dict[str, Any]]):
        """Muestra historial de transacciones."""
        if self.use_rich:
            table = Table(title="📊 TRANSACTION HISTORY")
            table.add_column("Date", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Amount", style="yellow")
            table.add_column("Description", style="white")

            for tx in transactions:
                table.add_row(
                    tx.get('date', '')[:10],
                    tx.get('type', ''),
                    f"{tx.get('amount', 0):.2f} DRACMA",
                    tx.get('description', '')
                )

            self.console.print(table)
        else:
            print("📊 TRANSACTION HISTORY")
            for tx in transactions:
                print(f"{tx.get('date', '')[:10]} | {tx.get('type', '')} | {tx.get('amount', 0):.2f} DracmaS | {tx.get('description', '')}")

    def show_datasets(self, datasets: List[Dict[str, Any]]):
        """Muestra datasets disponibles."""
        if self.use_rich:
            table = Table(title="📚 DATASETS")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Size", style="yellow")
            table.add_column("Status", style="white")
            table.add_column("Quality", style="magenta")

            for ds in datasets:
                table.add_row(
                    ds.get('id', ''),
                    ds.get('name', ''),
                    ds.get('size', ''),
                    ds.get('status', ''),
                    f"{ds.get('quality', 0)}%"
                )

            self.console.print(table)
        else:
            print("📚 DATASETS")
            for ds in datasets:
                print(f"{ds.get('id', '')} | {ds.get('name', '')} | {ds.get('size', '')} | {ds.get('status', '')} | Quality: {ds.get('quality', 0)}%")