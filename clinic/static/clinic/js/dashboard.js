(function () {
    var canvas = document.getElementById('appointmentTrend');
    var labelsNode = document.getElementById('appointment-chart-labels');
    var valuesNode = document.getElementById('appointment-chart-data');
    var fallback = document.getElementById('chartFallback');

    if (!canvas || !labelsNode || !valuesNode) {
        return;
    }

    if (typeof Chart === 'undefined') {
        if (fallback) {
            fallback.hidden = false;
        }
        return;
    }

    var labels = JSON.parse(labelsNode.textContent);
    var values = JSON.parse(valuesNode.textContent);
    var styles = getComputedStyle(document.documentElement);

    function chartColors() {
        styles = getComputedStyle(document.documentElement);
        return {
            primary: styles.getPropertyValue('--primary').trim(),
            muted: styles.getPropertyValue('--text-muted').trim(),
            border: styles.getPropertyValue('--border').trim()
        };
    }

    var colors = chartColors();
    var trendChart = new Chart(canvas, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Appointments',
                data: values,
                borderColor: colors.primary,
                backgroundColor: colors.primary + '22',
                borderWidth: 3,
                fill: true,
                tension: 0.35,
                pointRadius: 3,
                pointHoverRadius: 5,
                pointBackgroundColor: colors.primary
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { intersect: false, mode: 'index' }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: colors.muted },
                    border: { color: colors.border }
                },
                y: {
                    beginAtZero: true,
                    ticks: { color: colors.muted, precision: 0 },
                    grid: { color: colors.border },
                    border: { display: false }
                }
            }
        }
    });

    var themeObserver = new MutationObserver(function () {
        var nextColors = chartColors();
        trendChart.data.datasets[0].borderColor = nextColors.primary;
        trendChart.data.datasets[0].backgroundColor = nextColors.primary + '22';
        trendChart.data.datasets[0].pointBackgroundColor = nextColors.primary;
        trendChart.options.scales.x.ticks.color = nextColors.muted;
        trendChart.options.scales.x.border.color = nextColors.border;
        trendChart.options.scales.y.ticks.color = nextColors.muted;
        trendChart.options.scales.y.grid.color = nextColors.border;
        trendChart.update();
    });

    themeObserver.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-theme', 'data-accent']
    });
})();
