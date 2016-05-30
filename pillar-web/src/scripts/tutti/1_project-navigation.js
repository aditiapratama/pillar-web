function projectNavCollapse() {

	$("#project_nav").addClass('collapsed');
	$('.project_split').addClass('collapsed');

	$("#project_context").addClass('project_nav-collapsed');


	$('.project_nav-expand-btn').show();
	$('.project_nav-collapse-btn').hide();

	$("ul.breadcrumb.context").addClass('active');

	if (typeof Ps !== 'undefined'){
		Ps.destroy(document.getElementById('project_tree'));
	};
};

function projectNavExpand() {

	$("#project_nav").removeClass('collapsed');
	$('.project_split').removeClass('collapsed');

	$("#project_context").removeAttr('class');


	$('.project_nav-expand-btn').hide();
	$('.project_nav-collapse-btn').show();

	$("ul.breadcrumb.context").removeClass('active');

	if (typeof Ps !== 'undefined'){
		Ps.initialize(document.getElementById('project_tree'), {suppressScrollX: true});
	};
};

function projectNavCheck(){

	/* Only run if we're in a project */
	if(document.getElementById("project-flex") !== null) {

		var nav_status = Cookies.get('bcloud_ui_nav_collapse');

		if (nav_status) {
			if (nav_status == 'expanded') {
				projectNavExpand();

			} else if ( nav_status == 'collapsed' ) {
				projectNavCollapse();
			}
		} else {
			projectNavExpand();
		}

	}
}

function projectNavToggle(){

	var nav_status = Cookies.get('bcloud_ui_nav_collapse');

	if (nav_status) {
		if (nav_status == 'expanded') {

			projectNavCollapse();
			Cookies.set('bcloud_ui_nav_collapse', 'collapsed');

		} else if ( nav_status == 'collapsed' ) {

			projectNavExpand();
			Cookies.set('bcloud_ui_nav_collapse', 'expanded');

		}
	} else {
		projectNavCollapse();
		Cookies.set('bcloud_ui_nav_collapse', 'collapsed');
	}
}

$('.project_split, .project_nav-collapse-btn, .project_nav-expand-btn').on('click', function (e) {
	projectNavToggle();
});

/* Check if we're in a project */
if(document.getElementById("project_container") !== null) {

	$(document).keypress(function(e) {
		var tag = e.target.tagName.toLowerCase();

		/* Toggle when pressing [T] key */
		if(e.which == 116 && tag != 'input' && tag != 'textarea' && !e.ctrlKey && !e.metaKey && !e.altKey) {
			projectNavToggle();
		}
	});
}

/* Check on load */
$( document ).ready(function() {
	projectNavCheck();
});


/* Small utility to enable specific node_types under the Add New dropdown */
/* It takes:
	 * empty: Enable every item
	 * false: Disable every item
	 * array: Disable every item except a list of node_types, e.g: ['asset', 'group']
*/
function addMenuEnable(node_types){
	$("#item_add").parent().removeClass('disabled');
	$("ul.add_new-menu li[class^='button-']").hide().addClass('disabled');

	if (node_types === undefined) {
		$("ul.add_new-menu li[class^='button-']").show().removeClass('disabled');
	} else if (node_types == false) {
		$("#item_add").parent().addClass('disabled');
	} else {
		$.each(node_types, function(index, value) {
			$("ul.add_new-menu li[class*='button-" + value +"']").show().removeClass('disabled');
		});
	}
}

function addMenuDisable(node_types){
	$.each(node_types, function(index, value) {
		$("ul.add_new-menu li[class*='button-" + value +"']").addClass('disabled');
	});
}

/* Completely hide specific items (like Texture when on project root) */
function addMenuHide(node_types){
	$.each(node_types, function(index, value) {
		$("ul.add_new-menu li[class*='button-" + value +"']").hide().addClass('disabled');
	});
}
