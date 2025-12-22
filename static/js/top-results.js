(function (global) {
    const SORT_TAX = 'tax';
    const SORT_PROFIT = 'profit';
    const STORAGE_KEY = 'topResultsSort';
    const EPSILON = 1e-9;
    let cachedCalcData = null;

    function parseNumber(value) {
        if (typeof value === 'number') {
            return Number.isFinite(value) ? value : NaN;
        }
        if (typeof value === 'string') {
            const trimmed = value.trim();
            if (trimmed === '') {
                return NaN;
            }
            const parsed = parseFloat(trimmed.replace(',', '.'));
            return Number.isNaN(parsed) ? NaN : parsed;
        }
        return NaN;
    }

    function toNumber(value) {
        const num = parseNumber(value);
        return Number.isFinite(num) ? num : NaN;
    }

    function getCalcData() {
        if (cachedCalcData !== null) {
            return cachedCalcData;
        }
        const script = document.getElementById('calc-data');
        if (!script) {
            cachedCalcData = null;
            return cachedCalcData;
        }
        try {
            cachedCalcData = JSON.parse(script.textContent || '{}') || {};
        } catch (err) {
            console.error('Не удалось распарсить calc_data JSON:', err);
            cachedCalcData = null;
        }
        return cachedCalcData;
    }

    function collectRegimes(calcData) {
        if (!calcData || typeof calcData !== 'object') {
            return [];
        }
        const regimes = calcData.regimes || {};
        const items = [];
        Object.keys(regimes).forEach((regimeId) => {
            const regime = regimes[regimeId] || {};
            const summary = regime.summary || {};
            const burden = toNumber(summary.burden_percent ?? (regime.burden ? regime.burden.burden_percent : undefined));
            const totalBurden = toNumber(summary.total_burden ?? (regime.burden ? regime.burden.total_tax_burden : undefined));
            const netProfit = toNumber(summary.net_profit);
            if (!Number.isFinite(burden) || !Number.isFinite(netProfit)) {
                return;
            }
            items.push({
                id: regimeId,
                title: regime.title || regime.id || regimeId,
                burdenPercent: burden,
                totalBurden: Number.isFinite(totalBurden) ? totalBurden : 0,
                netProfit,
            });
        });
        return items;
    }

    function formatMoney(value) {
        const num = Number(value) || 0;
        return num.toLocaleString('ru-RU', { maximumFractionDigits: 0 });
    }

    function formatPercent(value) {
        const num = Number(value) || 0;
        return num.toLocaleString('ru-RU', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }

    function comparatorTax(a, b) {
        const diff = a.burdenPercent - b.burdenPercent;
        if (Math.abs(diff) > EPSILON) {
            return diff;
        }
        const profitDiff = b.netProfit - a.netProfit;
        if (Math.abs(profitDiff) > EPSILON) {
            return profitDiff;
        }
        return a.title.localeCompare(b.title);
    }

    function comparatorProfit(a, b) {
        const diff = b.netProfit - a.netProfit;
        if (Math.abs(diff) > EPSILON) {
            return diff;
        }
        const loadDiff = a.burdenPercent - b.burdenPercent;
        if (Math.abs(loadDiff) > EPSILON) {
            return loadDiff;
        }
        return a.title.localeCompare(b.title);
    }

    function sortRegimes(regimes, sortKey) {
        const comparator = sortKey === SORT_PROFIT ? comparatorProfit : comparatorTax;
        return regimes.slice().sort(comparator).slice(0, 5);
    }

    function renderRows(rows, tbody) {
        if (!tbody) {
            return;
        }
        tbody.innerHTML = '';
        if (!rows.length) {
            const emptyRow = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 4;
            cell.textContent = 'Нет данных для отображения.';
            emptyRow.appendChild(cell);
            tbody.appendChild(emptyRow);
            return;
        }

        rows.forEach((item) => {
            const tr = document.createElement('tr');
            const nameCell = document.createElement('td');
            nameCell.className = 'regime-name';
            nameCell.textContent = item.title;

            const burdenSumCell = document.createElement('td');
            burdenSumCell.className = 'number-cell';
            burdenSumCell.textContent = formatMoney(item.totalBurden);

            const burdenPercentCell = document.createElement('td');
            burdenPercentCell.className = 'number-cell';
            burdenPercentCell.textContent = `${formatPercent(item.burdenPercent)}%`;

            const netProfitCell = document.createElement('td');
            netProfitCell.className = 'number-cell';
            netProfitCell.textContent = formatMoney(item.netProfit);

            tr.appendChild(nameCell);
            tr.appendChild(burdenSumCell);
            tr.appendChild(burdenPercentCell);
            tr.appendChild(netProfitCell);
            tbody.appendChild(tr);
        });
    }

    function loadPreference(defaultValue) {
        try {
            const stored = global.localStorage ? global.localStorage.getItem(STORAGE_KEY) : null;
            if (stored === SORT_PROFIT || stored === SORT_TAX) {
                return stored;
            }
        } catch (err) {
            // ignore storage issues
        }
        return defaultValue;
    }

    function savePreference(value) {
        try {
            if (global.localStorage) {
                global.localStorage.setItem(STORAGE_KEY, value);
            }
        } catch (err) {
            // ignore storage issues
        }
    }

    function updateControls(controls, selectedValue) {
        controls.forEach((control) => {
            control.checked = control.value === selectedValue;
        });
    }

    function init() {
        const container = document.getElementById('top-results');
        if (!container) {
            return;
        }
        const calcData = getCalcData();
        const regimes = collectRegimes(calcData);
        if (!regimes.length) {
            return;
        }

        const tbody = container.querySelector('#top-results-body');
        const controls = Array.from(container.querySelectorAll('input[name="top-results-sort"]'));
        const defaultSort = container.dataset.defaultSort === SORT_PROFIT ? SORT_PROFIT : SORT_TAX;
        let currentSort = loadPreference(defaultSort);
        updateControls(controls, currentSort);
        renderRows(sortRegimes(regimes, currentSort), tbody);

        controls.forEach((input) => {
            input.addEventListener('change', () => {
                if (!input.checked) {
                    return;
                }
                currentSort = input.value === SORT_PROFIT ? SORT_PROFIT : SORT_TAX;
                savePreference(currentSort);
                renderRows(sortRegimes(regimes, currentSort), tbody);
            });
        });
    }

    global.TopResults = {
        init,
    };
})(window);
