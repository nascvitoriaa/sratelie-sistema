from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from models import db, Cliente, Produto, Ingrediente, Estoque, Pedido, ItemPedido
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sratelie-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sratelie.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')

        if usuario == 'admin' and senha == 'admin123':
            session['logged_in'] = True
            return redirect(url_for('dashboard'))

        flash('Usuário ou senha incorretos')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Logout realizado com sucesso!')
    return redirect(url_for('login'))

@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template(
        'dashboard.html',
        total_clientes=Cliente.query.count(),
        total_produtos=Produto.query.count(),
        total_ingredientes=Ingrediente.query.count(),
        total_pedidos=Pedido.query.count()
    )


@app.route('/clientes')
@login_required
def clientes():
    return render_template('clientes.html', clientes=Cliente.query.order_by(Cliente.nome).all())


@app.route('/api/clientes', methods=['POST'])
@login_required
def criar_cliente():
    dados = request.json

    cliente = Cliente(
        nome=dados.get('nome'),
        email=dados.get('email'),
        telefone=dados.get('telefone'),
        endereco=dados.get('endereco'),
        cidade=dados.get('cidade')
    )

    db.session.add(cliente)
    db.session.commit()

    return jsonify(cliente.to_dict())


@app.route('/api/clientes/<int:id>', methods=['DELETE'])
@login_required
def deletar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/produtos')
@login_required
def produtos():
    return render_template('produtos.html', produtos=Produto.query.order_by(Produto.nome).all())


@app.route('/api/produtos', methods=['POST'])
@login_required
def criar_produto():
    dados = request.json

    produto = Produto(
        nome=dados.get('nome'),
        descricao=dados.get('descricao'),
        categoria=dados.get('categoria'),
        preco_venda=float(dados.get('preco_venda') or 0),
        custo_producao=float(dados.get('custo_producao') or 0),
        tempo_producao=int(dados.get('tempo_producao') or 0)
    )

    db.session.add(produto)
    db.session.commit()

    return jsonify(produto.to_dict())


@app.route('/ingredientes')
@login_required
def ingredientes():
    return render_template('ingredientes.html', ingredientes=Ingrediente.query.order_by(Ingrediente.nome).all())


@app.route('/api/ingredientes', methods=['POST'])
@login_required
def criar_ingrediente():
    dados = request.json

    ingrediente = Ingrediente(
        nome=dados.get('nome'),
        unidade=dados.get('unidade'),
        preco_unitario=float(dados.get('preco_unitario') or 0)
    )

    db.session.add(ingrediente)
    db.session.flush()

    estoque = Estoque(
        ingrediente_id=ingrediente.id,
        quantidade=float(dados.get('quantidade') or 0),
        quantidade_minima=float(dados.get('quantidade_minima') or 0),
        quantidade_alerta=float(dados.get('quantidade_alerta') or 0)
    )

    db.session.add(estoque)
    db.session.commit()

    return jsonify(ingrediente.to_dict())


@app.route('/estoque')
@login_required
def estoque():
    return render_template('estoque.html', itens=Estoque.query.all())


@app.route('/api/estoque/<int:id>', methods=['PUT'])
@login_required
def atualizar_estoque(id):
    item = Estoque.query.get_or_404(id)
    dados = request.json

    item.quantidade = float(dados.get('quantidade') or 0)

    db.session.commit()

    return jsonify({'ok': True})


@app.route('/pedidos')
@login_required
def pedidos():
    return render_template(
        'pedidos.html',
        pedidos=Pedido.query.order_by(Pedido.data_pedido.desc()).all(),
        clientes=Cliente.query.order_by(Cliente.nome).all(),
        produtos=Produto.query.order_by(Produto.nome).all()
    )


