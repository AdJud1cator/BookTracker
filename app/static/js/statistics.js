document.addEventListener('DOMContentLoaded', function () {
    // --- Stat Cards ---
    fetch('/stats/summary')
        .then(res => res.json())
        .then(stats => {
            document.getElementById('statCards').innerHTML = `
        <div class="stat-card">
            <div class="stat-label">Total Books Read</div>
            <div class="stat-value">${stats.total_books_read}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Total Pages Read</div>
            <div class="stat-value">${stats.total_pages_read}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Favorite Genre</div>
            <div class="stat-value">${stats.favorite_genre || '-'}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Most-Read Author</div>
            <div class="stat-value">${stats.most_read_author || '-'}</div>
        </div>
        <div class="stat-break"></div>
        <div class="stat-card">
            <div class="stat-label">Longest Book Read</div>
            <div class="stat-value" style="font-size:1.15rem;">${stats.longest_book?.title || '-'}</div>
            <div class="stat-extra">${stats.longest_book?.pages ? stats.longest_book.pages + ' pages' : ''}</div>
        </div>
        <div class="stat-break"></div>
        <div class="stat-card">
            <div class="stat-label">Shortest Book Read</div>
            <div class="stat-value" style="font-size:1.15rem;">${stats.shortest_book?.title || '-'}</div>
            <div class="stat-extra">${stats.shortest_book?.pages ? stats.shortest_book.pages + ' pages' : ''}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Books Shared</div>
            <div class="stat-value">${stats.books_shared}</div>
        </div>
    `;
        });

    // --- Books Over Time Chart ---
    let booksOverTimeChart;
    function renderBooksOverTime(range) {
        fetch(`/stats/books_over_time?range=${range}`)
            .then(res => res.json())
            .then(booksOverTimeData => {
                const ctx = document.getElementById('booksOverTime');
                if (booksOverTimeChart) booksOverTimeChart.destroy();
                booksOverTimeChart = new Chart(ctx, {
                    type: range === 'years' || range === 'all' ? 'bar' : 'line',
                    data: {
                        labels: booksOverTimeData.labels,
                        datasets: [{
                            label: "Books Completed",
                            data: booksOverTimeData.data,
                            backgroundColor: "#0d6efd",
                            borderColor: "#0d6efd",
                            tension: 0.25,
                            fill: true
                        }]
                    },
                    options: {
                        scales: {
                            y: { beginAtZero: true, ticks: { stepSize: 1 } }
                        }
                    }
                });
            });
    }
    renderBooksOverTime('months');
    document.getElementById('booksTimeRange').addEventListener('change', function () {
        renderBooksOverTime(this.value);
    });

    // --- Pages Over Time Chart ---
    let pagesOverTimeChart;
    function renderPagesOverTime(range) {
        fetch(`/stats/pages_over_time?range=${range}`)
            .then(res => res.json())
            .then(pagesOverTimeData => {
                const ctx = document.getElementById('pagesOverTime');
                if (pagesOverTimeChart) pagesOverTimeChart.destroy();
                pagesOverTimeChart = new Chart(ctx, {
                    type: range === 'years' || range === 'all' ? 'bar' : 'line',
                    data: {
                        labels: pagesOverTimeData.labels,
                        datasets: [{
                            label: "Pages Read",
                            data: pagesOverTimeData.data,
                            backgroundColor: "#20c997",
                            borderColor: "#20c997",
                            tension: 0.25,
                            fill: true
                        }]
                    },
                    options: {
                        scales: {
                            y: { beginAtZero: true }
                        }
                    }
                });
            });
    }
    renderPagesOverTime('months');
    document.getElementById('pagesTimeRange').addEventListener('change', function () {
        renderPagesOverTime(this.value);
    });

    // --- Genre Pie Chart ---
    fetch('/stats/genres')
        .then(res => res.json())
        .then(genreData => {
            const genreLabels = Object.keys(genreData);
            const genreCounts = Object.values(genreData);
            new Chart(document.getElementById('genrePie'), {
                type: 'doughnut',
                data: {
                    labels: genreLabels,
                    datasets: [{
                        data: genreCounts,
                        backgroundColor: [
                            "#0d6efd", "#6610f2", "#6f42c1", "#d63384", "#fd7e14", "#ffc107", "#198754", "#20c997", "#0dcaf0", "#adb5bd", "#6c757d"
                        ]
                    }]
                },
                options: {
                    plugins: {
                        legend: { position: 'right' },
                        tooltip: {
                            callbacks: {
                                label: function (context) {
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const count = context.parsed;
                                    const percent = ((count / total) * 100).toFixed(1);
                                    return `${context.label}: ${count} (${percent}%)`;
                                }
                            }
                        }
                    }
                }
            });
        });

    // --- Status Pie Chart ---
    fetch('/stats/statuses')
        .then(res => res.json())
        .then(statusData => {
            new Chart(document.getElementById('statusPie'), {
                type: 'doughnut',
                data: {
                    labels: Object.keys(statusData),
                    datasets: [{
                        data: Object.values(statusData),
                        backgroundColor: ["#0d6efd", "#ffc107", "#6f42c1"]
                    }]
                },
                options: {
                    cutout: '65%',
                    plugins: {
                        legend: { position: 'right' },
                        tooltip: {
                            callbacks: {
                                label: function (context) {
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const count = context.parsed;
                                    const percent = ((count / total) * 100).toFixed(1);
                                    return `${context.label}: ${count} (${percent}%)`;
                                }
                            }
                        }
                    }
                }
            });
        });

    // --- Top Authors Bar Chart ---
    fetch('/stats/authors')
        .then(res => res.json())
        .then(authorData => {
            new Chart(document.getElementById('authorBar'), {
                type: 'bar',
                data: {
                    labels: Object.keys(authorData),
                    datasets: [{
                        label: "Books Read",
                        data: Object.values(authorData),
                        backgroundColor: "#0d6efd"
                    }]
                },
                options: {
                    indexAxis: 'y',
                    scales: {
                        x: { beginAtZero: true }
                    }
                }
            });
        });
});