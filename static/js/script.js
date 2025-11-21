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
// FUNCTIONAL SVG RENDERER WITH PAN + ZOOM
// ======================================================================
function renderGridSVG(nodes, edges) {
    if (!mapBox || !nodes) return;

    // Clear old SVG
    mapBox.innerHTML = "";

    // Create <svg>
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("width", "100%");
    svg.setAttribute("height", "100%");
    svg.setAttribute("viewBox", "0 0 1000 700");

    // Enable zoom/pan
    svg.style.cursor = "grab";
    enablePanZoom(svg);

    // === Tooltip Div (HTML overlay) ===
    const tooltip = document.createElement("div");
    tooltip.style.position = "absolute";
    tooltip.style.padding = "6px 10px";
    tooltip.style.border = "1px solid #444";
    tooltip.style.background = "#fff";
    tooltip.style.fontSize = "12px";
    tooltip.style.display = "none";
    tooltip.style.pointerEvents = "none";
    tooltip.style.borderRadius = "4px";
    tooltip.style.zIndex = "50";
    mapBox.style.position = "relative";
    mapBox.appendChild(tooltip);

    // ------------------------------
    // Draw edges
    // ------------------------------
    edges.forEach(([src, dst]) => {
        const s = nodes[src];
        const d = nodes[dst];
        if (!s || !d) return;

        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", s.x);
        line.setAttribute("y1", s.y);
        line.setAttribute("x2", d.x);
        line.setAttribute("y2", d.y);
        line.setAttribute("stroke", "#888");
        line.setAttribute("stroke-width", "3");
        svg.appendChild(line);
    });

    // ------------------------------
    // Draw nodes
    // ------------------------------
    for (const id in nodes) {
        const n = nodes[id];

        // Node circle
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", n.x);
        circle.setAttribute("cy", n.y);
        circle.setAttribute("r", 10);
        circle.setAttribute("fill", "black");

        // Add hover tooltip behavior
        circle.addEventListener("mousemove", (e) => {
            tooltip.style.display = "block";

            tooltip.innerHTML = `
                <b>${id}</b><br>
                Type: ${n.type}<br>
                X: ${n.x}, Y: ${n.y}
            `;

            tooltip.style.left = (e.offsetX + 15) + "px";
            tooltip.style.top = (e.offsetY + 15) + "px";
        });

        circle.addEventListener("mouseleave", () => {
            tooltip.style.display = "none";
        });

        svg.appendChild(circle);

        // Node label
        const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
        label.setAttribute("x", n.x + 14);
        label.setAttribute("y", n.y + 4);
        label.setAttribute("font-size", "12");
        label.textContent = id;

        svg.appendChild(label);
    }

    mapBox.appendChild(svg);
}

function enablePanZoom(svg) {
    let isPanning = false;
    let start = { x: 0, y: 0 };
    let viewBox = { x: 0, y: 0, w: 1000, h: 700 };

    svg.addEventListener("mousedown", (e) => {
        isPanning = true;
        start.x = e.clientX;
        start.y = e.clientY;
        svg.style.cursor = "grabbing";
    });

    svg.addEventListener("mousemove", (e) => {
        if (!isPanning) return;

        const dx = (start.x - e.clientX) * (viewBox.w / svg.clientWidth);
        const dy = (start.y - e.clientY) * (viewBox.h / svg.clientHeight);

        viewBox.x += dx;
        viewBox.y += dy;

        svg.setAttribute("viewBox", `${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`);

        start.x = e.clientX;
        start.y = e.clientY;
    });

    svg.addEventListener("mouseup", () => {
        isPanning = false;
        svg.style.cursor = "grab";
    });

    svg.addEventListener("mouseleave", () => {
        isPanning = false;
        svg.style.cursor = "grab";
    });

    svg.addEventListener("wheel", (e) => {
        e.preventDefault();

        const zoomFactor = 1.1;
        if (e.deltaY < 0) {
            viewBox.w /= zoomFactor;
            viewBox.h /= zoomFactor;
        } else {
            viewBox.w *= zoomFactor;
            viewBox.h *= zoomFactor;
        }

        svg.setAttribute("viewBox", `${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`);
    });
}


});
