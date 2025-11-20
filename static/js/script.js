document.addEventListener("DOMContentLoaded", function () {
    const mapBox = document.getElementById("gridMap");

    // Simulate grid load for command center page
    if (mapBox) {
        setTimeout(() => {
            mapBox.innerHTML = `
                <svg width="100%" height="100%">
                    <line x1="50" y1="50" x2="150" y2="120" stroke="#aaa" stroke-width="2"/>
                    <circle cx="50" cy="50" r="6" fill="black" />
                    <circle cx="150" cy="120" r="6" fill="black" />
                </svg>
            `;
        }, 800);
    }

    // Sidebar buttons navigation
    const navItems = document.querySelectorAll(".nav-item");

    navItems.forEach((item) => {
        const text = item.textContent.trim();

        if (text === "Command Center") {
            item.onclick = () => window.location.href = "/";
        }

        if (text === "Topology View") {
            item.onclick = () => window.location.href = "/topology";
        }

        if (text === "Operations View") {
            item.onclick = () => window.location.href = "/operations";
        }

        if (text === "System Settings") {
            item.onclick = () => window.location.href = "/settings";
        }
    });
});
// ---------------- SETTINGS PAGE TABS ---------------------
document.addEventListener("DOMContentLoaded", () => {
    const tabs = document.querySelectorAll(".settings-tab");
    const panels = document.querySelectorAll(".settings-content");

    tabs.forEach(tab => {
        tab.addEventListener("click", () => {

            // Remove highlight
            tabs.forEach(t => t.classList.remove("active"));
            panels.forEach(p => p.classList.remove("active"));

            // Activate selected
            tab.classList.add("active");
            const target = tab.dataset.tab;
            document.getElementById(`tab-${target}`).classList.add("active");
        });
    });
});
// -------------------- THEME SWITCHING ----------------------

document.addEventListener("DOMContentLoaded", () => {

    const themeSelector = document.getElementById("themeSelector");

    // Load saved theme
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
        document.body.classList.add("dark-mode");
        if (themeSelector) themeSelector.value = "dark";
    }

    // When user changes theme
    if (themeSelector) {
        themeSelector.addEventListener("change", () => {
            const selected = themeSelector.value;

            if (selected === "dark") {
                document.body.classList.add("dark-mode");
                localStorage.setItem("theme", "dark");
            } else {
                document.body.classList.remove("dark-mode");
                localStorage.setItem("theme", "light");
            }
        });
    }

});

document.addEventListener("DOMContentLoaded", () => {

    const execBtn = document.getElementById("executeBtn");
    const execOutput = document.getElementById("execOutput");

    if (execBtn) {
        execBtn.addEventListener("click", async () => {
            execOutput.textContent = "Running Gurobi solver...";

            const res = await fetch("/run-solver", { method: "POST" });
            const data = await res.json();

            if (!data.ok) {
                execOutput.textContent = "Error: " + data.error;
                return;
            }

            execOutput.textContent = data.output;
        });
    }

});


document.addEventListener("DOMContentLoaded", () => {
    const solverSelector = document.getElementById("solverSelector");

    if (solverSelector) {
        solverSelector.addEventListener("change", async () => {
            await fetch("/set-solver", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ solver: solverSelector.value })
            });

            alert("Solver selection saved!");
        });
    }
});
