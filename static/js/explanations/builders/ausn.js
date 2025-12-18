(function (global) {
    const format = global.ExplanationsFormat;
    if (!format) {
        return;
    }
    const { fmtMoney, fmtPercent, renderMarkdown } = format;

    function buildAusn8Markdown(params) {
        const revenue = params.revenue || 0;
        const expenses = params.expenses || 0;
        const tax = params.tax || 0;
        const totalBurden = params.totalBurden || 0;
        const burdenPct = params.burdenPct || 0;
        const netProfit = params.netProfit || 0;
        const baseCost = params.baseCost || 0;
        const baseRent = params.baseRent || 0;
        const baseOther = params.baseOther || 0;
        const baseFot = params.baseFot || 0;
        const fixedContrib = params.fixedContrib || 0;
        const burdenPercentText = fmtPercent(burdenPct);

        const lines = [
            '# Пояснение к расчёту налоговой нагрузки (АУСН 8%)',
            '',
            '## 1. Вводные данные',
            'Режим: АУСН 8% (доходы).',
            '',
            'Учитывается:',
            '- Налог 8% от выручки.',
            '- НДС не применяется.',
            '- Фиксированный взнос ИП за себя не уменьшает налог, но добавляется к итоговой нагрузке отдельной строкой.',
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
            '',
            '## 4. Расчёт налога АУСН 8%',
            'Налог по АУСН:',
            `${fmtMoney(revenue)} × 8% = ${fmtMoney(tax)} ₽.`,
            '',
            '## 5. Страховые взносы',
            'Фиксированный взнос за ИП:',
            `${fmtMoney(fixedContrib)} ₽ — платёж не влияет на налог АУСН и учитывается только в итоговой нагрузке.`,
            '',
            '## 6. Совокупная налоговая нагрузка',
            'Сумма налогов и взносов:',
            `${fmtMoney(tax)} + 0 ₽ + ${fmtMoney(fixedContrib)} = ${fmtMoney(totalBurden)} ₽.`,
            '',
            'Доля от выручки:',
            `${fmtMoney(totalBurden)} / ${fmtMoney(revenue)} × 100% = ${burdenPercentText}%.`,
            '',
            '## 7. Чистая прибыль',
            'Формула:',
            'доходы − расходы (без налогов) − налог АУСН − фиксированный взнос за ИП.',
            '',
            'Расчёт:',
            `${fmtMoney(revenue)} − ${fmtMoney(expenses)} − ${fmtMoney(tax)} − ${fmtMoney(fixedContrib)} = ${fmtMoney(netProfit)} ₽.`,
        ];

        return renderMarkdown(lines);
    }

    function buildAusn20Markdown(params) {
        const revenue = params.revenue || 0;
        const expenses = params.expenses || 0;
        const tax = params.tax || 0;
        const totalBurden = params.totalBurden || 0;
        const burdenPct = params.burdenPct || 0;
        const netProfit = params.netProfit || 0;
        const baseCost = params.baseCost || 0;
        const baseRent = params.baseRent || 0;
        const baseOther = params.baseOther || 0;
        const baseFot = params.baseFot || 0;
        const fixedContrib = params.fixedContrib || 0;
        const burdenPercentText = fmtPercent(burdenPct);
        const annualBase = revenue - expenses;
        const positiveBase = Math.max(annualBase, 0);
        const tax20 = positiveBase * 0.20;
        const minTax = revenue * 0.03;
        const comparisonText = tax20 > minTax ? 'больше' : (tax20 < minTax ? 'меньше' : 'равен');
        const chosenTax = tax20 > minTax ? tax20 : minTax;

        const lines = [
            '# Пояснение к расчёту налоговой нагрузки (АУСН 20%)',
            '',
            '## 1. Вводные данные',
            'Режим: АУСН 20% (доходы минус расходы).',
            '',
            'Учитывается:',
            '- Налог считается: 20% от прибыли, но не меньше 3% от выручки.',
            '- НДС не применяется.',
            '- Фиксированный взнос ИП за себя не уменьшает налог и добавляется к итоговой нагрузке отдельной строкой.',
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
            '',
            '## 4. Расчёт налога АУСН 20%',
            'Налоговая база за год:',
            `${fmtMoney(revenue)} ₽ − ${fmtMoney(expenses)} ₽ = ${fmtMoney(annualBase)} ₽.`,
            '',
            'Налог 20% от разницы:',
            `${fmtMoney(positiveBase)} ₽ × 20% = ${fmtMoney(tax20)} ₽.`,
            '',
            'Минимальный налог 3% от доходов:',
            `${fmtMoney(revenue)} ₽ × 3% = ${fmtMoney(minTax)} ₽.`,
            '',
            'Фактический налог к уплате:',
            `так как налог 20% (${fmtMoney(tax20)} ₽) ${comparisonText} минимального налога (${fmtMoney(minTax)} ₽), к уплате принимается ${fmtMoney(chosenTax)} ₽. В таблице показана именно эта сумма: ${fmtMoney(tax)} ₽ за год.`,
            '',
            '## 5. Страховые взносы',
            'Фиксированный взнос за ИП:',
            `${fmtMoney(fixedContrib)} ₽ — платёж не влияет на налоговую базу АУСН 20% и учитывается только в «налоговой нагрузке».`,
            '',
            '## 6. Совокупная налоговая нагрузка',
            'Сумма налогов и взносов:',
            `${fmtMoney(tax)} + 0 ₽ + ${fmtMoney(fixedContrib)} = ${fmtMoney(totalBurden)} ₽.`,
            '',
            'Доля от выручки:',
            `${fmtMoney(totalBurden)} / ${fmtMoney(revenue)} × 100% = ${burdenPercentText}%.`,
            '',
            '## 7. Чистая прибыль',
            'Формула:',
            'доходы − расходы (без налогов) − налог АУСН − фиксированный взнос за ИП.',
            '',
            'Расчёт:',
            `${fmtMoney(revenue)} − ${fmtMoney(expenses)} − ${fmtMoney(tax)} − ${fmtMoney(fixedContrib)} = ${fmtMoney(netProfit)} ₽.`,
        ];

        return renderMarkdown(lines);
    }

    global.ExplanationBuilders = global.ExplanationBuilders || {};
    global.ExplanationBuilders.buildAusn8Markdown = buildAusn8Markdown;
    global.ExplanationBuilders.buildAusn20Markdown = buildAusn20Markdown;
})(window);