@app.route('/api/pedidos', methods=['POST'])
@login_required
def criar_pedido():
    dados = request.json

    produto = Produto.query.get(int(dados.get('produto_id')))
    quantidade = int(dados.get('quantidade') or 1)

    pedido = Pedido(
        cliente_id=int(dados.get('cliente_id')),
        status=dados.get('status'),
        desconto=0
    )

    db.session.add(pedido)
    db.session.flush()

    item = ItemPedido(
        pedido_id=pedido.id,
        produto_id=produto.id,
        quantidade=quantidade,
        preco_unitario=produto.preco_venda
    )

    db.session.add(item)
    db.session.commit()

    return jsonify({'ok': True})


@app.route('/relatorios')
@login_required
def relatorios():
    pedidos = Pedido.query.all()
    faturamento = sum(p.total() for p in pedidos)
    lucro = sum(p.lucro() for p in pedidos)

    return render_template(
        'relatorios.html',
        faturamento=faturamento,
        lucro=lucro,
        total_pedidos=len(pedidos)
    )


@app.route('/configuracoes')
@login_required
def configuracoes():
    return render_template('configuracoes.html')


def seed():
    if Cliente.query.count() > 0:
        return

    clientes = [
        Cliente(nome='Maria Silva', telefone='(11) 99999-1111', email='maria@email.com', cidade='São Paulo'),
        Cliente(nome='João Souza', telefone='(11) 98888-2222', email='joao@email.com', cidade='Guarulhos'),
        Cliente(nome='Ana Oliveira', telefone='(11) 97777-3333', email='ana@email.com', cidade='Osasco'),
        Cliente(nome='Carlos Lima', telefone='(11) 96666-4444', email='carlos@email.com', cidade='Santo André'),
        Cliente(nome='Juliana Costa', telefone='(11) 95555-5555', email='juliana@email.com', cidade='São Paulo'),
        Cliente(nome='Fernanda Rocha', telefone='(11) 94444-6666', email='fernanda@email.com', cidade='Diadema'),
        Cliente(nome='Lucas Martins', telefone='(11) 93333-7777', email='lucas@email.com', cidade='Mauá'),
        Cliente(nome='Patrícia Alves', telefone='(11) 92222-8888', email='patricia@email.com', cidade='Taboão'),
        Cliente(nome='Renata Gomes', telefone='(11) 91111-9999', email='renata@email.com', cidade='São Bernardo'),
        Cliente(nome='Mariana Lopes', telefone='(11) 90000-1010', email='mariana@email.com', cidade='São Paulo'),
        Cliente(nome='Beatriz Santos', telefone='(11) 98888-2020', email='beatriz@email.com', cidade='Osasco'),
        Cliente(nome='Rafael Pereira', telefone='(11) 97777-3030', email='rafael@email.com', cidade='Guarulhos'),
        Cliente(nome='Camila Nunes', telefone='(11) 96666-4040', email='camila@email.com', cidade='São Paulo'),
        Cliente(nome='Bruna Melo', telefone='(11) 95555-5050', email='bruna@email.com', cidade='Santo André'),
        Cliente(nome='Thiago Ramos', telefone='(11) 94444-6060', email='thiago@email.com', cidade='Diadema'),
    ]

    produtos = [
        Produto(nome='Brigadeiro Gourmet', categoria='Docinhos', preco_venda=3.50, custo_producao=1.40),
        Produto(nome='Beijinho', categoria='Docinhos', preco_venda=3.00, custo_producao=1.20),
        Produto(nome='Bolo de Chocolate', categoria='Bolos', preco_venda=55.00, custo_producao=32.00),
        Produto(nome='Bolo de Morango', categoria='Bolos', preco_venda=65.00, custo_producao=38.00),
        Produto(nome='Copo da Felicidade', categoria='Sobremesas', preco_venda=16.00, custo_producao=7.50),
        Produto(nome='Trufa de Chocolate', categoria='Docinhos', preco_venda=4.50, custo_producao=2.00),
        Produto(nome='Brownie Recheado', categoria='Sobremesas', preco_venda=8.00, custo_producao=3.80),
        Produto(nome='Mini Pudim', categoria='Sobremesas', preco_venda=10.00, custo_producao=4.50),
    ]

    ingredientes = [
        Ingrediente(nome='Leite Condensado', unidade='Unid.', preco_unitario=5.50),
        Ingrediente(nome='Chocolate em Pó', unidade='Kg', preco_unitario=25.00),
        Ingrediente(nome='Manteiga', unidade='Kg', preco_unitario=30.00),
        Ingrediente(nome='Morango', unidade='Kg', preco_unitario=18.00),
        Ingrediente(nome='Creme de Leite', unidade='Unid.', preco_unitario=4.50),
        Ingrediente(nome='Açúcar', unidade='Kg', preco_unitario=4.00),
        Ingrediente(nome='Farinha de Trigo', unidade='Kg', preco_unitario=5.00),
        Ingrediente(nome='Chocolate Granulado', unidade='Kg', preco_unitario=22.00),
        Ingrediente(nome='Leite em Pó', unidade='Kg', preco_unitario=28.00),
        Ingrediente(nome='Ovos', unidade='Dúzia', preco_unitario=12.00),
    ]

    db.session.add_all(clientes + produtos + ingredientes)
    db.session.commit()

    estoques = [
        Estoque(ingrediente_id=ingredientes[0].id, quantidade=12, quantidade_minima=3, quantidade_alerta=6),
        Estoque(ingrediente_id=ingredientes[1].id, quantidade=2, quantidade_minima=1, quantidade_alerta=3),
        Estoque(ingrediente_id=ingredientes[2].id, quantidade=1, quantidade_minima=1, quantidade_alerta=2),
        Estoque(ingrediente_id=ingredientes[3].id, quantidade=4, quantidade_minima=2, quantidade_alerta=5),
        Estoque(ingrediente_id=ingredientes[4].id, quantidade=10, quantidade_minima=3, quantidade_alerta=6),
        Estoque(ingrediente_id=ingredientes[5].id, quantidade=8, quantidade_minima=2, quantidade_alerta=4),
        Estoque(ingrediente_id=ingredientes[6].id, quantidade=9, quantidade_minima=2, quantidade_alerta=5),
        Estoque(ingrediente_id=ingredientes[7].id, quantidade=1, quantidade_minima=1, quantidade_alerta=3),
        Estoque(ingrediente_id=ingredientes[8].id, quantidade=5, quantidade_minima=2, quantidade_alerta=4),
        Estoque(ingrediente_id=ingredientes[9].id, quantidade=2, quantidade_minima=1, quantidade_alerta=3),
    ]

    db.session.add_all(estoques)
    db.session.commit()

    pedidos_dados = [
        (0, 0, 20, 'Concluído'),
        (1, 2, 1, 'Em preparo'),
        (2, 4, 3, 'Pendente'),
        (3, 6, 5, 'Concluído'),
        (4, 1, 25, 'Concluído'),
        (5, 3, 1, 'Em preparo'),
        (6, 5, 8, 'Pendente'),
        (7, 7, 2, 'Concluído'),
        (8, 0, 30, 'Concluído'),
        (9, 4, 4, 'Em preparo'),
        (10, 6, 6, 'Concluído'),
        (11, 2, 1, 'Pendente'),
        (12, 5, 10, 'Concluído'),
        (13, 1, 18, 'Concluído'),
        (14, 3, 1, 'Em preparo'),
    ]

    for cliente_i, produto_i, quantidade, status in pedidos_dados:
        pedido = Pedido(
            cliente_id=clientes[cliente_i].id,
            status=status,
            desconto=0
        )

        db.session.add(pedido)
        db.session.flush()

        item = ItemPedido(
            pedido_id=pedido.id,
            produto_id=produtos[produto_i].id,
            quantidade=quantidade,
            preco_unitario=produtos[produto_i].preco_venda
        )

        db.session.add(item)

    db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed()

    app.run(debug=True)