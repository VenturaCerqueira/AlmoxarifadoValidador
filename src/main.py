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
    {"name": "Relatórios", "description": "Rotas para buscas complexas e auditorias."},
    {"name": "Entidades", "description": "Operações com entidades."},
    {"name": "Almoxarifados", "description": "Operações com almoxarifados."},
    {"name": "Produtos", "description": "Operações com produtos."},
    {"name": "Operações", "description": "Consulta os tipos de operações."},
    {"name": "Lotes", "description": "Operações com lotes de produtos."},
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

# --- Rotas de Relatórios ---
@app.get("/relatorios/itens-por-filtro/", response_model=List[schemas.ItensReportSchema], tags=["Relatórios"])
def get_detailed_items_report_by_filter(
    entidade_id: int,
    almoxarifado_id: int | None = None,
    produto_id: int | None = None,
    lote_id: int | None = None,
    operacao_id: int | None = None,
    db: Session = Depends(get_db)
):
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

    itens_do_banco = db.query(models.ItemMovimentacao, models.Produto.codigo, models.Produto.descricao, models.Lote.numero).join(models.Produto).outerjoin(models.Lote).filter(models.ItemMovimentacao.fk_movimentacao_geral.in_(movimentacoes_ids)).all()
    
    relatorio_final = []
    for item, prod_codigo, prod_desc, lote_num in itens_do_banco:
        relatorio_final.append({
            "movimentacao_id": item.fk_movimentacao_geral, "produto_codigo": prod_codigo,
            "produto_descricao": prod_desc, "lote_numero": lote_num,
            "quantidade": item.quantidade, "valor_unitario": item.valor_unitario
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
    produtos = db.query(models.Produto).distinct().join(models.ItemMovimentacao).join(models.MovimentacaoGeral).join(models.Almoxarifado).filter(models.Almoxarifado.fk_entidade == entidade_id).order_by(models.Produto.descricao).all()
    return produtos