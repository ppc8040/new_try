// Cache selected rows at Confirm time — reused by all subsequent modals
let _cachedSelectedRows = [];
let _cachedAllocationRows = [];

function getSelectedRows() {
    let selectedRows = [];
    let invalidInputs = false;

    document.querySelectorAll(".releases-table1 tbody tr").forEach((row) => {
        let inputField = row.querySelector(".pallet-input");
        let inputValue = parseInt(inputField.value.trim());

        if (!isNaN(inputValue) && inputValue > 0) {
            let rowData = Array.from(row.querySelectorAll("td:not(:last-child)")).map(td => td.innerText.trim());
            let noOfPallets = parseInt(rowData[4]);

            if (inputValue > noOfPallets) {
                inputField.style.border = "2px solid red";
                invalidInputs = true;
            } else {
                inputField.style.border = "";
                rowData.push(inputValue);
                selectedRows.push(rowData);
            }
        } else {
            inputField.style.border = "";
        }
    });

    if (invalidInputs) {
        return [];
    }

    return selectedRows;
}

function confirmRelease() {
    let selectedRows = getSelectedRows();
    if (selectedRows.length === 0) {
        alert("No valid pallets selected for release.");
        return;
    }

    // Cache for use throughout the rest of the flow
    _cachedSelectedRows = selectedRows;

    document.querySelector("#releaseSummaryTable tbody").innerHTML = selectedRows
        .map(row => `<tr>${row.map(col => `<td>${col}</td>`).join('')}</tr>`)
        .join('');

    document.getElementById("releaseModal").style.display = "block";
}

function closeModal() {
    document.getElementById("releaseModal").style.display = "none";
}

// ── PO Allocation Modal — opens when Submit is clicked in Confirm Release ──
function openPOAllocationModal() {
    let selectedRows = _cachedSelectedRows;
    if (!selectedRows || selectedRows.length === 0) {
        alert("No valid data to submit.");
        return;
    }

    // Build payload
    // Row columns: [0]=CustomerCode [1]=CustomerPart [2]=IndusPart
    //              [3]=Coils/Pallet [4]=NumPallets [5]=Quantity [6]=PalletsForRelease

    // Group by indus_part: sum (coils_per_pallet * pallets_for_release) across all rows
    // for the same Indus Part so the backend runs ONE clean FIFO pass per part.
    let grouped = {};
    selectedRows.forEach(row => {
        let indus_part = row[2];
        let lineQty    = parseInt(row[3]) * parseInt(row[6]);  // coils/pallet × pallets for release

        if (grouped[indus_part]) {
            grouped[indus_part].release_qty += lineQty;
        } else {
            grouped[indus_part] = {
                customer_code:       row[0],
                customer_part:       row[1],
                indus_part:          indus_part,
                release_qty:         lineQty
            };
        }
    });

    let releaseItems = Object.values(grouped);

    // Hide Confirm Release modal while loading
    document.getElementById("releaseModal").style.display = "none";

    fetch('/views/get-po-allocation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items: releaseItems })
    })
    .then(response => response.ok ? response.json() : Promise.reject('Network error'))
    .then(data => {
        if (data.error) {
            alert('Error fetching PO data: ' + data.error);
            document.getElementById("releaseModal").style.display = "block";
            return;
        }

        // Cache allocation rows for inclusion in the email
        _cachedAllocationRows = data.rows || [];

        let tbody = document.querySelector("#poAllocationTable tbody");
        tbody.innerHTML = '';

        if (_cachedAllocationRows.length > 0) {
            _cachedAllocationRows.forEach(row => {
                let tr = document.createElement('tr');
                // Highlight rows with partial fulfilment (Remaining Open Qty > 0)
                if (typeof row[7] === 'number' && row[7] > 0) {
                    tr.style.backgroundColor = '#fffbf0';
                }
                row.forEach(col => {
                    let td = document.createElement('td');
                    td.textContent = col;
                    tr.appendChild(td);
                });
                tbody.appendChild(tr);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:#7f8c8d;">No open PO data found.</td></tr>';
        }

        document.getElementById("poAllocationModal").style.display = "block";
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while fetching PO allocation data.');
        document.getElementById("releaseModal").style.display = "block";
    });
}

function closePOAllocationModal() {
    document.getElementById("poAllocationModal").style.display = "none";
    // Go back to Confirm Release
    document.getElementById("releaseModal").style.display = "block";
}

function proceedFromPOAllocation() {
    document.getElementById("poAllocationModal").style.display = "none";
    // Open the Release Notes modal
    document.getElementById("notesModal").style.display = "block";
    document.getElementById("releaseNotesInput").value = "";
    document.getElementById("releaseNotesInput").focus();
}
// ── END PO Allocation Modal ──

function openNotesModal() {
    // Routes through PO Allocation first
    openPOAllocationModal();
}

function closeNotesModal() {
    document.getElementById("notesModal").style.display = "none";
    // Go back to PO Allocation modal (not Confirm Release)
    document.getElementById("poAllocationModal").style.display = "block";
}

function submitReleaseData() {
    let data = _cachedSelectedRows;
    if (!data || data.length === 0) {
        alert("No valid data to submit.");
        return;
    }

    let notes = document.getElementById("releaseNotesInput").value.trim();

    fetch('/views/submit-releases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            data: data,
            notes: notes,
            po_allocation: _cachedAllocationRows
        })
    })
    .then(response => response.ok ? response.json() : Promise.reject('Network response was not ok'))
    .then(responseData => {
        alert(responseData.success ? 'Releases submitted successfully!' : 'Error: ' + (responseData.error || 'Unknown error occurred.'));
        if (responseData.success) {
            document.getElementById("notesModal").style.display = "none";
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while submitting data. Please try again.');
    });
}
