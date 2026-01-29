"""
Test case runner for local execution.

Executes test cases in debug mode for local development.
Uses the same pattern as wally-cli: finder.py + validator.py
"""

import importlib.util
import sys
import time
import traceback
import warnings
from pathlib import Path
from typing import Any, Callable, Optional

from .exceptions import TestCaseExecutionError, TestCaseNotFoundError
from .models import ExampleTestCase, TestCase, TestCaseRunResult


class TestCaseRunner:
    """
    Runs test cases locally in debug mode.

    Test case code follows the wally-cli pattern:
    - finder.py: find(html_content) -> list of elements
    - validator.py: validate(element) -> bool
    """

    def __init__(self, verbose: bool = False, workspace_dir: Optional[Path] = None):
        """
        Initialize test case runner.

        Args:
            verbose: Enable verbose output
            workspace_dir: Base workspace directory
        """
        self.verbose = verbose
        self.workspace_dir = workspace_dir

    def _load_module_from_file(self, filepath: Path, module_name: str) -> Any:
        """
        Load a Python module from a file.

        Args:
            filepath: Path to the Python file
            module_name: Name to assign to the module

        Returns:
            Loaded module
        """
        spec = importlib.util.spec_from_file_location(module_name, filepath)
        if spec is None or spec.loader is None:
            raise ImportError(f"Não foi possível carregar o módulo: {filepath}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    def _load_finder_validator(
        self,
        testcase: TestCase,
        code_dir: Path,
    ) -> tuple[Callable, Callable]:
        """
        Load finder and validator functions from code directory.

        Args:
            testcase: Test case metadata
            code_dir: Directory containing finder.py and validator.py

        Returns:
            Tuple of (find_func, validate_func)

        Raises:
            TestCaseExecutionError: If files or functions not found
        """
        finder_file = code_dir / "finder.py"
        validator_file = code_dir / "validator.py"

        if not finder_file.exists():
            raise TestCaseExecutionError(
                message=f"Arquivo finder.py não encontrado em {code_dir}",
                hint="O caso de teste deve conter finder.py com função find(html_content)",
            )

        if not validator_file.exists():
            raise TestCaseExecutionError(
                message=f"Arquivo validator.py não encontrado em {code_dir}",
                hint="O caso de teste deve conter validator.py com função validate(element)",
            )

        # Add code_dir to sys.path for imports
        sys_path_modified = False
        if str(code_dir) not in sys.path:
            sys.path.insert(0, str(code_dir))
            sys_path_modified = True

        try:
            # Load modules
            finder_module = self._load_module_from_file(finder_file, f"finder_{testcase.id}")
            validator_module = self._load_module_from_file(
                validator_file, f"validator_{testcase.id}"
            )

            # Register finder in sys.modules so validator can import it
            sys.modules["finder"] = finder_module

            # Get functions
            find_func = getattr(finder_module, "find", None)
            validate_func = getattr(validator_module, "validate", None)

            if not find_func:
                raise TestCaseExecutionError(
                    message="Função 'find' não encontrada em finder.py",
                    hint="finder.py deve definir: def find(html_content: str) -> List[Element]",
                )

            if not validate_func:
                raise TestCaseExecutionError(
                    message="Função 'validate' não encontrada em validator.py",
                    hint="validator.py deve definir: def validate(element) -> bool",
                )

            return find_func, validate_func

        finally:
            # Clean up sys.path
            if sys_path_modified and str(code_dir) in sys.path:
                sys.path.remove(str(code_dir))

    def run_example(
        self,
        testcase: TestCase,
        example: ExampleTestCase,
        code_dir: Optional[Path] = None,
    ) -> TestCaseRunResult:
        """
        Run a test case against a specific example.

        Args:
            testcase: Test case to run
            example: Example to test against
            code_dir: Directory containing finder.py and validator.py

        Returns:
            TestCaseRunResult with execution details
        """
        start_time = time.time()

        try:
            if code_dir is None:
                raise TestCaseExecutionError(
                    message="code_dir é obrigatório para execução",
                    hint="Use workspace.get_testcase_code_dir(norm_id, testcase_id)",
                )

            # Load finder and validator
            find_func, validate_func = self._load_finder_validator(testcase, code_dir)

            # Execute finder to get elements
            with warnings.catch_warnings(record=True):
                warnings.simplefilter("always")
                elements = find_func(example.html)

            if elements is None:
                elements = []
            else:
                elements = list(elements)  # Materialize generator if needed

            # Validate each element
            stats = {"pass": 0, "fail": 0, "error": 0}
            issues = []

            for element in elements:
                try:
                    passed = validate_func(element)
                    if passed:
                        stats["pass"] += 1
                    else:
                        stats["fail"] += 1
                        issues.append(self._get_element_info(element))
                except Exception as ve:
                    stats["error"] += 1
                    issues.append(
                        {
                            "error": str(ve),
                            "element": str(element)[:100],
                        }
                    )

            # Determine overall result
            # compliant: all elements pass (or no elements found)
            # non-compliant: at least one element fails
            total_elements = len(elements)
            all_passed = stats["fail"] == 0 and stats["error"] == 0

            # Expected result
            expected_compliant = example.expected_result.lower() in (
                "compliant",
                "pass",
                "true",
                "passed",
                "valid",
            )

            # Test passes if result matches expectation
            test_passed = all_passed == expected_compliant

            execution_time = (time.time() - start_time) * 1000

            return TestCaseRunResult(
                test_case_id=testcase.id,
                example_id=example.id,
                passed=test_passed,
                expected="compliant" if expected_compliant else "non-compliant",
                actual="compliant" if all_passed else "non-compliant",
                execution_time_ms=execution_time,
                details={
                    "elements_found": total_elements,
                    "stats": stats,
                    "issues": issues[:5] if issues else [],  # Limit issues
                },
            )

        except TestCaseExecutionError:
            raise
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return TestCaseRunResult(
                test_case_id=testcase.id,
                example_id=example.id,
                passed=False,
                expected=example.expected_result,
                actual="error",
                error_message=str(e),
                execution_time_ms=execution_time,
            )

    def _get_element_info(self, element: Any) -> dict[str, Any]:
        """Extract info from an element for reporting."""
        info = {}

        # BeautifulSoup element
        if hasattr(element, "name"):
            info["tag"] = element.name
            if hasattr(element, "get"):
                info["id"] = element.get("id", "")
                info["class"] = element.get("class", [])
            if hasattr(element, "sourceline"):
                info["line"] = element.sourceline

        # lxml element
        elif hasattr(element, "tag"):
            info["tag"] = element.tag
            if hasattr(element, "get"):
                info["id"] = element.get("id", "")
                info["class"] = element.get("class", "")
            if hasattr(element, "sourceline"):
                info["line"] = element.sourceline

        # String representation as fallback
        try:
            snippet = str(element)
            if len(snippet) > 100:
                snippet = snippet[:100] + "..."
            info["snippet"] = snippet
        except Exception:
            pass

        return info

    def run_testcase(
        self,
        testcase: TestCase,
        code_dir: Path,
    ) -> dict[str, TestCaseRunResult]:
        """
        Run all examples for a test case.

        Args:
            testcase: Test case to run
            code_dir: Directory containing finder.py and validator.py

        Returns:
            Dict mapping example ID to result
        """
        results = {}

        for example in testcase.examples:
            result = self.run_example(testcase, example, code_dir)
            results[example.id] = result

        return results

    def run_testcase_single_example(
        self,
        testcase: TestCase,
        example_id: str,
        code_dir: Path,
    ) -> TestCaseRunResult:
        """
        Run a test case against a single example.

        Args:
            testcase: Test case to run
            example_id: ID of the example to test
            code_dir: Directory containing finder.py and validator.py

        Returns:
            TestCaseRunResult with execution details

        Raises:
            TestCaseNotFoundError: If example not found
        """
        example = None
        for ex in testcase.examples:
            if ex.id == example_id:
                example = ex
                break

        if example is None:
            raise TestCaseNotFoundError(
                message=f"Exemplo não encontrado: {example_id}",
                hint=f"Exemplos disponíveis: {[ex.id for ex in testcase.examples]}",
            )

        return self.run_example(testcase, example, code_dir)

    def debug_testcase(
        self,
        testcase: TestCase,
        example: ExampleTestCase,
        code_dir: Path,
    ) -> dict[str, Any]:
        """
        Run a test case in debug mode with detailed output.

        Args:
            testcase: Test case to run
            example: Example to test against
            code_dir: Directory containing finder.py and validator.py

        Returns:
            Dict with detailed debug information
        """
        debug_info: dict[str, Any] = {
            "testcase_id": testcase.id,
            "testcase_name": testcase.name,
            "example_id": example.id,
            "example_name": example.name,
            "expected_result": example.expected_result,
            "html_input": example.html,
            "code_dir": str(code_dir),
            "execution": {},
            "traceback": None,
        }

        try:
            find_func, validate_func = self._load_finder_validator(testcase, code_dir)

            start_time = time.time()

            # Run finder
            elements = find_func(example.html)
            if elements is None:
                elements = []
            else:
                elements = list(elements)

            finder_time = time.time()

            # Run validator on each element
            validation_results = []
            for i, element in enumerate(elements):
                try:
                    passed = validate_func(element)
                    validation_results.append(
                        {
                            "index": i,
                            "passed": passed,
                            "element": self._get_element_info(element),
                        }
                    )
                except Exception as ve:
                    validation_results.append(
                        {
                            "index": i,
                            "error": str(ve),
                            "element": self._get_element_info(element),
                        }
                    )

            execution_time = (time.time() - start_time) * 1000

            debug_info["execution"] = {
                "success": True,
                "elements_found": len(elements),
                "finder_time_ms": (finder_time - start_time) * 1000,
                "total_time_ms": execution_time,
                "validation_results": validation_results,
            }

        except Exception as e:
            debug_info["execution"] = {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }
            debug_info["traceback"] = traceback.format_exc()

        return debug_info
