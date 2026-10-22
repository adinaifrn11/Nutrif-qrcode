from flask import Flask, render_template, jsonify, request, redirect, url_for
import qrcode
import os
from datetime import datetime

from models import db, Aluno, Acesso, TentativaAcesso

app = Flask(__name__)

# Configuração do banco
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///nutrif.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# Pasta dos QR Codes
os.makedirs("static/img", exist_ok=True)


# Criar tabelas + aluno de teste
with app.app_context():
    db.create_all()

    aluno = Aluno.query.filter_by(matricula="ALUNO-001").first()
    if aluno is None:
        aluno = Aluno(
            matricula="ALUNO-001",
            nome="Aluno de Teste",
            email="aluno.teste@example.com",
            curso="Informática para Internet"
        )
        db.session.add(aluno)
        db.session.commit()

    # Gera o QR Code com o token individual
    print("=================================")
    print("TOKEN DO ALUNO:", aluno.token_qr)
    print("=================================")


# ====================== ROTAS DAS PÁGINAS ======================

@app.route("/")
def inicio():
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    aluno = Aluno.query.filter_by(matricula="ALUNO-001").first()
    return render_template("dashboard.html", aluno=aluno)


@app.route("/perfil")
def perfil():
    aluno = Aluno.query.filter_by(matricula="ALUNO-001").first()
    return render_template("perfil.html", aluno=aluno)


@app.route("/qr")
def mostrar_qr():
    aluno = Aluno.query.filter_by(matricula="ALUNO-001").first()
    if aluno is None:
        return "Aluno não encontrado.", 404
    return render_template("qr_code_aluno.html", aluno=aluno)


@app.route("/historico")
def historico():
    aluno = Aluno.query.filter_by(matricula="ALUNO-001").first()
    acessos = []
    if aluno:
        acessos = Acesso.query.filter_by(aluno_id=aluno.id)\
                              .order_by(Acesso.data_hora.desc()).all()
    return render_template("historico.html", aluno=aluno, acessos=acessos)


@app.route("/validacao")
def validacao():
    return render_template("validacao.html")


@app.route("/validacao-concluida")
def validacao_concluida():
    # Dados vindos da validação (podem ser passados por query string ou session)
    periodo = request.args.get("periodo", "manha")
    data = request.args.get("data", datetime.now().strftime("%d/%m/%Y"))
    hora = request.args.get("hora", datetime.now().strftime("%H:%M"))
    aluno_nome = request.args.get("aluno", "Aluno")

    nomes_periodo = {
        "manha": "Lanche da manhã",
        "tarde": "Lanche da tarde",
        "noite": "Lanche da noite"
    }

    return render_template(
        "validacaoconcluida.html",
        periodo_nome=nomes_periodo.get(periodo, periodo),
        data=data,
        hora=hora,
        aluno_nome=aluno_nome
    )


@app.route("/validacao-erro")
def validacao_erro():
    motivo = request.args.get("motivo", "Acesso negado")
    return render_template("validacaoerro.html", motivo=motivo)


# ====================== API DE VALIDAÇÃO ======================

@app.route("/api/validar", methods=["POST"])
def validar_qr():
    dados = request.get_json()

    if not dados:
        return jsonify({"resultado": "negado", "motivo": "Dados inválidos"}), 400

    token_qr = dados.get("token_qr")
    periodo = dados.get("periodo", "").lower().strip()

    if not token_qr or not periodo:
        return jsonify({"resultado": "negado", "motivo": "Token ou período não informado"}), 400

    if periodo not in ["manha", "tarde", "noite"]:
        return jsonify({"resultado": "negado", "motivo": "Período inválido"}), 400

    aluno = Aluno.query.filter_by(token_qr=token_qr).first()

    # QR Code inválido
    if aluno is None:
        tentativa = TentativaAcesso(
            aluno_id=None,
            periodo=periodo,
            resultado="negado",
            motivo="QR Code inválido"
        )
        db.session.add(tentativa)
        db.session.commit()
        return jsonify({"resultado": "negado", "motivo": "QR Code inválido"})

    # Aluno inativo
    if not aluno.ativo:
        tentativa = TentativaAcesso(
            aluno_id=aluno.id,
            periodo=periodo,
            resultado="negado",
            motivo="Aluno inativo"
        )
        db.session.add(tentativa)
        db.session.commit()
        return jsonify({
            "resultado": "negado",
            "motivo": "Aluno inativo",
            "aluno": aluno.nome
        })

    hoje = datetime.now().strftime("%Y-%m-%d")

    # Já utilizou neste período hoje?
    acesso_existente = Acesso.query.filter_by(
        aluno_id=aluno.id,
        data=hoje,
        periodo=periodo
    ).first()

    if acesso_existente:
        tentativa = TentativaAcesso(
            aluno_id=aluno.id,
            periodo=periodo,
            resultado="negado",
            motivo="Refeição já utilizada neste período"
        )
        db.session.add(tentativa)
        db.session.commit()
        return jsonify({
            "resultado": "negado",
            "motivo": "Refeição já utilizada neste período",
            "aluno": aluno.nome
        })

    # Autoriza o acesso
    novo_acesso = Acesso(
        aluno_id=aluno.id,
        periodo=periodo,
        data=hoje,
        data_hora=datetime.now()
    )
    db.session.add(novo_acesso)

    tentativa = TentativaAcesso(
        aluno_id=aluno.id,
        periodo=periodo,
        resultado="autorizado",
        motivo="Acesso liberado"
    )
    db.session.add(tentativa)
    db.session.commit()

    return jsonify({
        "resultado": "autorizado",
        "aluno": aluno.nome,
        "matricula": aluno.matricula,
        "periodo": periodo,
        "data": datetime.now().strftime("%d/%m/%Y"),
        "hora": datetime.now().strftime("%H:%M"),
        "mensagem": f"Acesso autorizado para {aluno.nome}"
    })


# ====================== API DE HISTÓRICO ======================

@app.route("/api/historico/<matricula>")
def api_historico(matricula):
    aluno = Aluno.query.filter_by(matricula=matricula).first()
    if not aluno:
        return jsonify({"erro": "Aluno não encontrado"}), 404

    acessos = Acesso.query.filter_by(aluno_id=aluno.id)\
                          .order_by(Acesso.data_hora.desc()).all()

    lista = []
    for a in acessos:
        lista.append({
            "periodo": a.periodo,
            "data": a.data,
            "data_hora": a.data_hora.strftime("%d/%m/%Y %H:%M:%S")
        })

    return jsonify({
        "aluno": aluno.nome,
        "matricula": aluno.matricula,
        "acessos": lista
    })


if __name__ == "__main__":
    app.run(debug=True)