"""
Status command for Wally Dev CLI.

Shows current workspace status and checked out norms.
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..config import LocalConfig
from ..constants import EXIT_SUCCESS
from ..workspace import WorkspaceManager

console = Console()


@click.command("status")
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Mostra informações detalhadas",
)
def status(verbose: bool) -> int:
    """
    Mostra o status do workspace local.

    Lista normas em checkout e informações do usuário logado.

    Exemplo:
        wally-dev status
        wally-dev status --verbose
    """
    config = LocalConfig()
    workspace = WorkspaceManager()

    # Login status
    if config.is_logged_in:
        console.print(
            Panel(
                "[green]✓ Logado[/green]",
                title="[bold cyan]Status de Autenticação[/bold cyan]",
                border_style="cyan",
            )
        )
    else:
        console.print(
            Panel(
                "[yellow]✗ Não logado[/yellow]\n\n"
                "[dim]Use 'wally-dev login' para autenticar[/dim]",
                title="[bold cyan]Status de Autenticação[/bold cyan]",
                border_style="yellow",
            )
        )
        return EXIT_SUCCESS

    # Locked norms
    locked_norms = config.get_locked_norms()
    workspace_norms = workspace.list_norms()

    console.print()
    if not locked_norms and not workspace_norms:
        console.print(
            Panel(
                "[dim]Nenhuma norma em checkout.[/dim]\n\n"
                "Use 'wally-dev checkout --norm-id <ID>' para começar.",
                title="[bold cyan]Workspace[/bold cyan]",
                border_style="cyan",
            )
        )
    else:
        console.print("[bold cyan]Normas em Checkout:[/bold cyan]\n")

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Norm ID", style="dim")
        table.add_column("Nome")
        table.add_column("Checkout em")
        table.add_column("Casos de Teste", justify="right")
        table.add_column("Status")

        # Combine locked norms and workspace norms
        all_norms = set(locked_norms.keys()) | set(workspace_norms)

        for norm_id in all_norms:
            lock_info = locked_norms.get(norm_id, {})
            workspace_info = workspace.get_workspace_info(norm_id)

            name = lock_info.get("norm_name", "-")
            checkout_at = lock_info.get("checkout_at", "-")
            if checkout_at and checkout_at != "-":
                # Format datetime
                try:
                    from datetime import datetime

                    dt = datetime.fromisoformat(checkout_at)
                    checkout_at = dt.strftime("%d/%m/%Y %H:%M")
                except ValueError:
                    pass

            tc_count = workspace_info.get("testcase_count", 0)

            if norm_id in locked_norms:
                status_str = "[green]Bloqueada[/green]"
            else:
                status_str = "[yellow]Apenas local[/yellow]"

            table.add_row(
                norm_id[:12] + ("..." if len(norm_id) > 12 else ""),
                name[:30] + ("..." if len(name) > 30 else ""),
                checkout_at if checkout_at != "-" else "[dim]-[/dim]",
                str(tc_count),
                status_str,
            )

        console.print(table)

        # Verbose details
        if verbose:
            for norm_id in all_norms:
                workspace_info = workspace.get_workspace_info(norm_id)
                console.print(f"\n[bold]Norma {norm_id}:[/bold]")
                console.print(f"  [dim]Caminho:[/dim] {workspace_info['path']}")

                if workspace_info.get("testcases"):
                    console.print("  [dim]Casos de teste:[/dim]")
                    for tc_id in workspace_info["testcases"][:5]:
                        console.print(f"    • {tc_id}")
                    if len(workspace_info["testcases"]) > 5:
                        console.print(f"    ... e mais {len(workspace_info['testcases']) - 5}")

    # Show config file location
    console.print(f"\n[dim]Config:[/dim] {config.config_file}")
    console.print(f"[dim]Workspace:[/dim] {workspace.workspace_dir}")

    return EXIT_SUCCESS
