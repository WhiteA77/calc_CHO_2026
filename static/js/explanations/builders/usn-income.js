(function (global) {
    const format = global.ExplanationsFormat;
    if (!format) {
        return;
    }
    const { fmtMoney, fmtPercent, renderMarkdown } = format;

    function buildUsnIncomeMarkdown(params) {
        const revenue = params.revenue || 0;
        const expenses = params.expenses || 0;
        const tax = params.tax || 0;
        const taxInitial = params.taxInitial || revenue * 0.06;
        const taxReduction = params.taxReduction || 0;
        const taxReductionLimit = params.taxReductionLimit || taxInitial * 0.5;
        const insurance = params.insurance || 0;
        const totalBurden = params.totalBurden || 0;
        const burdenPct = params.burdenPct || 0;
        const netProfit = params.netProfit || 0;
        const baseCost = params.baseCost || 0;
        const baseRent = params.baseRent || 0;
        const baseOther = params.baseOther || 0;
        const baseFot = params.baseFot || 0;
        const baseInsurStd = params.baseInsurStd || 0;
        const ownerExtra = params.ownerExtra || 0;
        const ownerExtraBase = params.ownerExtraBase || 0;
        const fixedContrib = params.fixedContrib || 0;
        const fixedContribReduction = params.fixedContribReduction || 0;
        const burdenPercentText = fmtPercent(burdenPct);
        const insuranceBreakdown = `${fmtMoney(baseInsurStd)} ₽ + ${fmtMoney(ownerExtra)} ₽ + ${fmtMoney(fixedContrib)} ₽`;
        const ownerBaseLine = `${fmtMoney(ownerExtraBase)} ₽ − 300 000 ₽`;
        const reductionLimited = baseInsurStd >= taxReductionLimit && Math.abs(taxReduction - taxReductionLimit) <= 0.01;
        const hasEmployees = baseFot > 0;
        const fixedReductionIntro = hasEmployees
            ? 'Так как есть сотрудники, фиксированный взнос может уменьшить налог не более чем на 50% от начисленной суммы.'
            : 'Сотрудников нет, поэтому фиксированный взнос может уменьшить налог вплоть до 0 ₽.';
        const standardReductionApplied = Math.min(baseInsurStd, taxReductionLimit);
        const fixedAvailable = hasEmployees
            ? Math.max(taxReductionLimit - standardReductionApplied, 0)
            : Math.max(taxInitial - standardReductionApplied, 0);

        const lines = [
            '# Пояснение к расчёту налоговой нагрузки (УСН Доходы 6%)',
            '',
            '## 1. Вводные данные',
            'Режим: УСН 6% (доходы).',
            '',
            'Учитывается:',
            '- Налог УСН 6% от выручки.',
            '- НДС не применяется.',
            '- Страховые взносы: 30% от ФОТ, 1% с доходов свыше 300 000 ₽ и фиксированный взнос за ИП.',
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
            '## 4. Расчёт налога УСН 6%',
            'Налог без уменьшения:',
            `${fmtMoney(revenue)} × 6% = ${fmtMoney(taxInitial)} ₽.`,
            '',
            'Сумма страховых взносов, участвующая в уменьшении налога (30% от ФОТ):',
            `${fmtMoney(baseInsurStd)} ₽.`,
            '',
            'Максимальное уменьшение (не более 50% от начисленного налога):',
            `${fmtMoney(taxInitial)} ₽ × 50% = ${fmtMoney(taxReductionLimit)} ₽.`,
        ];

        if (reductionLimited) {
            lines.push(
                '',
                'Фактическое уменьшение налога:',
                `так как сумма страховых взносов (30% от ФОТ) = ${fmtMoney(baseInsurStd)} ₽ превышает или равна максимальному допустимому уменьшению (${fmtMoney(taxReductionLimit)} ₽), налог может быть уменьшен только на ${fmtMoney(taxReduction)} ₽.`,
            );
        } else {
            lines.push(
                '',
                'Фактическое уменьшение налога:',
                `так как сумма страховых взносов (30% от ФОТ) = ${fmtMoney(baseInsurStd)} ₽ меньше максимального допустимого уменьшения (${fmtMoney(taxReductionLimit)} ₽), налог уменьшается на ${fmtMoney(taxReduction)} ₽.`,
            );
        }

        lines.push(
            '',
            'Фиксированный взнос за ИП:',
            `Сумма взноса: ${fmtMoney(fixedContrib)} ₽.`,
            fixedReductionIntro,
            hasEmployees
                ? `Доступный лимит уменьшения за счёт фиксированного взноса: ${fmtMoney(fixedAvailable)} ₽, использовано ${fmtMoney(fixedContribReduction)} ₽.`
                : `В расчёте налог уменьшен на ${fmtMoney(fixedContribReduction)} ₽ за счёт этого взноса.`,
            'Сам взнос при этом всё равно уплачивается и добавлен к общей налоговой нагрузке.',
            '',
            'Налог к уплате по УСН 6%:',
            `${fmtMoney(taxInitial)} ₽ − ${fmtMoney(taxReduction)} ₽ = ${fmtMoney(tax)} ₽.`,
            '',
            '## 5. Страховые взносы',
            '30% от ФОТ:',
            `${fmtMoney(baseFot)} × 30% = ${fmtMoney(baseInsurStd)} ₽.`,
            '',
            '1% с доходов свыше 300 000 ₽:',
            `(${ownerBaseLine}) × 1% = ${fmtMoney(ownerExtra)} ₽.`,
            '',
            'Фиксированный взнос за ИП:',
            `${fmtMoney(fixedContrib)} ₽ (указан во вводных данных).`,
            '',
            'Итого страховых взносов:',
            `${insuranceBreakdown} = ${fmtMoney(insurance)} ₽.`,
            '',
            '## 6. Совокупная налоговая нагрузка',
            'Сумма налогов и взносов:',
            `${fmtMoney(tax)} + 0 ₽ + ${fmtMoney(insurance)} = ${fmtMoney(totalBurden)} ₽.`,
            '',
            'Доля от выручки:',
            `${fmtMoney(totalBurden)} / ${fmtMoney(revenue)} × 100% = ${burdenPercentText}%.`,
            '',
            '## 7. Чистая прибыль',
            'Формула:',
            'доходы − расходы (без налогов) − налог УСН.',
            '',
            'Расчёт:',
            `${fmtMoney(revenue)} − ${fmtMoney(expenses)} − ${fmtMoney(tax)} = ${fmtMoney(netProfit)} ₽.`,
        );

        return renderMarkdown(lines);
    }

    function buildUsnIncome5Markdown(params) {
        const revenue = params.revenue || 0;
        const expenses = params.expenses || 0;
        const tax = params.tax || 0;
        const taxInitial = params.taxInitial || revenue * 0.06;
        const taxReduction = params.taxReduction || 0;
        const taxReductionLimit = params.taxReductionLimit || taxInitial * 0.5;
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
        const ownerExtra = params.ownerExtra || 0;
        const ownerExtraBase = params.ownerExtraBase || 0;
        const fixedContrib = params.fixedContrib || 0;
        const fixedContribReduction = params.fixedContribReduction || 0;
        const burdenPercentText = fmtPercent(burdenPct);
        const ownerBaseLine = `${fmtMoney(ownerExtraBase)} ₽ − 300 000 ₽`;
        const insuranceBreakdown = `${fmtMoney(baseInsurStd)} ₽ + ${fmtMoney(ownerExtra)} ₽ + ${fmtMoney(fixedContrib)} ₽`;
        const vatRate = 5;
        const vatCharged = revenue * vatRate / (100 + vatRate);
        const reductionLimited = baseInsurStd >= taxReductionLimit && Math.abs(taxReduction - taxReductionLimit) <= 0.01;
        const hasEmployees = baseFot > 0;
        const fixedReductionIntro = hasEmployees
            ? 'Так как есть сотрудники, фиксированный взнос может уменьшить налог не более чем на 50% от начисленной суммы.'
            : 'Сотрудников нет, поэтому фиксированный взнос может уменьшить налог вплоть до 0 ₽.';
        const standardReductionApplied = Math.min(baseInsurStd, taxReductionLimit);
        const fixedAvailable = hasEmployees
            ? Math.max(taxReductionLimit - standardReductionApplied, 0)
            : Math.max(taxInitial - standardReductionApplied, 0);

        const lines = [
            '# Пояснение к расчёту налоговой нагрузки (УСН Доходы 6% + НДС 5%)',
            '',
            '## 1. Вводные данные',
            'Режим: УСН 6% + НДС 5%.',
            '',
            'Учитывается:',
            '- Налог УСН 6% от выручки.',
            '- НДС 5% начисляется с выручки (без вычетов).',
            '- Страховые взносы: 30% от ФОТ, 1% с доходов свыше 300 000 ₽ и фиксированный взнос за ИП.',
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
            '',
            '## 4. Расчёт налога УСН 6%',
            'Налог без уменьшения:',
            `${fmtMoney(revenue)} × 6% = ${fmtMoney(taxInitial)} ₽.`,
            '',
            'Сумма страховых взносов, участвующая в уменьшении налога (30% от ФОТ):',
            `${fmtMoney(baseInsurStd)} ₽.`,
            '',
            'Максимальное уменьшение (не более 50% от начисленного налога):',
            `${fmtMoney(taxInitial)} ₽ × 50% = ${fmtMoney(taxReductionLimit)} ₽.`,
        ];

        if (reductionLimited) {
            lines.push(
                '',
                'Фактическое уменьшение налога:',
                `так как сумма страховых взносов (30% от ФОТ) = ${fmtMoney(baseInsurStd)} ₽ превышает или равна максимальному допустимому уменьшению (${fmtMoney(taxReductionLimit)} ₽), налог может быть уменьшен только на ${fmtMoney(taxReduction)} ₽.`,
            );
        } else {
            lines.push(
                '',
                'Фактическое уменьшение налога:',
                `так как сумма страховых взносов (30% от ФОТ) = ${fmtMoney(baseInsurStd)} ₽ меньше максимального допустимого уменьшения (${fmtMoney(taxReductionLimit)} ₽), налог уменьшается на ${fmtMoney(taxReduction)} ₽.`,
            );
        }

        lines.push(
            '',
            'Фиксированный взнос за ИП:',
            `Сумма взноса: ${fmtMoney(fixedContrib)} ₽.`,
            fixedReductionIntro,
            hasEmployees
                ? `Доступный лимит уменьшения за счёт фиксированного взноса: ${fmtMoney(fixedAvailable)} ₽, использовано ${fmtMoney(fixedContribReduction)} ₽.`
                : `В расчёте налог уменьшен на ${fmtMoney(fixedContribReduction)} ₽ за счёт этого взноса.`,
            'Сам взнос при этом остаётся отдельным обязательным платежом и добавлен к налоговой нагрузке.',
            '',
            'Налог к уплате по УСН 6%:',
            `${fmtMoney(taxInitial)} ₽ − ${fmtMoney(taxReduction)} ₽ = ${fmtMoney(tax)} ₽.`,
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
            '',
            '## 6. Страховые взносы',
            '30% от ФОТ:',
            `${fmtMoney(baseFot)} × 30% = ${fmtMoney(baseInsurStd)} ₽.`,
            '',
            '1% с доходов свыше 300 000 ₽:',
            `(${ownerBaseLine}) × 1% = ${fmtMoney(ownerExtra)} ₽.`,
            '',
            'Фиксированный взнос за ИП:',
            `${fmtMoney(fixedContrib)} ₽ (указан во вводных данных).`,
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

    function buildUsnIncome22Markdown(params) {
        const revenue = params.revenue || 0;
        const expenses = params.expenses || 0;
        const tax = params.tax || 0;
        const taxInitial = params.taxInitial || revenue * 0.06;
        const taxReduction = params.taxReduction || 0;
        const taxReductionLimit = params.taxReductionLimit || taxInitial * 0.5;
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
        const ownerExtra = params.ownerExtra || 0;
        const ownerExtraBase = params.ownerExtraBase || 0;
        const fixedContrib = params.fixedContrib || 0;
        const fixedContribReduction = params.fixedContribReduction || 0;
        const vatPurchasesPercent = params.vatPurchasesPercent || 0;
        const accumulatedVatCredit = params.accumulatedVatCredit || 0;
        const transitionMode = params.transitionMode || 'none';
        const burdenPercentText = fmtPercent(burdenPct);
        const ownerBaseLine = `${fmtMoney(ownerExtraBase)} ₽ − 300 000 ₽`;
        const insuranceBreakdown = `${fmtMoney(baseInsurStd)} ₽ + ${fmtMoney(ownerExtra)} ₽ + ${fmtMoney(fixedContrib)} ₽`;
        const vatRate = 22;
        const vatCharged = revenue * vatRate / (100 + vatRate);
        const purchasesBase = baseCost * (vatPurchasesPercent / 100);
        const vatDeductible = purchasesBase * vatRate / (100 + vatRate);
        const extraCreditApplied = transitionMode === 'vat' ? accumulatedVatCredit : 0;
        const creditPart = extraCreditApplied > 0 ? ` − ${fmtMoney(extraCreditApplied)} ₽ (накопленный НДС)` : '';
        const reductionLimited = baseInsurStd >= taxReductionLimit && Math.abs(taxReduction - taxReductionLimit) <= 0.01;
        const hasEmployees = baseFot > 0;
        const fixedReductionIntro = hasEmployees
            ? 'Так как есть сотрудники, фиксированный взнос может уменьшить налог не более чем на 50% от начисленной суммы.'
            : 'Сотрудников нет, поэтому фиксированный взнос может уменьшить налог вплоть до 0 ₽.';
        const standardReductionApplied = Math.min(baseInsurStd, taxReductionLimit);
        const fixedAvailable = hasEmployees
            ? Math.max(taxReductionLimit - standardReductionApplied, 0)
            : Math.max(taxInitial - standardReductionApplied, 0);

        const lines = [
            '# Пояснение к расчёту налоговой нагрузки (УСН Доходы 6% + НДС 22%)',
            '',
            '## 1. Вводные данные',
            'Режим: УСН 6% + НДС 22%.',
            '',
            'Учитывается:',
            '- Налог УСН 6% от выручки.',
            '- НДС 22% начисляется как на ОСНО: с выручки минус входящий НДС по закупкам.',
            '- Страховые взносы: 30% от ФОТ, 1% с доходов свыше 300 000 ₽ и фиксированный взнос за ИП.',
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
            '',
            '## 4. Расчёт налога УСН 6%',
            'Налог без уменьшения:',
            `${fmtMoney(revenue)} × 6% = ${fmtMoney(taxInitial)} ₽.`,
            '',
            'Сумма страховых взносов, участвующая в уменьшении налога (30% от ФОТ):',
            `${fmtMoney(baseInsurStd)} ₽.`,
            '',
            'Максимальное уменьшение (не более 50% от начисленного налога):',
            `${fmtMoney(taxInitial)} ₽ × 50% = ${fmtMoney(taxReductionLimit)} ₽.`,
        ];

        if (reductionLimited) {
            lines.push(
                '',
                'Фактическое уменьшение налога:',
                `так как сумма страховых взносов (30% от ФОТ) = ${fmtMoney(baseInsurStd)} ₽ превышает или равна максимальному допустимому уменьшению (${fmtMoney(taxReductionLimit)} ₽), налог может быть уменьшен только на ${fmtMoney(taxReduction)} ₽.`,
            );
        } else {
            lines.push(
                '',
                'Фактическое уменьшение налога:',
                `так как сумма страховых взносов (30% от ФОТ) = ${fmtMoney(baseInsurStd)} ₽ меньше максимального допустимого уменьшения (${fmtMoney(taxReductionLimit)} ₽), налог уменьшается на ${fmtMoney(taxReduction)} ₽.`,
            );
        }

        lines.push(
            '',
            'Фиксированный взнос за ИП:',
            `Сумма взноса: ${fmtMoney(fixedContrib)} ₽.`,
            fixedReductionIntro,
            hasEmployees
                ? `Доступный лимит уменьшения за счёт фиксированного взноса: ${fmtMoney(fixedAvailable)} ₽, использовано ${fmtMoney(fixedContribReduction)} ₽.`
                : `В расчёте налог уменьшен на ${fmtMoney(fixedContribReduction)} ₽ за счёт этого взноса.`,
            'Сам взнос при этом остаётся отдельным обязательным платежом и добавлен к налоговой нагрузке.',
            '',
            'Налог к уплате по УСН 6%:',
            `${fmtMoney(taxInitial)} ₽ − ${fmtMoney(taxReduction)} ₽ = ${fmtMoney(tax)} ₽.`,
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

        if (extraCreditApplied > 0) {
            lines.push(
                '',
                'Дополнительный вычет при переходе:',
                `накопленный входящий НДС = ${fmtMoney(extraCreditApplied)} ₽.`,
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
            `${fmtMoney(fixedContrib)} ₽ (указан во вводных данных).`,
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

    global.ExplanationBuilders = global.ExplanationBuilders || {};
    global.ExplanationBuilders.buildUsnIncomeMarkdown = buildUsnIncomeMarkdown;
    global.ExplanationBuilders.buildUsnIncome5Markdown = buildUsnIncome5Markdown;
    global.ExplanationBuilders.buildUsnIncome22Markdown = buildUsnIncome22Markdown;
})(window);
