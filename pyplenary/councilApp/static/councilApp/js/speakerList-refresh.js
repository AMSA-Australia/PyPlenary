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

var sl = document.getElementById('speaker-list');

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
		// Render speaker list
		sl.innerHTML = '';
		if (data.speakerlist.length === 0) {
			var elAlert = document.createElement('div');
			elAlert.className = 'alert alert-secondary';
			elAlert.innerText = 'No delegates are currently on the speaker list.';
			sl.appendChild(elAlert);
		} else {
			for (var speaker of data.speakerlist) {
				var elItem = document.createElement('div');
				elItem.classList.add('list-group-item');
				if (speaker.point_of_order) {
					elItem.classList.add('list-group-item-danger');
				} else if (speaker.delegate.first_time) {
					elItem.classList.add('list-group-item-primary');
				}
				sl.appendChild(elItem);
				
				var elL1 = document.createElement('div');
				elL1.className = 'h5 d-flex mb-0';
				elItem.appendChild(elL1);
				var elName = document.createElement('span');
				elName.innerText = speaker.delegate.name;
				elName.style.flexGrow = '1';
				elL1.appendChild(elName);
				if (speaker.point_of_order) {
					var elIcon = document.createElement('i');
					elIcon.className = 'bi bi-exclamation-triangle-fill';
					elIcon.dataset.toggle = 'tooltip';
					elIcon.title = 'Point of order';
					elL1.appendChild(elIcon);
				} else if (speaker.delegate.first_time) {
					var elIcon = document.createElement('i');
					elIcon.className = 'bi bi-star';
					elIcon.dataset.toggle = 'tooltip';
					elIcon.title = 'First-time attendee';
					elL1.appendChild(elIcon);
				}
				
				var elL2 = document.createElement('span');
				elL2.innerText = 'Speaker ' + speaker.delegate.speakerNum + '. ' + speaker.delegate.role + '.';
				elItem.appendChild(elL2);
			}
		}
	}
};
