// Draws each plotly chart on the page. A chart is a container with a
// data-chart attribute naming the json_script element that holds its spec.
document.querySelectorAll("[data-chart]").forEach(function (el) {
    var spec = JSON.parse(document.getElementById(el.dataset.chart).textContent);
    Plotly.newPlot(el, spec.data, spec.layout, spec.config);
});
