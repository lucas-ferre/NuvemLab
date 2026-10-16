import sqlite3

from fastapi.testclient import TestClient

from app import main


def criar_cliente(tmp_path, monkeypatch):
    banco = tmp_path / "contatos.db"
    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DATABASE_PATH", banco)
    main._ip_request_history.clear()
    main._ip_contact_history.clear()
    main._recent_latencies_ms.clear()
    return TestClient(main.app), banco


def test_pagina_inicial_e_cabecalhos(tmp_path, monkeypatch):
    cliente, _ = criar_cliente(tmp_path, monkeypatch)

    with cliente:
        resposta = cliente.get("/")

    assert resposta.status_code == 200
    assert "NuvemLab" in resposta.text
    assert 'href="/static/styles.css?v=20260820"' in resposta.text
    assert 'src="/static/app.js?v=20260820"' in resposta.text
    assert "Space+Grotesk" in resposta.text
    assert "Plus+Jakarta+Sans" in resposta.text
    assert "JetBrains+Mono" in resposta.text
    assert "cmd-palette-backdrop" in resposta.text
    assert resposta.headers["x-content-type-options"] == "nosniff"
    assert resposta.headers["x-frame-options"] == "DENY"
    assert "strict-transport-security" in resposta.headers
    assert "permissions-policy" in resposta.headers
    assert resposta.headers["cross-origin-opener-policy"] == "same-origin"
    assert "https://fonts.gstatic.com" in resposta.headers["content-security-policy"]
    assert "x-process-time-ms" in resposta.headers


def test_arquivos_estaticos_sao_servidos(tmp_path, monkeypatch):
    cliente, _ = criar_cliente(tmp_path, monkeypatch)

    with cliente:
        css = cliente.get("/static/styles.css")
        javascript = cliente.get("/static/app.js")

    assert css.status_code == 200
    assert css.headers["content-type"].startswith("text/css")
    assert "--bg-main" in css.text
    assert "--font-display" in css.text
    assert "Space Grotesk" in css.text
    assert '[data-theme="azure"]' in css.text
    assert javascript.status_code == 200
    assert "javascript" in javascript.headers["content-type"]
    assert "fetchTelemetryMetrics" in javascript.text
    assert "fetchRecentContacts" in javascript.text


def test_catalogo_de_servicos(tmp_path, monkeypatch):
    cliente, _ = criar_cliente(tmp_path, monkeypatch)

    with cliente:
        resposta = cliente.get("/api/servicos")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 4
    assert resposta.json()[0]["id"] == "arquitetura"
    assert resposta.json()[3]["id"] == "seguranca"
    assert resposta.headers["x-ratelimit-limit"] == "120"
    assert "x-ratelimit-remaining" in resposta.headers


def test_endpoint_metricas_telemetria(tmp_path, monkeypatch):
    cliente, _ = criar_cliente(tmp_path, monkeypatch)

    with cliente:
        cliente.get("/api/servicos")
        resposta = cliente.get("/api/status/metrics")

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["status"] == "operacional"
    assert dados["versao"] == "1.2.0"
    assert "uptime_segundos" in dados
    assert "total_contatos" in dados
    assert "WAL" in dados["banco_modo"]
    assert len(dados["seguranca_ativa"]) >= 4
    assert dados["total_requisicoes"] >= 1
    assert "latencia_media_ms" in dados
    assert "banco_tamanho_kb" in dados


def test_simulador_custos_finops(tmp_path, monkeypatch):
    cliente, _ = criar_cliente(tmp_path, monkeypatch)

    payload = {
        "requisicoes_mes": 100000,
        "memoria_mb": 512,
        "instancias": 2,
        "perfil": "standard",
    }
    with cliente:
        resposta = cliente.post("/api/simulador/custos", json=payload)

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["custo_azure_app_service"] > 0
    assert dados["custo_azure_container_apps"] > 0
    assert dados["economia_percentual"] > 0
    assert dados["economia_anual_usd"] > 0
    assert dados["sla_disponibilidade"] == "99.95%"
    assert "Standard" in dados["tier_recomendado"]


def test_documentacao_interativa_tem_csp_compativel(tmp_path, monkeypatch):
    cliente, _ = criar_cliente(tmp_path, monkeypatch)

    with cliente:
        resposta = cliente.get("/docs")

    assert resposta.status_code == 200
    assert "Swagger UI" in resposta.text
    assert "https://cdn.jsdelivr.net" in resposta.headers["content-security-policy"]


