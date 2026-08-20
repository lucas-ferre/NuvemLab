from __future__ import annotations

import html
import os
import sqlite3
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DATA_DIR = Path(os.getenv("DATA_DIR", PROJECT_DIR / "data"))
DATABASE_PATH = DATA_DIR / "contatos.db"
APP_START_TIME = time.time()

_ip_request_history: dict[str, list[float]] = defaultdict(list)
_ip_contact_history: dict[str, list[float]] = defaultdict(list)


class Servico(BaseModel):
    id: str
    nome: str
    descricao: str
    icone: str
    detalhes: list[str]


class ContatoEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: Annotated[str, Field(min_length=2, max_length=80)]
    email: EmailStr
    mensagem: Annotated[str, Field(min_length=10, max_length=1_000)]
    topico: Annotated[str | None, Field(max_length=50)] = "Geral"
    hp_website: Annotated[str | None, Field(max_length=100)] = None

    @field_validator("nome", "mensagem", "topico")
    @classmethod
    def sanitizar_texto(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        limpo = valor.strip()
        return html.escape(limpo)


class ContatoResposta(BaseModel):
    id: int
    status: str
    recebido_em: datetime
    protocolo: str


class MetricasResposta(BaseModel):
    status: str
    versao: str
    uptime_segundos: float
    total_contatos: int
    banco_modo: str
    seguranca_ativa: list[str]
    servicos_ativos: int
    timestamp: datetime


class SimulacaoEntrada(BaseModel):
    requisicoes_mes: int = Field(ge=1_000, le=100_000_000, default=50_000)
    memoria_mb: int = Field(ge=256, le=8192, default=512)
    instancias: int = Field(ge=1, le=20, default=1)


class SimulacaoResposta(BaseModel):
    custo_azure_app_service: float
    custo_on_premise_estimado: float
    economia_percentual: float
    sla_disponibilidade: str
    latencia_media_ms: float
    requisicoes_suportadas_segundo: int


SERVICOS = [
    Servico(
        id="arquitetura",
        nome="Arquitetura em nuvem",
        descricao="Planejamento de aplicações seguras, observáveis e preparadas para escalabilidade horizontal.",
        icone="cloud",
        detalhes=[
            "Design orientado a microserviços e containers",
            "Zone-redundancy e alta disponibilidade PaaS",
            "Isolamento de redes virtuais e zero trust",
        ],
    ),
    Servico(
        id="containers",
        nome="Containers & Docker",
        descricao="Empacotamento reproduzível com builds em múltiplos estágios, imagens mínimas e sem privilégios de root.",
        icone="box",
        detalhes=[
            "Multi-stage builds (Python 3.13-slim)",
            "Execução com usuário não-root (UID 10001)",
            "Filesystem read-only e tmpfs dedicado",
        ],
    ),
    Servico(
        id="automacao",
        nome="Entrega automatizada (CI/CD)",
        descricao="Pipelines com validações estáticas, testes automatizados e deploy contínuo em slots de homologação.",
        icone="cpu",
        detalhes=[
            "GitHub Actions com autenticação federada OIDC",
            "Publicação direta no Azure Container Registry",
            "Zero-downtime deployment com swap de slots",
        ],
    ),
    Servico(
        id="seguranca",
        nome="Segurança & Conformidade",
        descricao="Proteção em camadas com cabeçalhos OWASP recomendados, rate limiting, sanitização e auditoria.",
        icone="shield",
        detalhes=[
            "Content-Security-Policy e HSTS rigorosos",
            "Rate limiting e proteção contra DoS",
            "Sanitização e honeypots anti-spam",
        ],
    ),
]


def obter_conexao_banco() -> sqlite3.Connection:
    conexao = sqlite3.connect(DATABASE_PATH, timeout=5.0)
    conexao.execute("PRAGMA journal_mode = WAL;")
    conexao.execute("PRAGMA synchronous = NORMAL;")
    conexao.execute("PRAGMA busy_timeout = 5000;")
    conexao.execute("PRAGMA foreign_keys = ON;")
    return conexao


def preparar_banco() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with obter_conexao_banco() as conexao:
        conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS contatos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL,
                mensagem TEXT NOT NULL,
                topico TEXT DEFAULT 'Geral',
                criado_em TEXT NOT NULL
            )
            """
        )


def verificar_rate_limit(ip: str, historico: dict[str, list[float]], max_requisicoes: int, janela_segundos: int) -> bool:
    agora = time.time()
    tempos = historico[ip]
    historico[ip] = [t for t in tempos if agora - t < janela_segundos]
    if len(historico[ip]) >= max_requisicoes:
        return False
    historico[ip].append(agora)
    return True


@asynccontextmanager
async def lifespan(_: FastAPI):
    preparar_banco()
    yield


app = FastAPI(
    title="NuvemLab API",
    summary="API moderna e segura para o Projeto Integrador com Docker e Nuvem.",
    description=(
        "Serviço híbrido: página institucional reativa e endpoints REST para catálogo "
        "de serviços, telemetria em tempo real, simulações de custos e recebimento seguro de contatos."
    ),
    version="1.2.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.middleware("http")
async def middleware_seguranca_e_rate_limit(request: Request, call_next):
    ip_cliente = request.client.host if request.client else "127.0.0.1"

    if request.url.path.startswith("/api/") and request.url.path != "/api/status/metrics":
        if not verificar_rate_limit(ip_cliente, _ip_request_history, max_requisicoes=120, janela_segundos=60):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Limite de requisições excedido. Por favor, aguarde alguns instantes."},
                headers={"Retry-After": "60"},
            )

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
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; "
            "connect-src 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "object-src 'none'"
        )

    resposta.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    resposta.headers["X-Frame-Options"] = "DENY"
    resposta.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resposta.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
    resposta.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    resposta.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    resposta.headers["X-Permitted-Cross-Domain-Policies"] = "none"

    if request.url.path.startswith("/api/") or request.url.path == "/health":
        resposta.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    elif request.url.path.startswith("/static/"):
        resposta.headers["Cache-Control"] = "public, max-age=86400"

    return resposta


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def pagina_inicial(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "ano": datetime.now(UTC).year,
            "servicos": SERVICOS,
            "versao": "1.2.0",
        },
    )


@app.get("/api/servicos", response_model=list[Servico], tags=["serviços"])
def listar_servicos() -> list[Servico]:
    return SERVICOS


@app.post(
    "/api/contato",
    response_model=ContatoResposta,
    status_code=status.HTTP_201_CREATED,
    tags=["contato"],
)
def criar_contato(contato: ContatoEntrada, request: Request) -> ContatoResposta:
    ip_cliente = request.client.host if request.client else "127.0.0.1"

    if not verificar_rate_limit(ip_cliente, _ip_contact_history, max_requisicoes=5, janela_segundos=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Você atingiu o limite de envios de mensagens. Aguarde 1 minuto.",
            headers={"Retry-After": "60"},
        )

    if contato.hp_website:
        return ContatoResposta(
            id=99999,
            status="recebido",
            recebido_em=datetime.now(UTC),
            protocolo="NLB-BOT-DISCARD",
        )

    recebido_em = datetime.now(UTC)
    with obter_conexao_banco() as conexao:
        cursor = conexao.execute(
            """
            INSERT INTO contatos (nome, email, mensagem, topico, criado_em)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                contato.nome,
                str(contato.email).lower(),
                contato.mensagem,
                contato.topico or "Geral",
                recebido_em.isoformat(),
            ),
        )
        contato_id = int(cursor.lastrowid)

    protocolo = f"NLB-{recebido_em.strftime('%Y%m%d')}-{contato_id:04d}"

    return ContatoResposta(
        id=contato_id,
        status="recebido",
        recebido_em=recebido_em,
        protocolo=protocolo,
    )


