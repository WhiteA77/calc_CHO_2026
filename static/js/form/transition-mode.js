(function (global) {
    function init() {
        const modeInputs = document.querySelectorAll('input[name="transition_mode"]');
        const vatInput = document.getElementById('accumulated_vat_credit');
        const stockInput = document.getElementById('stock_expense_amount');

        if (!modeInputs.length || !vatInput || !stockInput) {
            return;
        }

        function setReadonly(el, state) {
            if (!el) {
                return;
            }
            if (state) {
                el.setAttribute('readonly', true);
            } else {
                el.removeAttribute('readonly');
            }
        }

        function resetValue(el) {
            if (!el) {
                return;
            }
            el.value = '0';
        }

        function handleModeChange() {
            const checked = Array.from(modeInputs).find((input) => input.checked);
            const mode = checked ? checked.value : 'none';

            if (mode === 'vat') {
                setReadonly(vatInput, false);
                setReadonly(stockInput, true);
                resetValue(stockInput);
            } else if (mode === 'stock') {
                setReadonly(stockInput, false);
                setReadonly(vatInput, true);
                resetValue(vatInput);
            } else {
                setReadonly(vatInput, true);
                setReadonly(stockInput, true);
                resetValue(vatInput);
                resetValue(stockInput);
            }
        }

        modeInputs.forEach((input) => input.addEventListener('change', handleModeChange));
        handleModeChange();
    }

    global.TransitionModeForm = {
        init,
    };
})(window);
