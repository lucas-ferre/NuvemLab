from __future__ import annotations

import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, EmailStr, Field

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DATA_DIR = Path(os.getenv("DATA_DIR", PROJECT_DIR / "data"))
DATABASE_PATH = DATA_DIR / "contatos.db"


class Servico(BaseModel):
    id: str
    nome: str
    descricao: str


class ContatoEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: Annotated[str, Field(min_length=2, max_length=80)]
    email: EmailStr
    mensagem: Annotated[str, Field(min_length=10, max_length=1_000)]


class ContatoResposta(BaseModel):
    id: int
    status: str
    recebido_em: datetime


SERVICOS = [
    Servico(
        id="arquitetura",
        nome="Arquitetura em nuvem",
        descricao="Planejamento de aplicações seguras, observáveis e preparadas para crescer.",
    ),
    Servico(
        id="containers",
        nome="Containers",
        descricao="Empacotamento consistente com Docker para desenvolvimento e produção.",
    ),
    Servico(
        id="automacao",
        nome="Entrega automatizada",
        descricao="Pipelines de CI/CD com validações e implantação controlada.",
    ),
]


def preparar_banco() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE_PATH) as conexao:
        conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS contatos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL,
                mensagem TEXT NOT NULL,
                criado_em TEXT NOT NULL
            )
            """
        )


@asynccontextmanager
async def lifespan(_: FastAPI):
    preparar_banco()
    yield


app = FastAPI(
    title="NuvemLab API",
    summary="API demonstrativa para o Projeto Integrador com Docker e Nuvem.",
    description=(
        "Serviço híbrido: página institucional e endpoints REST para catálogo "
        "de serviços e recebimento de contatos."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.middleware("http")
async def adicionar_cabecalhos_de_seguranca(request: Request, call_next):
    resposta = await call_next(request)
    if request.url.path in {"/docs", "/docs/oauth2-redirect", "/redoc"}:
        resposta.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: https://fastapi.tiangolo.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "connect-src 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'"
        )
    else:
        resposta.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "style-src 'self'; "
            "script-src 'self'; "
            "connect-src 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'"
        )
    resposta.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    resposta.headers["X-Frame-Options"] = "DENY"
    return resposta


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def pagina_inicial(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"ano": datetime.now(UTC).year, "servicos": SERVICOS},
    )


@app.get("/api/servicos", response_model=list[Servico], tags=["serviços"])
def listar_servicos() -> list[Servico]:
    """Retorna o catálogo público de serviços."""
    return SERVICOS


@app.post(
    "/api/contato",
    response_model=ContatoResposta,
    status_code=status.HTTP_201_CREATED,
    tags=["contato"],
)
def criar_contato(contato: ContatoEntrada) -> ContatoResposta:
    """Valida e armazena uma solicitação de contato no volume persistente."""
    recebido_em = datetime.now(UTC)
    with sqlite3.connect(DATABASE_PATH) as conexao:
        cursor = conexao.execute(
            """
            INSERT INTO contatos (nome, email, mensagem, criado_em)
            VALUES (?, ?, ?, ?)
            """,
            (
                contato.nome.strip(),
                str(contato.email).lower(),
                contato.mensagem.strip(),
                recebido_em.isoformat(),
            ),
        )
        contato_id = int(cursor.lastrowid)

    return ContatoResposta(
        id=contato_id,
        status="recebido",
        recebido_em=recebido_em,
    )


@app.get("/health", tags=["operação"])
def verificar_saude() -> dict[str, str]:
    """Confirma que a aplicação e o banco SQLite estão acessíveis."""
    with sqlite3.connect(DATABASE_PATH) as conexao:
        conexao.execute("SELECT 1").fetchone()
    return {"status": "ok"}
