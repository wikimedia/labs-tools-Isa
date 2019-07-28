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
    dom: "<'row'<'col-sm-6'lB><'col-sm-6'f>>" +
        "<'row'<'col-sm-12't>>" +
        "<'row'<'col-sm-5'i><'col-sm-7'p>>", 
    buttons: [{
        text: 'Show closed campaigns',
        className: "show-closed-campaigns-btn",
        action: function ( el, dt, node, config ) {
            var statusColumn = dt.column(booleanStatusColumn)
            if (statusColumn.search() === '1') {
                statusColumn.search('').draw();
                $(node).addClass("active");
            } else {
                statusColumn.search(1).draw();
                $(node).removeClass("active");
            }
        }
    }]
});

// Initially, the closed campaigns should be hidden
campaignTable.columns(booleanStatusColumn).search(1).draw();