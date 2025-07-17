from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal

# ------------------------------------------------
# Schema para Entidade
# ------------------------------------------------
class EntidadeSchema(BaseModel):
    id: int
    nome: str
    class Config: from_attributes = True

# ------------------------------------------------
# Schema para Almoxarifado
# ------------------------------------------------
class AlmoxarifadoSchema(BaseModel):
    id: int
    descricao: str
    class Config: from_attributes = True

# ------------------------------------------------
# Schema para Produto
# ------------------------------------------------
class ProdutoSchema(BaseModel):
    id: int
    codigo: str
    descricao: str | None
    class Config: from_attributes = True

# ------------------------------------------------
# Schema para Operacao
# ------------------------------------------------
class OperacaoSchema(BaseModel):
    id: int
    descricao: str | None
    class Config: from_attributes = True

# ------------------------------------------------
# Schema para Lote
# ------------------------------------------------
class LoteSchema(BaseModel):
    id: int
    numero: str | None
    class Config: from_attributes = True

# ------------------------------------------------
# Schema para MovimentacaoGeral (O QUE ESTAVA FALTANDO)
# ------------------------------------------------
class MovimentacaoGeralSchema(BaseModel):
    id: int
    numero: int | None
    data: datetime | None
    historico: str | None
    status: bool | None
    descricao_operacao: str | None
    class Config: from_attributes = True

# ------------------------------------------------
# Schema para ItemMovimentacao
# ------------------------------------------------
class ItemMovimentacaoSchema(BaseModel):
    id: int
    quantidade: Decimal | None
    valor_unitario: Decimal | None
    lote: str | None
    fk_produto: int
    fk_lote: int | None
    class Config: from_attributes = True

# ------------------------------------------------
# Schema para Relatório de Itens
# ------------------------------------------------
class ItensReportSchema(BaseModel):
    movimentacao_id: int
    produto_codigo: str
    produto_descricao: str | None
    lote_numero: str | None
    quantidade: Decimal | None
    valor_unitario: Decimal | None

# ------------------------------------------------
# Schema para Relatório de Consistência
# ------------------------------------------------
class ConsistenciaEstoqueSchema(BaseModel):
    produto_id: int
    produto_descricao: str
    almoxarifado_id: int
    almoxarifado_descricao: str
    total_entradas: Decimal
    total_saidas: Decimal
    saldo_calculado: Decimal
    saldo_atual_db: Decimal
    diferenca: Decimal