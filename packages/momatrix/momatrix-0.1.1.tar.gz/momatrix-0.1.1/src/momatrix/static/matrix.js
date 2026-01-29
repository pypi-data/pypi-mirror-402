function render({ model, el }) {
    el.classList.add("momatrix-container");

    const style = model.get("style");
    if (style) {
        el.classList.add(`momatrix-style-${style}`);
    }

    // --- Create UI Structure ---
    const controls = document.createElement("div");
    controls.className = "momatrix-controls";

    const createDimInput = (label, trait) => {
        const group = document.createElement("div");
        group.className = "momatrix-control-group";
        
        const lbl = document.createElement("label");
        lbl.textContent = label;
        
        const input = document.createElement("input");
        input.type = "number";
        input.min = "1";
        input.className = "momatrix-input-dim";
        input.value = model.get(trait);
        
        // Listen for UI changes
        input.addEventListener("change", () => {
            const val = parseInt(input.value, 10);
            if (val > 0) {
                model.set(trait, val);
                model.save_changes();
            }
        });

        group.appendChild(lbl);
        group.appendChild(input);
        return { group, input };
    };

    const rowControl = createDimInput("Rows:", "rows");
    const colControl = createDimInput("Cols:", "cols");

    controls.appendChild(rowControl.group);
    controls.appendChild(colControl.group);

    const grid = document.createElement("div");
    grid.className = "momatrix-grid";

    el.appendChild(controls);
    el.appendChild(grid);

    // --- State & Rendering ---

    let renderedRows = 0;
    let renderedCols = 0;

    function updateGrid() {
        const rows = model.get("rows");
        const cols = model.get("cols");
        const data = model.get("_data");

        // Update control inputs if they differ (e.g. external change)
        if (parseInt(rowControl.input.value) !== rows) rowControl.input.value = rows;
        if (parseInt(colControl.input.value) !== cols) colControl.input.value = cols;

        // Set Grid Layout
        grid.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;

        // Only rebuild if dimensions change
        if (rows !== renderedRows || cols !== renderedCols) {
            renderedRows = rows;
            renderedCols = cols;
            grid.innerHTML = "";

            for (let r = 0; r < rows; r++) {
                for (let c = 0; c < cols; c++) {
                    const cell = document.createElement("input");
                    cell.type = "number";
                    cell.className = "momatrix-cell";
                    cell.step = "any";
                    
                    // Safe access to data
                    const val = (data[r] && data[r][c] !== undefined) ? data[r][c] : 0;
                    cell.value = val;

                    cell.addEventListener("change", () => {
                        const cleanVal = parseFloat(cell.value);
                        const currentData = JSON.parse(JSON.stringify(model.get("_data"))); // deep copy
                        
                        // Ensure row exists
                        if (!currentData[r]) currentData[r] = [];
                        currentData[r][c] = isNaN(cleanVal) ? 0 : cleanVal;

                        model.set("_data", currentData);
                        model.save_changes();
                    });

                    grid.appendChild(cell);
                }
            }
        } else {
            // Update values in place to preserve focus
            for (let r = 0; r < rows; r++) {
                for (let c = 0; c < cols; c++) {
                    const index = r * cols + c;
                    if (index >= grid.children.length) break;
                    
                    const cell = grid.children[index];
                    const val = (data[r] && data[r][c] !== undefined) ? data[r][c] : 0;
                    
                    // Only update if value matches (handling strings vs numbers)
                    if (parseFloat(cell.value) !== val) {
                        cell.value = val;
                    }
                }
            }
        }
    }

    // --- Listeners ---
    model.on("change:rows", updateGrid);
    model.on("change:cols", updateGrid);
    model.on("change:_data", updateGrid);

    // Initial render
    updateGrid();
}

export default { render };
