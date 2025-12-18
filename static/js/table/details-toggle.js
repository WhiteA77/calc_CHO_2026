(function (global) {
    let calcDataCache = null;
    let calcDataParsed = false;

    function parseNumber(value) {
        const num = parseFloat(value);
        return Number.isNaN(num) ? 0 : num;
    }

    function numberOrZero(value) {
        if (typeof value === 'number') {
            return Number.isFinite(value) ? value : 0;
        }
        if (typeof value === 'string' && value.trim() !== '') {
            const parsed = parseFloat(value);
            return Number.isNaN(parsed) ? 0 : parsed;
        }
        return 0;
    }

    function getCalcData() {
        if (calcDataParsed) {
            return calcDataCache;
        }
        calcDataParsed = true;
        const el = document.getElementById('calc-data');
        if (!el) {
            calcDataCache = null;
            return calcDataCache;
        }

        try {
            const raw = el.textContent || '{}';
            calcDataCache = JSON.parse(raw) || {};
        } catch (err) {
            console.error('Не удалось распарсить calc_data JSON:', err);
            calcDataCache = null;
        }
        return calcDataCache;
    }

    function collectBaseDataset(table) {
        const ds = table.dataset;
        return {
            costOfGoods: parseNumber(ds.costOfGoods),
            rent: parseNumber(ds.rent),
            otherExpenses: parseNumber(ds.otherExpenses),
            annualFot: parseNumber(ds.annualFot),
            insuranceStandard: parseNumber(ds.insuranceStandard),
            fixedContrib: parseNumber(ds.fixedContrib),
            vatPurchasesPercent: parseNumber(ds.vatPurchasesPercent),
            vatShareCogs: parseNumber(ds.vatShareCogs !== undefined ? ds.vatShareCogs : ds.vatPurchasesPercent),
            vatShareRent: parseNumber(ds.vatShareRent !== undefined ? ds.vatShareRent : '1'),
            vatShareOther: parseNumber(ds.vatShareOther !== undefined ? ds.vatShareOther : '1'),
            accumulatedVatCredit: parseNumber(ds.accumulatedVatCredit),
            stockExtra: parseNumber(ds.stockExtra),
            transitionMode: ds.transitionMode || 'none',
        };
    }

    function collectRowDataset(row) {
        const data = row.dataset;
        return {
            regimeId: data.regimeId || '',
            regime: data.regime || '',
            revenue: parseNumber(data.revenue),
            expenses: parseNumber(data.expenses),
            tax: parseNumber(data.tax),
            vat: parseNumber(data.vat),
            insurance: parseNumber(data.insurance),
            totalBurden: parseNumber(data.totalBurden),
            burdenPercent: parseNumber(data.burdenPercent),
            netProfit: parseNumber(data.netProfit),
            ownerExtra: parseNumber(data.ownerExtra),
            ownerExtraBase: parseNumber(data.ownerExtraBase),
            usnRegularTax: parseNumber(data.usnRegularTax),
            usnMinTax: parseNumber(data.usnMinTax),
            taxInitial: parseNumber(data.taxInitial),
            taxReduction: parseNumber(data.taxReduction),
            taxReductionLimit: parseNumber(data.taxReductionLimit),
            fixedContrib: parseNumber(data.fixedContrib),
            fixedContribReduction: parseNumber(data.fixedReduction),
            ndflBase: parseNumber(data.ndflBase),
            ndflTax: parseNumber(data.ndflTax),
            incomeNoVat: parseNumber(data.incomeNoVat),
            expensesNoVat: parseNumber(data.expensesNoVat),
        };
    }

    function readNumber(source, key, fallbackValue, label, shouldWarn) {
        if (source && Object.prototype.hasOwnProperty.call(source, key)) {
            return numberOrZero(source[key]);
        }
        if (shouldWarn) {
            console.warn(`[calc] Поле ${label} отсутствует в calc_data, используется значение из data-* атрибутов.`);
        }
        return fallbackValue;
    }

    function buildBaseComponents(table, calcData) {
        const fallback = collectBaseDataset(table);
        const baseJson = calcData && calcData.base;
        if (!baseJson || typeof baseJson !== 'object') {
            return fallback;
        }
        const warn = true;

        return {
            costOfGoods: readNumber(baseJson, 'cost_of_goods_gross', fallback.costOfGoods, 'base.cost_of_goods', warn),
            rent: readNumber(baseJson, 'rent', fallback.rent, 'base.rent', warn),
            otherExpenses: readNumber(baseJson, 'other_expenses', fallback.otherExpenses, 'base.other_expenses', warn),
            annualFot: readNumber(baseJson, 'fot', fallback.annualFot, 'base.fot', warn),
            insuranceStandard: readNumber(baseJson, 'insurance_standard', fallback.insuranceStandard, 'base.insurance_standard', warn),
            fixedContrib: readNumber(baseJson, 'fixed_contrib', fallback.fixedContrib, 'base.fixed_contrib', warn),
            vatPurchasesPercent: readNumber(
                baseJson,
                'vat_purchases_percent',
                fallback.vatPurchasesPercent,
                'base.vat_purchases_percent',
                warn,
            ),
            vatShareCogs: readNumber(baseJson, 'vat_share_cogs', fallback.vatShareCogs, 'base.vat_share_cogs', warn),
            vatShareRent: readNumber(baseJson, 'vat_share_rent', fallback.vatShareRent, 'base.vat_share_rent', warn),
            vatShareOther: readNumber(baseJson, 'vat_share_other', fallback.vatShareOther, 'base.vat_share_other', warn),
            accumulatedVatCredit: readNumber(
                baseJson,
                'accumulated_vat_credit',
                fallback.accumulatedVatCredit,
                'base.accumulated_vat_credit',
                warn,
            ),
            stockExtra: readNumber(baseJson, 'stock_extra', fallback.stockExtra, 'base.stock_extra', warn),
            transitionMode: typeof baseJson.transition_mode === 'string'
                ? baseJson.transition_mode
                : (fallback.transitionMode || 'none'),
        };
    }

    function datasetToRegime(data) {
        const summary = {
            revenue: data.revenue,
            expenses: data.expenses,
            tax: data.tax,
            vat: data.vat,
            insurance: data.insurance,
            totalBurden: data.totalBurden,
            burdenPercent: data.burdenPercent,
            netProfit: data.netProfit,
        };

        const taxes = {
            usnTax: data.tax,
            usnTaxBeforeReduction: data.taxInitial,
            usnReduction: data.taxReduction,
            usnReductionLimit: data.taxReductionLimit,
            vatToPay: data.vat,
            vatCharged: data.vat,
            vatDeductible: 0,
            vatExtraCredit: 0,
        };

        const insurance = {
            insuranceTotal: data.insurance,
            insuranceStandard: 0,
            ownerExtra: data.ownerExtra,
            ownerExtraBase: data.ownerExtraBase,
            fixedContrib: data.fixedContrib,
        };

        const details = {
            ownerExtra: data.ownerExtra,
            ownerExtraBase: data.ownerExtraBase,
            usnRegularTax: data.usnRegularTax,
            usnMinTax: data.usnMinTax,
            taxInitial: data.taxInitial,
            taxReduction: data.taxReduction,
            taxReductionLimit: data.taxReductionLimit,
            fixedContrib: data.fixedContrib,
            fixedContribReduction: data.fixedContribReduction,
            ndflBase: data.ndflBase,
            ndflTax: data.ndflTax,
            incomeWithoutVat: data.incomeNoVat,
            expensesWithoutVat: data.expensesNoVat,
            taxReductionBase: 0,
            ausnTaxBase: 0,
            vatCharged: data.vat,
            vatDeductible: 0,
            vatExtraCredit: 0,
        };

        return {
            id: data.regimeId || data.regime || '',
            title: data.regime || '',
            summary,
            taxes,
            insurance,
            profit: { netProfit: data.netProfit },
            burden: {
                totalTaxBurden: data.totalBurden,
                burdenPercent: data.burdenPercent,
            },
            details,
        };
    }

    function jsonToRegime(jsonRegime, fallback, regimeId) {
        const summaryJson = jsonRegime.summary || {};
        const taxesJson = jsonRegime.taxes || {};
        const insuranceJson = jsonRegime.insurance || {};
        const detailsJson = jsonRegime.details || {};
        const burdenJson = jsonRegime.burden || {};
        const warn = true;

        const summary = {
            revenue: readNumber(summaryJson, 'revenue', fallback.revenue, `regime[${regimeId}].summary.revenue`, warn),
            expenses: readNumber(summaryJson, 'expenses', fallback.expenses, `regime[${regimeId}].summary.expenses`, warn),
            tax: readNumber(summaryJson, 'tax', fallback.tax, `regime[${regimeId}].summary.tax`, warn),
            vat: readNumber(summaryJson, 'vat', fallback.vat, `regime[${regimeId}].summary.vat`, warn),
            insurance: readNumber(summaryJson, 'insurance', fallback.insurance, `regime[${regimeId}].summary.insurance`, warn),
            totalBurden: readNumber(summaryJson, 'total_burden', fallback.totalBurden, `regime[${regimeId}].summary.total_burden`, warn),
            burdenPercent: readNumber(summaryJson, 'burden_percent', fallback.burdenPercent, `regime[${regimeId}].summary.burden_percent`, warn),
            netProfit: readNumber(summaryJson, 'net_profit', fallback.netProfit, `regime[${regimeId}].summary.net_profit`, warn),
        };

        const taxes = {
            usnTax: readNumber(taxesJson, 'usn_tax', fallback.tax, `regime[${regimeId}].taxes.usn_tax`, warn),
            usnTaxBeforeReduction: readNumber(
                taxesJson,
                'usn_tax_before_reduction',
                fallback.taxInitial,
                `regime[${regimeId}].taxes.usn_tax_before_reduction`,
                warn,
            ),
            usnReduction: readNumber(
                taxesJson,
                'usn_reduction',
                fallback.taxReduction,
                `regime[${regimeId}].taxes.usn_reduction`,
                warn,
            ),
            usnReductionLimit: readNumber(
                taxesJson,
                'usn_reduction_limit',
                fallback.taxReductionLimit,
                `regime[${regimeId}].taxes.usn_reduction_limit`,
                warn,
            ),
            vatToPay: readNumber(taxesJson, 'vat_to_pay', fallback.vat, `regime[${regimeId}].taxes.vat_to_pay`, warn),
            vatCharged: readNumber(taxesJson, 'vat_charged', fallback.vat, `regime[${regimeId}].taxes.vat_charged`, warn),
            vatDeductible: readNumber(
                taxesJson,
                'vat_deductible',
                0,
                `regime[${regimeId}].taxes.vat_deductible`,
                warn,
            ),
            vatExtraCredit: readNumber(
                taxesJson,
                'vat_extra_credit',
                0,
                `regime[${regimeId}].taxes.vat_extra_credit`,
                warn,
            ),
        };

        const insurance = {
            insuranceTotal: summary.insurance,
            insuranceStandard: readNumber(
                insuranceJson,
                'insurance_standard',
                0,
                `regime[${regimeId}].insurance.insurance_standard`,
                warn,
            ),
            ownerExtra: readNumber(insuranceJson, 'owner_extra', fallback.ownerExtra, `regime[${regimeId}].insurance.owner_extra`, warn),
            ownerExtraBase: readNumber(
                insuranceJson,
                'owner_extra_base',
                fallback.ownerExtraBase,
                `regime[${regimeId}].insurance.owner_extra_base`,
                warn,
            ),
            fixedContrib: readNumber(
                insuranceJson,
                'fixed_contrib',
                fallback.fixedContrib,
                `regime[${regimeId}].insurance.fixed_contrib`,
                warn,
            ),
        };

        const details = {
            ownerExtra: readNumber(detailsJson, 'owner_extra', fallback.ownerExtra, `regime[${regimeId}].details.owner_extra`, warn),
            ownerExtraBase: readNumber(
                detailsJson,
                'owner_extra_base',
                fallback.ownerExtraBase,
                `regime[${regimeId}].details.owner_extra_base`,
                warn,
            ),
            usnRegularTax: readNumber(
                detailsJson,
                'usn_regular_tax',
                fallback.usnRegularTax,
                `regime[${regimeId}].details.usn_regular_tax`,
                warn,
            ),
            usnMinTax: readNumber(detailsJson, 'usn_min_tax', fallback.usnMinTax, `regime[${regimeId}].details.usn_min_tax`, warn),
            taxInitial: readNumber(detailsJson, 'tax_initial', fallback.taxInitial, `regime[${regimeId}].details.tax_initial`, warn),
            taxReduction: readNumber(
                detailsJson,
                'tax_reduction',
                fallback.taxReduction,
                `regime[${regimeId}].details.tax_reduction`,
                warn,
            ),
            taxReductionLimit: readNumber(
                detailsJson,
                'tax_reduction_limit',
                fallback.taxReductionLimit,
                `regime[${regimeId}].details.tax_reduction_limit`,
                warn,
            ),
            taxReductionBase: readNumber(
                detailsJson,
                'tax_reduction_base',
                0,
                `regime[${regimeId}].details.tax_reduction_base`,
                warn,
            ),
            fixedContrib: readNumber(detailsJson, 'fixed_contrib', fallback.fixedContrib, `regime[${regimeId}].details.fixed_contrib`, warn),
            fixedContribReduction: readNumber(
                detailsJson,
                'fixed_contrib_reduction',
                fallback.fixedContribReduction,
                `regime[${regimeId}].details.fixed_contrib_reduction`,
                warn,
            ),
            ndflBase: readNumber(detailsJson, 'ndfl_base', fallback.ndflBase, `regime[${regimeId}].details.ndfl_base`, warn),
            ndflTax: readNumber(detailsJson, 'ndfl_tax', fallback.ndflTax, `regime[${regimeId}].details.ndfl_tax`, warn),
            incomeWithoutVat: readNumber(
                detailsJson,
                'income_without_vat',
                fallback.incomeNoVat,
                `regime[${regimeId}].details.income_without_vat`,
                warn,
            ),
            expensesWithoutVat: readNumber(
                detailsJson,
                'expenses_without_vat',
                fallback.expensesNoVat,
                `regime[${regimeId}].details.expenses_without_vat`,
                warn,
            ),
            ausnTaxBase: readNumber(detailsJson, 'ausn_tax_base', 0, `regime[${regimeId}].details.ausn_tax_base`, warn),
            vatCharged: readNumber(detailsJson, 'vat_charged', fallback.vat, `regime[${regimeId}].details.vat_charged`, warn),
            vatDeductible: readNumber(detailsJson, 'vat_deductible', 0, `regime[${regimeId}].details.vat_deductible`, warn),
            vatExtraCredit: readNumber(detailsJson, 'vat_extra_credit', 0, `regime[${regimeId}].details.vat_extra_credit`, warn),
        };

        return {
            id: jsonRegime.id || regimeId || fallback.regimeId || fallback.regime || '',
            title: jsonRegime.title || fallback.regime || '',
            summary,
            taxes,
            insurance,
            profit: { netProfit: summary.netProfit },
            burden: {
                totalTaxBurden: readNumber(
                    burdenJson,
                    'total_tax_burden',
                    fallback.totalBurden,
                    `regime[${regimeId}].burden.total_tax_burden`,
                    warn,
                ),
                burdenPercent: readNumber(
                    burdenJson,
                    'burden_percent',
                    fallback.burdenPercent,
                    `regime[${regimeId}].burden.burden_percent`,
                    warn,
                ),
            },
            details,
        };
    }

    function buildRegimePayload(row, calcData) {
        const fallback = collectRowDataset(row);
        const regimeId = row.dataset.regimeId || fallback.regimeId;

        if (!calcData || !calcData.regimes) {
            return datasetToRegime(fallback);
        }
        if (!regimeId) {
            console.warn('Строка режима не содержит data-regime-id, используется резервный источник данных.');
            return datasetToRegime(fallback);
        }

        const jsonRegime = calcData.regimes[regimeId];
        if (!jsonRegime) {
            console.error(`Режим с идентификатором ${regimeId} отсутствует в calc_data. Используется fallback из data-атрибутов.`);
            return datasetToRegime(fallback);
        }

        return jsonToRegime(jsonRegime, fallback, regimeId);
    }

    function toggleDetails(row, baseComponents, calcData) {
        const next = row.nextElementSibling;
        if (next && next.classList.contains('details-row')) {
            next.remove();
            return;
        }

        const explanationModule = global.Explanations;
        if (!explanationModule || typeof explanationModule.buildExplanation !== 'function') {
            return;
        }

        const regimePayload = buildRegimePayload(row, calcData);
        const detailsRow = document.createElement('tr');
        detailsRow.className = 'details-row';

        const cell = document.createElement('td');
        cell.colSpan = 9;
        const box = document.createElement('div');
        box.className = 'details-box';

        const title = document.createElement('div');
        title.className = 'details-title';
        title.textContent = `Расчёт для: ${regimePayload.title || regimePayload.id}`;

        const body = document.createElement('div');
        try {
            body.innerHTML = explanationModule.buildExplanation(regimePayload, baseComponents);
        } catch (err) {
            console.error('Ошибка при формировании пояснения:', err);
            body.innerHTML = `<p style="color:#ff6b6b;">Не удалось сформировать пояснение: ${err.message}</p>`;
        }

        box.appendChild(title);
        box.appendChild(body);
        cell.appendChild(box);
        detailsRow.appendChild(cell);

        row.parentNode.insertBefore(detailsRow, row.nextElementSibling);
    }

    function init() {
        const table = document.getElementById('regimes-table');
        if (!table) {
            return;
        }

        const calcData = getCalcData();
        const baseComponents = buildBaseComponents(table, calcData);

        table.querySelectorAll('tr.regime-row').forEach((row) => {
            row.addEventListener('click', () => toggleDetails(row, baseComponents, calcData));
        });
    }

    global.TableDetailsToggle = {
        init,
    };
})(window);
