
function projectNavCollapse() {

	$("#project_nav").addClass('project_nav-collapsed');
	$("#project_tree").hide();
	$("#project_context-header").show();

	$('#project_nav').perfectScrollbar('destroy');

	$('#project_nav-collapse-btn').html('<i class="fa fa-angle-double-right"></i>');

};

function projectNavExpand() {

	$("#project_nav").removeClass('project_nav-collapsed');
	$("#project_tree").show();
	$("#project_context-header").hide();

	$('#project_nav').perfectScrollbar({suppressScrollX: true});

	$('#project_nav-collapse-btn').html('<i class="fa fa-angle-double-left"></i>');

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

$('.project_split, #project_nav-collapse-btn').on('click', function (e) {
	projectNavToggle();
});

$( document ).ready(function() {
	projectNavCheck();
});

// $('.project_split').mousedown(function (e) {
// 	e.preventDefault();

// 	$(document).mousemove(function (e) {

// 		e.preventDefault();
// 		var x = e.pageX - $('#project_nav').offset().left;

// 		if (x > 60 && x < 320 && e.pageX < ($(window).width())) {
// 			$('#project_nav').css("width", x);
// 		};

// 		if ($('#project_nav').width() < 60) {
// 			console.log('collapse');
// 			$("#project_nav").addClass('project_nav-collapsed');
// 		}
// 		else if ($('#project_nav').width() > 61) {
// 			$("#project_nav").removeClass('project_nav-collapsed');
// 		}
// 	})
// });

// $(document).mouseup(function (e) {
// 	$(document).unbind('mousemove');
// });
