
	// Markdown initialization
	var convert = new Markdown.getSanitizingConverter().makeHtml;

	// Define the template for handlebars
	var source = $("#comment-template").html();
	var template = Handlebars.compile(source);


	// Register the helper for generating the comments list
	Handlebars.registerHelper('list', function(context, options) {
		var ret = "";

		// Loop through all first-level comments
		for(var i=0, j=context.length; i<j; i++) {

			/* Convert Markdown for each comment */
			context[i]['content'] = convert(context[i]['content']);

			// Append compiled comment to return string
			ret = ret + options.fn(context[i]);

			// Search for replies to the current comment
			if (context[i]['replies']) {

				var replies = context[i]['replies'];
				var compiled_replies = "";

				// Loop through replies
				for(var r=0, t=replies.length; r<t; r++) {

					// Append compiled replies
					compiled_replies = compiled_replies + options.fn(replies[r]);

				}

				// Append replies list to the return string
				ret = ret + compiled_replies;

			}
		}

		return ret;
	});

	// Helper for the if/else statement
	Handlebars.registerHelper('if', function(conditional, options) {
		if(conditional) {
			return options.fn(this);
		} else {
			return options.inverse(this);
		}
	});



	/* Build the markdown preview when typing in textarea */
	$(function() {
		var $textarea = $('.comment-reply-field textarea'),
				$container = $('.comment-reply-form'),
				$preview = $('.comment-reply-preview');

		// As we type in the textarea
		$textarea.keyup(function() {

			// Convert markdown
			$preview.html(convert($textarea.val()));

			// While we are at it, style when empty
			if ($textarea.val()) {
				$container.addClass('filled');
			} else {
				$container.removeClass('filled');
			};

		}).trigger('keyup');
	});


	/* Reply */
	$('body').on('click', '.comment-action-reply', function(){

		// container of the comment we are replying to
		parentDiv = $(this).closest('.comment-container');

		// container of the first-level comment in the thread
		parentDivFirst = $(this).parent().parent().siblings('.is-first');

		// Get the id of the comment
		if (parentDiv.hasClass('is-reply')) {
			parentNodeId = parentDivFirst.data('node_id');
		} else {
			parentNodeId = parentDiv.data('node_id');
		}

		// Get the textarea and set its parent_id data
		var commentField = document.getElementById('comment_field');
		commentField.setAttribute('data-parent_id', parentNodeId);

		// Add class for styling
		parentDiv.addClass('is-replying');

		// Move comment-reply container field after the parent container
		commentForm = $('.comment-reply-container').detach();
		parentDiv.after(commentForm);
	});


	/* Cancel Reply */
	$('.comment-action-cancel').click(function(){
		$('.comment-reply-container').detach().prependTo('#comments-list');
	});


	/* Rate */
	$('body').on('click', '.comment-rating-action', function(){

		var $this = $(this);
		var nodeId = $this.parent().parent().parent().data('node_id');
		var url = "/nodes/comments/" + nodeId + "/rate";
		var is_positive = true;
		var parentDiv = $this.parent();


		if ($this.hasClass('down')) {
			is_positive = false;
		};

		$.post(url, {'is_positive': is_positive}
		).done(function(data){

			// Add/remove styles for rated statuses
			if (data['data']['is_rated']){

				parentDiv.addClass('rated');

				if (data['data']['is_positive']){
					parentDiv.addClass('positive');
				} else {
					parentDiv.removeClass('positive');
				};

			} else {
				parentDiv.removeClass('rated');
			};

			$this.siblings('.comment-rating-value').text(data['data']['rating_up']);
		});
	});
