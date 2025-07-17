SET @entidade_id = 9; -- Forneça o ID da entidade desejada

WITH SaldoCalculado AS ( -- CTE para calcular o saldo de cada produto por almoxarifado e lote
    -- Etapa 1: Calcula o saldo com base em todas as movimentações de entrada e saída
    SELECT
        CASE -- Define o almoxarifado com base no tipo de operação
            WHEN o.tipo = 0 THEN mg.fk_almoxarifado_destino -- Entrada (usa almoxarifado de destino)
            WHEN o.tipo = 1 THEN mg.fk_almoxarifado_origem  -- Saída (usa almoxarifado de origem)
            ELSE NULL    
        END AS id_almoxarifado,
        im.fk_produto,
        im.lote,
        SUM(CASE -- Calcula o saldo com base no tipo de operação 
            WHEN o.tipo = 0 THEN im.quantidade -- Entrada (soma)
            WHEN o.tipo = 1 THEN -im.quantidade -- Saída (subtrai)
            ELSE 0 
        END) AS saldo_calculado
    FROM 
        item_movimentacao AS im
    INNER JOIN 
        movimentacao_geral AS mg ON im.fk_movimentacao_geral = mg.id
    INNER JOIN 
        operacao AS o ON mg.fk_operacao = o.id
    GROUP BY
        id_almoxarifado,
        im.fk_produto,
        im.lote
)
-- Etapa 2: Junta os dados e calcula a diferença
SELECT 
    p.id AS codigo_produto, -- ID do produto
    p.descricao AS produto_descricao, -- Descrição do produto
    sc.lote, -- Lote do produto
    sc.saldo_calculado, -- Saldo calculado a partir das movimentações
    -- Usa COALESCE para tratar casos onde não há saldo em banco, evitando erros no cálculo
    COALESCE(ia.quantidade, 0) AS saldo_banco, 
    -- NOVA COLUNA: Calcula a diferença entre o saldo dos movimentos e o saldo em estoque
    (sc.saldo_calculado - COALESCE(ia.quantidade, 0)) AS diferenca, -- Diferença entre o saldo calculado e o saldo em banco
    e.nome AS nome_entidade -- Nome da entidade associada ao almoxarifado
FROM 
    SaldoCalculado sc -- Usa a CTE para obter o saldo calculado
LEFT JOIN 
    item_almoxarifado ia ON sc.id_almoxarifado = ia.fk_almoxarifado 
                         AND sc.fk_produto = ia.fk_produto
INNER JOIN 
    produto p ON sc.fk_produto = p.id
INNER JOIN 
    almoxarifado a ON sc.id_almoxarifado = a.id
INNER JOIN
    entidade e ON a.fk_entidade = e.id
WHERE 
    e.id = @entidade_id
ORDER BY
    p.descricao,
    sc.lote;