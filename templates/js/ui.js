let ws = null;
let isEncoding = false;
let filesData = [];


function connect() {
	const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
	ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
	
	ws.onopen = () => {
		updateConnectionStatus(true);
	};
	
	ws.onmessage = (event) => {
		const data = JSON.parse(event.data);
		
		if (data.type === 'full') {
			filesData = data.files;
			updateFileList(data);
			updateOverallProgress(data);
		} else if (data.type === 'current') {
			updateCurrentFile(data);
			updateOverallProgress(data);
		}
	};
	
	ws.onclose = () => {
		updateConnectionStatus(false);
		setTimeout(connect, 3000);
	};
	
	ws.onerror = () => {
		updateConnectionStatus(false);
	};
}


function updateConnectionStatus(connected) {
	const status = document.getElementById('connectionStatus');
	if (connected) {
		status.innerHTML = '<span class="connected">✓ 연결됨</span>';
	} else {
		status.innerHTML = '<span class="disconnected">✗ 연결 끊김</span>';
	}
}


function updateOverallProgress(data) {
	const progressBar = document.getElementById('overallProgressBar');
	const progressText = document.getElementById('progressText');
	const percent = data.overall_progress || 0;
	
	progressBar.style.width = `${percent}%`;
	progressBar.textContent = `${percent.toFixed(1)}%`;
	progressText.textContent = `${data.completed_count || 0} / ${data.total_count || 0} 완료`;
	
	isEncoding = data.current_index >= 0;
	document.getElementById('startBtn').disabled = isEncoding;
	document.getElementById('stopCurrentBtn').disabled = !isEncoding;
	document.getElementById('stopAllBtn').disabled = !isEncoding;
}


function updateCurrentFile(data) {
	if (data.current_file && data.current_index >= 0 && data.current_index < filesData.length) {
		filesData[data.current_index] = data.current_file;
		
		const fileItems = document.querySelectorAll('.file-item');
		if (fileItems[data.current_index]) {
			const fileElement = fileItems[data.current_index];
			updateFileElement(fileElement, data.current_file);
		}
	}
}


function updateFileElement(element, file) {
	element.className = `file-item ${file.status}`;
	
	const statusBadge = element.querySelector('.status-badge');
	if (statusBadge) {
		statusBadge.className = `status-badge status-${file.status}`;
		statusBadge.textContent = file.status;
	}
	
	let progressBarHtml = '';
	let progressInfoHtml = '';
	
	if (file.status === 'in_progress' && file.progress) {
		progressBarHtml = `
			<div class="progress-bar-container">
				<div class="progress-bar" style="width: ${file.progress.percent}%">
					${file.progress.percent}%
				</div>
			</div>
		`;
		progressInfoHtml = `
			<div class="progress-info">
				<div class="progress-item">
					<span class="progress-label">Frame:</span> ${file.progress.frame}
				</div>
				<div class="progress-item">
					<span class="progress-label">FPS:</span> ${file.progress.fps}
				</div>
				<div class="progress-item">
					<span class="progress-label">Size:</span> ${file.progress.size}
				</div>
				<div class="progress-item">
					<span class="progress-label">Time:</span> ${file.progress.time}
				</div>
				<div class="progress-item">
					<span class="progress-label">Bitrate:</span> ${file.progress.bitrate}
				</div>
				<div class="progress-item">
					<span class="progress-label">Speed:</span> ${file.progress.speed}
				</div>
			</div>
		`;
	}
	
	const existingVideoInfo = element.querySelector('.video-info');
	const existingProgressBar = element.querySelector('.progress-bar-container');
	const existingProgressInfo = element.querySelector('.progress-info');
	
	if (existingProgressBar) {
		existingProgressBar.remove();
	}
	if (existingProgressInfo) {
		existingProgressInfo.remove();
	}
	
	if (progressBarHtml) {
		if (existingVideoInfo) {
			existingVideoInfo.insertAdjacentHTML('afterend', progressBarHtml);
		}
	}
	
	if (progressInfoHtml) {
		const newProgressBar = element.querySelector('.progress-bar-container');
		if (newProgressBar) {
			newProgressBar.insertAdjacentHTML('afterend', progressInfoHtml);
		}
	}
}


