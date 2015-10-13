
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
	$('body').on('click', '.comment-action-cancel', function(){
		$('.comment-reply-container').detach().prependTo('#comments-list');
	});


	/* Rate */
	$('body').on('click', '.comment-action-rating', function(){

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
