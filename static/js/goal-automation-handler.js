/**
 * Goal Automation Handler
 * 목표 기반 자동화 UI 핸들러
 */
class GoalAutomationHandler {
    constructor(wsClient) {
        this.wsClient = wsClient;
        this.isRunning = false;

        this.initUI();
        this.bindEvents();
    }

    initUI() {
        // UI 요소 참조
        this.goalInput = document.getElementById('goal-input');
        this.maxStepsInput = document.getElementById('max-steps-input');
        this.startBtn = document.getElementById('start-automation-btn');
        this.stopBtn = document.getElementById('stop-automation-btn');
        this.statusPanel = document.getElementById('automation-status');
        this.progressBar = document.getElementById('automation-progress');
        this.progressText = document.getElementById('automation-progress-text');
        this.historyLog = document.getElementById('automation-history');
    }

    bindEvents() {
        this.startBtn?.addEventListener('click', () => this.start());
        this.stopBtn?.addEventListener('click', () => this.stop());

        // Enter 키로 시작
        this.goalInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !this.isRunning) {
                this.start();
            }
        });
    }

    start() {
        const goal = this.goalInput?.value.trim();
        if (!goal) {
            alert('목표를 입력하세요');
            return;
        }

        const maxSteps = parseInt(this.maxStepsInput?.value) || 50;

        this.wsClient.send({
            type: 'goal_automation',
            action: 'start',
            goal: goal,
            max_steps: maxSteps
        });

        this.setRunningState(true);
        this.clearHistory();
        this.addHistoryEntry({
            step: 0,
            action_type: 'start',
            thought: `목표 자동화 시작: "${goal}"`
        });
    }

    stop() {
        this.wsClient.send({
            type: 'goal_automation',
            action: 'stop'
        });
    }

    handleMessage(data) {
        if (data.type === 'automation_status') {
            this.handleStatus(data);
        }
    }

    handleStatus(data) {
        this.isRunning = data.is_running;
        this.setRunningState(data.is_running);

        // 진행률 업데이트
        const percent = data.goal_status?.progress_percent || 0;
        if (this.progressBar) {
            this.progressBar.style.width = `${percent}%`;
        }
        if (this.progressText) {
            this.progressText.textContent = `${percent}%`;
        }

        // 상태 텍스트
        if (this.statusPanel) {
            const statusHtml = `
                <div class="status-item">
                    <span class="label">Step:</span>
                    <span class="value">${data.current_step}/${data.max_steps}</span>
                </div>
                <div class="status-item">
                    <span class="label">목표:</span>
                    <span class="value">${data.goal}</span>
                </div>
                <div class="status-item">
                    <span class="label">상태:</span>
                    <span class="value">${data.goal_status?.progress_description || '-'}</span>
                </div>
                <div class="status-item">
                    <span class="label">신뢰도:</span>
                    <span class="value">${((data.goal_status?.confidence || 0) * 100).toFixed(0)}%</span>
                </div>
            `;
            this.statusPanel.innerHTML = statusHtml;
        }

        // 마지막 액션 로그
        if (data.last_action && data.last_action.step > 0) {
            this.updateLastHistoryEntry(data.last_action);
        }

        // 완료 처리
        if (data.finish_reason) {
            this.handleFinish(data.finish_reason, data.goal_status);
        }
    }

    addHistoryEntry(action) {
        if (!this.historyLog) return;

        const entry = document.createElement('div');
        entry.className = 'history-entry';
        entry.dataset.step = action.step;
        entry.innerHTML = `
            <span class="step">Step ${action.step}</span>
            <span class="action">${action.action_type}</span>
            <span class="thought">${action.thought || ''}</span>
        `;
        this.historyLog.appendChild(entry);
        this.historyLog.scrollTop = this.historyLog.scrollHeight;
    }

    updateLastHistoryEntry(action) {
        if (!this.historyLog) return;

        // 같은 스텝의 엔트리가 있으면 업데이트, 없으면 추가
        const existing = this.historyLog.querySelector(`[data-step="${action.step}"]`);
        if (existing) {
            existing.innerHTML = `
                <span class="step">Step ${action.step}</span>
                <span class="action">${action.action_type}</span>
                <span class="thought">${action.thought || ''}</span>
            `;
        } else {
            this.addHistoryEntry(action);
        }
    }

    clearHistory() {
        if (this.historyLog) {
            this.historyLog.innerHTML = '';
        }
    }

    handleFinish(reason, goalStatus) {
        let message = '';
        let className = '';

        switch (reason) {
            case 'goal_achieved':
                message = '목표를 달성했습니다!';
                className = 'success';
                break;
            case 'max_steps':
                message = '최대 스텝에 도달했습니다.';
                className = 'warning';
                break;
            case 'user_stopped':
                message = '사용자가 중지했습니다.';
                className = 'info';
                break;
            case 'error':
                message = '오류가 발생했습니다.';
                className = 'error';
                break;
            default:
                message = `완료: ${reason}`;
                className = 'info';
        }

        // 완료 메시지 추가
        this.addHistoryEntry({
            step: '완료',
            action_type: className,
            thought: message
        });

        this.setRunningState(false);
    }

    setRunningState(running) {
        this.isRunning = running;

        if (this.startBtn) {
            this.startBtn.disabled = running;
            this.startBtn.textContent = running ? '실행 중...' : '시작';
        }
        if (this.stopBtn) {
            this.stopBtn.disabled = !running;
        }
        if (this.goalInput) {
            this.goalInput.disabled = running;
        }
        if (this.maxStepsInput) {
            this.maxStepsInput.disabled = running;
        }

        // 실행 중일 때 컨테이너에 클래스 추가
        const container = document.getElementById('goal-automation-panel');
        if (container) {
            container.classList.toggle('running', running);
        }
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GoalAutomationHandler;
}
