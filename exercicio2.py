"""
Exercício 2 - API de Locadora de Filmes
Python + Flask + SQLite

PROBLEMA: uma locadora quer controlar seu catálogo de filmes, as categorias
e as locações (quem alugou o quê e se já devolveu).
USUÁRIOS: atendentes e gerente da locadora.

TABELAS (3, relacionadas):
  categorias (id PK, nome)                       -> 5 registros
  filmes     (id PK, titulo, ano, categoria_id FK) -> 10 registros
  locacoes   (id PK, filme_id FK, cliente, data_locacao, devolvido) -> 10 registros

RELACIONAMENTOS: categorias 1---N filmes 1---N locacoes
"""
from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)
BANCO = "locadora.db"


# ==========================================================
# CONEXÃO
# ==========================================================
def conectar():
    conexao = sqlite3.connect(BANCO)
    conexao.row_factory = sqlite3.Row            # acessar colunas pelo nome
    conexao.execute("PRAGMA foreign_keys = ON")  # ativa FOREIGN KEY no SQLite
    return conexao


# ==========================================================
# CRIAÇÃO DAS TABELAS + DADOS DE TESTE
# ==========================================================
def criar_tabelas():
    conexao = conectar()

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL
        )
    """)

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS filmes (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo       TEXT NOT NULL,
            ano          INTEGER NOT NULL,
            categoria_id INTEGER NOT NULL,
            FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        )
    """)

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS locacoes (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            filme_id     INTEGER NOT NULL,
            cliente      TEXT NOT NULL,
            data_locacao TEXT NOT NULL,
            devolvido    INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (filme_id) REFERENCES filmes(id)
        )
    """)

    conexao.commit()
    conexao.close()


def popular_banco():
    """Insere os dados de teste só se o banco estiver vazio."""
    conexao = conectar()

    if conexao.execute("SELECT COUNT(*) FROM categorias").fetchone()[0] > 0:
        conexao.close()
        return

    categorias = ["Ação", "Comédia", "Drama", "Ficção Científica", "Terror"]
    conexao.executemany("INSERT INTO categorias (nome) VALUES (?)",
                        [(c,) for c in categorias])

    filmes = [
        ("Mad Max: Estrada da Fúria", 2015, 1),
        ("John Wick", 2014, 1),
        ("Superbad", 2007, 2),
        ("Se Beber, Não Case", 2009, 2),
        ("Cidade de Deus", 2002, 3),
        ("Central do Brasil", 1998, 3),
        ("Interestelar", 2014, 4),
        ("Matrix", 1999, 4),
        ("O Iluminado", 1980, 5),
        ("Corra!", 2017, 5),
    ]
    conexao.executemany(
        "INSERT INTO filmes (titulo, ano, categoria_id) VALUES (?, ?, ?)", filmes)

    locacoes = [
        (1, "Ana Souza",     "2026-10-01", 1),
        (2, "Bruno Lima",    "2026-10-02", 1),
        (3, "Carla Dias",    "2026-10-03", 1),
        (4, "Daniel Alves",  "2026-10-05", 0),
        (5, "Eduarda Rocha", "2026-10-06", 1),
        (7, "Felipe Costa",  "2026-10-08", 0),
        (8, "Gabriela Melo", "2026-10-09", 1),
        (9, "Henrique Reis", "2026-10-10", 0),
        (10, "Isabela Cruz", "2026-10-12", 1),
        (2, "Joana Pires",   "2026-10-15", 0),
    ]
    conexao.executemany(
        "INSERT INTO locacoes (filme_id, cliente, data_locacao, devolvido) "
        "VALUES (?, ?, ?, ?)", locacoes)

    conexao.commit()
    conexao.close()


# ==========================================================
# ROTA INICIAL
# ==========================================================
@app.route("/", methods=["GET"])
def inicio():
    return jsonify({
        "mensagem": "API da Locadora de Filmes",
        "versao": "1.0",
        "recursos": ["categorias", "filmes", "locacoes"]
    })


# ==========================================================
# ===================== CATEGORIAS (CRUD) ==================
# ==========================================================
@app.route("/categorias", methods=["POST"])
def cadastrar_categoria():
    dados = request.get_json()

    if not dados or not dados.get("nome"):
        return jsonify({"erro": "Informe o campo 'nome'."}), 400

    conexao = conectar()
    cursor = conexao.execute("INSERT INTO categorias (nome) VALUES (?)",
                             (dados["nome"],))
    conexao.commit()
    id_categoria = cursor.lastrowid
    conexao.close()

    return jsonify({
        "mensagem": "Categoria cadastrada com sucesso!",
        "categoria": {"id": id_categoria, "nome": dados["nome"]}
    }), 201


@app.route("/categorias", methods=["GET"])
def listar_categorias():
    conexao = conectar()
    categorias = conexao.execute(
        "SELECT * FROM categorias ORDER BY id").fetchall()
    conexao.close()
    return jsonify([dict(c) for c in categorias])


@app.route("/categorias/<int:id>", methods=["GET"])
def buscar_categoria(id):
    conexao = conectar()
    categoria = conexao.execute(
        "SELECT * FROM categorias WHERE id = ?", (id,)).fetchone()
    conexao.close()

    if categoria is None:
        return jsonify({"erro": "Categoria não encontrada!"}), 404
    return jsonify(dict(categoria))


@app.route("/categorias/<int:id>", methods=["PUT"])
def atualizar_categoria(id):
    dados = request.get_json()

    if not dados or not dados.get("nome"):
        return jsonify({"erro": "Informe o campo 'nome'."}), 400

    conexao = conectar()
    resultado = conexao.execute(
        "UPDATE categorias SET nome = ? WHERE id = ?", (dados["nome"], id))
    conexao.commit()
    conexao.close()

    if resultado.rowcount == 0:
        return jsonify({"erro": "Categoria não encontrada!"}), 404
    return jsonify({"mensagem": "Categoria atualizada com sucesso!"})


@app.route("/categorias/<int:id>", methods=["DELETE"])
def excluir_categoria(id):
    conexao = conectar()
    try:
        resultado = conexao.execute(
            "DELETE FROM categorias WHERE id = ?", (id,))
        conexao.commit()
    except sqlite3.IntegrityError:
        # Existem filmes usando essa categoria (FOREIGN KEY impede)
        conexao.close()
        return jsonify({
            "erro": "Não é possível excluir: há filmes nesta categoria."
        }), 409
    conexao.close()

    if resultado.rowcount == 0:
        return jsonify({"erro": "Categoria não encontrada!"}), 404
    return jsonify({"mensagem": "Categoria excluída com sucesso!"})


# ==========================================================
# ======================= FILMES (CRUD) ====================
# ==========================================================
@app.route("/filmes", methods=["POST"])
def cadastrar_filme():
    dados = request.get_json()

    if not dados or not all(k in dados for k in ("titulo", "ano", "categoria_id")):
        return jsonify({"erro": "Envie titulo, ano e categoria_id."}), 400

    conexao = conectar()

    categoria = conexao.execute(
        "SELECT id FROM categorias WHERE id = ?",
        (dados["categoria_id"],)).fetchone()
    if categoria is None:
        conexao.close()
        return jsonify({"erro": "Categoria não encontrada!"}), 404

    cursor = conexao.execute(
        "INSERT INTO filmes (titulo, ano, categoria_id) VALUES (?, ?, ?)",
        (dados["titulo"], dados["ano"], dados["categoria_id"]))
    conexao.commit()
    id_filme = cursor.lastrowid
    conexao.close()

    return jsonify({
        "mensagem": "Filme cadastrado com sucesso!",
        "filme": {"id": id_filme, **dados}
    }), 201


# GET /filmes                      -> todos (com JOIN para trazer a categoria)
# GET /filmes?categoria=Ação       -> QUERY STRING: filtra por categoria
# GET /filmes?ano=2014             -> QUERY STRING: filtra por ano
@app.route("/filmes", methods=["GET"])
def listar_filmes():
    categoria = request.args.get("categoria")
    ano = request.args.get("ano")

    sql = """
        SELECT filmes.id, filmes.titulo, filmes.ano,
               categorias.nome AS categoria
        FROM filmes
        JOIN categorias ON filmes.categoria_id = categorias.id
        WHERE 1 = 1
    """
    parametros = []

    if categoria:
        sql += " AND categorias.nome = ?"
        parametros.append(categoria)
    if ano:
        sql += " AND filmes.ano = ?"
        parametros.append(ano)

    sql += " ORDER BY filmes.id"

    conexao = conectar()
    filmes = conexao.execute(sql, parametros).fetchall()
    conexao.close()
    return jsonify([dict(f) for f in filmes])


# ----------------------------------------------------------
# DESAFIO DE CRIATIVIDADE
# GET /filmes/disponiveis -> filmes que NÃO estão alugados no momento
# (sem nenhuma locação com devolvido = 0)
# IMPORTANTE: esta rota fica ANTES de /filmes/<int:id> por clareza;
# como o <int:id> só aceita números, "disponiveis" não conflita.
# ----------------------------------------------------------
@app.route("/filmes/disponiveis", methods=["GET"])
def filmes_disponiveis():
    conexao = conectar()
    filmes = conexao.execute("""
        SELECT filmes.id, filmes.titulo, filmes.ano,
               categorias.nome AS categoria
        FROM filmes
        JOIN categorias ON filmes.categoria_id = categorias.id
        WHERE filmes.id NOT IN (
            SELECT filme_id FROM locacoes WHERE devolvido = 0
        )
        ORDER BY filmes.id
    """).fetchall()
    conexao.close()
    return jsonify([dict(f) for f in filmes])


@app.route("/filmes/<int:id>", methods=["GET"])
def buscar_filme(id):
    conexao = conectar()
    filme = conexao.execute("""
        SELECT filmes.id, filmes.titulo, filmes.ano,
               categorias.nome AS categoria
        FROM filmes
        JOIN categorias ON filmes.categoria_id = categorias.id
        WHERE filmes.id = ?
    """, (id,)).fetchone()
    conexao.close()

    if filme is None:
        return jsonify({"erro": "Filme não encontrado!"}), 404
    return jsonify(dict(filme))


@app.route("/filmes/<int:id>", methods=["PUT"])
def atualizar_filme(id):
    dados = request.get_json()

    if not dados or not all(k in dados for k in ("titulo", "ano", "categoria_id")):
        return jsonify({"erro": "Envie titulo, ano e categoria_id."}), 400

    conexao = conectar()

    categoria = conexao.execute(
        "SELECT id FROM categorias WHERE id = ?",
        (dados["categoria_id"],)).fetchone()
    if categoria is None:
        conexao.close()
        return jsonify({"erro": "Categoria não encontrada!"}), 404

    resultado = conexao.execute(
        "UPDATE filmes SET titulo = ?, ano = ?, categoria_id = ? WHERE id = ?",
        (dados["titulo"], dados["ano"], dados["categoria_id"], id))
    conexao.commit()
    conexao.close()

    if resultado.rowcount == 0:
        return jsonify({"erro": "Filme não encontrado!"}), 404
    return jsonify({"mensagem": "Filme atualizado com sucesso!"})


@app.route("/filmes/<int:id>", methods=["DELETE"])
def excluir_filme(id):
    conexao = conectar()
    try:
        resultado = conexao.execute("DELETE FROM filmes WHERE id = ?", (id,))
        conexao.commit()
    except sqlite3.IntegrityError:
        conexao.close()
        return jsonify({
            "erro": "Não é possível excluir: o filme possui locações."
        }), 409
    conexao.close()

    if resultado.rowcount == 0:
        return jsonify({"erro": "Filme não encontrado!"}), 404
    return jsonify({"mensagem": "Filme excluído com sucesso!"})


# ==========================================================
# ====================== LOCAÇÕES ==========================
# ==========================================================
@app.route("/locacoes", methods=["POST"])
def cadastrar_locacao():
    dados = request.get_json()

    if not dados or not all(k in dados for k in ("filme_id", "cliente", "data_locacao")):
        return jsonify({"erro": "Envie filme_id, cliente e data_locacao."}), 400

    conexao = conectar()

    filme = conexao.execute(
        "SELECT id FROM filmes WHERE id = ?", (dados["filme_id"],)).fetchone()
    if filme is None:
        conexao.close()
        return jsonify({"erro": "Filme não encontrado!"}), 404

    # Regra de negócio: não alugar um filme que já está alugado
    em_aberto = conexao.execute(
        "SELECT id FROM locacoes WHERE filme_id = ? AND devolvido = 0",
        (dados["filme_id"],)).fetchone()
    if em_aberto:
        conexao.close()
        return jsonify({"erro": "Filme já está alugado no momento."}), 409

    cursor = conexao.execute(
        "INSERT INTO locacoes (filme_id, cliente, data_locacao) VALUES (?, ?, ?)",
        (dados["filme_id"], dados["cliente"], dados["data_locacao"]))
    conexao.commit()
    id_locacao = cursor.lastrowid
    conexao.close()

    return jsonify({
        "mensagem": "Locação registrada com sucesso!",
        "locacao": {"id": id_locacao, **dados, "devolvido": 0}
    }), 201


# GET /locacoes                     -> todas, com JOIN no filme
# GET /locacoes?cliente=Ana Souza   -> QUERY STRING
@app.route("/locacoes", methods=["GET"])
def listar_locacoes():
    cliente = request.args.get("cliente")

    sql = """
        SELECT locacoes.id, filmes.titulo AS filme, locacoes.cliente,
               locacoes.data_locacao, locacoes.devolvido
        FROM locacoes
        JOIN filmes ON locacoes.filme_id = filmes.id
    """
    parametros = []
    if cliente:
        sql += " WHERE locacoes.cliente = ?"
        parametros.append(cliente)
    sql += " ORDER BY locacoes.id"

    conexao = conectar()
    locacoes = conexao.execute(sql, parametros).fetchall()
    conexao.close()
    return jsonify([dict(l) for l in locacoes])


@app.route("/locacoes/<int:id>", methods=["GET"])
def buscar_locacao(id):
    conexao = conectar()
    locacao = conexao.execute("""
        SELECT locacoes.id, filmes.titulo AS filme, locacoes.cliente,
               locacoes.data_locacao, locacoes.devolvido
        FROM locacoes
        JOIN filmes ON locacoes.filme_id = filmes.id
        WHERE locacoes.id = ?
    """, (id,)).fetchone()
    conexao.close()

    if locacao is None:
        return jsonify({"erro": "Locação não encontrada!"}), 404
    return jsonify(dict(locacao))


# Marca a locação como devolvida (o filme volta a ficar disponível)
@app.route("/locacoes/<int:id>/devolver", methods=["PUT"])
def devolver_locacao(id):
    conexao = conectar()
    resultado = conexao.execute(
        "UPDATE locacoes SET devolvido = 1 WHERE id = ?", (id,))
    conexao.commit()
    conexao.close()

    if resultado.rowcount == 0:
        return jsonify({"erro": "Locação não encontrada!"}), 404
    return jsonify({"mensagem": "Devolução registrada com sucesso!"})


@app.route("/locacoes/<int:id>", methods=["DELETE"])
def excluir_locacao(id):
    conexao = conectar()
    resultado = conexao.execute("DELETE FROM locacoes WHERE id = ?", (id,))
    conexao.commit()
    conexao.close()

    if resultado.rowcount == 0:
        return jsonify({"erro": "Locação não encontrada!"}), 404
    return jsonify({"mensagem": "Locação excluída com sucesso!"})


# ==========================================================
# INICIAR
# ==========================================================
if __name__ == "__main__":
    criar_tabelas()
    popular_banco()
    app.run(debug=True)
