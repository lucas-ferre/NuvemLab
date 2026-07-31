from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "relatorio-projeto.pdf"
DIAGRAM = ROOT / "docs" / "diagrama-arquitetura.png"

INK = colors.HexColor("#102238")
INK_SOFT = colors.HexColor("#52697D")
AZURE = colors.HexColor("#0078D4")
AZURE_DARK = colors.HexColor("#005A9E")
CYAN = colors.HexColor("#39D4D8")
PAPER = colors.HexColor("#F7FAFC")
PALE_BLUE = colors.HexColor("#EAF5FC")
LINE = colors.HexColor("#D5E3ED")
GREEN = colors.HexColor("#0A7B57")
AMBER = colors.HexColor("#9A6700")


def configure_fonts() -> tuple[str, str]:
    font_candidates = [
        (
            Path("C:/Windows/Fonts/segoeui.ttf"),
            Path("C:/Windows/Fonts/seguisb.ttf"),
        ),
        (
            Path("C:/Windows/Fonts/arial.ttf"),
            Path("C:/Windows/Fonts/arialbd.ttf"),
        ),
    ]
    for regular, bold in font_candidates:
        if regular.exists() and bold.exists():
            pdfmetrics.registerFont(TTFont("ReportRegular", str(regular)))
            pdfmetrics.registerFont(TTFont("ReportBold", str(bold)))
            return "ReportRegular", "ReportBold"
    return "Helvetica", "Helvetica-Bold"


REGULAR, BOLD = configure_fonts()


def build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName=BOLD,
            fontSize=23,
            leading=26,
            textColor=INK,
            alignment=TA_LEFT,
            spaceAfter=4 * mm,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["Normal"],
            fontName=REGULAR,
            fontSize=10,
            leading=13,
            textColor=INK_SOFT,
            spaceAfter=5 * mm,
        ),
        "page_title": ParagraphStyle(
            "PageTitle",
            parent=base["Heading1"],
            fontName=BOLD,
            fontSize=18,
            leading=22,
            textColor=INK,
            spaceAfter=3.5 * mm,
        ),
        "h2": ParagraphStyle(
            "Heading2",
            parent=base["Heading2"],
            fontName=BOLD,
            fontSize=11.2,
            leading=14,
            textColor=AZURE_DARK,
            spaceBefore=2.2 * mm,
            spaceAfter=1.3 * mm,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName=REGULAR,
            fontSize=8.8,
            leading=12,
            textColor=INK,
            spaceAfter=2.1 * mm,
        ),
        "body_small": ParagraphStyle(
            "BodySmall",
            parent=base["BodyText"],
            fontName=REGULAR,
            fontSize=8.2,
            leading=10.7,
            textColor=INK,
            spaceAfter=1.3 * mm,
        ),
        "body_tiny": ParagraphStyle(
            "BodyTiny",
            parent=base["BodyText"],
            fontName=REGULAR,
            fontSize=7.25,
            leading=9.1,
            textColor=INK_SOFT,
            spaceAfter=0.8 * mm,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName=REGULAR,
            fontSize=8.35,
            leading=11.2,
            leftIndent=4.5 * mm,
            firstLineIndent=-3.2 * mm,
            textColor=INK,
            spaceAfter=1.2 * mm,
        ),
        "caption": ParagraphStyle(
            "Caption",
            parent=base["Normal"],
            fontName=REGULAR,
            fontSize=7.2,
            leading=8.8,
            alignment=TA_CENTER,
            textColor=INK_SOFT,
            spaceBefore=1.2 * mm,
            spaceAfter=2 * mm,
        ),
        "table": ParagraphStyle(
            "Table",
            parent=base["Normal"],
            fontName=REGULAR,
            fontSize=7.5,
            leading=9.5,
            textColor=INK,
        ),
        "table_bold": ParagraphStyle(
            "TableBold",
            parent=base["Normal"],
            fontName=BOLD,
            fontSize=7.5,
            leading=9.5,
            textColor=INK,
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            parent=base["Normal"],
            fontName=BOLD,
            fontSize=7.5,
            leading=9.3,
            textColor=colors.white,
        ),
        "callout": ParagraphStyle(
            "Callout",
            parent=base["Normal"],
            fontName=REGULAR,
            fontSize=8.8,
            leading=11.8,
            textColor=INK,
        ),
        "callout_title": ParagraphStyle(
            "CalloutTitle",
            parent=base["Normal"],
            fontName=BOLD,
            fontSize=9,
            leading=11.5,
            textColor=AZURE_DARK,
        ),
        "code": ParagraphStyle(
            "Code",
            parent=base["Code"],
            fontName="Courier",
            fontSize=7.6,
            leading=10,
            leftIndent=3 * mm,
            rightIndent=3 * mm,
            borderColor=LINE,
            borderWidth=0.5,
            borderPadding=2.5 * mm,
            backColor=colors.white,
            textColor=INK,
            spaceBefore=1.5 * mm,
            spaceAfter=2.5 * mm,
        ),
    }


