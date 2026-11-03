# snipvault

[![CI](https://github.com/larissaribeiro-dev/snipvault/actions/workflows/ci.yml/badge.svg)](https://github.com/larissaribeiro-dev/snipvault/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

API REST para guardar, buscar e compartilhar trechos de código. Cada pessoa tem sua conta, organiza os snippets com tags, escolhe o que fica privado e o que vira público, e encontra tudo depois com busca por texto, linguagem e tag.

Todas as rotas, regras de negócio e acesso a dados ficam em camadas separadas, a autenticação usa JWT com `scrypt` da biblioteca padrão (sem dependências nativas) e a aplicação é criada por uma *app factory*, perimitindo deixar os testes rápidos e isolados, sem mocks.

```
$ curl -s -X POST localhost:8000/snippets \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -d '{"title": "Retry com backoff", "language": "python",
         "code": "time.sleep(2 ** attempt)", "tags": ["http", "retry"], "is_public": true}'
{
  "id": 1,
  "title": "Retry com backoff",
  "description": null,
  "language": "python",
  "code": "time.sleep(2 ** attempt)",
  "is_public": true,
  "tags": ["http", "retry"],
  "owner_id": 1,
  "created_at": "2026-11-02T14:03:11.402913Z",
  "updated_at": "2026-11-02T14:03:11.402917Z"
}

$ curl -s "localhost:8000/public/snippets?tag=retry"
{"items": [ ... ], "total": 1, "limit": 20, "offset": 0}
```

## Recursos

- Cadastro e login com JWT (`/auth/register`, `/auth/login`, `/auth/me`)
- CRUD completo de snippets, com `PATCH` parcial
- Tags normalizadas (minúsculas, sem duplicadas, até 10 por snippet)
- Snippets privados ou públicos; a listagem pública não exige login
- Busca por texto (título, descrição e código), linguagem e tag, com paginação
- Documentação interativa gerada automaticamente em `/docs` (Swagger) e `/redoc`
- Privacidade por padrão: snippet privado de outra pessoa responde `404`, sem revelar que existe
- Senhas com `scrypt` e sal aleatório; login com tempo de resposta uniforme para e-mails inexistentes
- Troca de banco só pela URL de conexão (SQLite por padrão, PostgreSQL e outros via SQLAlchemy)
- Dockerfile com usuário sem privilégios, `docker-compose` e `healthcheck`

## Instalação

Requer Python 3.10 ou superior.

```bash
git clone https://github.com/larissaribeiro-dev/snipvault.git
cd snipvault
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
cp .env.example .env             # ajuste a SNIPVAULT_SECRET_KEY
```

## Uso

### Subindo a API

```bash
snipvault                        # http://127.0.0.1:8000
snipvault --port 9000 --reload   # modo desenvolvimento
```

Abra [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) para testar as rotas pelo navegador.

### Com Docker

```bash
echo "SNIPVAULT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')" > .env
docker compose up --build
```

O banco fica no volume `snipvault-data`, então os dados sobrevivem a reinícios.

### Fluxo completo com curl

```bash
# 1. criar conta
curl -s -X POST localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "larissa@example.com", "password": "senha-segura-123"}'

# 2. pegar o token
TOKEN=$(curl -s -X POST localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "larissa@example.com", "password": "senha-segura-123"}' \
  | python -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')

# 3. buscar nos seus snippets
curl -s "localhost:8000/snippets?q=backoff&language=python&limit=10" \
  -H "Authorization: Bearer $TOKEN"

# 4. publicar um snippet que antes era privado
curl -s -X PATCH localhost:8000/snippets/1 \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"is_public": true}'
```

### Erros

Toda resposta de erro tem o mesmo formato:

```
$ curl -s localhost:8000/snippets/999 -H "Authorization: Bearer $TOKEN"
{"detail": "Snippet não encontrado"}
```

Erros de validação (`422`) listam o campo e o motivo. Veja todos os códigos em [docs/API.md](docs/API.md).

## Endpoints

| Método   | Rota                    | Auth     | Descrição                                   |
|----------|-------------------------|----------|---------------------------------------------|
| `GET`    | `/health`               | não      | Status e versão                             |
| `POST`   | `/auth/register`        | não      | Cria uma conta                              |
| `POST`   | `/auth/login`           | não      | Devolve um token de acesso                  |
| `GET`    | `/auth/me`              | sim      | Dados da conta autenticada                  |
| `POST`   | `/snippets`             | sim      | Cria um snippet                             |
| `GET`    | `/snippets`             | sim      | Lista os seus snippets (com filtros)        |
| `GET`    | `/snippets/{id}`        | opcional | Lê um snippet seu ou público                |
| `PATCH`  | `/snippets/{id}`        | sim      | Atualiza campos de um snippet seu           |
| `DELETE` | `/snippets/{id}`        | sim      | Remove um snippet seu                       |
| `GET`    | `/public/snippets`      | não      | Lista snippets públicos de todo mundo       |

Parâmetros de listagem: `q`, `language`, `tag`, `limit` (1 a 100, padrão 20) e `offset`.

## Configuração

Variáveis de ambiente, todas com o prefixo `SNIPVAULT_` (ou um arquivo `.env`):

| Variável                         | Padrão                       | Descrição                              |
|----------------------------------|------------------------------|----------------------------------------|
| `SNIPVAULT_DATABASE_URL`         | `sqlite:///./snipvault.db`   | URL de conexão do SQLAlchemy           |
| `SNIPVAULT_SECRET_KEY`           | valor de desenvolvimento     | Chave que assina os tokens. **Troque.**|
| `SNIPVAULT_ACCESS_TOKEN_MINUTES` | `60`                         | Validade do token                      |

Para PostgreSQL, instale um driver (`pip install "psycopg[binary]"`) e use
`SNIPVAULT_DATABASE_URL=postgresql+psycopg://usuario:senha@host/banco`.

## Como funciona

Cada requisição atravessa quatro camadas, e cada uma só conversa com a seguinte:

```
 POST /snippets
     |
     v
 routers/       HTTP  ->  valida a entrada (schemas.py) e resolve o usuário (deps.py)
     |
     v
 services/      regra de negócio: permissões, tags, filtros, paginação
     |
     v
 models.py      SQLAlchemy  ->  tabelas users, snippets, tags, snippet_tags
     |
     v
 banco          SQLite por padrão
```

Um passo a passo mais detalhado, com a decisão por trás de cada camada, está em [docs/ARQUITETURA.md](docs/ARQUITETURA.md).

### Estrutura do projeto

```
snipvault/
├── src/snipvault/
│   ├── main.py          # app factory
│   ├── config.py        # configuração via variáveis de ambiente
│   ├── database.py      # engine e base do SQLAlchemy
│   ├── models.py        # tabelas
│   ├── schemas.py       # entrada e saída da API (Pydantic)
│   ├── security.py      # hash de senha e JWT
│   ├── deps.py          # dependências: sessão, usuário atual, paginação
│   ├── errors.py        # erros de domínio
│   ├── cli.py           # comando `snipvault`
│   ├── routers/         # auth, snippets, health
│   └── services/        # regra de negócio
├── tests/
├── docs/
├── .github/workflows/ci.yml
├── Dockerfile
└── pyproject.toml
```

## Decisões de projeto

**Por que FastAPI?** Valida a entrada com tipos, gera a documentação OpenAPI sozinho e tem injeção de dependências, o que permite trocar banco e configuração nos testes sem monkeypatch.

**Por que uma *app factory*?** `create_app(settings)` monta uma aplicação nova a cada chamada. Os testes usam um SQLite em memória por teste, então nada vaza de um para o outro e a suíte roda em segundos.

**Por que `scrypt` e não bcrypt?** Faz parte da biblioteca padrão do Python, resiste a ataques com GPU por exigir memória e evita uma dependência com código nativo. O hash guarda os parâmetros, então dá para aumentar o custo no futuro sem invalidar senhas antigas.

**Por que snippet privado alheio devolve `404` e não `403`?** Um `403` confirmaria que o id existe. Já para snippets públicos de outra pessoa, tentar editar devolve `403`, porque aí não há nada a esconder.

**Por que `services/` separado das rotas?** As rotas só traduzem HTTP. A regra de negócio vive em funções comuns, que levantam erros de domínio (`errors.py`) e podem ser reaproveitadas por um CLI ou uma fila no futuro.

**Por que a busca escapa `%` e `_`?** Sem isso, quem buscasse por `50%` ou `snake_case` receberia resultados que não têm relação com o termo, porque esses caracteres são curingas do `LIKE`.

**Por que SQLite por padrão?** Para rodar o projeto sem instalar nada. Como o acesso é todo via SQLAlchemy, mudar para PostgreSQL é questão de trocar a URL.

## Testes

```bash
pip install -e ".[dev]"
make test       # pytest com cobertura (mínimo de 90%)
make lint       # ruff check + ruff format --check
```

Os testes sobem a aplicação inteira em memória e chamam os endpoints de verdade, cobrindo autenticação, permissões, filtros, paginação e casos de borda. A cobertura passa de 95%. O CI roda tudo no GitHub Actions nas versões 3.10 a 3.13 e também valida o build da imagem Docker.

## Roadmap

- [ ] Migrações com Alembic
- [ ] Limite de requisições por usuário (rate limiting)
- [ ] Refresh token e revogação
- [ ] Favoritos e contagem de visualizações
- [ ] Busca de texto completo (FTS5 / `tsvector`)
- [ ] Publicação da imagem no GitHub Container Registry

## Licença

Distribuído sob a licença MIT. Veja o arquivo [LICENSE](LICENSE).
