from sqlalchemy import (
    Column, 
    Integer, 
    String, 
    Boolean, 
    Text, 
    Numeric, 
    ForeignKey,
    DateTime,
    Date
)
from sqlalchemy.orm import relationship

from ..database.database import Base

# 1. Modelo Entidade
class Entidade(Base):
    __tablename__ = "entidade"
    id = Column(Integer, primary_key=True, index=True)
    fk_cidade = Column(Integer)
    nome = Column(String(100), nullable=False)
    cnpj = Column(String(14), unique=True, index=True)
    endereco = Column(String(100))
    sigla = Column(String(50))
    brasao = Column(Text)
    status = Column(Boolean, default=True)

    almoxarifados = relationship("Almoxarifado", back_populates="entidade")
    operacoes = relationship("Operacao", back_populates="entidade")
    lotes = relationship("Lote", back_populates="entidade")

# 2. Modelo Almoxarifado
class Almoxarifado(Base):
    __tablename__ = "almoxarifado"
    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String(100), nullable=False)
    endereco = Column(String(100))
    fk_lotacao = Column(Integer)
    fk_entidade = Column(Integer, ForeignKey("entidade.id"), nullable=False)

    entidade = relationship("Entidade", back_populates="almoxarifados")

    movimentacoes_origem = relationship(
        "MovimentacaoGeral", 
        foreign_keys="[MovimentacaoGeral.fk_almoxarifado_origem]", 
        back_populates="almoxarifado_origem"
    )
    movimentacoes_destino = relationship(
        "MovimentacaoGeral", 
        foreign_keys="[MovimentacaoGeral.fk_almoxarifado_destino]", 
        back_populates="almoxarifado_destino"
    )

# 3. Modelo MovimentacaoGeral
class MovimentacaoGeral(Base):
    __tablename__ = "movimentacao_geral"
    id = Column(Integer, primary_key=True, index=True)
    numero = Column(Integer)
    data = Column(DateTime)
    historico = Column(Text)
    status = Column(Boolean)

    fk_almoxarifado_origem = Column(Integer, ForeignKey("almoxarifado.id"))
    fk_almoxarifado_destino = Column(Integer, ForeignKey("almoxarifado.id"))
    fk_operacao = Column(Integer, ForeignKey("operacao.id"))
    fk_inventario = Column(Integer)
    fk_nota_fiscal = Column(Integer)
    fk_requisicao = Column(Integer)
    fk_requisicao_transferencia = Column(Integer)
    fk_movimentador = Column(Integer)
    fk_lotacao_devolucao = Column(Integer)

    almoxarifado_origem = relationship("Almoxarifado", foreign_keys=[fk_almoxarifado_origem], back_populates="movimentacoes_origem")
    almoxarifado_destino = relationship("Almoxarifado", foreign_keys=[fk_almoxarifado_destino], back_populates="movimentacoes_destino")
    operacao = relationship("Operacao", back_populates="movimentacoes")
    itens = relationship("ItemMovimentacao", back_populates="movimentacao_geral")

# 4. Modelo ItemMovimentacao
class ItemMovimentacao(Base):
    __tablename__ = "item_movimentacao"
    id = Column(Integer, primary_key=True, index=True)
    quantidade = Column(Numeric(10, 3))
    lote = Column(String(100))
    valor_unitario = Column(Numeric(15, 3))

    fk_movimentacao_geral = Column(Integer, ForeignKey("movimentacao_geral.id"), nullable=False)
    fk_produto = Column(Integer, ForeignKey("produto.id"), nullable=False)
    fk_lote = Column(Integer, ForeignKey("lote.id"))

    movimentacao_geral = relationship("MovimentacaoGeral", back_populates="itens")
    produto = relationship("Produto", back_populates="itens_movimentados")
    lote = relationship("Lote", back_populates="itens_movimentados")

# 5. Modelo Produto
class Produto(Base):
    __tablename__ = "produto"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, index=True, nullable=False)
    descricao = Column(String(255))
    status = Column(Boolean, default=True)
    codigo_barras = Column(String(255))
    estoque_minimo = Column(Numeric(10, 3))
    estoque_maximo = Column(Numeric(10, 3))
    prazo_reposicao = Column(Integer)
    fk_tipo_produto = Column(Integer)
    fk_unidade_medida = Column(Integer)

    itens_movimentados = relationship("ItemMovimentacao", back_populates="produto")

# 6. Modelo Operacao
class Operacao(Base):
    __tablename__ = "operacao"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(5), nullable=False)
    descricao = Column(String(255))
    tipo = Column(Integer) # 0 = Entrada, 1 = Saída
    op_nota = Column(Integer)
    fk_entidade = Column(Integer, ForeignKey("entidade.id"), nullable=False)

    entidade = relationship("Entidade", back_populates="operacoes")
    movimentacoes = relationship("MovimentacaoGeral", back_populates="operacao")

# 7. Modelo Lote
class Lote(Base):
    __tablename__ = "lote"
    id = Column(Integer, primary_key=True, index=True)
    nome_fabricante = Column(String(50))
    numero = Column(String(30))
    data_fabricacao = Column(Date)
    data_validade = Column(Date)
    fk_entidade = Column(Integer, ForeignKey("entidade.id"), nullable=False)

    entidade = relationship("Entidade", back_populates="lotes")
    itens_movimentados = relationship("ItemMovimentacao", back_populates="lote")

# 8. Modelo ItemAlmoxarifado (para o saldo atual)
class ItemAlmoxarifado(Base):
    __tablename__ = "item_almoxarifado"
    id = Column(Integer, primary_key=True)
    fk_produto = Column(Integer, ForeignKey("produto.id"), nullable=False)
    fk_lote = Column(Integer, ForeignKey("lote.id"))
    fk_almoxarifado = Column(Integer, ForeignKey("almoxarifado.id"), nullable=False)
    quantidade = Column(Numeric(10, 3))
    valor_medio = Column(Numeric(10, 3))