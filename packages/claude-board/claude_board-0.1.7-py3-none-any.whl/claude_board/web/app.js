/**
 * Claude Board - Frontend Application
 *
 * Features:
 * - WebSocket connection for real-time updates
 * - Audio notifications using Web Audio API
 * - Vibration for mobile devices
 * - Responsive UI updates
 */

class ClaudeBoardApp {
    constructor() {
        this.ws = null;
        this.state = null;
        this.audioContext = null;
        this.notificationsEnabled = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 1000;

        this.initElements();
        this.initEventListeners();
        this.connect();
        this.startSessionTimer();
    }

    initElements() {
        // Status bar
        this.yoloToggle = document.getElementById('yolo-toggle');
        this.connectionStatus = document.getElementById('connection-status');
        this.sessionTime = document.getElementById('session-time');

        // Current task
        this.currentTaskText = document.getElementById('current-task-text');

        // Pending section
        this.pendingSection = document.getElementById('pending-section');
        this.noPendingSection = document.getElementById('no-pending-section');
        this.pendingToolName = document.getElementById('pending-tool-name');
        this.pendingToolInput = document.getElementById('pending-tool-input');
        this.approveBtn = document.getElementById('approve-btn');
        this.denyBtn = document.getElementById('deny-btn');

        // Completed
        this.completedCount = document.getElementById('completed-count');
        this.completedList = document.getElementById('completed-list');

        // Stats
        this.totalCount = document.getElementById('total-count');
        this.approvedCount = document.getElementById('approved-count');
        this.deniedCount = document.getElementById('denied-count');

        // Notifications
        this.enableNotificationsBtn = document.getElementById('enable-notifications-btn');
        this.notificationsStatus = document.getElementById('notifications-status');

        // TODO List
        this.todoCount = document.getElementById('todo-count');
        this.todoList = document.getElementById('todo-list');
    }

