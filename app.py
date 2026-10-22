
from flask import Flask, render_template
import qrcode
import os

app = Flask(__name__)

# Criar a pasta para guardar o QR Code
os.makedirs("static/img", exist_ok=True)

# Gerar o QR Code
dados = "ALUNO-001"
imagem = qrcode.make(dados)

# Salvar o QR Code
imagem.save("static/img/qr_aluno.png")


# Página inicial
@app.route("/")
def inicio():
    return render_template("login.html")

@app.route("/perfil")
def perfil():
    return render_template("perfil.html")    


# Página do QR Code
@app.route("/qr")
def mostrar_qr():
    return render_template("qr_code_aluno.html")


if __name__ == "__main__":
    app.run(debug=True)

