$(document).ready(function() {
    // Assuming your data is stored in a variable called data
    var table = $('#myTable').DataTable({
        data: window.files,  // Using 'window.files' here
        pageLength: 25,
        columns: [                               
            {         
                "className": 'details-control',
                "data": "type",    
                "render": function (data, type, row, meta) {
                    return '<img src="static/images/' + data + '.png" width="32" height="32" alt="' + data + '">';
                }
            },          
            { "data": "started_at" },
            { "data": "hash" },
            { "data": "overall_status" },
            { "data": "duration" },
            {
                "data": "testcases",
                "render": function(data) {
                    return data.length;
                }
            },
            {
                "data": "testcases",
                "render": function(data) {
                    return data.filter(testcase => testcase.status === 'PASS').length;
                }
            },
            {
                "data": "testcases",
                "render": function(data) {
                    return data.filter(testcase => testcase.status === 'FAIL').length;
                }
            }            
        ]
    });

    // Add event listener for opening and closing details
    $('#myTable tbody').on('click', 'td.details-control', function () {
        var tr = $(this).closest('tr');
        var row = table.row(tr);

        if (row.child.isShown()) {
            // This row is already open - close it
            row.child.hide();
            tr.removeClass('shown');
        }
        else {
            // Open this row
            row.child(format(row.data())).show();
            tr.addClass('shown');
        }
    });
});

function format (rowData) {
    var div = $('<div/>');
    var testcases = rowData.testcases;
    // Create a new table for the testcases
    var table = $('<table/>');
    // Add table headers
    table.append('<tr><th>Test Case</th><th>Status</th><th>Duration</th></tr>');

    // Iterate over each testcase and add it to the table as a new row
    testcases.forEach(function(testcase) {
        var duration = testcase.duration ? testcase.duration + ' ms' : 'N/A';
        table.append(
            '<tr><td>' + testcase.testcase +
            '</td><td>' + testcase.status +
            '</td><td>' + testcase.duration +
            '</td></tr>'
        );
    });

    div.append(table);

    return div;
}


