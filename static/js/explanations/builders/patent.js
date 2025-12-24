(function (global) {
    const format = global.ExplanationsFormat;
    if (!format) {
        return;
    }
    const { fmtMoney, fmtPercent, renderMarkdown } = format;

    function buildPatentMarkdown(params) {
        const revenue = params.revenue || 0;
        const expenses = params.expensesWithoutVat || params.expenses || 0;
        const patentCost = params.patentCostYear !== undefined
            ? params.patentCostYear
            : (params.patentTaxBeforeDeduction !== undefined ? params.patentTaxBeforeDeduction : 0);
        const taxBeforeDeduction = params.patentTaxBeforeDeduction !== undefined
            ? params.patentTaxBeforeDeduction
            : patentCost;
        const fixedContrib = params.fixedContrib || 0;
        const contribWorkers = params.contribWorkers || params.baseInsurStd || 0;
        const ownerExtra = params.contribSelfExtra || params.ownerExtra || 0;
        const pvdUsed = params.patentPvdUsed || params.contribSelfExtraBase || params.ownerExtraBase || 0;
        const manualPvd = params.patentPvdPeriod || 0;
        const patentPvdSource = params.patentPvdSource || (params.patentPvdAuto ? 'auto' : '');
        const isAutoPvd = patentPvdSource === 'auto';
        const contribSelfTotal = fixedContrib + ownerExtra;
        const totalContrib = contribSelfTotal + contribWorkers;
        const netProfitCash = params.netProfitCash !== undefined ? params.netProfitCash : params.netProfit;
        const hasEmployeesLimit = (params.hasEmployeesPatentLimit || 0) > 0;
        const employeesCount = params.employeesCount || params.employees || 0;
        const payroll = params.payroll || params.baseFot || 0;
        const hasEmployees =
            hasEmployeesLimit
            || contribWorkers > 0
            || employeesCount > 0
            || payroll > 0;
        const limitPercent = hasEmployees ? 0.5 : 1;
        const limitPercentText = hasEmployees ? '50% (есть работники)' : '100% (нет работников)';
        const calculatedLimit = taxBeforeDeduction * limitPercent;
        const taxLimit = params.patentTaxDeductionLimit !== undefined ? params.patentTaxDeductionLimit : calculatedLimit;
        const patentReduction = Math.min(totalContrib, taxLimit);
        const taxDeduction = params.patentTaxDeduction !== undefined ? params.patentTaxDeduction : patentReduction;
        const taxPayableCalculated = Math.max(taxBeforeDeduction - taxDeduction, 0);
        const taxPayable = params.patentTaxPayable !== undefined
            ? params.patentTaxPayable
            : params.tax !== undefined
                ? params.tax
                : taxPayableCalculated;
        const baseForShare = taxBeforeDeduction || 0;
        const patentReducedShare = baseForShare > 0 ? patentReduction / baseForShare : 0;
        const patentRatePercent = 6;

        const limitFromCost = patentCost * limitPercent;
        const displayLimit = limitFromCost > 0 ? limitFromCost : taxLimit;
        const lines = [
            '# Пояснение к расчёту налоговой нагрузки (ПСН, патент)',
            '',
            '## 1. Общие параметры',
            `Выручка за год: ${fmtMoney(revenue)} ₽ (на величину патента не влияет, налог фиксирован).`,
            `Стоимость патента на год (ввод пользователя): ${fmtMoney(patentCost)} ₽.`,
            `Основные расходы (себестоимость + аренда + прочие + ФОТ): ${fmtMoney(expenses)} ₽ — для ПСН они не влияют на налог, но уменьшают чистую прибыль.`,
            '',
            '## 2. Страховые взносы',
            `Взносы за работников (30% от ФОТ): ${fmtMoney(contribWorkers)} ₽.`,
            isAutoPvd
                ? `ПВД для расчёта 1% берётся автоматически из стоимости патента: ${fmtMoney(patentCost)} ₽ / ${patentRatePercent}% = ${fmtMoney(pvdUsed)} ₽.`
                : `ПВД для расчёта 1% введён вручную: ${fmtMoney(manualPvd || pvdUsed)} ₽ (если не заполнить, он берётся из стоимости патента).`,
            `Фиксированный взнос ИП: ${fmtMoney(fixedContrib)} ₽.`,
            `1% свыше 300 000 ₽ от ПВД: max(${fmtMoney(pvdUsed)} ₽ − 300 000 ₽, 0) × 1% = ${fmtMoney(ownerExtra)} ₽.`,
            `Итого взносы ИП за себя (фиксированный + 1%): ${fmtMoney(contribSelfTotal)} ₽.`,
            '',
            '## 3. Общая сумма взносов',
            `Всего взносов, доступных для уменьшения патента: ${fmtMoney(totalContrib)} ₽ (работники + ИП).`,
            '',
            '## 4. Уменьшение стоимости патента',
            hasEmployees
                ? 'Есть сотрудники или выплачивался ФОТ, поэтому закон ограничивает уменьшение патента 50% его стоимости.'
                : 'Нет сотрудников и не выплачивался ФОТ, поэтому патент можно уменьшить на всю стоимость (100%).',
            limitFromCost > 0
                ? `Лимит уменьшения составляет ${limitPercentText}: ${fmtMoney(patentCost)} ₽ × ${hasEmployees ? '50%' : '100%'} = ${fmtMoney(limitFromCost)} ₽.`
                : `Лимит уменьшения задаётся правилом ${hasEmployees ? '50%' : '100%'} от стоимости патента.`,
            `Правило расчёта суммы уменьшения: берём меньшую величину из доступных взносов (${fmtMoney(totalContrib)} ₽) и рассчитанного лимита (${fmtMoney(displayLimit)} ₽).`,
            `Налог к уплате после уменьшения: ${fmtMoney(taxPayable)} ₽.`,
            '',
            '## 5. Итог',
            `Обязательные платежи (налог после уменьшения + взносы): ${fmtMoney(taxPayable)} ₽ + ${fmtMoney(totalContrib)} ₽ = ${fmtMoney(taxPayable + totalContrib)} ₽.`,
            `Чистая прибыль (cash): ${fmtMoney(revenue)} ₽ − ${fmtMoney(expenses)} ₽ − ${fmtMoney(taxPayable)} ₽ − ${fmtMoney(totalContrib)} ₽ = ${fmtMoney(netProfitCash)} ₽.`,
        ];

        return renderMarkdown(lines);
    }

    global.ExplanationBuilders = global.ExplanationBuilders || {};
    global.ExplanationBuilders.buildPatentMarkdown = buildPatentMarkdown;
})(window);
