from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    telefone = db.Column(db.String(20))
    endereco = db.Column(db.String(200))
    cidade = db.Column(db.String(100))
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

    pedidos = db.relationship('Pedido', backref='cliente', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'telefone': self.telefone,
            'endereco': self.endereco,
            'cidade': self.cidade
        }


class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    categoria = db.Column(db.String(100))
    preco_venda = db.Column(db.Float, nullable=False)
    custo_producao = db.Column(db.Float, nullable=False)
    tempo_producao = db.Column(db.Integer)
    ativo = db.Column(db.Boolean, default=True)

    def lucro(self):
        return self.preco_venda - self.custo_producao

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'categoria': self.categoria,
            'preco_venda': self.preco_venda,
            'custo_producao': self.custo_producao,
            'ativo': self.ativo
        }


class Ingrediente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    unidade = db.Column(db.String(20))
    preco_unitario = db.Column(db.Float)

    estoque = db.relationship('Estoque', backref='ingrediente', uselist=False)

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'unidade': self.unidade,
            'preco_unitario': self.preco_unitario
        }


class Estoque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ingrediente_id = db.Column(db.Integer, db.ForeignKey('ingrediente.id'))
    quantidade = db.Column(db.Float, default=0)
    quantidade_minima = db.Column(db.Float, default=0)
    quantidade_alerta = db.Column(db.Float, default=0)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def status(self):
        if self.quantidade <= self.quantidade_minima:
            return 'Baixo'
        elif self.quantidade <= self.quantidade_alerta:
            return 'Atenção'
        return 'OK'

    def to_dict(self):
        return {
            'id': self.id,
            'ingrediente': self.ingrediente.nome if self.ingrediente else '',
            'quantidade': self.quantidade,
            'status': self.status()
        }


class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'))
    status = db.Column(db.String(30), default='em_andamento')
    observacoes = db.Column(db.Text)
    desconto = db.Column(db.Float, default=0)
    data_pedido = db.Column(db.DateTime, default=datetime.utcnow)
    data_entrega = db.Column(db.DateTime)

    itens = db.relationship(
        'ItemPedido',
        backref='pedido',
        lazy=True,
        cascade='all, delete-orphan'
    )

    def total(self):
        total = sum(item.subtotal() for item in self.itens)
        return total - self.desconto

    def lucro(self):
        return sum(item.lucro() for item in self.itens)

    def to_dict(self):
        return {
            'id': self.id,
            'cliente': self.cliente.nome if self.cliente else '',
            'status': self.status,
            'total': self.total()
        }


class ItemPedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'))
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'))
    quantidade = db.Column(db.Integer)
    preco_unitario = db.Column(db.Float)

    produto = db.relationship('Produto')

    def subtotal(self):
        return self.quantidade * self.preco_unitario

    def lucro(self):
        if self.produto:
            return (self.produto.preco_venda - self.produto.custo_producao) * self.quantidade
        return 0


class Configuracao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(100), unique=True)
    valor = db.Column(db.String(255))

    @staticmethod
    def get(chave, default=None):
        config = Configuracao.query.filter_by(chave=chave).first()
        return config.valor if config else default

    @staticmethod
    def set(chave, valor):
        config = Configuracao.query.filter_by(chave=chave).first()
        if not config:
            config = Configuracao(chave=chave, valor=str(valor))
            db.session.add(config)
        else:
            config.valor = str(valor)
        db.session.commit()