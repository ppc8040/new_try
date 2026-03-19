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

    document.querySelector("#releaseSummaryTable tbody").innerHTML = selectedRows
        .map(row => `<tr>${row.map(col => `<td>${col}</td>`).join('')}</tr>`)
        .join('');

    document.getElementById("releaseModal").style.display = "block";
}

function closeModal() {
    document.getElementById("releaseModal").style.display = "none";
}

function openNotesModal() {
    document.getElementById("releaseModal").style.display = "none";
    document.getElementById("notesModal").style.display = "block";
    document.getElementById("releaseNotesInput").value = "";
    document.getElementById("releaseNotesInput").focus();
}

function closeNotesModal() {
    document.getElementById("notesModal").style.display = "none";
    document.getElementById("releaseModal").style.display = "block";
}

function submitReleaseData() {
    let data = getSelectedRows();
    if (data.length === 0) {
        alert("No valid data to submit.");
        return;
    }

    let notes = document.getElementById("releaseNotesInput").value.trim();

    fetch('/views/submit-releases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: data, notes: notes })
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
