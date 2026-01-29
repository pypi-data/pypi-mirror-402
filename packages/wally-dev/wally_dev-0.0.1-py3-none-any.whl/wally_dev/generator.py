"""
TestCase Generator for Wally Dev CLI.

Uses OpenAI API to generate test case code (finder.py, validator.py)
and example HTML files for accessibility rules.
"""

import json
from typing import Any, Optional

from .models import Rule


class TestCaseGenerator:
    """
    Generates test case code using OpenAI API.

    Creates finder.py, validator.py and HTML examples
    for accessibility rule validation.
    """

    # Target context descriptions for prompts
    TARGET_CONTEXT = {
        "html": "páginas HTML estáticas",
        "react": "aplicações React com JSX/TSX",
        "angular": "aplicações Angular com templates",
        "vue": "aplicações Vue.js com templates",
        "sonarqube": "código analisado via SonarQube",
    }

    def __init__(
        self,
        api_key: str,
        target: str = "html",
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 8000,
    ):
        """
        Initialize the generator.

        Args:
            api_key: OpenAI API key
            target: Target technology (html, react, angular, vue, sonarqube)
            model: OpenAI model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
        """
        self.api_key = api_key
        self.target = target.lower()
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client: Any = None

    @property
    def client(self) -> Any:
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            try:
                import openai

                self._client = openai.OpenAI(api_key=self.api_key)
            except ImportError as e:
                raise ImportError(
                    "openai package is required for test case generation. "
                    "Install with: pip install openai"
                ) from e
        return self._client

    def _build_prompt(self, rule: Rule) -> str:
        """
        Build the prompt for ChatGPT.

        Args:
            rule: The accessibility rule to generate tests for

        Returns:
            Complete prompt string
        """
        target_desc = self.TARGET_CONTEXT.get(self.target, "páginas web")

        return f"""Você é um especialista em acessibilidade web e automação de testes.

## CONTEXTO
Estou desenvolvendo casos de teste automatizados para validar a conformidade de {target_desc} com regras de acessibilidade.

### Sobre a Regra a ser Testada
- **ID**: {rule.id}
- **Nome**: {rule.name}
- **Descrição**: {rule.description or 'Sem descrição'}
- **Categoria**: {rule.category or 'unknown'}
- **Severidade**: {rule.severity or 'medium'}
- **Automatizável**: {'Sim' if rule.is_automatable else 'Não'}

### Configuração do TestCase
- **Linguagem**: Python
- **Target**: {self.target}

## TAREFA
Crie um caso de teste Python para validar esta regra de acessibilidade em {target_desc}.

### Estrutura Esperada

1. **finder.py** - Módulo que encontra elementos HTML relevantes para esta regra
   - Função `find(html_content: str) -> List[Any]`
   - Usa BeautifulSoup para parsear o HTML
   - Retorna lista de elementos que precisam ser validados
   - Deve ser específico para o tipo de elemento que a regra trata

2. **validator.py** - Módulo que valida se cada elemento está em conformidade
   - Função `validate(element: Any) -> bool`
   - Retorna True se o elemento está em conformidade, False caso contrário
   - Deve implementar a lógica específica desta regra
   - Considere edge cases

3. **compliant.html** - Exemplo de HTML que PASSA na validação (acessível)
   - Deve ser um exemplo realista de {target_desc}
   - Deve demonstrar a implementação correta da regra
   - Estrutura HTML5 válida

4. **non_compliant.html** - Exemplo de HTML que FALHA na validação (inacessível)
   - Deve mostrar violações típicas desta regra
   - Deve ser um exemplo realista de erros comuns
   - Estrutura HTML5 válida

## FORMATO DE RESPOSTA
Responda APENAS com JSON válido no seguinte formato (sem markdown, sem explicações):

{{
  "finder_py": "# código completo do finder.py aqui",
  "validator_py": "# código completo do validator.py aqui",
  "compliant_html": "<!DOCTYPE html>...código HTML compliant...",
  "non_compliant_html": "<!DOCTYPE html>...código HTML non-compliant..."
}}

## REQUISITOS TÉCNICOS

1. **finder.py**:
   - Import: `from bs4 import BeautifulSoup`
   - Docstring explicando o que busca
   - Tipo de retorno: `List[Any]`
   - Considere elementos específicos do target ({self.target})

2. **validator.py**:
   - Docstring explicando a validação
   - Tipo de retorno: `bool`
   - Lógica clara e bem comentada
   - Considere edge cases

3. **HTML Examples**:
   - HTML5 válido com DOCTYPE
   - lang="pt-BR" no html
   - Meta viewport e charset
   - Comentários explicando o que está certo/errado

## IMPORTANTE
- Foque APENAS nesta regra específica
- O código deve ser funcional e testável
- Use nomes de variáveis em inglês
- Comentários podem ser em português
"""

    def _fix_newlines(self, obj: Any) -> Any:
        """
        Convert literal \\n to actual newlines in strings.

        Args:
            obj: Object to process (string, dict, or list)

        Returns:
            Object with fixed newlines
        """
        if isinstance(obj, str):
            return obj.replace("\\n", "\n").replace("\\t", "\t")
        elif isinstance(obj, dict):
            return {k: self._fix_newlines(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._fix_newlines(item) for item in obj]
        return obj

    def generate(self, rule: Rule) -> Optional[dict[str, str]]:
        """
        Generate test case code for a rule.

        Args:
            rule: The accessibility rule to generate tests for

        Returns:
            Dictionary with generated code:
                - finder_py: finder.py code
                - validator_py: validator.py code
                - compliant_html: compliant example HTML
                - non_compliant_html: non-compliant example HTML
            Or None if generation fails.
        """
        prompt = self._build_prompt(rule)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Você é um especialista em acessibilidade web. "
                            "Responda APENAS com JSON válido. "
                            "Use \\n para quebras de linha dentro das strings."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            content = response.choices[0].message.content.strip()

            # Remove possible markdown code markers
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content.rsplit("```", 1)[0]
            if content.startswith("json"):
                content = content[4:].strip()

            result = json.loads(content)

            # Fix escaped newlines
            result = self._fix_newlines(result)

            # Validate required fields
            required_fields = ["finder_py", "validator_py"]
            for field in required_fields:
                if field not in result or not result[field]:
                    return None

            # Build combined code for the testcase
            result["code"] = self._build_combined_code(
                result.get("finder_py", ""),
                result.get("validator_py", ""),
            )

            final_result: dict[str, str] = result
            return final_result

        except json.JSONDecodeError:
            return None
        except Exception:
            return None

    def _build_combined_code(self, finder_code: str, validator_code: str) -> str:
        """
        Build a combined code module from finder and validator.

        Args:
            finder_code: The finder.py code
            validator_code: The validator.py code

        Returns:
            Combined Python module code
        """
        # Extract the core logic from both files
        return f'''"""
Auto-generated test case code.
Combines finder and validator logic.
"""

# ============================================================================
# FINDER
# ============================================================================

{finder_code}

# ============================================================================
# VALIDATOR
# ============================================================================

{validator_code}

# ============================================================================
# RUNNER
# ============================================================================

def run(html_content: str) -> list[dict]:
    """
    Execute the test case on HTML content.

    Args:
        html_content: HTML string to analyze

    Returns:
        List of results with element info and validation status
    """
    results = []
    elements = find(html_content)

    for element in elements:
        is_valid = validate(element)
        results.append({{
            "element": str(element)[:200],
            "valid": is_valid,
        }})

    return results


def check_compliance(html_content: str) -> tuple[bool, list[dict]]:
    """
    Check if HTML content is compliant with this rule.

    Args:
        html_content: HTML string to analyze

    Returns:
        Tuple of (all_passed, results)
    """
    results = run(html_content)
    all_passed = all(r["valid"] for r in results) if results else True
    return all_passed, results
'''


class GeneratorResult:
    """Result of test case generation."""

    def __init__(
        self,
        success: bool,
        finder_py: Optional[str] = None,
        validator_py: Optional[str] = None,
        compliant_html: Optional[str] = None,
        non_compliant_html: Optional[str] = None,
        code: Optional[str] = None,
        error: Optional[str] = None,
    ):
        self.success = success
        self.finder_py = finder_py
        self.validator_py = validator_py
        self.compliant_html = compliant_html
        self.non_compliant_html = non_compliant_html
        self.code = code
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "finder_py": self.finder_py,
            "validator_py": self.validator_py,
            "compliant_html": self.compliant_html,
            "non_compliant_html": self.non_compliant_html,
            "code": self.code,
        }
