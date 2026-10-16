from __future__ import annotations

import html
import os
import platform
import sqlite3
import time
from collections import defaultdict, deque
from collections.abc import Iterator
from contextlib import asynccontextmanager, contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.gzip import GZipMiddleware
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
_recent_latencies_ms: deque[float] = deque(maxlen=30)
_total_requests_processed: int = 0


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


class ContatoRecenteItem(BaseModel):
    id: int
    protocolo: str
    nome_mascarado: str
    email_mascarado: str
    topico: str
    previa_mensagem: str
    criado_em: str


class MetricasResposta(BaseModel):
    status: str
    versao: str
    uptime_segundos: float
    total_contatos: int
    banco_modo: str
    seguranca_ativa: list[str]
    servicos_ativos: int
    total_requisicoes: int = 0
    latencia_media_ms: float = 0.0
    historico_latencia_ms: list[float] = Field(default_factory=list)
    banco_tamanho_kb: float = 0.0
    python_versao: str = ""
    timestamp: datetime


class SimulacaoEntrada(BaseModel):
    requisicoes_mes: int = Field(ge=1_000, le=100_000_000, default=50_000)
    memoria_mb: int = Field(ge=256, le=8192, default=512)
    instancias: int = Field(ge=1, le=20, default=1)
    perfil: Literal["starter", "standard", "premium"] = "standard"


class SimulacaoResposta(BaseModel):
    custo_azure_app_service: float
    custo_azure_container_apps: float
    custo_on_premise_estimado: float
    economia_percentual: float
    economia_anual_usd: float
    sla_disponibilidade: str
    latencia_media_ms: float
    requisicoes_suportadas_segundo: int
    tier_recomendado: str
    vcpu_alocada: float


SERVICOS = [
    Servico(
        id="arquitetura",
        nome="Arquitetura em nuvem",
        descricao=(
            "Planejamento de aplicações seguras, observáveis e preparadas "
            "para escalabilidade horizontal."
        ),
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
        descricao=(
            "Empacotamento reproduzível com builds em múltiplos estágios, "
            "imagens mínimas e sem privilégios de root."
        ),
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
        descricao=(
            "Pipelines com validações estáticas, testes automatizados e "
            "deploy contínuo em slots de homologação."
        ),
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
        descricao=(
            "Proteção em camadas com cabeçalhos OWASP recomendados, "
            "rate limiting, sanitização e auditoria."
        ),
        icone="shield",
        detalhes=[
            "Content-Security-Policy e HSTS rigorosos",
            "Rate limiting e proteção contra DoS",
            "Sanitização e honeypots anti-spam",
        ],
    ),
]


