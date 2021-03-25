var sl = document.getElementById('speaker-list');
var locDD = document.getElementById('location-dropdown');

document.querySelectorAll('button[name="action"]').forEach(function(el) {
	el.addEventListener('click', function() {
		if (el.getAttribute('value') !== 'remove' && locDD.value === '---') {
			locDD.classList.add('is-invalid');
			return;
		}
		locDD.classList.remove('is-invalid');
		
		var xhr = new XMLHttpRequest();
		xhr.addEventListener('load', function() {
			document.getElementById('speaker-controls').style.display = 'flex';
			document.getElementById('adding-spinner').style.display = 'none';
		});
		xhr.open('GET', '/ajax/speakerAdd?action=' + el.getAttribute('value'));
		document.getElementById('speaker-controls').style.display = 'none';
		document.getElementById('adding-spinner').style.display = 'block';
		xhr.send();
	});
});

locDD.addEventListener('change', function() {
	locDD.classList.remove('is-invalid');
});

function removeSpeaker(evt) {
	var elItem = evt.target.parentNode.parentNode.parentNode.parentNode;
	var xhr = new XMLHttpRequest();
	xhr.open('GET', '/ajax/speakerRemove?delegateId=' + elItem.dataset.delegateId);
	xhr.send();
	evt.preventDefault();
}

// Superadmin stuff

if (is_superadmin) {
	var dragulaSL = dragula([sl]);
	
	dragulaSL.on("drop", function(el, target, source, sibling) {
		var order = Array.from(sl.querySelectorAll('.list-group-item'), (el) => el.dataset.delegateId).join(',');
		var xhr = new XMLHttpRequest();
		xhr.open('GET', '/ajax/reorderSpeakers?order=' + order);
		xhr.send();
	});
	
	document.getElementById('mode-dropdown').addEventListener('click', function() {
		var xhr = new XMLHttpRequest();
		xhr.open('GET', '/ajax/changeSpeakingMode?mode=' + document.getElementById('mode-dropdown').value);
		xhr.send();
	});
}

// Live refresh

var ws = new WebSocket(
	(window.location.protocol === 'https:' ? 'wss://' : 'ws://')
	+ window.location.host
	+ '/ws/speaker-list/'
);

var delegate_id;

ws.onmessage = function(event) {
	//console.log("WebSocket message received:", event);
	data = JSON.parse(event.data);
	
	if (data.type === 'init') {
		delegate_id = data.delegate_id;
		
		// Hide initial loading spinner
		document.getElementById('speaker-controls').style.display = 'flex';
		document.getElementById('adding-spinner').style.display = 'none';
	}
	
	if (data.type === 'init' || data.type === 'speakerlist_updated') {
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
				if (speaker.intention === 1) {
					elItem.classList.add('list-group-item-danger');
				} else if (speaker.intention === 2) {
					elItem.style.borderLeft = '0.5em solid #198754';
				} else if (speaker.intention === 3) {
					elItem.style.borderLeft = '0.5em solid #ffc107';
				} else if (speaker.delegate.first_time) {
					elItem.classList.add('list-group-item-primary');
				}
				elItem.dataset.delegateId = speaker.delegate.id;
				sl.appendChild(elItem);
				
				var elL1 = document.createElement('div');
				elL1.className = 'h5 d-flex mb-0';
				elItem.appendChild(elL1);
				
				var elName = document.createElement('span');
				elName.innerText = speaker.delegate.name;
				elName.style.flexGrow = '1';
				elL1.appendChild(elName);
				if (is_superadmin) {
					var elA = document.createElement('a');
					elA.href = '#';
					elA.className = 'text-muted';
					elA.innerHTML = '<i class="bi bi-x-circle ms-1"></i>';
					elA.addEventListener('click', removeSpeaker);
					elName.appendChild(elA);
				}
				
				// Intention text
				if (speaker.intention === 2) {
					var elIntention = document.createElement('span');
					elIntention.innerText = 'FOR';
					elL1.appendChild(elIntention);
				} else if (speaker.intention === 3) {
					var elIntention = document.createElement('span');
					elIntention.innerText = 'AGAINST';
					elL1.appendChild(elIntention);
				}
				
				// Icon
				if (speaker.intention === 1) {
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
		
		var on_list = data.speakerlist.some((s) => s.delegate.id == delegate_id);
		
		// Update button states
		document.querySelectorAll('.speaker-controls-mode').forEach(function(el) { el.style.display = 'none'; });
		if (data.mode === 'standard') {
			document.getElementById('controls-standard').style.display = 'flex';
			if (on_list) {
				document.querySelectorAll('button[name="action"][value="add"]').forEach(function(el) { el.style.display = 'none'; });
				document.querySelectorAll('button[name="action"][value="remove"]').forEach(function(el) { el.style.display = 'inline'; });
			} else {
				document.querySelectorAll('button[name="action"][value="add"]').forEach(function(el) { el.style.display = 'inline'; });
				document.querySelectorAll('button[name="action"][value="remove"]').forEach(function(el) { el.style.display = 'none'; });
			}
		} else if (data.mode === 'rollcall') {
			document.getElementById('controls-rollcall').style.display = 'flex';
			if (on_list) {
				document.querySelectorAll('button[name="action"][value="add"]').forEach(function(el) { el.style.display = 'none'; });
				document.querySelectorAll('button[name="action"][value="remove"]').forEach(function(el) { el.style.display = 'inline'; });
			} else {
				document.querySelectorAll('button[name="action"][value="add"]').forEach(function(el) { el.style.display = 'inline'; });
				document.querySelectorAll('button[name="action"][value="remove"]').forEach(function(el) { el.style.display = 'none'; });
			}
		} else if (data.mode === 'formal') {
			if (on_list) {
				document.getElementById('controls-formal-remove').style.display = 'flex';
				document.querySelectorAll('button[name="action"][value="remove"]').forEach(function(el) { el.style.display = 'inline'; });
			} else {
				document.getElementById('controls-formal-add-for').style.display = 'flex';
				document.getElementById('controls-formal-add-against').style.display = 'flex';
			}
		}
		
		$('[data-toggle="tooltip"]').tooltip();
	}
};
