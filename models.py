from datetime import datetime
from uuid import uuid4
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint

db = SQLAlchemy()


class Aluno(db.Model):
    __tablename__ = "alunos"

    id = db.Column(db.Integer, primary_key=True)
    matricula = db.Column(db.String(30), unique=True, nullable=False)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True)
    curso = db.Column(db.String(100))
    token_qr = db.Column(
        db.String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid4())
    )
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    acessos = db.relationship("Acesso", backref="aluno", lazy=True)
    tentativas = db.relationship("TentativaAcesso", backref="aluno", lazy=True)


class Acesso(db.Model):
    __tablename__ = "acessos"

    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey("alunos.id"), nullable=False)
    periodo = db.Column(db.String(10), nullable=False)  # manha, tarde, noite
    data = db.Column(db.String(10), nullable=False)     # YYYY-MM-DD
    data_hora = db.Column(db.DateTime, default=datetime.now, nullable=False)
    funcionario_id = db.Column(db.Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "aluno_id", "data", "periodo",
            name="uq_acesso_aluno_data_periodo"
        ),
    )


class TentativaAcesso(db.Model):
    __tablename__ = "tentativas_acesso"

    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey("alunos.id"), nullable=True)
    periodo = db.Column(db.String(10), nullable=False)
    data_hora = db.Column(db.DateTime, default=datetime.now, nullable=False)
    resultado = db.Column(db.String(20), nullable=False)  # autorizado / negado
    motivo = db.Column(db.String(200))