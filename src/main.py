from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List
from decimal import Decimal
from pathlib import Path

from .models import models
from .schemas import schemas
from .database.database import SessionLocal, engine, Base

Base.metadata.create_all(bind=engine)

tags_metadata = [
    {"name": "Frontend", "description": "Rota para servir a aplicação web."},
    {"name": "Relatórios", "description": "Rotas para buscas complexas e auditorias de estoque."},
]

app = FastAPI(title="API do Almoxarifado", openapi_tags=tags_metadata)

BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Rota Principal (Frontend) ---
@app.get("/", tags=["Frontend"], response_model=None)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- ROTA DE RELATÓRIO COM AUDITORIA ---
@app.get("/relatorios/itens-por-filtro/", response_model=List[schemas.ItensReportSchema], tags=["Relatórios"])
def get_detailed_items_report_by_filter(
    entidade_id: int,
    almoxarifado_id: int | None = None,
    produto_id: int | None = None,
    lote_id: int | None = None,
    operacao_id: int | None = None,
    db: Session = Depends(get_db)
):
    # Parte 1: Encontrar as movimentações que correspondem aos filtros
    query_mov_ids = db.query(models.MovimentacaoGeral.id)
    almoxarifados_ids = [id_tuple[0] for id_tuple in db.query(models.Almoxarifado.id).filter(models.Almoxarifado.fk_entidade == entidade_id).all()]
    if not almoxarifados_ids: return []
    query_mov_ids = query_mov_ids.filter(or_(models.MovimentacaoGeral.fk_almoxarifado_origem.in_(almoxarifados_ids), models.MovimentacaoGeral.fk_almoxarifado_destino.in_(almoxarifados_ids)))

    if almoxarifado_id: query_mov_ids = query_mov_ids.filter(or_(models.MovimentacaoGeral.fk_almoxarifado_origem == almoxarifado_id, models.MovimentacaoGeral.fk_almoxarifado_destino == almoxarifado_id))
    if operacao_id: query_mov_ids = query_mov_ids.filter(models.MovimentacaoGeral.fk_operacao == operacao_id)
    if produto_id or lote_id:
        query_mov_ids = query_mov_ids.join(models.ItemMovimentacao)
        if produto_id: query_mov_ids = query_mov_ids.filter(models.ItemMovimentacao.fk_produto == produto_id)
        if lote_id: query_mov_ids = query_mov_ids.filter(models.ItemMovimentacao.fk_lote == lote_id)

    movimentacoes_ids = [id_tuple[0] for id_tuple in query_mov_ids.distinct().all()]
    if not movimentacoes_ids: return []

    # Parte 2: Buscar os itens dessas movimentações e os dados para o cálculo
    itens_base = (
        db.query(
            models.ItemMovimentacao,
            models.Produto.codigo,
            models.Produto.descricao,
            models.Lote.numero,
            models.Operacao.tipo,
            models.MovimentacaoGeral
        )
        .join(models.Produto, models.ItemMovimentacao.fk_produto == models.Produto.id)
        .join(models.MovimentacaoGeral, models.ItemMovimentacao.fk_movimentacao_geral == models.MovimentacaoGeral.id)
        .join(models.Operacao, models.MovimentacaoGeral.fk_operacao == models.Operacao.id)
        .outerjoin(models.Lote, models.ItemMovimentacao.fk_lote == models.Lote.id)
        .filter(models.ItemMovimentacao.fk_movimentacao_geral.in_(movimentacoes_ids))
        .all()
    )
    
    # Parte 3: Processar cada item e fazer a auditoria
    relatorio_final = []
    for item, prod_codigo, prod_desc, lote_num, op_tipo, mov in itens_base:
        almox_afetado_id = mov.fk_almoxarifado_destino if op_tipo == 0 else mov.fk_almoxarifado_origem
        if not almox_afetado_id: continue

        # Calcula o total de entradas (tipo 0)
        total_entradas = db.query(func.sum(models.ItemMovimentacao.quantidade)).join(models.MovimentacaoGeral).join(models.Operacao).filter(models.ItemMovimentacao.fk_produto == item.fk_produto, models.ItemMovimentacao.fk_lote == item.fk_lote, models.MovimentacaoGeral.fk_almoxarifado_destino == almox_afetado_id, models.Operacao.tipo == 0).scalar() or Decimal(0)
        # Calcula o total de saídas (tipo 1)
        total_saidas = db.query(func.sum(models.ItemMovimentacao.quantidade)).join(models.MovimentacaoGeral).join(models.Operacao).filter(models.ItemMovimentacao.fk_produto == item.fk_produto, models.ItemMovimentacao.fk_lote == item.fk_lote, models.MovimentacaoGeral.fk_almoxarifado_origem == almox_afetado_id, models.Operacao.tipo == 1).scalar() or Decimal(0)
        saldo_calculado = total_entradas - total_saidas

        # Busca o saldo atual na tabela item_almoxarifado
        saldo_db_obj = db.query(models.ItemAlmoxarifado.quantidade).filter(models.ItemAlmoxarifado.fk_produto == item.fk_produto, models.ItemAlmoxarifado.fk_lote == item.fk_lote, models.ItemAlmoxarifado.fk_almoxarifado == almox_afetado_id).first()
        saldo_db = saldo_db_obj[0] if saldo_db_obj else Decimal(0)

        relatorio_final.append({
            "movimentacao_id": item.fk_movimentacao_geral, "produto_codigo": prod_codigo,
            "produto_descricao": prod_desc, "lote_numero": lote_num,
            "quantidade_movimentada": item.quantidade,
            "saldo_calculado": saldo_calculado, "saldo_db": saldo_db,
            "diferenca": saldo_calculado - saldo_db
        })
    return relatorio_final

