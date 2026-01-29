"""
Norms command for Wally Dev CLI.

Lists and manages accessibility norms.
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..config import LocalConfig, Settings
from ..constants import EXIT_ERROR_API, EXIT_ERROR_AUTH, EXIT_SUCCESS
from ..exceptions import (
    APIError,
    ConnectionFailedError,
    NotLoggedInError,
    PermissionDeniedError,
    WallyDevError,
)

console = Console()


@click.group("norms")
def norms() -> None:
    """
    Gerencia normas de acessibilidade.

    Comandos para listar e visualizar informações sobre normas.
    """
    pass


@norms.command("list")
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Mostra informações detalhadas",
)
def list_norms(verbose: bool = False) -> int:
    """
    Lista todas as normas disponíveis para o usuário.

    Exibe ID e nome de cada norma acessível na organização atual.

    Exemplos:
        wally-dev norms list
        wally-dev norms list --verbose
    """
    config = LocalConfig()
    settings = Settings()

    # Check login
    if not config.is_logged_in:
        raise NotLoggedInError()

    try:
        with config.create_api_client(settings) as client:
            # Fetch norms
            with console.status("[bold cyan]Buscando normas...[/bold cyan]"):
                norms_list = client.list_norms()

            if not norms_list:
                console.print(
                    Panel(
                        "[yellow]Nenhuma norma encontrada.[/yellow]\n\n"
                        "[dim]Verifique se você tem acesso a normas nesta organização.[/dim]",
                        title="[bold]📋 Normas[/bold]",
                        border_style="yellow",
                    )
                )
                return EXIT_SUCCESS

            # Build table
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("ID", style="dim")
            table.add_column("Nome")

            if verbose:
                table.add_column("Versão")
                table.add_column("Regras", justify="right")
                table.add_column("Status")

            for norm in norms_list:
                if verbose:
                    status = ""
                    if norm.locked_by:
                        status = "[yellow]🔒 Bloqueada[/yellow]"
                    else:
                        status = "[green]✓ Disponível[/green]"

                    table.add_row(
                        norm.id,
                        norm.name,
                        norm.version or "-",
                        str(norm.rules_count or 0),
                        status,
                    )
                else:
                    table.add_row(norm.id, norm.name)

            console.print()
            console.print(
                Panel(
                    table,
                    title=f"[bold]📋 Normas ({len(norms_list)})[/bold]",
                    border_style="cyan",
                )
            )
            console.print()

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

    except ConnectionFailedError as e:
        console.print(
            Panel(
                f"[red]✗ {e.user_message}[/red]\n\n[dim]{e.hint}[/dim]",
                title="[bold red]Erro de Conexão[/bold red]",
                border_style="red",
            )
        )
        return EXIT_ERROR_API

    except PermissionDeniedError as e:
        console.print(
            Panel(
                f"[red]✗ {e.user_message}[/red]",
                title="[bold red]Acesso Negado[/bold red]",
                border_style="red",
            )
        )
        return EXIT_ERROR_AUTH

    except APIError as e:
        console.print(
            Panel(
                f"[red]✗ {e.user_message}[/red]",
                title="[bold red]Erro de API[/bold red]",
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
