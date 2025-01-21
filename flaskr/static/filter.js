function filterTable() {
    const input = document.getElementById('search-input');
    const filter = input.value.toUpperCase();
    const activeTab = document.querySelector('.active-tab-name').textContent.trim();

    let table, rows, columnIndex;

    if (activeTab.includes('Inventory')) {
        table = document.querySelector('.inventory-table');
        columnIndex = getColumnIndex(table, 'Customer Part');
    } else if (activeTab.includes('Transit')) {
        table = document.querySelector('.transit-table');
        columnIndex = getColumnIndex(table, 'Customer Part');
    } else if (activeTab.includes('OOR')) {
        table = document.querySelector('.oor-table');
        columnIndex = getColumnIndex(table, 'Customer Material');
    }

    if (table && columnIndex !== -1) {
        rows = table.getElementsByTagName('tr');

        for (let i = 1; i < rows.length; i++) {
            const cell = rows[i].getElementsByTagName('td')[columnIndex];
            if (cell) {
                const cellValue = cell.textContent || cell.innerText;
                rows[i].style.display = cellValue.toUpperCase().indexOf(filter) > -1 ? '' : 'none';
            }
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
