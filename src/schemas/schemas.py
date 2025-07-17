from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal

class EntidadeSchema(BaseModel):
    id: int
    nome: str
    class Config: from_attributes = True

class AlmoxarifadoSchema(BaseModel):
    id: int
    descricao: str
    class Config: from_attributes = True

class ProdutoSchema(BaseModel):
    id: int
    codigo: str
    descricao: str | None
    class Config: from_attributes = True

class OperacaoSchema(BaseModel):
    id: int
    descricao: str | None
    class Config: from_attributes = True

class LoteSchema(BaseModel):
    id: int
    numero: str | None
    class Config: from_attributes = True

# NOVO SCHEMA PARA O RELATÓRIO
class ItensReportSchema(BaseModel):
    movimentacao_id: int
    produto_codigo: str
    produto_descricao: str | None
    lote_numero: str | None
    quantidade_movimentada: Decimal | None
    saldo_calculado: Decimal
    saldo_db: Decimal
    diferenca: Decimal