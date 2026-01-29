"""
Login command for Wally Dev CLI.

Authenticates user with username/password and stores access token locally.
"""

import getpass
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..api_client import WallyDevApiClient
from ..config import LocalConfig, Settings
from ..constants import DEFAULT_BACKEND_URL, EXIT_ERROR_AUTH, EXIT_SUCCESS
from ..exceptions import InvalidCredentialsError, WallyDevError

console = Console()


@click.command("login")
@click.option(
    "--username",
    "-u",
    "username",
    default=None,
    help="Nome de usuário (email)",
)
@click.option(
    "--backend-url",
    "backend_url",
    default=None,
    help=f"URL do backend (padrão: {DEFAULT_BACKEND_URL})",
)
def login(username: Optional[str] = None, backend_url: Optional[str] = None) -> int:
    """
    Autentica com a plataforma Wally.

    Solicita username e password para autenticação, depois exibe a lista
    de organizações para seleção.

    Exemplo:
        wally-dev login
        wally-dev login --username user@example.com
    """
    config = LocalConfig()
    settings = Settings()

    # Use provided URL or settings default
    url = backend_url or settings.backend_url

    console.print("\n[bold cyan]🔐 Login na plataforma Wally[/bold cyan]\n")

    # Prompt for username if not provided
    if not username:
        username = click.prompt("Email")

    # Ensure username is not None for mypy
    username_str: str = username

    # Always prompt for password using getpass (secure, hidden input)
    password = getpass.getpass("Senha: ")

    console.print("\n[dim]Autenticando...[/dim]")

    try:
        # Login with username/password (no org_id required)
        with WallyDevApiClient(base_url=url) as client:
            login_response = client.login(username=username_str, password=password)

            # Store access token temporarily to fetch organizations
            client.access_token = login_response.access_token
            client.refresh_token = login_response.refresh_token

            # Fetch user organizations
            console.print("[dim]Buscando organizações...[/dim]\n")
            organizations = client.list_organizations()

        if not organizations:
            console.print(
                Panel(
                    "[yellow]Você não está vinculado a nenhuma organização.[/yellow]\n\n"
                    "[dim]Entre em contato com o administrador da sua organização.[/dim]",
                    title="[bold yellow]Sem Organizações[/bold yellow]",
                    border_style="yellow",
                )
            )
            return EXIT_ERROR_AUTH

        # Get the last used organization (if any)
        last_org_id = config.organization_id

        # Display organizations table
        table = Table(
            title="📋 Organizações Disponíveis", show_header=True, header_style="bold cyan"
        )
        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("Nome", style="white")
        table.add_column("ID", style="dim")
        table.add_column("", width=3)  # For asterisk

        default_index = None
        for i, org in enumerate(organizations, start=1):
            is_last_used = org.id == last_org_id
            marker = "[yellow]*[/yellow]" if is_last_used else ""
            if is_last_used:
                default_index = i
            table.add_row(
                str(i),
                org.name,
                org.id[:20] + "..." if len(org.id) > 20 else org.id,
                marker,
            )

        console.print(table)

        if default_index:
            console.print("\n[dim]* Última organização utilizada[/dim]")

        # Prompt for organization selection
        while True:
            selection = click.prompt(
                "Selecione o número da organização",
                default=str(default_index) if default_index else None,
            )

            try:
                selected_index = int(selection)
                if 1 <= selected_index <= len(organizations):
                    selected_org = organizations[selected_index - 1]
                    break
                else:
                    console.print(
                        f"[red]Número inválido. Digite um número entre 1 e {len(organizations)}.[/red]"
                    )
            except ValueError:
                console.print("[red]Por favor, digite um número válido.[/red]")

        # Store credentials
        config.access_token = login_response.access_token
        config.refresh_token = login_response.refresh_token
        config.user_email = login_response.user.email
        config.user_id = login_response.user.id
        config.organization_id = selected_org.id
        if backend_url:
            config.backend_url = backend_url

        # Success message
        console.print(
            Panel(
                f"[green]✓ Login realizado com sucesso![/green]\n\n"
                f"[dim]Usuário:[/dim] {login_response.user.email}\n"
                f"[dim]Organização:[/dim] {selected_org.name}\n"
                f"[dim]ID:[/dim] {login_response.user.id}",
                title="[bold green]Autenticado[/bold green]",
                border_style="green",
            )
        )

        console.print("\n[dim]Credenciais armazenadas em:[/dim]", config.config_file)
        console.print("\n[dim]Próximos passos:[/dim]")
        console.print("  • Use [cyan]wally-dev norms list[/cyan] para listar normas disponíveis")
        console.print(
            "  • Use [cyan]wally-dev checkout --norm-id <ID>[/cyan] para baixar casos de teste"
        )
        console.print("  • Use [cyan]wally-dev status[/cyan] para ver normas em checkout\n")

        return EXIT_SUCCESS

    except InvalidCredentialsError as e:
        console.print(
            Panel(
                f"[red]✗ {e.user_message}[/red]\n\n" f"[dim]{e.hint}[/dim]",
                title="[bold red]Erro de Autenticação[/bold red]",
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
