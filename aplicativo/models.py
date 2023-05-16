from django.db import models
from django.utils import timezone


class Produto(models.Model):

    nome = models.CharField(max_length=255)
    fabricante = models.CharField(max_length=255)
    tipo = models.CharField(max_length=255)
    descricao = models.CharField(max_length=255, null=True)
    ativo = models.BooleanField()
    deletado = models.BooleanField(default=False)

    def __str__(self):
        return self.nome


class Movimentacao(models.Model):

    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    data_hora = models.DateTimeField(default=timezone.now)
    quantidade = models.PositiveIntegerField()
    tipo_movimentacao = models.BooleanField()
    local = models.CharField(max_length=255)
    deletado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.quantidade} unidades do produto {self.produto.nome} movimentadas em {self.data_horahora} para " \
               f"{self.local}"


