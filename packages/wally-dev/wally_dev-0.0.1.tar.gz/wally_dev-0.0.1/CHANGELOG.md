# Changelog

Todas as alterações notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Added
- Comando `norms list` para listar normas disponíveis
- Comando `rules list` para listar regras de uma norma
- Flag `--debug` no comando `run` mostrando elementos e validações detalhadas
- Coluna de número da linha no output de debug
- Suporte a Python 3.13

### Changed
- Melhorias na documentação e README

## [0.1.0] - 2026-01-12

### Added
- Comando `login` para autenticação com username/password
- Comando `logout` para remover credenciais e desbloquear normas
- Comando `checkout` para baixar casos de teste de uma norma
- Comando `push` para enviar alterações ao servidor
- Comando `run` para execução local de casos de teste
- Comando `status` para verificar estado do workspace
- Suporte ao padrão finder/validator para casos de teste
- Download de exemplos (compliant/non-compliant) como arquivos HTML
- Auto-refresh de tokens JWT expirados
- Interface rica com tabelas e painéis (Rich)
- Configuração via variáveis de ambiente
- Suporte a múltiplas normas em checkout simultâneo

### Security
- Armazenamento seguro de tokens em arquivo local
- Senha solicitada de forma interativa (não visível no histórico)

[Unreleased]: https://gitlab.com/AcessibilidadeParaTodos/wally/wally-dev/-/compare/v0.1.0...main
[0.1.0]: https://gitlab.com/AcessibilidadeParaTodos/wally/wally-dev/-/tags/v0.1.0
