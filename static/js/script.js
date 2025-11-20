document.addEventListener("DOMContentLoaded", () => {
    const execBtn = document.getElementById("executeBtn");
    const execOutput = document.getElementById("execOutput");
    const mapBox = document.getElementById("gridMap");

    if (!execBtn) return;

    execBtn.addEventListener("click", async () => {
        execOutput.textContent = "Running solver...";

        const res = await fetch("/run-solver", { method: "POST" });
        const data = await res.json();

        if (!data.ok) {
            execOutput.textContent = "Error: " + data.error;
            return;
        }

        // Show actions
        execOutput.innerHTML = data.actions.map(a => "• " + a).join("<br>");

        // Draw the grid
        renderGridSVG(data.nodes, data.flows);
    });

    function renderGridSVG(nodes, flows) {
        if (!mapBox || !nodes) return;

        let svg = `<svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">`;

        // Draw flows
        flows.forEach(f => {
            const s = nodes[f.src];
            const d = nodes[f.dst];
            if (!s || !d) return;

            svg += `
                <line x1="${s.x}" y1="${s.y}"
                      x2="${d.x}" y2="${d.y}"
                      stroke="red" stroke-width="3" />
            `;
        });

        // Draw nodes
        for (const id in nodes) {
            const n = nodes[id];
            svg += `
                <circle cx="${n.x}" cy="${n.y}" r="10" fill="#333"></circle>
                <text x="${n.x + 14}" y="${n.y + 4}" font-size="12">${id}</text>
            `;
        }

        svg += "</svg>";
        mapBox.innerHTML = svg;
    }
});