STYLES = build_styles()


def p(text: str, style: str = "body") -> Paragraph:
    return Paragraph(text, STYLES[style])


def table(
    rows: list[list[str | Paragraph]],
    widths: list[float],
    *,
    compact: bool = False,
    header: bool = True,
) -> Table:
    converted: list[list[Paragraph]] = []
    for row_index, row in enumerate(rows):
        converted.append(
            [
                cell
                if isinstance(cell, Paragraph)
                else p(
                    cell,
                    "table_header"
                    if header and row_index == 0
                    else "table_bold"
                    if column_index == 0
                    else "table",
                )
                for column_index, cell in enumerate(row)
            ]
        )

    result = Table(converted, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    result.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), AZURE_DARK if header else colors.white),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.35, LINE),
                ("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1), [colors.white, PAPER]),
                ("LEFTPADDING", (0, 0), (-1, -1), 2.1 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2.1 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 1.7 * mm if compact else 2.1 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.7 * mm if compact else 2.1 * mm),
            ]
        )
    )
    return result


def callout(title: str, text: str, color: colors.Color = PALE_BLUE) -> Table:
    result = Table(
        [[p(title, "callout_title"), p(text, "callout")]],
        colWidths=[31 * mm, 145 * mm],
        hAlign="LEFT",
    )
    result.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), color),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("LINEBEFORE", (0, 0), (0, -1), 3, AZURE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 2.6 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6 * mm),
            ]
        )
    )
    return result


def bullet(text: str) -> Paragraph:
    return p(f"- {text}", "bullet")


def draw_page(canvas, doc) -> None:
    page_width, page_height = A4
    canvas.saveState()
    canvas.setFillColor(PAPER)
    canvas.rect(0, 0, page_width, page_height, fill=1, stroke=0)

    canvas.setFillColor(AZURE)
    canvas.rect(0, page_height - 7 * mm, page_width, 7 * mm, fill=1, stroke=0)
    canvas.setFillColor(CYAN)
    canvas.rect(0, page_height - 7 * mm, 44 * mm, 7 * mm, fill=1, stroke=0)

    canvas.setFont(BOLD, 7)
    canvas.setFillColor(INK_SOFT)
    canvas.drawString(18 * mm, page_height - 13 * mm, "PROJETO INTEGRADOR COM DOCKER E NUVEM")
    canvas.setFont(REGULAR, 7)
    canvas.drawRightString(page_width - 18 * mm, page_height - 13 * mm, "NuvemLab")

    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(18 * mm, 12 * mm, page_width - 18 * mm, 12 * mm)
    canvas.setFillColor(INK_SOFT)
    canvas.setFont(REGULAR, 6.7)
    canvas.drawString(18 * mm, 7.2 * mm, "Relatório técnico - Unidade 05")
    canvas.drawRightString(
        page_width - 18 * mm,
        7.2 * mm,
        f"Página {doc.page} de 5",
    )
    canvas.restoreState()


