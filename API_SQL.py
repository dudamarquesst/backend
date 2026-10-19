from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)

# ==========================================
# CONEXÃO COM O BANCO DE DADOS
# ==========================================

def conectar_banco():
    conexao = sqlite3.connect("biblioteca.db")
    conexao.row_factory = sqlite3.Row
    return conexao


# ==========================================
# CRIAÇÃO DA TABELA
# ==========================================

def criar_tabela():

    conexao = conectar_banco()

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS livros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            autor TEXT NOT NULL
        )
    """)

    conexao.commit()
    conexao.close()


# ==========================================
# ROTA INICIAL
# ==========================================

@app.route("/", methods=["GET"])
def inicio():

    return jsonify({
        "mensagem": "API da Biblioteca",
        "versao": "1.0"
    })


# ==========================================
# CREATE - CADASTRAR LIVRO
# ==========================================

@app.route("/livros", methods=["POST"])
def cadastrar_livro():

    dados = request.get_json()

    titulo = dados["titulo"]
    autor = dados["autor"]

    conexao = conectar_banco()

    cursor = conexao.execute(
        """
        INSERT INTO livros (titulo, autor)
        VALUES (?, ?)
        """,
        (titulo, autor)
    )

    conexao.commit()

    id_livro = cursor.lastrowid

    conexao.close()

    return jsonify({
        "mensagem": "Livro cadastrado com sucesso!",
        "id": id_livro,
        "titulo": titulo,
        "autor": autor
    }), 201


# ==========================================
# READ - LISTAR TODOS OS LIVROS
# ==========================================

@app.route("/livros", methods=["GET"])
def listar_livros():

    conexao = conectar_banco()

    livros = conexao.execute(
        "SELECT * FROM livros"
    ).fetchall()

    conexao.close()

    return jsonify([
        dict(livro)
        for livro in livros
    ])


# ==========================================
# READ - BUSCAR LIVRO POR ID
# ==========================================

@app.route("/livros/<int:id>", methods=["GET"])
def buscar_livro(id):

    conexao = conectar_banco()

    livro = conexao.execute(
        "SELECT * FROM livros WHERE id = ?",
        (id,)
    ).fetchone()

    conexao.close()

    if livro is None:

        return jsonify({
            "erro": "Livro não encontrado!"
        }), 404

    return jsonify(dict(livro))


# ==========================================
# UPDATE - ATUALIZAR LIVRO
# ==========================================

@app.route("/livros/<int:id>", methods=["PUT"])
def atualizar_livro(id):

    dados = request.get_json()

    titulo = dados["titulo"]
    autor = dados["autor"]

    conexao = conectar_banco()

    resultado = conexao.execute(
        """
        UPDATE livros
        SET titulo = ?, autor = ?
        WHERE id = ?
        """,
        (titulo, autor, id)
    )

    conexao.commit()

    conexao.close()

    if resultado.rowcount == 0:

        return jsonify({
            "erro": "Livro não encontrado!"
        }), 404

    return jsonify({
        "mensagem": "Livro atualizado com sucesso!"
    })


# ==========================================
# DELETE - EXCLUIR LIVRO
# ==========================================

@app.route("/livros/<int:id>", methods=["DELETE"])
def excluir_livro(id):

    conexao = conectar_banco()

    resultado = conexao.execute(
        "DELETE FROM livros WHERE id = ?",
        (id,)
    )

    conexao.commit()

    conexao.close()

    if resultado.rowcount == 0:

        return jsonify({
            "erro": "Livro não encontrado!"
        }), 404

    return jsonify({
        "mensagem": "Livro excluído com sucesso!"
    })


# ==========================================
# INICIAR SERVIDOR
# ==========================================

if __name__ == "__main__":

    criar_tabela()

    app.run(debug=True)