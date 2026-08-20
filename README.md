# NuvemLab - Projeto Integrador com Docker e Nuvem 

Aplicação cloud-native moderna e segura construída com FastAPI, Docker e Azure:
uma página institucional reativa com alternância de temas (Dark/Light), um **Explorador Interativo de Arquitetura**, um **Console / Playground da API ao vivo**, um **Simulador FinOps de Dimensionamento**, **Monitor de Telemetria em Tempo Real** e formulário de contato com persistência em **SQLite WAL** montado em volume Docker.

---

## Notas de Atualização - Versão 1.1.1

- **Design System Moderno (UI/UX 2026):** Estética Liquid Glass/Glassmorphism, suporte nativo a temas **Dark / Light / Azure**, menu mobile drawer responsivo e animações suaves respeitando `prefers-reduced-motion`.
- **Novas Interações no Frontend:**
  - **Explorador Interativo de Arquitetura:** nós clicáveis da infraestrutura com detalhamento de protocolos, portas e camadas de segurança.
  - **Playground da API REST ao Vivo:** console para executar chamadas reais (`GET` e `POST`), medir latência em ms e visualizar payloads JSON formatados.
  - **Calculadora FinOps & Dimensionamento:** simulação interativa de requisições, memória, RPS suportado e comparativo de custos com servidores dedicados.
  - **Monitor de Telemetria:** painel em tempo real consultando uptime, status operacional e registros gravados.
- **Segurança & Hardening Reforçados (OWASP):**
  - **Rate Limiting por IP** (janela deslizante com HTTP 429 e cabeçalho `Retry-After`).
  - **Armadilha Anti-Spam Honeypot** para descarte silencioso de bots maliciosos.
  - **Sanitização contra XSS** nos campos de entrada e validação estrita Pydantic v2.
  - **Cabeçalhos OWASP:** `Strict-Transport-Security` (HSTS), `Permissions-Policy`, `Cross-Origin-Opener-Policy`, `Cross-Origin-Resource-Policy`, `Content-Security-Policy` e `X-Frame-Options: DENY`.
  - **SQLite WAL Mode:** concorrência sem bloqueio de escrita (`PRAGMA journal_mode = WAL`).

---

## Entregáveis

- [`Dockerfile`](Dockerfile): imagem oficial Python 3.13-slim, build em dois estágios, usuário não-root (UID 10001), porta 8000 e `HEALTHCHECK`.
- [`Relatório final`](docs/relatorio-projeto.pdf): relatório técnico com cinco páginas.
- [`Diagrama da arquitetura`](docs/diagrama-arquitetura.png): versão PNG para entrega. O arquivo SVG editável está no mesmo diretório.
- [`docker-compose.yml`](docker-compose.yml): simulação explícita de rede, mapeamento de porta e volume persistente.

---

## Executar com Docker

Pré-requisito: Docker Desktop ou Docker Engine com Docker Compose.

```bash
docker compose up --build
```

Depois, acesse:

- **Aplicação & Console:** <http://localhost:8000>
- **Swagger/OpenAPI:** <http://localhost:8000/docs>
- **Telemetria Operacional:** <http://localhost:8000/api/status/metrics>
- **Health check:** <http://localhost:8000/health>

O Compose cria:
- a rede bridge nomeada `nuvemlab_net`;
- o mapeamento `127.0.0.1:8000` para a porta `8000` do container;
- o volume `nuvemlab_contatos_data`, montado em `/home/data`.

Para encerrar sem apagar o volume:

```bash
docker compose down
```

---

## Comprovar a persistência

1. Envie uma mensagem pelo formulário ou via API.
2. Reinicie o serviço com `docker compose restart`.
3. Consulte a quantidade de registros:

```bash
docker compose exec web python -c "import sqlite3; print(sqlite3.connect('/home/data/contatos.db').execute('select count(*) from contatos').fetchone()[0])"
```

O total continua preservado após o reinício porque o banco está no volume nomeado.

---

## Executar e testar sem Docker

```bash
python -m venv .venv
```

No Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000
```

Testes automatizados e lint:

```bash
python -m pytest
```

---

## Rotas Principais da API

| Método | Rota | Finalidade | Segurança |
|---|---|---|---|
| `GET` | `/` | Página institucional reativa com Console, FinOps e Telemetria | CSP, HSTS, COOP |
| `GET` | `/api/servicos` | Catálogo enriquecido de serviços em JSON | Rate Limiter, Cache-Control |
| `GET` | `/api/status/metrics` | Telemetria pública, uptime e contagem do banco | Rate Limiter, Cache-Control |
| `POST` | `/api/simulador/custos` | Cálculo de dimensionamento e estimativa FinOps | Pydantic v2 Validation |
| `POST` | `/api/contato` | Validação, sanitização XSS, honeypot e persistência | Rate Limit (5/min), Honeypot, XSS Escape |
| `GET` | `/health` | Saúde da aplicação e do SQLite WAL | Probe Liveness |
| `GET` | `/docs` | Documentação interativa OpenAPI Swagger | CSP Especial Swagger |

Exemplo de envio via cURL:

```bash
curl -X POST http://localhost:8000/api/contato \
  -H "Content-Type: application/json" \
  -d '{"nome":"Maria Souza","email":"maria@example.com","mensagem":"Gostaria de conhecer os serviços.","topico":"Arquitetura Cloud"}'
```

---

## Deploy no Azure App Service

A estratégia selecionada é CI/CD com GitHub Actions, Azure Container Registry e slot `staging` do Azure App Service. O fluxo completo e as configurações necessárias estão em [`docs/deploy-azure.md`](docs/deploy-azure.md).

