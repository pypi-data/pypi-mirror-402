function trackVisibleIndicators() {
    // Track the most visible card over time
    let currentMostVisibleId = null;
    let mostVisibleCounter = 0;
    let lastTrackedIndicator = null;
    const REQUIRED_CONSECUTIVE_CHECKS = 3; // 3 seconds at 1 check per second

    function resetTracking() {
        currentMostVisibleId = null;
        mostVisibleCounter = 0;
    }

    function fetchTracking(indicatorId) {
        fetch("/api/tracking/event/", {
            method: "POST",
            body: JSON.stringify({
                indicator: indicatorId,
                event: "attention-sur-resume-indicateur",
            }),
        });
    }

    function getMostVisibleIndicatorCard() {
        const indicatorCards = document.querySelectorAll(".indicator-card");
        const visibilityData = [];

        indicatorCards.forEach((card, index) => {
            const rect = card.getBoundingClientRect();
            const windowHeight =
                window.innerHeight || document.documentElement.clientHeight;
            const windowWidth =
                window.innerWidth || document.documentElement.clientWidth;

            // Calculate the visible portion of the card
            const visibleTop = Math.max(0, rect.top);
            const visibleBottom = Math.min(windowHeight, rect.bottom);
            const visibleLeft = Math.max(0, rect.left);
            const visibleRight = Math.min(windowWidth, rect.right);

            // Calculate visible area (only if card is actually visible)
            const visibleHeight = Math.max(0, visibleBottom - visibleTop);
            const visibleWidth = Math.max(0, visibleRight - visibleLeft);
            const visibleArea = visibleHeight * visibleWidth;

            // Calculate total card area
            const totalArea = rect.width * rect.height;

            const visibilityRatio = visibleArea / totalArea;

            let isVisible = visibleArea > 0;
            // Check if visible area is at least 20% of total area
            if (visibilityRatio < 0.2) {
                isVisible = false;
            }
            // 40% for the first card
            if (index == 0 && visibilityRatio < 0.4) {
                isVisible = false;
            }
            if (isVisible) {
                visibilityData.push({
                    card,
                    visibleArea,
                    totalArea,
                });
            }
        });

        // No visible cards - reset tracking
        if (visibilityData.length === 0) {
            resetTracking();
            return;
        }

        // Sort by visible area (descending)
        visibilityData.sort((a, b) => b.visibleArea - a.visibleArea);

        const mostVisible = visibilityData[0];

        // Check if there are other visible cards and if the most visible is at least twice as visible
        if (visibilityData.length > 1) {
            const secondMostVisible = visibilityData[1];
            if (mostVisible.visibleArea < 2 * secondMostVisible.visibleArea) {
                resetTracking();
                return;
            }
        }

        const indicatorId = mostVisible.card.getAttribute("data-indicator");

        // Check if it's the same card as before
        if (indicatorId === currentMostVisibleId) {
            mostVisibleCounter++;

            // Add the class only after 3 consecutive seconds
            if (
                mostVisibleCounter >= REQUIRED_CONSECUTIVE_CHECKS &&
                indicatorId !== lastTrackedIndicator
            ) {
                fetchTracking(indicatorId);
                lastTrackedIndicator = indicatorId;
            }
        } else {
            // Different card - reset counter
            currentMostVisibleId = indicatorId;
            mostVisibleCounter = 1;
        }
    }

    // Start tracking only after first scroll
    window.addEventListener(
        "scroll",
        () => {
            setInterval(() => {
                getMostVisibleIndicatorCard();
            }, 1000);
        },
        { once: true }
    );
}

export { trackVisibleIndicators };
