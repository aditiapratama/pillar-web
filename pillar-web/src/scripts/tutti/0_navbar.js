$(function () {
	$('[data-toggle="tooltip"]').tooltip()
})

function NavbarTransparent() {

	var startingpoint = 80;

	$(window).on("scroll", function () {

		if ($(this).scrollTop() > startingpoint) {
			$('.navbar-overlay, .navbar-transparent').addClass('is-active');
		} else {
			$('.navbar-overlay, .navbar-transparent').removeClass('is-active');
		};
	});
};

NavbarTransparent();
