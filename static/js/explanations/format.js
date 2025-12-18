(function (global) {
    function fmtMoney(value) {
        const num = Number(value) || 0;
        return num.toLocaleString('ru-RU', { maximumFractionDigits: 0 });
    }

    function fmtPercent(value) {
        const num = Number(value) || 0;
        return num.toLocaleString('ru-RU', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }

    function renderMarkdown(lines) {
        return `<pre class="markdown-explanation">${lines.join('\n')}\n</pre>`;
    }

    global.ExplanationsFormat = {
        fmtMoney,
        fmtPercent,
        renderMarkdown,
    };
})(window);
