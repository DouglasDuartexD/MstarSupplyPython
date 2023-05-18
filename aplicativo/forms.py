from django import forms
from .models import Produto
from .models import Movimentacao
from django.forms import Select
from django.db.models import Q, Sum

# Gera o formulário para o cadastro de produtos
class ProdutoForm(forms.ModelForm):

    # Torna o campo descrição não obrigatório para o form control
    descricao = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}), required=False)

    def clean_nome(self):

        nome = self.cleaned_data['nome']

        # Verifica se o nome que está sendo cadastrado já existe no banco, caso exista verifica se não está deletado.
        # Excluindo a si mesmo desta busca para que possa ser possivel utilizar o form corretamente na função de editar
        if Produto.objects.filter(nome__iexact=nome, deletado=False).exclude(id=self.instance.id).exists():

            raise forms.ValidationError("Este nome de produto já está em uso. Por favor, escolha outro nome.")

        return nome

    class Meta:

        model = Produto

        fields = [

            'nome',
            'fabricante',
            'tipo',
            'descricao',
            'ativo'

        ]

        widgets = {

            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'fabricante': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.TextInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'checkbox_ativo'}),


        }


class MovimentacaoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        produto_id = self.instance.produto.id if self.instance.pk else None
        self.fields['produto'].queryset = Produto.objects.filter(Q(ativo=True) | Q(id=produto_id), deletado=False)

    class Meta:
        tipos_movimentacao = (
            (True, 'Entrada'),
            (False, 'Saída')
        )
        model = Movimentacao
        fields = ['produto', 'quantidade', 'local', 'tipo_movimentacao', 'data_hora']
        widgets = {
            'produto': Select(attrs={'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control'}),
            'local': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_movimentacao': forms.Select(choices=tipos_movimentacao, attrs={'class': 'form-control'}),
            'data_hora': forms.DateTimeInput(attrs={'class': 'form-control', 'id': 'data_hora'}),

        }

    def clean_quantidade(self):

        # Inicio - Recuperando os dados enviados ao Form
        tipo_movimentacao = self.data['tipo_movimentacao']
        quantidade_movimentada = self.cleaned_data['quantidade']
        produto_selecionado = self.cleaned_data['produto']
        # Fim

        # Inicio - Obter totais ENTRADAS por produto
        total_produto_entrada = Movimentacao.objects.filter(
            tipo_movimentacao=True,
            deletado=False,
            produto=produto_selecionado
        ).aggregate(total_entrada=Sum('quantidade')) or 0
        # -------------------- Fim --------------------

        # Inicio - Obter totais SAIDAS por produto
        total_produto_saida = Movimentacao.objects.filter(
            tipo_movimentacao=False,
            deletado=False,
            produto=produto_selecionado
        ).aggregate(total_saida=Sum('quantidade')) or 0
        # -------------------- Fim --------------------

        total_entrada = total_produto_entrada['total_entrada'] or 0
        total_saida = total_produto_saida['total_saida'] or 0
        total_estoque_produto = total_entrada - total_saida or 0
        movimentacao_valida = (total_estoque_produto - quantidade_movimentada) >= 0

        if quantidade_movimentada <= 0:
            raise forms.ValidationError(f"A quantidade deve ser maior que zero.")
        elif not movimentacao_valida and tipo_movimentacao == 'False' and total_entrada > 0:
            raise forms.ValidationError(
                f"Estoque insuficiente, existem <strong>{total_estoque_produto} itens</strong> do produto "
                f"<strong>em estoque</strong>, faça mais entradas "
                f"deste produto para ser possivel efetuar a saida.")
        elif tipo_movimentacao == 'False' and total_estoque_produto == 0:
            raise forms.ValidationError(
                f"Estoque insuficiente, existem <strong>0 itens</strong> do produto "
                f"<strong>em estoque</strong>, faça mais entradas "
                f"deste produto para ser possivel efetuar a saida.")

        return quantidade_movimentada
