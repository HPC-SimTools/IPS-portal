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
	    ]
    } );
} );
