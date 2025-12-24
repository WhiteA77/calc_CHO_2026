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
        patent: () => builders.buildPatentMarkdown,
    };

    const STOCK_ELIGIBLE = new Set([
        'usn_profit_no_vat',
        'usn_profit_vat_5',
        'usn_profit_vat_22',
        'osno_ooo',
        'osno_ip',
        'patent',
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
        const isPatent = normalized.includes('патент') || normalized.includes('psn') || normalized.includes('псн');

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
        if (isPatent && builders.buildPatentMarkdown) {
            return builders.buildPatentMarkdown;
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
        const baseInsuranceStd = getNumber(
            base.insuranceStandard !== undefined
                ? base.insuranceStandard
                : base.insurance_standard !== undefined
                    ? base.insurance_standard
                    : 0,
        );
        const fixedContrib = getNumber(
            insurance.fixedContrib !== undefined
                ? insurance.fixedContrib
                : base.fixedContrib !== undefined
                    ? base.fixedContrib
                    : base.fixed_contrib,
        );
        const patentCostYearValue = details.patent_cost_year !== undefined
            ? details.patent_cost_year
            : base.patentCostYear !== undefined
                ? base.patentCostYear
                : base.patent_cost_year !== undefined
                    ? base.patent_cost_year
                    : details.tax_before_deduction;
        const patentCostYear = getNumber(patentCostYearValue);
        const baseFot = getNumber(
            base.annualFot !== undefined
                ? base.annualFot
                : base.fot !== undefined
                    ? base.fot
                    : 0,
        );
        const payroll = getNumber(
            base.payroll !== undefined
                ? base.payroll
                : baseFot,
        );
        const employeesCount = getNumber(
            base.employeesCount !== undefined
                ? base.employeesCount
                : base.employees !== undefined
                    ? base.employees
                    : 0,
        );

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
            baseFot,
            baseInsurStd: baseInsuranceStd,
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
            fixedContrib,
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
            patentCostYear,
            patentTaxBeforeDeduction: getNumber(details.tax_before_deduction),
            patentTaxDeduction: getNumber(details.tax_deduction),
            patentTaxDeductionLimit: getNumber(details.tax_deduction_limit),
            patentTaxPayable: getNumber(details.tax_payable !== undefined ? details.tax_payable : summary.tax),
            patentPvdPeriod: getNumber(details.patent_pvd_period),
            patentPvdUsed: getNumber(details.patent_pvd_used),
            patentPvdAuto: getNumber(details.patent_pvd_auto),
            patentPvdSource: typeof details.patent_pvd_source === 'string' ? details.patent_pvd_source : '',
            patentDeductibleContrib: getNumber(details.deductible_contrib),
            contribSelf: getNumber(details.contrib_self !== undefined ? details.contrib_self : fixedContrib),
            contribWorkers: getNumber(details.contrib_workers !== undefined ? details.contrib_workers : baseInsuranceStd),
            contribSelfExtra: getNumber(details.contrib_self_extra !== undefined ? details.contrib_self_extra : details.owner_extra),
            contribSelfExtraBase: getNumber(
                details.contrib_self_extra_base !== undefined ? details.contrib_self_extra_base : details.owner_extra_base,
            ),
            hasEmployeesPatentLimit: getNumber(details.has_employees_patent_limit),
            payroll,
            employeesCount,
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
