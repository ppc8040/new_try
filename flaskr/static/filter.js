function filterTable() {
    const input = document.getElementById('search-input');
    const filter = input.value.toUpperCase();
    const activeTab = document.querySelector('.active-tab-name').textContent.trim();

    let table, rows, columnIndices = [];

    if (activeTab.includes('Inventory')) {
        table = document.querySelector('.inventory-table');
        columnIndices = [getColumnIndex(table, 'Customer Part')];
    } else if (activeTab.includes('Transit')) {
        table = document.querySelector('.transit-table');
        columnIndices = [getColumnIndex(table, 'Customer Part')];
    } else if (activeTab.includes('Open Order')) {
        table = document.querySelector('.oor-table');
        columnIndices = [
            getColumnIndex(table, 'Customer Part'),
            getColumnIndex(table, 'Customer PO#') // Include both columns
        ];
    } else if (activeTab.includes('Releases')) {
        table = document.querySelector('.releases-table');
        columnIndices = [getColumnIndex(table, 'Customer Part')];
    }


    if (table && columnIndices.length > 0) {
        rows = table.getElementsByTagName('tr');

        for (let i = 1; i < rows.length; i++) {
            let isVisible = false;
            for (let columnIndex of columnIndices) {
                if (columnIndex !== -1) {
                    const cell = rows[i].getElementsByTagName('td')[columnIndex];
                    if (cell) {
                        const cellValue = cell.textContent || cell.innerText;
                        if (cellValue.toUpperCase().indexOf(filter) > -1) {
                            isVisible = true;
                            break;
                        }
                    }
                }
            }
            rows[i].style.display = isVisible ? '' : 'none';
        }
    }
}

function getColumnIndex(table, headerName) {
    const headers = table.getElementsByTagName('th');
    for (let i = 0; i < headers.length; i++) {
        if (headers[i].textContent.trim() === headerName) {
            return i;
        }
    }
    return -1;
}
