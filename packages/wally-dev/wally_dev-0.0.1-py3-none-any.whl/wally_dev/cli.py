"""
Wally Dev CLI - Command Line Interface.

Ferramenta para desenvolvimento local de casos de teste de acessibilidade.
"""

import sys

import click
from dotenv import load_dotenv
from rich.console import Console

from . import __version__
from .commands import (
    checkout,
    login,
    logout,
    norms,
    organizations,
    push,
    rules,
    run,
    status,
    testcases,
)

# Load .env file if present
load_dotenv()

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="wally-dev")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    Wally Dev CLI - Ferramenta para desenvolvimento local de casos de teste.

    Use os comandos abaixo para gerenciar o desenvolvimento de casos de teste
    de acessibilidade da plataforma Wally.

    \b
    Workflow típico:
      1. wally-dev login                     # Autenticar
      2. wally-dev checkout --norm-id <id>   # Baixar casos de teste
      3. wally-dev testcases list            # Listar casos de teste
      4. [editar arquivos em ./workspace/]   # Desenvolver
      5. wally-dev run --testcase <id>       # Testar localmente
      6. wally-dev push --norm-id <id>       # Enviar alterações

    \b
    Para mais informações sobre cada comando:
      wally-dev <comando> --help
    """
    ctx.ensure_object(dict)


# Register commands
cli.add_command(login)
cli.add_command(logout)
cli.add_command(checkout)
cli.add_command(norms)
cli.add_command(organizations)
cli.add_command(push)
cli.add_command(rules)
cli.add_command(run)
cli.add_command(status)
cli.add_command(testcases)


def main() -> int:
    """Main entry point for the CLI."""
    try:
        return cli(standalone_mode=False) or 0
    except click.ClickException as e:
        e.show()
        return e.exit_code
    except click.Abort:
        console.print("\n[yellow]Operação cancelada.[/yellow]")
        return 130
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrompido pelo usuário.[/yellow]")
        return 130
    except Exception as e:
        console.print(f"\n[red]Erro inesperado: {e}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
