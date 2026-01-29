"""
Testcases command for Wally Dev CLI.

Creates and manages test cases for accessibility rules.
"""

import os
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.table import Table

from ..config import LocalConfig, Settings
from ..constants import EXIT_ERROR_API, EXIT_ERROR_AUTH, EXIT_SUCCESS
from ..exceptions import (
    APIError,
    ConnectionFailedError,
    NormNotFoundError,
    NotLoggedInError,
    PermissionDeniedError,
    RuleNotFoundError,
    WallyDevError,
)
from ..generator import TestCaseGenerator
from ..workspace import WorkspaceManager

console = Console()

# Targets suportados para geração de testcases
SUPPORTED_TARGETS = ["html", "react", "angular", "vue", "sonarqube"]


@click.group("testcases")
def testcases() -> None:
    """
    Gerencia casos de teste de acessibilidade.

    Comandos para criar, listar e gerenciar casos de teste dentro de normas.
    """
    pass


@testcases.command("create")
@click.option(
    "--all",
    "create_all",
    is_flag=True,
    help="Cria casos de teste para todas as regras sem testcase",
)
@click.option(
    "--rule-id",
    "rule_id",
    type=str,
    help="ID específico da regra para criar o testcase",
)
@click.option(
    "--target",
    "target",
    type=click.Choice(SUPPORTED_TARGETS, case_sensitive=False),
    required=True,
    help="Tecnologia alvo (HTML, REACT, ANGULAR, VUE, SONARQUBE)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Mostra o que seria criado sem executar",
)
@click.option(
    "--delay",
    type=float,
    default=2.0,
    help="Delay entre chamadas à API de IA (segundos)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Força criação mesmo se regra já tiver testcase para o target",
)
def create_testcase(
    create_all: bool,
    rule_id: Optional[str],
    target: str,
    dry_run: bool,
    delay: float,
    force: bool,
) -> int:
    """
    Cria casos de teste para regras de acessibilidade.

    Gera automaticamente código (finder.py, validator.py) e exemplos HTML
    usando IA para validar conformidade com regras de acessibilidade.

    REQUER: Norma em checkout local (use 'wally-dev checkout --norm-id <id>' primeiro).

    \b
    Exemplos:
        # Criar testcases para todas as regras sem testcase
        wally-dev testcases create --all --target HTML

        # Criar testcase para uma regra específica
        wally-dev testcases create --rule-id 507f1f77bcf86cd799439011 --target REACT

        # Preview do que seria criado
        wally-dev testcases create --all --target HTML --dry-run
    """
    config = LocalConfig()
    settings = Settings()

    # Check login
    if not config.is_logged_in:
        raise NotLoggedInError()

    # Validate mutually exclusive options
    if not create_all and not rule_id:
        console.print(
            Panel(
                "[red]✗ Especifique --all ou --rule-id[/red]\n\n"
                "[dim]Use --all para criar testcases para todas as regras,\n"
                "ou --rule-id para uma regra específica.[/dim]",
                title="[bold red]Parâmetro Obrigatório[/bold red]",
                border_style="red",
            )
        )
        return EXIT_ERROR_API

    if create_all and rule_id:
        console.print(
            Panel(
                "[red]✗ Use apenas --all ou --rule-id, não ambos[/red]",
                title="[bold red]Parâmetros Conflitantes[/bold red]",
                border_style="red",
            )
        )
        return EXIT_ERROR_API

    # Check for checkout (locked norm)
    locked_norms = config.get_locked_norms()
    if not locked_norms:
        console.print(
            Panel(
                "[red]✗ Nenhuma norma em checkout local.[/red]\n\n"
                "[dim]Para criar testcases, primeiro faça checkout de uma norma:\n"
                "  wally-dev checkout --norm-id <norm_id>[/dim]",
                title="[bold red]Checkout Necessário[/bold red]",
                border_style="red",
            )
        )
        return EXIT_ERROR_API

    # Get the first (and usually only) locked norm
    if len(locked_norms) > 1:
        console.print(
            Panel(
                "[yellow]⚠ Múltiplas normas em checkout. Usando a primeira.[/yellow]\n\n"
                f"[dim]Normas em checkout: {list(locked_norms.keys())}[/dim]",
                title="[bold yellow]Aviso[/bold yellow]",
                border_style="yellow",
            )
        )

    norm_id = list(locked_norms.keys())[0]
    norm_info = locked_norms[norm_id]
    norm_name = norm_info.get("norm_name", norm_id)

    # Check OpenAI API key
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key and not dry_run:
        console.print(
            Panel(
                "[red]✗ OPENAI_API_KEY não configurada.[/red]\n\n"
                "[dim]Para gerar testcases com IA, configure a variável de ambiente:\n"
                "  export OPENAI_API_KEY='sua-chave-aqui'\n\n"
                "Ou use --dry-run para ver o que seria criado.[/dim]",
                title="[bold red]Configuração Necessária[/bold red]",
                border_style="red",
            )
        )
        return EXIT_ERROR_API

    try:
        with config.create_api_client(settings) as client:
            # Fetch all rules for the norm
            with console.status("[bold cyan]Buscando regras da norma...[/bold cyan]"):
                rules = client.get_rules_by_norm(norm_id)

            if not rules:
                console.print(
                    Panel(
                        f"[yellow]Nenhuma regra encontrada para a norma {norm_name}.[/yellow]",
                        title="[bold]📜 Regras[/bold]",
                        border_style="yellow",
                    )
                )
                return EXIT_SUCCESS

            # If specific rule_id, filter
            if rule_id:
                rules = [r for r in rules if r.id == rule_id]
                if not rules:
                    raise RuleNotFoundError(message=f"Regra não encontrada: {rule_id}")

            # Fetch existing testcases for the norm to check which rules already have them
            with console.status("[bold cyan]Verificando testcases existentes...[/bold cyan]"):
                existing_testcases = client.get_testcases_by_norm(norm_id)

            # Map rule_id -> list of testcases for that rule
            testcases_by_rule: dict[str, list] = {}
            for tc in existing_testcases:
                if tc.rule_id not in testcases_by_rule:
                    testcases_by_rule[tc.rule_id] = []
                testcases_by_rule[tc.rule_id].append(tc)

            # Determine which rules need testcases for this target
            rules_to_process = []
            rules_skipped = []

            target_lower = target.lower()
            for rule in rules:
                existing_for_rule = testcases_by_rule.get(rule.id, [])

                # Check if this rule has a testcase for the target
                has_testcase_for_target = any(
                    tc.language and tc.language.lower() == target_lower for tc in existing_for_rule
                )

                if has_testcase_for_target and not force:
                    rules_skipped.append((rule, existing_for_rule))
                else:
                    rules_to_process.append(rule)

            # Print summary
            console.print()
            console.print(
                Panel(
                    f"[bold]📋 Norma:[/bold] {norm_name}\n"
                    f"[bold]🎯 Target:[/bold] {target.upper()}\n"
                    f"[bold]📊 Total de regras:[/bold] {len(rules)}\n"
                    f"[bold]✅ Regras a processar:[/bold] {len(rules_to_process)}\n"
                    f"[bold]⏭️  Regras puladas (já têm testcase):[/bold] {len(rules_skipped)}\n"
                    f"[bold]🔧 Modo:[/bold] {'DRY RUN' if dry_run else 'EXECUÇÃO'}",
                    title="[bold cyan]🧪 Gerador de TestCases[/bold cyan]",
                    border_style="cyan",
                )
            )

            if not rules_to_process:
                console.print(
                    "\n[green]✓ Todas as regras já possuem testcases para este target![/green]"
                )
                if rules_skipped and not force:
                    console.print(
                        f"\n[dim]Regras já com testcase para [bold]{target.upper()}[/bold]:[/dim]"
                    )
                    for rule, testcases in rules_skipped:
                        tc_langs = ", ".join(sorted({tc.language or "unknown" for tc in testcases}))
                        console.print(f"  • {rule.name[:50]} → {tc_langs}")
                    console.print("\n[dim]Use --force para recriar testcases existentes.[/dim]")
                return EXIT_SUCCESS

            # Dry run - just show what would be created
            if dry_run:
                table = Table(show_header=True, header_style="bold cyan")
                table.add_column("ID", style="dim")
                table.add_column("Nome da Regra")
                table.add_column("Categoria")
                table.add_column("Automatizável", justify="center")

                for rule in rules_to_process:
                    auto_badge = "✓" if rule.is_automatable else "✗"
                    table.add_row(
                        rule.id,
                        rule.name,
                        rule.category or "-",
                        auto_badge,
                    )

                console.print()
                console.print(
                    Panel(
                        table,
                        title=f"[bold]📝 Regras que receberiam testcases ({len(rules_to_process)})[/bold]",
                        border_style="cyan",
                    )
                )
                console.print("\n[dim]Execute sem --dry-run para criar os testcases.[/dim]")
                return EXIT_SUCCESS

            # Initialize generator
            if not openai_api_key:
                # This shouldn't happen since we check earlier, but mypy needs this
                raise ValueError("OPENAI_API_KEY is required")
            generator = TestCaseGenerator(
                api_key=openai_api_key,
                target=target_lower,
            )

            workspace = WorkspaceManager()

            # Process rules
            success_count = 0
            failed_rules = []

            console.print()
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("[cyan]Gerando testcases...", total=len(rules_to_process))

                for i, rule in enumerate(rules_to_process):
                    progress.update(
                        task,
                        description=f"[cyan]Processando: {rule.name[:40]}...",
                    )

                    try:
                        # Generate code with AI
                        generated = generator.generate(rule)

                        if generated:
                            # Create testcase via API
                            testcase = client.create_testcase(
                                norm_id=norm_id,
                                rule_id=rule.id,
                                name=f"TC: {rule.name}",
                                description=f"Caso de teste automatizado para: {rule.description or rule.name}",
                                language=target_lower,
                                code=generated.get("code"),
                                finder_code=generated.get("finder_py"),
                                validator_code=generated.get("validator_py"),
                            )

                            # Save to local workspace
                            workspace.save_generated_testcase(
                                norm_id=norm_id,
                                testcase_id=testcase.id,
                                generated=generated,
                            )

                            # Create examples if generated
                            if generated.get("compliant_html"):
                                client.create_example(
                                    testcase_id=testcase.id,
                                    name="compliant-example.html",
                                    html_content=generated["compliant_html"],
                                    is_compliant=True,
                                )

                            if generated.get("non_compliant_html"):
                                client.create_example(
                                    testcase_id=testcase.id,
                                    name="non-compliant-example.html",
                                    html_content=generated["non_compliant_html"],
                                    is_compliant=False,
                                )

                            success_count += 1
                        else:
                            failed_rules.append((rule, "Falha na geração com IA"))

                    except Exception as e:
                        failed_rules.append((rule, str(e)))

                    progress.update(task, advance=1)

                    # Delay between API calls to avoid rate limiting
                    if i < len(rules_to_process) - 1:
                        import time

                        time.sleep(delay)

            # Final summary
            console.print()
            if success_count > 0:
                console.print(
                    Panel(
                        f"[green]✓ {success_count} testcases criados com sucesso![/green]\n\n"
                        f"[dim]Testcases salvos em:[/dim] ./workspace/{norm_id}/testCases/\n\n"
                        "[dim]Próximos passos:[/dim]\n"
                        "  1. Revise o código gerado em ./workspace/\n"
                        "  2. Execute 'wally-dev run --testcase <id>' para testar\n"
                        "  3. Execute 'wally-dev push' para enviar alterações",
                        title="[bold green]Sucesso[/bold green]",
                        border_style="green",
                    )
                )

            if failed_rules:
                console.print()
                table = Table(show_header=True, header_style="bold red")
                table.add_column("Regra")
                table.add_column("Erro")

                for rule, error in failed_rules:
                    table.add_row(rule.name[:40], error[:60])

                console.print(
                    Panel(
                        table,
                        title=f"[bold red]⚠ {len(failed_rules)} falhas[/bold red]",
                        border_style="red",
                    )
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

    except RuleNotFoundError as e:
        console.print(
            Panel(
                f"[red]✗ {e.user_message}[/red]",
                title="[bold red]Regra Não Encontrada[/bold red]",
                border_style="red",
            )
        )
        return EXIT_ERROR_API

    except NormNotFoundError as e:
        console.print(
            Panel(
                f"[red]✗ {e.user_message}[/red]",
                title="[bold red]Norma Não Encontrada[/bold red]",
                border_style="red",
            )
        )
        return EXIT_ERROR_API

    except PermissionDeniedError as e:
        console.print(
            Panel(
                f"[red]✗ {e.user_message}[/red]",
                title="[bold red]Permissão Negada[/bold red]",
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

    except (APIError, WallyDevError) as e:
        console.print(
            Panel(
                f"[red]✗ {e.user_message}[/red]",
                title="[bold red]Erro[/bold red]",
                border_style="red",
            )
        )
        return EXIT_ERROR_API


@testcases.command("list")
@click.option(
    "--rule-id",
    "rule_id",
    type=str,
    help="Filtrar testcases por ID da regra",
)
def list_testcases(rule_id: Optional[str]) -> int:
    """
    Lista casos de teste da norma em checkout.

    Exibe todos os testcases existentes para a norma atualmente em checkout local.
    """
    config = LocalConfig()
    settings = Settings()

    if not config.is_logged_in:
        raise NotLoggedInError()

    locked_norms = config.get_locked_norms()
    if not locked_norms:
        console.print(
            Panel(
                "[red]✗ Nenhuma norma em checkout local.[/red]\n\n"
                "[dim]Faça checkout primeiro: wally-dev checkout --norm-id <id>[/dim]",
                title="[bold red]Checkout Necessário[/bold red]",
                border_style="red",
            )
        )
        return EXIT_ERROR_API

    norm_id = list(locked_norms.keys())[0]
    norm_info = locked_norms[norm_id]
    norm_name = norm_info.get("norm_name", norm_id)

    try:
        with config.create_api_client(settings) as client:
            with console.status("[bold cyan]Buscando testcases...[/bold cyan]"):
                testcases_list = client.get_testcases_by_norm(norm_id)

            if rule_id:
                testcases_list = [tc for tc in testcases_list if tc.rule_id == rule_id]

            if not testcases_list:
                console.print(
                    Panel(
                        f"[yellow]Nenhum testcase encontrado para a norma {norm_name}.[/yellow]",
                        title="[bold]🧪 TestCases[/bold]",
                        border_style="yellow",
                    )
                )
                return EXIT_SUCCESS

            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("ID", style="dim")
            table.add_column("Nome")
            table.add_column("Target")
            table.add_column("Enabled", justify="center")

            for tc in testcases_list:
                enabled_badge = "✓" if tc.enabled else "✗"
                table.add_row(
                    tc.id,
                    tc.name[:50] if tc.name else "-",
                    tc.language or "-",
                    enabled_badge,
                )

            console.print()
            console.print(
                Panel(
                    table,
                    title=f"[bold]🧪 TestCases de {norm_name} ({len(testcases_list)})[/bold]",
                    border_style="cyan",
                )
            )
            console.print()

            return EXIT_SUCCESS

    except Exception as e:
        console.print(
            Panel(
                f"[red]✗ Erro: {e}[/red]",
                title="[bold red]Erro[/bold red]",
                border_style="red",
            )
        )
        return EXIT_ERROR_API


@testcases.command("summary")
@click.option(
    "--target",
    "target",
    type=click.Choice(SUPPORTED_TARGETS, case_sensitive=False),
    help="Filtrar por um target específico (opcional)",
)
def summary_testcases(target: Optional[str]) -> int:
    """
    Exibe um resumo de cobertura de testcases para a norma em checkout.

    Mostra quais regras têm testcases para cada target e quais ainda estão faltando.

    \b
    Exemplos:
        # Resumo completo de todos os targets
        wally-dev testcases summary

        # Resumo apenas para HTML
        wally-dev testcases summary --target html
    """
    config = LocalConfig()
    settings = Settings()

    if not config.is_logged_in:
        raise NotLoggedInError()

    locked_norms = config.get_locked_norms()
    if not locked_norms:
        console.print(
            Panel(
                "[red]✗ Nenhuma norma em checkout local.[/red]\n\n"
                "[dim]Faça checkout primeiro: wally-dev checkout --norm-id <id>[/dim]",
                title="[bold red]Checkout Necessário[/bold red]",
                border_style="red",
            )
        )
        return EXIT_ERROR_API

    norm_id = list(locked_norms.keys())[0]
    norm_info = locked_norms[norm_id]
    norm_name = norm_info.get("norm_name", norm_id)

    try:
        with config.create_api_client(settings) as client:
            with console.status("[bold cyan]Buscando dados da norma...[/bold cyan]"):
                rules = client.get_rules_by_norm(norm_id)
                testcases = client.get_testcases_by_norm(norm_id)

            if not rules:
                console.print(
                    Panel(
                        f"[yellow]Nenhuma regra encontrada para a norma {norm_name}.[/yellow]",
                        title="[bold]📋 Resumo de Cobertura[/bold]",
                        border_style="yellow",
                    )
                )
                return EXIT_SUCCESS

            # Map rule_id -> list of testcases for that rule
            testcases_by_rule: dict[str, list] = {}
            for tc in testcases:
                if tc.rule_id not in testcases_by_rule:
                    testcases_by_rule[tc.rule_id] = []
                testcases_by_rule[tc.rule_id].append(tc)

            # Get all unique targets from testcases
            all_targets_set: set[str] = set()
            for tc_list in testcases_by_rule.values():
                for tc in tc_list:
                    if tc.language:
                        all_targets_set.add(tc.language.lower())
            all_targets: list[str] = sorted(all_targets_set) or list(SUPPORTED_TARGETS)

            # Filter by target if specified
            if target:
                target_lower = target.lower()
                if target_lower not in all_targets:
                    all_targets = [target_lower]
                else:
                    all_targets = [target_lower]

            # Build summary
            console.print()
            console.print(
                Panel(
                    f"[bold]📋 Norma:[/bold] {norm_name}\n"
                    f"[bold]📊 Total de regras:[/bold] {len(rules)}\n"
                    f"[bold]🎯 Targets com testcases:[/bold] {', '.join(t.upper() for t in all_targets) or 'Nenhum'}",
                    title="[bold cyan]📈 Resumo de Cobertura[/bold cyan]",
                    border_style="cyan",
                )
            )
            console.print()

            # Create a table for each target
            for tgt in all_targets:
                rules_with_tc = []
                rules_without_tc = []

                for rule in rules:
                    testcases_for_rule = testcases_by_rule.get(rule.id, [])
                    has_tc_for_target = any(
                        tc.language and tc.language.lower() == tgt for tc in testcases_for_rule
                    )

                    if has_tc_for_target:
                        rules_with_tc.append(rule)
                    else:
                        rules_without_tc.append(rule)

                # Build table
                table = Table(show_header=True, header_style="bold")
                table.add_column("Status", width=8)
                table.add_column("ID", style="dim", width=10)
                table.add_column("Regra")
                table.add_column("Categoria", width=15)
                table.add_column("Automática", width=10, justify="center")

                # Add rules with testcases
                for rule in rules_with_tc:
                    auto_badge = "✓" if rule.is_automatable else "✗"
                    table.add_row(
                        "[green]✓[/green]",
                        rule.id[:10],
                        rule.name,
                        rule.category or "-",
                        auto_badge,
                    )

                # Add rules without testcases
                for rule in rules_without_tc:
                    auto_badge = "✓" if rule.is_automatable else "✗"
                    table.add_row(
                        "[red]✗[/red]",
                        rule.id[:10],
                        rule.name,
                        rule.category or "-",
                        auto_badge,
                    )

                coverage = len(rules_with_tc) / len(rules) * 100 if rules else 0
                coverage_color = (
                    "green" if coverage >= 80 else "yellow" if coverage >= 50 else "red"
                )

                console.print(
                    Panel(
                        table,
                        title=f"[bold cyan]{tgt.upper()} - Cobertura: [{coverage_color}]{coverage:.0f}%[/{coverage_color}] "
                        f"([green]{len(rules_with_tc)}[/green]✓ / "
                        f"[red]{len(rules_without_tc)}[/red]✗)[/bold cyan]",
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

    except Exception as e:
        console.print(
            Panel(
                f"[red]✗ Erro: {e}[/red]",
                title="[bold red]Erro[/bold red]",
                border_style="red",
            )
        )
        return EXIT_ERROR_API
