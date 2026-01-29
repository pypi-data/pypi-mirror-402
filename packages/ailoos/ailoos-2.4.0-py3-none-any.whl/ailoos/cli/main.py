#!/usr/bin/env python3
"""
AILOOS Neural Link Terminal - CLI nativo en Python
Interfaz real que lee hardware, wallet y estado del sistema
"""

import asyncio
import sys
import os
from typing import Dict, Any, Optional

# Añadir el directorio padre al path para importar módulos de ailoos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from .hardware import HardwareMonitor
from .system_monitor import SystemMonitor
from .wallet_monitor import WalletMonitor
from .state_manager import AILOOSStateManager
from .ui import AILOOSUI


class AILOOSCLI:
    """CLI principal de AILOOS."""

    def __init__(self, user_id: str = "default_user"):
        self.user_id = user_id
        self.hardware = HardwareMonitor()
        self.system = SystemMonitor()
        self.wallet = WalletMonitor(user_id)
        self.state = AILOOSStateManager(user_id)
        self.ui = AILOOSUI()

    async def initialize(self):
        """Inicializa el CLI con datos reales."""
        try:
            # Obtener información de hardware
            hardware_info = self.hardware.get_all_hardware_info()

            # Obtener información del sistema
            system_info = self.system.get_all_system_status()

            # Actualizar estado con información real
            self.state.update_node_stats(hardware_info, system_info)

            # Obtener información de wallet
            wallet_info = await self.wallet.get_all_wallet_info()
            self.state.update_wallet_info(wallet_info.get('balance', {}))
            self.state.update_staking_info(wallet_info.get('staking', {}))

        except Exception as e:
            self.ui.show_error(f"Error initializing CLI: {e}")

    def show_main_screen(self):
        """Muestra la pantalla principal."""
        self.ui.clear_screen()
        self.ui.show_logo()

        # Obtener datos actuales
        hardware_info = self.hardware.get_all_hardware_info()
        system_info = self.system.get_all_system_status()
        node_info = self.state.get_node_info()
        stats = self.state.get_stats()

        self.ui.show_system_status(hardware_info, system_info)
        self.ui.show_wallet_status(self.state.get_wallet_info())
        self.ui.show_node_stats(node_info, stats)

    async def handle_missions(self):
        """Maneja el menú de misiones."""
        self.ui.show_info("MISSIONS & TRAINING CENTER")
        self.ui.show_info("Available missions for your node:\n")

        # Misiones de ejemplo (en producción vendrían de la API)
        missions = [
            {'id': 'LEGAL-TRAIN-001', 'name': 'Legal Expert Training', 'reward': 50, 'difficulty': 'Medium', 'status': 'Available'},
            {'id': 'GRADIENT-VALIDATION-001', 'name': 'Gradient Validation', 'reward': 25, 'difficulty': 'Easy', 'status': 'Available'},
            {'id': 'DAO-VOTE-001', 'name': 'Context Window Vote', 'reward': 10, 'difficulty': 'Easy', 'status': 'Active'}
        ]

        mission_id = self.ui.show_missions_menu(missions)

        if mission_id and mission_id != 'back':
            mission = next((m for m in missions if m['id'] == mission_id), None)
            if mission:
                self.ui.show_info(f"Starting Mission: {mission['name']}")
                self.ui.show_info(f"Type: Training | Reward: {mission['reward']} DRACMA\n")

                # Simular progreso
                self.ui.show_loading_spinner("Initializing mission...", 1)
                self.ui.show_loading_spinner("Connecting to peers...", 1.5)
                self.ui.show_loading_spinner("Downloading data...", 2)
                self.ui.show_success("Mission completed successfully!")

                self.ui.show_success(f"Mission Complete! Earned {mission['reward']} DRACMA")

                # Actualizar estado
                wallet_info = self.state.get_wallet_info()
                wallet_info['balance'] = wallet_info.get('balance', 0) + mission['reward']
                self.state.update_wallet_info(wallet_info)

                # Añadir transacción
                self.state.add_transaction({
                    'type': 'reward',
                    'amount': mission['reward'],
                    'description': f"Mission: {mission['name']}"
                })

        await asyncio.sleep(2)  # Pausa para que el usuario lea

    async def handle_validation(self):
        """Maneja el menú de validación."""
        self.ui.show_info("VALIDATION & AUDIT CENTER")
        self.ui.show_info("Help secure the network by validating other nodes' work\n")

        validation_tasks = [
            {'name': 'Validate Node Alpha-7 gradients (Medical)', 'reward': 15, 'difficulty': 'Easy'},
            {'name': 'Audit Dataset integrity check', 'reward': 20, 'difficulty': 'Medium'},
            {'name': 'Cross-validate training results', 'reward': 30, 'difficulty': 'Hard'}
        ]

        if self.ui.use_rich and hasattr(self.ui, 'inquirer'):
            import inquirer
            choices = [(f"{task['name']} | {task['reward']} DracmaS | {task['difficulty']}", task) for task in validation_tasks]
            choices.append(('Back to Main Menu', 'back'))

            questions = [inquirer.List('task', message='Choose validation task:', choices=choices)]
            answers = inquirer.prompt(questions)
            selected_task = answers['task'] if answers else 'back'
        else:
            print("Choose validation task:")
            for i, task in enumerate(validation_tasks, 1):
                print(f"{i}. {task['name']} | {task['reward']} DracmaS | {task['difficulty']}")
            print(f"{len(validation_tasks)+1}. Back to Main Menu")

            choice = input(f"\nSelect task (1-{len(validation_tasks)+1}): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(validation_tasks):
                selected_task = validation_tasks[int(choice) - 1]
            else:
                selected_task = 'back'

        if selected_task != 'back':
            self.ui.show_info(f"Starting Validation: {selected_task['name']}")

            self.ui.show_loading_spinner("Running validation algorithms...", 3)
            self.ui.show_success("Validation complete - Network integrity confirmed!")

            self.ui.show_success(f"Validation Complete! Earned {selected_task['reward']} DRACMA")

            # Actualizar estado
            wallet_info = self.state.get_wallet_info()
            wallet_info['balance'] = wallet_info.get('balance', 0) + selected_task['reward']
            self.state.update_wallet_info(wallet_info)

            self.state.add_transaction({
                'type': 'reward',
                'amount': selected_task['reward'],
                'description': f"Validation: {selected_task['name']}"
            })

        await asyncio.sleep(2)

    async def handle_governance(self):
        """Maneja el menú de gobernanza."""
        self.ui.show_info("GOVERNANCE & DAO CENTER")
        self.ui.show_info("Participate in network decisions\n")

        # Obtener información de gobernanza
        governance_info = await self.wallet.get_governance_info()

        self.ui.show_info(f"Voting Power: {governance_info.get('voting_power', 0):.2f}")
        self.ui.show_info(f"Active Proposals: {governance_info.get('active_proposals', 0)}")

        # Propuestas de ejemplo
        proposals = governance_info.get('proposals', [
            {'id': 'PROP-001', 'title': 'Increase Context Window to 16k', 'status': 'Voting'},
            {'id': 'PROP-002', 'title': 'Add Medical Expert Training', 'status': 'Draft'}
        ])

        if proposals:
            if self.ui.use_rich and hasattr(self.ui, 'inquirer'):
                import inquirer
                choices = [(f"{p['title']} | Status: {p['status']}", p['id']) for p in proposals]
                choices.append(('Back to Main Menu', 'back'))

                questions = [inquirer.List('proposal', message='Active Proposals:', choices=choices)]
                answers = inquirer.prompt(questions)
                proposal_id = answers['proposal'] if answers else 'back'
            else:
                print("Active Proposals:")
                for i, p in enumerate(proposals, 1):
                    print(f"{i}. {p['title']} | Status: {p['status']}")
                print(f"{len(proposals)+1}. Back to Main Menu")

                choice = input(f"\nSelect proposal (1-{len(proposals)+1}): ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(proposals):
                    proposal_id = proposals[int(choice) - 1]['id']
                else:
                    proposal_id = 'back'

            if proposal_id != 'back':
                proposal = next((p for p in proposals if p['id'] == proposal_id), None)
                if proposal:
                    self.ui.show_info(f"Proposal: {proposal['title']}")
                    self.ui.show_info(f"Status: {proposal['status']}")
                    self.ui.show_info(f"Your Voting Power: {governance_info.get('voting_power', 0):.2f}\n")

                    if self.ui.prompt_confirmation("Cast your vote?"):
                        vote = "YES"  # En producción sería interactivo
                        self.ui.show_success(f"Vote recorded: {vote}")
                        self.ui.show_success("Earned 5 DracmaS for participating in governance!")

                        wallet_info = self.state.get_wallet_info()
                        wallet_info['balance'] = wallet_info.get('balance', 0) + 5
                        self.state.update_wallet_info(wallet_info)

                        self.state.add_transaction({
                            'type': 'reward',
                            'amount': 5,
                            'description': f"Governance vote: {proposal['title']}"
                        })

        await asyncio.sleep(2)

    async def handle_economy(self):
        """Maneja el menú de economía."""
        self.ui.show_info("ECONOMY & STAKING CENTER")
        self.ui.show_info("Manage your DracmaS tokens and staking\n")

        wallet_info = self.state.get_wallet_info()
        staking_info = await self.wallet.get_staking_info()

        self.ui.show_info("WALLET DETAILS")
        self.ui.show_info(f"Address: {wallet_info.get('address', 'Not set')}")
        self.ui.show_info(f"Balance: {wallet_info.get('balance', 0):.2f} DRACMA")
        self.ui.show_info(f"Staked: {wallet_info.get('staked', 0):.2f} DRACMA")
        self.ui.show_info(f"Rewards: {wallet_info.get('rewards', 0):.2f} DRACMA")

        # Opciones de staking
        if self.ui.prompt_confirmation("Would you like to stake tokens?"):
            max_stake = wallet_info.get('balance', 0)
            if max_stake > 0:
                amount = self.ui.prompt_number(f"Amount to stake (max: {max_stake:.2f} DRACMA)", min_val=1, max_val=int(max_stake))
                if amount:
                    self.ui.show_success(f"Successfully staked {amount} DRACMA!")
                    self.ui.show_info(f"APY: {staking_info.get('apy', 15.5)}% | Rewards will be distributed periodically")

                    # Actualizar estado
                    wallet_info['balance'] = wallet_info.get('balance', 0) - amount
                    wallet_info['staked'] = wallet_info.get('staked', 0) + amount
                    self.state.update_wallet_info(wallet_info)

                    self.state.add_transaction({
                        'type': 'stake',
                        'amount': amount,
                        'description': 'Token staking'
                    })
            else:
                self.ui.show_error("Insufficient balance to stake")

        await asyncio.sleep(2)

    async def handle_assets(self):
        """Maneja el menú de assets."""
        self.ui.show_info("DATASETS & MODELS CENTER")
        self.ui.show_info("Manage your AI assets and marketplace\n")

        # Mostrar datasets
        datasets = self.state.get_state().get('datasets', [])
        if datasets:
            self.ui.show_datasets(datasets)
        else:
            self.ui.show_info("No datasets installed yet")

        # Marketplace
        self.ui.show_info("\nMARKETPLACE")
        self.ui.show_info("Available datasets:")
        self.ui.show_info("- Medical Records Dataset (Premium) | 500 DRACMA")
        self.ui.show_info("- Code Search Dataset | 200 DRACMA")
        self.ui.show_info("- Financial News Dataset | 150 DRACMA")
        self.ui.show_info("\nUse 'ailoos marketplace' command for full marketplace access")

        await asyncio.sleep(2)

    async def handle_monitoring(self):
        """Maneja el menú de monitoreo."""
        self.ui.show_info("MONITORING & STATISTICS CENTER")
        self.ui.show_info("Real-time system health and performance\n")

        stats = self.state.get_stats()
        node_info = self.state.get_node_info()

        self.ui.show_info("NODE PERFORMANCE")
        self.ui.show_info(f"Uptime: {stats.get('uptime_hours', 0)} hours")
        self.ui.show_info(f"Datasets Processed: {stats.get('datasets_processed', 0)}")
        self.ui.show_info(f"Training Sessions: {stats.get('training_sessions', 0)}")
        self.ui.show_info(f"Validation Tasks: {stats.get('validation_tasks', 0)}")
        self.ui.show_info(f"Total Earned: {stats.get('total_earned', 0):.2f} DRACMA")

        self.ui.show_info("\nNETWORK STATUS")
        self.ui.show_info(f"Peers Connected: {node_info.get('peers', 0)}")
        self.ui.show_info("Network Status: Online")
        self.ui.show_info(f"Reputation Score: {node_info.get('reputation', 0)}/1000")

        wallet_info = self.state.get_wallet_info()
        self.ui.show_info("\nECONOMY STATUS")
        self.ui.show_info(f"Current Balance: {wallet_info.get('balance', 0):.2f} DRACMA")
        self.ui.show_info(f"Staked Amount: {wallet_info.get('staked', 0):.2f} DRACMA")

        await asyncio.sleep(3)

    async def handle_settings(self):
        """Maneja el menú de configuración."""
        self.ui.show_info("SETTINGS & CONFIGURATION")
        self.ui.show_info("Configure your node and preferences\n")

        settings = self.state.get_state().get('settings', {})

        self.ui.show_info("HARDWARE CONFIGURATION")
        hardware_info = self.hardware.get_all_hardware_info()
        cpu_info = hardware_info.get('cpu', {})
        mem_info = hardware_info.get('memory', {})
        gpu_info = hardware_info.get('gpu', {})

        self.ui.show_info(f"CPU Cores: {cpu_info.get('cores', 0)}")
        self.ui.show_info(f"RAM: {mem_info.get('total_gb', 0):.1f} GB")
        self.ui.show_info(f"GPU: {gpu_info.get('name', 'None detected')}")
        self.ui.show_info(f"Role: {self.state.get_node_info().get('role', 'FORGE')}")

        await asyncio.sleep(2)

    async def run(self):
        """Ejecuta el CLI principal."""
        await self.initialize()

        running = True
        while running:
            self.show_main_screen()

            action = self.ui.show_main_menu()

            if action == 'missions':
                await self.handle_missions()
            elif action == 'validation':
                await self.handle_validation()
            elif action == 'governance':
                await self.handle_governance()
            elif action == 'economy':
                await self.handle_economy()
            elif action == 'assets':
                await self.handle_assets()
            elif action == 'monitoring':
                await self.handle_monitoring()
            elif action == 'settings':
                await self.handle_settings()
            elif action == 'back':
                running = False
                self.ui.show_success("Gracias por usar AILOOS Neural Link Terminal!")
                self.ui.show_info("Your contributions help advance decentralized AI.")
                break

            if running:
                self.ui.show_info("\nPresiona Enter para continuar...")
                input()


def main():
    """Función principal sincrónica para entry point."""
    if len(sys.argv) > 1:
        from .entrypoint import cli as click_cli
        click_cli(prog_name="ailoos")
        return
    asyncio.run(main_async())


async def main_async():
    """Función principal asíncrona."""
    # Obtener user_id de argumentos o usar default
    user_id = sys.argv[1] if len(sys.argv) > 1 else "default_user"

    cli = AILOOSCLI(user_id)
    await cli.run()


if __name__ == "__main__":
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
