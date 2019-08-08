/*********** Campaign directory page ***********/

// Hidden booleanStatusColumn is used internally to hide/show closed campaigns
// This allows filtering the same way regardless of UI language setting
var booleanStatusColumn = [8];

var campaignTable = $('#campaign_table').DataTable({
    responsive: true,
    columnDefs: [
        {
            targets: [0],
            responsivePriority: 1
        }, 
        {
            targets: [-1],
            responsivePriority: 2
        },
        {
            targets: booleanStatusColumn,
            visible: false
        },
    ],
    "language": {
        // Hide the text which shows the total number of campaigns when filters are applied
        "infoFiltered": ""
    },
    // See https://stackoverflow.com/questions/32252616/ for explanation of dom setting below
    // It's used to get the button in the same line as the other table controls in the header
    dom: "f" +
         "<'row'<'col-sm-12'tr>>" +
         "<'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>"
});

// Initially, the closed campaigns should be hidden
// Todo use searchCols datatables option
campaignTable.columns(booleanStatusColumn).search(1).draw();

$('#show-closed-campaigns-checkbox').change(function() {
    var statusSearch = (this.checked) ? '' : 1;
    campaignTable.column(booleanStatusColumn).search(statusSearch).draw();
});