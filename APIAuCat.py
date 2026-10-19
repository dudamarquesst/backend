from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)


# ==========================================================
# CONEXÃO COM O BANCO DE DADOS
# ==========================================================

def conectar_banco():
    conexao = sqlite3.connect("biblioteca2.db")

    # Permite acessar as colunas pelo nome
    conexao.row_factory = sqlite3.Row

    # Ativa o uso de chaves estrangeiras no SQLite
    conexao.execute("PRAGMA foreign_keys = ON")

    return conexao


# ==========================================================
# CRIAÇÃO DAS TABELAS
# ==========================================================

def criar_tabelas():

    conexao = conectar_banco()

    # ------------------------------------------------------
    # TABELA AUTORES
    # ------------------------------------------------------

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS autores (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nome TEXT NOT NULL,

            nacionalidade TEXT NOT NULL
        )
    """)

    # ------------------------------------------------------
    # TABELA LIVROS
    # ------------------------------------------------------

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS livros (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            titulo TEXT NOT NULL,

            ano INTEGER NOT NULL,

            autor_id INTEGER NOT NULL,

            FOREIGN KEY (autor_id)
                REFERENCES autores(id)
        )
    """)

    conexao.commit()

    conexao.close()


# ==========================================================
# ROTA INICIAL
# ==========================================================

@app.route("/", methods=["GET"])
def inicio():

    return jsonify({
        "mensagem": "API da Biblioteca",
        "versao": "2.0",
        "recursos": [
            "Autores",
            "Livros"
        ]
    })


# ==========================================================
# ======================= AUTORES ==========================
# ==========================================================


# ----------------------------------------------------------
# CREATE - CADASTRAR AUTOR
# ----------------------------------------------------------

@app.route("/autores", methods=["POST"])
def cadastrar_autor():

    dados = request.get_json()

    nome = dados["nome"]

    nacionalidade = dados["nacionalidade"]

    conexao = conectar_banco()

    cursor = conexao.execute("""
        INSERT INTO autores
        (nome, nacionalidade)

        VALUES (?, ?)
    """, (
        nome,
        nacionalidade
    ))

    conexao.commit()

    id_autor = cursor.lastrowid

    conexao.close()

    return jsonify({

        "mensagem": "Autor cadastrado com sucesso!",

        "autor": {
            "id": id_autor,
            "nome": nome,
            "nacionalidade": nacionalidade
        }

    }), 201


# ----------------------------------------------------------
# READ - LISTAR AUTORES
# ----------------------------------------------------------

@app.route("/autores", methods=["GET"])
def listar_autores():

    conexao = conectar_banco()

    autores = conexao.execute("""
        SELECT *
        FROM autores
        ORDER BY id
    """).fetchall()

    conexao.close()

    return jsonify([
        dict(autor)
        for autor in autores
    ])


# ----------------------------------------------------------
# READ - BUSCAR AUTOR POR ID
# ----------------------------------------------------------

@app.route("/autores/<int:id>", methods=["GET"])
def buscar_autor(id):

    conexao = conectar_banco()

    autor = conexao.execute("""
        SELECT *
        FROM autores

        WHERE id = ?
    """, (id,)).fetchone()

    conexao.close()

    if autor is None:

        return jsonify({
            "erro": "Autor não encontrado!"
        }), 404

    return jsonify(dict(autor))


# ----------------------------------------------------------
# UPDATE - ATUALIZAR AUTOR
# ----------------------------------------------------------

@app.route("/autores/<int:id>", methods=["PUT"])
def atualizar_autor(id):

    dados = request.get_json()

    nome = dados["nome"]

    nacionalidade = dados["nacionalidade"]

    conexao = conectar_banco()

    resultado = conexao.execute("""
        UPDATE autores

        SET
            nome = ?,
            nacionalidade = ?

        WHERE id = ?
    """, (
        nome,
        nacionalidade,
        id
    ))

    conexao.commit()

    conexao.close()

    if resultado.rowcount == 0:

        return jsonify({
            "erro": "Autor não encontrado!"
        }), 404

    return jsonify({

        "mensagem": "Autor atualizado com sucesso!"

    })


# ----------------------------------------------------------
# DELETE - EXCLUIR AUTOR
# ----------------------------------------------------------

@app.route("/autores/<int:id>", methods=["DELETE"])
def excluir_autor(id):

    conexao = conectar_banco()

    resultado = conexao.execute("""
        DELETE FROM autores

        WHERE id = ?
    """, (id,))

    conexao.commit()

    conexao.close()

    if resultado.rowcount == 0:

        return jsonify({
            "erro": "Autor não encontrado!"
        }), 404

    return jsonify({

        "mensagem": "Autor excluído com sucesso!"

    })


