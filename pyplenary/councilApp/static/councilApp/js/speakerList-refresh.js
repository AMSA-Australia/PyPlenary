document.querySelectorAll('button[name="action"]').forEach(function(el) {
	el.addEventListener('click', function(evt) {
		var xhr = new XMLHttpRequest();
		xhr.addEventListener('load', function() {
			document.getElementById('speaker-controls').style.display = 'flex';
			document.getElementById('adding-spinner').style.display = 'none';
			
			var payload = JSON.parse(this.responseText);
			if (payload.btnstate === 'add') {
				document.querySelector('button[name="action"][value="add"]').style.display = 'inline';
				document.querySelector('button[name="action"][value="remove"]').style.display = 'none';
			} else if (payload.btnstate === 'remove') {
				document.querySelector('button[name="action"][value="add"]').style.display = 'none';
				document.querySelector('button[name="action"][value="remove"]').style.display = 'inline';
			}
		});
		xhr.open('GET', '/ajax/speakerAdd?action=' + el.getAttribute('value'));
		document.getElementById('speaker-controls').style.display = 'none';
		document.getElementById('adding-spinner').style.display = 'block';
		xhr.send();
	});
});

// Live refresh

var ws = new WebSocket(
	(window.location.protocol === 'https:' ? 'wss://' : 'ws://')
	+ window.location.host
	+ '/ws/speaker-list/'
);

ws.onmessage = function(event) {
	//console.log("WebSocket message received:", event);
	data = JSON.parse(event.data);
	
	if (data.type === 'speakerlist_updated') {
		// Update the speaker list
		var xhr = new XMLHttpRequest();
		xhr.addEventListener('load', function() {
			document.getElementById('speaker-list').innerHTML = this.responseText;
			document.getElementById('updating-spinner').style.display = 'none';
		});
		xhr.open('GET', '/speaker_list/inner');
		document.getElementById('updating-spinner').style.display = 'block';
		xhr.send();
	}
};