def build_story() -> list:
    story: list = []

    # Página 1
    story.extend(
        [
            Spacer(1, 3 * mm),
            p("Projeto Integrador com<br/>Docker e Nuvem", "title"),
            p(
                "<b>NuvemLab</b> - aplicação institucional híbrida com FastAPI, "
                "Docker e Azure App Service",
                "subtitle",
            ),
            table(
                [
                    [
                        "<b>Equipe</b><br/>________________________________",
                        "<b>Turma</b><br/>________________",
                        "<b>Data</b><br/>____/____/________",
                    ]
                ],
                [88 * mm, 44 * mm, 44 * mm],
                compact=True,
                header=False,
            ),
            Spacer(1, 3.5 * mm),
            p("Resumo executivo", "h2"),
            p(
                "O NuvemLab combina uma página responsiva com uma API REST real. "
                "A solução publica o catálogo em <b>GET /api/servicos</b>, recebe "
                "contatos em <b>POST /api/contato</b>, documenta a API em "
                "<b>/docs</b> e expõe o health check <b>/health</b>. O código é "
                "empacotado em um container Docker e preparado para o Azure App "
                "Service. O modelo principal é <b>PaaS</b>: a plataforma opera "
                "infraestrutura, host, roteamento, TLS e escala; a equipe mantém "
                "imagem, código, configurações e dados.",
            ),
            Spacer(1, 1 * mm),
            Image(str(DIAGRAM), width=176 * mm, height=99 * mm),
            p(
                "Figura 1 - Fluxos de entrega e execução. O SQLite demonstra o "
                "volume persistente com uma instância.",
                "caption",
            ),
            callout(
                "Decisão arquitetural",
                "<b>PaaS + FastAPI + Docker + Azure App Service.</b> A combinação "
                "mantém a aplicação portável e reduz o trabalho operacional sem "
                "abrir mão do controle sobre o código e a imagem.",
            ),
        ]
    )
    story.append(PageBreak())

    # Página 2
    story.extend(
        [
            p("1. Planejamento da arquitetura", "page_title"),
            p("Escolha e justificativa do modelo de serviço", "h2"),
            p(
                "Foi escolhido <b>PaaS</b>, representado pelo Azure App Service. "
                "Em IaaS, a equipe administraria máquinas virtuais, sistema "
                "operacional, patches e parte da rede, trabalho desproporcional a "
                "uma aplicação pequena. SaaS não se aplica porque o objetivo é "
                "desenvolver software próprio. XaaS é um termo abrangente, porém "
                "menos preciso para a divisão de responsabilidades adotada. O "
                "container personalizado adiciona portabilidade, mas a plataforma "
                "gerenciada continua sendo o serviço principal.",
            ),
            table(
                [
                    ["Modelo", "Avaliação", "Justificativa"],
                    [
                        "IaaS",
                        "Não adotado",
                        "Maior controle, mas exige gestão de VM, SO e patches.",
                    ],
                    [
                        "PaaS",
                        "Adotado",
                        "Foco no código; runtime, TLS, roteamento e escala gerenciados.",
                    ],
                    [
                        "SaaS",
                        "Não aplicável",
                        "Seria consumir uma solução pronta, não implantar a aplicação.",
                    ],
                    [
                        "XaaS",
                        "Conceito geral",
                        "Útil como categoria ampla, mas não descreve a escolha com precisão.",
                    ],
                ],
                [24 * mm, 34 * mm, 118 * mm],
                compact=True,
            ),
            Spacer(1, 3 * mm),
            p("Componentes usados", "h2"),
            table(
                [
                    ["Componente", "Papel na solução"],
                    ["FastAPI + Uvicorn", "Página, API REST, validação, OpenAPI e servidor ASGI."],
                    [
                        "Jinja2 + assets locais",
                        "HTML responsivo, estilos e integração do formulário.",
                    ],
                    ["SQLite", "Persistência demonstrativa de contatos em uma instância."],
                    ["Docker", "Imagem reproduzível baseada em Python oficial."],
                    ["Docker Compose", "Rede, porta, volume e políticas locais de segurança."],
                    [
                        "Azure Container Registry",
                        "Registro privado com imagens versionadas por commit.",
                    ],
                    ["Azure App Service", "PaaS Linux para HTTPS, slots, métricas e escala."],
                    ["GitHub Actions", "Testes, build, push, smoke test e promoção."],
                ],
                [50 * mm, 126 * mm],
                compact=True,
            ),
            Spacer(1, 3 * mm),
            callout(
                "Modo de hospedagem",
                "O relatório assume <b>um único container Linux no modo clássico</b> "
                "do App Service. Na configuração moderna com sidecars, a porta é "
                "definida por <i>target-port</i>, e não por WEBSITES_PORT.",
            ),
            Spacer(1, 2 * mm),
            p("Fluxo de execução", "h2"),
            p(
                "O usuário acessa a borda HTTPS do App Service. A plataforma "
                "encaminha a requisição à porta 8000 do container. O FastAPI "
                "processa a página e os endpoints; contatos válidos são gravados "
                "em <b>/home/data/contatos.db</b>. O endpoint /health valida a "
                "aplicação e a abertura do banco.",
            ),
        ]
    )
    story.append(PageBreak())

    # Página 3
    story.extend(
        [
            p("2. Preparação do ambiente com Docker", "page_title"),
            p("Dockerfile configurado", "h2"),
            p(
                "A imagem usa <b>python:3.13-slim</b> e dois estágios. O primeiro "
                "cria o ambiente virtual e instala dependências; o segundo recebe "
                "somente o runtime e o código. O processo executa com UID/GID "
                "10001, sem root. O EXPOSE documenta a porta, enquanto o mapeamento "
                "real é feito pelo Compose ou pela plataforma.",
            ),
            table(
                [
                    ["Elemento", "Implementação", "Resultado"],
                    [
                        "Imagem oficial",
                        "python:3.13-slim",
                        "Base pequena e mantida pelo projeto Python.",
                    ],
                    [
                        "Multi-stage",
                        "builder + runtime",
                        "Dependências isoladas da etapa de construção.",
                    ],
                    ["Privilégios", "USER app (10001)", "Reduz o impacto de uma exploração."],
                    ["Porta", "EXPOSE 8000", "Contrato explícito; não publica a porta sozinho."],
                    [
                        "Inicialização",
                        "Uvicorn em 0.0.0.0:8000",
                        "Aceita o tráfego encaminhado pela plataforma.",
                    ],
                    ["Proxy", "--proxy-headers", "Interpreta os cabeçalhos da terminação TLS."],
                    ["Saúde", "GET /health", "Verifica API e acesso ao SQLite."],
                    ["Arquivos", ".dockerignore", "Exclui caches, Git, banco, testes e segredos."],
                ],
                [34 * mm, 61 * mm, 81 * mm],
                compact=True,
            ),
            Spacer(1, 3 * mm),
            p("Simulação de rede, porta e volume persistente", "h2"),
            table(
                [
                    ["Requisito", "Configuração no docker-compose.yml", "Evidência"],
                    [
                        "Rede",
                        "bridge nomeada nuvemlab_net",
                        "Isolamento e resolução do serviço web.",
                    ],
                    [
                        "Porta",
                        "127.0.0.1:8000:8000",
                        "Acesso local sem expor em todas as interfaces.",
                    ],
                    [
                        "Volume",
                        "nuvemlab_contatos_data:/home/data",
                        "O SQLite permanece após restart.",
                    ],
                ],
                [30 * mm, 74 * mm, 72 * mm],
                compact=True,
            ),
            Spacer(1, 3 * mm),
            p("Controles de segurança", "h2"),
            bullet("<b>Filesystem somente leitura</b>, exceto volume e tmpfs em /tmp."),
            bullet("<b>cap_drop: ALL</b> e <b>no-new-privileges</b> no Compose."),
            bullet("Validação Pydantic de formato e tamanho; SQL parametrizado."),
            bullet("CSP, nosniff, proteção contra frames e política de referenciador."),
            bullet("Segredos não entram na imagem nem no repositório."),
            p("Execução e comprovação", "h2"),
            p(
                "O comando <b>docker compose up --build</b> cria todos os recursos. "
                "Depois de enviar um contato, <b>docker compose restart</b> reinicia "
                "o serviço sem apagar o volume; a contagem no SQLite permanece. "
                "O comando <b>docker compose down</b> encerra o ambiente e preserva "
                "o volume por padrão.",
            ),
            p(
                "docker compose up --build<br/>"
                'docker compose exec web python -c "import sqlite3; '
                "print(sqlite3.connect('/home/data/contatos.db').execute("
                "'select count(*) from contatos').fetchone()[0])\"",
                "code",
            ),
        ]
    )
    story.append(PageBreak())

    # Página 4
    story.extend(
        [
            p("3. Simulação de deploy no Azure", "page_title"),
            p("Estratégia automatizada (CI/CD)", "h2"),
            p(
                "A entrega selecionada combina GitHub Actions, Azure Container "
                "Registry e Azure App Service. A autenticação usa OpenID Connect "
                "(OIDC), evitando publish profile e senhas permanentes do registro.",
            ),
            table(
                [
                    ["Etapa", "Ação e critério de aceite"],
                    ["1. Validar", "Instala dependências; Ruff e seis testes precisam passar."],
                    ["2. Autenticar", "GitHub obtém token temporário do Azure por OIDC."],
                    ["3. Construir", "Docker cria a imagem e aplica a tag imutável github.sha."],
                    ["4. Publicar", "A imagem é enviada ao ACR privado."],
                    ["5. Staging", "O slot recebe a nova tag e inicia o container."],
                    ["6. Testar", "O pipeline exige resposta 200 de GET /health."],
                    ["7. Promover", "Swap aquece e move staging para production."],
                    ["8. Reverter", "Novo swap restaura a versão anterior se necessário."],
                ],
                [34 * mm, 142 * mm],
                compact=True,
            ),
            Spacer(1, 3 * mm),
            p("Configurações do App Service", "h2"),
            table(
                [
                    ["App setting", "Valor", "Finalidade"],
                    ["WEBSITES_PORT", "8000", "Roteia a única porta HTTP do container clássico."],
                    ["PORT", "8000", "Configura a porta de escuta do Uvicorn."],
                    [
                        "WEBSITES_ENABLE_APP_SERVICE_STORAGE",
                        "true",
                        "Habilita a persistência compartilhada em /home.",
                    ],
                    [
                        "DATA_DIR",
                        "/home/data",
                        "Mantém o código em /app e somente os dados em /home.",
                    ],
                ],
                [76 * mm, 25 * mm, 75 * mm],
                compact=True,
            ),
            Spacer(1, 3 * mm),
            p("Plataforma, identidade e segurança", "h2"),
            bullet("<b>Plano Standard:</b> fornece slots e Azure Monitor Autoscale por métricas."),
            bullet(
                "<b>ACR privado:</b> App Service usa identidade gerenciada; em RBAC "
                "tradicional, recebe AcrPull."
            ),
            bullet(
                "<b>TLS:</b> termina na borda do App Service; habilitar HTTPS Only, "
                "TLS mínimo e logs do container."
            ),
            bullet(
                "<b>Slots:</b> identidades e rede não são trocadas; staging também "
                "precisa de permissão para baixar a imagem."
            ),
            callout(
                "Limite consciente",
                "SQLite em /home demonstra persistência com <b>uma instância</b>. "
                "Antes do scale-out de produção, os contatos migram para Azure SQL "
                "ou Azure Database for PostgreSQL, mantendo os containers sem estado.",
                colors.HexColor("#FFF8E6"),
            ),
        ]
    )
    story.append(PageBreak())

    # Página 5
    story.extend(
        [
            p("4. Benefícios, desafios e conceitos de nuvem", "page_title"),
            p("Benefícios e desafios", "h2"),
            table(
                [
                    ["Benefício", "Desafio relacionado", "Tratamento"],
                    [
                        "Menor carga operacional",
                        "Dependência do provedor",
                        "Container padrão e configuração documentada.",
                    ],
                    [
                        "Deploy repetível",
                        "Falha de uma versão",
                        "Staging, smoke test, tag imutável e rollback.",
                    ],
                    [
                        "TLS e identidade gerenciados",
                        "Segredos e permissões",
                        "OIDC e privilégio mínimo.",
                    ],
                    [
                        "Escala horizontal",
                        "Estado compartilhado",
                        "Banco gerenciado antes de múltiplas instâncias.",
                    ],
                    [
                        "Observabilidade",
                        "Custo do plano",
                        "Métricas, orçamento, alertas e limites de escala.",
                    ],
                ],
                [42 * mm, 54 * mm, 80 * mm],
                compact=True,
            ),
            Spacer(1, 2.5 * mm),
            p("Escalabilidade, elasticidade e responsabilidade compartilhada", "h2"),
            p(
                "<b>Escalabilidade</b> é a capacidade de aumentar recursos ou "
                "instâncias. <b>Elasticidade</b> é ajustar essa capacidade "
                "automaticamente conforme métricas e limites. O scale-out do App "
                "Service fornece escalabilidade; as regras do Azure Monitor "
                "Autoscale acrescentam elasticidade.",
                "body_small",
            ),
            table(
                [
                    ["Responsabilidade Azure", "Responsabilidade da equipe"],
                    [
                        "Datacenter, hardware, virtualização e host",
                        "Código, lógica de negócio e testes",
                    ],
                    [
                        "Plataforma, patches gerenciados, roteamento e TLS",
                        "Dockerfile, imagem e dependências",
                    ],
                    [
                        "Mecanismo de escala, slots e métricas",
                        "Dados, retenção, variáveis e segredos",
                    ],
                    [
                        "Disponibilidade do serviço contratado",
                        "Alertas, incidentes, permissões e custos",
                    ],
                ],
                [88 * mm, 88 * mm],
                compact=True,
            ),
            Spacer(1, 2.5 * mm),
            p("Validação e evidências", "h2"),
            table(
                [
                    ["Verificação", "Resultado"],
                    [
                        "Pytest",
                        "6 testes: página, docs, catálogo, persistência, validação e health check.",
                    ],
                    ["Ruff", "Código Python sem erros de lint."],
                    ["Interface", "Sem erros de console; formulário retornou 201 Created."],
                    ["Diagrama", "SVG válido e PNG renderizado sem cortes ou sobreposições."],
                    ["Relatório", "PDF final com exatamente cinco páginas."],
                ],
                [42 * mm, 134 * mm],
                compact=True,
            ),
            Spacer(1, 2 * mm),
            p("Conclusão", "h2"),
            p(
                "A proposta atende ao enunciado com uma solução executável, segura "
                "e reproduzível. PaaS reduz o trabalho indiferenciado de "
                "infraestrutura; Docker padroniza a execução; CI/CD e slots reduzem "
                "o risco de entrega. O SQLite cumpre a demonstração de volume, e a "
                "migração prevista para um banco gerenciado completa o caminho para "
                "uma produção realmente escalável.",
                "body_small",
            ),
            p("Referências oficiais", "h2"),
            p(
                "1. Microsoft Learn. <link href='https://learn.microsoft.com/"
                "azure/app-service/configure-custom-container' "
                "color='#005A9E'>Configure a custom container for Azure App Service</link>.<br/>"
                "2. Microsoft Learn. <link href='https://learn.microsoft.com/"
                "azure/app-service/deploy-container-github-action' "
                "color='#005A9E'>Deploy a container with GitHub Actions</link>.<br/>"
                "3. Microsoft Learn. <link href='https://learn.microsoft.com/"
                "azure/app-service/deploy-staging-slots' "
                "color='#005A9E'>Set up staging environments</link>.<br/>"
                "4. Microsoft Learn. <link href='https://learn.microsoft.com/"
                "azure/app-service/manage-scale-up' "
                "color='#005A9E'>Scale up and out in App Service</link>.<br/>"
                "5. Docker Docs. <link href='https://docs.docker.com/reference/dockerfile/#expose' "
                "color='#005A9E'>Dockerfile reference: EXPOSE</link>.<br/>"
                "6. FastAPI. <link href='https://fastapi.tiangolo.com/deployment/docker/' "
                "color='#005A9E'>FastAPI in Containers - Docker</link>.",
                "body_tiny",
            ),
        ]
    )

    return story


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=17 * mm,
        leftMargin=17 * mm,
        topMargin=20 * mm,
        bottomMargin=16 * mm,
        title="Projeto Integrador com Docker e Nuvem - NuvemLab",
        author="Equipe NuvemLab",
        subject="Relatório técnico do Projeto Integrador",
    )
    doc.build(build_story(), onFirstPage=draw_page, onLaterPages=draw_page)
    print(OUTPUT)


if __name__ == "__main__":
    main()
