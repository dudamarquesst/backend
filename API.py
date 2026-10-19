from flask import Flask, jsonify, request

app = Flask(__name__)

# Banco de dados em memória
livros = [
    {
        "id": 1,
        "titulo": "Dom Casmurro",
        "autor": "Machado de Assis"
    },
    {
        "id": 2,
        "titulo": "1984",
        "autor": "George Orwell"
    }
]

# Página inicial
@app.route("/")
def inicio():
    return jsonify({
        "mensagem": "API Biblioteca",
        "versao": "1.0"
    })

# ==========================
# READ - Listar todos os livros
# ==========================
@app.route("/livros", methods=["GET"])
def listar_livros():
    return jsonify(livros)


# ==========================
# READ - Buscar livro por ID
# ==========================
@app.route("/livros/<int:id>", methods=["GET"])
def buscar_livro(id):

    for livro in livros:
        if livro["id"] == id:
            return jsonify(livro)

    return jsonify({
        "erro": "Livro não encontrado."
    }), 404


# ==========================
# CREATE - Cadastrar livro
# ==========================
@app.route("/livros", methods=["POST"])
def cadastrar_livro():

    dados = request.get_json()

    livros.append(dados)

    return jsonify({
        "mensagem": "Livro cadastrado com sucesso!",
        "livro": dados
    }), 201


# ==========================
# UPDATE - Atualizar livro
# ==========================
@app.route("/livros/<int:id>", methods=["PUT"])
def atualizar_livro(id):

    dados = request.get_json()

    for livro in livros:

        if livro["id"] == id:

            livro["titulo"] = dados["titulo"]
            livro["autor"] = dados["autor"]

            return jsonify({
                "mensagem": "Livro atualizado com sucesso!",
                "livro": livro
            })

    return jsonify({
        "erro": "Livro não encontrado."
    }), 404


# ==========================
# DELETE - Excluir livro
# ==========================
@app.route("/livros/<int:id>", methods=["DELETE"])
def excluir_livro(id):

    for livro in livros:

        if livro["id"] == id:

            livros.remove(livro)

            return jsonify({
                "mensagem": "Livro removido com sucesso!"
            })

    return jsonify({
        "erro": "Livro não encontrado."
    }), 404


# ==========================
# Inicialização do servidor
# ==========================
if __name__ == "__main__":
    app.run(debug=True)