"""
Run command for Wally Dev CLI.

Executes test cases locally in debug mode.
"""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from ..config import LocalConfig
from ..constants import EXIT_ERROR_API, EXIT_ERROR_AUTH, EXIT_ERROR_RUNTIME, EXIT_SUCCESS
from ..exceptions import (
    NotLoggedInError,
    TestCaseExecutionError,
    TestCaseNotFoundError,
    WallyDevError,
)
from ..models import ExampleTestCase, TestCaseRunResult
from ..runner import TestCaseRunner
from ..workspace import WorkspaceManager

console = Console()


def _find_norm_for_testcase(workspace: WorkspaceManager, testcase_id: str) -> Optional[str]:
    """Find which norm contains a test case."""
    for norm_id in workspace.list_norms():
        info = workspace.get_workspace_info(norm_id)
        if testcase_id in info.get("testcases", []):
            return norm_id
    return None


def _load_examples_from_dir(examples_dir: Path) -> list[ExampleTestCase]:
    """Load all examples from a directory structure.

    Structure expected:
        examples/
            compliant/
                example1.html
                example2.html
            non-compliant/
                example1.html
    """
    examples: list[ExampleTestCase] = []

    if not examples_dir.exists():
        return examples

    # Load compliant examples
    compliant_dir = examples_dir / "compliant"
    if compliant_dir.exists():
        for html_file in sorted(compliant_dir.glob("*.html")):
            with open(html_file, encoding="utf-8") as f:
                html_content = f.read()
            examples.append(
                ExampleTestCase(
                    _id=f"compliant/{html_file.name}",
                    name=f"✓ {html_file.stem}",
                    description=None,
                    html=html_content,
                    expectedResult="compliant",
                    explanation=f"Exemplo compliant: {html_file.name}",
                )
            )

    # Load non-compliant examples
    non_compliant_dir = examples_dir / "non-compliant"
    if non_compliant_dir.exists():
        for html_file in sorted(non_compliant_dir.glob("*.html")):
            with open(html_file, encoding="utf-8") as f:
                html_content = f.read()
            examples.append(
                ExampleTestCase(
                    _id=f"non-compliant/{html_file.name}",
                    name=f"✗ {html_file.stem}",
                    description=None,
                    html=html_content,
                    expectedResult="non-compliant",
                    explanation=f"Exemplo não-compliant: {html_file.name}",
                )
            )

    return examples


