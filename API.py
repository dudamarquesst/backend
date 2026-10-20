from flask import Flask, jsonify, request

# Cria a aplicação Flask
app = Flask(__name__)

# ==========================================================
# "Banco de dados" em memória: uma lista de dicionários.
# Simples, mas os dados SOMEM sempre que o servidor reinicia.
# (A versão API_SQL.py resolve isso usando SQLite.)
# ==========================================================
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


# ==========================================================
# Página inicial: só confirma que a API está no ar
# ==========================================================
@app.route("/")
def inicio():
    return jsonify({
        "mensagem": "API Biblioteca",
        "versao": "1.0"
    })


# ==========================================================
# READ - Listar todos os livros
# GET /livros
# ==========================================================
@app.route("/livros", methods=["GET"])
def listar_livros():
    # jsonify converte a lista de dicionários em JSON
    return jsonify(livros)


# ==========================================================
# READ - Buscar livro por ID
# GET /livros/1   (<int:id> captura o número da URL)
# ==========================================================
@app.route("/livros/<int:id>", methods=["GET"])
def buscar_livro(id):
    # Percorre a lista procurando o livro com esse id
    for livro in livros:
        if livro["id"] == id:
            return jsonify(livro)

    # Se saiu do for sem retornar, não achou -> 404 (Not Found)
    return jsonify({
        "erro": "Livro não encontrado."
    }), 404


# ==========================================================
# CREATE - Cadastrar livro
# POST /livros   Body: {"id": 3, "titulo": "...", "autor": "..."}
# ==========================================================
@app.route("/livros", methods=["POST"])
def cadastrar_livro():
    # Lê o JSON enviado no corpo da requisição
    dados = request.get_json()

    # ATENÇÃO: não valida nada e não gera o id sozinho.
    # Quem chama precisa mandar o "id", e ids repetidos são aceitos.
    livros.append(dados)

    # 201 = Created (criado com sucesso)
    return jsonify({
        "mensagem": "Livro cadastrado com sucesso!",
        "livro": dados
    }), 201


# ==========================================================
# UPDATE - Atualizar livro
# PUT /livros/1   Body: {"titulo": "...", "autor": "..."}
# ==========================================================
@app.route("/livros/<int:id>", methods=["PUT"])
def atualizar_livro(id):
    dados = request.get_json()

    for livro in livros:
        if livro["id"] == id:
            # Altera os campos do dicionário que já está na lista
            # (se faltar "titulo" ou "autor" no JSON, dá erro 500)
            livro["titulo"] = dados["titulo"]
            livro["autor"] = dados["autor"]

            return jsonify({
                "mensagem": "Livro atualizado com sucesso!",
                "livro": livro
            })

    # Não achou o id
    return jsonify({
        "erro": "Livro não encontrado."
    }), 404


# ==========================================================
# DELETE - Excluir livro
# DELETE /livros/1
# ==========================================================
@app.route("/livros/<int:id>", methods=["DELETE"])
def excluir_livro(id):
    for livro in livros:
        if livro["id"] == id:
            # Remove o livro da lista.
            # Pode remover dentro do for porque retorna logo em seguida.
            livros.remove(livro)

            return jsonify({
                "mensagem": "Livro removido com sucesso!"
            })

    return jsonify({
        "erro": "Livro não encontrado."
    }), 404


# ==========================================================
# Inicialização do servidor
# ==========================================================
# Só executa quando o arquivo é rodado direto (python API.py)
if __name__ == "__main__":
    # Sobe em http://127.0.0.1:5000
    # debug=True: reinicia ao salvar o arquivo e mostra erros detalhados
    app.run(debug=True)







"""
THUNDER CLIENT - (APIAuCat.py)

PREPARAÇÃO
  python -m venv venv
  venv\Scripts\activate
  pip install flask
  python APIAuCat.py
  Servidor: http://127.0.0.1:5000 (deixar o terminal aberto)

Em todos: New Request > escolher o método > colar a URL > Send.
Nos POST e PUT: aba Body > JSON e colar o JSON.

1. ROTA INICIAL
   GET http://127.0.0.1:5000/
   Esperado: 200, "mensagem": "API da Biblioteca" e a lista de recursos

2. CRIAR AUTOR
   POST http://127.0.0.1:5000/autores
   Body: {"nome": "Machado de Assis", "nacionalidade": "Brasileira"}
   Esperado: 201, com o autor e o id gerado (1)

3. CRIAR SEGUNDO AUTOR
   POST http://127.0.0.1:5000/autores
   Body: {"nome": "George Orwell", "nacionalidade": "Britânica"}
   Esperado: 201, id 2

4. LISTAR AUTORES
   GET http://127.0.0.1:5000/autores
   Esperado: 200, lista com os dois autores

5. BUSCAR AUTOR POR ID
   GET http://127.0.0.1:5000/autores/1
   Esperado: 200, só o Machado

6. CRIAR LIVRO
   POST http://127.0.0.1:5000/livros
   Body: {"titulo": "Dom Casmurro", "ano": 1899, "autor_id": 1}
   Esperado: 201
   (criar outro com "autor_id": 2, ex.: 1984, ano 1949)

7. LISTAR LIVROS
   GET http://127.0.0.1:5000/livros
   Esperado: 200, cada livro com "autor" e "nacionalidade" (JOIN)

8. BUSCAR LIVRO POR ID
   GET http://127.0.0.1:5000/livros/1
   Esperado: 200

9. ATUALIZAR LIVRO
   PUT http://127.0.0.1:5000/livros/1
   Body: {"titulo": "Dom Casmurro", "ano": 1900, "autor_id": 1}
   Esperado: 200 (conferir com o GET do passo 8)

10. ATUALIZAR AUTOR
    PUT http://127.0.0.1:5000/autores/1
    Body: {"nome": "Machado de Assis", "nacionalidade": "Brasileiro"}
    Esperado: 200

TESTES DE ERRO
  GET    /livros/999                          -> 404
  GET    /autores/999                         -> 404
  POST   /livros com "autor_id": 999          -> 404 "Autor não encontrado!"
  PUT    /livros/999                          -> 404
  POST   /autores com {"nome": "Fulano"}      -> 500 (KeyError, campo faltando)
  DELETE /autores/1 (autor com livro)         -> 500 (IntegrityError)

EXCLUSÃO
  DELETE http://127.0.0.1:5000/livros/1       -> 200
  Depois: DELETE /autores/1 -> 200 (agora o autor não tem livros)
  Na ordem inversa dá erro.

SE ALGO FALHAR
  - Sem resposta: o servidor não está rodando (ver o terminal)
  - 500 em POST/PUT: Body fora de JSON ou aspas simples no JSON
  - Codespaces: se 127.0.0.1 não abrir, usar a URL da aba Ports (porta 5000)
  - Dados estranhos: apagar o biblioteca2.db e rodar de novo
"""