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
			document.getElementById('loading-spinner').style.display = 'none';
		});
		xhr.open('GET', '/speaker_list/inner');
		document.getElementById('loading-spinner').style.display = 'block';
		xhr.send();
	}
};
