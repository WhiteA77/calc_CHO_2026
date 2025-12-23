(function (global) {
    const format = global.ExplanationsFormat;
    if (!format) {
        return;
    }
    const { fmtMoney, fmtPercent, renderMarkdown } = format;

    function buildPatentMarkdown(params) {
        const revenue = params.revenue || 0;
        const expenses = params.expensesWithoutVat || params.expenses || 0;
        const patentCost = params.patentCostYear || params.tax || 0;
        const taxBeforeDeduction = params.patentTaxBeforeDeduction || patentCost;
        const taxDeduction = params.patentTaxDeduction || 0;
        const taxLimit = params.patentTaxDeductionLimit || taxBeforeDeduction;
        const taxPayable = params.tax || Math.max(taxBeforeDeduction - taxDeduction, 0);
        const contribSelf = params.contribSelf || params.fixedContrib || 0;
        const contribWorkers = params.contribWorkers || params.baseInsurStd || 0;
        const contribSelfExtra = params.contribSelfExtra || params.ownerExtra || 0;
        const contribBase = params.contribSelfExtraBase || params.ownerExtraBase || 0;
        const totalContrib = contribSelf + contribWorkers;
        const netProfitCash = params.netProfitCash !== undefined ? params.netProfitCash : params.netProfit;
        const hasEmployeesLimit = (params.hasEmployeesPatentLimit || 0) > 0;
        const limitText = hasEmployeesLimit ? '50%' : '100%';

        const lines = [
            '# Пояснение к расчёту налоговой нагрузки (ПСН, патент)',
            '',
            '## 1. Вводные данные',
            `Выручка за год: ${fmtMoney(revenue)} ₽.`,
            `Стоимость патента до уменьшения: ${fmtMoney(taxBeforeDeduction)} ₽.`,
            '',
            '## 2. Расходы бизнеса',
            `Основные расходы (себестоимость + аренда + прочие + ФОТ): ${fmtMoney(expenses)} ₽.`,
            `Страховые взносы за работников (30% от ФОТ): ${fmtMoney(contribWorkers)} ₽.`,
            '',
            '## 3. Взносы ИП за себя',
            `Фиксированный взнос: ${fmtMoney(contribSelf - contribSelfExtra)} ₽.`,
            `Дополнительно 1% с прибыли до взносов (${fmtMoney(contribBase)} ₽ − 300 000 ₽): ${fmtMoney(contribSelfExtra)} ₽.`,
            `Итого взносов ИП: ${fmtMoney(contribSelf)} ₽.`,
            '',
            '## 4. Уменьшение стоимости патента',
            `Сумма взносов, доступная для зачёта: ${fmtMoney(totalContrib)} ₽.`,
            `Лимит уменьшения (${limitText} от стоимости патента): ${fmtMoney(taxLimit)} ₽.`,
            `Фактическое уменьшение: ${fmtMoney(taxDeduction)} ₽.`,
            `Налог к уплате после уменьшения: ${fmtMoney(taxPayable)} ₽.`,
            '',
            '## 5. Итоговые платежи и прибыль',
            `Совокупные платежи (налог + взносы): ${fmtMoney(taxPayable)} ₽ + ${fmtMoney(totalContrib)} ₽ = ${fmtMoney(taxPayable + totalContrib)} ₽.`,
            `Чистая прибыль (cash): ${fmtMoney(revenue)} ₽ − ${fmtMoney(expenses)} ₽ − ${fmtMoney(taxPayable)} ₽ − ${fmtMoney(totalContrib)} ₽ = ${fmtMoney(netProfitCash)} ₽.`,
        ];

        return renderMarkdown(lines);
    }

    global.ExplanationBuilders = global.ExplanationBuilders || {};
    global.ExplanationBuilders.buildPatentMarkdown = buildPatentMarkdown;
})(window);
