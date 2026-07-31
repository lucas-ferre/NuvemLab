# Simulação de deploy no Azure App Service

## Escopo adotado

O projeto usa um único container Linux no modo clássico do Azure App Service.
Nesse modo, a aplicação recebe uma única porta HTTP. Se a opção de sidecars ou
`sitecontainers` for usada, a porta deve ser definida como `target-port` e as
configurações abaixo precisam ser adaptadas.

Recursos propostos:

- Azure Container Registry (ACR) privado;
- App Service Plan Standard;
- Web App Linux com slots `staging` e `production`;
- identidade gerenciada para o App Service baixar imagens;
- GitHub Actions autenticado por OpenID Connect (OIDC).

## Configuração da aplicação

Definir explicitamente estas configurações no App Service e no slot:

| Configuração | Valor | Motivo |
|---|---:|---|
| `WEBSITES_PORT` | `8000` | Roteia o tráfego para a porta interna do container |
| `PORT` | `8000` | Informa ao comando Uvicorn a porta de escuta |
| `WEBSITES_ENABLE_APP_SERVICE_STORAGE` | `true` | Mantém `/home` persistente |
| `DATA_DIR` | `/home/data` | Coloca somente os dados no armazenamento persistente |

Também devem ser habilitados `HTTPS Only`, TLS mínimo compatível com os clientes
e logs do container. O App Service encerra TLS na borda; o container recebe HTTP
e processa os cabeçalhos encaminhados pelo proxy.

## Sequência do pipeline

1. Um `push` na branch `main` dispara o workflow.
2. O job de validação instala dependências, executa Ruff e os testes Pytest.
3. O GitHub obtém um token temporário do Azure por OIDC.
4. A imagem é construída e marcada com o SHA do commit.
5. A imagem é enviada ao ACR privado.
6. O App Service atualiza o slot `staging` para a tag imutável.
7. O pipeline chama `GET /health` no slot.
8. Com o smoke test aprovado, ocorre o swap de `staging` para `production`.
9. Em caso de falha após a promoção, um novo swap restaura a versão anterior.

O workflow de exemplo está em
`.github/workflows/deploy-azure.yml`. Ele usa variáveis de repositório para nomes
e URLs, e secrets somente para os identificadores exigidos pelo login OIDC. Não
há senha do ACR ou publish profile armazenado no repositório.

## Identidade e permissões

O App Service deve ter identidade gerenciada e permissão de leitura no ACR.
Em registros com RBAC tradicional, a função é `AcrPull`. Em registros com o modo
RBAC + ABAC, usar `Container Registry Repository Reader`. A identidade do
pipeline precisa da permissão equivalente de escrita no repositório.

As identidades e configurações de rede não são trocadas durante o swap. Portanto,
o slot `staging` também precisa de acesso ao ACR e às dependências externas.

## Escala e dados

No plano Standard, o Azure Monitor Autoscale pode aumentar ou reduzir o número
de instâncias por CPU, memória, agenda ou outra métrica. Isso implementa
elasticidade; a possibilidade de executar várias instâncias representa
escalabilidade.

O banco SQLite em `/home/data` existe apenas para demonstrar volume persistente
com uma instância. O compartilhamento de um arquivo SQLite em armazenamento de
rede entre várias instâncias pode gerar contenção e risco operacional. Antes de
ativar o scale-out em produção, migrar os contatos para Azure SQL, Azure
Database for PostgreSQL ou outro banco gerenciado.

## Referências oficiais

- [Configurar um container personalizado no App Service](https://learn.microsoft.com/azure/app-service/configure-custom-container)
- [Implantar um container com GitHub Actions](https://learn.microsoft.com/azure/app-service/deploy-container-github-action)
- [Usar slots de implantação](https://learn.microsoft.com/azure/app-service/deploy-staging-slots)
- [Escalar um aplicativo no App Service](https://learn.microsoft.com/azure/app-service/manage-scale-up)
- [Práticas recomendadas do App Service](https://learn.microsoft.com/azure/app-service/app-service-best-practices)
- [Dockerfile: instrução EXPOSE](https://docs.docker.com/reference/dockerfile/#expose)
- [FastAPI em containers](https://fastapi.tiangolo.com/deployment/docker/)