@click.command("run")
@click.option(
    "--testcase",
    "testcase_id",
    required=True,
    help="ID do caso de teste local para executar",
)
@click.option(
    "--example",
    "example_path",
    default=None,
    help="Caminho do exemplo específico (ex: compliant/page.html ou non-compliant/error.html)",
)
@click.option(
    "--norm-id",
    "norm_id",
    default=None,
    help="ID da norma (detectado automaticamente se omitido)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Mostra informações detalhadas de debug",
)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    help="Mostra elementos encontrados pelo finder e resultado de cada validate",
)
@click.option(
    "--show-code",
    is_flag=True,
    help="Mostra o código do caso de teste",
)
def run(
    testcase_id: str,
    example_path: Optional[str] = None,
    norm_id: Optional[str] = None,
    verbose: bool = False,
    debug: bool = False,
    show_code: bool = False,
) -> int:
    """
    Executa um caso de teste localmente em modo debug.

    Permite testar a implementação do caso de teste contra
    os exemplos definidos (cenários de passa/falha).


    Exemplos:
        wally-dev run --testcase abc123
        wally-dev run --testcase abc123 --example ex1
        wally-dev run --testcase abc123 --verbose --show-code
    """
    config = LocalConfig()
    workspace = WorkspaceManager()
    runner = TestCaseRunner(verbose=verbose)

    # Check login
    if not config.is_logged_in:
        raise NotLoggedInError()

    try:
        # Find norm if not provided
        if not norm_id:
            norm_id = _find_norm_for_testcase(workspace, testcase_id)
            if not norm_id:
                raise TestCaseNotFoundError(
                    message=f"Caso de teste não encontrado no workspace: {testcase_id}",
                    hint="Verifique se você fez checkout da norma correspondente.",
                )

        # Load test case
        testcase = workspace.load_testcase(norm_id, testcase_id)

        # Get code directory
        code_dir = workspace.get_testcase_code_dir(norm_id, testcase_id)
        if not code_dir.exists():
            raise TestCaseNotFoundError(
                message=f"Diretório de código não encontrado: {code_dir}",
                hint="O caso de teste deve conter uma pasta 'code/' com finder.py e validator.py",
            )

        # Get examples directory and count
        examples_dir = workspace.get_testcase_dir(norm_id, testcase_id) / "examples"
        example_count = len(_load_examples_from_dir(examples_dir))

        # Show test case info
        console.print()
        console.print(
            Panel(
                f"[bold]{testcase.name}[/bold]\n\n"
                f"[dim]ID:[/dim] {testcase_id}\n"
                f"[dim]Norma:[/dim] {norm_id}\n"
                f"[dim]Exemplos:[/dim] {example_count}",
                title="[bold cyan]🧪 Caso de Teste[/bold cyan]",
                border_style="cyan",
            )
        )

        # Show code if requested
        if show_code:
            # Show finder.py code
            finder_file = code_dir / "finder.py"
            validator_file = code_dir / "validator.py"
            if finder_file.exists():
                console.print("\n[bold]finder.py:[/bold]")
                with open(finder_file, encoding="utf-8") as f:
                    code_content = f.read()
                syntax = Syntax(code_content, "python", theme="monokai", line_numbers=True)
                console.print(syntax)
            if validator_file.exists():
                console.print("\n[bold]validator.py:[/bold]")
                with open(validator_file, encoding="utf-8") as f:
                    code_content = f.read()
                syntax = Syntax(code_content, "python", theme="monokai", line_numbers=True)
                console.print(syntax)
            console.print()

        # Run specific example or all examples
        if example_path:
            # Run single example from file path (e.g., compliant/page.html)
            example_file = examples_dir / example_path

            if not example_file.exists():
                raise TestCaseNotFoundError(
                    message=f"Exemplo não encontrado: {example_path}",
                    hint=f"Verifique se o arquivo existe em: {examples_dir}",
                )

            console.print(f"\n[bold]Executando exemplo: {example_path}[/bold]\n")

            # Load HTML content from file
            with open(example_file, encoding="utf-8") as f:
                html_content = f.read()

            # Determine expected result from path
            expected_result = (
                "compliant" if example_path.startswith("compliant") else "non-compliant"
            )

            # Create example object
            example = ExampleTestCase(
                _id=example_file.stem,
                name=example_file.name,
                description=None,
                html=html_content,
                expectedResult=expected_result,
                explanation=f"Exemplo de {example_path}",
            )

            # Show example details
            console.print(f"[dim]Arquivo:[/dim] {example_path}")
            console.print(f"[dim]Resultado esperado:[/dim] {expected_result}")
            if verbose:
                console.print("\n[dim]HTML de entrada:[/dim]")
                html_syntax = Syntax(
                    html_content[:500] + ("..." if len(html_content) > 500 else ""),
                    "html",
                    theme="monokai",
                )
                console.print(html_syntax)

            console.print()

            # Execute
            if debug:
                debug_info = runner.debug_testcase(testcase, example, code_dir)
                _show_debug_output(debug_info)
                # Also show final pass/fail
                execution = debug_info.get("execution", {})
                if execution.get("success"):
                    validation_results = execution.get("validation_results", [])
                    all_passed = all(
                        vr.get("passed") and "error" not in vr for vr in validation_results
                    )
                    expected_compliant = example.expected_result.lower() in (
                        "compliant",
                        "pass",
                        "true",
                    )
                    test_passed = all_passed == expected_compliant
                    if test_passed:
                        console.print(
                            Panel(
                                f"[green]✓ PASSOU[/green] (esperado: {example.expected_result})",
                                border_style="green",
                            )
                        )
                    else:
                        console.print(
                            Panel(
                                f"[red]✗ FALHOU[/red] (esperado: {example.expected_result}, obtido: {'compliant' if all_passed else 'non-compliant'})",
                                border_style="red",
                            )
                        )
            elif verbose:
                debug_info = runner.debug_testcase(testcase, example, code_dir)
                _show_debug_output(debug_info)
            else:
                single_result = runner.run_example(testcase, example, code_dir)
                if single_result:
                    _show_result(single_result)

        else:
            # Run all examples from examples/ directory
            examples = _load_examples_from_dir(examples_dir)

            if not examples:
                console.print("[yellow]Nenhum example encontrado na pasta examples/[/yellow]")
                return EXIT_SUCCESS

            console.print(f"\n[bold]Executando todos os exemplos ({len(examples)}):[/bold]\n")

            results = {}
            for example in examples:
                if debug:
                    # Show debug info for each example
                    console.print(f"\n[bold cyan]── {example.id} ──[/bold cyan]")
                    debug_info = runner.debug_testcase(testcase, example, code_dir)
                    _show_debug_output(debug_info)

                    # Calculate result for summary
                    execution = debug_info.get("execution", {})
                    if execution.get("success"):
                        validation_results = execution.get("validation_results", [])
                        all_passed = all(
                            vr.get("passed") and "error" not in vr for vr in validation_results
                        )
                        expected_compliant = example.expected_result.lower() in (
                            "compliant",
                            "pass",
                            "true",
                        )
                        test_passed = all_passed == expected_compliant
                        from ..models import TestCaseRunResult

                        results[example.id] = TestCaseRunResult(
                            test_case_id=testcase.id,
                            example_id=example.id,
                            passed=test_passed,
                            expected="compliant" if expected_compliant else "non-compliant",
                            actual="compliant" if all_passed else "non-compliant",
                            execution_time_ms=execution.get("total_time_ms", 0),
                        )
                else:
                    run_result: Optional[TestCaseRunResult] = runner.run_example(
                        testcase, example, code_dir
                    )
                    if run_result:
                        results[example.id] = run_result

            # Build results table
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Exemplo", style="dim")
            table.add_column("Esperado")
            table.add_column("Obtido")
            table.add_column("Status")
            table.add_column("Tempo (ms)", justify="right")

            passed_count = 0
            for example in examples:
                result = results.get(example.id)
                if result:
                    status = "[green]✓ PASS[/green]" if result.passed else "[red]✗ FAIL[/red]"
                    if result.passed:
                        passed_count += 1
                    table.add_row(
                        example.name[:30] + ("..." if len(example.name) > 30 else ""),
                        result.expected,
                        result.actual,
                        status,
                        f"{result.execution_time_ms:.2f}",
                    )

            console.print(table)

            # Summary
            total = len(examples)
            console.print()
            if passed_count == total:
                console.print(
                    Panel(
                        f"[green]✓ Todos os testes passaram! ({passed_count}/{total})[/green]",
                        border_style="green",
                    )
                )
            else:
                console.print(
                    Panel(
                        f"[red]✗ {total - passed_count} teste(s) falharam ({passed_count}/{total} passaram)[/red]",
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

    except TestCaseNotFoundError as e:
        console.print(
            Panel(
                f"[red]✗ {e.user_message}[/red]" + (f"\n\n[dim]{e.hint}[/dim]" if e.hint else ""),
                title="[bold red]Caso de Teste Não Encontrado[/bold red]",
                border_style="red",
            )
        )
        return EXIT_ERROR_API

    except TestCaseExecutionError as e:
        console.print(
            Panel(
                f"[red]✗ {e.user_message}[/red]" + (f"\n\n[dim]{e.hint}[/dim]" if e.hint else ""),
                title="[bold red]Erro de Execução[/bold red]",
                border_style="red",
            )
        )
        return EXIT_ERROR_RUNTIME

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
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        return EXIT_ERROR_RUNTIME


def _show_result(result: TestCaseRunResult) -> None:
    """Show test result in a formatted way."""
    if result.passed:
        console.print(
            Panel(
                f"[green]✓ PASSOU[/green]\n\n"
                f"[dim]Esperado:[/dim] {result.expected}\n"
                f"[dim]Obtido:[/dim] {result.actual}\n"
                f"[dim]Tempo:[/dim] {result.execution_time_ms:.2f}ms",
                title="[bold green]Resultado[/bold green]",
                border_style="green",
            )
        )
    else:
        error_msg = f"\n[dim]Erro:[/dim] {result.error_message}" if result.error_message else ""
        console.print(
            Panel(
                f"[red]✗ FALHOU[/red]\n\n"
                f"[dim]Esperado:[/dim] {result.expected}\n"
                f"[dim]Obtido:[/dim] {result.actual}\n"
                f"[dim]Tempo:[/dim] {result.execution_time_ms:.2f}ms{error_msg}",
                title="[bold red]Resultado[/bold red]",
                border_style="red",
            )
        )


def _show_debug_output(debug_info: dict) -> None:
    """Show detailed debug output with finder elements and validate results."""
    execution = debug_info.get("execution", {})

    if execution.get("success"):
        elements_found = execution.get("elements_found", 0)
        finder_time = execution.get("finder_time_ms", 0)
        total_time = execution.get("total_time_ms", 0)

        console.print(
            Panel(
                f"[green]Execução bem sucedida[/green]\n\n"
                f"[dim]Elementos encontrados:[/dim] {elements_found}\n"
                f"[dim]Tempo finder:[/dim] {finder_time:.2f}ms\n"
                f"[dim]Tempo total:[/dim] {total_time:.2f}ms",
                title="[bold cyan]🔍 Debug Output[/bold cyan]",
                border_style="cyan",
            )
        )

        # Show validation results for each element
        validation_results = execution.get("validation_results", [])
        if validation_results:
            console.print("\n[bold]📋 Elementos e Validações:[/bold]")

            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("#", justify="right", style="dim")
            table.add_column("Linha", justify="right")
            table.add_column("Tag")
            table.add_column("validate()", justify="center")
            table.add_column("Snippet", max_width=60)

            for vr in validation_results:
                idx = vr.get("index", "?")
                elem = vr.get("element", {})

                line = elem.get("line", "-")
                line_str = str(line) if line else "-"

                tag = elem.get("tag", "?")

                snippet = elem.get("snippet", "")[:60]
                if len(elem.get("snippet", "")) > 60:
                    snippet += "..."

                if "error" in vr:
                    status = f"[red]ERROR: {vr['error'][:20]}[/red]"
                elif vr.get("passed"):
                    status = "[green]✓ True[/green]"
                else:
                    status = "[red]✗ False[/red]"

                table.add_row(str(idx), line_str, tag, status, snippet)

            console.print(table)

            # Summary
            passed = sum(1 for vr in validation_results if vr.get("passed") and "error" not in vr)
            failed = sum(
                1 for vr in validation_results if not vr.get("passed") and "error" not in vr
            )
            errors = sum(1 for vr in validation_results if "error" in vr)

            console.print(
                f"\n[dim]Resumo: {passed} passou, {failed} falhou, {errors} erro(s)[/dim]"
            )
        else:
            console.print("\n[yellow]Nenhum elemento encontrado pelo finder[/yellow]")
    else:
        console.print(
            Panel(
                f"[red]Erro na execução[/red]\n\n"
                f"[dim]Tipo:[/dim] {execution.get('error_type')}\n"
                f"[dim]Mensagem:[/dim] {execution.get('error')}",
                title="[bold red]Debug Output[/bold red]",
                border_style="red",
            )
        )

        if debug_info.get("traceback"):
            console.print("\n[bold]Traceback:[/bold]")
            console.print(Syntax(debug_info["traceback"], "python", theme="monokai"))
