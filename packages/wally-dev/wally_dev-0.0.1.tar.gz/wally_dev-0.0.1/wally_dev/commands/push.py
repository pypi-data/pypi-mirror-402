"""
Push command for Wally Dev CLI.

Uploads modified test cases and unlocks the norm.
"""

from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.table import Table

from ..config import LocalConfig, Settings
from ..constants import EXIT_ERROR_API, EXIT_ERROR_AUTH, EXIT_SUCCESS
from ..exceptions import NotLoggedInError, WallyDevError
from ..workspace import WorkspaceManager

console = Console()


@click.command("push")
@click.option(
    "--norm-id",
    "norm_id",
    required=False,
    default=None,
    help="ID da norma para fazer push (opcional, usa a norma em checkout)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Força push sem confirmação",
)
@click.option(
    "--keep-lock",
    is_flag=True,
    help="Mantém a norma bloqueada após o push",
)
def push(norm_id: Optional[str], force: bool, keep_lock: bool) -> int:
    """
    Envia alterações e desbloqueia a norma.

    Faz upload dos casos de teste modificados localmente e
    desbloqueia a norma no servidor, permitindo edições via sistema.

    Se --norm-id não for informado e houver apenas uma norma em checkout,
    usa essa norma automaticamente. Se houver múltiplas, exibe lista
    para seleção.

    Exemplo:
        wally-dev push
        wally-dev push --norm-id 507f1f77bcf86cd799439011
        wally-dev push --keep-lock
    """
    config = LocalConfig()
    settings = Settings()
    workspace = WorkspaceManager()

    # Check login
    if not config.is_logged_in:
        raise NotLoggedInError()

    # If norm_id not provided, try to detect from local checkout
    if not norm_id:
        norm_id = _get_norm_for_push(config)
        if not norm_id:
            return EXIT_ERROR_API

    # Check if norm is checked out locally
    if not config.is_norm_locked_locally(norm_id):
        console.print(
            Panel(
                f"[yellow]Esta norma não está em checkout local.[/yellow]\n\n"
                f"[dim]Use 'wally-dev checkout --norm-id {norm_id}' primeiro.[/dim]",
                title="[bold yellow]Norma Não Encontrada[/bold yellow]",
                border_style="yellow",
            )
        )
        return EXIT_SUCCESS

    try:
        # First, check for locally modified testcases using checksums (fast, no API call)
        locally_modified_ids = workspace.get_locally_modified_testcases(norm_id)

        if not locally_modified_ids:
            # No local modifications detected
            console.print(
                Panel(
                    "[yellow]Nenhuma alteração local detectada.[/yellow]\n\n"
                    "[dim]Os arquivos não foram modificados desde o checkout.[/dim]",
                    title="[bold yellow]Sem Alterações[/bold yellow]",
                    border_style="yellow",
                )
            )

            # Still allow unlock if user wants
            if not keep_lock:
                if click.confirm("Deseja desbloquear a norma mesmo assim?", default=False):
                    with config.create_api_client(settings) as client:
                        client.unlock_norm(norm_id)
                        config.remove_locked_norm(norm_id)
                        console.print("[green]✓ Norma desbloqueada.[/green]")
            return EXIT_SUCCESS

        # Show which testcases have local modifications
        console.print(
            f"\n[bold]Casos de teste modificados localmente ({len(locally_modified_ids)}):[/bold]"
        )
        for tc_id in locally_modified_ids[:10]:
            changes = workspace.get_testcase_changes(norm_id, tc_id)
            change_summary = []
            if changes["added"]:
                change_summary.append(f"+{len(changes['added'])}")
            if changes["modified"]:
                change_summary.append(f"~{len(changes['modified'])}")
            if changes["deleted"]:
                change_summary.append(f"-{len(changes['deleted'])}")
            console.print(f"  • {tc_id[:20]}... [{', '.join(change_summary) or 'modificado'}]")
        if len(locally_modified_ids) > 10:
            console.print(f"  ... e mais {len(locally_modified_ids) - 10}")
        console.print()

        with config.create_api_client(settings) as client:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                # Load only modified testcases for upload
                task = progress.add_task("Carregando casos de teste modificados...", total=None)
                modified = []
                for tc_id in locally_modified_ids:
                    try:
                        tc = workspace.load_testcase(norm_id, tc_id)
                        modified.append(tc)
                    except Exception as e:
                        console.print(f"[dim]Aviso: Não foi possível carregar {tc_id}: {e}[/dim]")
                progress.update(task, completed=True)

            # Show changes summary
            console.print()
            if modified:
                console.print(
                    f"[bold]Pronto para enviar ({len(modified)} caso(s) de teste):[/bold]"
                )
                table = Table(show_header=True, header_style="bold cyan")
                table.add_column("ID", style="dim")
                table.add_column("Nome")
                table.add_column("Código", justify="center")
                table.add_column("Exemplos", justify="right")

                for tc in modified:
                    table.add_row(
                        tc.id[:12] + "...",
                        tc.name[:40] + ("..." if len(tc.name) > 40 else ""),
                        "✓" if tc.code else "—",
                        str(len(tc.examples)),
                    )

                console.print(table)
                console.print()

            # Confirm push
            if not force and modified:
                if not Confirm.ask(f"Enviar {len(modified)} caso(s) de teste modificado(s)?"):
                    console.print("[dim]Push cancelado.[/dim]")
                    return EXIT_SUCCESS

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                # Sync modified test case files
                if modified:
                    task = progress.add_task("Sincronizando arquivos...", total=None)

                    for tc in modified:
                        # Get file changes for this testcase
                        changes = workspace.get_testcase_changes(norm_id, tc.id)

                        # Get existing files from server to map names to IDs
                        try:
                            server_files = client.get_testcase_files(tc.id)
                            file_map = {f.get("name"): f for f in server_files}
                        except Exception:
                            file_map = {}

                        # Upload modified files
                        for rel_path in changes.get("modified", []):
                            file_path = workspace.get_testcase_dir(norm_id, tc.id) / rel_path
                            if file_path.exists():
                                # Find file ID by name
                                file_name = file_path.name
                                server_file = file_map.get(file_name)

                                if server_file:
                                    file_id = server_file.get("_id") or server_file.get("id")
                                    with open(file_path, "rb") as f:
                                        content = f.read()
                                    try:
                                        client.update_file_binary(file_id, content)
                                        console.print(f"  [green]✓[/green] {rel_path}")
                                    except Exception as e:
                                        console.print(f"  [red]✗[/red] {rel_path}: {e}")
                                else:
                                    console.print(
                                        f"  [yellow]⚠[/yellow] {rel_path}: arquivo não encontrado no servidor"
                                    )

                        # Note: For deleted files, we need to be careful
                        # The server might not allow deleting required files
                        for rel_path in changes.get("deleted", []):
                            file_name = rel_path.split("/")[-1] if "/" in rel_path else rel_path
                            server_file = file_map.get(file_name)
                            if server_file:
                                file_id = server_file.get("_id") or server_file.get("id")
                                try:
                                    client.delete_file(file_id)
                                    console.print(f"  [red]✗[/red] {rel_path} (removido)")
                                except Exception as e:
                                    console.print(
                                        f"  [yellow]⚠[/yellow] {rel_path}: não foi possível remover: {e}"
                                    )

                    progress.update(task, completed=True)

                    # Update checksums after successful push
                    progress.update(task, description="Atualizando checksums...")
                    workspace.save_checksums(norm_id)

                # Unlock norm (unless keep-lock)
                if not keep_lock:
                    task = progress.add_task("Desbloqueando norma...", total=None)
                    client.unlock_norm(norm_id)
                    progress.update(task, completed=True)

                    # Remove from local tracking
                    config.remove_locked_norm(norm_id)

        # Success output
        console.print()
        if modified:
            console.print(
                Panel(
                    f"[green]✓ Push realizado com sucesso![/green]\n\n"
                    f"[dim]Casos de teste enviados:[/dim] {len(modified)}\n"
                    f"[dim]Norma desbloqueada:[/dim] {'Não' if keep_lock else 'Sim'}",
                    title="[bold green]Push Completo[/bold green]",
                    border_style="green",
                )
            )
        else:
            unlock_msg = "Norma desbloqueada." if not keep_lock else ""
            console.print(
                Panel(
                    f"[green]✓ {unlock_msg or 'Concluído sem alterações.'}[/green]",
                    title="[bold green]Push Completo[/bold green]",
                    border_style="green",
                )
            )

        if keep_lock:
            console.print(
                "\n[dim]A norma continua bloqueada. Use 'wally-dev push' "
                "novamente sem --keep-lock para desbloquear.[/dim]\n"
            )

        return EXIT_SUCCESS

    except NotLoggedInError as e:
        console.print(
            Panel(
                f"[red]✗ {e.user_message}[/red]\n\n[dim]{e.hint}[/dim]",
                title="[bold red]Não Autenticado[/bold red]",
                border_style="red",
            )
        )
        return EXIT_ERROR_AUTH

    except WallyDevError as e:
        console.print(
            Panel(
                f"[red]✗ {e.user_message}[/red]",
                title="[bold red]Erro[/bold red]",
                border_style="red",
            )
        )
        return e.exit_code

    except Exception as e:
        console.print(f"[red]Erro inesperado: {e}[/red]")
        return EXIT_ERROR_API


