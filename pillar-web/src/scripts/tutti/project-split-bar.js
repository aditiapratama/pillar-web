

$('.project_split').mousedown(function (e) {
	e.preventDefault();

	$(document).mousemove(function (e) {

		e.preventDefault();
		var x = e.pageX - $('#project_nav').offset().left;

		if (x > 100 && x < 320 && e.pageX < ($(window).width())) {
			$('#project_nav').css("width", x);
		}
	})
});

$(document).mouseup(function (e) {
	$(document).unbind('mousemove');
});
