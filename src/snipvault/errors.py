class DomainError(Exception):
    """Erro de regra de negócio. A camada HTTP converte em resposta com o status certo."""

    status_code = 400
    detail = "Requisição inválida"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.detail
        super().__init__(self.detail)


class EmailAlreadyRegistered(DomainError):
    status_code = 409
    detail = "Já existe uma conta com esse e-mail"


class InvalidCredentials(DomainError):
    status_code = 401
    detail = "E-mail ou senha incorretos"


class SnippetNotFound(DomainError):
    status_code = 404
    detail = "Snippet não encontrado"


class PermissionDenied(DomainError):
    status_code = 403
    detail = "Você não tem permissão para alterar este snippet"