def test_contato_valido_e_persistido(tmp_path, monkeypatch):
    cliente, banco = criar_cliente(tmp_path, monkeypatch)
    dados = {
        "nome": "Luane Silva",
        "email": "luane@example.com",
        "mensagem": "Gostaria de conhecer melhor os serviços oferecidos.",
        "topico": "Arquitetura Cloud",
    }

    with cliente:
        resposta = cliente.post("/api/contato", json=dados)

    assert resposta.status_code == 201
    resposta_json = resposta.json()
    assert resposta_json["status"] == "recebido"
    assert resposta_json["protocolo"].startswith("NLB-")

    with sqlite3.connect(banco) as conexao:
        registro = conexao.execute(
            "SELECT nome, email, mensagem, topico FROM contatos"
        ).fetchone()

    assert registro == (dados["nome"], dados["email"], dados["mensagem"], dados["topico"])


def test_contatos_recentes_mascaramento_lgpd(tmp_path, monkeypatch):
    cliente, _ = criar_cliente(tmp_path, monkeypatch)
    dados = {
        "nome": "Carlos Eduardo Mendes",
        "email": "carlos.mendes@empresa.com.br",
        "mensagem": "Solicito avaliação de migração de containers para Azure App Service.",
        "topico": "Docker & Containers",
    }

    with cliente:
        cliente.post("/api/contato", json=dados)
        recentes = cliente.get("/api/contatos/recentes?limite=5")

    assert recentes.status_code == 200
    lista = recentes.json()
    assert len(lista) == 1
    item = lista[0]
    assert item["protocolo"].startswith("NLB-")
    assert item["nome_mascarado"] == "Carlos M."
    assert item["email_mascarado"] == "ca***@empresa.com.br"
    assert "carlos.mendes@" not in item["email_mascarado"]


def test_contato_sanitizacao_xss(tmp_path, monkeypatch):
    cliente, banco = criar_cliente(tmp_path, monkeypatch)
    dados = {
        "nome": "<b>Hacker</b>",
        "email": "teste@example.com",
        "mensagem": "<script>alert('xss')</script> Mensagem com tags.",
        "topico": "<img src=x onerror=alert(1)>",
    }

    with cliente:
        resposta = cliente.post("/api/contato", json=dados)

    assert resposta.status_code == 201

    with sqlite3.connect(banco) as conexao:
        registro = conexao.execute(
            "SELECT nome, mensagem, topico FROM contatos"
        ).fetchone()

    assert "<script>" not in registro[1]
    assert "&lt;script&gt;" in registro[1]
    assert "&lt;b&gt;Hacker&lt;/b&gt;" in registro[0]


def test_contato_honeypot_descarta_spambot(tmp_path, monkeypatch):
    cliente, banco = criar_cliente(tmp_path, monkeypatch)
    dados = {
        "nome": "Bot Spammer",
        "email": "bot@spam.com",
        "mensagem": "Compre produtos agora mesmo online!",
        "hp_website": "http://spamlink.xyz",
    }

    with cliente:
        resposta = cliente.post("/api/contato", json=dados)

    assert resposta.status_code == 201
    assert resposta.json()["protocolo"] == "NLB-BOT-DISCARD"

    with sqlite3.connect(banco) as conexao:
        total = conexao.execute("SELECT count(*) FROM contatos").fetchone()[0]
    assert total == 0


def test_contato_rate_limiting(tmp_path, monkeypatch):
    cliente, _ = criar_cliente(tmp_path, monkeypatch)
    dados = {
        "nome": "Usuario Teste",
        "email": "usuario@example.com",
        "mensagem": "Testando limite de requisições consecutivas.",
    }

    with cliente:
        for _ in range(5):
            res = cliente.post("/api/contato", json=dados)
            assert res.status_code == 201

        bloqueado = cliente.post("/api/contato", json=dados)
        assert bloqueado.status_code == 429
        assert "Retry-After" in bloqueado.headers


def test_contato_invalido_nao_e_aceito(tmp_path, monkeypatch):
    cliente, _ = criar_cliente(tmp_path, monkeypatch)

    with cliente:
        resposta = cliente.post(
            "/api/contato",
            json={"nome": "A", "email": "email-invalido", "mensagem": "curta"},
        )

    assert resposta.status_code == 422


def test_healthcheck(tmp_path, monkeypatch):
    cliente, _ = criar_cliente(tmp_path, monkeypatch)

    with cliente:
        resposta = cliente.get("/health")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}
