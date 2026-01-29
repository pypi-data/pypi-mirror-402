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

        // Multi-project support
        this.activeProject = null;  // Currently selected project path

        // Terminal support
        this.terminal = null;
        this.terminalFitAddon = null;
        this.terminalWs = null;
        this.connectedSessionId = null;
        this.sessions = [];

        this.initElements();
        this.initEventListeners();
        this.initTerminal();
        this.connect();
        this.loadSessions();

        // Create debounced version of loadSessions (5 second delay)
        this._loadSessionsTimeout = null;
        this.debouncedLoadSessions = () => {
            if (this._loadSessionsTimeout) {
                clearTimeout(this._loadSessionsTimeout);
            }
            this._loadSessionsTimeout = setTimeout(() => {
                this.loadSessions();
            }, 5000);
        };
    }

    initElements() {
        // Header
        this.connectionStatus = document.getElementById('connection-status');

        // Project selector
        this.projectSection = document.getElementById('project-section');
        this.projectTabs = document.getElementById('project-tabs');

        // TODO section
        this.todoSection = document.getElementById('todo-section');
        this.todoCount = document.getElementById('todo-count');
        this.todoList = document.getElementById('todo-list');

        // Status section
        this.statusSection = document.getElementById('status-section');
        this.statusTitle = document.getElementById('status-title');
        this.statusContent = document.getElementById('status-content');

        // Pending section
        this.pendingSection = document.getElementById('pending-section');
        this.pendingToolName = document.getElementById('pending-tool-name');
        this.pendingToolInput = document.getElementById('pending-tool-input');

        // Completed section
        this.completedSection = document.getElementById('completed-section');
        this.completedCount = document.getElementById('completed-count');
        this.completedList = document.getElementById('completed-list');

        // Notifications
        this.notificationsContainer = document.getElementById('notifications-container');
        this.enableNotificationsBtn = document.getElementById('enable-notifications-btn');
        this.notificationsStatus = document.getElementById('notifications-status');

        // Bottom bar - Action buttons
        this.approveBtn = document.getElementById('approve-btn');
        this.denyBtn = document.getElementById('deny-btn');

        // Bottom bar - Stats
        this.totalCount = document.getElementById('total-count');
        this.approvedCount = document.getElementById('approved-count');
        this.deniedCount = document.getElementById('denied-count');

        // Bottom bar - YOLO
        this.yoloToggle = document.getElementById('yolo-toggle');

        // Terminal elements
        this.terminalSection = document.getElementById('terminal-section');
        this.terminalContainer = document.getElementById('terminal-container');
        this.sessionSelect = document.getElementById('session-select');
        this.terminalConnectBtn = document.getElementById('terminal-connect-btn');
        this.terminalDisconnectBtn = document.getElementById('terminal-disconnect-btn');
        this.promptInput = document.getElementById('prompt-input');
        this.promptSendBtn = document.getElementById('prompt-send-btn');
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
            // Skip if focus is in the prompt input
            if (document.activeElement === this.promptInput) return;

            if (!this.state?.pending_request) return;

            if (e.key === 'y' || e.key === 'Y' || e.key === 'Enter') {
                e.preventDefault();
                this.makeDecision('approve');
            } else if (e.key === 'n' || e.key === 'N' || e.key === 'Escape') {
                e.preventDefault();
                this.makeDecision('deny');
            }
        });

        // Terminal event listeners
        this.sessionSelect.addEventListener('change', () => this.onSessionSelectChange());
        this.terminalConnectBtn.addEventListener('click', () => this.connectToSession());
        this.terminalDisconnectBtn.addEventListener('click', () => this.disconnectFromSession());
        this.promptSendBtn.addEventListener('click', () => this.sendPrompt());
        this.promptInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendPrompt();
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

        // Auto-select active project if not set
        if (!this.activeProject && state.active_project) {
            this.activeProject = state.active_project;
        } else if (!this.activeProject && state.project_list && state.project_list.length > 0) {
            // Default to first project with pending, or just first project
            const withPending = state.project_list.find(p => p.has_pending);
            this.activeProject = withPending?.project_path || state.project_list[0].project_path;
        }

        // Notify if new pending request (in any project)
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

        // Refresh sessions list periodically (debounced to avoid too many requests)
        this.debouncedLoadSessions();

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

        // Render project tabs
        this.renderProjectTabs();

        // YOLO toggle
        this.yoloToggle.textContent = this.state.yolo_mode ? 'ON' : 'OFF';
        this.yoloToggle.className = `toggle-btn ${this.state.yolo_mode ? 'on' : 'off'}`;

        // Get active project state (or global state if no project selected)
        const projectState = this.getActiveProjectState();

        // Pending request - update buttons and sections
        const hasPending = !!projectState?.pending_request;

        // Enable/disable action buttons
        this.approveBtn.disabled = !hasPending;
        this.denyBtn.disabled = !hasPending;

        if (hasPending) {
            const request = projectState.pending_request;

            // Show pending section
            this.pendingSection.classList.remove('hidden');
            this.pendingToolName.textContent = request.tool_name;
            this.pendingToolInput.textContent = this.formatToolInput(request);

            // Hide status section when pending
            this.statusSection.classList.add('hidden');
        } else {
            // Hide pending section
            this.pendingSection.classList.add('hidden');

            // Status section is hidden by default (no content when nothing pending)
            this.statusSection.classList.add('hidden');
        }

        // TODO List - hide when empty
        this.renderTodos(projectState);

        // Completed tasks - hide when empty
        this.renderCompleted(projectState);

        // Stats (from active project or global)
        const stats = projectState?.stats || this.state.stats;
        this.totalCount.textContent = stats.total_requests;
        this.approvedCount.textContent = stats.approved_count;
        this.deniedCount.textContent = stats.denied_count;
    }

    getActiveProjectState() {
        if (!this.state) return null;

        // If we have an active project selected, get its state
        if (this.activeProject && this.state.projects && this.state.projects[this.activeProject]) {
            return this.state.projects[this.activeProject];
        }

        // Fall back to global state
        return this.state;
    }

    renderProjectTabs() {
        const projects = this.state?.project_list || [];

        // Hide if only one or no projects
        if (projects.length <= 1) {
            this.projectSection.classList.add('hidden');
            return;
        }

        this.projectSection.classList.remove('hidden');
        this.projectTabs.innerHTML = '';

        for (const project of projects) {
            const tab = document.createElement('button');
            tab.className = 'project-tab';
            if (project.project_path === this.activeProject) {
                tab.classList.add('active');
            }
            if (project.has_pending) {
                tab.classList.add('has-pending');
            }

            // Show pending indicator
            const indicator = project.has_pending ? ' ⚠️' : '';
            tab.innerHTML = `
                <span class="project-name">${this.escapeHtml(project.project_name)}${indicator}</span>
                <span class="project-stats">${project.todo_count} todos</span>
            `;

            tab.onclick = () => this.selectProject(project.project_path);
            this.projectTabs.appendChild(tab);
        }
    }

    async selectProject(projectPath) {
        this.activeProject = projectPath;

        // Notify server about active project selection
        try {
            await fetch('/api/projects/active', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ project_path: projectPath })
            });
        } catch (error) {
            console.error('Error setting active project:', error);
        }

        this.render();
    }

    formatToolInput(request) {
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
        return inputText;
    }

    renderTodos(projectState) {
        const todos = projectState?.todos || this.state.todos || [];
        this.todoCount.textContent = todos.length;

        // Hide section when empty
        if (todos.length === 0) {
            this.todoSection.classList.add('hidden');
            return;
        }

        this.todoSection.classList.remove('hidden');
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

    renderCompleted(projectState) {
        const tasks = projectState?.completed_tasks || this.state.completed_tasks || [];
        this.completedCount.textContent = tasks.length;

        // Hide section when empty
        if (tasks.length === 0) {
            this.completedSection.classList.add('hidden');
            return;
        }

        this.completedSection.classList.remove('hidden');
        this.completedList.innerHTML = '';

        // Show most recent first
        const sortedTasks = [...tasks].reverse();
        for (const task of sortedTasks) {
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
        }
        // Note: buttons will be re-enabled by the state update from WebSocket
    }

    // ==================== Terminal Methods ====================

    initTerminal() {
        // Check if xterm.js is loaded
        if (typeof Terminal === 'undefined') {
            console.warn('xterm.js not loaded, terminal features disabled');
            return;
        }

        // Create terminal instance (READ-ONLY mode)
        // disableStdin: true makes the terminal read-only
        // Users interact via the prompt input box below
        this.terminal = new Terminal({
            cursorBlink: false,  // No blinking cursor in read-only mode
            cursorStyle: 'bar',
            cursorWidth: 1,
            disableStdin: true,  // Disable keyboard input - terminal is read-only
            fontSize: 14,
            fontFamily: '"Monaco", "Consolas", "Lucida Console", monospace',
            theme: {
                background: '#1a1a2e',
                foreground: '#eaeaea',
                cursor: '#60a5fa',
                cursorAccent: '#1a1a2e',
                selection: 'rgba(96, 165, 250, 0.3)',
                black: '#1a1a2e',
                red: '#f87171',
                green: '#4ade80',
                yellow: '#fbbf24',
                blue: '#60a5fa',
                magenta: '#c084fc',
                cyan: '#22d3ee',
                white: '#eaeaea',
                brightBlack: '#4a4a5e',
                brightRed: '#fca5a5',
                brightGreen: '#86efac',
                brightYellow: '#fde047',
                brightBlue: '#93c5fd',
                brightMagenta: '#d8b4fe',
                brightCyan: '#67e8f9',
                brightWhite: '#ffffff'
            },
            scrollback: 10000,
            allowProposedApi: true
        });

        // Load addons
        if (typeof FitAddon !== 'undefined') {
            this.terminalFitAddon = new FitAddon.FitAddon();
            this.terminal.loadAddon(this.terminalFitAddon);
        }

        if (typeof WebLinksAddon !== 'undefined') {
            const webLinksAddon = new WebLinksAddon.WebLinksAddon();
            this.terminal.loadAddon(webLinksAddon);
        }

        // Open terminal in container
        this.terminal.open(this.terminalContainer);

        // Fit terminal to container
        if (this.terminalFitAddon) {
            this.terminalFitAddon.fit();
        }

        // Handle window resize
        window.addEventListener('resize', () => {
            if (this.terminalFitAddon && this.terminalSection && !this.terminalSection.classList.contains('hidden')) {
                this.terminalFitAddon.fit();
                this.sendTerminalResize();
            }
        });

        // Terminal is READ-ONLY - no keyboard input forwarding
        // Users send prompts via the input box below the terminal
        // This prevents accidental input and keeps the terminal as an observation window

        // Write welcome message
        this.terminal.writeln('\x1b[1;34m=== Claude Board Terminal (Read-Only) ===\x1b[0m');
        this.terminal.writeln('Select a session and click Connect to observe.');
        this.terminal.writeln('Use the input box below to send prompts.');
        this.terminal.writeln('');
    }

    async loadSessions() {
        try {
            const response = await fetch('/api/sessions');
            if (response.ok) {
                const data = await response.json();
                this.sessions = data.sessions || [];
                this.updateSessionSelect();

                // Always show terminal section so users can see available sessions
                this.terminalSection.classList.remove('hidden');
            }
        } catch (error) {
            console.error('Error loading sessions:', error);
        }
    }

    updateSessionSelect() {
        // Clear existing options (except first)
        while (this.sessionSelect.options.length > 1) {
            this.sessionSelect.remove(1);
        }

        // Add session options
        for (const session of this.sessions) {
            const option = document.createElement('option');
            option.value = session.session_id;
            const name = session.name || session.session_id.substring(0, 8);
            const state = session.state || 'unknown';
            option.textContent = `${name} (${state})`;
            this.sessionSelect.appendChild(option);
        }

        // Re-select current session if still available
        if (this.connectedSessionId) {
            this.sessionSelect.value = this.connectedSessionId;
        }
    }

    onSessionSelectChange() {
        const sessionId = this.sessionSelect.value;
        this.terminalConnectBtn.disabled = !sessionId;
    }

    async connectToSession() {
        const sessionId = this.sessionSelect.value;
        if (!sessionId) return;

        // Disconnect from any existing session
        this.disconnectFromSession();

        // Connect to the terminal WebSocket
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/sessions/${sessionId}/terminal`;

        console.log('Connecting to terminal WebSocket:', wsUrl);

        this.terminalWs = new WebSocket(wsUrl);

        this.terminalWs.onopen = () => {
            console.log('Terminal WebSocket connected');
            this.connectedSessionId = sessionId;

            // Update UI
            this.terminalConnectBtn.classList.add('hidden');
            this.terminalDisconnectBtn.classList.remove('hidden');
            this.promptInput.disabled = false;
            this.promptSendBtn.disabled = false;
            this.sessionSelect.disabled = true;

            // Clear terminal and show connection message
            this.terminal.clear();
            this.terminal.writeln(`\x1b[1;32mConnected to session: ${sessionId}\x1b[0m`);
            this.terminal.writeln('');

            // Send initial terminal size
            this.sendTerminalResize();

            // Fit terminal
            if (this.terminalFitAddon) {
                this.terminalFitAddon.fit();
            }
        };

        this.terminalWs.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (message.type === 'output') {
                // Write output to terminal (decode base64 if needed)
                const data = message.data;
                if (typeof data === 'string') {
                    this.terminal.write(data);
                }
            } else if (message.type === 'history') {
                // Write history output
                if (message.data) {
                    this.terminal.write(message.data);
                }
            } else if (message.type === 'session_ended') {
                this.terminal.writeln('');
                this.terminal.writeln('\x1b[1;33mSession ended.\x1b[0m');
                this.disconnectFromSession();
            } else if (message.type === 'error') {
                this.terminal.writeln('');
                this.terminal.writeln(`\x1b[1;31mError: ${message.message}\x1b[0m`);
            }
        };

        this.terminalWs.onclose = () => {
            console.log('Terminal WebSocket disconnected');
            if (this.connectedSessionId === sessionId) {
                this.terminal.writeln('');
                this.terminal.writeln('\x1b[1;33mDisconnected from session.\x1b[0m');
                this.resetTerminalUI();
            }
        };

        this.terminalWs.onerror = (error) => {
            console.error('Terminal WebSocket error:', error);
            this.terminal.writeln('');
            this.terminal.writeln('\x1b[1;31mConnection error.\x1b[0m');
        };
    }

    disconnectFromSession() {
        if (this.terminalWs) {
            this.terminalWs.close();
            this.terminalWs = null;
        }
        this.resetTerminalUI();
    }

    resetTerminalUI() {
        this.connectedSessionId = null;
        this.terminalConnectBtn.classList.remove('hidden');
        this.terminalDisconnectBtn.classList.add('hidden');
        this.promptInput.disabled = true;
        this.promptSendBtn.disabled = true;
        this.sessionSelect.disabled = false;
    }

    sendTerminalResize() {
        if (this.terminalWs && this.terminalWs.readyState === WebSocket.OPEN && this.terminal) {
            this.terminalWs.send(JSON.stringify({
                type: 'resize',
                rows: this.terminal.rows,
                cols: this.terminal.cols
            }));
        }
    }

    async sendPrompt() {
        const prompt = this.promptInput.value.trim();
        if (!prompt) return;

        if (!this.connectedSessionId) {
            alert('Not connected to a session');
            return;
        }

        // Clear input
        this.promptInput.value = '';

        // Send prompt via REST API
        try {
            const response = await fetch(`/api/sessions/${this.connectedSessionId}/prompt`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: prompt })
            });

            if (!response.ok) {
                const error = await response.json();
                this.terminal.writeln(`\x1b[1;31mError sending prompt: ${error.detail || 'Unknown error'}\x1b[0m`);
            }
        } catch (error) {
            console.error('Error sending prompt:', error);
            this.terminal.writeln(`\x1b[1;31mError sending prompt: ${error.message}\x1b[0m`);
        }
    }
}

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ClaudeBoardApp();
});
