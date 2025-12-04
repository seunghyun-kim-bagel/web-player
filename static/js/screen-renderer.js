/**
 * Web Player - 화면 렌더러
 */
class ScreenRenderer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.remoteWidth = 0;
        this.remoteHeight = 0;
        this.lastFrameTime = 0;
        this.fps = 0;
        this.frameCount = 0;
        this.fpsHistory = [];
        this.maxFpsHistory = 10;
    }

    renderFrame(frameData) {
        this.remoteWidth = frameData.width;
        this.remoteHeight = frameData.height;

        const img = new Image();
        img.onload = () => {
            // 캔버스 크기 조정 (최초 또는 해상도 변경 시)
            if (this.canvas.width !== img.width || this.canvas.height !== img.height) {
                this.canvas.width = img.width;
                this.canvas.height = img.height;
                console.log(`Canvas resized to ${img.width}x${img.height}`);
            }

            // 화면 그리기
            this.ctx.drawImage(img, 0, 0);

            // FPS 계산
            this.calculateFPS();
            this.frameCount++;
        };

        img.onerror = () => {
            console.error('Failed to load frame image');
        };

        img.src = 'data:image/jpeg;base64,' + frameData.data;
    }

    calculateFPS() {
        const now = performance.now();
        if (this.lastFrameTime) {
            const delta = now - this.lastFrameTime;
            const instantFps = 1000 / delta;

            // FPS 이력에 추가
            this.fpsHistory.push(instantFps);
            if (this.fpsHistory.length > this.maxFpsHistory) {
                this.fpsHistory.shift();
            }

            // 평균 FPS 계산
            const sum = this.fpsHistory.reduce((a, b) => a + b, 0);
            this.fps = Math.round(sum / this.fpsHistory.length);
        }
        this.lastFrameTime = now;
    }

    canvasToRemoteCoords(canvasX, canvasY) {
        const rect = this.canvas.getBoundingClientRect();

        // 캔버스 내 상대 위치 계산
        const relativeX = canvasX;
        const relativeY = canvasY;

        // 스케일 계산
        const scaleX = this.remoteWidth / this.canvas.width;
        const scaleY = this.remoteHeight / this.canvas.height;

        return {
            x: Math.round(relativeX * scaleX),
            y: Math.round(relativeY * scaleY)
        };
    }

    drawClickFeedback(canvasX, canvasY) {
        // 클릭 위치에 시각적 피드백
        const ctx = this.ctx;

        // 외부 원
        ctx.beginPath();
        ctx.arc(canvasX, canvasY, 15, 0, 2 * Math.PI);
        ctx.strokeStyle = 'rgba(233, 69, 96, 0.8)';
        ctx.lineWidth = 3;
        ctx.stroke();

        // 내부 점
        ctx.beginPath();
        ctx.arc(canvasX, canvasY, 5, 0, 2 * Math.PI);
        ctx.fillStyle = 'rgba(233, 69, 96, 0.8)';
        ctx.fill();

        // 애니메이션으로 사라지게
        setTimeout(() => {
            // 다음 프레임이 덮어씌움
        }, 200);
    }

    getFPS() {
        return this.fps;
    }

    getResolution() {
        if (this.remoteWidth && this.remoteHeight) {
            return `${this.remoteWidth}x${this.remoteHeight}`;
        }
        return '-';
    }

    getFrameCount() {
        return this.frameCount;
    }

    clear() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.frameCount = 0;
        this.fps = 0;
        this.fpsHistory = [];
    }
}
