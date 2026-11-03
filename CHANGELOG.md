# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e versionamento
[SemVer](https://semver.org/lang/pt-BR/).

## [0.1.0] - 2026-11-02

### Adicionado
- Cadastro e login com JWT; senhas guardadas com scrypt.
- CRUD de snippets com tags, visibilidade pública/privada e `PATCH` parcial.
- Busca por texto, linguagem e tag, com paginação.
- Listagem pública de snippets em `/public/snippets`.
- Endpoint `/health`, comando `snipvault`, Dockerfile e docker-compose.
- Testes automatizados, lint com Ruff e CI no GitHub Actions (Python 3.10 a 3.13).
