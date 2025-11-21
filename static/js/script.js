document.addEventListener("DOMContentLoaded", () => {

    // ======================================================================
    // 1. SIDEBAR NAVIGATION
    // ======================================================================
    document.querySelectorAll(".nav-item").forEach(item => {
        item.addEventListener("click", () => {
            const target = item.dataset.link;
            if (target) window.location.href = target;
        });
    });

    // ======================================================================
    // 2. ACTION-CARD NAVIGATION
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

    // ======================================================================
    // 5. SOLVER SELECTOR
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
    // 6. EXECUTE SOLVER + DRAW GRAPH
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

            // Show textual actions
            execOutput.innerHTML = data.actions.map(a => "• " + a).join("<br>");

            // Render grid graph
            renderGridSVG(data.nodes, data.primary_edges);
        });
    }

// ======================================================================
// CLEAN + COLORED + INTERACTIVE GRID RENDERER
// ======================================================================
function renderGridSVG(nodes, edges) {
    if (!mapBox || !nodes) return;

    // Clear previous svg
    mapBox.innerHTML = "";

    // Create SVG
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("width", "100%");
    svg.setAttribute("height", "100%");
    svg.setAttribute("viewBox", "0 0 1000 700");
    svg.style.cursor = "grab";

    enablePanZoom(svg);

    // Tooltip overlay
    const tooltip = document.createElement("div");
    tooltip.style.position = "absolute";
    tooltip.style.display = "none";
    tooltip.style.padding = "6px 10px";
    tooltip.style.background = "#fff";
    tooltip.style.border = "1px solid #444";
    tooltip.style.borderRadius = "4px";
    tooltip.style.fontSize = "12px";
    tooltip.style.pointerEvents = "none";
    tooltip.style.zIndex = "10";

    mapBox.style.position = "relative";
    mapBox.appendChild(tooltip);

    // Color palette
    function getNodeColor(type) {
        switch (type) {
            case "Gen":
            case "Solar": return "#f4d03f";
            case "Wind": return "#5dade2";
            case "Nuclear": return "#a569bd";
            case "Thermal": return "#e67e22";

            case "Bus":
            case "Storage": return "#58d68d";

            case "Railway": return "#16a085";
            case "Factory": return "#c0392b";
            case "Residential": return "#7f8c8d";

            default: return "#000";
        }
    }

    // Draw edges
    edges.forEach(([src, dst]) => {
        const s = nodes[src];
        const d = nodes[dst];
        if (!s || !d) return;

        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", s.x);
        line.setAttribute("y1", s.y);
        line.setAttribute("x2", d.x);
        line.setAttribute("y2", d.y);
        line.setAttribute("stroke", "#999");
        line.setAttribute("stroke-width", "3");
        svg.appendChild(line);
    });

    // Draw nodes
    for (const id in nodes) {
        const n = nodes[id];
        const color = getNodeColor(n.type);

        // Circle
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", n.x);
        circle.setAttribute("cy", n.y);
        circle.setAttribute("r", 12);
        circle.setAttribute("fill", color);
        circle.setAttribute("stroke", "#222");
        circle.setAttribute("stroke-width", "2");

        // Tooltip behavior
        circle.addEventListener("mousemove", (e) => {
            tooltip.style.display = "block";
            tooltip.style.left = (e.offsetX + 15) + "px";
            tooltip.style.top = (e.offsetY + 15) + "px";

            tooltip.innerHTML = `
                <b>${id}</b><br>
                Type: ${n.type}<br>
                Position: (${n.x}, ${n.y})
            `;
        });

        circle.addEventListener("mouseleave", () => {
            tooltip.style.display = "none";
        });

        svg.appendChild(circle);

        // Label
        const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
        label.setAttribute("x", n.x + 16);
        label.setAttribute("y", n.y + 4);
        label.setAttribute("font-size", "12");
        label.setAttribute("fill", "#000");
        label.textContent = id;
        svg.appendChild(label);
    }

    mapBox.appendChild(svg);
}


    // ======================================================================
    // 8. PAN + ZOOM
    // ======================================================================
    function enablePanZoom(svg) {
        let isPanning = false;
        let start = { x: 0, y: 0 };
        let view = { x: 0, y: 0, w: 1000, h: 700 };

        svg.addEventListener("mousedown", (e) => {
            isPanning = true;
            start.x = e.clientX;
            start.y = e.clientY;
            svg.style.cursor = "grabbing";
        });

        svg.addEventListener("mousemove", (e) => {
            if (!isPanning) return;
            const dx = (start.x - e.clientX) * (view.w / svg.clientWidth);
            const dy = (start.y - e.clientY) * (view.h / svg.clientHeight);

            view.x += dx;
            view.y += dy;

            svg.setAttribute("viewBox", `${view.x} ${view.y} ${view.w} ${view.h}`);
            start.x = e.clientX;
            start.y = e.clientY;
        });

        svg.addEventListener("mouseup", () => {
            isPanning = false;
            svg.style.cursor = "grab";
        });

        svg.addEventListener("wheel", (e) => {
            e.preventDefault();

            const zoom = 1.1;
            if (e.deltaY < 0) {
                view.w /= zoom;
                view.h /= zoom;
            } else {
                view.w *= zoom;
                view.h *= zoom;
            }

            svg.setAttribute("viewBox", `${view.x} ${view.y} ${view.w} ${view.h}`);
        });
    }

});
