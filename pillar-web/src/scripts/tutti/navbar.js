function NavbarTransparent(color_txt, color_bg, startingpoint, factor) {

	// Defaults
	startingpoint = typeof startingpoint !== 'undefined' ? startingpoint : 50;
	color_txt = typeof color_txt !== 'undefined' ? color_txt : 255;
	color_bg = typeof color_bg !== 'undefined' ? color_bg : 96;
	factor = typeof factor !== 'undefined' ? factor : 6;

	$(window).on("scroll", function () {

		scroll = Math.min(Math.max(parseInt(($(this).scrollTop() - startingpoint)), 0), $(this).scrollTop());

		if ($(this).scrollTop() > startingpoint) {

			// We start with 0 opacity, and scroll to 1.0
			opacity = ((startingpoint - $(this).scrollTop()) * (-0.5 * factor)) / 50;
			opacity = Math.min(Math.max(parseFloat((opacity)), 0), 1.0)
			$('.navbar-overlay').css('background-color', 'rgba(' + color_bg + ',' + color_bg + ',' + color_bg + ',' + opacity + ')');

			color = 255;

			if (color_bg > 150){
				color = Math.min(Math.max(parseInt((color_bg - (scroll * (1 * factor)))), color_txt), color_bg);
			};

			padding_top = Math.min(Math.max(parseFloat((80 - (scroll * (0.2 * factor)))), 50), 80);
			// padding_sides = Math.min(Math.max(parseFloat((20 - (scroll * (0.1 * factor)))), 15), 20);

			$('.navbar-transparent a').not('.navbar-transparent ul.dropdown-menu li a').css({
				'color' : 'rgb(' + color + ',' + color + ',' + color + ')',
				'height' : padding_top,
				// 'padding-left' : padding_sides,
				// 'padding-right' : padding_sides,
				'text-shadow' : 'none'
			});

		} else {
			$('.navbar-overlay').css('background-color', 'rgba(' + color_bg + ',' + color_bg + ',' + color_bg + ',0)');
			$('.navbar-transparent a').not('.navbar-transparent ul.dropdown-menu li a').css({
				'color' : 'white',
				'height' : '80px',
				// 'padding-top' : '35px',
				// 'padding-left' : '20px',
				// 'padding-right' : '20px',
				'text-shadow' : '
					1px 1px 10px rgba(0,0,0,' + (opacity / 3) + '),
					1px 1px 0 rgba(0,0,0,' + (opacity / 3) + ')'
			});
		};
	});
};

NavbarTransparent();
