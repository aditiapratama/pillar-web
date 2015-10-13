function NavbarTransparent() {

	startingpoint = 80;

	$(window).on("scroll", function () {

		scroll = Math.min(Math.max(parseInt(($(this).scrollTop() - startingpoint)), 0), $(this).scrollTop());

		if ($(this).scrollTop() > startingpoint) {
			$('.navbar-overlay, .navbar-transparent').addClass('is-active');
		} else {
			$('.navbar-overlay, .navbar-transparent').removeClass('is-active');
		};
	});
};

NavbarTransparent();
