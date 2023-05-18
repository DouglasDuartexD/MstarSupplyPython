import os
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import (
    Case,
    When,
    Sum,
    Value,
    IntegerField,
    F,
    Subquery,
    OuterRef,
    CharField,
)
from django.db.models.functions import Concat, Cast
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Image,
    Spacer,
    Paragraph,
)
from reportlab.lib.styles import getSampleStyleSheet
from .models import Produto, Movimentacao
from .forms import ProdutoForm, MovimentacaoForm

# ---- Inicio Home page ----


def index(request):
    # Busca as movimentações que não estrous deletadas, ordenado pela data
    movimentacoes = Movimentacao.objects.filter(deletado=False).order_by("data_hora")

    # Obtem a contagem de movimentações de entradas e saidas
    contagem_total_entradas = Movimentacao.objects.filter(
        deletado=False, tipo_movimentacao=True
    ).count()
    contagem_total_saidas = Movimentacao.objects.filter(
        deletado=False, tipo_movimentacao=False
    ).count()

    # Recupera os valores das movimentações de entradas e saidas baseadas no nome do produto,
    # somando as quantidades em um novo campo chamado total_quantidade
    entradas_por_produto_total = (
        Movimentacao.objects.filter(deletado=False, tipo_movimentacao=True)
        .values("produto__nome")
        .annotate(total_quantidade=Sum("quantidade"))
    )
    saidas_por_produto_total = (
        Movimentacao.objects.filter(deletado=False, tipo_movimentacao=False)
        .values("produto__nome")
        .annotate(total_quantidade=Sum("quantidade"))
    )

    # Inicia a contagem de produtos por entradas ou saidas para calcular a media de entrada e saida dos produtos
    contagem_produtos_entradas = {}
    for entrada in entradas_por_produto_total:
        produto = entrada['produto__nome']
        total_quantidade = entrada['total_quantidade']
        contagem_produtos_entradas[produto] = Movimentacao.objects.filter(
            deletado=False, tipo_movimentacao=True, produto__nome=produto
        ).count()

    medias_entradas = {}
    for entrada in entradas_por_produto_total:
        produto = entrada['produto__nome']
        total_quantidade = entrada['total_quantidade']
        media_entradas = round(total_quantidade / contagem_produtos_entradas[produto], 0)
        medias_entradas[produto] = media_entradas

    contagem_produtos_saidas = {}
    for saida in saidas_por_produto_total:
        produto = saida['produto__nome']
        total_quantidade = saida['total_quantidade']
        contagem_produtos_saidas[produto] = Movimentacao.objects.filter(
            deletado=False, tipo_movimentacao=False, produto__nome=produto
        ).count() or 0

    medias_saidas = {}
    for saida in saidas_por_produto_total:
        produto = saida['produto__nome']
        total_quantidade = saida['total_quantidade']
        media_saidas = round(total_quantidade / contagem_produtos_saidas[produto], 0)
        medias_saidas[produto] = media_saidas

    entradas_e_saidas_mes = {}
    for movimentacao in movimentacoes:
        data = movimentacao.data_hora.strftime("%m/%Y")
        if data not in entradas_e_saidas_mes:
            entradas_e_saidas_mes[data] = {"entradas": 0, "saidas": 0}
        if movimentacao.tipo_movimentacao:
            entradas_e_saidas_mes[data]["entradas"] += movimentacao.quantidade
        else:
            entradas_e_saidas_mes[data]["saidas"] += movimentacao.quantidade
        entradas_e_saidas_mes[data]["nome_produto"] = movimentacao.produto.nome

    # Cria as categorias disponíveis no dicionário para o gráfico Entradas x Saidas
    categorias_mes_ano = list(entradas_e_saidas_mes.keys())

    # Atrela os dados de entrada e saida do dicionário a suas variaveis para possibilitar a renderização
    entradas_mes_ano = [
        entradas_e_saidas_mes[categoria]["entradas"] for categoria in categorias_mes_ano
    ]
    saidas_mes_ano = [
        entradas_e_saidas_mes[categoria]["saidas"] for categoria in categorias_mes_ano
    ]

    # Soma os totais para exibição do total de entrada e saida.
    total_entradas = sum(entradas_mes_ano)
    total_saidas = sum(saidas_mes_ano)

    # Calcula o estoque total
    total_estoque = total_entradas - total_saidas

    return render(
        request,
        "home/index.html",
        {
            "categorias_mes_ano": categorias_mes_ano,
            "entradas_mes_ano": entradas_mes_ano,
            "saidas_mes_ano": saidas_mes_ano,
            "total_entradas": total_entradas,
            "total_saidas": total_saidas,
            "total_estoque": total_estoque,
            "contagem_total_entradas": contagem_total_entradas,
            "contagem_total_saidas": contagem_total_saidas,
            "entradas_por_produto_total": entradas_por_produto_total,
            "saidas_por_produto_total": saidas_por_produto_total,
            "medias_entradas": medias_entradas,
            "medias_saidas": medias_saidas,
        },
    )

