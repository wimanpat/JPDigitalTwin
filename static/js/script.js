document.addEventListener("DOMContentLoaded", () => {

    // ======================================================================
    // 1. SIDEBAR NAVIGATION (LEFT MENU)
    // ======================================================================
    document.querySelectorAll(".nav-item").forEach(item => {
        item.addEventListener("click", () => {
            const target = item.dataset.link;
            if (target) window.location.href = target;
        });
    });


    // ======================================================================
    // 2. ACTION-CARD NAVIGATION (COMMAND CENTER BUTTONS)
    // ======================================================================
    document.querySelectorAll(".action-card").forEach(card => {
        card.addEventListener("click", () => {
            const target = card.dataset.link;
            if (target) window.location.href = target;
        });
    });


    // ======================================================================
    // 3. SETTINGS PAGE TABS
    // ======================================================================
    const tabs = document.querySelectorAll(".settings-tab");
    const panels = document.querySelectorAll(".settings-content");

    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            panels.forEach(p => p.classList.remove("active"));

            tab.classList.add("active");
            const panel = document.getElementById(`tab-${tab.dataset.tab}`);
            if (panel) panel.classList.add("active");
        });
    });


    // ======================================================================
    // 4. THEME SWITCHER
    // ======================================================================
    const themeSelector = document.getElementById("themeSelector");

    // Load saved theme
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
        document.body.classList.add("dark-mode");
        if (themeSelector) themeSelector.value = "dark";
    }

    // When changed
    if (themeSelector) {
        themeSelector.addEventListener("change", () => {
            if (themeSelector.value === "dark") {
                document.body.classList.add("dark-mode");
                localStorage.setItem("theme", "dark");
            } else {
                document.body.classList.remove("dark-mode");
                localStorage.setItem("theme", "light");
            }
        });
    }


    // ======================================================================
    // 5. SOLVER SELECTION (SETTINGS → Solver drop-down)
    // ======================================================================
    const solverSelector = document.getElementById("solverSelector");

    if (solverSelector) {
        solverSelector.addEventListener("change", async () => {
            await fetch("/set-solver", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ solver: solverSelector.value })
            });
        });
    }


    // ======================================================================
    // 6. EXECUTE SOLVER BUTTON
    // ======================================================================
    const execBtn = document.getElementById("executeBtn");
    const execOutput = document.getElementById("execOutput");
    const mapBox = document.getElementById("gridMap");

    if (execBtn) {
        execBtn.addEventListener("click", async () => {
            execOutput.textContent = "Running solver...";

            const res = await fetch("/run-solver", { method: "POST" });
            const data = await res.json();

            if (!data.ok) {
                execOutput.textContent = "Error: " + data.error;
                return;
            }

            // Show readable output
            execOutput.innerHTML = data.actions.map(a => "• " + a).join("<br>");

            // Draw primary electrical topology
            renderGridSVG(data.nodes, data.primary_edges);
        });
    }


    // ======================================================================
    // 7. SVG GRID RENDERER  (Topology View + Command Center Snapshot)
    // ======================================================================
    function getNodeColor(type) {
    switch (type) {
        case "Solar": return "#f4d03f";          // Yellow
        case "Wind": return "#5dade2";           // Blue
        case "Nuclear": return "#a569bd";        // Purple
        case "Thermal": return "#e67e22";        // Orange
        case "Storage": return "#58d68d";        // Green
        case "Railway": return "#16a085";        // Teal
        case "Factory": return "#c0392b";        // Red
        case "Residential": return "#7f8c8d";    // Gray
        default: return "#000000";               // Black fallback
    }
}


    function renderGridSVG(nodes, edges) {
        if (!mapBox || !nodes) return;

        let svg = `<svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">`;

        // Draw edges (lines)
        edges.forEach(([src, dst]) => {
            const s = nodes[src];
            const d = nodes[dst];
            if (!s || !d) return;

            svg += `
                <line x1="${s.x}" y1="${s.y}"
                      x2="${d.x}" y2="${d.y}"
                      stroke="#888" stroke-width="3" />
            `;
        });

        // Draw nodes (circles + labels)
        for (const id in nodes) {
            const n = nodes[id];
            const color = getNodeColor(n.type);

        svg += `
    <circle cx="${n.x}" cy="${n.y}" r="12" fill="${color}" stroke="#222" stroke-width="2"></circle>
    <text x="${n.x + 18}" y="${n.y + 4}" font-size="13" fill="#000">${id}</text>
        `;

        }

        svg += `</svg>`;
        mapBox.innerHTML = svg;
    }

});
