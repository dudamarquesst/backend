from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/cadastro", methods=["POST"])
def cadastro():

    dados = request.get_json()

    return jsonify({
        "mensagem": "Cadastro realizado",
        "dados": dados
    })

if __name__ == "__main__":
    app.run(debug=True)