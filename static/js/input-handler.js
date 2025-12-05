/**
 * Web Player - 입력 핸들러
 */
class InputHandler {
    constructor(canvas, wsClient, renderer) {
        this.canvas = canvas;
        this.wsClient = wsClient;
        this.renderer = renderer;
        this.isDragging = false;
        this.dragStartX = 0;
        this.dragStartY = 0;
        this.dragStartCanvasX = 0;
        this.dragStartCanvasY = 0;
        this.enabled = false;

        this.setupEventListeners();
    }

    enable() {
        this.enabled = true;
        console.log('Input handler enabled');
    }

    disable() {
        this.enabled = false;
        console.log('Input handler disabled');
    }

    setupEventListeners() {
        // 마우스 클릭 (click 이벤트는 mouseup 이후 발생하므로 드래그와 구분 가능)
        this.canvas.addEventListener('click', (e) => this.handleClick(e));

        // 더블클릭
        this.canvas.addEventListener('dblclick', (e) => this.handleDoubleClick(e));

        // 우클릭
        this.canvas.addEventListener('contextmenu', (e) => this.handleRightClick(e));

        // 드래그
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        this.canvas.addEventListener('mouseleave', (e) => this.handleMouseLeave(e));

        // 스크롤
        this.canvas.addEventListener('wheel', (e) => this.handleWheel(e), { passive: false });

        // 키보드 (document 레벨)
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
    }

    getCanvasCoords(event) {
        const rect = this.canvas.getBoundingClientRect();
        return {
            canvasX: event.clientX - rect.left,
            canvasY: event.clientY - rect.top
        };
    }

    handleClick(event) {
        console.log('[InputHandler] handleClick called, enabled:', this.enabled);

        if (!this.enabled) {
            console.log('[InputHandler] Click ignored: handler not enabled');
            return;
        }
        if (event.button !== 0) return; // 좌클릭만

        // 드래그였으면 클릭 무시
        if (this.wasDragging) {
            this.wasDragging = false;
            return;
        }

        const { canvasX, canvasY } = this.getCanvasCoords(event);
        console.log('[InputHandler] Canvas coords:', canvasX, canvasY);

        const remoteCoords = this.renderer.canvasToRemoteCoords(canvasX, canvasY);
        console.log('[InputHandler] Remote coords:', remoteCoords);

        const action = {
            type: 'action',
            action_type: 'click',
            x: remoteCoords.x,
            y: remoteCoords.y
        };

        console.log('[InputHandler] Sending action:', action);
        this.wsClient.send(action);

        this.renderer.drawClickFeedback(canvasX, canvasY);
        console.log(`✓ Click sent: (${remoteCoords.x}, ${remoteCoords.y})`);
    }

    handleDoubleClick(event) {
        if (!this.enabled) return;
        event.preventDefault();

        const { canvasX, canvasY } = this.getCanvasCoords(event);
        const remoteCoords = this.renderer.canvasToRemoteCoords(canvasX, canvasY);

        this.wsClient.send({
            type: 'action',
            action_type: 'double_click',
            x: remoteCoords.x,
            y: remoteCoords.y
        });

        console.log(`Double click at (${remoteCoords.x}, ${remoteCoords.y})`);
    }

    handleRightClick(event) {
        if (!this.enabled) return;
        event.preventDefault();

        const { canvasX, canvasY } = this.getCanvasCoords(event);
        const remoteCoords = this.renderer.canvasToRemoteCoords(canvasX, canvasY);

        this.wsClient.send({
            type: 'action',
            action_type: 'right_click',
            x: remoteCoords.x,
            y: remoteCoords.y
        });

        console.log(`Right click at (${remoteCoords.x}, ${remoteCoords.y})`);
    }

    handleMouseDown(event) {
        if (!this.enabled) return;
        if (event.button !== 0) return;

        this.isDragging = true;
        this.wasDragging = false;

        const { canvasX, canvasY } = this.getCanvasCoords(event);
        this.dragStartCanvasX = canvasX;
        this.dragStartCanvasY = canvasY;

        const remoteCoords = this.renderer.canvasToRemoteCoords(canvasX, canvasY);
        this.dragStartX = remoteCoords.x;
        this.dragStartY = remoteCoords.y;
    }

    handleMouseMove(event) {
        if (!this.enabled || !this.isDragging) return;

        const { canvasX, canvasY } = this.getCanvasCoords(event);

        // 일정 거리 이상 이동하면 드래그로 인식
        const distance = Math.sqrt(
            Math.pow(canvasX - this.dragStartCanvasX, 2) +
            Math.pow(canvasY - this.dragStartCanvasY, 2)
        );

        if (distance > 5) {
            this.wasDragging = true;
        }
    }

    handleMouseUp(event) {
        if (!this.enabled || !this.isDragging) return;
        if (event.button !== 0) return;

        this.isDragging = false;

        const { canvasX, canvasY } = this.getCanvasCoords(event);
        const remoteCoords = this.renderer.canvasToRemoteCoords(canvasX, canvasY);

        // 드래그였다면 drag 액션 전송
        if (this.wasDragging) {
            this.wsClient.send({
                type: 'action',
                action_type: 'drag',
                start_x: this.dragStartX,
                start_y: this.dragStartY,
                end_x: remoteCoords.x,
                end_y: remoteCoords.y
            });

            console.log(`Drag from (${this.dragStartX}, ${this.dragStartY}) to (${remoteCoords.x}, ${remoteCoords.y})`);
        }
    }

    handleMouseLeave(event) {
        // 캔버스를 벗어나면 드래그 취소
        this.isDragging = false;
        this.wasDragging = false;
    }

    handleWheel(event) {
        if (!this.enabled) return;
        event.preventDefault();

        const { canvasX, canvasY } = this.getCanvasCoords(event);
        const remoteCoords = this.renderer.canvasToRemoteCoords(canvasX, canvasY);

        const direction = event.deltaY < 0 ? 'up' : 'down';

        this.wsClient.send({
            type: 'action',
            action_type: 'scroll',
            x: remoteCoords.x,
            y: remoteCoords.y,
            direction: direction
        });

        console.log(`Scroll ${direction} at (${remoteCoords.x}, ${remoteCoords.y})`);
    }

    handleKeyDown(event) {
        if (!this.enabled) return;

        // 캔버스에 포커스가 있을 때만 처리 (또는 body에 포커스)
        const activeElement = document.activeElement;
        if (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA') {
            return; // 입력 필드에서는 무시
        }

        // Ctrl/Cmd + Key 조합
        if (event.ctrlKey || event.metaKey || event.altKey) {
            event.preventDefault();

            let keys = [];
            if (event.ctrlKey) keys.push('ctrl');
            if (event.metaKey) keys.push('cmd');
            if (event.altKey) keys.push('alt');
            if (event.shiftKey) keys.push('shift');
            keys.push(event.key.toLowerCase());

            this.wsClient.send({
                type: 'action',
                action_type: 'hotkey',
                key: keys.join(' ')
            });

            console.log(`Hotkey: ${keys.join(' + ')}`);
        }
        // 특수 키만 전송 (일반 텍스트는 전송하지 않음)
        else if (['Enter', 'Tab', 'Escape', 'Backspace', 'Delete',
                  'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight',
                  'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12'
                 ].includes(event.key)) {
            event.preventDefault();

            this.wsClient.send({
                type: 'action',
                action_type: 'hotkey',
                key: event.key.toLowerCase()
            });

            console.log(`Key: ${event.key}`);
        }
    }
}
