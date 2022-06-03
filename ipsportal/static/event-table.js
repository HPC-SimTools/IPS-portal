$(document).ready( function () {
    $('#event-table').DataTable( {
	ajax: {
	    url: `/api/run/${$('#event-table').attr('runid')}/events`,
	    dataSrc: ''
	},
	deferRender: true,
        order: [[ 1, "desc" ]],
	lengthMenu: [[10, 25, 100, -1], [10, 25, 100, "All"]],
	columns: [
	    {data: 'created',
	     defaultContent: ''},
	    {data: 'seqnum',
	     defaultContent: ''},
	    {data: 'eventtype',
	     defaultContent: ''},
	    {data: 'code',
	     defaultContent: ''},
	    {data: 'walltime',
	     defaultContent: ''},
	    {data: 'phystimestamp',
	     defaultContent: ''},
	    {data: 'comment',
	     defaultContent: ''}
	],
	buttons: [
            {
		text: 'Reload',
		action: function ( e, dt, node, config ) {
                    dt.ajax.reload();
		}
            }
	],
	processing: true,
	dom:
	"<'row'<'col-sm-12 col-md-6'B><'col-sm-12 col-md-6'f>>" +
	    "<'row'<'col-sm-12'tr>>" +
	    "<'row'<'col-sm-12 col-md-5'l><'col-sm-12 col-md-3'i><'col-sm-12 col-md-4'p>>",
    } );
} );
