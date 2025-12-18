(function (global) {
    const builders = global.ExplanationBuilders || {};

    function getNumber(value) {
        if (typeof value === 'number') {
            return Number.isFinite(value) ? value : 0;
        }
        if (typeof value === 'string' && value.trim() !== '') {
            const parsed = parseFloat(value);
            return Number.isNaN(parsed) ? 0 : parsed;
        }
        return 0;
    }

    const BUILDER_MAP = {
        ausn_income: () => builders.buildAusn8Markdown,
        ausn_profit: () => builders.buildAusn20Markdown,
        usn_income_no_vat: () => builders.buildUsnIncomeMarkdown,
        usn_income_vat_5: () => builders.buildUsnIncome5Markdown,
        usn_income_vat_22: () => builders.buildUsnIncome22Markdown,
        usn_profit_no_vat: () => builders.buildUsnDrNoVatMarkdown,
        usn_profit_vat_5: () => builders.buildUsnDr5Markdown,
        usn_profit_vat_22: () => builders.buildUsnDr22Markdown,
        osno_ooo: () => builders.buildOsnoMarkdown,
        osno_ip: () => builders.buildOsnoIpMarkdown,
    };

    const STOCK_ELIGIBLE = new Set([
        'usn_profit_no_vat',
        'usn_profit_vat_5',
        'usn_profit_vat_22',
        'osno_ooo',
        'osno_ip',
    ]);

    function selectBuilder(regime) {
        if (!regime) {
            return null;
        }
        const regimeId = regime.id;
        if (regimeId && BUILDER_MAP[regimeId]) {
            const factory = BUILDER_MAP[regimeId];
            const builderFn = typeof factory === 'function' ? factory() : null;
            if (typeof builderFn === 'function') {
                return builderFn;
            }
        }
        return detectBuilderByTitle(regime.title);
    }

    function detectBuilderByTitle(title) {
        const normalized = (title || '').toLowerCase();
        if (!normalized) {
            return null;
        }
        const isAusn8 = normalized.includes('аусн 8');
        const isAusn20 = normalized.includes('аусн 20');
        const includesUsn = normalized.includes('усн');
        const isUsnIncome = includesUsn && normalized.includes('доходы 6%');
        const isUsnDr = includesUsn && (normalized.includes('д-р 15%') || normalized.includes('др 15%'));
        const isUsnIncomeNoVat = isUsnIncome && !normalized.includes('ндс');
        const isUsnIncome5 = isUsnIncome && normalized.includes('ндс 5');
        const isUsnIncome22 = isUsnIncome && normalized.includes('ндс 22');
        const isUsnDrNoVat = isUsnDr && !normalized.includes('ндс');
        const isUsnDr5 = isUsnDr && normalized.includes('ндс 5');
        const isUsnDr22 = isUsnDr && normalized.includes('ндс 22');
        const hasOsno = normalized.includes('осно');
        const includesOoo = normalized.includes('ооо') || normalized.includes('ooo');
        const includesIp = normalized.includes('ип') || normalized.includes('ip');
        const isOsnoCompany = hasOsno && includesOoo;
        const isOsnoIp = hasOsno && includesIp;

        if (isAusn8 && builders.buildAusn8Markdown) {
            return builders.buildAusn8Markdown;
        }
        if (isAusn20 && builders.buildAusn20Markdown) {
            return builders.buildAusn20Markdown;
        }
        if (isUsnIncomeNoVat && builders.buildUsnIncomeMarkdown) {
            return builders.buildUsnIncomeMarkdown;
        }
        if (isUsnIncome5 && builders.buildUsnIncome5Markdown) {
            return builders.buildUsnIncome5Markdown;
        }
        if (isUsnIncome22 && builders.buildUsnIncome22Markdown) {
            return builders.buildUsnIncome22Markdown;
        }
        if (isUsnDrNoVat && builders.buildUsnDrNoVatMarkdown) {
            return builders.buildUsnDrNoVatMarkdown;
        }
        if (isUsnDr5 && builders.buildUsnDr5Markdown) {
            return builders.buildUsnDr5Markdown;
        }
        if (isUsnDr22 && builders.buildUsnDr22Markdown) {
            return builders.buildUsnDr22Markdown;
        }
        if (isOsnoCompany && builders.buildOsnoMarkdown) {
            return builders.buildOsnoMarkdown;
        }
        if (isOsnoIp && builders.buildOsnoIpMarkdown) {
            return builders.buildOsnoIpMarkdown;
        }
        if (hasOsno && builders.buildOsnoIpMarkdown && !isOsnoCompany) {
            return builders.buildOsnoIpMarkdown;
        }
        if (hasOsno && builders.buildOsnoMarkdown) {
            return builders.buildOsnoMarkdown;
        }
        return null;
    }

    function buildParams(regime, baseComponents) {
        const summary = regime.summary || {};
        const taxes = regime.taxes || {};
        const insurance = regime.insurance || {};
        const burden = regime.burden || {};
        const details = regime.details || {};
        const base = baseComponents || {};
        const transitionMode = base.transitionMode || 'none';
        const baseStockExtra = getNumber(base.stockExtra);
        const stockApplicable = transitionMode === 'stock'
            && baseStockExtra > 0
            && regime.id
            && STOCK_ELIGIBLE.has(regime.id);

        return {
            revenue: getNumber(summary.revenue),
            expenses: getNumber(summary.expenses),
            tax: getNumber(summary.tax),
            vat: getNumber(summary.vat),
            insurance: getNumber(summary.insurance),
            totalBurden: getNumber(burden.totalTaxBurden !== undefined ? burden.totalTaxBurden : summary.totalBurden),
            burdenPct: getNumber(burden.burdenPercent !== undefined ? burden.burdenPercent : summary.burdenPercent),
            netProfit: getNumber(summary.netProfit),
            ownerExtra: getNumber(details.ownerExtra !== undefined ? details.ownerExtra : insurance.ownerExtra),
            ownerExtraBase: getNumber(details.ownerExtraBase !== undefined ? details.ownerExtraBase : insurance.ownerExtraBase),
            baseCost: getNumber(base.costOfGoods),
            baseRent: getNumber(base.rent),
            baseOther: getNumber(base.otherExpenses),
            baseFot: getNumber(base.annualFot),
            baseInsurStd: getNumber(base.insuranceStandard),
            vatShareCogs: getNumber(base.vatShareCogs),
            vatShareRent: getNumber(base.vatShareRent),
            vatShareOther: getNumber(base.vatShareOther),
            stockExtra: stockApplicable ? baseStockExtra : 0,
            transitionMode,
            vatPurchasesPercent: getNumber(base.vatPurchasesPercent),
            accumulatedVatCredit: getNumber(base.accumulatedVatCredit),
            usnRegularTax: getNumber(details.usnRegularTax),
            usnMinTax: getNumber(details.usnMinTax),
            taxInitial: getNumber(details.taxInitial !== undefined ? details.taxInitial : taxes.usnTaxBeforeReduction),
            taxReduction: getNumber(details.taxReduction !== undefined ? details.taxReduction : taxes.usnReduction),
            taxReductionLimit: getNumber(
                details.taxReductionLimit !== undefined ? details.taxReductionLimit : taxes.usnReductionLimit,
            ),
            fixedContrib: getNumber(insurance.fixedContrib !== undefined ? insurance.fixedContrib : base.fixedContrib),
            fixedContribReduction: getNumber(details.fixedContribReduction),
            ndflTax: getNumber(details.ndflTax),
            ndflBase: getNumber(details.ndflBase),
            incomeWithoutVat: getNumber(details.incomeWithoutVat),
            expensesWithoutVat: getNumber(details.expensesWithoutVat),
            vatCharged: getNumber(details.vatCharged),
            vatDeductible: getNumber(details.vatDeductible),
            vatExtraCredit: getNumber(details.vatExtraCredit),
            vatPayable: getNumber(details.vatPayable),
            vatRefund: getNumber(details.vatRefund),
            cogsNoVat: getNumber(details.cogsNoVat),
            rentNoVat: getNumber(details.rentNoVat),
            otherNoVat: getNumber(details.otherNoVat),
            vatDeductibleCogs: getNumber(details.vatDeductibleCogs),
            vatDeductibleRent: getNumber(details.vatDeductibleRent),
            vatDeductibleOther: getNumber(details.vatDeductibleOther),
            netProfitAccounting: getNumber(details.netProfitAccounting),
            netProfitCash: getNumber(details.netProfitCash !== undefined ? details.netProfitCash : summary.netProfit),
            totalPayments: getNumber(details.totalPayments),
        };
    }

    function buildExplanation(regime, baseComponents) {
        if (!builders) {
            throw new Error('Модуль пояснений не инициализирован');
        }
        if (!regime) {
            throw new Error('Не переданы данные режима');
        }

        const builder = selectBuilder(regime);
        if (typeof builder !== 'function') {
            throw new Error(`Неизвестный режим для пояснения: ${regime.title || regime.id || 'без названия'}`);
        }

        const params = buildParams(regime, baseComponents);
        return builder(params);
    }

    global.Explanations = {
        buildExplanation,
    };
})(window);
