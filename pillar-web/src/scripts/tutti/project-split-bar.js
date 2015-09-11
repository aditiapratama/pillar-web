
function projectNavCollapse() {

	$("#project_nav").hide();
	$('.project_split').hide();
	$("#project_context-header").show();

	$("#project_context").addClass('project_nav-collapsed');

	$('#project_nav').perfectScrollbar('destroy');

	$('.project_nav-collapse-btn').html('<i class="fa fa-angle-double-right"></i>');

};

function projectNavExpand() {

	$("#project_nav").show();
	$('.project_split').show();
	$("#project_context-header").hide();

	$("#project_context").removeAttr('class');

	$('#project_nav').perfectScrollbar({suppressScrollX: true});

	$('.project_nav-collapse-btn').html('<i class="fa fa-angle-left"></i>');

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

$('.project_split, .project_nav-collapse-btn').on('click', function (e) {
	projectNavToggle();
});

$( document ).ready(function() {
	projectNavCheck();
});
