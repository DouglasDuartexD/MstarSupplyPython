"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from aplicativo import views

urlpatterns = [

    # Inicio e Admin
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),

    # Produtos
    path('produto/', views.index_produto, name='produto'),
    path('produto/create', views.create_produto, name='create_produto'),
    path('produto/edit/<int:pk>', views.edit_produto, name='edit_produto'),
    path('produto/delete/<int:pk>', views.delete_produto, name='delete_produto'),
    path('produto/stock', views.stock_produto, name='stock_produto'),

    # Movimentações
    path('movimentacao/', views.index_movimentacao, name='movimentacao'),
    path('movimentacao/create', views.create_movimentacao, name='create_movimentacao'),
    path('movimentacao/edit/<int:pk>', views.edit_movimentacao, name='edit_movimentacao'),
    path('movimentacao/delete/<int:pk>', views.delete_movimentacao, name='delete_movimentacao'),
    path('movimentacao/export-pdf/', views.export_pdf_movimentacao, name='export_pdf_movimentacao'),

]
