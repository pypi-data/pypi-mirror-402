"""
Checkout command for Wally Dev CLI.

Locks a norm and downloads test cases for local development.
"""

from datetime import datetime
from typing import Any, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..config import LocalConfig, Settings
from ..constants import EXIT_ERROR_API, EXIT_ERROR_AUTH, EXIT_SUCCESS
from ..exceptions import NormLockedError, NormNotFoundError, NotLoggedInError, WallyDevError
from ..workspace import WorkspaceManager

console = Console()


@click.command("checkout")
@click.option(
    "--norm-id",
    "norm_id",
    required=False,
    default=None,
    help="ID da norma para fazer checkout (opcional, se não informado exibe lista)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Força checkout mesmo se já existir localmente",
)
def checkout(norm_id: Optional[str], force: bool) -> int:
    """
    Faz checkout de uma norma para desenvolvimento local.

    Bloqueia a norma no servidor (impede edições via sistema) e
    baixa todos os casos de teste para o diretório workspace local.

    Se --norm-id não for informado, exibe a lista de normas disponíveis
    para seleção interativa.

    Estrutura criada:
        ./workspace/[normId]/testCases/
            [testCaseId].json  - Dados do caso de teste
            [testCaseId].py    - Código de implementação

    Exemplo:
        wally-dev checkout
        wally-dev checkout --norm-id 507f1f77bcf86cd799439011
    """
    config = LocalConfig()
    settings = Settings()
    workspace = WorkspaceManager()

    # Check login
    if not config.is_logged_in:
        raise NotLoggedInError()

    try:
        with config.create_api_client(settings) as client:
            # If norm_id not provided, show interactive selection
            if not norm_id:
                norm_id = _select_norm_interactive(client, config)
                if not norm_id:
                    return EXIT_ERROR_API

            # Check if already checked out locally
            if config.is_norm_locked_locally(norm_id) and not force:
                info = workspace.get_workspace_info(norm_id)
                console.print(
                    Panel(
                        f"[yellow]Esta norma já está em checkout local.[/yellow]\n\n"
                        f"[dim]Caminho:[/dim] {info['path']}\n"
                        f"[dim]Casos de teste:[/dim] {info['testcase_count']}\n\n"
                        f"[dim]Use --force para baixar novamente ou 'wally-dev push' para enviar alterações.[/dim]",
                        title="[bold yellow]Norma já em checkout[/bold yellow]",
                        border_style="yellow",
                    )
                )
                return EXIT_SUCCESS

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                # Get norm info
                task = progress.add_task("Buscando informações da norma...", total=None)
                norm = client.get_norm(norm_id)
                progress.update(task, completed=True)

                # Check if norm is locked by someone else (not the current user)
                already_locked_by_me = norm.locked_by and norm.locked_by == config.user_id
                if norm.locked_by and not already_locked_by_me:
                    progress.stop()
                    raise NormLockedError(
                        message=f"Norma está bloqueada por outro usuário: {norm.locked_by}"
                    )

                # Lock the norm (only if not already locked by me)
                if not already_locked_by_me:
                    progress.update(task, description="Bloqueando norma no servidor...")
                    client.lock_norm(norm_id)
                else:
                    progress.update(task, description="Norma já está bloqueada por você...")

                # Download test cases as ZIP
                progress.update(task, description="Baixando casos de teste (ZIP)...")
                try:
                    zip_content = client.export_testcases_zip(norm_id, target="html")

                    # Extract to workspace
                    progress.update(task, description="Extraindo casos de teste...")
                    count = workspace.extract_testcases_zip(norm_id, zip_content)
                except Exception as e:
                    # If export fails (e.g., no testcases), continue with count=0
                    console.print(f"[dim]Aviso (testcases): {e}[/dim]")
                    count = 0
                    workspace.ensure_norm_dir(norm_id)

                # Download examples as ZIP
                progress.update(task, description="Baixando examples (ZIP)...")
                examples_count = 0
                try:
                    examples_zip = client.export_examples_zip(norm_id)

                    # Extract examples to workspace
                    progress.update(task, description="Extraindo examples...")
                    examples_count = workspace.extract_examples_zip(norm_id, examples_zip)
                except Exception as e:
                    # If export fails (e.g., no examples), continue
                    console.print(f"[dim]Aviso (examples): {e}[/dim]")

                # Save checksums for change detection
                progress.update(task, description="Salvando checksums...")
                workspace.save_checksums(norm_id)

                # Track locally
                config.add_locked_norm(
                    norm_id,
                    {
                        "norm_name": norm.name,
                        "checkout_at": datetime.now().isoformat(),
                        "testcase_count": count,
                        "examples_count": examples_count,
                    },
                )

        # Success output
        console.print()
        console.print(
            Panel(
                f"[green]✓ Checkout realizado com sucesso![/green]\n\n"
                f"[dim]Norma:[/dim] {norm.name}\n"
                f"[dim]ID:[/dim] {norm_id}\n"
                f"[dim]Casos de teste:[/dim] {count}\n"
                f"[dim]Examples:[/dim] {examples_count}",
                title="[bold green]Checkout Completo[/bold green]",
                border_style="green",
            )
        )

        workspace_info = workspace.get_workspace_info(norm_id)
        console.print(f"\n[dim]Workspace:[/dim] {workspace_info['path']}")

        # List extracted test cases from workspace
        if count > 0:
            testcases_dir = workspace.get_testcases_dir(norm_id)
            testcase_dirs = [d for d in testcases_dir.iterdir() if d.is_dir()]

            console.print("\n[bold]Casos de teste baixados:[/bold]")
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("ID", style="dim")
            table.add_column("Arquivos", justify="right")

            for tc_dir in sorted(testcase_dirs)[:10]:  # Show first 10
                files = list(tc_dir.iterdir())
                table.add_row(
                    tc_dir.name[:20] + ("..." if len(tc_dir.name) > 20 else ""),
                    str(len(files)),
                )

            if len(testcase_dirs) > 10:
                table.add_row("...", f"+ {len(testcase_dirs) - 10}")

            console.print(table)

        console.print("\n[dim]Próximos passos:[/dim]")
        console.print(f"  • Edite os arquivos em [cyan]./workspace/{norm_id}/testCases/[/cyan]")
        console.print(
            "  • Use [cyan]wally-dev run --testcase <ID> --example <ID>[/cyan] para testar"
        )
        console.print(
            f"  • Use [cyan]wally-dev push --norm-id {norm_id}[/cyan] para enviar alterações\n"
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

    except NormNotFoundError as e:
        console.print(
            Panel(
                f"[red]✗ {e.user_message}[/red]\n\n[dim]{e.hint}[/dim]",
                title="[bold red]Norma Não Encontrada[/bold red]",
                border_style="red",
            )
        )
        return EXIT_ERROR_API

    except NormLockedError as e:
        console.print(
            Panel(
                f"[red]✗ {e.user_message}[/red]\n\n[dim]{e.hint}[/dim]",
                title="[bold red]Norma Bloqueada[/bold red]",
                border_style="red",
            )
        )
        return EXIT_ERROR_API

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


def _select_norm_interactive(client: Any, config: LocalConfig) -> Optional[str]:
    """
    Display norms list and let user select one interactively.

    Args:
        client: WallyDevApiClient instance
        config: LocalConfig instance

    Returns:
        Selected norm ID or None if cancelled/no norms
    """
    console.print("\n[bold cyan]📋 Selecionar Norma para Checkout[/bold cyan]\n")
    console.print("[dim]Buscando normas disponíveis...[/dim]\n")

    norms = client.list_norms()

    if not norms:
        console.print(
            Panel(
                "[yellow]Nenhuma norma disponível.[/yellow]\n\n"
                "[dim]Verifique se você tem acesso a normas nesta organização.[/dim]",
                title="[bold yellow]Sem Normas[/bold yellow]",
                border_style="yellow",
            )
        )
        return None

    # Get locally locked norms to mark them
    locally_locked = config.get_locked_norms() or {}

    # Display norms table
    table = Table(
        title="📋 Normas Disponíveis",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Nome", style="white")
    table.add_column("ID", style="dim")
    table.add_column("Status", width=12)
    table.add_column("", width=3)  # For markers

    for i, norm in enumerate(norms, start=1):
        is_local = norm.id in locally_locked
        is_locked = bool(norm.locked_by)

        # Status indicator
        if is_locked:
            if norm.locked_by == config.user_id:
                status = "[yellow]🔒 Você[/yellow]"
            else:
                status = "[red]🔒 Outro[/red]"
        else:
            status = "[green]✓ Livre[/green]"

        marker = "[cyan]↓[/cyan]" if is_local else ""

        table.add_row(
            str(i),
            norm.name[:30] + ("..." if len(norm.name) > 30 else ""),
            norm.id[:20] + "..." if len(norm.id) > 20 else norm.id,
            status,
            marker,
        )

    console.print(table)
    console.print("\n[dim]↓ = já em checkout local[/dim]")
    console.print(f"[dim]Total: {len(norms)} norma(s)[/dim]\n")

    # Prompt for selection
    while True:
        try:
            selection = click.prompt("Selecione o número da norma (0 para cancelar)")
            selected_index = int(selection)

            if selected_index == 0:
                console.print("[yellow]Operação cancelada.[/yellow]")
                return None

            if 1 <= selected_index <= len(norms):
                selected_norm = norms[selected_index - 1]
                selected_id: str = selected_norm.id
                return selected_id
            else:
                console.print(
                    f"[red]Número inválido. Digite um número entre 1 e {len(norms)}, ou 0 para cancelar.[/red]"
                )
        except ValueError:
            console.print("[red]Por favor, digite um número válido.[/red]")
