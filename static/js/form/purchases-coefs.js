(function (global) {
    const monthIds = [
        'purchases_jan',
        'purchases_feb',
        'purchases_mar',
        'purchases_apr',
        'purchases_may',
        'purchases_jun',
        'purchases_jul',
        'purchases_aug',
        'purchases_sep',
        'purchases_oct',
        'purchases_nov',
        'purchases_dec',
    ];

    function recalcCoefficients() {
        let sum = 0;
        monthIds.forEach((id) => {
            const el = document.getElementById(id);
            if (!el) {
                return;
            }
            const val = parseFloat(String(el.value).replace(',', '.'));
            if (!Number.isNaN(val) && val > 0) {
                sum += val;
            }
        });

        const base = 1200;
        const percent = sum > 0 ? (sum / base) * 100 : 0;

        const sumEl = document.getElementById('coef-sum');
        const percentEl = document.getElementById('coef-percent');

        if (sumEl) {
            sumEl.textContent = sum.toFixed(2);
        }
        if (percentEl) {
            percentEl.textContent = percent.toFixed(1);
        }

        const summary = document.querySelector('.month-summary');
        if (summary) {
            if (percent === 0) {
                summary.style.color = '#e0e0e0';
            } else if (percent >= 90 && percent <= 110) {
                summary.style.color = '#6bcf7f';
            } else {
                summary.style.color = '#ffb86c';
            }
        }
    }

    function init() {
        monthIds.forEach((id) => {
            const el = document.getElementById(id);
            if (!el) {
                return;
            }
            el.addEventListener('input', recalcCoefficients);
        });
        recalcCoefficients();
    }

    global.PurchasesCoefsForm = {
        init,
    };
})(window);
