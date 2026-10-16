# NuvemLab - Projeto Integrador com Docker e Nuvem

Aplicação cloud-native moderna e segura construída com **FastAPI**, **Docker** e **Azure App Service**:
uma página institucional reativa acompanhada de **Explorador Interativo de Arquitetura**, **Console / Playground da API ao Vivo**, **Calculadora FinOps Multi-Tier**, **Monitor de Telemetria em Tempo Real** e formulário de contato com persistência em **SQLite WAL** montado em volume Docker.

---

## Visão Geral e Arquitetura da Solução

- **Interface & Design System:**
  - Identidade tipográfica *Cloud Native Geometric* combinando `Space Grotesk` (títulos e marca), `Plus Jakarta Sans` (interface e leitura) e `JetBrains Mono` (código, métricas e protocolos com números tabulares `tabular-nums`).
  - Estética *Liquid Glass / Glassmorphism* com suporte nativo a três temas visuais (**Dark**, **Azure Deep** e **Light**), menu mobile drawer responsivo, **Command Palette rápida (`Ctrl+K`)** e animações suaves respeitando `prefers-reduced-motion`.
- **Módulos Interativos:**
  - **Explorador de Arquitetura:** topologia navegável por clique ou teclado detalhando protocolos, portas, camadas de defesa e teste de latência real por componente.
  - **Playground da API REST:** console integrado para executar chamadas reais (`GET` e `POST`), medir o tempo de processamento em milissegundos, inspecionar cabeçalhos HTTP/OWASP e gerar comandos `cURL`.
  - **Calculadora FinOps & Dimensionamento:** simulação de requisições, memória, instâncias e perfis de carga (*Dev/Basic*, *Standard S1* e *Premium P1v3*) comparando custos entre **Azure App Service**, **Azure Container Apps** e infraestrutura **On-Premise**, com exportação em JSON.
  - **Monitor de Telemetria & Persistência:** painel em tempo real com curva gráfica de latência (SVG Sparkline), tamanho do banco em KB, uptime, histórico de disponibilidade e mural de protocolos recentes com mascaramento automático de dados (LGPD).
- **Segurança & Hardening (OWASP):**
  - **Rate Limiting por IP** em janela deslizante com cabeçalhos `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` e `Retry-After`.
  - **Proteção Anti-Spam e Anti-XSS:** armadilha *Honeypot* para descarte silencioso de bots, sanitização de HTML e validação estrita com Pydantic v2.
  - **Cabeçalhos de Segurança:** `Strict-Transport-Security` (HSTS), `Content-Security-Policy` (CSP), `Permissions-Policy`, `Cross-Origin-Opener-Policy`, `Cross-Origin-Resource-Policy` e `X-Frame-Options: DENY`.
  - **Persistência Concorrente:** banco SQLite configurado em modo `WAL` (*Write-Ahead Logging*) com gerenciamento seguro de conexões e container executado sob usuário não-root (`UID 10001`).

---

## Entregáveis

- [`Dockerfile`](Dockerfile): imagem oficial Python 3.13-slim, build em dois estágios, usuário não-root (`UID 10001`), porta `8000` e `HEALTHCHECK`.
- [`Relatório final`](docs/relatorio-projeto.pdf): relatório técnico com cinco páginas.
- [`Diagrama da arquitetura`](docs/diagrama-arquitetura.png): versão PNG para entrega (com arquivo SVG editável no mesmo diretório).
- [`docker-compose.yml`](docker-compose.yml): configuração explícita de rede bridge, mapeamento de porta, filesystem somente leitura e volume persistente.

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
- **Protocolos Recentes (LGPD):** <http://localhost:8000/api/contatos/recentes>
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

## Comprovar a Persistência

1. Envie uma mensagem pelo formulário de contato ou via API (o protocolo gerado é exibido imediatamente no painel de protocolos persistidos da página).
2. Reinicie o serviço com `docker compose restart`.
3. Consulte a quantidade de registros no banco:

```bash
docker compose exec web python -c "import sqlite3; print(sqlite3.connect('/home/data/contatos.db').execute('select count(*) from contatos').fetchone()[0])"
```

O total continua preservado após o reinício porque o banco está armazenado no volume nomeado.

---

## Executar e Testar sem Docker

```bash
python -m venv .venv
```

No Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000
```

Validação estática (lint) e testes automatizados:

```bash
python -m ruff check .
python -m pytest
```

---

## Rotas Principais da API

| Método | Rota | Finalidade | Segurança |
|---|---|---|---|
| `GET` | `/` | Página institucional com Console API, FinOps, Command Palette e Telemetria | CSP, HSTS, COOP |
| `GET` | `/api/servicos` | Catálogo enriquecido de serviços em JSON | Rate Limiter, Cache-Control |
| `GET` | `/api/status/metrics` | Telemetria operacional, curva de latência, tamanho do DB e contagem | Cache-Control, X-Process-Time-Ms |
| `GET` | `/api/contatos/recentes` | Últimos protocolos gravados com mascaramento de dados (LGPD) | Rate Limiter, LGPD Masking |
| `POST` | `/api/simulador/custos` | Cálculo de dimensionamento Multi-Tier e comparativo FinOps | Pydantic v2 Validation |
| `POST` | `/api/contato` | Validação, sanitização XSS, honeypot e persistência SQLite WAL | Rate Limit (5/min), Honeypot, XSS Escape |
| `GET` | `/health` | Saúde da aplicação e verificação de acesso ao SQLite WAL | Probe Liveness |
| `GET` | `/docs` | Documentação interativa OpenAPI Swagger | CSP Especial Swagger |

Exemplo de envio via cURL:

```bash
curl -X POST http://localhost:8000/api/contato \
  -H "Content-Type: application/json" \
  -d '{"nome":"Maria Souza","email":"maria@example.com","mensagem":"Gostaria de conhecer os serviços.","topico":"Arquitetura Cloud"}'
```

---

## Deploy no Azure App Service

A estratégia adotada utiliza CI/CD com GitHub Actions, autenticação federada OIDC, Azure Container Registry (ACR) e slot `staging` no Azure App Service com promoção por swap. O fluxo completo e as configurações necessárias estão documentados em [`docs/deploy-azure.md`](docs/deploy-azure.md).
