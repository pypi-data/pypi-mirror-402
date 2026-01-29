function enableAnchorLinks() {
    document.querySelectorAll("button.anchor-link").forEach((button) => {
        button.addEventListener("click", () => {
            const anchor = button.dataset.anchor;
            window.history.replaceState(undefined, undefined, "#" + anchor);
            navigator.clipboard.writeText(window.location.href);
            setTimeout(() => {
                // to close the tooltip and not trigger it again when reloading the URL
                button.parentElement.click();
            }, 500);
        });
    });
}

function trackAnchorLinks() {
    const buttons = document.querySelectorAll('button[data-track="true"]');
    if (buttons.length === 0) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                fetch("/api/tracking/event/", {
                    method: "POST",
                    body: JSON.stringify({
                        indicator: entry.target.dataset.indicator,
                        event: "vue-resume-indicateur",
                    }),
                });
                observer.unobserve(entry.target);
            }
        });
    });

    window.addEventListener(
        "scroll",
        () => {
            buttons.forEach((button) => observer.observe(button));
        },
        { once: true }
    );
}

export { enableAnchorLinks, trackAnchorLinks };
