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
	    ]
    } );
} );