def _get_norm_for_push(config: LocalConfig) -> Optional[str]:
    """
    Get norm ID for push based on local checkout state.

    - If no norms in checkout: show error
    - If exactly one norm: use it automatically
    - If multiple norms: show selection list

    Returns:
        Norm ID or None if no selection
    """
    locked_norms = config.get_locked_norms()

    if not locked_norms:
        console.print(
            Panel(
                "[yellow]Nenhuma norma em checkout local.[/yellow]\n\n"
                "[dim]Use 'wally-dev checkout' para fazer checkout de uma norma.[/dim]",
                title="[bold yellow]Sem Checkout[/bold yellow]",
                border_style="yellow",
            )
        )
        return None

    # If only one norm, use it automatically
    if len(locked_norms) == 1:
        norm_id = list(locked_norms.keys())[0]
        norm_info = locked_norms[norm_id]
        norm_name = norm_info.get("norm_name", "Desconhecida")
        console.print(f"\n[dim]Usando norma em checkout:[/dim] {norm_name} ({norm_id[:12]}...)\n")
        return norm_id

    # Multiple norms - show selection
    console.print("\n[bold cyan]📋 Selecionar Norma para Push[/bold cyan]\n")

    table = Table(
        title="📋 Normas em Checkout",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Nome", style="white")
    table.add_column("ID", style="dim")
    table.add_column("Checkout em", style="dim")

    norm_list = list(locked_norms.items())
    for i, (norm_id, info) in enumerate(norm_list, start=1):
        checkout_at = info.get("checkout_at", "")[:10]  # Just date part
        table.add_row(
            str(i),
            info.get("norm_name", "Desconhecida")[:30],
            norm_id[:20] + "...",
            checkout_at,
        )

    console.print(table)
    console.print()

    # Prompt for selection
    while True:
        try:
            selection = click.prompt("Selecione o número da norma (0 para cancelar)")
            selected_index = int(selection)

            if selected_index == 0:
                console.print("[yellow]Operação cancelada.[/yellow]")
                return None

            if 1 <= selected_index <= len(norm_list):
                selected_norm_id: str = norm_list[selected_index - 1][0]
                return selected_norm_id
            else:
                console.print(
                    f"[red]Número inválido. Digite um número entre 1 e {len(norm_list)}, ou 0 para cancelar.[/red]"
                )
        except ValueError:
            console.print("[red]Por favor, digite um número válido.[/red]")
