(function (global) {
    function initModules() {
        const modules = [
            global.TransitionModeForm,
            global.PurchasesCoefsForm,
            global.OtherExpensesForm,
            global.FotModeForm,
            global.TableDetailsToggle,
            global.RegimesTableSort,
            global.TopResults,
        ];

        modules.forEach((module) => {
            if (module && typeof module.init === 'function') {
                module.init();
            }
        });
    }

    if (document.readyState !== 'loading') {
        initModules();
    } else {
        document.addEventListener('DOMContentLoaded', initModules);
    }
})(window);
