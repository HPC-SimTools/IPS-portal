$(document).ready( function () {
    $('#runs-table').DataTable( {
	ajax: {
	    url: '/api/runs',
	    dataSrc: ''
	},
	deferRender: true,
	order: [[ 0, 'desc' ]],
	columns: [
	    {data: 'runid',
	     render: function(data, type, row, meta){
		 if(type === 'display'){
                     data = `<a href="/${data}">${data}</a>`;
		 }
		 return data;}},
	    {data: 'state',
	     defaultContent: ''},
	    {data: 'rcomment',
	     defaultContent: ''},
	    {data: 'simname',
	     defaultContent: ''},
	    {data: 'host',
	     defaultContent: ''},
	    {data: 'user',
	     defaultContent: ''},
	    {data: 'startat',
	     defaultContent: ''},
	    {data: 'stopat',
	     defaultContent: ''}
	],
	buttons: {
	    buttons: [
		{
		    text: 'Reload',
		    className: 'btn btn-primary',
		    action: function ( e, dt, node, config ) {
			dt.ajax.reload();
		    }
		}
	    ],
	    dom: {
		button: {
		    className: 'btn'
		}
	    }
	},
	processing: true,
	dom:
		"<'row'<'col-sm-12 col-md-6'B><'col-sm-12 col-md-6'f>>" +
		"<'row'<'col-sm-12'tr>>" +
		"<'row'<'col-sm-12 col-md-5'l><'col-sm-12 col-md-3'i><'col-sm-12 col-md-4'p>>",
    } );
} );
