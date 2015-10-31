
function projectNavCollapse() {

	$("#project_nav").addClass('collapsed');
	$('.project_split').addClass('collapsed');

	$("#project_context").addClass('project_nav-collapsed');

	$('#project_nav').perfectScrollbar('destroy');

	$('.project_nav-expand-btn').show();
	$('.project_nav-collapse-btn').hide();

	$("ul.breadcrumb.context").addClass('active');

};

function projectNavExpand() {

	$("#project_nav").removeClass('collapsed');
	$('.project_split').removeClass('collapsed');

	$("#project_context").removeAttr('class');

	$('#project_nav').perfectScrollbar({suppressScrollX: true});

	$('.project_nav-expand-btn').hide();
	$('.project_nav-collapse-btn').show();

	$("ul.breadcrumb.context").removeClass('active');

};

function projectNavCheck(){
	nav_status = Cookies.get('bcloud_ui_nav_collapse');

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

function projectNavToggle(){

	nav_status = Cookies.get('bcloud_ui_nav_collapse');

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

$(document).keypress(function(e) {
	var tag = e.target.tagName.toLowerCase();

	if(e.which == 116 && tag != 'input' && tag != 'textarea') {
		projectNavToggle();
	}
});

$( document ).ready(function() {
	projectNavCheck();
});
