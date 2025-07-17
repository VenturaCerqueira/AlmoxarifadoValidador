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
            const text = textField.includes('+') ? (item[textField.split('+')[0].trim()] + ' - ' + item[textField.split('+')[1].trim()]) : item[textField];
            const option = new Option(text, item[valueField]);
            select.add(option);
        });
        select.disabled = false;
    }

    fetch('/entidades/').then(r => r.json()).then(data => populateSelect(selects.entidade, data, 'id', 'nome', 'Selecione uma entidade'));

    selects.entidade.addEventListener('change', () => {
        const entidadeId = selects.entidade.value;
        searchButton.disabled = !entidadeId;
        ['almoxarifado', 'produto', 'lote', 'operacao'].forEach(k => {
            selects[k].innerHTML = '<option value="">Primeiro, selecione uma entidade</option>';
            selects[k].disabled = true;
        });

        if (!entidadeId) return;

        fetch(`/entidades/${entidadeId}/almoxarifados/`).then(r => r.json()).then(data => populateSelect(selects.almoxarifado, data, 'id', 'descricao', 'Todos os almoxarifados'));
        fetch(`/entidades/${entidadeId}/lotes/`).then(r => r.json()).then(data => populateSelect(selects.lote, data, 'id', 'numero', 'Todos os lotes'));
        fetch(`/entidades/${entidadeId}/operacoes/`).then(r => r.json()).then(data => populateSelect(selects.operacao, data, 'id', 'descricao', 'Todas as operações'));
        fetch(`/entidades/${entidadeId}/produtos-movimentados/`).then(r => r.json()).then(data => {
            if (data.length > 0) {
                populateSelect(selects.produto, data, 'id', 'codigo + descricao', 'Todos os produtos relevantes');
            } else {
                selects.produto.innerHTML = '<option value="">Nenhum produto movimentado</option>';
                selects.produto.disabled = false;
            }
        });
    });

    searchButton.addEventListener('click', () => {
        const entidadeId = selects.entidade.value;
        if (!entidadeId) { alert('A seleção da Entidade é obrigatória.'); return; }

        let url = `/relatorios/itens-por-filtro/?entidade_id=${entidadeId}`;
        if (selects.almoxarifado.value) url += `&almoxarifado_id=${selects.almoxarifado.value}`;
        if (selects.produto.value) url += `&produto_id=${selects.produto.value}`;
        if (selects.lote.value) url += `&lote_id=${selects.lote.value}`;
        if (selects.operacao.value) url += `&operacao_id=${selects.operacao.value}`;
        
        resultsArea.innerHTML = `<div class="status-message">Buscando dados para o relatório...</div>`;

        fetch(url)
            .then(res => res.ok ? res.json() : Promise.reject('Erro na busca'))
            .then(data => {
                if (data.length === 0) {
                    resultsArea.innerHTML = `<div class="status-message">Nenhum item encontrado com os filtros selecionados.</div>`;
                    return;
                }
                const tableHeaders = `<thead><tr>
                    <th>ID Mov.</th><th>Cód. Produto</th><th>Produto</th><th>Lote</th>
                    <th>Qtde. Mov.</th><th>Saldo Calculado</th><th>Saldo no Banco</th><th class="diferenca-col">Diferença</th>
                </tr></thead>`;
                const tableRows = data.map(item => {
                    const diferencaClasse = item.diferenca == 0 ? 'diff-ok' : 'diff-error';
                    return `<tr class="${diferencaClasse}">
                        <td>${item.movimentacao_id}</td><td>${item.produto_codigo}</td>
                        <td>${item.produto_descricao || ''}</td><td>${item.lote_numero || 'N/A'}</td>
                        <td>${item.quantidade_movimentada}</td><td>${item.saldo_calculado}</td>
                        <td>${item.saldo_db}</td><td class="diferenca-col">${item.diferenca}</td>
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