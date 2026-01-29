"""Logout command for Wally Dev CLI.

Clears stored credentials and unlocks any locked norms.
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm

from ..config import LocalConfig, Settings
from ..constants import EXIT_SUCCESS
from ..exceptions import WallyDevError
from ..workspace import WorkspaceManager

console = Console()


@click.command("logout")
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Força logout sem confirmação",
)
def logout(force: bool) -> int:
    """
    Remove credenciais locais.

    Desloga da plataforma Wally:
    - Desbloqueia todas as normas em checkout no servidor
    - Remove o workspace local
    - Remove o token de acesso armazenado

    Exemplo:
        wally-dev logout
        wally-dev logout --force
    """
    config = LocalConfig()
    settings = Settings()
    workspace = WorkspaceManager()

    if not config.is_logged_in:
        console.print(
            Panel(
                "[yellow]Você não está logado.[/yellow]",
                title="[bold yellow]Aviso[/bold yellow]",
                border_style="yellow",
            )
        )
        return EXIT_SUCCESS

    # Check for locked norms
    locked_norms = config.get_locked_norms()

    if locked_norms:
        console.print(
            Panel(
                "[yellow]⚠ Você tem normas em checkout:[/yellow]\n\n"
                + "\n".join(
                    [
                        f"  • {norm_id} - {info.get('norm_name', 'N/A')}"
                        for norm_id, info in locked_norms.items()
                    ]
                )
                + "\n\n[dim]Estas normas serão desbloqueadas e o workspace será removido.[/dim]",
                title="[bold yellow]Atenção[/bold yellow]",
                border_style="yellow",
            )
        )

    # Confirm logout
    if not force:
        if not Confirm.ask("Confirma logout?"):
            console.print("[dim]Logout cancelado.[/dim]")
            return EXIT_SUCCESS

    unlocked_count = 0
    unlock_errors = []

    # Unlock all locked norms on server
    if locked_norms:
        try:
            with config.create_api_client(settings) as client:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task("Desbloqueando normas...", total=len(locked_norms))

                    for norm_id in locked_norms.keys():
                        try:
                            progress.update(task, description=f"Desbloqueando {norm_id}...")
                            client.unlock_norm(norm_id)
                            unlocked_count += 1
                        except WallyDevError as e:
                            unlock_errors.append(f"{norm_id}: {e.user_message}")
                        progress.advance(task)
        except WallyDevError as e:
            console.print(
                f"[yellow]Aviso: Não foi possível conectar ao servidor: {e.user_message}[/yellow]"
            )
            console.print("[dim]As normas podem permanecer bloqueadas no servidor.[/dim]")

    # Delete workspace for all norms
    workspace_norms = workspace.list_norms()
    deleted_count = 0
    for norm_id in workspace_norms:
        try:
            workspace.delete_norm(norm_id)
            deleted_count += 1
        except Exception:
            pass  # Ignore deletion errors

    # Clear config (credentials and locked norms tracking)
    config.clear()

    # Show results
    result_lines = ["[green]✓ Logout realizado com sucesso![/green]"]

    if unlocked_count > 0:
        result_lines.append(f"\n[dim]Normas desbloqueadas:[/dim] {unlocked_count}")

    if deleted_count > 0:
        result_lines.append(f"[dim]Workspace removido:[/dim] {deleted_count} normas")

    if unlock_errors:
        result_lines.append("\n[yellow]Erros ao desbloquear:[/yellow]")
        for error in unlock_errors:
            result_lines.append(f"  • {error}")

    console.print(
        Panel(
            "\n".join(result_lines),
            title="[bold green]Deslogado[/bold green]",
            border_style="green",
        )
    )

    return EXIT_SUCCESS