# ---- Fim Home Page ----


# ---- Inicio Produtos ----
def index_produto(request):
    # Busca todos os objetos do modelo Produto que não estão deletados
    produtos = Produto.objects.filter(deletado=False)

    # Renderiza a template 'produto/index.html' com a lista de produtos
    return render(request, "produto/index.html", {"produtos": produtos})


def stock_produto(request):
    # Recupera os valores dos as movimentações de entradas e saidas baseadas no nome do produto.
    saidas_por_produto = (
        Movimentacao.objects.filter(deletado=False, tipo_movimentacao=False)
        .values("produto__nome", "produto__pk")
        .annotate(total_quantidade=Sum("quantidade"))
    )

    # Recupera os valores das entradas, em seguida cria 3 novos campos, total_entradas, total_saidas e estoque.
    entradas_por_produto = (
        Movimentacao.objects.filter(deletado=False, tipo_movimentacao=True)
        .values("produto__nome", "produto__ativo", "produto__pk")
        .annotate(total_entradas=Sum("quantidade"))
        .annotate(
            total_saidas=Subquery(
                saidas_por_produto.filter(produto__pk=OuterRef("produto__pk")).values(
                    "total_quantidade"
                )[:1]
            )
        )
        .annotate(
            estoque=Case(
                When(total_saidas__isnull=True, then=F("total_entradas")),
                default=F("total_entradas") - F("total_saidas"),
                output_field=IntegerField(),
            )
        )
    )

    return render(
        request,
        "produto/stock.html",
        {
            "entradas_por_produto": entradas_por_produto,
            "saidas_por_produto": saidas_por_produto,
        },
    )


def create_produto(request):
    # Verifica se o request é um metodo POST, se for POST irá executar as alterações do form
    if request.method == "POST":
        form = ProdutoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Produto cadastrado com sucesso.")
            return redirect("produto")
    else:
        form = ProdutoForm(initial={"ativo": "True"})

    return render(request, "produto/create.html", {"form": form})


def edit_produto(request, pk):
    # Guarda o Id do produto em uma tempdata para utiliza-lo na sessão da atual view
    produto = get_object_or_404(Produto, pk=pk)
    request.session["tempdata"] = pk

    # Verifica se o request é um metodo POST, se for POST irá executar as alterações do form
    # caso contrário retornará a tela do form com os dados preenchidos
    if request.method == "POST":
        form = ProdutoForm(request.POST, instance=produto)
        if form.is_valid():
            form.save()
            messages.success(request, "Produto editado com sucesso.")
            return redirect("produto")
    else:
        form = ProdutoForm(instance=produto)

    return render(request, "produto/edit.html", {"form": form, "produto.pk": pk})


def delete_produto(request, pk):
    # Recupera o id para atualização do campo deletado do banco para true
    # assim o dado será deletado de forma recuperável
    produto = get_object_or_404(Produto, id=pk)
    produto.deletado = True
    produto.save()
    messages.success(request, "Produto deletado com sucesso.")

    return HttpResponseRedirect(reverse("produto"))

# ---- Fim Produtos ----


# ---- Inicio Movimentações ----

def index_movimentacao(request):
    # Busca todos os objetos do modelo Produto que não estão deletados
    movimentacoes = Movimentacao.objects.filter(deletado=False).annotate(
        id_busca_grid=Concat(Value("#"), Cast(F("pk"), output_field=CharField()))
    )

    return render(request, "movimentacao/index.html", {"movimentacoes": movimentacoes})


def create_movimentacao(request):

    # Verifica se o request é um metodo POST, se for POST irá executar as alterações do form
    # caso contrário retornará a tela do form com os dados preenchidos
    if request.method == "POST":
        form = MovimentacaoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Movimentação cadastrado com sucesso.")

            return redirect("movimentacao")
    else:
        form = MovimentacaoForm()

    return render(request, "movimentacao/create.html", {"form": form})


