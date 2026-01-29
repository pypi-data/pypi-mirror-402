"""
Rules command for Wally Dev CLI.

Lists and manages accessibility rules within norms.
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
    NormNotFoundError,
    NotLoggedInError,
    PermissionDeniedError,
    WallyDevError,
)

console = Console()


@click.group("rules")
def rules() -> None:
    """
    Gerencia regras de acessibilidade.

    Comandos para listar e visualizar informações sobre regras dentro de normas.
    """
    pass


@rules.command("list")
@click.option(
    "--norm-id",
    "norm_id",
    required=True,
    help="ID da norma para listar as regras",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Mostra informações detalhadas",
)
def list_rules(norm_id: str, verbose: bool = False) -> int:
    """
    Lista todas as regras de uma norma.

    Exibe ID e nome de cada regra associada à norma especificada.

    Exemplos:
        wally-dev rules list --norm-id 6954434ffdd23615c0e5d85d
        wally-dev rules list --norm-id 6954434ffdd23615c0e5d85d --verbose
    """
    config = LocalConfig()
    settings = Settings()

    # Check login
    if not config.is_logged_in:
        raise NotLoggedInError()

    try:
        with config.create_api_client(settings) as client:
            # Fetch norm info first
            with console.status("[bold cyan]Buscando informações...[/bold cyan]"):
                norm = client.get_norm(norm_id)
                rules_list = client.get_rules_by_norm(norm_id)

            if not rules_list:
                console.print(
                    Panel(
                        f"[yellow]Nenhuma regra encontrada para a norma {norm.name}.[/yellow]",
                        title="[bold]📜 Regras[/bold]",
                        border_style="yellow",
                    )
                )
                return EXIT_SUCCESS

            # Build table
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("ID", style="dim")
            table.add_column("Nome")

            if verbose:
                table.add_column("Severidade")
                table.add_column("Categoria")
                table.add_column("Automatizável", justify="center")

            for rule in rules_list:
                if verbose:
                    severity_color = {
                        "critical": "red",
                        "high": "yellow",
                        "medium": "blue",
                        "low": "green",
                    }.get(rule.severity or "", "dim")
                    severity_display = (
                        f"[{severity_color}]{rule.severity or '-'}[/{severity_color}]"
                    )

                    # Get category from raw data if available
                    category = getattr(rule, "category", None) or "-"
                    automatable = getattr(rule, "is_automatable", None)
                    automatable_display = (
                        "✓" if automatable else "✗" if automatable is False else "-"
                    )

                    table.add_row(
                        rule.id,
                        rule.name,
                        severity_display,
                        category,
                        automatable_display,
                    )
                else:
                    table.add_row(rule.id, rule.name)

            console.print()
            console.print(
                Panel(
                    table,
                    title=f"[bold]📜 Regras de {norm.name} ({len(rules_list)})[/bold]",
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

    except NormNotFoundError as e:
        console.print(
            Panel(
                f"[red]✗ {e.user_message}[/red]",
                title="[bold red]Norma Não Encontrada[/bold red]",
                border_style="red",
            )
        )
        return EXIT_ERROR_API

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
