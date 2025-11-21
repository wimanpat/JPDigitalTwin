document.addEventListener("DOMContentLoaded", () => {

    // ===================== SIDEBAR NAVIGATION ======================
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(item => {
        const text = item.textContent.trim();

        if (text === "Command Center") item.onclick = () => window.location.href = "/";
        if (text === "Topology View") item.onclick = () => window.location.href = "/topology";
        if (text === "Operations View") item.onclick = () => window.location.href = "/operations";
        if (text === "System Settings") item.onclick = () => window.location.href = "/settings";
    });


    // ===================== SETTINGS PAGE TABS ======================
    const tabs = document.querySelectorAll(".settings-tab");
    const panels = document.querySelectorAll(".settings-content");

    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            panels.forEach(p => p.classList.remove("active"));

            tab.classList.add("active");
            document.getElementById(`tab-${tab.dataset.tab}`).classList.add("active");
        });
    });


    // ===================== THEME SWITCHER ======================
    const themeSelector = document.getElementById("themeSelector");
    const savedTheme = localStorage.getItem("theme");

    if (savedTheme === "dark") {
        document.body.classList.add("dark-mode");
        if (themeSelector) themeSelector.value = "dark";
    }

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


    // ===================== SOLVER SELECTOR DROPDOWN ======================
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


    // ===================== EXECUTE SOLVER BUTTON ======================
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

            execOutput.innerHTML = data.actions.map(a => "• " + a).join("<br>");
            renderGridSVG(data.nodes, data.primary_edges);

        });
    }


    // ===================== GRID RENDERING ======================
    function renderGridSVG(nodes, edges) {
    if (!mapBox || !nodes) return;

    let svg = `<svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">`;

    // Draw edges
    edges.forEach(e => {
        const s = nodes[e[0]];
        const d = nodes[e[1]];
        svg += `
            <line x1="${s.x}" y1="${s.y}"
                  x2="${d.x}" y2="${d.y}"
                  stroke="#888" stroke-width="3" />
        `;
    });

    // Draw nodes
    for (const id in nodes) {
        const n = nodes[id];
        svg += `
            <circle cx="${n.x}" cy="${n.y}" r="10" fill="#000"></circle>
            <text x="${n.x + 14}" y="${n.y + 4}" font-size="12">${id}</text>
        `;
    }

    svg += "</svg>";
    mapBox.innerHTML = svg;
}


});

document.addEventListener("DOMContentLoaded", () => {

    // ---- SIDEBAR NAVIGATION ----
    document.querySelectorAll(".nav-item").forEach(item => {
        item.addEventListener("click", () => {
            const link = item.dataset.link;
            if (link) window.location.href = link;
        });
    });

    // ---- FIX: CENTER ACTION CARD NAVIGATION ----
    document.querySelectorAll(".action-card").forEach(card => {
        card.addEventListener("click", () => {
            const link = card.dataset.link;
            if (link) window.location.href = link;
        });
    });

});

