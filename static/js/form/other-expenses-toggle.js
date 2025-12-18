(function (global) {
    function init() {
        const revenueInput = document.getElementById('revenue');
        const percentInput = document.getElementById('other_percent');
        const amountInput = document.getElementById('other_amount');
        const modeInputs = document.getElementsByName('other_mode');

        if (!revenueInput || !percentInput || !amountInput || !modeInputs.length) {
            return;
        }

        function updateFromPercent() {
            const revenue = parseFloat(revenueInput.value) || 0;
            const percent = parseFloat(percentInput.value) || 0;
            amountInput.value = (revenue * percent / 100).toFixed(2);
        }

        function updateFromAmount() {
            const revenue = parseFloat(revenueInput.value) || 0;
            const amount = parseFloat(amountInput.value) || 0;
            percentInput.value = revenue > 0 ? (amount / revenue * 100).toFixed(2) : 0;
        }

        function refreshMode() {
            const mode = Array.from(modeInputs).find((input) => input.checked)?.value || 'percent';
            if (mode === 'percent') {
                percentInput.removeAttribute('readonly');
                amountInput.setAttribute('readonly', true);
                updateFromPercent();
            } else {
                amountInput.removeAttribute('readonly');
                percentInput.setAttribute('readonly', true);
                updateFromAmount();
            }
        }

        percentInput.addEventListener('input', updateFromPercent);
        amountInput.addEventListener('input', updateFromAmount);
        revenueInput.addEventListener('input', refreshMode);
        Array.from(modeInputs).forEach((input) => input.addEventListener('change', refreshMode));

        refreshMode();
    }

    global.OtherExpensesForm = {
        init,
    };
})(window);
