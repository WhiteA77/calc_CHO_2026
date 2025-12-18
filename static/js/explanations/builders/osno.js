(function (global) {
    const format = global.ExplanationsFormat;
    if (!format) {
        return;
    }
    const { fmtMoney, fmtPercent, renderMarkdown } = format;

    function buildOsnoMarkdown(params) {
        const revenue = params.revenue || 0;
        const tax = params.tax || 0;
        const vatPayment = params.vat || 0;
        const insurance = params.insurance || 0;
        const totalBurden = params.totalBurden || 0;
        const burdenPct = params.burdenPct || 0;
        const baseCost = params.baseCost || 0;
        const baseRent = params.baseRent || 0;
        const baseOther = params.baseOther || 0;
        const baseFot = params.baseFot || 0;
        const baseInsurStd = params.baseInsurStd || 0;
        const incomeWithoutVat = params.incomeWithoutVat || 0;
        const expensesWithoutVatParam = params.expensesWithoutVat || 0;
        const vatPurchasesPercent = params.vatPurchasesPercent || 0;
        const rentSharePercent = (params.vatShareRent || 0) * 100;
        const otherSharePercent = (params.vatShareOther || 0) * 100;
        const stockExtra = params.stockExtra || 0;
        const accumulatedVatCredit = params.accumulatedVatCredit || 0;
        const transitionMode = params.transitionMode || 'none';
        const vatChargedParam = params.vatCharged;
        const vatDeductibleParam = params.vatDeductible;
        const vatPayableBalance = params.vatPayable !== undefined
            ? params.vatPayable
            : (params.netProfitAccounting || 0) - (params.netProfitCash || params.netProfit || 0);
        const vatRefund = params.vatRefund || 0;
        const cogsVat = params.vatDeductibleCogs || 0;
        const rentVat = params.vatDeductibleRent || 0;
        const otherVat = params.vatDeductibleOther || 0;
        const cogsNoVat = params.cogsNoVat || Math.max(baseCost - cogsVat, 0);
        const rentNoVat = params.rentNoVat || Math.max(baseRent - rentVat, 0);
        const otherNoVat = params.otherNoVat || Math.max(baseOther - otherVat, 0);
        const netProfitAccounting = params.netProfitAccounting !== undefined
            ? params.netProfitAccounting
            : ((incomeWithoutVat || 0) - expensesWithoutVatParam - tax);
        const netProfitCash = params.netProfitCash !== undefined
            ? params.netProfitCash
            : (netProfitAccounting - vatPayableBalance);
        const expensesWithoutVat = expensesWithoutVatParam
            || (cogsNoVat + rentNoVat + otherNoVat + baseFot + baseInsurStd + (stockExtra > 0 ? stockExtra : 0));
        const vatCharged = vatChargedParam || (revenue * 22 / 122);
        const vatDeductible = vatDeductibleParam || (cogsVat + rentVat + otherVat);
        const creditPart = transitionMode === 'vat' && accumulatedVatCredit > 0
            ? ` − ${fmtMoney(accumulatedVatCredit)} ₽ (накопленный НДС)`
            : '';
        const revenueNet = incomeWithoutVat > 0 ? incomeWithoutVat : Math.max(revenue - vatCharged, 0);
        const profitBase = revenueNet - expensesWithoutVat;
        const positiveProfitBase = Math.max(profitBase, 0);
        const burdenPercentText = fmtPercent(burdenPct);
        const stockPart = stockExtra > 0 ? stockExtra : 0;

        const lines = [
            '# Пояснение к расчёту налоговой нагрузки (ОСНО + НДС 22% (ООО))',
            '',
            '## 1. Вводные данные',
            'Режим: ОСНО + НДС 22% (ООО).',
            '',
            'Учитывается:',
            '- НДС 22%: начисленный с выручки минус входящий по закупкам (себестоимость, аренда, прочие).',
            '- Налог на прибыль 25% с базы после расходов без НДС (ФОТ и взносы входят целиком).',
            '- Страховые взносы: только 30% от ФОТ (для ООО нет взносов ИП).',
            '',
            '## 2. Доходы',
            `Выручка с НДС: ${fmtMoney(revenue)} ₽.`,
            'НДС, включённый в цену (метод «включённый НДС»):',
            `${fmtMoney(revenue)} × 22 / 122 = ${fmtMoney(vatCharged)} ₽.`,
            `Доходы без НДС (база для налога на прибыль): ${fmtMoney(revenueNet)} ₽.`,
            '',
            '## 3. Расходы для налога на прибыль (без НДС)',
            'Себестоимость, аренда и прочие расходы вводятся с НДС. Для базы по прибыли берём суммы без НДС.',
            `Итого расходы без НДС: ${fmtMoney(expensesWithoutVat)} ₽.`,
            '',
            'Структура расходов:',
            `- Себестоимость: ${fmtMoney(baseCost)} ₽ с НДС → ${fmtMoney(cogsNoVat)} ₽ без НДС (входящий НДС ${fmtMoney(cogsVat)} ₽, доля облагаемых закупок ${fmtPercent(vatPurchasesPercent)}%).`,
            `- Аренда: ${fmtMoney(baseRent)} ₽ с НДС → ${fmtMoney(rentNoVat)} ₽ без НДС (входящий НДС ${fmtMoney(rentVat)} ₽, доля с НДС ${fmtPercent(rentSharePercent)}%).`,
            `- Прочие: ${fmtMoney(baseOther)} ₽ с НДС → ${fmtMoney(otherNoVat)} ₽ без НДС (входящий НДС ${fmtMoney(otherVat)} ₽, доля с НДС ${fmtPercent(otherSharePercent)}%).`,
            `- ФОТ (без НДС): ${fmtMoney(baseFot)} ₽.`,
            `- Страховые взносы 30% от ФОТ: ${fmtMoney(baseInsurStd)} ₽.`,
            ...(stockPart > 0 ? [`- Списание остатков при переходе: ${fmtMoney(stockPart)} ₽.`] : []),
            '',
            '## 4. Расчёт налога на прибыль 25%',
            'Налог на прибыль = (доходы без НДС − расходы без НДС) × 25%.',
            'Налоговая база:',
            `${fmtMoney(revenueNet)} − ${fmtMoney(expensesWithoutVat)} = ${fmtMoney(profitBase)} ₽.`,
            '',
            'Налог на прибыль:',
            `${fmtMoney(positiveProfitBase)} × 25% = ${fmtMoney(tax)} ₽.`,
            '',
            '## 5. Расчёт НДС 22%',
            '',
            '### 5.1. НДС к начислению',
            'Формула та же: выручка × 22 / 122.',
            `${fmtMoney(revenue)} × 22 / 122 = ${fmtMoney(vatCharged)} ₽.`,
            '',
            '### 5.2. Входящий НДС к вычету',
            `- Себестоимость: ${fmtMoney(baseCost)} ₽ × ${fmtPercent(vatPurchasesPercent)}% × 22 / 122 = ${fmtMoney(cogsVat)} ₽.`,
            `- Аренда: ${fmtMoney(baseRent)} ₽ × ${fmtPercent(rentSharePercent)}% × 22 / 122 = ${fmtMoney(rentVat)} ₽.`,
            `- Прочие расходы: ${fmtMoney(baseOther)} ₽ × ${fmtPercent(otherSharePercent)}% × 22 / 122 = ${fmtMoney(otherVat)} ₽.`,
            `Итого входящий НДС: ${fmtMoney(vatDeductible)} ₽.`,
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
            'Расчёт НДС к уплате (баланс):',
            `${fmtMoney(vatCharged)} − ${fmtMoney(vatDeductible)}${creditPart} = ${fmtMoney(vatPayableBalance)} ₽.`,
        );

        if (vatPayableBalance < 0 && vatRefund > 0) {
            lines.push(`Получилась сумма к возмещению: ${fmtMoney(vatRefund)} ₽.`);
        } else {
            lines.push(`Фактический платёж в бюджет: ${fmtMoney(vatPayment)} ₽.`);
        }

        lines.push(
            '',
            '## 6. Страховые взносы',
            'ООО платит только взносы 30% с ФОТ:',
            `${fmtMoney(baseFot)} × 30% = ${fmtMoney(baseInsurStd)} ₽.`,
            '',
            'Итого страховых взносов:',
            `${fmtMoney(baseInsurStd)} ₽ = ${fmtMoney(insurance)} ₽.`,
            '',
            '## 7. Совокупные платежи и налоговая нагрузка',
            'Платежи = налог на прибыль + НДС к перечислению + страховые взносы.',
            `${fmtMoney(tax)} + ${fmtMoney(vatPayment)} + ${fmtMoney(insurance)} = ${fmtMoney(totalBurden)} ₽.`,
            '',
            'Доля от выручки:',
            `${fmtMoney(totalBurden)} / ${fmtMoney(revenue)} × 100% = ${burdenPercentText}%.`,
            '',
            '## 8. Чистая прибыль',
            '- Бухгалтерская (P&L, без учёта НДС к уплате):',
            `${fmtMoney(revenueNet)} − ${fmtMoney(expensesWithoutVat)} − ${fmtMoney(tax)} = ${fmtMoney(netProfitAccounting)} ₽.`,
            '',
            '- Денежная (cash, с учётом НДС как денежного потока):',
            `${fmtMoney(netProfitAccounting)} − ${fmtMoney(vatPayableBalance)} = ${fmtMoney(netProfitCash)} ₽.`,
        );

        return renderMarkdown(lines);
    }

    function buildOsnoIpMarkdown(params) {
        const revenue = params.revenue || 0;
        const vat = params.vat || 0;
        const insurance = params.insurance || 0;
        const totalBurden = params.totalBurden || 0;
        const burdenPct = params.burdenPct || 0;
        const baseCost = params.baseCost || 0;
        const baseRent = params.baseRent || 0;
        const baseOther = params.baseOther || 0;
        const baseFot = params.baseFot || 0;
        const baseInsurStd = params.baseInsurStd || 0;
        const fixedContrib = params.fixedContrib || 0;
        const ownerExtra = params.ownerExtra || 0;
        const ownerExtraBase = params.ownerExtraBase || 0;
        const vatPurchasesPercent = params.vatPurchasesPercent || 0;
        const stockExtra = params.stockExtra || 0;
        const accumulatedVatCredit = params.accumulatedVatCredit || 0;
        const transitionMode = params.transitionMode || 'none';
        const incomeWithoutVat = params.incomeWithoutVat || 0;
        const expensesWithoutVat = params.expensesWithoutVat || 0;
        const ndflTax = params.ndflTax || params.tax || 0;

        const stockPart = stockExtra > 0 ? stockExtra : 0;
        const vatRate = 22;
        const vatCharged = params.vatCharged || (revenue * vatRate / (100 + vatRate));
        const cogsVat = params.vatDeductibleCogs || (baseCost * (vatPurchasesPercent / 100) * vatRate / (100 + vatRate));
        const rentVat = params.vatDeductibleRent || 0;
        const otherVat = params.vatDeductibleOther || 0;
        const cogsNoVat = params.cogsNoVat || Math.max(baseCost - cogsVat, 0);
        const rentNoVat = params.rentNoVat || Math.max(baseRent - rentVat, 0);
        const otherNoVat = params.otherNoVat || Math.max(baseOther - otherVat, 0);
        const vatDeductible = params.vatDeductible || (cogsVat + rentVat + otherVat);
        const vatPayableBalance = params.vatPayable !== undefined
            ? params.vatPayable
            : (params.netProfitAccounting || (incomeWithoutVat - expensesWithoutVat - ndflTax)) - (params.netProfitCash || params.netProfit || 0);
        const vatRefund = params.vatRefund || 0;
        const rentSharePercent = (params.vatShareRent || 0) * 100;
        const otherSharePercent = (params.vatShareOther || 0) * 100;
        const netProfitAccounting = params.netProfitAccounting !== undefined
            ? params.netProfitAccounting
            : (incomeWithoutVat - expensesWithoutVat - ndflTax);
        const netProfitCash = params.netProfitCash !== undefined
            ? params.netProfitCash
            : (netProfitAccounting - vatPayableBalance);
        const creditPart = transitionMode === 'vat' && accumulatedVatCredit > 0
            ? ` − ${fmtMoney(accumulatedVatCredit)} ₽ (накопленный НДС)`
            : '';
        const baseWithout1pct = Math.max(incomeWithoutVat - expensesWithoutVat - fixedContrib, 0);
        const excessOverThreshold = Math.max(baseWithout1pct - 300000, 0);
        const extra1pctCalc = ownerExtra || excessOverThreshold * 0.01;
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
            '- В налоговую базу по НДФЛ включены расходы без НДС и фиксированный взнос ИП; дополнительный 1% рассчитывается отдельно.',
            '',
            '## 2. Доходы',
            `Выручка (с НДС): ${fmtMoney(revenue)} ₽.`,
            `Доходы без НДС для расчёта НДФЛ: ${fmtMoney(incomeWithoutVat)} ₽.`,
            '',
            '## 3. Расходы (без НДС)',
            `Расходы, уменьшающие базу НДФЛ: ${fmtMoney(expensesWithoutVat)} ₽.`,
            '',
            'Структура расходов:',
            `- Себестоимость (без НДС по облагаемым закупкам): ${fmtMoney(cogsNoVat)} ₽.`,
            `- Аренда (без НДС): ${fmtMoney(rentNoVat)} ₽.`,
            `- Прочие расходы (без НДС): ${fmtMoney(otherNoVat)} ₽.`,
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
            `- Себестоимость: ${fmtMoney(baseCost)} ₽ × ${fmtPercent(vatPurchasesPercent)}% × 22 / 122 = ${fmtMoney(cogsVat)} ₽.`,
            `- Аренда: ${fmtMoney(baseRent)} ₽ × ${fmtPercent(rentSharePercent)}% × 22 / 122 = ${fmtMoney(rentVat)} ₽.`,
            `- Прочие расходы: ${fmtMoney(baseOther)} ₽ × ${fmtPercent(otherSharePercent)}% × 22 / 122 = ${fmtMoney(otherVat)} ₽.`,
            `Итого входящий НДС: ${fmtMoney(vatDeductible)} ₽.`,
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
            `${fmtMoney(vatCharged)} − ${fmtMoney(vatDeductible)}${creditPart} = ${fmtMoney(vatPayableBalance)} ₽.`,
            vatPayableBalance < 0 && vatRefund > 0
                ? `Сумма к возмещению: ${fmtMoney(vatRefund)} ₽.`
                : `Платёж в бюджет: ${fmtMoney(vat)} ₽.`,
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
            '- Бухгалтерская (до НДС к уплате):',
            `${fmtMoney(incomeWithoutVat)} − ${fmtMoney(expensesWithoutVat)} − ${fmtMoney(ndflTax)} = ${fmtMoney(netProfitAccounting)} ₽.`,
            '',
            '- Денежная (cash) с учётом движения по НДС:',
            `${fmtMoney(netProfitAccounting)} − ${fmtMoney(vatPayableBalance)} = ${fmtMoney(netProfitCash)} ₽.`,
            );

        return renderMarkdown(lines);
    }

    global.ExplanationBuilders = global.ExplanationBuilders || {};
    global.ExplanationBuilders.buildOsnoMarkdown = buildOsnoMarkdown;
    global.ExplanationBuilders.buildOsnoIpMarkdown = buildOsnoIpMarkdown;
})(window);