    initEventListeners() {
        // YOLO toggle
        this.yoloToggle.addEventListener('click', () => this.toggleYolo());

        // Approve/Deny buttons
        this.approveBtn.addEventListener('click', () => this.makeDecision('approve'));
        this.denyBtn.addEventListener('click', () => this.makeDecision('deny'));

        // Enable notifications button
        this.enableNotificationsBtn.addEventListener('click', () => this.enableNotifications());

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (!this.state?.pending_request) return;

            if (e.key === 'y' || e.key === 'Y' || e.key === 'Enter') {
                e.preventDefault();
                this.makeDecision('approve');
            } else if (e.key === 'n' || e.key === 'N' || e.key === 'Escape') {
                e.preventDefault();
                this.makeDecision('deny');
            }
        });
    }

    enableNotifications() {
        // Initialize AudioContext (requires user gesture)
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }

        // Resume if suspended
        if (this.audioContext.state === 'suspended') {
            this.audioContext.resume();
        }

        // Request browser notification permission
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }

        // Test sound
        this.playNotificationSound();

        // Test vibration
        this.vibrate();

        // Mark as enabled
        this.notificationsEnabled = true;

        // Update UI
        this.enableNotificationsBtn.classList.add('hidden');
        this.notificationsStatus.classList.remove('hidden');

        console.log('Notifications enabled');
    }

    playNotificationSound() {
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }

        // Resume audio context if suspended (needed for mobile)
        if (this.audioContext.state === 'suspended') {
            this.audioContext.resume();
        }

        // Create a pleasant notification sound - two tones
        const now = this.audioContext.currentTime;

        // First tone
        const osc1 = this.audioContext.createOscillator();
        const gain1 = this.audioContext.createGain();
        osc1.connect(gain1);
        gain1.connect(this.audioContext.destination);
        osc1.frequency.setValueAtTime(523.25, now); // C5
        gain1.gain.setValueAtTime(0.3, now);
        gain1.gain.exponentialRampToValueAtTime(0.01, now + 0.15);
        osc1.start(now);
        osc1.stop(now + 0.15);

        // Second tone (higher)
        const osc2 = this.audioContext.createOscillator();
        const gain2 = this.audioContext.createGain();
        osc2.connect(gain2);
        gain2.connect(this.audioContext.destination);
        osc2.frequency.setValueAtTime(659.25, now + 0.1); // E5
        gain2.gain.setValueAtTime(0.3, now + 0.1);
        gain2.gain.exponentialRampToValueAtTime(0.01, now + 0.3);
        osc2.start(now + 0.1);
        osc2.stop(now + 0.3);
    }

    vibrate() {
        // Vibrate for mobile devices - maximum intensity pattern
        if ('vibrate' in navigator) {
            // Very long continuous vibration pattern (total ~2.5 seconds)
            // Multiple rapid pulses feel stronger than single long vibration
            navigator.vibrate([
                500, 50, 500, 50, 500, 50, 500, 50, 200
            ]);
        }
    }

    startContinuousVibration() {
        // Stop any existing vibration interval
        this.stopContinuousVibration();

        // Vibrate immediately
        this.vibrate();

        // Then repeat every 2 seconds while pending (more urgent)
        this.vibrationInterval = setInterval(() => {
            if (this.state?.pending_request && this.notificationsEnabled) {
                this.vibrate();
                this.playNotificationSound();
            } else {
                this.stopContinuousVibration();
            }
        }, 2500);
    }

    stopContinuousVibration() {
        if (this.vibrationInterval) {
            clearInterval(this.vibrationInterval);
            this.vibrationInterval = null;
        }
        // Stop any ongoing vibration
        if ('vibrate' in navigator) {
            navigator.vibrate(0);
        }
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        console.log('Connecting to WebSocket:', wsUrl);
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.updateConnectionStatus(true);
        };

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (message.type === 'state_update') {
                this.handleStateUpdate(message.data);
            }
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateConnectionStatus(false);
            this.scheduleReconnect();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('Max reconnection attempts reached');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

        setTimeout(() => this.connect(), delay);
    }

    updateConnectionStatus(connected) {
        this.connectionStatus.textContent = connected ? 'Connected' : 'Disconnected';
        this.connectionStatus.className = `status-badge ${connected ? 'connected' : 'disconnected'}`;
    }

    handleStateUpdate(state) {
        const hadPending = this.state?.pending_request;
        const hasPending = state.pending_request;

        this.state = state;

        // Notify if new pending request
        if (!hadPending && hasPending) {
            if (this.notificationsEnabled) {
                this.playNotificationSound();
                this.startContinuousVibration();
            }
            // Also try to show browser notification
            this.showBrowserNotification(state.pending_request);
        }

        // Stop vibration when request is handled
        if (hadPending && !hasPending) {
            this.stopContinuousVibration();
        }

        this.render();
    }

    showBrowserNotification(request) {
        if ('Notification' in window && Notification.permission === 'granted') {
            const notification = new Notification('Claude Board', {
                body: `${request.tool_name}: ${request.display_text}`,
                icon: '🎛️',
                tag: 'claude-board',
                requireInteraction: true
            });

            notification.onclick = () => {
                window.focus();
                notification.close();
            };
        }
    }

    render() {
        if (!this.state) return;

        // YOLO toggle
        this.yoloToggle.textContent = this.state.yolo_mode ? 'ON' : 'OFF';
        this.yoloToggle.className = `toggle-btn ${this.state.yolo_mode ? 'on' : 'off'}`;

        // Current task
        this.currentTaskText.textContent = this.state.current_task || 'No active task';

        // Pending request
        if (this.state.pending_request) {
            this.pendingSection.classList.remove('hidden');
            this.noPendingSection.classList.add('hidden');

            const request = this.state.pending_request;
            this.pendingToolName.textContent = request.tool_name;

            // Format tool input nicely
            let inputText = '';
            if (request.tool_name === 'Bash') {
                inputText = request.tool_input.command || '';
            } else if (request.tool_name === 'Write' || request.tool_name === 'Read') {
                inputText = request.tool_input.file_path || '';
                if (request.tool_name === 'Write' && request.tool_input.content) {
                    const preview = request.tool_input.content.substring(0, 500);
                    inputText += `\n\n--- Content Preview ---\n${preview}`;
                    if (request.tool_input.content.length > 500) {
                        inputText += '\n... (truncated)';
                    }
                }
            } else if (request.tool_name === 'Edit') {
                inputText = request.tool_input.file_path || '';
                inputText += `\n\n--- Replace ---\n${request.tool_input.old_string || ''}\n\n--- With ---\n${request.tool_input.new_string || ''}`;
            } else if (request.tool_name === 'Glob') {
                inputText = `Pattern: ${request.tool_input.pattern || ''}`;
                if (request.tool_input.path) {
                    inputText += `\nPath: ${request.tool_input.path}`;
                }
            } else if (request.tool_name === 'Grep') {
                inputText = `Pattern: ${request.tool_input.pattern || ''}`;
                if (request.tool_input.path) {
                    inputText += `\nPath: ${request.tool_input.path}`;
                }
            } else {
                inputText = JSON.stringify(request.tool_input, null, 2);
            }
            this.pendingToolInput.textContent = inputText;
        } else {
            this.pendingSection.classList.add('hidden');
            this.noPendingSection.classList.remove('hidden');
        }

        // Completed tasks
        this.completedCount.textContent = this.state.completed_tasks.length;
        this.completedList.innerHTML = '';

        // Show most recent first
        const tasks = [...this.state.completed_tasks].reverse();
        for (const task of tasks) {
            const li = document.createElement('li');
            li.innerHTML = `
                <span class="task-icon ${task.approved ? 'approved' : 'denied'}">
                    ${task.approved ? '✓' : '✗'}
                </span>
                <span class="task-text">${this.escapeHtml(task.display_text)}</span>
                <span class="task-time">${this.formatTime(task.timestamp)}</span>
            `;
            this.completedList.appendChild(li);
        }

        // Stats
        this.totalCount.textContent = this.state.stats.total_requests;
        this.approvedCount.textContent = this.state.stats.approved_count;
        this.deniedCount.textContent = this.state.stats.denied_count;

        // TODO List
        this.renderTodos();
    }

    renderTodos() {
        const todos = this.state.todos || [];
        this.todoCount.textContent = todos.length;
        this.todoList.innerHTML = '';

        for (const todo of todos) {
            const li = document.createElement('li');
            const statusClass = todo.status;
            let icon = '';
            let displayText = todo.content;

            if (todo.status === 'completed') {
                icon = '✓';
            } else if (todo.status === 'in_progress') {
                icon = '◐';
                displayText = todo.activeForm || todo.content;
            } else {
                icon = '○';
            }

            li.innerHTML = `
                <span class="todo-icon ${statusClass}">${icon}</span>
                <span class="todo-text ${statusClass}">${this.escapeHtml(displayText)}</span>
            `;
            this.todoList.appendChild(li);
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatTime(isoString) {
        const date = new Date(isoString);
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
    }

    startSessionTimer() {
        setInterval(() => {
            if (this.state?.stats?.start_time) {
                const start = new Date(this.state.stats.start_time);
                const now = new Date();
                const diff = Math.floor((now - start) / 1000);

                const hours = Math.floor(diff / 3600);
                const minutes = Math.floor((diff % 3600) / 60);
                const seconds = diff % 60;

                this.sessionTime.textContent =
                    `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
            }
        }, 1000);
    }

    async toggleYolo() {
        const newValue = !this.state?.yolo_mode;

        try {
            const response = await fetch('/api/yolo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled: newValue })
            });

            if (!response.ok) {
                throw new Error('Failed to toggle YOLO mode');
            }
        } catch (error) {
            console.error('Error toggling YOLO:', error);
            alert('Failed to toggle YOLO mode');
        }
    }

    async makeDecision(decision) {
        if (!this.state?.pending_request) return;

        const requestId = this.state.pending_request.id;
        const endpoint = decision === 'approve' ? '/api/approve' : '/api/deny';

        // Disable buttons during request
        this.approveBtn.disabled = true;
        this.denyBtn.disabled = true;

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ request_id: requestId })
            });

            if (!response.ok) {
                throw new Error('Failed to submit decision');
            }

            // Provide haptic feedback
            if (decision === 'approve') {
                this.vibrate();
            }
        } catch (error) {
            console.error('Error making decision:', error);
            alert('Failed to submit decision');
        } finally {
            this.approveBtn.disabled = false;
            this.denyBtn.disabled = false;
        }
    }
}

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ClaudeBoardApp();
});
