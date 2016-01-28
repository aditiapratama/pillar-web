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
	var url = '/nodes/groups/create';
	var group = {name: "New Folder", projectId: ProjectUtils.projectId()};
	if (typeof(parentId) != 'undefined') {group.parent_id = parentId};
	$.post(url, group)
		.done(function(data) {
			editNode(data.data.asset_id);
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
	if (ProjectUtils.isProject() === 'True') {
		url = window.location.href + 'edit';
		window.location.replace(url);
	} else {
		editNode(ProjectUtils.nodeId());
	}
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
	if (ProjectUtils.isProject() === 'True') {
		addGroup();
	} else {
		addGroup(ProjectUtils.nodeId());
	}

});

/* Move Node */
var movingNodeId = Cookies.get('bcloud_moving_node_id');

function moveModeEnter() {
	$('#overlay-mode-move-container').addClass('visible');
	$('.button-move').addClass('disabled');
};

function moveModeExit() {
	/* Remove cookie, display current node, remove UI */
	if (ProjectUtils.isProject() === 'True') {
		displayProject(ProjectUtils.projectId());
	} else {
		displayNode(ProjectUtils.nodeId());
	}
	$('#overlay-mode-move-container').removeClass('visible');
	$('.button-move').removeClass('disabled');
	Cookies.remove('bcloud_moving_node_id');
};

if (movingNodeId) {
	moveModeEnter();
} else {
	$('#overlay-mode-move-container').removeClass('visible');
	$('.button-move').removeClass('disabled');
};

$('#item_move').click(function(e){
	e.preventDefault;
	moveModeEnter();
	// Set the nodeId in the cookie
	Cookies.set('bcloud_moving_node_id', ProjectUtils.nodeId());
});

$("#item_move_accept").click(function(e) {
	e.preventDefault();
	var movingNodeId = Cookies.get('bcloud_moving_node_id');
	var moveNodeParams = {node_id: movingNodeId};
	// If we are not at the root of the project, add the parent node id to the
	// request params
	if (ProjectUtils.isProject() != 'True') {
		moveNodeParams.dest_parent_node_id = ProjectUtils.nodeId();
	}

	$.post(urlNodeMove, moveNodeParams,
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
	$.post(urlNodeFeature, {node_id : ProjectUtils.nodeId()},
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
	$.post(urlNodeDelete, {node_id : ProjectUtils.nodeId()},
		function(data){
		// Feedback logic
	})
	.done(function(){
		statusBarSet('success', 'Node deleted', 'pi-trash');
		if (ProjectUtils.parentNodeId() != '') {
			displayNode(ProjectUtils.parentNodeId());
		} else {
			// Display the project when the group is at the root of the tree
			displayProject(ProjectUtils.projectId());
		}
	});
});


/* Toggle public */
$('#item_toggle_public').click(function(e){
	e.preventDefault;
	var currentNodeId = ProjectUtils.nodeId();
	$.post(urlNodeTogglePublic, {node_id : currentNodeId},
		function(data){
		// Feedback logic
	})
	.done(function(data){
		statusBarSet('success', data.data.message);
		displayNode(currentNodeId);
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
