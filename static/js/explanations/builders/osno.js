(function (global) {
    const format = global.ExplanationsFormat;
    if (!format) {
        return;
    }
    const { fmtMoney, fmtPercent, renderMarkdown } = format;

    function buildOsnoMarkdown(params) {
        const revenue = params.revenue || 0;
        const expenses = params.expenses || 0;
        const tax = params.tax || 0;
        const vat = params.vat || 0;
        const insurance = params.insurance || 0;
        const totalBurden = params.totalBurden || 0;
        const burdenPct = params.burdenPct || 0;
        const netProfit = params.netProfit || 0;
        const ownerExtra = params.ownerExtra || 0;
        const ownerExtraBase = params.ownerExtraBase || 0;
        const baseCost = params.baseCost || 0;
        const baseRent = params.baseRent || 0;
        const baseOther = params.baseOther || 0;
        const baseFot = params.baseFot || 0;
        const baseInsurStd = params.baseInsurStd || 0;
        const fixedContrib = params.fixedContrib || 0;
        const vatPurchasesPercent = params.vatPurchasesPercent || 0;
        const stockExtra = params.stockExtra || 0;
        const accumulatedVatCredit = params.accumulatedVatCredit || 0;
        const transitionMode = params.transitionMode || 'none';

        const stockPart = stockExtra > 0 ? stockExtra : 0;
        const profitBase = revenue - expenses - stockPart - vat;
        const positiveProfitBase = Math.max(profitBase, 0);
        const vatRate = 22;
        const vatCharged = revenue * vatRate / (100 + vatRate);
        const purchasesBase = baseCost * (vatPurchasesPercent / 100);
        const vatDeductible = purchasesBase * vatRate / (100 + vatRate);
        const burdenPercentText = fmtPercent(burdenPct);
        const ownerBaseLine = `${fmtMoney(ownerExtraBase)} ₽ − 300 000 ₽`;
        const insuranceBreakdown = `${fmtMoney(baseInsurStd)} ₽ + ${fmtMoney(ownerExtra)} ₽ + ${fmtMoney(fixedContrib)} ₽`;
        const creditPart = transitionMode === 'vat' && accumulatedVatCredit > 0
            ? ` − ${fmtMoney(accumulatedVatCredit)} ₽ (накопленный НДС)`
            : '';

        const lines = [
            '# Пояснение к расчёту налоговой нагрузки (ОСНО + НДС 22% (ООО))',
            '',
            '## 1. Вводные данные',
            'Режим: ОСНО + НДС 22% (ООО).',
            '',
            'Учитывается:',
            '- НДС 22%: начисленный с выручки минус входящий по закупкам.',
            '- Налог на прибыль 25% с базы после расходов, НДС и списания остатков (если применимо).',
            '- Страховые взносы: 30% от ФОТ, 1% с доходов свыше 300 000 ₽ и фиксированный взнос за ИП (учтён в расходах и добавлен в нагрузку).',
            '',
            '## 2. Доходы',
            `Доходы за период: ${fmtMoney(revenue)} ₽.`,
            '',
            '## 3. Расходы (без налогов)',
            `Итого расходы: ${fmtMoney(expenses)} ₽.`,
            '',
            'Структура расходов:',
            `- Себестоимость: ${fmtMoney(baseCost)} ₽.`,
            `- Аренда: ${fmtMoney(baseRent)} ₽.`,
            `- Прочие расходы: ${fmtMoney(baseOther)} ₽.`,
            `- ФОТ: ${fmtMoney(baseFot)} ₽.`,
            `- Страховые взносы 30% от ФОТ: ${fmtMoney(baseInsurStd)} ₽.`,
            `- Взнос 1% с доходов свыше 300 000 ₽: ${fmtMoney(ownerExtra)} ₽.`,
            `- Фиксированный взнос за ИП: ${fmtMoney(fixedContrib)} ₽.`,
            '',
            '## 4. Расчёт налога на прибыль 25%',
            'Налоговая база:',
            `${fmtMoney(revenue)} − ${fmtMoney(expenses)}${stockPart > 0 ? ` − ${fmtMoney(stockPart)} (остатки)` : ''} − ${fmtMoney(vat)} (НДС) = ${fmtMoney(profitBase)} ₽.`,
            '',
            'Налог на прибыль:',
            `${fmtMoney(positiveProfitBase)} × 25% = ${fmtMoney(tax)} ₽.`,
            '',
            '## 5. Расчёт НДС 22%',
            '',
            '### 5.1. НДС к начислению',
            'Формула: выручка × 22 / 122.',
            '',
            `${fmtMoney(revenue)} × 22 / 122 = ${fmtMoney(vatCharged)} ₽.`,
            '',
            '### 5.2. НДС к вычету по закупкам',
            `Себестоимость с НДС: ${fmtMoney(baseCost)} ₽.`,
            `Доля закупок с НДС: ${fmtPercent(vatPurchasesPercent)}%.`,
            '',
            'НДС к вычету:',
            `${fmtMoney(baseCost)} × ${fmtPercent(vatPurchasesPercent)}% × 22 / 122 = ${fmtMoney(vatDeductible)} ₽.`,
        ];

        if (transitionMode === 'vat' && accumulatedVatCredit > 0) {
            lines.push(
                '',
                `Дополнительный вычет при переходе: накопленный входящий НДС = ${fmtMoney(accumulatedVatCredit)} ₽.`,
            );
        }

        lines.push(
            '',
            '### 5.3. НДС к уплате',
            'НДС к уплате:',
            `${fmtMoney(vatCharged)} − ${fmtMoney(vatDeductible)}${creditPart} = ${fmtMoney(vat)} ₽.`,
            '',
            '## 6. Страховые взносы',
            '30% от ФОТ:',
            `${fmtMoney(baseFot)} × 30% = ${fmtMoney(baseInsurStd)} ₽.`,
            '',
            '1% с доходов свыше 300 000 ₽:',
            `(${ownerBaseLine}) × 1% = ${fmtMoney(ownerExtra)} ₽.`,
            '',
            'Фиксированный взнос за ИП:',
            `${fmtMoney(fixedContrib)} ₽ (учитывается в расходах и добавлен к нагрузке).`,
            '',
            'Итого страховых взносов:',
            `${insuranceBreakdown} = ${fmtMoney(insurance)} ₽.`,
            '',
            '## 7. Совокупная налоговая нагрузка',
            'Сумма налогов и взносов:',
            `${fmtMoney(tax)} + ${fmtMoney(vat)} + ${fmtMoney(insurance)} = ${fmtMoney(totalBurden)} ₽.`,
            '',
            'Доля от выручки:',
            `${fmtMoney(totalBurden)} / ${fmtMoney(revenue)} × 100% = ${burdenPercentText}%.`,
            '',
            '## 8. Чистая прибыль',
            'Формула:',
            'доходы − расходы (без налогов) − налог УСН − НДС.',
            '',
            'Расчёт:',
            `${fmtMoney(revenue)} − ${fmtMoney(expenses)} − ${fmtMoney(tax)} − ${fmtMoney(vat)} = ${fmtMoney(netProfit)} ₽.`,
        );

        return renderMarkdown(lines);
    }

    function buildOsnoIpMarkdown(params) {
        const revenue = params.revenue || 0;
        const expenses = params.expenses || 0;
        const ndflTax = params.ndflTax || params.tax || 0;
        const vat = params.vat || 0;
        const insurance = params.insurance || 0;
        const totalBurden = params.totalBurden || 0;
        const burdenPct = params.burdenPct || 0;
        const netProfit = params.netProfit || 0;
        const baseCost = params.baseCost || 0;
        const baseRent = params.baseRent || 0;
        const baseOther = params.baseOther || 0;
        const baseFot = params.baseFot || 0;
        const baseInsurStd = params.baseInsurStd || 0;
        const fixedContrib = params.fixedContrib || 0;
        const vatPurchasesPercent = params.vatPurchasesPercent || 0;
        const stockExtra = params.stockExtra || 0;
        const accumulatedVatCredit = params.accumulatedVatCredit || 0;
        const transitionMode = params.transitionMode || 'none';
        const incomeWithoutVat = params.incomeWithoutVat || 0;
        const expensesWithoutVat = params.expensesWithoutVat || 0;

        const stockPart = stockExtra > 0 ? stockExtra : 0;
        const vatRate = 22;
        const vatCharged = revenue * vatRate / (100 + vatRate);
        const purchasesBase = baseCost * (vatPurchasesPercent / 100);
        const vatDeductible = purchasesBase * vatRate / (100 + vatRate);
        const creditPart = transitionMode === 'vat' && accumulatedVatCredit > 0
            ? ` − ${fmtMoney(accumulatedVatCredit)} ₽ (накопленный НДС)`
            : '';
        const baseWithout1pct = Math.max(incomeWithoutVat - expensesWithoutVat - fixedContrib, 0);
        const excessOverThreshold = Math.max(baseWithout1pct - 300000, 0);
        const extra1pctCalc = excessOverThreshold * 0.01;
        const ndflBaseCalc = Math.max(baseWithout1pct - extra1pctCalc, 0);
        const insuranceBreakdown = `${fmtMoney(baseInsurStd)} ₽ + ${fmtMoney(extra1pctCalc)} ₽ + ${fmtMoney(fixedContrib)} ₽`;
        const burdenPercentText = fmtPercent(burdenPct);
        const ndflEffective = ndflBaseCalc > 0 ? (ndflTax / ndflBaseCalc * 100) : 0;
        const ndflScale = [
            'до 2 400 000 ₽ — 13%',
            '2 400 001–5 000 000 ₽ — 15%',
            '5 000 001–20 000 000 ₽ — 18%',
            '20 000 001–50 000 000 ₽ — 20%',
            'свыше 50 000 000 ₽ — 22%',
        ];

        const lines = [
            '# Пояснение к расчёту налоговой нагрузки (ОСНО + НДС 22% (ИП))',
            '',
            '## 1. Вводные данные',
            'Режим: ОСНО + НДС 22% (ИП).',
            '',
            'Учитывается:',
            '- НДС рассчитывается так же, как у юридических лиц: начисление с выручки и вычеты по закупкам.',
            '- Вместо налога на прибыль рассчитывается НДФЛ ИП по прогрессивной шкале.',
            '- В налоговую базу по НДФЛ включены расходы без НДС, фиксированный взнос ИП и дополнительный 1% взнос.',
            '',
            '## 2. Доходы',
            `Выручка (с НДС): ${fmtMoney(revenue)} ₽.`,
            `Доходы без НДС для расчёта НДФЛ: ${fmtMoney(incomeWithoutVat)} ₽.`,
            '',
            '## 3. Расходы (без НДС)',
            `Расходы, уменьшающие базу НДФЛ: ${fmtMoney(expensesWithoutVat)} ₽.`,
            '',
            'Структура расходов:',
            `- Себестоимость (без НДС по облагаемым закупкам): ${fmtMoney(baseCost - vatDeductible)} ₽.`,
            `- Аренда: ${fmtMoney(baseRent)} ₽.`,
            `- Прочие расходы: ${fmtMoney(baseOther)} ₽.`,
            `- ФОТ: ${fmtMoney(baseFot)} ₽.`,
            `- Страховые взносы 30% от ФОТ: ${fmtMoney(baseInsurStd)} ₽.`,
            ...(stockPart > 0 ? [`- Списание остатков товара: ${fmtMoney(stockPart)} ₽.`] : []),
            '',
            '## 4. База ИП и взнос 1% свыше 300 000 ₽',
            '1. База ИП без учёта 1%:',
            `   ${fmtMoney(incomeWithoutVat)} − ${fmtMoney(expensesWithoutVat)} − ${fmtMoney(fixedContrib)} = ${fmtMoney(baseWithout1pct)} ₽.`,
            ...(excessOverThreshold > 0
                ? [
                    '',
                    '2. Превышение над 300 000 ₽:',
                    `   ${fmtMoney(baseWithout1pct)} − 300 000 ₽ = ${fmtMoney(excessOverThreshold)} ₽.`,
                    '',
                    '3. Дополнительный взнос 1%:',
                    `   ${fmtMoney(excessOverThreshold)} × 1% = ${fmtMoney(extra1pctCalc)} ₽.`,
                    '',
                    '4. База для НДФЛ:',
                    `   ${fmtMoney(baseWithout1pct)} − ${fmtMoney(extra1pctCalc)} = ${fmtMoney(ndflBaseCalc)} ₽.`,
                    '',
                ]
                : [
                    '',
                    '2. База не превышает 300 000 ₽, взнос 1% = 0 ₽.',
                    '',
                    '3. База для НДФЛ:',
                    `   ${fmtMoney(baseWithout1pct)} = ${fmtMoney(ndflBaseCalc)} ₽.`,
                    '',
                ]),
            '## 5. Расчёт НДФЛ по прогрессивной шкале',
            `Ступени (2026): ${ndflScale.join(', ')}.`,
            '',
            `Итоговый НДФЛ: ${fmtMoney(ndflTax)} ₽ (эффективная ставка ${fmtPercent(ndflEffective)}%).`,
            '',
            '## 6. Расчёт НДС 22%',
            '',
            '### 6.1. НДС к начислению',
            `${fmtMoney(revenue)} × 22 / 122 = ${fmtMoney(vatCharged)} ₽.`,
            '',
            '### 6.2. НДС к вычету по закупкам',
            `Себестоимость с НДС: ${fmtMoney(baseCost)} ₽.`,
            `Доля закупок с НДС: ${fmtPercent(vatPurchasesPercent)}%.`,
            '',
            'НДС к вычету:',
            `${fmtMoney(baseCost)} × ${fmtPercent(vatPurchasesPercent)}% × 22 / 122 = ${fmtMoney(vatDeductible)} ₽.`,
        ];

        if (transitionMode === 'vat' && accumulatedVatCredit > 0) {
            lines.push(
                '',
                `Дополнительный вычет при переходе: накопленный входящий НДС = ${fmtMoney(accumulatedVatCredit)} ₽.`,
            );
        }

        lines.push(
            '',
            '### 6.3. НДС к уплате',
            `${fmtMoney(vatCharged)} − ${fmtMoney(vatDeductible)}${creditPart} = ${fmtMoney(vat)} ₽.`,
            '',
            '## 7. Страховые взносы',
            '30% от ФОТ:',
            `${fmtMoney(baseFot)} × 30% = ${fmtMoney(baseInsurStd)} ₽.`,
            '',
            '1% с доходов свыше 300 000 ₽:',
            ...(excessOverThreshold > 0
                ? [`   ${fmtMoney(excessOverThreshold)} × 1% = ${fmtMoney(extra1pctCalc)} ₽.`]
                : ['   превышения нет, взнос 1% = 0 ₽.']),
            '',
            'Фиксированный взнос ИП:',
            `${fmtMoney(fixedContrib)} ₽.`,
            '',
            'Итого страховых взносов:',
            `${insuranceBreakdown} = ${fmtMoney(insurance)} ₽.`,
            '',
            '## 8. Совокупная налоговая нагрузка',
            'Сумма налогов и взносов:',
            `${fmtMoney(ndflTax)} + ${fmtMoney(vat)} + ${fmtMoney(insurance)} = ${fmtMoney(totalBurden)} ₽.`,
            '',
            'Доля от выручки:',
            `${fmtMoney(totalBurden)} / ${fmtMoney(revenue)} × 100% = ${burdenPercentText}%.`,
            '',
            '## 9. Чистая прибыль',
            'Формула:',
            'доходы без НДС − расходы без НДС − НДФЛ − фиксированный взнос − взнос 1%.',
            '',
            'Расчёт:',
            `${fmtMoney(incomeWithoutVat)} − ${fmtMoney(expensesWithoutVat)} − ${fmtMoney(ndflTax)} − ${fmtMoney(extra1pctCalc)} − ${fmtMoney(fixedContrib)} = ${fmtMoney(netProfit)} ₽.`,
            );

        return renderMarkdown(lines);
    }

    global.ExplanationBuilders = global.ExplanationBuilders || {};
    global.ExplanationBuilders.buildOsnoMarkdown = buildOsnoMarkdown;
    global.ExplanationBuilders.buildOsnoIpMarkdown = buildOsnoIpMarkdown;
})(window);