def edit_movimentacao(request, pk):
    # Guarda o Id do produto em uma tempdata para utiliza-lo na sessão da atual view
    movimentacao = get_object_or_404(Movimentacao, pk=pk)
    request.session["tempdata"] = pk

    # Verifica se o request é um metodo POST, se for POST irá executar as alterações do form
    # caso contrário retornará a tela do form com os dados preenchidos
    if request.method == "POST":
        form = MovimentacaoForm(request.POST, instance=movimentacao)
        if form.is_valid():
            form.save()
            messages.success(request, "Movimentação editado com sucesso.")

            return redirect("movimentacao")
    else:
        form = MovimentacaoForm(instance=movimentacao)

    return render(
        request,
        "movimentacao/edit.html",
        {"form": form, "tempdata": request.session.get("tempdata")},
    )


def delete_movimentacao(request, pk):
    movimentacao = get_object_or_404(Movimentacao, id=pk)
    movimentacao.deletado = True
    movimentacao.save()
    messages.success(request, "Movimentacao deletada com sucesso.")

    return HttpResponseRedirect(reverse("movimentacao"))
# ---- Fim Movimentações ----


# ---- Inicio Relatórios ----
def export_pdf_movimentacao(request):

    # Cria a resposta HTTP com o tipo de conteúdo do PDF
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="movimentações_mensal.pdf"'

    # Define as configurações do PDF
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []

    # Obtem o caminho absoluto da pasta static
    caminho_static = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static"
    )

    # Constrói o caminho absoluto da imagem
    caminho_imagem = os.path.join(caminho_static, "img", "pdf-logo-min.png")

    # Cria um objeto Image com o caminho absoluto da imagem
    imagem = Image(caminho_imagem)
    imagem.drawHeight = 125
    imagem.drawWidth = 300

    # Cria o estilo para o título
    styles = getSampleStyleSheet()
    title_style = styles["Title"]

    # Cria a estrutura de layout usando uma tabela
    tabela = Table([[imagem]])
    tabela.setStyle([("VALIGN", (1, 3), (0, 0), "MIDDLE")])

    # Adiciona a tabela aos elementos do documento
    elements.append(tabela)

    # Adiciona uma linha em branco
    elements.append(Spacer(1, 12))

    # Adiciona o texto "Total de movimentações"
    elements.append(Paragraph("<u><b>Total de movimentações</b></u>", title_style))

    # Adiciona uma linha em branco
    elements.append(Spacer(1, 12))

    # Obtém as movimentações
    movimentacoes = Movimentacao.objects.filter(deletado=False).order_by("data_hora")

    # Cria a estrutura de tabela
    conteudo_grid = [["Mês/Ano", "Entradas", "Saídas"]]

    # Preenche a tabela com os dados das movimentações
    entradas_e_saidas = {}
    for movimentacao in movimentacoes:
        data_mes_ano = movimentacao.data_hora.strftime("%m/%Y")
        if data_mes_ano not in entradas_e_saidas:
            entradas_e_saidas[data_mes_ano] = {"entradas": 0, "saidas": 0}
        if movimentacao.tipo_movimentacao:
            entradas_e_saidas[data_mes_ano]["entradas"] += movimentacao.quantidade
        else:
            entradas_e_saidas[data_mes_ano]["saidas"] += movimentacao.quantidade

    for data_mes_ano, valores in entradas_e_saidas.items():
        entradas = valores["entradas"]
        saidas = valores["saidas"]
        conteudo_grid.append([data_mes_ano, entradas, saidas])

    # Define o estilo da tabela
    table_style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.gray),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]
    )

    # Cria a tabela com os dados
    table = Table(conteudo_grid)
    table.setStyle(table_style)

    # Aplica o estilo para os itens de movimentação individualmente
    for i in range(1, len(conteudo_grid)):
        for j in range(len(conteudo_grid[i])):
            if j != 0:  # Ignorar a primeira coluna (mes/ano)
                valor = conteudo_grid[i][j]
                if j == 1 and valor > 0:  # Entrada (pintar de verde)
                    item_style = ("TEXTCOLOR", (j, i), (j, i), colors.green)
                elif j == 2 and valor > 0:  # Saída (pintar de vermelho)
                    item_style = ("TEXTCOLOR", (j, i), (j, i), colors.red)
                else:  # Zero ou mês/ano (manter a cor padrão)
                    item_style = ("TEXTCOLOR", (j, i), (j, i), colors.black)
                table.setStyle(TableStyle([item_style]))

    # Adiciona a tabela aos elementos do documento
    elements.append(table)

    # Gera o PDF
    doc.build(elements)

    return response
