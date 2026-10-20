from flask import Flask, jsonify, request

app = Flask(__name__)

# "Banco" simples só para o Requisito 1 ter o que consultar
LIVROS = {
    "Dom Casmurro": "Machado de Assis",
    "1984": "George Orwell",
}


# ==========================================================
# REQUISITO 1 - GET /livro/<titulo>   (parâmetro de rota)
# Ex.: http://127.0.0.1:5000/livro/Dom%20Casmurro
# O Flask decodifica o %20 sozinho: titulo = "Dom Casmurro"
# ==========================================================
@app.route("/livro/<titulo>", methods=["GET"])
def consultar_livro(titulo):
    autor = LIVROS.get(titulo)

    # Se o livro não estiver na lista, ainda assim responde
    # (o enunciado só mostra o caso de sucesso), mas com 404 é mais correto
    if autor is None:
        return jsonify({"erro": "Livro não encontrado!"}), 404

    return jsonify({
        "titulo": titulo,
        "autor": autor
    })


# ==========================================================
# REQUISITO 2 - GET /autor?nome=...   (Query String)
# Ex.: http://127.0.0.1:5000/autor?nome=Machado%20de%20Assis
# ==========================================================
@app.route("/autor", methods=["GET"])
def consultar_autor():
    nome = request.args.get("nome")

    if not nome:
        return jsonify({"erro": "Informe o parâmetro 'nome'."}), 400

    return jsonify({"autor": nome})


# ==========================================================
# REQUISITO 3 - POST /livro   (corpo JSON)
# Body: {"titulo": "...", "autor": "...", "ano": 1899}
# ==========================================================
@app.route("/livro", methods=["POST"])
def cadastrar_livro():
    dados = request.get_json()

    if not dados or not all(k in dados for k in ("titulo", "autor", "ano")):
        return jsonify({"erro": "Envie titulo, autor e ano."}), 400

    return jsonify({
        "mensagem": "Livro cadastrado com sucesso!",
        "livro": dados
    }), 201


if __name__ == "__main__":
    app.run(debug=True)
