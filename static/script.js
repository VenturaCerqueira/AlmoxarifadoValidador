document.addEventListener('DOMContentLoaded', () => {
    const selects = {
        entidade: document.getElementById('filtro-entidade'),
        almoxarifado: document.getElementById('filtro-almoxarifado'),
        produto: document.getElementById('filtro-produto'),
        lote: document.getElementById('filtro-lote'),
        operacao: document.getElementById('filtro-operacao'),
    };
    const searchButton = document.getElementById('search-button');
    const resultsArea = document.getElementById('results-area');

    function populateSelect(select, data, valueField, textField, prompt) {
        select.innerHTML = `<option value="">${prompt}</option>`;
        data.forEach(item => {
            const text = textField.includes('+') 
                ? textField.split('+').map(k => item[k.trim()]).join(' - ') 
                : item[textField];
            const option = new Option(text, item[valueField]);
            select.add(option);
        });
        select.disabled = false;
    }

    // Carrega o filtro inicial de entidades
    fetch('/entidades/').then(r => r.json()).then(data => populateSelect(selects.entidade, data, 'id', 'nome', 'Selecione uma entidade'));

    // Quando uma entidade é selecionada, carrega TODOS os filtros dependentes
    selects.entidade.addEventListener('change', () => {
        const entidadeId = selects.entidade.value;
        searchButton.disabled = !entidadeId;

        // Limpa e desabilita todos os filtros filhos
        ['almoxarifado', 'produto', 'lote', 'operacao'].forEach(k => {
            selects[k].innerHTML = `<option value="">Selecione uma entidade</option>`;
            selects[k].disabled = true;
        });

        if (!entidadeId) return;

        // Popula os dropdowns com base na entidade selecionada
        fetch(`/entidades/${entidadeId}/almoxarifados/`).then(r => r.json()).then(data => populateSelect(selects.almoxarifado, data, 'id', 'descricao', 'Todos os almoxarifados'));
        fetch(`/entidades/${entidadeId}/produtos-movimentados/`).then(r => r.json()).then(data => populateSelect(selects.produto, data, 'id', 'descricao', 'Todos os produtos relevantes'));
        fetch(`/entidades/${entidadeId}/lotes/`).then(r => r.json()).then(data => populateSelect(selects.lote, data, 'id', 'numero', 'Todos os lotes'));
        fetch(`/entidades/${entidadeId}/operacoes/`).then(r => r.json()).then(data => populateSelect(selects.operacao, data, 'id', 'descricao', 'Todas as operações'));
    });

    // Ação do botão de busca
    searchButton.addEventListener('click', () => {
        const entidadeId = selects.entidade.value;
        if (!entidadeId) {
            alert('A seleção da Entidade é obrigatória.');
            return;
        }

        // Monta a URL para a API de relatório com os filtros selecionados
        let url = `/relatorios/itens-por-filtro/?entidade_id=${entidadeId}`;
        if (selects.almoxarifado.value) url += `&almoxarifado_id=${selects.almoxarifado.value}`;
        if (selects.produto.value) url += `&produto_id=${selects.produto.value}`;
        if (selects.lote.value) url += `&lote_id=${selects.lote.value}`;
        if (selects.operacao.value) url += `&operacao_id=${selects.operacao.value}`;
        
        resultsArea.innerHTML = `<div class="status-message">Buscando dados para o relatório...</div>`;

        // Chama a API e renderiza a tabela de resultados com os itens
        fetch(url)
            .then(res => res.ok ? res.json() : Promise.reject('Erro na busca'))
            .then(data => {
                if (data.length === 0) {
                    resultsArea.innerHTML = `<div class="status-message">Nenhum item encontrado com os filtros selecionados.</div>`;
                    return;
                }
                const tableHeaders = `<thead><tr><th>ID Mov.</th><th>Cód. Produto</th><th>Produto</th><th>Lote</th><th>Quantidade</th><th>Valor Unitário</th></tr></thead>`;
                const tableRows = data.map(item => {
                    const valorFmt = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(item.valor_unitario || 0);
                    return `<tr>
                        <td>${item.movimentacao_id}</td>
                        <td>${item.produto_codigo}</td>
                        <td>${item.produto_descricao || ''}</td>
                        <td>${item.lote_numero || 'N/A'}</td>
                        <td>${item.quantidade}</td>
                        <td>${valorFmt}</td>
                    </tr>`;
                }).join('');
                resultsArea.innerHTML = `<table>${tableHeaders}<tbody>${tableRows}</tbody></table>`;
            })
            .catch(err => {
                console.error(err);
                resultsArea.innerHTML = `<div class="status-message error-message">Ocorreu um erro ao gerar o relatório.</div>`;
            });
    });
});