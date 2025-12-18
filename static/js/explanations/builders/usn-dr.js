(function (global) {
    const format = global.ExplanationsFormat;
    if (!format) {
        return;
    }
    const { fmtMoney, fmtPercent, renderMarkdown } = format;

    function buildUsnDrMarkdown(params, options) {
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
        const stockExtra = params.stockExtra || 0;
        const usnRegularTax = params.usnRegularTax || 0;
        const usnMinTax = params.usnMinTax || 0;
        const vatPurchasesPercent = params.vatPurchasesPercent || 0;
        const accumulatedVatCredit = params.accumulatedVatCredit || 0;
        const transitionMode = params.transitionMode || 'none';
        const title = options.title;
        const includeVatSection = Boolean(options.includeVatSection);
        const vatRate = options.vatRate;
        const burdenPercentText = fmtPercent(burdenPct);
        const ownerBaseLine = `${fmtMoney(ownerExtraBase)} ₽ − 300 000 ₽`;
        const insuranceBreakdown = `${fmtMoney(baseInsurStd)} ₽ + ${fmtMoney(ownerExtra)} ₽ + ${fmtMoney(fixedContrib)} ₽`;
        const stockPart = stockExtra > 0 ? stockExtra : 0;
        const usnBase = revenue - expenses - stockPart;
        const positiveBase = Math.max(usnBase, 0);
        const regularTax = usnRegularTax || positiveBase * 0.15;
        const minTax = usnMinTax || revenue * 0.01;
        const usesMinTax = Math.abs(tax - minTax) < Math.abs(tax - regularTax);

        const lines = [
            `# Пояснение к расчёту налоговой нагрузки (${title})`,
            '',
            '## 1. Вводные данные',
            `Режим: ${title}.`,
            '',
            'Учитывается:',
            '- УСН 15% с прибыли (доходы − расходы).',
            includeVatSection
                ? (vatRate === 5
                    ? '- НДС 5%: начисляется с выручки без вычетов.'
                    : '- НДС 22%: начисленный с выручки минус входящий по закупкам.')
                : '- НДС не применяется.',
            '- Страховые взносы: 30% от ФОТ, 1% с доходов свыше 300 000 ₽ и фиксированный взнос за ИП (учитывается и в расходах, и в итоговой нагрузке).',
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
        ];

        if (stockPart > 0) {
            lines.push(
                '',
                `Дополнительно: при переходе учтено единовременное списание остатков товара на ${fmtMoney(stockPart)} ₽ (уменьшает налоговую базу, но не входит в расходы).`,
            );
        }

        lines.push(
            '',
            '## 4. Расчёт налога УСН 15%',
            'Налоговая база:',
            `${fmtMoney(revenue)} − ${fmtMoney(expenses)}${stockPart > 0 ? ` − ${fmtMoney(stockPart)} (остатки)` : ''} = ${fmtMoney(usnBase)} ₽.`,
            '',
            'Налог по УСН 15%:',
            `${fmtMoney(positiveBase)} × 15% = ${fmtMoney(regularTax)} ₽.`,
            '',
            'Минимальный налог 1% от доходов:',
            `${fmtMoney(revenue)} × 1% = ${fmtMoney(minTax)} ₽.`,
            '',
            usesMinTax
                ? `Так как налог по ставке 15% (${fmtMoney(regularTax)} ₽) меньше минимального, к уплате принимается минимальный налог ${fmtMoney(tax)} ₽.`
                : 'Так как налог по ставке 15% не меньше минимального, к уплате берётся результат по ставке 15%.',
        );

        if (includeVatSection && vatRate === 5) {
            const vatCharged = revenue * vatRate / (100 + vatRate);
            lines.push(
                '',
                '## 5. Расчёт НДС 5%',
                '',
                '### 5.1. НДС к начислению',
                'Формула: выручка × 5 / 105.',
                '',
                `${fmtMoney(revenue)} × 5 / 105 = ${fmtMoney(vatCharged)} ₽.`,
                '',
                '### 5.2. НДС к вычету',
                'В этом режиме вычеты по НДС не применяются (льгота 5%).',
                '',
                '### 5.3. НДС к уплате',
                'НДС к уплате:',
                `${fmtMoney(vatCharged)} − 0 ₽ = ${fmtMoney(vat)} ₽.`,
            );
        } else if (includeVatSection && vatRate === 22) {
            const vatCharged = revenue * vatRate / (100 + vatRate);
            const purchasesBase = baseCost * (vatPurchasesPercent / 100);
            const vatDeductible = purchasesBase * vatRate / (100 + vatRate);
            const creditPart = accumulatedVatCredit > 0 && transitionMode === 'vat'
                ? ` − ${fmtMoney(accumulatedVatCredit)} ₽ (накопленный НДС)`
                : '';

            lines.push(
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
            );

            if (accumulatedVatCredit > 0 && transitionMode === 'vat') {
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
            );
        }

        lines.push(
            '',
            `${includeVatSection ? '## 6.' : '## 5.'} Страховые взносы`,
            '30% от ФОТ:',
            `${fmtMoney(baseFot)} × 30% = ${fmtMoney(baseInsurStd)} ₽.`,
            '',
            '1% с доходов свыше 300 000 ₽:',
            `(${ownerBaseLine}) × 1% = ${fmtMoney(ownerExtra)} ₽.`,
            '',
            'Фиксированный взнос за ИП:',
            `${fmtMoney(fixedContrib)} ₽ (уменьшает налоговую базу и добавлен в итоговую нагрузку).`,
            '',
            'Итого страховых взносов:',
            `${insuranceBreakdown} = ${fmtMoney(insurance)} ₽.`,
            '',
            `${includeVatSection ? '## 7.' : '## 6.'} Совокупная налоговая нагрузка`,
            'Сумма налогов и взносов:',
            `${fmtMoney(tax)} + ${fmtMoney(vat)} + ${fmtMoney(insurance)} = ${fmtMoney(totalBurden)} ₽.`,
            '',
            'Доля от выручки:',
            `${fmtMoney(totalBurden)} / ${fmtMoney(revenue)} × 100% = ${burdenPercentText}%.`,
            '',
            `${includeVatSection ? '## 8.' : '## 7.'} Чистая прибыль`,
            'Формула:',
            includeVatSection
                ? 'доходы − расходы (без налогов) − налог УСН − НДС.'
                : 'доходы − расходы (без налогов) − налог УСН.',
            '',
            'Расчёт:',
            includeVatSection
                ? `${fmtMoney(revenue)} − ${fmtMoney(expenses)} − ${fmtMoney(tax)} − ${fmtMoney(vat)} = ${fmtMoney(netProfit)} ₽.`
                : `${fmtMoney(revenue)} − ${fmtMoney(expenses)} − ${fmtMoney(tax)} = ${fmtMoney(netProfit)} ₽.`,
        );

        return renderMarkdown(lines);
    }

    function buildUsnDrNoVatMarkdown(params) {
        return buildUsnDrMarkdown(params, {
            title: 'УСН «доходы минус расходы» 15%',
            includeVatSection: false,
        });
    }

    function buildUsnDr5Markdown(params) {
        return buildUsnDrMarkdown(params, {
            title: 'УСН «доходы минус расходы» 15% + НДС 5%',
            includeVatSection: true,
            vatRate: 5,
        });
    }

    function buildUsnDr22Markdown(params) {
        return buildUsnDrMarkdown(params, {
            title: 'УСН «доходы минус расходы» 15% + НДС 22%',
            includeVatSection: true,
            vatRate: 22,
        });
    }

    global.ExplanationBuilders = global.ExplanationBuilders || {};
    global.ExplanationBuilders.buildUsnDrNoVatMarkdown = buildUsnDrNoVatMarkdown;
    global.ExplanationBuilders.buildUsnDr5Markdown = buildUsnDr5Markdown;
    global.ExplanationBuilders.buildUsnDr22Markdown = buildUsnDr22Markdown;
})(window);
