/**
 * Web Player - 메인 애플리케이션
 */

// 전역 변수
let wsClient;
let screenRenderer;
let inputHandler;
let aiCommandHandler;
let fpsUpdateInterval;

// DOM 요소
const elements = {
    connectionStatus: null,
    fpsCounter: null,
    resolution: null,
    loading: null,
    canvas: null,
    btnConnect: null,
    btnDisconnect: null,
    btnFullscreen: null,
    qualitySlider: null,
    qualityValue: null
};

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    console.log('Web Player initializing...');
    initializeElements();
    initializeApp();
});

function initializeElements() {
    elements.connectionStatus = document.getElementById('connection-status');
    elements.fpsCounter = document.getElementById('fps-counter');
    elements.resolution = document.getElementById('resolution');
    elements.loading = document.getElementById('loading');
    elements.canvas = document.getElementById('screen-canvas');
    elements.btnConnect = document.getElementById('btn-connect');
    elements.btnDisconnect = document.getElementById('btn-disconnect');
    elements.btnFullscreen = document.getElementById('btn-fullscreen');
    elements.qualitySlider = document.getElementById('quality-slider');
    elements.qualityValue = document.getElementById('quality-value');
}

function initializeApp() {
    // WebSocket URL 생성
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    // WebSocket 클라이언트 생성
    wsClient = new WebSocketClient(wsUrl);

    // 화면 렌더러 생성
    screenRenderer = new ScreenRenderer('screen-canvas');

    // 입력 핸들러 생성
    inputHandler = new InputHandler(elements.canvas, wsClient, screenRenderer);

    // AI 명령 핸들러 생성
    aiCommandHandler = new AICommandHandler(wsClient);

    // WebSocket 이벤트 핸들러 등록
    wsClient.on('open', handleWebSocketOpen);
    wsClient.on('message', handleWebSocketMessage);
    wsClient.on('error', handleWebSocketError);
    wsClient.on('close', handleWebSocketClose);

    // UI 컨트롤 설정
    setupUIControls();

    // FPS 업데이트 인터벌
    fpsUpdateInterval = setInterval(updateStats, 500);

    // 자동 연결
    wsClient.connect();

    console.log('Web Player initialized');
}

function handleWebSocketOpen(event) {
    console.log('Connected to server');
    updateConnectionStatus('connected', 'Connected');
    hideLoading();
    enableDisconnectButton();
    inputHandler.enable();
    aiCommandHandler.enable();
}

function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'screen':
            screenRenderer.renderFrame(data);
            break;

        case 'status':
            console.log('Status:', data.message);
            if (data.status === 'connected') {
                updateConnectionStatus('connected', 'Connected');
            }
            break;

        case 'ai_response':
            // AI 명령 응답 처리
            aiCommandHandler.handleResponse(data);
            break;

        case 'error':
            console.error('Server error:', data.message);
            showNotification('Error: ' + data.message, 'error');
            break;

        default:
            console.log('Unknown message type:', data.type);
    }
}

function handleWebSocketError(event) {
    console.error('WebSocket error:', event);
    updateConnectionStatus('error', 'Connection Error');
}

function handleWebSocketClose(event) {
    console.log('Disconnected from server');
    updateConnectionStatus('disconnected', 'Disconnected');
    showLoading();
    enableConnectButton();
    inputHandler.disable();
    aiCommandHandler.disable();
    screenRenderer.clear();
}

function setupUIControls() {
    // 연결 버튼
    elements.btnConnect.addEventListener('click', () => {
        wsClient.connect();
        updateConnectionStatus('connecting', 'Connecting...');
    });

    // 연결 해제 버튼
    elements.btnDisconnect.addEventListener('click', () => {
        wsClient.disconnect();
    });

    // 전체화면 버튼
    elements.btnFullscreen.addEventListener('click', () => {
        toggleFullscreen();
    });

    // 품질 슬라이더
    elements.qualitySlider.addEventListener('input', (e) => {
        elements.qualityValue.textContent = e.target.value + '%';
    });

    elements.qualitySlider.addEventListener('change', (e) => {
        const quality = parseInt(e.target.value);
        wsClient.send({
            type: 'config',
            setting: 'quality',
            value: quality
        });
        console.log(`Quality changed to ${quality}%`);
    });

    // ESC 키로 전체화면 종료
    document.addEventListener('fullscreenchange', () => {
        if (!document.fullscreenElement) {
            console.log('Exited fullscreen');
        }
    });
}

function toggleFullscreen() {
    if (!document.fullscreenElement) {
        elements.canvas.requestFullscreen().catch(err => {
            console.error('Fullscreen error:', err);
            showNotification('Fullscreen not available', 'error');
        });
    } else {
        document.exitFullscreen();
    }
}

// UI 업데이트 함수
function updateConnectionStatus(status, message) {
    elements.connectionStatus.textContent = message;
    elements.connectionStatus.className = `status-${status}`;
}

function updateStats() {
    elements.fpsCounter.textContent = `${screenRenderer.getFPS()} FPS`;
    elements.resolution.textContent = screenRenderer.getResolution();
}

function showLoading() {
    elements.loading.classList.remove('hidden');
}

function hideLoading() {
    elements.loading.classList.add('hidden');
}

function enableConnectButton() {
    elements.btnConnect.disabled = false;
    elements.btnDisconnect.disabled = true;
}

function enableDisconnectButton() {
    elements.btnConnect.disabled = true;
    elements.btnDisconnect.disabled = false;
}

function showNotification(message, type = 'info') {
    // 간단한 알림 표시 (콘솔 + alert)
    console.log(`[${type.toUpperCase()}] ${message}`);

    // 프로덕션에서는 토스트 알림 등으로 대체
    if (type === 'error') {
        // 중요한 에러만 alert
        // alert(message);
    }
}

// 클린업
window.addEventListener('beforeunload', () => {
    if (fpsUpdateInterval) {
        clearInterval(fpsUpdateInterval);
    }
    if (wsClient) {
        wsClient.disconnect();
    }
});
