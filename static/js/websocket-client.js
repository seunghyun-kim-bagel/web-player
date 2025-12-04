/**
 * Web Player - WebSocket 클라이언트
 */
class WebSocketClient {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.isManualClose = false;
        this.callbacks = {
            onOpen: null,
            onMessage: null,
            onError: null,
            onClose: null
        };
    }

    connect() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.log('Already connected');
            return;
        }

        console.log(`Connecting to ${this.url}`);
        this.isManualClose = false;
        this.ws = new WebSocket(this.url);

        this.ws.onopen = (event) => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            if (this.callbacks.onOpen) {
                this.callbacks.onOpen(event);
            }
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (this.callbacks.onMessage) {
                    this.callbacks.onMessage(data);
                }
            } catch (e) {
                console.error('Failed to parse message:', e);
            }
        };

        this.ws.onerror = (event) => {
            console.error('WebSocket error:', event);
            if (this.callbacks.onError) {
                this.callbacks.onError(event);
            }
        };

        this.ws.onclose = (event) => {
            console.log('WebSocket closed:', event.code, event.reason);
            if (this.callbacks.onClose) {
                this.callbacks.onClose(event);
            }

            // 수동 종료가 아닌 경우에만 재연결 시도
            if (!this.isManualClose) {
                this.attemptReconnect();
            }
        };
    }

    disconnect() {
        this.isManualClose = true;
        if (this.ws) {
            this.ws.close(1000, 'User disconnected');
            this.ws = null;
        }
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
            return true;
        } else {
            console.error('WebSocket is not connected');
            return false;
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

        setTimeout(() => {
            if (!this.isManualClose) {
                this.connect();
            }
        }, delay);
    }

    on(event, callback) {
        const eventMap = {
            'open': 'onOpen',
            'message': 'onMessage',
            'error': 'onError',
            'close': 'onClose'
        };

        if (eventMap[event]) {
            this.callbacks[eventMap[event]] = callback;
        }
    }

    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }

    getState() {
        if (!this.ws) return 'CLOSED';
        const states = ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'];
        return states[this.ws.readyState];
    }
}