@contextmanager
def obter_conexao_banco() -> Iterator[sqlite3.Connection]:
    conexao = sqlite3.connect(DATABASE_PATH, timeout=5.0)
    try:
        conexao.execute("PRAGMA journal_mode = WAL;")
        conexao.execute("PRAGMA synchronous = NORMAL;")
        conexao.execute("PRAGMA busy_timeout = 5000;")
        conexao.execute("PRAGMA foreign_keys = ON;")
        with conexao:
            yield conexao
    finally:
        conexao.close()


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
        conexao.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_contatos_criado_em
            ON contatos (id DESC)
            """
        )


def _limpar_historico_expirado(
    historico: dict[str, list[float]], agora: float, janela_segundos: int
) -> None:
    if len(historico) > 500:
        ips_expirados = [
            ip for ip, tempos in historico.items()
            if not tempos or (agora - tempos[-1]) >= janela_segundos
        ]
        for ip in ips_expirados:
            historico.pop(ip, None)


def avaliar_rate_limit(
    ip: str,
    historico: dict[str, list[float]],
    max_requisicoes: int,
    janela_segundos: int,
) -> tuple[bool, int, int]:
    agora = time.time()
    _limpar_historico_expirado(historico, agora, janela_segundos)
    tempos = [t for t in historico[ip] if agora - t < janela_segundos]
    historico[ip] = tempos

    if len(tempos) >= max_requisicoes:
        mais_antigo = tempos[0]
        reset_seg = max(1, int(janela_segundos - (agora - mais_antigo)))
        return False, 0, reset_seg

    historico[ip].append(agora)
    restante = max(0, max_requisicoes - len(historico[ip]))
    reset_seg = janela_segundos
    return True, restante, reset_seg


def verificar_rate_limit(
    ip: str,
    historico: dict[str, list[float]],
    max_requisicoes: int,
    janela_segundos: int,
) -> bool:
    permitido, _, _ = avaliar_rate_limit(ip, historico, max_requisicoes, janela_segundos)
    return permitido


def mascarar_nome(nome: str) -> str:
    partes = html.unescape(nome).strip().split()
    if not partes:
        return "Anônimo"
    if len(partes) == 1:
        return partes[0]
    return f"{partes[0]} {partes[-1][0].upper()}."


def mascarar_email(email: str) -> str:
    if "@" not in email:
        return "***"
    usuario, dominio = email.split("@", 1)
    prefixo = usuario[0] + "***" if len(usuario) <= 2 else usuario[:2] + "***"
    return f"{prefixo}@{dominio}"


def formatar_protocolo(contato_id: int, criado_em_iso: str) -> str:
    try:
        dt = datetime.fromisoformat(criado_em_iso)
        data_str = dt.strftime("%Y%m%d")
    except ValueError:
        data_str = datetime.now(UTC).strftime("%Y%m%d")
    return f"NLB-{data_str}-{contato_id:04d}"


@asynccontextmanager
async def lifespan(_: FastAPI):
    preparar_banco()
    yield


app = FastAPI(
    title="NuvemLab API",
    summary="API moderna e segura para o Projeto Integrador com Docker e Nuvem.",
    description=(
        "Serviço híbrido: página institucional reativa e endpoints REST para catálogo "
        "de serviços, telemetria em tempo real, simulações de custos e "
        "recebimento seguro de contatos."
    ),
    version="1.2.0",
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=500)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.middleware("http")
async def middleware_seguranca_e_rate_limit(request: Request, call_next):
    global _total_requests_processed
    inicio = time.perf_counter()
    ip_cliente = request.client.host if request.client else "127.0.0.1"

    rate_info: tuple[int, int, int] | None = None
    if request.url.path.startswith("/api/") and request.url.path != "/api/status/metrics":
        permitido, restante, reset_seg = avaliar_rate_limit(
            ip_cliente, _ip_request_history, max_requisicoes=120, janela_segundos=60
        )
        rate_info = (120, restante, reset_seg)
        if not permitido:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": (
                        "Limite de requisições excedido. "
                        "Por favor, aguarde alguns instantes."
                    )
                },
                headers={
                    "Retry-After": str(reset_seg),
                    "X-RateLimit-Limit": "120",
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_seg),
                },
            )

    resposta = await call_next(request)

    duracao_ms = round((time.perf_counter() - inicio) * 1000, 2)
    _total_requests_processed += 1
    _recent_latencies_ms.append(duracao_ms)
    resposta.headers["X-Process-Time-Ms"] = str(duracao_ms)

    if rate_info is not None:
        limite, restante, reset_seg = rate_info
        resposta.headers.setdefault("X-RateLimit-Limit", str(limite))
        resposta.headers.setdefault("X-RateLimit-Remaining", str(restante))
        resposta.headers.setdefault("X-RateLimit-Reset", str(reset_seg))

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
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' data: https://fonts.gstatic.com; "
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


@app.get("/api/contatos/recentes", response_model=list[ContatoRecenteItem], tags=["contato"])
def listar_contatos_recentes(
    limite: Annotated[
        int, Query(ge=1, le=20, description="Quantidade máxima de registros recentes")
    ] = 5,
) -> list[ContatoRecenteItem]:
    with obter_conexao_banco() as conexao:
        linhas = conexao.execute(
            """
            SELECT id, nome, email, mensagem, topico, criado_em
            FROM contatos
            ORDER BY id DESC
            LIMIT ?
            """,
            (limite,),
        ).fetchall()

    itens: list[ContatoRecenteItem] = []
    for cid, nome, email, mensagem, topico, criado_em in linhas:
        msg_limpa = html.unescape(mensagem)
        previa = msg_limpa if len(msg_limpa) <= 72 else f"{msg_limpa[:69]}..."
        itens.append(
            ContatoRecenteItem(
                id=int(cid),
                protocolo=formatar_protocolo(int(cid), str(criado_em)),
                nome_mascarado=html.escape(mascarar_nome(str(nome))),
                email_mascarado=mascarar_email(str(email)),
                topico=str(topico or "Geral"),
                previa_mensagem=html.escape(previa),
                criado_em=str(criado_em),
            )
        )
    return itens


@app.post(
    "/api/contato",
    response_model=ContatoResposta,
    status_code=status.HTTP_201_CREATED,
    tags=["contato"],
)
def criar_contato(contato: ContatoEntrada, request: Request) -> ContatoResposta:
    ip_cliente = request.client.host if request.client else "127.0.0.1"

    if not verificar_rate_limit(
        ip_cliente, _ip_contact_history, max_requisicoes=5, janela_segundos=60
    ):
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
        contato_id = int(cursor.lastrowid or 1)

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

    tamanho_kb = 0.0
    if DATABASE_PATH.exists():
        tamanho_kb = round(DATABASE_PATH.stat().st_size / 1024, 2)

    latencias = list(_recent_latencies_ms)
    media_latencia = round(sum(latencias) / len(latencias), 2) if latencias else 2.4

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
        total_requisicoes=_total_requests_processed,
        latencia_media_ms=media_latencia,
        historico_latencia_ms=latencias[-15:],
        banco_tamanho_kb=tamanho_kb,
        python_versao=platform.python_version(),
        timestamp=datetime.now(UTC),
    )


@app.post("/api/simulador/custos", response_model=SimulacaoResposta, tags=["simulador"])
def simular_custos(entrada: SimulacaoEntrada) -> SimulacaoResposta:
    reqs = entrada.requisicoes_mes
    mem = entrada.memoria_mb
    inst = entrada.instancias
    perfil = entrada.perfil

    multiplicador_perfil = {"starter": 0.75, "standard": 1.0, "premium": 1.65}.get(perfil, 1.0)
    fator_memoria = max(0.0, (mem - 512) / 512) * 3.5

    custo_azure_base = (
        (13.0 * multiplicador_perfil + fator_memoria) * inst
        + (reqs / 1_000_000) * 0.40
    )
    custo_container_apps = max(
        6.5,
        (8.5 * inst) + (reqs / 1_000_000) * 0.85 + (fator_memoria * 0.6 * inst),
    )
    custo_on_premise = (45.0 * inst) + 25.0 + (fator_memoria * 2.2 * inst)

    economia = max(0.0, ((custo_on_premise - custo_azure_base) / custo_on_premise) * 100)
    economia_anual = max(0.0, (custo_on_premise - custo_azure_base) * 12)
    reqs_sec = max(50, int((mem / 256) * 120 * inst))
    latencia = max(6.5, 38.0 - (inst * 3.5) - (1.5 if perfil == "premium" else 0.0))
    vcpu = round(max(0.5, (mem / 1024) * inst), 1)

    if inst >= 4 or reqs > 2_000_000 or mem >= 2048:
        tier_rec = "Premium v3 (P1v3 Auto-Scale)"
        sla = "99.99%" if inst >= 2 else "99.95%"
    elif inst >= 2 or reqs >= 250_000:
        tier_rec = "Standard (S1 Zone-Redundant)"
        sla = "99.95%"
    else:
        tier_rec = "Basic / Standard (B1/S1 Linux)"
        sla = "99.95%"

    return SimulacaoResposta(
        custo_azure_app_service=round(custo_azure_base, 2),
        custo_azure_container_apps=round(custo_container_apps, 2),
        custo_on_premise_estimado=round(custo_on_premise, 2),
        economia_percentual=round(economia, 1),
        economia_anual_usd=round(economia_anual, 2),
        sla_disponibilidade=sla,
        latencia_media_ms=round(latencia, 1),
        requisicoes_suportadas_segundo=reqs_sec,
        tier_recomendado=tier_rec,
        vcpu_alocada=vcpu,
    )


@app.get("/health", tags=["operação"])
def verificar_saude() -> dict[str, str]:
    with obter_conexao_banco() as conexao:
        conexao.execute("SELECT 1").fetchone()
    return {"status": "ok"}
