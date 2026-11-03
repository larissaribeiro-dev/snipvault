# Arquitetura

Este documento explica como o código está dividido e por quê. Para o uso da API, veja
[API.md](API.md).

## Visão geral

```
routers/  ->  services/  ->  models.py  ->  banco
   ^              |
 schemas.py    errors.py
   ^
 deps.py
```

A dependência só aponta para a direita: `services` não conhece FastAPI e `models` não conhece
`services`.

## Camadas

### `routers/`

Cada função de rota recebe os dados já validados, chama um serviço e devolve o resultado. Não há
`if` de regra de negócio aqui. A conversão do modelo ORM para JSON acontece pelo `response_model`.

### `schemas.py`

Modelos Pydantic de entrada e saída. É aqui que mora a normalização (e-mail em minúsculas,
linguagem em minúsculas, tags limpas e sem duplicatas), de modo que os serviços sempre recebem
dados prontos.

`SnippetUpdate` usa `model_dump(exclude_unset=True)` para distinguir "não enviei o campo" de
"enviei `null`". Para `description`, `null` limpa o valor; para os campos obrigatórios, é rejeitado.

### `deps.py`

Dependências do FastAPI: sessão do banco (uma por requisição, sempre fechada no `finally`),
configuração, usuário autenticado e parâmetros de listagem. Há duas versões do usuário:

- `CurrentUser` exige token válido;
- `OptionalUser` aceita requisição anônima, mas rejeita um token inválido (um token vencido
  não deve ser tratado em silêncio como visitante).

### `services/`

Funções simples que recebem uma `Session` e levantam erros de domínio. Aqui ficam:

- visibilidade (`get_visible_snippet`) e posse (`get_owned_snippet`);
- reaproveitamento de tags já existentes;
- filtros, ordenação e contagem total.

### `errors.py`

Erros de domínio carregam o status HTTP e a mensagem. Um único *exception handler* em `main.py`
os converte em resposta, então as rotas não precisam de `try/except`.

### `models.py`

Quatro tabelas: `users`, `snippets`, `tags` e a associativa `snippet_tags`. As datas usam um tipo
próprio (`UTCDateTime`) porque o SQLite não guarda fuso horário: sem ele, a API devolveria datas
com `Z` ao criar e sem `Z` ao listar.

## Ciclo de vida

`create_app()` recebe um `Settings`, cria o engine e guarda `settings` e a *session factory* em
`app.state`. As tabelas são criadas no *lifespan* da aplicação. Como nada é global, os testes criam
uma aplicação nova (com SQLite em memória) para cada caso.

## Segurança

- Senhas: `scrypt` (N=2^14, r=8, p=1) com sal de 16 bytes; os parâmetros ficam no próprio hash.
- Tokens: JWT HS256 com `sub` e `exp` obrigatórios.
- Login: quando o e-mail não existe, o serviço ainda calcula um hash descartável, para que o tempo
  de resposta não revele quais e-mails têm conta.
- Busca: curingas do `LIKE` são escapados.

## Limites conhecidos

- Não há migrações: as tabelas são criadas na primeira execução (`create_all`). Alembic está no roadmap.
- Não há revogação de token; a validade curta é a mitigação.
- O SQLite atende bem uso pessoal, mas para vários processos use PostgreSQL.
