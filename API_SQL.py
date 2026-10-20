from flask import Flask, jsonify, request
import sqlite3

# Cria a aplicação Flask
app = Flask(__name__)


# ==========================================
# CONEXÃO COM O BANCO DE DADOS
# ==========================================
def conectar_banco():
    # Abre (ou cria, se não existir) o arquivo biblioteca.db
    conexao = sqlite3.connect("biblioteca.db")

    # Faz cada linha do SELECT se comportar como dicionário:
    # permite dict(linha), necessário para o jsonify
    conexao.row_factory = sqlite3.Row

    return conexao


# ==========================================
# CRIAÇÃO DA TABELA
# ==========================================
def criar_tabela():
    conexao = conectar_banco()

    # IF NOT EXISTS: só cria se a tabela ainda não existir
    # PRIMARY KEY AUTOINCREMENT: o banco gera o id sozinho (1, 2, 3...)
    # NOT NULL: o campo é obrigatório
    conexao.execute("""
        CREATE TABLE IF NOT EXISTS livros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            autor TEXT NOT NULL
        )
    """)

    # commit() grava a mudança; close() libera a conexão
    conexao.commit()
    conexao.close()


# ==========================================
# ROTA INICIAL
# ==========================================
# Só confirma que a API está no ar
@app.route("/", methods=["GET"])
def inicio():
    return jsonify({
        "mensagem": "API da Biblioteca",
        "versao": "1.0"
    })


# ==========================================
# CREATE - CADASTRAR LIVRO
# POST /livros   Body: {"titulo": "...", "autor": "..."}
# (o id não precisa ser enviado: o banco gera)
# ==========================================
@app.route("/livros", methods=["POST"])
def cadastrar_livro():
    # Lê o JSON enviado no corpo da requisição
    dados = request.get_json()

    # ATENÇÃO: se faltar um campo, dá KeyError e a API responde 500
    titulo = dados["titulo"]
    autor = dados["autor"]

    conexao = conectar_banco()

    # Os "?" são parâmetros: o SQLite troca pelos valores da tupla.
    # Isso protege contra SQL Injection (nunca concatene strings no SQL).
    cursor = conexao.execute(
        """
        INSERT INTO livros (titulo, autor)
        VALUES (?, ?)
        """,
        (titulo, autor)
    )

    conexao.commit()

    # id que o banco gerou para o registro recém-criado
    id_livro = cursor.lastrowid

    conexao.close()

    # 201 = Created (criado com sucesso)
    return jsonify({
        "mensagem": "Livro cadastrado com sucesso!",
        "id": id_livro,
        "titulo": titulo,
        "autor": autor
    }), 201


# ==========================================
# READ - LISTAR TODOS OS LIVROS
# GET /livros
# ==========================================
@app.route("/livros", methods=["GET"])
def listar_livros():
    conexao = conectar_banco()

    # fetchall() devolve TODAS as linhas do resultado
    livros = conexao.execute(
        "SELECT * FROM livros"
    ).fetchall()

    conexao.close()

    # Converte cada linha (sqlite3.Row) em dict para virar JSON
    return jsonify([
        dict(livro)
        for livro in livros
    ])


# ==========================================
# READ - BUSCAR LIVRO POR ID
# GET /livros/1   (<int:id> captura o número da URL)
# ==========================================
@app.route("/livros/<int:id>", methods=["GET"])
def buscar_livro(id):
    conexao = conectar_banco()

    # fetchone() devolve UMA linha, ou None se não achar nada
    livro = conexao.execute(
        "SELECT * FROM livros WHERE id = ?",
        (id,)   # (id,) com vírgula: é uma tupla de 1 item
    ).fetchone()

    conexao.close()

    # Não achou -> 404 (Not Found)
    if livro is None:
        return jsonify({
            "erro": "Livro não encontrado!"
        }), 404

    return jsonify(dict(livro))


# ==========================================
# UPDATE - ATUALIZAR LIVRO
# PUT /livros/1   Body: {"titulo": "...", "autor": "..."}
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

    # rowcount = quantas linhas foram alteradas.
    # 0 significa que nenhum livro tem esse id -> 404
    if resultado.rowcount == 0:
        return jsonify({
            "erro": "Livro não encontrado!"
        }), 404

    return jsonify({
        "mensagem": "Livro atualizado com sucesso!"
    })


# ==========================================
# DELETE - EXCLUIR LIVRO
# DELETE /livros/1
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

    # Mesma lógica do UPDATE: rowcount 0 = id não existe
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
# Só executa quando o arquivo é rodado direto (python API_SQL.py)
if __name__ == "__main__":
    criar_tabela()         # garante que a tabela existe
    app.run(debug=True)    # sobe em http://127.0.0.1:5000
                           # debug=True: reinicia ao salvar e mostra erros
