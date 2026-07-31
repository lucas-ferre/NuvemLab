# NuvemLab - Projeto Integrador com Docker e Nuvem

Aplicação institucional híbrida construída com FastAPI: uma página responsiva,
uma API REST, um formulário de contato persistido em SQLite e documentação
OpenAPI automática. O pacote demonstra Docker localmente e uma estratégia de
deploy automatizado no Azure App Service.

## Entregáveis

- [`Dockerfile`](Dockerfile): imagem oficial Python, build em dois estágios,
  usuário não-root, porta 8000 e `HEALTHCHECK`.
- [`Relatório final`](docs/relatorio-projeto.pdf): relatório técnico com cinco
  páginas.
- [`Diagrama da arquitetura`](docs/diagrama-arquitetura.png): versão PNG para
  entrega. O arquivo SVG editável está no mesmo diretório.
- [`docker-compose.yml`](docker-compose.yml): simulação explícita de rede,
  mapeamento de porta e volume persistente.

## Executar com Docker

Pré-requisito: Docker Desktop ou Docker Engine com Docker Compose.

```bash
docker compose up --build
```

Depois, acesse:

- Aplicação: <http://localhost:8000>
- Swagger/OpenAPI: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>

Abra a interface pela URL do FastAPI. O arquivo `app/templates/index.html` é um
template Jinja e não funciona corretamente quando aberto diretamente pelo
explorador de arquivos, Live Server ou GitHub Pages.

O Compose cria:

- a rede bridge nomeada `nuvemlab_net`;
- o mapeamento `127.0.0.1:8000` para a porta `8000` do container;
- o volume `nuvemlab_contatos_data`, montado em `/home/data`.

Para encerrar sem apagar o volume:

```bash
docker compose down
```

## Comprovar a persistência

1. Envie uma mensagem pelo formulário.
2. Reinicie o serviço com `docker compose restart`.
3. Consulte a quantidade de registros:

```bash
docker compose exec web python -c "import sqlite3; print(sqlite3.connect('/home/data/contatos.db').execute('select count(*) from contatos').fetchone()[0])"
```

O total continua igual depois do reinício porque o banco está no volume nomeado.

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

Testes e lint:

```bash
python -m pytest
python -m ruff check app tests
```

## Rotas principais

| Método | Rota | Finalidade |
|---|---|---|
| `GET` | `/` | Página institucional |
| `GET` | `/api/servicos` | Catálogo de serviços em JSON |
| `POST` | `/api/contato` | Validação e persistência de contato |
| `GET` | `/health` | Saúde da aplicação e do SQLite |
| `GET` | `/docs` | Documentação interativa da API |

Exemplo de requisição:

```bash
curl -X POST http://localhost:8000/api/contato \
  -H "Content-Type: application/json" \
  -d '{"nome":"Maria Souza","email":"maria@example.com","mensagem":"Gostaria de conhecer os serviços."}'
```

## Deploy simulado

A estratégia selecionada é CI/CD com GitHub Actions, Azure Container Registry e
slot `staging` do Azure App Service. O fluxo completo e as configurações
necessárias estão em [`docs/deploy-azure.md`](docs/deploy-azure.md). O workflow
de referência está em [`.github/workflows/deploy-azure.yml`](.github/workflows/deploy-azure.yml).

O job de deploy é desabilitado por padrão, portanto o primeiro `push` executa
somente a validação. Depois de criar a identidade federada e cadastrar os três
secrets OIDC e as variáveis descritas no guia, defina a repository variable
`AZURE_DEPLOY_ENABLED=true` para habilitar a publicação no Azure.

> O SQLite atende à demonstração de volume com uma instância. Para escala
> horizontal de produção, o projeto prevê a migração dos dados para Azure SQL ou
> Azure Database for PostgreSQL.

## Estrutura

```text
.
|-- app/
|   |-- main.py
|   |-- static/
|   `-- templates/
|-- data/
|-- docs/
|-- tests/
|-- Dockerfile
|-- docker-compose.yml
|-- requirements.txt
`-- README.md
```
