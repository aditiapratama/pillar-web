

/* Edit Node */
function editNode(nodeId) {

	// Remove the 'n_' suffix from the id
	if (nodeId.substring(0, 2) == 'n_') {
		nodeId = nodeId.substr(2);
	}

	var url = '/nodes/' + nodeId + '/edit?embed=1'
	$.get(url, function(dataHtml) {
		// Prevent flicker by scrolling to top before showing anything
		$("#project_context-container").scrollTop(0);

		// Update the DOM injecting the generate HTML into the page
		$('#project_context').html(dataHtml);
		window.location.replace('#' + nodeId);

		$('.project-mode-view').hide();
		$('.project-mode-edit').show();
	})
	.fail(function(dataResponse) {
		$('#project_context').html($('<iframe id="server_error"/>'));
		$('#server_error').attr('src', url);
	})
	.always(function(){
		$('.button-edit-icon').addClass('pi-edit').removeClass('pi-spin spinner');
	});
}


/* Add Node */
function addNode() {

	var url = '/files/upload?embed=1'
	$.get(url, function(dataHtml) {
		// Prevent flicker by scrolling to top before showing anything
		$("#project_context-container").scrollTop(0);

		// Update the DOM injecting the generate HTML into the page
		$('#project_context').html(dataHtml);

		$('.project-mode-view, .project-mode-edit').hide();
	})
	.fail(function(dataResponse) {
		$('#project_context').html($('<iframe id="server_error"/>'));
		$('#server_error').attr('src', url);
	})
	.always(function(){
		$('.button-add-icon').addClass('pi-collection-plus').removeClass('pi-spin spinner');
	});
}

/* Add Group */
function addGroup(parentId) {
	var url = '/nodes/groups/create'
	$.post(url, {
		name: "New Folder",
		parent_id: parentId})
		.done(function(data) {
			if (parentId) {
				// We are in embedded mode and try to call the editNode function
				editNode(data.data.asset_id);
			} else {
				window.location.replace("/nodes/" + data.data.asset_id + "/edit");
			}
			//alert( "Data Loaded: " + data.message );
	})
	.always(function(){
		$('.button-add-group-icon').addClass('pi-collection-plus').removeClass('pi-spin spinner');
	});
}


/* Edit Button */
$('#item_edit').click(function(e){
	$('.button-edit-icon').addClass('pi-spin spinner').removeClass('pi-edit');
	// When clicking on the edit icon, embed the edit
	e.preventDefault;
	node_id = document.getElementById("item_edit");
	editNode(node_id.getAttribute('data-node_id'));
});


/* Add Asset Button */
$('#item_add').click(function(e){
	$('.button-add-icon').addClass('pi-spin spinner').removeClass('pi-collection-plus');
	e.preventDefault;
	addNode();
});


/* Add Group Button */
$('#item_add_group').click(function(e){
	$('.button-add-group-icon').addClass('pi-spin spinner').removeClass('pi-collection-plus');
	e.preventDefault;
	parentNodeId = Cookies.get('bcloud_current_node_id');
	addGroup(parentNodeId);
});

/* Move Node */
moving_node_id = Cookies.get('bcloud_moving_node_id');

function moveModeEnter() {
	$('#overlay-mode-move-container').addClass('visible');
	$('.button-move').addClass('disabled');
};

function moveModeExit() {
	/* Remove cookie, display current node, remove UI */
	var current_node = document.getElementById("item_edit");
	displayNode(current_node.getAttribute('data-node_id'));

	$('#overlay-mode-move-container').removeClass('visible');
	$('.button-move').removeClass('disabled');

	Cookies.remove('bcloud_moving_node_id');
};

if (moving_node_id) {
	moveModeEnter();
} else {
	$('#overlay-mode-move-container').removeClass('visible');
	$('.button-move').removeClass('disabled');
};

$('#item_move').click(function(e){
	e.preventDefault;

	moveModeEnter();

	node_id = document.getElementById("item_edit");
	moving_node_id = Cookies.get('bcloud_moving_node_id');

	Cookies.set('bcloud_moving_node_id', node_id.getAttribute('data-node_id'));
});

$("#item_move_accept").click(function(e) {

	e.preventDefault();

	var current_node = document.getElementById("item_edit");
	var moving_node_id = Cookies.get('bcloud_moving_node_id');

	$.post(urlNodeMove, {
		node_id: moving_node_id, dest_parent_node_id: current_node.getAttribute('data-node_id')},
		function(data){
	}).done(function() {
		statusBarSet('success', 'Moved just fine');
		Cookies.remove('bcloud_moving_node_id');
		moveModeExit();

		$('#project_tree').jstree("refresh");
	});
});

$("#item_move_cancel").click(function(e) {
	e.preventDefault();
	moveModeExit();
});


/* Featured Toggle */
$('#item_featured').click(function(e){
	e.preventDefault;
	var current_node = document.getElementById("item_edit");
	var current_node_id = current_node.getAttribute('data-node_id');

	$.post(urlNodeFeature, {node_id : current_node_id},
		function(data){
		// Feedback logic
	})
	.done(function(){
		// $('.button-featured').addClass('featured');
		// $('.button-featured-icon').addClass('pi-star-filled').removeClass('pi-star');
		statusBarSet('success', 'Featured status toggled', 'pi-star-filled');
	});
});


/* Delete */
$('#item_delete').click(function(e){
	e.preventDefault;
	var current_node = document.getElementById("item_edit");
	var current_node_id = current_node.getAttribute('data-node_id');
	var parentNodeId = Cookies.get('bcloud_parent_node_id');

	$.post(urlNodeDelete, {node_id : current_node_id},
		function(data){
		// Feedback logic
	})
	.done(function(){
		statusBarSet('success', 'Node deleted', 'pi-trash');
		displayNode(parentNodeId);
	});
});


/* Toggle public */
$('#item_toggle_public').click(function(e){
	e.preventDefault;
	var current_node = document.getElementById("item_edit");
	var current_node_id = current_node.getAttribute('data-node_id');
	var parentNodeId = Cookies.get('bcloud_parent_node_id');

	$.post(urlNodeTogglePublic, {node_id : current_node_id},
		function(data){
	})
	.done(function(data){
		statusBarSet('success', data.data.message);
	});
});


/* Status Bar */
function statusBarSet(classes, html, icon_name){
	/* Utility to notify the user by temporarily flashing text on the project header
		 Usage:
			'classes' can be: success, error, warning, info, default
			'html': the text to display, can contain html tags
				(in case of errors, it's better to use data.status + data.statusText instead )
			'icon_name': optional, sets a custom icon (otherwise an icon based on the class will be used)
	*/

	var icon = '';

	if (!icon_name) {
		if (classes == 'error') {
			icon_name = 'ion-alert-circled';
		} else if (classes == 'success') {
			icon_name = 'ion-checkmark-round';
		} else if (classes == 'warning') {
			icon_name = 'ion-alert-circled';
		} else if (classes == 'info') {
			icon_name = 'ion-information-circled';
		} else {
			icon = '<i class="' + icon_name + '"></i>';
		};
	} else {
		icon = '<i class="' + icon_name + '"></i>';
	};

	var text = icon + html;
	$("#project-statusbar").addClass('active ' + classes);
	$("#project-statusbar").html(text);

	/* Back to normal */
	setTimeout(function(){
	$("#project-statusbar").removeAttr('class');
	$("#project-statusbar").html();
	}, 2000);
};
