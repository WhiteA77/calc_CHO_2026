(function (global) {
    const SORT_TAX = 'tax';
    const SORT_PROFIT = 'profit';
    const STORAGE_KEY = 'regimesTableSort';
    const TARGET_REGIME_ID = 'patent';
    const EPSILON = 1e-9;

    function parseNumber(value) {
        if (typeof value === 'number') {
            return Number.isFinite(value) ? value : NaN;
        }
        if (typeof value === 'string') {
            const trimmed = value.trim();
            if (!trimmed) {
                return NaN;
            }
            const parsed = parseFloat(trimmed.replace(',', '.'));
            return Number.isNaN(parsed) ? NaN : parsed;
        }
        return NaN;
    }

    function getRowData(row) {
        const ds = row.dataset || {};
        const burdenPercent = parseNumber(ds.burdenPercent);
        const netProfit = parseNumber(ds.netProfit);
        const titleCell = row.querySelector('.regime-name');
        const title = titleCell ? titleCell.textContent.trim() : (row.dataset.regime || row.dataset.regimeId || '');
        const regimeId = (ds.regimeId || '').toLowerCase();
        return {
            row,
            burdenPercent,
            netProfit,
            title,
            isTarget: regimeId === TARGET_REGIME_ID,
        };
    }

    function comparatorTax(a, b) {
        const aValue = Number.isFinite(a.burdenPercent) ? a.burdenPercent : Number.POSITIVE_INFINITY;
        const bValue = Number.isFinite(b.burdenPercent) ? b.burdenPercent : Number.POSITIVE_INFINITY;
        if (Math.abs(aValue - bValue) > EPSILON) {
            return aValue - bValue;
        }
        const aProfit = Number.isFinite(a.netProfit) ? a.netProfit : Number.NEGATIVE_INFINITY;
        const bProfit = Number.isFinite(b.netProfit) ? b.netProfit : Number.NEGATIVE_INFINITY;
        if (Math.abs(bProfit - aProfit) > EPSILON) {
            return bProfit - aProfit;
        }
        return a.title.localeCompare(b.title);
    }

    function comparatorProfit(a, b) {
        const aProfit = Number.isFinite(a.netProfit) ? a.netProfit : Number.NEGATIVE_INFINITY;
        const bProfit = Number.isFinite(b.netProfit) ? b.netProfit : Number.NEGATIVE_INFINITY;
        if (Math.abs(bProfit - aProfit) > EPSILON) {
            return bProfit - aProfit;
        }
        const aValue = Number.isFinite(a.burdenPercent) ? a.burdenPercent : Number.POSITIVE_INFINITY;
        const bValue = Number.isFinite(b.burdenPercent) ? b.burdenPercent : Number.POSITIVE_INFINITY;
        if (Math.abs(aValue - bValue) > EPSILON) {
            return aValue - bValue;
        }
        return a.title.localeCompare(b.title);
    }

    function sortRows(rows, sortKey) {
        const comparator = sortKey === SORT_PROFIT ? comparatorProfit : comparatorTax;
        return rows.slice().sort(comparator);
    }

    function placeTargetFirst(rows) {
        const pinned = [];
        const rest = [];
        rows.forEach((item) => {
            if (item.isTarget) {
                pinned.push(item);
            } else {
                rest.push(item);
            }
        });
        return pinned.concat(rest);
    }

    function loadPreference(defaultValue) {
        try {
            const stored = global.localStorage ? global.localStorage.getItem(STORAGE_KEY) : null;
            if (stored === SORT_PROFIT || stored === SORT_TAX) {
                return stored;
            }
        } catch (err) {
            // ignore
        }
        return defaultValue;
    }

    function savePreference(value) {
        try {
            if (global.localStorage) {
                global.localStorage.setItem(STORAGE_KEY, value);
            }
        } catch (err) {
            // ignore
        }
    }

    function removeDetailsRows(table) {
        table.querySelectorAll('tr.details-row').forEach((row) => row.remove());
    }

    function updateControls(controls, selected) {
        controls.forEach((ctrl) => {
            ctrl.checked = ctrl.value === selected;
        });
    }

    function init() {
        const table = document.getElementById('regimes-table');
        if (!table) {
            return;
        }
        const tbody = table.querySelector('tbody');
        if (!tbody) {
            return;
        }
        const rowNodes = Array.from(tbody.querySelectorAll('tr.regime-row'));
        if (!rowNodes.length) {
            return;
        }

        const rowsWithData = rowNodes.map(getRowData);
        const controls = Array.from(document.querySelectorAll('input[name="regimes-sort"]'));
        const defaultSort = SORT_TAX;
        let currentSort = loadPreference(defaultSort);
        updateControls(controls, currentSort);

        function applySort(sortKey) {
            const nextSort = sortKey === SORT_PROFIT ? SORT_PROFIT : SORT_TAX;
            currentSort = nextSort;
            removeDetailsRows(table);
            const sorted = placeTargetFirst(sortRows(rowsWithData, currentSort));
            sorted.forEach((item) => {
                tbody.appendChild(item.row);
            });
        }

        applySort(currentSort);

        controls.forEach((input) => {
            input.addEventListener('change', () => {
                if (!input.checked) {
                    return;
                }
                const newSort = input.value;
                if (newSort === currentSort) {
                    return;
                }
                savePreference(newSort);
                applySort(newSort);
            });
        });
    }

    global.RegimesTableSort = {
        init,
    };
})(window);
