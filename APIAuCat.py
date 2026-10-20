from flask import Flask, jsonify, request
import sqlite3

# Cria a aplicação Flask. __name__ diz ao Flask onde está o projeto.
app = Flask(__name__)


# ==========================================================
# CONEXÃO COM O BANCO DE DADOS
# ==========================================================
def conectar_banco():
    # Abre (ou cria, se não existir) o arquivo do banco SQLite
    conexao = sqlite3.connect("biblioteca2.db")

    # Faz cada linha do SELECT se comportar como um dicionário:
    # permite linha["nome"] e dict(linha) -> necessário para o jsonify
    conexao.row_factory = sqlite3.Row

    # No SQLite as chaves estrangeiras vêm DESLIGADAS por padrão.
    # Sem isso, ele aceitaria um livro com autor_id inexistente.
    conexao.execute("PRAGMA foreign_keys = ON")

    return conexao


# ==========================================================
# CRIAÇÃO DAS TABELAS
# ==========================================================
def criar_tabelas():
    conexao = conectar_banco()

    # ------------------------------------------------------
    # TABELA AUTORES (lado "1" da relação: um autor...)
    # ------------------------------------------------------
    conexao.execute("""
CREATE TABLE IF NOT EXISTS autores (
id INTEGER PRIMARY KEY AUTOINCREMENT,
nome TEXT NOT NULL,
nacionalidade TEXT NOT NULL
)
""")

    # ------------------------------------------------------
    # TABELA LIVROS (lado "N": ...tem vários livros)
    # autor_id é a FOREIGN KEY: aponta para autores.id
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

    # commit() grava as mudanças; close() libera a conexão
    conexao.commit()
    conexao.close()


# ==========================================================
# ROTA INICIAL
# ==========================================================
# Só confirma que a API está no ar
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
# POST /autores   Body: {"nome": "...", "nacionalidade": "..."}
# ----------------------------------------------------------
@app.route("/autores", methods=["POST"])
def cadastrar_autor():
    # Lê o JSON enviado no corpo da requisição
    dados = request.get_json()

    # ATENÇÃO: se faltar um campo, dá KeyError e a API responde 500
    nome = dados["nome"]
    nacionalidade = dados["nacionalidade"]

    conexao = conectar_banco()

    # Os "?" são parâmetros: o SQLite troca pelos valores da tupla.
    # Isso protege contra SQL Injection (nunca concatene strings no SQL).
    cursor = conexao.execute("""
INSERT INTO autores
(nome, nacionalidade)
VALUES (?, ?)
""", (
        nome,
        nacionalidade
))

    conexao.commit()

    # id que o banco gerou para o registro recém-criado
    id_autor = cursor.lastrowid
    conexao.close()

    # 201 = Created (criado com sucesso)
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
# GET /autores
# ----------------------------------------------------------
@app.route("/autores", methods=["GET"])
def listar_autores():
    conexao = conectar_banco()

    # fetchall() devolve TODAS as linhas do resultado
    autores = conexao.execute("""
SELECT *
FROM autores
ORDER BY id
""").fetchall()

    conexao.close()

    # Converte cada linha (sqlite3.Row) em dict para virar JSON
    return jsonify([
        dict(autor)
        for autor in autores
])


# ----------------------------------------------------------
# READ - BUSCAR AUTOR POR ID
# GET /autores/1   (<int:id> captura o número da URL)
# ----------------------------------------------------------
@app.route("/autores/<int:id>", methods=["GET"])
def buscar_autor(id):
    conexao = conectar_banco()

    # fetchone() devolve UMA linha, ou None se não achar nada
    autor = conexao.execute("""
SELECT *
FROM autores
WHERE id = ?
""", (id,)).fetchone()   # (id,) com vírgula: é uma tupla de 1 item

    conexao.close()

    # Não achou -> 404 (Not Found)
    if autor is None:
        return jsonify({
            "erro": "Autor não encontrado!"
}), 404

    return jsonify(dict(autor))


# ----------------------------------------------------------
# UPDATE - ATUALIZAR AUTOR
# PUT /autores/1   Body: {"nome": "...", "nacionalidade": "..."}
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

    # rowcount = quantas linhas foram alteradas.
    # 0 significa que nenhum autor tem esse id -> 404
    if resultado.rowcount == 0:
        return jsonify({
            "erro": "Autor não encontrado!"
}), 404

    return jsonify({
        "mensagem": "Autor atualizado com sucesso!"
})


# ----------------------------------------------------------
# DELETE - EXCLUIR AUTOR
# DELETE /autores/1
# ATENÇÃO: se o autor tiver livros, a FOREIGN KEY bloqueia o
# DELETE (IntegrityError) e a API responde 500. Exclua os livros antes.
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

    # Mesma lógica do UPDATE: rowcount 0 = id não existe
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
# POST /livros   Body: {"titulo": "...", "ano": 1899, "autor_id": 1}
# O autor precisa existir antes de cadastrar o livro.
# ----------------------------------------------------------
@app.route("/livros", methods=["POST"])
def cadastrar_livro():
    dados = request.get_json()

    titulo = dados["titulo"]
    ano = dados["ano"]
    autor_id = dados["autor_id"]

    conexao = conectar_banco()

    # Verifica se o autor existe (regra de integridade feita na API)
    autor = conexao.execute("""
SELECT id
FROM autores
WHERE id = ?
""", (autor_id,)).fetchone()

    # Se não existe, fecha a conexão e responde 404 sem inserir nada
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
# GET /livros
# JOIN: junta as duas tabelas pela chave estrangeira, assim cada
# livro já vem com o nome e a nacionalidade do autor.
# "AS autor" renomeia a coluna autores.nome no resultado.
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
# GET /livros/1   (mesmo JOIN, filtrando por um livro)
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
# PUT /livros/1   Body: {"titulo": "...", "ano": 1900, "autor_id": 1}
# ----------------------------------------------------------
@app.route("/livros/<int:id>", methods=["PUT"])
def atualizar_livro(id):
    dados = request.get_json()

    titulo = dados["titulo"]
    ano = dados["ano"]
    autor_id = dados["autor_id"]

    conexao = conectar_banco()

    # Confere se o NOVO autor_id existe antes de atualizar
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

    # rowcount 0 = não existe livro com esse id
    if resultado.rowcount == 0:
        return jsonify({
            "erro": "Livro não encontrado!"
}), 404

    return jsonify({
        "mensagem": "Livro atualizado com sucesso!"
})


# ----------------------------------------------------------
# DELETE - EXCLUIR LIVRO
# DELETE /livros/1
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
# Só executa quando o arquivo é rodado direto (python APIAuCat.py)
if __name__ == "__main__":
    criar_tabelas()        # garante que as tabelas existem
    app.run(debug=True)    # sobe o servidor em http://127.0.0.1:5000
                           # debug=True: reinicia ao salvar e mostra erros
