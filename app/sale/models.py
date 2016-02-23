#!/usr/bin/env python
#coding: utf-8
#
# Copyright 2016, Marcos Salomão.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
__author__ = "Marcos Salomão"
__email__ = "salomao.marcos@gmail.com"
__copyright__ = "Copyright 2016, Marcos Salomão"
__license__ = "Apache 2.0"

import logging
import datetime

from app import user
from app import util
from app.marketplace import models as marketplace

from google.appengine.ext import ndb
from google.appengine.api import search as search_api
from app.product import models as product
from app.customer import models as customer

class SaleModel(ndb.Model):
	"""Entidade representa uma venda realizada"""

	# Cliente
	customer = ndb.LocalStructuredProperty(customer.CustomerModel, keep_keys=True, required=True, repeated=False)

	# Produto
	product = ndb.LocalStructuredProperty(product.ProductModel, keep_keys=True, required=True, repeated=False)

	# Quantidade
	quantity = ndb.IntegerProperty(required=True, default=1)

	# Data Venda
	sale_date = ndb.DateTimeProperty(required=True, default=datetime.datetime.today())

	# Valor Total
	amount = ndb.FloatProperty(required=True)

	# Tarifa Venda
	fare = ndb.FloatProperty(required=False)

	# Total Líquido
	net_total = ndb.FloatProperty(required=True)

	#Cód Rastreamento	
	track_code = ndb.StringProperty(indexed=False)

	#Data criação	
	created_date = ndb.DateTimeProperty(auto_now_add=True)


def get(id):
	"""Selecionar uma venda pelo id.
	"""

	#Identificando usuário da requisição
	email = user.get_current_user().email()

	logging.debug("Obtendo a entidade da loja para o usuario %s", email)

	#Obtendo marketplace como parent
	marketplaceModel = marketplace.get(email)

	logging.debug("Loja encontrada com sucesso")

	#Realizando query, selecionando a venda pelo pai e id
	sale = ndb.Key('SaleModel', int(id), parent=marketplaceModel.key).get() 

	if sale is None:
		raise IndexError("Venda não encontrada!")

	logging.debug("Venda encontrado com sucesso")

	return customer


def get_sales_query():
	""" Retorna a query.
	"""

	logging.debug("Listando os clientes cadastrados")

	#Identificando usuário da requisição
	email = user.get_current_user().email()

	logging.debug("Obtendo a entidade da loja para o usuario %s", email)

	#Obtendo marketplace como parent
	marketplaceModel = marketplace.get(email)

	# Retorna query
	return SaleModel.query(ancestor=marketplaceModel.key)


def list():
	"""Listar as vendas realizadas.
	"""
	#Realizando query, listando os clientes
	sales = get_sales_query().fetch()

	logging.debug("Foram selecionada(s) %d venda(s) realizadas na loja do usuário %s", 
		len(sales), email)

	#Retornando
	return sales

@ndb.transactional
def save(sale):
	"""Incluir ou atualizar uma venda.
	"""

	logging.debug("Persistindo uma venda na loja")

	#Identificando usuário da requisição
	email = user.get_current_user().email()

	logging.debug("Obtendo a entidade da loja para o usuario %s", email)

	#Obtendo marketplace como parent
	marketplaceModel = marketplace.get(email)

	logging.debug("Loja encontrada com sucesso")

	logging.debug("Criando model para o cliente ou selecionando o existente para atualizá-lo")

	if sale.id is not None:
		saleModel = ndb.Key('SaleModel', int(sale.id), 
			parent=marketplaceModel.key).get() 
	else:
		saleModel = SaleModel(parent=marketplaceModel.key)

	#Selecionando produto
	productModel = ndb.Key('ProductModel', int(sale.product.id), 
			parent=marketplaceModel.key).get() 
	if productModel is None:
		raise IndexError("Produto com o id %d não encontrado!", sale.product.id)
	saleModel.product = productModel

	#Selecionando cliente
	customerModel = ndb.Key('CustomerModel', int(sale.customer.id), 
			parent=marketplaceModel.key).get() 
	if customerModel is None:
		raise IndexError("Cliente com o id %d não encontrado!", sale.customer.id)
	saleModel.customer = customerModel

	saleModel.quantity = sale.quantity
	saleModel.sale_date = sale.sale_date
	saleModel.amount = sale.amount
	saleModel.fare = sale.fare
	saleModel.net_total = sale.net_total
	saleModel.track_code = sale.track_code

	logging.debug("Persistindo venda...")

	saleModel.put()

	logging.debug("Persistida venda %d com sucesso na loja %s", 
		saleModel.key.id(), marketplaceModel.name)

	#Retornando cliente cadastrado com o id
	return saleModel


@ndb.transactional
def delete(id):
	"""Remove uma venda realizada.
	"""

	logging.debug("Removendo a venda %d persistida na loja", id)

	#Identificando usuário da requisição
	email = user.get_current_user().email()

	logging.debug("Obtendo a entidade da loja para o usuario %s", email)

	#Obtendo marketplace como parent
	marketplaceModel = marketplace.get(email)

	logging.debug("Loja encontrada com sucesso")

	#Realizando query, selecionando o cliente pelo pai e id
	sale = ndb.Key('SaleModel', int(id), parent=marketplaceModel.key).get() 

	if sale is None:
		raise IndexError("Venda não encontrada!")

	logging.debug("Venda encontrada com sucesso")

	sale.key.delete()

	logging.debug("Venda removida com sucesso")