# ==========================================================
# ======================== LIVROS ==========================
# ==========================================================


# ----------------------------------------------------------
# CREATE - CADASTRAR LIVRO
# ----------------------------------------------------------

@app.route("/livros", methods=["POST"])
def cadastrar_livro():

    dados = request.get_json()

    titulo = dados["titulo"]

    ano = dados["ano"]

    autor_id = dados["autor_id"]

    conexao = conectar_banco()

    # Verifica se o autor existe

    autor = conexao.execute("""
        SELECT id
        FROM autores

        WHERE id = ?
    """, (autor_id,)).fetchone()

    if autor is None:

        conexao.close()

        return jsonify({

            "erro": "Autor não encontrado!"

        }), 404

    # Insere o livro

    cursor = conexao.execute("""
        INSERT INTO livros
        (titulo, ano, autor_id)

        VALUES (?, ?, ?)
    """, (
        titulo,
        ano,
        autor_id
    ))

    conexao.commit()

    id_livro = cursor.lastrowid

    conexao.close()

    return jsonify({

        "mensagem": "Livro cadastrado com sucesso!",

        "livro": {
            "id": id_livro,
            "titulo": titulo,
            "ano": ano,
            "autor_id": autor_id
        }

    }), 201


# ----------------------------------------------------------
# READ - LISTAR LIVROS COM AUTOR
# ----------------------------------------------------------

@app.route("/livros", methods=["GET"])
def listar_livros():

    conexao = conectar_banco()

    livros = conexao.execute("""
        SELECT

            livros.id,

            livros.titulo,

            livros.ano,

            autores.nome AS autor,

            autores.nacionalidade

        FROM livros

        JOIN autores

        ON livros.autor_id = autores.id

        ORDER BY livros.id
    """).fetchall()

    conexao.close()

    return jsonify([
        dict(livro)
        for livro in livros
    ])


# ----------------------------------------------------------
# READ - BUSCAR LIVRO POR ID
# ----------------------------------------------------------

@app.route("/livros/<int:id>", methods=["GET"])
def buscar_livro(id):

    conexao = conectar_banco()

    livro = conexao.execute("""
        SELECT

            livros.id,

            livros.titulo,

            livros.ano,

            autores.nome AS autor,

            autores.nacionalidade

        FROM livros

        JOIN autores

        ON livros.autor_id = autores.id

        WHERE livros.id = ?
    """, (id,)).fetchone()

    conexao.close()

    if livro is None:

        return jsonify({

            "erro": "Livro não encontrado!"

        }), 404

    return jsonify(dict(livro))


# ----------------------------------------------------------
# UPDATE - ATUALIZAR LIVRO
# ----------------------------------------------------------

@app.route("/livros/<int:id>", methods=["PUT"])
def atualizar_livro(id):

    dados = request.get_json()

    titulo = dados["titulo"]

    ano = dados["ano"]

    autor_id = dados["autor_id"]

    conexao = conectar_banco()

    # Verifica se o autor existe

    autor = conexao.execute("""
        SELECT id
        FROM autores

        WHERE id = ?
    """, (autor_id,)).fetchone()

    if autor is None:

        conexao.close()

        return jsonify({

            "erro": "Autor não encontrado!"

        }), 404

    # Atualiza o livro

    resultado = conexao.execute("""
        UPDATE livros

        SET

            titulo = ?,

            ano = ?,

            autor_id = ?

        WHERE id = ?
    """, (
        titulo,
        ano,
        autor_id,
        id
    ))

    conexao.commit()

    conexao.close()

    if resultado.rowcount == 0:

        return jsonify({

            "erro": "Livro não encontrado!"

        }), 404

    return jsonify({

        "mensagem": "Livro atualizado com sucesso!"

    })


# ----------------------------------------------------------
# DELETE - EXCLUIR LIVRO
# ----------------------------------------------------------

@app.route("/livros/<int:id>", methods=["DELETE"])
def excluir_livro(id):

    conexao = conectar_banco()

    resultado = conexao.execute("""
        DELETE FROM livros

        WHERE id = ?
    """, (id,))

    conexao.commit()

    conexao.close()

    if resultado.rowcount == 0:

        return jsonify({

            "erro": "Livro não encontrado!"

        }), 404

    return jsonify({

        "mensagem": "Livro excluído com sucesso!"

    })


# ==========================================================
# INICIAR A APLICAÇÃO
# ==========================================================

if __name__ == "__main__":

    criar_tabelas()

    app.run(debug=True)