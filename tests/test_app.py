import sqlite3

from fastapi.testclient import TestClient

from app import main


def criar_cliente(tmp_path, monkeypatch):
    banco = tmp_path / "contatos.db"
    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DATABASE_PATH", banco)
    return TestClient(main.app), banco


def test_pagina_inicial_e_cabecalhos(tmp_path, monkeypatch):
    cliente, _ = criar_cliente(tmp_path, monkeypatch)

    with cliente:
        resposta = cliente.get("/")

    assert resposta.status_code == 200
    assert "NuvemLab" in resposta.text
    assert resposta.headers["x-content-type-options"] == "nosniff"
    assert resposta.headers["x-frame-options"] == "DENY"


def test_catalogo_de_servicos(tmp_path, monkeypatch):
    cliente, _ = criar_cliente(tmp_path, monkeypatch)

    with cliente:
        resposta = cliente.get("/api/servicos")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 3
    assert resposta.json()[0]["id"] == "arquitetura"


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
    }

    with cliente:
        resposta = cliente.post("/api/contato", json=dados)

    assert resposta.status_code == 201
    assert resposta.json()["status"] == "recebido"

    with sqlite3.connect(banco) as conexao:
        registro = conexao.execute(
            "SELECT nome, email, mensagem FROM contatos"
        ).fetchone()

    assert registro == (dados["nome"], dados["email"], dados["mensagem"])


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
