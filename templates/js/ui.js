let ws = null;
let isEncoding = false;
let filesData = [];
let lastFullData = null;
let settingsOpen = false;


function connect() {
	const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
	ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

	ws.onopen = () => {
		updateConnectionStatus(true);
	};

	ws.onmessage = (event) => {
		const data = JSON.parse(event.data);

		if (data.type === 'full') {
			lastFullData = data;
			filesData = data.files;
			updateEncodeSettings(data.encode_settings);
			// 설정 페이지를 보는 동안에는 목록 갱신이 페이지를 덮어쓰지 않도록 한다.
			if (!settingsOpen) {
				updateFileList(data);
			}
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


function updateEncodeSettings(settings) {
	if (!settings) return;
	const resolution = (settings.default_resolution || 'HD').toUpperCase();
	const crf = (settings.crf === null || settings.crf === undefined) ? '자동' : escapeHtml(settings.crf);
	document.getElementById('encodeSettings').innerHTML = `
		<span><span class="info-label">코덱:</span> ${escapeHtml(settings.codec)}</span>
		<span><span class="info-label">Preset:</span> ${escapeHtml(settings.preset)}</span>
		<span><span class="info-label">CRF:</span> ${crf}</span>
		<span class="encode-settings-right">
			<label for="defaultResolutionSelect">기본 해상도:</label>
			<select id="defaultResolutionSelect" onchange="changeDefaultResolution(this.value)">
				<option value="HD" ${resolution === 'HD' ? 'selected' : ''}>HD (1280)</option>
				<option value="FHD" ${resolution === 'FHD' ? 'selected' : ''}>FHD (1920)</option>
			</select>
		</span>
	`;
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
	if (file.status === 'in_progress' && file.progress) {
		progressBarHtml = `
			<div class="progress-bar-container">
				<div class="progress-bar" style="width: ${file.progress.percent}%">
					${file.progress.percent}%
				</div>
			</div>
		`;
	}

	const progressInfoHtml = buildProgressInfoHtml(file);
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
		const anchor = element.querySelector('.progress-bar-container') || existingVideoInfo;
		if (anchor) {
			anchor.insertAdjacentHTML('afterend', progressInfoHtml);
		}
	}
}


// 진행 중 파일은 Frame/FPS/Size/Time/Bitrate/Speed 를, 완료 파일은 파일크기·소요시간 요약을 표시한다.
function buildProgressInfoHtml(file) {
	if (file.status === 'in_progress' && file.progress) {
		return `
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
					<span class="progress-label">Time:</span> ${formatTimeWithEta(file)}
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

	if (file.status === 'completed') {
		const sizeDetail = (0 < file.input_size)
			? ` (원본 ${formatFileSize(file.input_size)} / ${formatCompressionRate(file.output_size, file.input_size)})`
			: '';
		const outputItem = file.output_filename
			? `<div class="progress-item">
					<span class="progress-label">출력:</span> ${file.output_filename}
				</div>`
			: '';

		return `
			<div class="progress-info completed-info">
				${outputItem}
				<div class="progress-item">
					<span class="progress-label">파일크기:</span> ${formatFileSize(file.output_size)}${sizeDetail}
				</div>
				<div class="progress-item">
					<span class="progress-label">소요시간:</span> ${formatDuration(file.elapsed_seconds)}
				</div>
			</div>
		`;
	}

	return '';
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
	data.files.forEach((file, index) => {
		// 바로 위가 완료·진행 중 파일이면 위로 이동 불가
		const canMoveUp = index > 0 && !['completed', 'in_progress'].includes(data.files[index - 1].status);
		const statusClass = `status-${file.status}`;
		const itemClass = file.status;
		
		const canChangeResolution = file.status === 'pending' && file.video_info.resolution;
		
		let resolutionSelector = '';
		if (canChangeResolution) {
			resolutionSelector = `
				<div class="resolution-selector">
					<label>해상도:</label>
					<select onchange="changeResolution('${file.filename}', this.value)">
						<option value="hd" ${file.resolution_mode.toLowerCase() === 'hd' ? 'selected' : ''}>HD (1280)</option>
						<option value="fhd" ${file.resolution_mode.toLowerCase() === 'fhd' ? 'selected' : ''}>FHD (1920)</option>
					</select>
				</div>
			`;
		}
		
		let videoInfoHtml = '';
		if (file.video_info) {
			const subtitle = file.subtitle ? '🟢 자막' : '✗ 자막';
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
					<div class="info-item output-info-item">
						<span class="info-icon">📤</span>
						<span class="info-label">출력:</span> ${file.output_filename}
					</div>
					` : ''}
				</div>
			`;
		}
		
		let progressBarHtml = '';
		if (file.status === 'in_progress' && file.progress) {
			progressBarHtml = `
				<div class="progress-bar-container">
					<div class="progress-bar" style="width: ${file.progress.percent}%">
						${file.progress.percent}%
					</div>
				</div>
			`;
		}
		const progressInfoHtml = buildProgressInfoHtml(file);
		
		html += `
			<div class="file-item ${itemClass}">
				<div class="file-header">
					<div>
						<span class="filename">${file.filename}</span>
						${file.output_filename && file.output_filename !== file.filename ? 
							`<span class="output-filename">→ ${file.output_filename}</span>` : ''}
					</div>
					<div class="file-header-right">
						${file.status === 'pending' ? `
						<div class="move-buttons">
							<button onclick="moveFile('${file.filename}', 'first')" ${canMoveUp ? '' : 'disabled'}>⏫ 처음으로</button>
							<button onclick="moveFile('${file.filename}', 'up')" ${canMoveUp ? '' : 'disabled'}>🔼 한칸위</button>
							<button onclick="moveFile('${file.filename}', 'down')">🔽 한칸아래</button>
							<button onclick="moveFile('${file.filename}', 'last')">⏬ 마지막으로</button>
						</div>
						` : ''}
						${resolutionSelector}
						${file.status === 'completed' ? `
						<button class="btn-reencode" onclick="reencodeFile('${file.filename}')">🔄 재인코딩</button>
						` : ''}
						<span class="status-badge ${statusClass}">${file.status}</span>
					</div>
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


// 바이트 단위 파일 크기를 읽기 쉬운 단위로 변환한다.
function formatFileSize(bytes) {
	if (!bytes || bytes <= 0) return '-';
	const units = ['B', 'KB', 'MB', 'GB', 'TB'];
	let value = bytes;
	let unit = 0;
	while (value >= 1024 && unit < units.length - 1) {
		value /= 1024;
		unit++;
	}
	return `${value.toFixed(unit === 0 ? 0 : 2)} ${units[unit]}`;
}


// 압축률 = (원본 크기 - 출력 크기) / 원본 크기 * 100
function formatCompressionRate(outputBytes, inputBytes) {
	if (!outputBytes || !inputBytes || inputBytes <= 0) return '-';
	const rate = Math.max(0, (1 - outputBytes / inputBytes) * 100);
	return `${rate.toFixed(1)}%`;
}


// "HH:MM:SS.ms" 형식의 FFmpeg 시간 문자열을 초 단위로 변환 (형식이 다르면 null)
function parseTimeToSeconds(timeStr) {
	const parts = (timeStr || '').split(':');
	if (parts.length !== 3) return null;
	const seconds = parseInt(parts[0], 10) * 3600 + parseInt(parts[1], 10) * 60 + parseFloat(parts[2]);
	return isNaN(seconds) ? null : seconds;
}


// 인코딩된 영상 시간 뒤에 남은 예상 시간((전체 길이 - 현재 위치) / speed)을 붙여 반환
function formatTimeWithEta(file) {
	const current = parseTimeToSeconds(file.progress.time);
	const speed = parseFloat(file.progress.speed);
	const duration = file.video_info ? file.video_info.duration : 0;
	// 프레임 기준((전체 프레임 - 현재 프레임) / 인코딩 fps), 불가하면 time 기준((전체 길이 - 현재 위치) / speed)
	const totalFrames = file.video_info ? duration * file.video_info.fps : 0;

	let eta = '--:--:--';
	if (totalFrames > 0 && file.progress.fps > 0) {
		eta = formatDuration(Math.max(totalFrames - file.progress.frame, 0) / file.progress.fps);
	} else if (current !== null && speed > 0 && duration > 0) {
		eta = formatDuration(Math.max(duration - current, 0) / speed);
	}
	return `${file.progress.time} (남은 예상 시간 = ${eta})`;
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


async function refreshFiles() {
	const refreshBtn = document.getElementById('refreshBtn');
	refreshBtn.disabled = true;

	try {
		const response = await fetch('/refresh', { method: 'POST' });
		const result = await response.json();

		if (!result.success) {
			alert(result.message || '새로고침 실패');
		}
	} catch (error) {
		alert('새로고침 중 오류 발생: ' + error.message);
	} finally {
		refreshBtn.disabled = false;
	}
}


async function moveFile(filename, direction) {
	try {
		const response = await fetch('/move-file', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				filename: filename,
				direction: direction
			})
		});

		const result = await response.json();

		if (!result.success) {
			alert(result.message || '순서 변경 실패');
		}
	} catch (error) {
		alert('순서 변경 중 오류 발생: ' + error.message);
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


// 설정 페이지 항목 정의 (conf/encode.json)
const X265_PRESET_OPTIONS = [
	['ultrafast', 'ultrafast (가장 빠름)'],
	['superfast', 'superfast'],
	['veryfast', 'veryfast'],
	['faster', 'faster'],
	['fast', 'fast'],
	['medium', 'medium'],
	['slow', 'slow (기본)'],
	['slower', 'slower'],
	['veryslow', 'veryslow'],
	['placebo', 'placebo (가장 느림)']
];

const SETTINGS_SECTIONS = [
	{
		title: '인코딩',
		fields: [
			{ key: 'video_codec', label: '영상 코덱', type: 'select', options: [['libsvtav1', 'SVT-AV1'], ['libx265', 'x265']] },
			{ key: 'svtav1_preset', label: 'SVT-AV1 Preset (0~13)', type: 'number', min: 0, max: 13, step: 1, codec: 'libsvtav1', help: '0 = 가장 느림·최고 품질, 13 = 가장 빠름' },
			{ key: 'x265_preset', label: 'x265 Preset', type: 'select', options: X265_PRESET_OPTIONS, codec: 'libx265', help: '빠를수록 인코딩은 빨라지고 품질·압축 효율은 낮아집니다. x265는 항상 10 bit로 인코딩합니다' },
			{ key: 'svtav1_bit_depth', label: 'SVT-AV1 비트 깊이', type: 'select', options: [['8', '8 bit'], ['10', '10 bit']], codec: 'libsvtav1', help: 'SVT-AV1 픽셀 포맷입니다' },
			{ key: 'crf', label: 'CRF (비우면 자동)', type: 'number', min: 0, max: 63, step: 1, nullable: true },
			{ key: 'volume', label: '볼륨', type: 'number', min: 0, max: 10, step: 0.05 },
			{ key: 'audio_bitrate', label: '오디오 비트레이트', type: 'text' },
			{ key: 'default_resolution', label: '기본 해상도', type: 'select', options: [['HD', 'HD (1280)'], ['FHD', 'FHD (1920)']] }
		]
	},
	{
		title: '검색·저장',
		fields: [
			{ key: 'search_subfolders', label: '하위 폴더 내 영상 검색', type: 'checkbox', help: '입력 디렉토리 아래 모든 폴더의 MP4 파일을 검색합니다 (기본: 사용 안 함)' },
			{ key: 'preserve_folder_structure', label: '원본 폴더 구조 유지', type: 'checkbox', help: '출력 디렉토리에 입력 파일의 하위 폴더 구조를 그대로 만듭니다 (기본: 사용 안 함)' }
		]
	},
	{
		title: '경로',
		fields: [
			{ key: 'ffmpeg_path', label: 'FFmpeg 경로', type: 'text' },
			{ key: 'ffprobe_path', label: 'FFprobe 경로', type: 'text' },
			{ key: 'input_dir', label: '입력 디렉토리', type: 'text' },
			{ key: 'output_dir', label: '출력 디렉토리', type: 'text' },
			{ key: 'subtitle_dir', label: '자막 디렉토리', type: 'text' },
			{ key: 'log_dir', label: '로그 디렉토리', type: 'text' }
		]
	}
];


function escapeHtml(value) {
	const text = (value === null || value === undefined) ? '' : String(value);
	return text.replace(/[&<>"']/g, (char) => ({
		'&': '&amp;',
		'<': '&lt;',
		'>': '&gt;',
		'"': '&quot;',
		"'": '&#39;'
	}[char]));
}


async function putSettings(payload) {
	try {
		const response = await fetch('/settings', {
			method: 'PUT',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(payload)
		});
		return await response.json();
	} catch (error) {
		alert('설정 저장 중 오류 발생: ' + error.message);
		return null;
	}
}


async function changeDefaultResolution(resolution) {
	const result = await putSettings({ default_resolution: resolution });

	if (!result || !result.success) {
		alert((result && result.message) || '기본 해상도 변경 실패');
		// 실패하면 마지막으로 알려진 값으로 되돌린다.
		const select = document.getElementById('defaultResolutionSelect');
		if (select && lastFullData && lastFullData.encode_settings) {
			select.value = (lastFullData.encode_settings.default_resolution || 'HD').toUpperCase();
		}
	}
}


function renderSettingsField(field, value) {
	const id = `setting_${field.key}`;
	const label = escapeHtml(field.label);
	const help = field.help ? `<small class="settings-help">${escapeHtml(field.help)}</small>` : '';
	const codecClass = field.codec ? ' codec-field' : '';
	const codecAttr = field.codec ? ` data-codec="${escapeHtml(field.codec)}"` : '';

	if (field.type === 'checkbox') {
		return `
			<label class="settings-field settings-checkbox${codecClass}"${codecAttr} for="${id}">
				<input id="${id}" type="checkbox" ${value ? 'checked' : ''}>
				<span>${label}</span>
				${help}
			</label>
		`;
	}

	if (field.type === 'select') {
		const options = field.options.map(([optionValue, optionLabel]) => {
			const selected = (String(optionValue).toLowerCase() === String(value).toLowerCase()) ? 'selected' : '';
			return `<option value="${escapeHtml(optionValue)}" ${selected}>${escapeHtml(optionLabel)}</option>`;
		}).join('');
		const onchange = (field.key === 'video_codec') ? ' onchange="onVideoCodecChange(this.value)"' : '';
		return `
			<label class="settings-field${codecClass}"${codecAttr} for="${id}">
				<span>${label}</span>
				<select id="${id}"${onchange}>${options}</select>
				${help}
			</label>
		`;
	}

	const attributes = (field.type === 'number')
		? `type="number" min="${field.min}" max="${field.max}" step="${field.step}"`
		: 'type="text"';
	return `
		<label class="settings-field${codecClass}"${codecAttr} for="${id}">
			<span>${label}</span>
			<input id="${id}" ${attributes} value="${escapeHtml(value)}" autocomplete="off">
			${help}
		</label>
	`;
}


// 선택한 코덱에 해당하는 preset·bit depth 항목만 표시한다.
function applyCodecFieldVisibility(codec) {
	const normalized = (codec || 'libsvtav1').toLowerCase();
	document.querySelectorAll('.codec-field').forEach((element) => {
		element.style.display = (element.dataset.codec.toLowerCase() === normalized) ? '' : 'none';
	});
}


function onVideoCodecChange(codec) {
	applyCodecFieldVisibility(codec);
}


function renderSettingsPage(settings) {
	const sections = SETTINGS_SECTIONS.map((section) => `
		<div class="settings-section">
			<h3>${escapeHtml(section.title)}</h3>
			<div class="settings-grid">
				${section.fields.map((field) => renderSettingsField(field, settings[field.key])).join('')}
			</div>
		</div>
	`).join('');

	document.getElementById('fileList').innerHTML = `
		<div class="settings-page">
			<div class="settings-header">
				<h2>⚙️ 기본 설정</h2>
				<button class="btn btn-secondary" onclick="closeSettings()">✖ 닫기</button>
			</div>
			<p class="settings-hint">
				저장하면 conf/encode.json 에 기록되고 실행 중인 인코더에 바로 반영됩니다.
				해상도 변경은 아직 시작하지 않은 파일에만 적용됩니다.
			</p>
			${sections}
			<div class="settings-actions">
				<button class="btn btn-primary" onclick="saveSettings()">💾 저장</button>
				<span class="settings-status" id="settingsStatus"></span>
			</div>
		</div>
	`;

	applyCodecFieldVisibility(settings.video_codec || 'libsvtav1');
}


async function openSettings() {
	try {
		const response = await fetch('/settings');
		const result = await response.json();

		if (!result.success) {
			alert(result.message || '설정을 불러오지 못했습니다');
			return;
		}

		settingsOpen = true;
		renderSettingsPage(result.settings);
	} catch (error) {
		alert('설정을 불러오는 중 오류 발생: ' + error.message);
	}
}


function closeSettings() {
	settingsOpen = false;
	if (lastFullData) {
		updateFileList(lastFullData);
	} else {
		document.getElementById('fileList').innerHTML = `
			<div class="empty-state">
				<p>인코딩할 파일이 없습니다</p>
			</div>
		`;
	}
}


function toggleSettings() {
	if (settingsOpen) {
		closeSettings();
	} else {
		openSettings();
	}
}


async function saveSettings() {
	const status = document.getElementById('settingsStatus');
	const payload = {};

	for (const section of SETTINGS_SECTIONS) {
		for (const field of section.fields) {
			const input = document.getElementById(`setting_${field.key}`);
			if (!input) continue;

			if (field.type === 'checkbox') {
				payload[field.key] = input.checked;
				continue;
			}

			const raw = input.value.trim();
			payload[field.key] = (field.nullable && raw === '') ? null : raw;
		}
	}

	if (status) {
		status.textContent = '저장 중...';
		status.className = 'settings-status';
	}

	const result = await putSettings(payload);
	if (!result || !result.success) {
		const errors = (result && result.errors) ? Object.values(result.errors).join('\n') : '';
		const message = errors || (result && result.message) || '설정 저장 실패';
		if (status) {
			status.textContent = message.replace(/\n/g, ' / ');
			status.className = 'settings-status error';
		}
		alert(message);
		return;
	}

	if (status) {
		status.textContent = '✓ 저장했습니다';
		status.className = 'settings-status success';
	}
}


async function reencodeFile(filename) {
	if (!confirm(`"${filename}" 파일을 다시 인코딩하시겠습니까?\n기존 출력 파일은 덮어씁니다.`)) return;

	try {
		const response = await fetch('/reencode', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ filename: filename })
		});

		const result = await response.json();
		if (!result.success) {
			alert(result.message || '재인코딩 실패');
		}
	} catch (error) {
		alert('재인코딩 중 오류 발생: ' + error.message);
	}
}


connect();