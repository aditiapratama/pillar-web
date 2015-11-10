
function projectNavCollapse() {

	$("#project_nav").addClass('collapsed');
	$('.project_split').addClass('collapsed');

	$("#project_context").addClass('project_nav-collapsed');


	$('.project_nav-expand-btn').show();
	$('.project_nav-collapse-btn').hide();

	$("ul.breadcrumb.context").addClass('active');

	if (typeof Ps !== 'undefined'){
		Ps.destroy(document.getElementById('project_nav'));
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
		Ps.initialize(document.getElementById('project_nav'), {suppressScrollX: true});
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
		if(e.which == 116 && tag != 'input' && tag != 'textarea') {
			projectNavToggle();
		}
	});
}

/* Check on load */
$( document ).ready(function() {
	projectNavCheck();
});
