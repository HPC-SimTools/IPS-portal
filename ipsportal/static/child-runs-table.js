$(document).ready( function () {
    $('#child-runs-table').DataTable( {
	ajax: {
	    url: `/api/run/${$('#child-runs-table').attr('runid')}/children`,
	    dataSrc: ''
	},
	deferRender: true,
	responsive: true,
	order: [[ 0, 'desc' ]],
	columns: [
	    {data: 'runid',
	     render: function(data, type, row, meta){
		 if(type === 'display'){
                     data = `<a href="/${data}">${data}</a>`;
		 }
		 return data;},
	     responsivePriority: 1},
	    {data: 'state',
	     defaultContent: '',
	     responsivePriority: 8},
	    {data: 'rcomment',
	     defaultContent: '',
	     responsivePriority: 4},
	    {data: 'simname',
	     defaultContent: '',
	     responsivePriority: 2},
	    {data: 'host',
	     defaultContent: ''},
	    {data: 'user',
	     defaultContent: '',
	     responsivePriority: 5},
	    {data: 'startat',
	     defaultContent: '',
	     responsivePriority: 6},
	    {data: 'stopat',
	     defaultContent: '',
	     responsivePriority: 7},
	    {data: 'walltime',
	     defaultContent: '',
	     responsivePriority: 3}
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
	    else if (data['state'] == 'Timeout') {
		$(row).addClass('table-warning');
	    }
        }
    }
			      );
} );
