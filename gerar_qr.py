
import qrcode
import os

dados = "ALUNO-001"

imagem = qrcode.make(dados)

# Criar a pasta se ela ainda não existir
os.makedirs("static/img", exist_ok=True)

# Salvar o QR Code na pasta desejada
imagem.save("static/img/qr_aluno.png")

print("QR Code salvo em static/img/qr_aluno.png")

#a cada 6 horas / disponivel por 30