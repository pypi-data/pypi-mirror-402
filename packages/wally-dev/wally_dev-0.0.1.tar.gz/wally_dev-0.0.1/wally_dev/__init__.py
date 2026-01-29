"""
Wally Dev CLI - Ferramenta para desenvolvimento local de casos de teste de acessibilidade.

Este módulo fornece uma CLI para desenvolvedores que trabalham com casos de teste
de acessibilidade da plataforma Wally.

Comandos disponíveis:
    - login: Autenticação com username/password
    - logout: Remove credenciais locais
    - checkout: Bloqueia norma e baixa casos de teste para desenvolvimento local
    - push: Faz upload de alterações e desbloqueia a norma
    - run: Executa caso de teste localmente em modo debug
    - norms list: Lista normas disponíveis
    - rules list: Lista regras de uma norma
    - status: Mostra status do workspace

Example:
    >>> from wally_dev import __version__
    >>> print(__version__)
    0.1.1
"""

__version__ = "0.1.1"
__author__ = "Equallyze"
__email__ = "contato@equallyze.com"

from .config import Settings
from .exceptions import WallyDevError

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "Settings",
    "WallyDevError",
]
