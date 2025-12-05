/**
 * Web Player - AI 명령 핸들러
 * UI-TARS를 통한 자연어 명령 처리
 */
class AICommandHandler {
    constructor(wsClient) {
        this.wsClient = wsClient;
        this.isProcessing = false;
        this.enabled = false;

        // DOM 요소
        this.elements = {
            input: document.getElementById('ai-command-input'),
            executeBtn: document.getElementById('btn-ai-execute'),
            status: document.getElementById('ai-status'),
            statusText: document.getElementById('ai-status-text'),
            response: document.getElementById('ai-response'),
            thoughtText: document.getElementById('ai-thought-text'),
            actionText: document.getElementById('ai-action-text')
        };

        this.setupEventListeners();
    }

    setupEventListeners() {
        // 실행 버튼 클릭
        this.elements.executeBtn.addEventListener('click', () => {
            this.executeCommand();
        });

        // Enter 키로 실행
        this.elements.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.executeCommand();
            }
        });

        // 입력 필드 포커스 시 키보드 이벤트 차단
        this.elements.input.addEventListener('focus', () => {
            // InputHandler의 키보드 이벤트가 간섭하지 않도록
            document.activeElement.dataset.aiInput = 'true';
        });

        this.elements.input.addEventListener('blur', () => {
            delete document.activeElement.dataset.aiInput;
        });
    }

    enable() {
        this.enabled = true;
        this.elements.input.disabled = false;
        this.elements.executeBtn.disabled = false;
        console.log('AI Command Handler enabled');
    }

    disable() {
        this.enabled = false;
        this.elements.input.disabled = true;
        this.elements.executeBtn.disabled = true;
        this.hideStatus();
        this.hideResponse();
        console.log('AI Command Handler disabled');
    }

    async executeCommand() {
        if (!this.enabled || this.isProcessing) return;

        const instruction = this.elements.input.value.trim();
        if (!instruction) {
            this.showError('명령을 입력해주세요.');
            return;
        }

        this.isProcessing = true;
        this.showStatus('AI가 화면을 분석하고 있습니다...');
        this.hideResponse();
        this.setButtonLoading(true);

        try {
            // AI 명령 전송
            this.wsClient.send({
                type: 'ai_command',
                instruction: instruction
            });

            console.log(`AI Command sent: ${instruction}`);
        } catch (error) {
            console.error('Failed to send AI command:', error);
            this.showError('명령 전송에 실패했습니다.');
            this.isProcessing = false;
            this.setButtonLoading(false);
        }
    }

    handleResponse(data) {
        this.isProcessing = false;
        this.setButtonLoading(false);
        this.hideStatus();

        if (data.success) {
            this.showResponse({
                thought: data.thought || '분석 완료',
                action: data.action_type ?
                    `${data.action_type}(${JSON.stringify(data.action_params || {})})` :
                    '완료',
                success: true
            });

            // 명령 실행 완료 후 입력 필드 초기화
            this.elements.input.value = '';

            console.log('AI Command executed successfully:', data);
        } else {
            this.showResponse({
                thought: data.error || '오류가 발생했습니다',
                action: '실패',
                success: false
            });

            console.error('AI Command failed:', data);
        }
    }

    showStatus(message) {
        this.elements.statusText.textContent = message;
        this.elements.status.classList.remove('hidden');
    }

    hideStatus() {
        this.elements.status.classList.add('hidden');
    }

    showResponse({ thought, action, success }) {
        this.elements.thoughtText.textContent = thought;
        this.elements.actionText.textContent = action;

        this.elements.response.classList.remove('hidden', 'success', 'error');
        this.elements.response.classList.add(success ? 'success' : 'error');
    }

    hideResponse() {
        this.elements.response.classList.add('hidden');
    }

    showError(message) {
        this.showResponse({
            thought: message,
            action: '-',
            success: false
        });
    }

    setButtonLoading(loading) {
        if (loading) {
            this.elements.executeBtn.classList.add('loading');
            this.elements.executeBtn.disabled = true;
            this.elements.input.disabled = true;
        } else {
            this.elements.executeBtn.classList.remove('loading');
            this.elements.executeBtn.disabled = false;
            this.elements.input.disabled = false;
        }
    }
}
