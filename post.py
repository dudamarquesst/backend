from flask import Flask, request, jsonify

# Cria a aplicação Flask
app = Flask(__name__)


# ==========================================================
# POST /cadastro
# Rota mínima para praticar o envio de um corpo JSON.
# Não usa banco: só devolve o que recebeu ("eco").
#
# methods=["POST"]: esta rota só aceita POST.
# Um GET em /cadastro retorna 405 (Method Not Allowed).
# ==========================================================
@app.route("/cadastro", methods=["POST"])
def cadastro():
    # Lê o JSON enviado no corpo da requisição.
    # No Thunder Client: aba Body > JSON. Sem isso, dados fica None.
    dados = request.get_json()

    # Devolve uma mensagem e os mesmos dados recebidos
    return jsonify({
        "mensagem": "Cadastro realizado",
        "dados": dados
    })


# Só executa quando o arquivo é rodado direto (python post.py)
if __name__ == "__main__":
    # Sobe em http://127.0.0.1:5000
    # debug=True: reinicia ao salvar e mostra erros detalhados
    app.run(debug=True)
