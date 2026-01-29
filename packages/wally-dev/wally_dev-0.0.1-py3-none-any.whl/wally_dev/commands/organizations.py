"""
Organizations commands for Wally Dev CLI.

Manage organizations: list available organizations and select active one.
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..api_client import WallyDevApiClient
from ..config import LocalConfig, Settings
from ..constants import EXIT_ERROR_AUTH, EXIT_SUCCESS
from ..exceptions import TokenExpiredError, WallyDevError

console = Console()


@click.group("organizations")
def organizations() -> None:
    """
    Gerenciar organizações.

    Comandos para listar e selecionar organizações disponíveis.
    """
    pass


@organizations.command("list")
def list_organizations() -> int:
    """
    Lista as organizações disponíveis para o usuário.

    Exibe uma tabela com todas as organizações às quais o usuário
    tem acesso, marcando a organização atualmente selecionada.

    Exemplo:
        wally-dev organizations list
    """
    config = LocalConfig()
    settings = Settings()

    # Check if user is authenticated
    if not config.access_token:
        console.print(
            Panel(
                "[yellow]Você não está autenticado.[/yellow]\n\n"
                "[dim]Use [cyan]wally-dev login[/cyan] para autenticar.[/dim]",
                title="[bold yellow]Não Autenticado[/bold yellow]",
                border_style="yellow",
            )
        )
        return EXIT_ERROR_AUTH

    console.print("\n[dim]Buscando organizações...[/dim]\n")

    try:
        with WallyDevApiClient(
            base_url=config.backend_url or settings.backend_url,
            access_token=config.access_token,
            refresh_token=config.refresh_token,
        ) as client:
            orgs = client.list_organizations()

        if not orgs:
            console.print(
                Panel(
                    "[yellow]Você não está vinculado a nenhuma organização.[/yellow]\n\n"
                    "[dim]Entre em contato com o administrador da sua organização.[/dim]",
                    title="[bold yellow]Sem Organizações[/bold yellow]",
                    border_style="yellow",
                )
            )
            return EXIT_SUCCESS

        # Get current organization
        current_org_id = config.organization_id

        # Display organizations table
        table = Table(
            title="📋 Organizações Disponíveis",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("Nome", style="white")
        table.add_column("ID", style="dim")
        table.add_column("Descrição", style="dim", max_width=40)
        table.add_column("", width=3)  # For asterisk

        for i, org in enumerate(orgs, start=1):
            is_current = org.id == current_org_id
            marker = "[green]✓[/green]" if is_current else ""
            description = (
                org.description[:37] + "..."
                if org.description and len(org.description) > 40
                else (org.description or "")
            )
            table.add_row(
                str(i),
                org.name,
                org.id[:20] + "..." if len(org.id) > 20 else org.id,
                description,
                marker,
            )

        console.print(table)

        if current_org_id:
            console.print("\n[dim]✓ Organização atualmente selecionada[/dim]")
        else:
            console.print(
                "\n[yellow]Nenhuma organização selecionada.[/yellow] "
                "Use [cyan]wally-dev organizations select[/cyan] para selecionar."
            )

        console.print(f"\n[dim]Total: {len(orgs)} organização(ões)[/dim]\n")

        return EXIT_SUCCESS

    except TokenExpiredError:
        console.print(
            Panel(
                "[red]Sua sessão expirou.[/red]\n\n"
                "[dim]Use [cyan]wally-dev login[/cyan] para autenticar novamente.[/dim]",
                title="[bold red]Sessão Expirada[/bold red]",
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
        return EXIT_ERROR_AUTH


@organizations.command("select")
def select_organization() -> int:
    """
    Seleciona a organização ativa.

    Exibe a lista de organizações disponíveis e permite
    selecionar qual organização usar para os próximos comandos.

    Exemplo:
        wally-dev organizations select
    """
    config = LocalConfig()
    settings = Settings()

    # Check if user is authenticated
    if not config.access_token:
        console.print(
            Panel(
                "[yellow]Você não está autenticado.[/yellow]\n\n"
                "[dim]Use [cyan]wally-dev login[/cyan] para autenticar.[/dim]",
                title="[bold yellow]Não Autenticado[/bold yellow]",
                border_style="yellow",
            )
        )
        return EXIT_ERROR_AUTH

    console.print("\n[bold cyan]🏢 Selecionar Organização[/bold cyan]\n")
    console.print("[dim]Buscando organizações...[/dim]\n")

    try:
        with WallyDevApiClient(
            base_url=config.backend_url or settings.backend_url,
            access_token=config.access_token,
            refresh_token=config.refresh_token,
        ) as client:
            orgs = client.list_organizations()

        if not orgs:
            console.print(
                Panel(
                    "[yellow]Você não está vinculado a nenhuma organização.[/yellow]\n\n"
                    "[dim]Entre em contato com o administrador da sua organização.[/dim]",
                    title="[bold yellow]Sem Organizações[/bold yellow]",
                    border_style="yellow",
                )
            )
            return EXIT_ERROR_AUTH

        # Get current organization
        current_org_id = config.organization_id

        # Display organizations table
        table = Table(
            title="📋 Organizações Disponíveis",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("Nome", style="white")
        table.add_column("ID", style="dim")
        table.add_column("", width=3)  # For asterisk

        default_index = None
        for i, org in enumerate(orgs, start=1):
            is_current = org.id == current_org_id
            marker = "[yellow]*[/yellow]" if is_current else ""
            if is_current:
                default_index = i
            table.add_row(
                str(i),
                org.name,
                org.id[:20] + "..." if len(org.id) > 20 else org.id,
                marker,
            )

        console.print(table)

        if default_index:
            console.print("\n[dim]* Organização atualmente selecionada[/dim]")

        # Prompt for organization selection
        while True:
            selection = click.prompt(
                "Selecione o número da organização",
                default=str(default_index) if default_index else None,
            )

            try:
                selected_index = int(selection)
                if 1 <= selected_index <= len(orgs):
                    selected_org = orgs[selected_index - 1]
                    break
                else:
                    console.print(
                        f"[red]Número inválido. Digite um número entre 1 e {len(orgs)}.[/red]"
                    )
            except ValueError:
                console.print("[red]Por favor, digite um número válido.[/red]")

        # Check if same organization was selected
        if selected_org.id == current_org_id:
            console.print(
                Panel(
                    f"[cyan]A organização [bold]{selected_org.name}[/bold] já está selecionada.[/cyan]",
                    title="[bold cyan]Sem Alteração[/bold cyan]",
                    border_style="cyan",
                )
            )
            return EXIT_SUCCESS

        # Update config with selected organization
        config.organization_id = selected_org.id

        console.print(
            Panel(
                f"[green]✓ Organização alterada com sucesso![/green]\n\n"
                f"[dim]Organização:[/dim] {selected_org.name}\n"
                f"[dim]ID:[/dim] {selected_org.id}",
                title="[bold green]Organização Selecionada[/bold green]",
                border_style="green",
            )
        )

        return EXIT_SUCCESS

    except TokenExpiredError:
        console.print(
            Panel(
                "[red]Sua sessão expirou.[/red]\n\n"
                "[dim]Use [cyan]wally-dev login[/cyan] para autenticar novamente.[/dim]",
                title="[bold red]Sessão Expirada[/bold red]",
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
        return EXIT_ERROR_AUTH
