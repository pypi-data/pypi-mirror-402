"""
Workspace management for Wally Dev CLI.

Handles local file operations for test cases.
"""

import json
from pathlib import Path
from typing import Optional

from .constants import TESTCASES_DIR_NAME, WORKSPACE_DIR_NAME
from .exceptions import TestCaseNotFoundError, WorkspaceError
from .models import TestCase


class WorkspaceManager:
    """
    Manages the local workspace for test case development.

    Directory structure:
        ./workspace/
            [normId]/
                testCases/
                    [testCaseId].json
                    [testCaseId].py  (implementation)
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize workspace manager.

        Args:
            base_path: Base directory for workspace. Defaults to current directory.
        """
        self.base_path = base_path or Path.cwd()
        self.workspace_dir = self.base_path / WORKSPACE_DIR_NAME

    def get_norm_dir(self, norm_id: str) -> Path:
        """Get the directory for a specific norm."""
        return self.workspace_dir / norm_id

    def get_testcases_dir(self, norm_id: str) -> Path:
        """Get the test cases directory for a specific norm."""
        return self.get_norm_dir(norm_id) / TESTCASES_DIR_NAME

    def get_testcase_dir(self, norm_id: str, testcase_id: str) -> Path:
        """Get the directory for a specific test case."""
        return self.get_testcases_dir(norm_id) / testcase_id

    def get_testcase_code_dir(self, norm_id: str, testcase_id: str) -> Path:
        """Get the code directory for a specific test case."""
        return self.get_testcase_dir(norm_id, testcase_id) / "code"

    def ensure_norm_dir(self, norm_id: str) -> Path:
        """
        Ensure the norm directory structure exists.

        Returns:
            Path to the norm directory
        """
        norm_dir = self.get_norm_dir(norm_id)
        testcases_dir = self.get_testcases_dir(norm_id)

        norm_dir.mkdir(parents=True, exist_ok=True)
        testcases_dir.mkdir(parents=True, exist_ok=True)

        return norm_dir

    def save_testcase(self, norm_id: str, testcase: TestCase) -> Path:
        """
        Save a test case to the local workspace.

        Creates two files:
        - [testCaseId].json: Full test case data
        - [testCaseId].py: Implementation code (if present)

        Args:
            norm_id: Norm identifier
            testcase: Test case to save

        Returns:
            Path to the saved JSON file
        """
        testcases_dir = self.get_testcases_dir(norm_id)
        testcases_dir.mkdir(parents=True, exist_ok=True)

        # Save JSON data
        json_path = testcases_dir / f"{testcase.id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(testcase.to_file_dict(), f, indent=2, ensure_ascii=False)

        # Save implementation code separately if present
        if testcase.code:
            code_path = testcases_dir / f"{testcase.id}.py"
            with open(code_path, "w", encoding="utf-8") as f:
                f.write(testcase.code)

        return json_path

    def save_testcases(self, norm_id: str, testcases: list[TestCase]) -> int:
        """
        Save multiple test cases to the local workspace.

        Args:
            norm_id: Norm identifier
            testcases: List of test cases to save

        Returns:
            Number of test cases saved
        """
        self.ensure_norm_dir(norm_id)
        count = 0
        for tc in testcases:
            self.save_testcase(norm_id, tc)
            count += 1
        return count

    def extract_testcases_zip(self, norm_id: str, zip_content: bytes) -> int:
        """
        Extract test cases from a ZIP file into the workspace.

        The ZIP structure from the backend is:
            <testCaseId>/
                testcase.json
                code/
                    finder.py
                    validator.py
                    runner.py (optional)
                    requirements.txt

        This method extracts to:
            workspace/<normId>/testCases/
                <testCaseId>/
                    testcase.json
                    code/
                        finder.py
                        validator.py
                        ...

        Args:
            norm_id: Norm identifier
            zip_content: ZIP file content as bytes

        Returns:
            Number of test cases extracted

        Raises:
            WorkspaceError: If extraction fails
        """
        import io
        import zipfile

        self.ensure_norm_dir(norm_id)
        testcases_dir = self.get_testcases_dir(norm_id)

        try:
            with zipfile.ZipFile(io.BytesIO(zip_content), "r") as zip_ref:
                # Get all entries in the ZIP
                entries = zip_ref.namelist()

                # Find unique test case directories
                # Structure: <testcase_id>/... or <testcase_id>/code/...
                testcase_ids = set()
                for entry in entries:
                    parts = entry.split("/")
                    if len(parts) >= 1 and parts[0]:
                        testcase_ids.add(parts[0])

                # Extract all files preserving structure
                for entry in entries:
                    if entry.endswith("/"):
                        continue  # Skip directories

                    parts = entry.split("/")
                    if len(parts) < 1:
                        continue

                    # Get testcase_id and relative path
                    testcase_id = parts[0]
                    relative_path = "/".join(parts[1:]) if len(parts) > 1 else ""

                    if not relative_path:
                        continue  # Skip if no file

                    # Create target path preserving subdirectories (like code/)
                    target_path = testcases_dir / testcase_id / relative_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)

                    # Extract file
                    with zip_ref.open(entry) as src, open(target_path, "wb") as dst:
                        dst.write(src.read())

                return len(testcase_ids)

        except zipfile.BadZipFile as e:
            raise WorkspaceError(
                message=f"Arquivo ZIP inválido: {e}",
                user_message="O arquivo de exportação está corrompido.",
            ) from e
        except Exception as e:
            raise WorkspaceError(
                message=f"Erro ao extrair ZIP: {e}",
                user_message="Falha ao extrair os casos de teste.",
            ) from e

    def extract_examples_zip(self, norm_id: str, zip_content: bytes) -> int:
        """
        Extract examples from a ZIP file into the workspace.

        The ZIP structure from the backend is:
            <testCaseId>/
                examples/
                    compliant/
                        example1.html
                        example2.html
                    non-compliant/
                        example1.html

        This method extracts to:
            workspace/<normId>/testCases/
                <testCaseId>/
                    examples/
                        compliant/
                            example1.html
                        non-compliant/
                            example1.html

        Args:
            norm_id: Norm identifier
            zip_content: ZIP file content as bytes

        Returns:
            Number of examples extracted

        Raises:
            WorkspaceError: If extraction fails
        """
        import io
        import zipfile

        testcases_dir = self.get_testcases_dir(norm_id)

        try:
            with zipfile.ZipFile(io.BytesIO(zip_content), "r") as zip_ref:
                entries = zip_ref.namelist()
                examples_count = 0

                for entry in entries:
                    if entry.endswith("/"):
                        continue  # Skip directories

                    parts = entry.split("/")
                    if len(parts) < 4:  # testcase_id/examples/type/file
                        continue

                    testcase_id = parts[0]
                    relative_path = "/".join(parts[1:])  # examples/compliant/file.html

                    # Create target path
                    target_path = testcases_dir / testcase_id / relative_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)

                    # Extract file
                    with zip_ref.open(entry) as src, open(target_path, "wb") as dst:
                        dst.write(src.read())

                    examples_count += 1

                return examples_count

        except zipfile.BadZipFile as e:
            raise WorkspaceError(
                message=f"Arquivo ZIP inválido: {e}",
                user_message="O arquivo de exportação está corrompido.",
            ) from e
        except Exception as e:
            raise WorkspaceError(
                message=f"Erro ao extrair ZIP de examples: {e}",
                user_message="Falha ao extrair os examples.",
            ) from e

    def load_testcase(self, norm_id: str, testcase_id: str) -> TestCase:
        """
        Load a test case from the local workspace.

        Args:
            norm_id: Norm identifier
            testcase_id: Test case identifier

        Returns:
            Loaded test case

        Raises:
            TestCaseNotFoundError: If test case file doesn't exist
        """
        testcase_dir = self.get_testcases_dir(norm_id) / testcase_id
        json_path = testcase_dir / "testcase.json"

        if not json_path.exists():
            raise TestCaseNotFoundError(
                message=f"Caso de teste não encontrado localmente: {testcase_id}"
            )

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        # Ensure the testcase has an ID (from folder name if not in JSON)
        if "_id" not in data and "id" not in data:
            data["_id"] = testcase_id

        # Load implementation code from code/ directory
        code_dir = testcase_dir / "code"
        if code_dir.exists():
            # Look for main.py or any .py file
            main_py = code_dir / "main.py"
            if main_py.exists():
                with open(main_py, encoding="utf-8") as f:
                    data["code"] = f.read()
            else:
                # Find first .py file
                py_files = list(code_dir.glob("*.py"))
                if py_files:
                    with open(py_files[0], encoding="utf-8") as f:
                        data["code"] = f.read()

        # Load examples from examples/ directory
        examples_dir = testcase_dir / "examples"
        if examples_dir.exists():
            examples = []

            # Load compliant examples
            compliant_dir = examples_dir / "compliant"
            if compliant_dir.exists():
                for html_file in compliant_dir.glob("*.html"):
                    with open(html_file, encoding="utf-8") as f:
                        html_content = f.read()
                    examples.append(
                        {
                            "id": html_file.stem,
                            "name": html_file.stem.replace("-", " ").replace("_", " ").title(),
                            "html": html_content,
                            "expectedResult": "compliant",
                            "explanation": f"Exemplo compliant: {html_file.stem}",
                        }
                    )

            # Load non-compliant examples
            non_compliant_dir = examples_dir / "non-compliant"
            if non_compliant_dir.exists():
                for html_file in non_compliant_dir.glob("*.html"):
                    with open(html_file, encoding="utf-8") as f:
                        html_content = f.read()
                    examples.append(
                        {
                            "id": html_file.stem,
                            "name": html_file.stem.replace("-", " ").replace("_", " ").title(),
                            "html": html_content,
                            "expectedResult": "non-compliant",
                            "explanation": f"Exemplo não-compliant: {html_file.stem}",
                        }
                    )

            if examples:
                data["examples"] = examples

        return TestCase.from_api_response(data)

    def load_all_testcases(self, norm_id: str) -> list[TestCase]:
        """
        Load all test cases from the local workspace for a norm.

        Args:
            norm_id: Norm identifier

        Returns:
            List of loaded test cases
        """
        testcases_dir = self.get_testcases_dir(norm_id)
        testcases: list[TestCase] = []

        if not testcases_dir.exists():
            return testcases

        # Each testcase is a directory with testcase.json inside
        for testcase_dir in testcases_dir.iterdir():
            if testcase_dir.is_dir() and (testcase_dir / "testcase.json").exists():
                testcase_id = testcase_dir.name
                try:
                    tc = self.load_testcase(norm_id, testcase_id)
                    testcases.append(tc)
                except (json.JSONDecodeError, KeyError):
                    # Skip malformed files
                    continue

        return testcases

    def get_modified_testcases(
        self, norm_id: str, original_testcases: list[TestCase]
    ) -> list[TestCase]:
        """
        Compare local test cases with originals and return modified ones.

        Args:
            norm_id: Norm identifier
            original_testcases: Original test cases from server

        Returns:
            List of test cases that have been modified locally
        """
        original_map = {tc.id: tc for tc in original_testcases}
        local_testcases = self.load_all_testcases(norm_id)
        modified = []

        for local_tc in local_testcases:
            original_tc = original_map.get(local_tc.id)
            if original_tc is None:
                # New test case
                modified.append(local_tc)
            elif self._has_changes(original_tc, local_tc):
                modified.append(local_tc)

        return modified

    def _has_changes(self, original: TestCase, local: TestCase) -> bool:
        """Check if local test case has changes compared to original."""
        # Compare code
        if original.code != local.code:
            return True

        # Compare examples
        if len(original.examples) != len(local.examples):
            return True

        orig_examples = {ex.id: ex for ex in original.examples}
        for local_ex in local.examples:
            orig_ex = orig_examples.get(local_ex.id)
            if orig_ex is None:
                return True
            if (
                orig_ex.html != local_ex.html
                or orig_ex.expected_result != local_ex.expected_result
                or orig_ex.explanation != local_ex.explanation
            ):
                return True

        return False

    def list_norms(self) -> list[str]:
        """
        List all norm IDs in the workspace.

        Returns:
            List of norm IDs
        """
        if not self.workspace_dir.exists():
            return []

        return [
            d.name
            for d in self.workspace_dir.iterdir()
            if d.is_dir() and (d / TESTCASES_DIR_NAME).exists()
        ]

    def delete_norm(self, norm_id: str) -> bool:
        """
        Delete a norm's workspace.

        Args:
            norm_id: Norm identifier

        Returns:
            True if deleted, False if didn't exist
        """
        import shutil

        norm_dir = self.get_norm_dir(norm_id)
        if norm_dir.exists():
            shutil.rmtree(norm_dir)
            return True
        return False

    def get_workspace_info(self, norm_id: str) -> dict:
        """
        Get information about a norm's workspace.

        Args:
            norm_id: Norm identifier

        Returns:
            Dictionary with workspace info
        """
        testcases_dir = self.get_testcases_dir(norm_id)
        info = {
            "norm_id": norm_id,
            "path": str(self.get_norm_dir(norm_id)),
            "exists": testcases_dir.exists(),
            "testcase_count": 0,
            "testcases": [],
        }

        if testcases_dir.exists():
            # Each testcase is a directory with testcase.json inside
            testcase_dirs = [
                d for d in testcases_dir.iterdir() if d.is_dir() and (d / "testcase.json").exists()
            ]
            info["testcase_count"] = len(testcase_dirs)
            info["testcases"] = [d.name for d in testcase_dirs]

        return info

    def save_generated_testcase(
        self,
        norm_id: str,
        testcase_id: str,
        generated: dict[str, str],
    ) -> Path:
        """
        Save generated test case files to the workspace.

        Creates the following structure:
            workspace/<normId>/testCases/<testCaseId>/
                testcase.json
                code/
                    finder.py
                    validator.py
                    requirements.txt
                examples/
                    compliant/
                        compliant-example.html
                    non-compliant/
                        non-compliant-example.html

        Args:
            norm_id: Norm identifier
            testcase_id: Test case identifier
            generated: Dictionary with generated code:
                - finder_py: finder.py code
                - validator_py: validator.py code
                - compliant_html: compliant example HTML
                - non_compliant_html: non-compliant example HTML
                - code: combined code (optional)

        Returns:
            Path to the test case directory
        """
        testcase_dir = self.get_testcase_dir(norm_id, testcase_id)
        code_dir = testcase_dir / "code"
        examples_dir = testcase_dir / "examples"
        compliant_dir = examples_dir / "compliant"
        non_compliant_dir = examples_dir / "non-compliant"

        # Create directory structure
        for directory in [code_dir, compliant_dir, non_compliant_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Save testcase.json with metadata
        testcase_json = testcase_dir / "testcase.json"
        metadata = {
            "_id": testcase_id,
            "normId": norm_id,
            "generatedBy": "wally-dev-cli",
            "hasCode": bool(generated.get("finder_py") or generated.get("validator_py")),
            "hasExamples": bool(
                generated.get("compliant_html") or generated.get("non_compliant_html")
            ),
        }
        with open(testcase_json, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # Save finder.py
        if generated.get("finder_py"):
            finder_path = code_dir / "finder.py"
            with open(finder_path, "w", encoding="utf-8") as f:
                f.write(generated["finder_py"])

        # Save validator.py
        if generated.get("validator_py"):
            validator_path = code_dir / "validator.py"
            with open(validator_path, "w", encoding="utf-8") as f:
                f.write(generated["validator_py"])

        # Save combined code if available
        if generated.get("code"):
            main_path = code_dir / "main.py"
            with open(main_path, "w", encoding="utf-8") as f:
                f.write(generated["code"])

        # Save requirements.txt
        requirements_path = code_dir / "requirements.txt"
        requirements_content = "beautifulsoup4>=4.12.0\n"
        with open(requirements_path, "w", encoding="utf-8") as f:
            f.write(requirements_content)

        # Save compliant example
        if generated.get("compliant_html"):
            compliant_path = compliant_dir / "compliant-example.html"
            with open(compliant_path, "w", encoding="utf-8") as f:
                f.write(generated["compliant_html"])

        # Save non-compliant example
        if generated.get("non_compliant_html"):
            non_compliant_path = non_compliant_dir / "non-compliant-example.html"
            with open(non_compliant_path, "w", encoding="utf-8") as f:
                f.write(generated["non_compliant_html"])

        return testcase_dir

    # =========================================================================
    # Checksum-based change detection
    # =========================================================================

    CHECKSUMS_FILE = ".wally-checksums.json"

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute MD5 hash of a file."""
        import hashlib

        md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5.update(chunk)
        return md5.hexdigest()

    def _get_checksums_path(self, norm_id: str) -> Path:
        """Get path to checksums file for a norm."""
        return self.get_norm_dir(norm_id) / self.CHECKSUMS_FILE

    def save_checksums(self, norm_id: str) -> dict[str, dict[str, str]]:
        """
        Compute and save checksums for all files in a norm's workspace.

        Saves to .wally-checksums.json in the norm directory.

        Returns:
            Dict mapping testcase_id -> {filepath: hash}
        """
        testcases_dir = self.get_testcases_dir(norm_id)
        checksums: dict[str, dict[str, str]] = {}

        if not testcases_dir.exists():
            return checksums

        for testcase_dir in testcases_dir.iterdir():
            if not testcase_dir.is_dir():
                continue

            testcase_id = testcase_dir.name
            checksums[testcase_id] = {}

            # Hash all files recursively
            for file_path in testcase_dir.rglob("*"):
                if file_path.is_file():
                    relative_path = str(file_path.relative_to(testcase_dir))
                    checksums[testcase_id][relative_path] = self._compute_file_hash(file_path)

        # Save to file
        checksums_path = self._get_checksums_path(norm_id)
        with open(checksums_path, "w", encoding="utf-8") as f:
            json.dump(checksums, f, indent=2)

        return checksums

    def load_checksums(self, norm_id: str) -> dict[str, dict[str, str]]:
        """
        Load saved checksums for a norm.

        Returns:
            Dict mapping testcase_id -> {filepath: hash}, or empty dict if not found
        """
        checksums_path = self._get_checksums_path(norm_id)
        if not checksums_path.exists():
            return {}

        try:
            with open(checksums_path, encoding="utf-8") as f:
                result: dict[str, dict[str, str]] = json.load(f)
                return result
        except (OSError, json.JSONDecodeError):
            return {}

    def get_locally_modified_testcases(self, norm_id: str) -> list[str]:
        """
        Get list of testcase IDs that have been modified since checkout.

        Compares current file hashes with saved checksums.

        Returns:
            List of testcase IDs with local modifications
        """
        saved_checksums = self.load_checksums(norm_id)
        if not saved_checksums:
            # No checksums saved - can't determine modifications
            return []

        testcases_dir = self.get_testcases_dir(norm_id)
        if not testcases_dir.exists():
            return []

        modified = []

        for testcase_dir in testcases_dir.iterdir():
            if not testcase_dir.is_dir():
                continue

            testcase_id = testcase_dir.name
            saved_hashes = saved_checksums.get(testcase_id, {})

            # Check for modifications
            is_modified = False

            # Get current files
            current_files = set()
            for file_path in testcase_dir.rglob("*"):
                if file_path.is_file():
                    relative_path = str(file_path.relative_to(testcase_dir))
                    current_files.add(relative_path)

                    # Check if file is new or modified
                    saved_hash = saved_hashes.get(relative_path)
                    if saved_hash is None:
                        # New file
                        is_modified = True
                        break

                    current_hash = self._compute_file_hash(file_path)
                    if current_hash != saved_hash:
                        # Modified file
                        is_modified = True
                        break

            # Check for deleted files
            if not is_modified:
                saved_files = set(saved_hashes.keys())
                if saved_files - current_files:
                    # Some files were deleted
                    is_modified = True

            if is_modified:
                modified.append(testcase_id)

        return modified

    def get_testcase_changes(self, norm_id: str, testcase_id: str) -> dict:
        """
        Get detailed changes for a specific testcase.

        Returns:
            Dict with 'added', 'modified', 'deleted' lists of file paths
        """
        saved_checksums = self.load_checksums(norm_id)
        saved_hashes = saved_checksums.get(testcase_id, {})

        testcase_dir = self.get_testcase_dir(norm_id, testcase_id)

        changes: dict[str, list[str]] = {
            "added": [],
            "modified": [],
            "deleted": [],
        }

        if not testcase_dir.exists():
            changes["deleted"] = list(saved_hashes.keys())
            return changes

        # Check current files
        current_files = {}
        for file_path in testcase_dir.rglob("*"):
            if file_path.is_file():
                relative_path = str(file_path.relative_to(testcase_dir))
                current_files[relative_path] = self._compute_file_hash(file_path)

        # Find added and modified
        for path, current_hash in current_files.items():
            saved_hash = saved_hashes.get(path)
            if saved_hash is None:
                changes["added"].append(path)
            elif current_hash != saved_hash:
                changes["modified"].append(path)

        # Find deleted
        for path in saved_hashes:
            if path not in current_files:
                changes["deleted"].append(path)

        return changes
