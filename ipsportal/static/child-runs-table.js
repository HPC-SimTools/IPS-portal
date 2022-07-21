$(document).ready( function () {
    $('#child-runs-table').DataTable( {
	ajax: {
	    url: `/api/run/${$('#child-runs-table').attr('runid')}/children`,
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
	     defaultContent: ''},
	    {data: 'walltime',
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
	createdRow: function(row, data, dataIndex){
            if( data['state'] ==  'Completed'){
		if (data['ok']) {
                    $(row).addClass('table-success');
		} else {
		    $(row).addClass('table-danger');
		}
	    }
        }
    }
			      );
} );