@app.get("/api/status/metrics", response_model=MetricasResposta, tags=["telemetria"])
def obter_metricas() -> MetricasResposta:
    uptime = time.time() - APP_START_TIME
    with obter_conexao_banco() as conexao:
        total = conexao.execute("SELECT COUNT(*) FROM contatos").fetchone()[0]

    return MetricasResposta(
        status="operacional",
        versao="1.2.0",
        uptime_segundos=round(uptime, 2),
        total_contatos=total,
        banco_modo="SQLite WAL (Write-Ahead Logging)",
        seguranca_ativa=[
            "Rate Limiting por IP",
            "Honeypot Anti-Spam",
            "Sanitização XSS",
            "Cabeçalhos OWASP (HSTS, CSP, COOP)",
            "Container Não-Root (UID 10001)",
        ],
        servicos_ativos=len(SERVICOS),
        timestamp=datetime.now(UTC),
    )


@app.post("/api/simulador/custos", response_model=SimulacaoResposta, tags=["simulador"])
def simular_custos(entrada: SimulacaoEntrada) -> SimulacaoResposta:
    reqs = entrada.requisicoes_mes
    inst = entrada.instancias

    custo_azure_base = 13.0 * inst + (reqs / 1_000_000) * 0.40
    custo_on_premise = 45.0 * inst + 25.0

    economia = max(0.0, ((custo_on_premise - custo_azure_base) / custo_on_premise) * 100)
    reqs_sec = max(50, int((entrada.memoria_mb / 256) * 120 * inst))
    latencia = max(8.5, 45.0 - (inst * 4.0))

    return SimulacaoResposta(
        custo_azure_app_service=round(custo_azure_base, 2),
        custo_on_premise_estimado=round(custo_on_premise, 2),
        economia_percentual=round(economia, 1),
        sla_disponibilidade="99.95%",
        latencia_media_ms=round(latencia, 1),
        requisicoes_suportadas_segundo=reqs_sec,
    )


@app.get("/health", tags=["operação"])
def verificar_saude() -> dict[str, str]:
    with obter_conexao_banco() as conexao:
        conexao.execute("SELECT 1").fetchone()
    return {"status": "ok"}


