(function (global) {
    function init() {
        const empInput = document.getElementById('employees');
        const salaryInput = document.getElementById('salary');
        const fotAnnualInput = document.getElementById('fot_annual');
        const fotModeInputs = document.getElementsByName('fot_mode');

        if (!empInput || !salaryInput || !fotAnnualInput || !fotModeInputs.length) {
            return;
        }

        function getFotMode() {
            const checked = Array.from(fotModeInputs).find((input) => input.checked);
            return checked ? checked.value : 'staff';
        }

        function updateFotFromStaff() {
            if (getFotMode() !== 'staff') {
                return;
            }
            const emp = parseFloat(empInput.value) || 0;
            const sal = parseFloat(salaryInput.value) || 0;
            const annual = emp * sal * 12;
            fotAnnualInput.value = annual ? annual.toFixed(2) : '0.00';
        }

        function refreshFotMode() {
            const mode = getFotMode();
            if (mode === 'staff') {
                empInput.removeAttribute('readonly');
                salaryInput.removeAttribute('readonly');
                fotAnnualInput.setAttribute('readonly', true);
                updateFotFromStaff();
            } else {
                fotAnnualInput.removeAttribute('readonly');
                empInput.removeAttribute('readonly');
                salaryInput.removeAttribute('readonly');
            }
        }

        empInput.addEventListener('input', updateFotFromStaff);
        salaryInput.addEventListener('input', updateFotFromStaff);
        Array.from(fotModeInputs).forEach((input) => input.addEventListener('change', refreshFotMode));

        refreshFotMode();
    }

    global.FotModeForm = {
        init,
    };
})(window);
