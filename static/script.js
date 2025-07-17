document.addEventListener('DOMContentLoaded', () => {
    // Referências aos elementos do DOM
    const selects = {
        entidade: document.getElementById('filtro-entidade'),
        almoxarifado: document.getElementById('filtro-almoxarifado'),
        produto: document.getElementById('filtro-produto'),
        lote: document.getElementById('filtro-lote'),
    };
    const searchButton = document.getElementById('search-button');
    const resetButton = document.getElementById('reset-button'); // Botão de limpar
    const resultsArea = document.getElementById('results-area');

    // Novos elementos para filtros dos resultados
    const resultsFilterPanel = document.getElementById('results-filter-panel');
    const resultSearchInput = document.getElementById('filtro-texto-resultado');
    const diffCheckbox = document.getElementById('filtro-diferenca');

    // Variável para guardar os dados da busca, para filtrar no frontend
    let fullReportData = [];

    // Função para popular os dropdowns
    const populateSelect = (select, data, valueField, textField, prompt) => {
        select.innerHTML = `<option value="">${prompt}</option>`;
        data.forEach(item => {
            const displayText = Array.isArray(textField) ? `${item[textField[0]]} - ${item[textField[1]]}` : item[textField];
            select.add(new Option(displayText, item[valueField]));
        });
        select.disabled = false;
    };

    // Função para renderizar a tabela de resultados
    const renderTable = (data) => {
        if (!data || data.length === 0) {
            resultsArea.innerHTML = `<p class="text-center text-muted">Nenhum item encontrado com os filtros aplicados.</p>`;
            return;
        }

        const tableHeaders = `
            <thead class="thead-light">
                <tr>
                    <th>Cód. Produto</th>
                    <th>Produto</th>
                    <th>Lote</th>
                    <th>Saldo Calculado</th>
                    <th>Saldo no Banco</th>
                    <th>Diferença</th>
                </tr>
            </thead>`;

        const tableRows = data.map(item => {
            const diferenca = parseFloat(item.diferenca);
            const diffClass = diferenca !== 0 ? 'table-danger' : ''; // Classe de perigo para linhas com diferença
            return `
                <tr class="${diffClass}">
                    <td>${item.produto_codigo}</td>
                    <td>${item.produto_descricao || ''}</td>
                    <td>${item.lote_numero || 'N/A'}</td>
                    <td>${parseFloat(item.saldo_calculado).toFixed(3)}</td>
                    <td>${parseFloat(item.saldo_db).toFixed(3)}</td>
                    <td><b>${parseFloat(item.diferenca).toFixed(3)}</b></td>
                </tr>`;
        }).join('');

        resultsArea.innerHTML = `<table class="table table-bordered table-hover">${tableHeaders}<tbody>${tableRows}</tbody></table>`;
    };

    // Função para aplicar os filtros na tabela já carregada
    const applyClientFilters = () => {
        const searchText = resultSearchInput.value.toLowerCase();
        const showOnlyDiff = diffCheckbox.checked;

        let filteredData = [...fullReportData];

        if (searchText) {
            filteredData = filteredData.filter(item =>
                (item.produto_descricao || '').toLowerCase().includes(searchText)
            );
        }

        if (showOnlyDiff) {
            filteredData = filteredData.filter(item => parseFloat(item.diferenca) !== 0);
        }

        renderTable(filteredData);
    };

    // Carrega entidades iniciais
    fetch('/entidades/').then(r => r.json()).then(data => populateSelect(selects.entidade, data, 'id', 'nome', 'Selecione uma entidade'));

    // Evento de mudança na seleção da entidade
    selects.entidade.addEventListener('change', () => {
        const entidadeId = selects.entidade.value;
        searchButton.disabled = !entidadeId;
        
        ['almoxarifado', 'produto', 'lote'].forEach(k => {
            selects[k].innerHTML = '<option value="">Primeiro, selecione uma entidade</option>';
            selects[k].disabled = true;
        });

        if (!entidadeId) return;

        fetch(`/entidades/${entidadeId}/almoxarifados/`).then(r => r.json()).then(data => populateSelect(selects.almoxarifado, data, 'id', 'nome', 'Todos os almoxarifados'));
        fetch(`/entidades/${entidadeId}/lotes/`).then(r => r.json()).then(data => populateSelect(selects.lote, data, 'id', 'numero', 'Todos os lotes'));
        fetch(`/entidades/${entidadeId}/produtos-movimentados/`).then(r => r.json()).then(data => populateSelect(selects.produto, data, 'id', ['codigo', 'descricao'], 'Todos os produtos'));
    });

    // Evento de clique no botão "Gerar Relatório"
    searchButton.addEventListener('click', () => {
        const entidadeId = selects.entidade.value;
        if (!entidadeId) return;

        let url = `/relatorios/itens-por-filtro/?entidade_id=${entidadeId}`;
        if (selects.almoxarifado.value) url += `&almoxarifado_id=${selects.almoxarifado.value}`;
        if (selects.produto.value) url += `&produto_id=${selects.produto.value}`;
        if (selects.lote.value) url += `&lote_id=${selects.lote.value}`;
        
        resultsArea.innerHTML = `<p class="text-center text-muted">Buscando dados...</p>`;
        resultsFilterPanel.style.display = 'none'; // Garante que filtros estão ocultos durante a busca

        fetch(url)
            .then(res => res.ok ? res.json() : Promise.reject('Erro na busca'))
            .then(data => {
                fullReportData = data; // Guarda os dados completos
                renderTable(fullReportData);
                if (data.length > 0) {
                    resultsFilterPanel.style.display = 'flex'; // Mostra os filtros da tabela
                }
            })
            .catch(err => {
                console.error(err);
                resultsArea.innerHTML = `<p class="text-center text-danger">Ocorreu um erro ao gerar o relatório.</p>`;
            });
    });
    
    // Funcionalidade do botão "Limpar Consulta"
    resetButton.addEventListener('click', () => {
        // Reseta os filtros principais
        selects.entidade.value = '';
        selects.entidade.dispatchEvent(new Event('change')); // Dispara o evento para limpar os outros selects

        // Limpa os filtros dos resultados
        resultSearchInput.value = '';
        diffCheckbox.checked = false;
        resultsFilterPanel.style.display = 'none';

        // Limpa a área de resultados
        fullReportData = [];
        resultsArea.innerHTML = `<p class="text-center text-muted">Selecione uma entidade e clique em "Gerar Relatório".</p>`;
    });

    // Adiciona os listeners para os filtros da tabela
    resultSearchInput.addEventListener('input', applyClientFilters);
    diffCheckbox.addEventListener('change', applyClientFilters);
});