$(function () {
	$('[data-toggle="tooltip"]').tooltip({'delay' : {'show': 1250, 'hide': 250}})
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

// Search
var tu = $('#cloud-search').typeahead({hint: true}, {
	source: index.ttAdapter(),
	displayKey: 'name',
	limit: 10,
	minLength: 2,
	templates: {
		suggestion: function(hit) {

			var hitMedia = (hit.media ? ' · <span class="media">'+hit.media+'</span>' : '');
			var hitFree = (hit.is_free ? '<div class="search-hit-ribbon"><span>free</span></div>' : '');
			var hitPicture;

			if (hit.picture){
				hitPicture = '<img src="' + hit.picture + '"/>';
			} else {
				hitPicture = '<div class="search-hit-thumbnail-icon">';
				hitPicture += (hit.media ? '<i class="pi-' + hit.media + '"></i>' : '<i class="dark pi-'+ hit.node_type + '"></i>');
				hitPicture += '</div>';
			};

			return '' +
				'<a href="/nodes/'+ hit.objectID + '/view?redir=1" class="search-site-result" id="'+ hit.objectID + '">' +
					'<div class="search-hit">' +
						'<div class="search-hit-thumbnail">' +
							hitPicture +
							hitFree +
						'</div>' +
						'<div class="search-hit-name" title="' + hit.name + '">' +
							hit._highlightResult.name.value + ' ' +
						'</div>' +
						'<div class="search-hit-meta">' +
							'<span class="project">' + hit._highlightResult.project.name.value + '</span> · ' +
							'<span class="node_type">' + hit.node_type + '</span>' +
							hitMedia +
						'</div>' +
					'</div>'+
				'</a>';
		}
	}
});

$('#cloud-search').bind('typeahead:select', function(ev, hit) {
	$('.search-icon').removeClass('pi-search').addClass('pi-spin spin');
	$('.search-input .advanced').removeClass('active');

	window.location.href = '/nodes/'+ hit.objectID + '/view?redir=1';
});

$('#cloud-search').bind('typeahead:active', function() {
	$('#search-overlay').addClass('active');
	$('.page-body').addClass('blur');
});

$('#cloud-search').bind('typeahead:close', function() {
	$('#search-overlay').removeClass('active');
	$('.page-body').removeClass('blur');
	$('.search-input .advanced').removeClass('active');
});

$('.search-input .search-icon').on('click', function() {
	$('#cloud-search').focus();
});

$( "#cloud-search" ).keyup(function(e) {

	if ( $('.tt-dataset').is(':empty') ){
		$('.search-input .advanced').removeClass('active');
		if(e.keyCode == 13){
			window.location.href = '/search#q='+ $("#cloud-search").val() + '&page=1';
		};
	} else {
		$('.search-input .advanced').addClass('active');
	};
});