function updateFileList(data) {
	const fileList = document.getElementById('fileList');
	
	if (!data.files || data.files.length === 0) {
		fileList.innerHTML = `
			<div class="empty-state">
				<svg fill="currentColor" viewBox="0 0 20 20">
					<path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"/>
				</svg>
				<p>인코딩할 파일이 없습니다</p>
			</div>
		`;
		return;
	}
	
	let html = '';
	data.files.forEach((file) => {
		const statusClass = `status-${file.status}`;
		const itemClass = file.status;
		
		const canChangeResolution = file.status === 'pending' && file.video_info.resolution;
		
		let resolutionSelector = '';
		if (canChangeResolution) {
			resolutionSelector = `
				<div class="resolution-selector">
					<label>해상도:</label>
					<select onchange="changeResolution('${file.filename}', this.value)">
						<option value="hd" ${file.resolution_mode === 'hd' ? 'selected' : ''}>HD (1280)</option>
						<option value="fhd" ${file.resolution_mode === 'fhd' ? 'selected' : ''}>FHD (1920)</option>
					</select>
				</div>
			`;
		}
		
		let videoInfoHtml = '';
		if (file.video_info) {
			const subtitle = file.subtitle ? '✓ 자막' : '✗ 자막';
			const scale = file.scale ? `📐 ${file.scale}` : '📐 원본 크기';
			
			videoInfoHtml = `
				<div class="video-info">
					<div class="info-item">
						<span class="info-icon">📹</span>
						<span class="info-label">해상도:</span> ${file.video_info.resolution}
					</div>
					<div class="info-item">
						<span class="info-icon">⏱️</span>
						<span class="info-label">길이:</span> ${formatDuration(file.video_info.duration)}
					</div>
					<div class="info-item">
						<span class="info-icon">🎞️</span>
						<span class="info-label">코덱:</span> ${file.video_info.codec}
					</div>
					<div class="info-item">
						<span class="info-icon">💾</span>
						<span class="info-label">비트레이트:</span> ${file.video_info.bitrate}
					</div>
					<div class="info-item">
						<span class="info-icon">🎬</span>
						<span class="info-label">FPS:</span> ${file.video_info.fps.toFixed(2)}
					</div>
					<div class="info-item">
						<span class="info-icon">${subtitle.startsWith('✓') ? '💬' : '📝'}</span>
						${subtitle}
					</div>
					<div class="info-item">
						<span class="info-icon">🔧</span>
						${scale}
					</div>
					${file.output_filename ? `
					<div class="info-item">
						<span class="info-icon">📤</span>
						<span class="info-label">출력:</span> ${file.output_filename}
					</div>
					` : ''}
				</div>
				${resolutionSelector}
			`;
		}
		
		let progressBarHtml = '';
		let progressInfoHtml = '';
		if (file.status === 'in_progress' && file.progress) {
			progressBarHtml = `
				<div class="progress-bar-container">
					<div class="progress-bar" style="width: ${file.progress.percent}%">
						${file.progress.percent}%
					</div>
				</div>
			`;
			progressInfoHtml = `
				<div class="progress-info">
					<div class="progress-item">
						<span class="progress-label">Frame:</span> ${file.progress.frame}
					</div>
					<div class="progress-item">
						<span class="progress-label">FPS:</span> ${file.progress.fps}
					</div>
					<div class="progress-item">
						<span class="progress-label">Size:</span> ${file.progress.size}
					</div>
					<div class="progress-item">
						<span class="progress-label">Time:</span> ${file.progress.time}
					</div>
					<div class="progress-item">
						<span class="progress-label">Bitrate:</span> ${file.progress.bitrate}
					</div>
					<div class="progress-item">
						<span class="progress-label">Speed:</span> ${file.progress.speed}
					</div>
				</div>
			`;
		}
		
		html += `
			<div class="file-item ${itemClass}">
				<div class="file-header">
					<div>
						<span class="filename">${file.filename}</span>
						${file.output_filename && file.output_filename !== file.filename ? 
							`<span class="output-filename">→ ${file.output_filename}</span>` : ''}
					</div>
					<span class="status-badge ${statusClass}">${file.status}</span>
				</div>
				${videoInfoHtml}
				${progressBarHtml}
				${progressInfoHtml}
			</div>
		`;
	});
	
	fileList.innerHTML = html;
}


function formatDuration(seconds) {
	if (!seconds) return '00:00:00';
	const h = Math.floor(seconds / 3600);
	const m = Math.floor((seconds % 3600) / 60);
	const s = Math.floor(seconds % 60);
	return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}


async function startEncoding() {
	if (isEncoding) return;
	
	try {
		const response = await fetch('/start', { method: 'POST' });
		const result = await response.json();
		
		if (!result.success) {
			alert(result.message || '인코딩 시작 실패');
		}
	} catch (error) {
		alert('인코딩 시작 중 오류 발생: ' + error.message);
	}
}


async function stopCurrent() {
	if (!confirm('현재 파일의 인코딩을 중단하시겠습니까?')) return;
	
	try {
		const response = await fetch('/stop-current', { method: 'POST' });
		const result = await response.json();
		
		if (!result.success) {
			alert(result.message || '중단 실패');
		}
	} catch (error) {
		alert('중단 중 오류 발생: ' + error.message);
	}
}


async function stopAll() {
	if (!confirm('전체 인코딩을 중단하시겠습니까?')) return;
	
	try {
		const response = await fetch('/stop-all', { method: 'POST' });
		const result = await response.json();
		
		if (!result.success) {
			alert(result.message || '중단 실패');
		}
	} catch (error) {
		alert('중단 중 오류 발생: ' + error.message);
	}
}


async function changeResolution(filename, resolution) {
	try {
		const response = await fetch('/set-resolution', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				filename: filename,
				resolution: resolution
			})
		});
		
		const result = await response.json();
		
		if (!result.success) {
			alert(result.message || '해상도 변경 실패');
		}
	} catch (error) {
		alert('해상도 변경 중 오류 발생: ' + error.message);
	}
}


connect();