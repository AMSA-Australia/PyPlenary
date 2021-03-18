var ws = new WebSocket(
	(window.location.protocol === 'https:' ? 'wss://' : 'ws://')
	+ window.location.host
	+ '/ws/speaker-list/'
);

ws.onmessage = function(event) {
	console.log("WebSocket message received:", event);
};