# --- Rotas de Suporte para Filtros (API) ---
@app.get("/entidades/", response_model=List[schemas.EntidadeSchema], tags=["Entidades"])
def listar_entidades(db: Session = Depends(get_db)):
    return db.query(models.Entidade).order_by(models.Entidade.nome).all()

@app.get("/entidades/{entidade_id}/almoxarifados/", response_model=List[schemas.AlmoxarifadoSchema], tags=["Almoxarifados"])
def listar_almoxarifados_por_entidade(entidade_id: int, db: Session = Depends(get_db)):
    entidade = db.query(models.Entidade).filter(models.Entidade.id == entidade_id).first()
    if not entidade: raise HTTPException(status_code=404, detail="Entidade não encontrada")
    return entidade.almoxarifados

@app.get("/entidades/{entidade_id}/operacoes/", response_model=List[schemas.OperacaoSchema], tags=["Operações"])
def listar_operacoes_por_entidade(entidade_id: int, db: Session = Depends(get_db)):
    entidade = db.query(models.Entidade).filter(models.Entidade.id == entidade_id).first()
    if not entidade: raise HTTPException(status_code=404, detail="Entidade não encontrada")
    return entidade.operacoes

@app.get("/entidades/{entidade_id}/lotes/", response_model=List[schemas.LoteSchema], tags=["Lotes"])
def listar_lotes_por_entidade(entidade_id: int, db: Session = Depends(get_db)):
    entidade = db.query(models.Entidade).filter(models.Entidade.id == entidade_id).first()
    if not entidade: raise HTTPException(status_code=404, detail="Entidade não encontrada")
    return entidade.lotes

@app.get("/entidades/{entidade_id}/produtos-movimentados/", response_model=List[schemas.ProdutoSchema], tags=["Produtos"])
def listar_produtos_movimentados_por_entidade(entidade_id: int, db: Session = Depends(get_db)):
    almoxarifados_ids = [id_tuple[0] for id_tuple in db.query(models.Almoxarifado.id).filter(models.Almoxarifado.fk_entidade == entidade_id).all()]
    if not almoxarifados_ids: return []
    produtos = (
        db.query(models.Produto).distinct().join(models.ItemMovimentacao)
        .join(models.MovimentacaoGeral, models.ItemMovimentacao.fk_movimentacao_geral == models.MovimentacaoGeral.id)
        .filter(or_(
            models.MovimentacaoGeral.fk_almoxarifado_origem.in_(almoxarifados_ids),
            models.MovimentacaoGeral.fk_almoxarifado_destino.in_(almoxarifados_ids)
        )).order_by(models.Produto.descricao).all()
    )
    return produtos