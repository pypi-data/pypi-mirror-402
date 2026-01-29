function getIndicator() {
    return JSON.parse(document.getElementById("indicator-js").textContent);
}

async function downloadMethodo() {
    const indicator = getIndicator();
    const response = await fetch(`/api/indicators/${indicator.name}/methodo/`);

    if (!response.ok) {
        throw new Error("Failed to fetch the PDF file.");
    }

    // Create a download link
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${indicator.title}.pdf`;
    a.click();
    window.URL.revokeObjectURL(url);
}

document.addEventListener("DOMContentLoaded", () => {
    const buttons = document.querySelectorAll(".methodo-export-button");
    buttons.forEach((button) => {
        button.addEventListener("click", downloadMethodo);
    });
});
