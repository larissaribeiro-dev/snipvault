# Referência da API

Base: `http://localhost:8000`. A versão interativa fica em `/docs`.

Rotas protegidas exigem o header `Authorization: Bearer <token>`.

## Autenticação

### `POST /auth/register`

```json
{ "email": "larissa@example.com", "password": "senha-segura-123" }
```

`201`: `{ "id": 1, "email": "larissa@example.com", "created_at": "..." }`

O e-mail é normalizado para minúsculas. A senha deve ter de 8 a 128 caracteres.

### `POST /auth/login`

Mesmo corpo do cadastro. `200`: `{ "access_token": "...", "token_type": "bearer" }`

### `GET /auth/me`

`200`: dados da conta dona do token.

## Snippets

### Campos

| Campo         | Tipo             | Regras                                                    |
|---------------|------------------|-----------------------------------------------------------|
| `title`       | string           | 1 a 120 caracteres                                        |
| `description` | string ou `null` | até 500 caracteres                                        |
| `language`    | string           | 1 a 30 caracteres; guardada em minúsculas                 |
| `code`        | string           | 1 a 50.000 caracteres                                     |
| `is_public`   | boolean          | padrão `false`                                            |
| `tags`        | lista de string  | até 10; `a-z`, `0-9`, `+ # . _ -`; até 30 caracteres cada |

### `POST /snippets`

Cria. `201` com o snippet completo.

### `GET /snippets`

Lista os snippets de quem está autenticado, do mais novo para o mais antigo.

| Parâmetro  | Descrição                                                         |
|------------|-------------------------------------------------------------------|
| `q`        | busca (sem diferenciar maiúsculas) em título, descrição e código |
| `language` | linguagem exata                                                   |
| `tag`      | tag exata                                                         |
| `limit`    | 1 a 100 (padrão 20)                                               |
| `offset`   | a partir de 0                                                     |

Resposta: `{ "items": [...], "total": 42, "limit": 20, "offset": 0 }`. O `total` considera os
filtros, não só a página atual.

### `GET /snippets/{id}`

Autenticação opcional. Devolve o snippet se ele for público ou pertencer a quem pede.

### `PATCH /snippets/{id}`

Envie só o que quer mudar. `description` aceita `null` para limpar; os demais campos não aceitam `null`.
Enviar `tags` substitui a lista inteira.

### `DELETE /snippets/{id}`

`204` sem corpo.

## Snippets públicos

### `GET /public/snippets`

Sem autenticação. Aceita os mesmos parâmetros de `GET /snippets`.

## Códigos de resposta

| Código | Quando                                                                       |
|--------|------------------------------------------------------------------------------|
| `401`  | token ausente, inválido ou expirado; credenciais de login erradas            |
| `403`  | tentar alterar ou apagar um snippet público de outra pessoa                  |
| `404`  | snippet inexistente, ou privado de outra pessoa                              |
| `409`  | e-mail já cadastrado                                                         |
| `422`  | corpo ou parâmetros inválidos (o campo e o motivo vêm em `detail`)           |
