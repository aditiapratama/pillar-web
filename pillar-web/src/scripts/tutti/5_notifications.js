
// Store the title, to later append notifications count
var page_title = document.title;

var unread_on_load = 0;
var unread_new = 0;


function getNotificationsOnce() {
	$.getJSON( "/notifications/", function( data ) {
		unread_on_load = data['items'].length;
	});
};


// getNotifications by fetching json every X seconds
function getNotifications(){
	$.getJSON( "/notifications/", function( data ) {

		var items = [];
		unread_new = 0;

		// Only if there's actual data
		if (data['items'][0]){

			// Loop through each item
			$.each(data['items'], function(i, no){

				// Increase the unread_new counter
				if (!no['is_read']){ unread_new++ };

				// Check if the current item has been read, to style it
				var is_read = no['is_read'] ? 'is_read' : '';

				var read_info = 'data-id="'+ no['_id'] + '" data-read="' + no['is_read'] + '"';

				// Notification list item
				var content = '<li class="nc-item ' + is_read +'" data-id="'+ no['_id'] + '">';

					// User's avatar
					content += '<div class="nc-avatar">';
						content += '<img ' + read_info + ' src="' + no['username_avatar'] + '"/> ';
					content += '</div>';

					// Text of the notification
					content += '<div class="nc-text">';

						// Username and action
						content += no['username'] + ' ' + no['action'] + ' ';

						// Object
						content += '<a ' + read_info + '" href="' + no['context_object_url'] + '">';
							content += no['context_object_name'] + ' ';
						content += '</a> ';

						// Date
						content += '<span class="nc-date">';
							content += '<a ' + read_info + '" href="' + no['context_object_url'] + '">' + no['date'] + '</a>';
						content += '</span>';

						// Read Toggle
						content += '<a href="/notifications/' + no['_id'] + '/read-toggle" class="nc-button nc-read_toggle">';
							if (no['is_read']){
								content += '<i title="Mark as Unread" class="pi pi-circle-dot"></i>';
							} else {
								content += '<i title="Mark as Read" class="pi pi-circle"></i>';
							};
						content += '</a>';

						// // Subscription Toggle
						// content += '<a href="/notifications/' + no['_id'] + '/subscription-toggle" class="nc-button nc-subscription_toggle">';
						// 	if (no['is_subscribed']){
						// 		content += '<i title="Turn Off Notifications" class="fa fa-toggle-on"></i>';
						// 	} else {
						// 		content += '<i title="Turn On Notifications" class="fa fa-toggle-off"></i>';
						// 	};
						// content += '</a>';

					content += '</div>';
				content += '</li>';

				items.push(content);
			}); // each

			if (unread_new > 0) {
				// Set page title, display notifications and set counter
				document.title = '(' + unread_new + ') ' + page_title;
				$('#notifications-count').addClass('bloom');
				$('#notifications-count').html('<span>' + unread_new + '</span>');
				$('#notifications-toggle i').removeClass('pi-notifications-none').addClass('pi-notifications-active');
			} else {
				document.title = page_title;
				$('#notifications-count').removeAttr('class');
				$('#notifications-toggle i').removeClass('pi-notifications-active').addClass('pi-notifications-none');
			};
		} else {
			var content = '<li class="nc-item nc-item-empty">';
			content += 'No notifications... yet.';
			content += '</li>';

			items.push(content);

		}; // if items

		// Populate the list
		$('ul#notifications-list').html( items.join('') );

		checkPopNotification(
				data['items'][0]['username'],
				data['items'][0]['username_avatar'],
				data['items'][0]['action'],
				data['items'][0]['date'],
				data['items'][0]['context_object_name'],
				data['items'][0]['context_object_url'])

	})
	.done(function(){
		// clear the counter
		unread_on_load = unread_new;
	});
};


// Used when we click somewhere in the page
function hideNotifications(){
	$('#notifications').hide();
	$('#notifications-toggle').removeClass('active');
};

// Click anywhere in the page to hide #notifications
$(document).click(function() { hideNotifications(); });
// ...but clicking inside #notifications shouldn't hide itself
$('#notifications').on('click', function(e){ e.stopPropagation(); });


function popNotification(){

	// pop!
	$("#notification-pop").addClass('in');

	// After 10s, add a class to make it disappear
	setTimeout(function(){
		$("#notification-pop").addClass('out');

		// And a second later, remove all classes
		setTimeout(function(){
			$("#notification-pop").removeAttr('class');
		}, 1000);

	}, 10000);

	// Set them the same so it doesn't pop up again
	unread_on_load = unread_new;
};


function checkPopNotification(username, username_avatar, action, date, context_object_name, context_object_url){

	// If there's new content
	if (unread_new > unread_on_load){

		$('#notification-pop').data('url', context_object_url);

		var text = '<span class="nc-author">' + username + '</span> ';
		text += action;

		text += ' <a href="' + context_object_url + '">';
			text += context_object_name + ' ';
		text += '</a>';

		text += '<span class="nc-date">';
			text += ' <a href="' + context_object_url + '">';
				text += date;
			text += '</a>';
		text += '</span>';

		$('#notification-pop .nc-text').html(text);
		$('#notification-pop .nc-avatar img').attr('src', username_avatar);

		popNotification();

	};
};


// Function to set #notifications flyout height and resize if needed
function notificationsResize(){
	var height = $(window).height() - 80;

	if ($('#notifications').height() > height){
		$('#notifications').css({
				'max-height' : height / 2,
				'overflow-y' : 'scroll'
			}
		);
	} else {
		$('#notifications').css({
				'max-height' : '1000%',
				'overflow-y' : 'initial'
			}
		);
	};
};


// Toggle the #notifications flyout
$('#notifications-toggle').on('click', function(e){
	e.stopPropagation();

	$('#notifications').toggle();
	$(this).toggleClass("active");

	notificationsResize();
	getNotifications();
});


$('#notification-pop').on('click', function(e){
	e.stopPropagation();
	window.location.href = $(this).data('url');
});


// Read/Subscription Toggles
$('ul#notifications-list').on('click', '.nc-button', function(e){
	e.preventDefault();

	$.get($(this).attr('href'));
	getNotifications();
});


// Mark All as Read
$('#notifications-markallread').on('click', function(e){
	e.preventDefault();

	$.get("/notifications/read-all");

	$('ul#notifications-list li.nc-item:not(.is_read)').each(function(){
		$(this).addClass('is_read');
	});

	document.title = page_title;
	$('#notifications-count').removeAttr('class');
	$('#notifications-toggle i').removeClass('pi-notifications-active').addClass('pi-notifications-none');

	unread_on_load = unread_new;
});


function getNotificationsLoop() {
	getNotifications();

	setTimeout(function () {
		getNotificationsLoop();
	}, 10000);
}
