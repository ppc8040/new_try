function getSelectedRows() {
    let selectedRows = [];
    let invalidInputs = false;  // Flag to check if any input is invalid

    document.querySelectorAll(".releases-table tbody tr").forEach((row) => {
        let inputField = row.querySelector(".pallet-input");
        let inputValue = parseInt(inputField.value.trim());

        if (!isNaN(inputValue) && inputValue > 0) {
            let rowData = Array.from(row.querySelectorAll("td:not(:last-child)")).map(td => td.innerText.trim());
            let noOfPallets = parseInt(rowData[4]);  // "No. of Pallets" column (5th column, index 4)

            // Check if input value exceeds the available number of pallets
            if (inputValue > noOfPallets) {
                inputField.style.border = "2px solid red";  // Highlight invalid input with red border
                invalidInputs = true;  // Set flag to true
            } else {
                inputField.style.border = "";  // Reset border if valid
                rowData.push(inputValue);
                selectedRows.push(rowData);
            }
        } else {
            inputField.style.border = "";  // Reset border if input is not a valid number
        }
    });

    // Show an alert for invalid inputs only once, and prevent submission
    if (invalidInputs) {
        return [];  // Return an empty array to prevent further processing
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

function submitReleaseData() {
    let data = getSelectedRows();
    if (data.length === 0) {
        alert("No valid data to submit.");
        return;
    }

    fetch('/views/submit-releases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data })
    })
    .then(response => response.ok ? response.json() : Promise.reject('Network response was not ok'))
    .then(responseData => {
        alert(responseData.success ? 'Releases submitted successfully!' : 'Error: ' + (responseData.error || 'Unknown error occurred.'));
        if (responseData.success) closeModal();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while submitting data. Please try again.');
    });
}
