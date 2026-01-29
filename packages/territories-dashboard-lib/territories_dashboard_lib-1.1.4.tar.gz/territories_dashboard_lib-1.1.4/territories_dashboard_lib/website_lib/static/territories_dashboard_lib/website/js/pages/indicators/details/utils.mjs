function addEmptyGraphMessage(ctx) {
    const oldChart = Chart.getChart(ctx);
    if (oldChart) {
        oldChart.destroy();
    }
    const noMessageDiv =
        ctx.parentElement.parentElement.querySelector(".no-data-message");
    if (noMessageDiv) noMessageDiv.dataset.show = "true";
}

function removeEmptyGraphMessage(ctx) {
    const noMessageDiv =
        ctx.parentElement.parentElement.querySelector(".no-data-message");
    if (noMessageDiv) noMessageDiv.dataset.show = "false";
}

export { addEmptyGraphMessage, removeEmptyGraphMessage };
