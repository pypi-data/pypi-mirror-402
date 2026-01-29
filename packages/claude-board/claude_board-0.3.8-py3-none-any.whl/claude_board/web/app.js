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

        // Multi-session support
        this.activeSessionId = null;  // Currently selected Claude session ID

        // Terminal support
        this.terminal = null;
        this.terminalFitAddon = null;
        this.terminalWs = null;
        this.connectedSessionId = null;
        this.sessions = [];

        this.initElements();
        this.initEventListeners();
        // Note: initTerminal() is now called lazily when terminal is expanded
        this.connect();
        // Chat sessions are now pushed via WebSocket, no need for initial load
        // this.loadSessions() is kept for manual refresh when needed (e.g., terminal dropdown)

        // Update header height on load and resize
        this.updateHeaderHeight();
        window.addEventListener('resize', () => this.updateHeaderHeight());
    }

    updateHeaderHeight() {
        // Dynamically calculate fixed header height and set CSS variable
        if (this.fixedHeader && this.mainContainer) {
            const headerHeight = this.fixedHeader.offsetHeight;
            this.mainContainer.style.paddingTop = `${headerHeight + 16}px`;
        }
    }

    initElements() {
        // Fixed header (for dynamic height calculation)
        this.fixedHeader = document.getElementById('fixed-header');
        this.mainContainer = document.getElementById('main-container');

        // Header
        this.connectionStatus = document.getElementById('connection-status');

        // Project selector
        this.projectSection = document.getElementById('project-section');
        this.projectTabs = document.getElementById('project-tabs');

        // TODO section
        this.todoSection = document.getElementById('todo-section');
        this.todoHeader = document.getElementById('todo-header');
        this.todoCount = document.getElementById('todo-count');
        this.todoList = document.getElementById('todo-list');

        // Status section
        this.statusSection = document.getElementById('status-section');
        this.statusTitle = document.getElementById('status-title');
        this.statusContent = document.getElementById('status-content');

        // Pending section
        this.pendingSection = document.getElementById('pending-section');
        this.pendingCount = document.getElementById('pending-count');
        this.pendingList = document.getElementById('pending-list');
        this.selectedRequestId = null;  // Currently selected request for keyboard shortcuts

        // Completed section
        this.completedSection = document.getElementById('completed-section');
        this.completedCount = document.getElementById('completed-count');
        this.completedList = document.getElementById('completed-list');

        // Notification bell (header)
        this.notificationBell = document.getElementById('notification-bell');

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
        this.terminalToggle = document.getElementById('terminal-toggle');
        this.terminalBody = document.getElementById('terminal-body');
        this.terminalStatus = document.getElementById('terminal-status');
        this.terminalContainer = document.getElementById('terminal-container');
        this.sessionSelect = document.getElementById('session-select');
        this.terminalSessionCount = document.getElementById('terminal-session-count');

        // Session tabs bar
        this.sessionTabsBar = document.getElementById('session-tabs-bar');

        // Prompt input bar (in bottom bar)
        this.promptInputBar = document.getElementById('prompt-input-bar');
        this.promptInput = document.getElementById('prompt-input');
        this.promptSendBtn = document.getElementById('prompt-send-btn');
        this.terminalExpanded = false;  // Track terminal expand state
    }

    initEventListeners() {
        // YOLO toggle
        this.yoloToggle.addEventListener('click', () => this.toggleYolo());

        // Approve/Deny buttons
        this.approveBtn.addEventListener('click', () => this.makeDecision('approve'));
        this.denyBtn.addEventListener('click', () => this.makeDecision('deny'));

        // Notification bell click handler
        this.notificationBell.addEventListener('click', () => this.enableNotifications());

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Skip if focus is in the prompt input
            if (document.activeElement === this.promptInput) return;

            // Use selected request for keyboard shortcuts
            if (!this.selectedRequestId) return;

            if (e.key === 'y' || e.key === 'Y' || e.key === 'Enter') {
                e.preventDefault();
                this.approveRequest(this.selectedRequestId);
            } else if (e.key === 'n' || e.key === 'N' || e.key === 'Escape') {
                e.preventDefault();
                this.denyRequest(this.selectedRequestId);
            }
        });

        // TODO header click to expand/collapse when all completed
        this.todoHeader.addEventListener('click', () => this.toggleTodoExpand());

        // Terminal event listeners
        this.terminalToggle.addEventListener('click', (e) => {
            // Don't toggle if clicking on controls
            if (e.target.closest('.terminal-controls')) return;
            this.toggleTerminal();
        });
        // Session select auto-connects when changed
        this.sessionSelect.addEventListener('change', () => this.onSessionSelectChange());
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

        // Update bell icon to show enabled state
        this.notificationBell.classList.add('enabled');
        this.notificationBell.title = 'Notifications enabled';

        console.log('Notifications enabled');
    }

    triggerBellShake() {
        // Trigger shake animation on the bell to prompt user to click
        if (!this.notificationsEnabled && this.notificationBell) {
            this.notificationBell.classList.add('shake');
            // Remove the class after animation completes to allow re-triggering
            setTimeout(() => {
                this.notificationBell.classList.remove('shake');
            }, 1200);  // Match the animation duration
        }
    }

    // Start periodic bell shake when there are pending requests but notifications are not enabled
    startBellReminder() {
        if (this.bellReminderInterval) return;  // Already running

        // Shake every 5 seconds while there are pending requests
        this.bellReminderInterval = setInterval(() => {
            if (!this.notificationsEnabled && this.state?.pending_requests?.length > 0) {
                this.triggerBellShake();
            } else if (this.notificationsEnabled) {
                this.stopBellReminder();
            }
        }, 5000);

        // Initial shake
        this.triggerBellShake();
    }

    stopBellReminder() {
        if (this.bellReminderInterval) {
            clearInterval(this.bellReminderInterval);
            this.bellReminderInterval = null;
        }
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
            } else if (message.type === 'stop_notification') {
                // Claude finished responding - single notification
                this.handleStopNotification(message);
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
                // Also try to show browser notification
                this.showBrowserNotification(state.pending_request);
            } else {
                // Start periodic bell shake to prompt user to enable notifications
                this.startBellReminder();
            }
        }

        // Stop vibration and bell reminder when request is handled
        if (hadPending && !hasPending) {
            this.stopContinuousVibration();
            this.stopBellReminder();
        }

        // Update chat sessions from WebSocket push (no more polling!)
        if (state.chat_sessions) {
            this.sessions = state.chat_sessions;
            // Update session count in terminal header
            if (this.terminalSessionCount) {
                this.terminalSessionCount.textContent = `(${this.sessions.length})`;
            }
            // Update dropdown if terminal is expanded
            if (this.terminalExpanded) {
                this.updateSessionSelect();
            }
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

    handleStopNotification(message) {
        // Claude finished responding - play single notification
        // Only notify if notifications are enabled
        if (this.notificationsEnabled) {
            this.playSingleNotificationSound();
            this.vibrateSingle();
        }
        console.log('Claude finished responding:', message.session_id);
    }

    playSingleNotificationSound() {
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }

        // Resume audio context if suspended (needed for mobile)
        if (this.audioContext.state === 'suspended') {
            this.audioContext.resume();
        }

        // Single soft tone to indicate completion
        const now = this.audioContext.currentTime;
        const osc = this.audioContext.createOscillator();
        const gain = this.audioContext.createGain();
        osc.connect(gain);
        gain.connect(this.audioContext.destination);
        osc.frequency.setValueAtTime(440, now); // A4 - softer tone
        gain.gain.setValueAtTime(0.2, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.2);
        osc.start(now);
        osc.stop(now + 0.2);
    }

    vibrateSingle() {
        // Single short vibration for completion notification
        if ('vibrate' in navigator) {
            navigator.vibrate(100);  // Single 100ms vibration
        }
    }

    render() {
        if (!this.state) return;

        // Render session tabs (based on Claude sessions, not projects)
        this.renderSessionTabs();

        // YOLO toggle
        this.yoloToggle.textContent = this.state.yolo_mode ? 'ON' : 'OFF';
        this.yoloToggle.className = `toggle-btn ${this.state.yolo_mode ? 'on' : 'off'}`;

        // Get active session state (filtered to active session's requests)
        const sessionState = this.getActiveSessionState();

        // Show/hide terminal based on active session type
        this.updateTerminalVisibility();

        // Pending requests - filtered to active session
        const pendingRequests = sessionState?.pending_requests || [];
        const hasPending = pendingRequests.length > 0;

        // Update pending count
        this.pendingCount.textContent = pendingRequests.length;

        // Validate selected request is still in current session's requests
        if (this.selectedRequestId) {
            const stillValid = pendingRequests.some(r => r.id === this.selectedRequestId);
            if (!stillValid) {
                // Select first request of current session if available
                this.selectedRequestId = pendingRequests.length > 0 ? pendingRequests[0].id : null;
            }
        }

        // Enable/disable action buttons based on selected request
        this.approveBtn.disabled = !this.selectedRequestId;
        this.denyBtn.disabled = !this.selectedRequestId;

        if (hasPending) {
            // Show pending section
            this.pendingSection.classList.remove('hidden');

            // Render pending requests list
            this.renderPendingRequests(pendingRequests);

            // Hide status section when pending
            this.statusSection.classList.add('hidden');
        } else {
            // Hide pending section
            this.pendingSection.classList.add('hidden');
            this.pendingList.innerHTML = '';
            this.selectedRequestId = null;

            // Status section is hidden by default (no content when nothing pending)
            this.statusSection.classList.add('hidden');
        }

        // Get project state for active session's project
        const activeSessionId = this.activeSessionId || this.state?.active_session_id;
        const activeSession = this.state?.claude_sessions?.[activeSessionId];
        const projectPath = activeSession?.project_path;

        // Find project state - try direct match first, then search
        let projectState = null;
        if (projectPath) {
            // Try direct match
            projectState = this.state?.projects?.[projectPath];

            // If not found, try to find by comparing paths
            if (!projectState && this.state?.projects) {
                for (const [path, state] of Object.entries(this.state.projects)) {
                    // Compare normalized paths
                    if (path === projectPath || path.endsWith(projectPath) || projectPath.endsWith(path)) {
                        projectState = state;
                        break;
                    }
                }
            }
        }

        // TODO List - use project state for active session
        this.renderTodos(projectState);

        // Completed tasks - use project state for active session
        this.renderCompleted(projectState);

        // Stats (global)
        const stats = this.state.stats;
        this.totalCount.textContent = stats.total_requests;
        this.approvedCount.textContent = stats.approved_count;
        this.deniedCount.textContent = stats.denied_count;
    }

    getActiveSessionState() {
        if (!this.state) return null;

        // Get pending requests for the active session only
        const activeSessionId = this.activeSessionId || this.state.active_session_id;
        if (!activeSessionId) {
            return this.state;
        }

        // Filter pending requests to active session
        const sessionRequests = (this.state.pending_requests || []).filter(
            r => r.session_id === activeSessionId
        );

        // Return a view of state filtered to active session
        return {
            ...this.state,
            pending_requests: sessionRequests,
        };
    }

    renderSessionTabs() {
        const sessions = this.state?.session_list || [];

        // Clear existing tabs
        this.projectTabs.innerHTML = '';

        // Hide/show tabs bar based on sessions
        // Always show tabs bar when there are sessions (including ended ones)
        if (sessions.length === 0) {
            this.sessionTabsBar.classList.add('hidden');
            // Update header height when tabs visibility changes
            setTimeout(() => this.updateHeaderHeight(), 0);
            return;
        }

        this.sessionTabsBar.classList.remove('hidden');
        // Update header height when tabs visibility changes
        setTimeout(() => this.updateHeaderHeight(), 0);

        // Use server's active_session_id if we haven't selected one
        if (!this.activeSessionId && this.state.active_session_id) {
            this.activeSessionId = this.state.active_session_id;
        }

        // If the selected session no longer exists, select first available
        const activeExists = sessions.some(s => s.session_id === this.activeSessionId);
        if (!activeExists && sessions.length > 0) {
            // Prefer non-ended sessions
            const activeSession = sessions.find(s => !s.ended) || sessions[0];
            this.activeSessionId = activeSession.session_id;
        }

        for (const session of sessions) {
            const tab = document.createElement('button');
            tab.className = 'session-tab';
            if (session.session_id === this.activeSessionId) {
                tab.classList.add('active');
            }
            if (session.pending_count > 0) {
                tab.classList.add('has-pending');
            }
            if (session.ended) {
                tab.classList.add('ended');
            }

            // Show pending count badge if any
            const pendingBadge = session.pending_count > 0
                ? `<span class="tab-badge">${session.pending_count}</span>`
                : '';

            // Show session type indicator (internal = 💻, external = empty)
            const typeIcon = session.is_external && !session.chat_session_id
                ? ''
                : '<span class="tab-icon">💻</span>';

            // Show ended indicator for ended sessions
            const endedBadge = session.ended
                ? '<span class="tab-ended-badge">Ended</span>'
                : '';

            // Close button for ended sessions
            const closeBtn = session.ended
                ? `<span class="tab-close" onclick="event.stopPropagation(); app.removeSession('${session.session_id}')" title="Remove this session">✕</span>`
                : '';

            tab.innerHTML = `
                ${typeIcon}<span class="tab-name">${this.escapeHtml(session.project_name)}</span>${pendingBadge}${endedBadge}${closeBtn}
            `;

            tab.onclick = () => this.selectSession(session.session_id);
            this.projectTabs.appendChild(tab);
        }
    }

    async removeSession(sessionId) {
        // Remove session from UI (notify server to remove from tracking)
        try {
            await fetch(`/api/session/${sessionId}`, {
                method: 'DELETE'
            });
        } catch (error) {
            console.error('Error removing session:', error);
        }
    }

    async selectSession(sessionId) {
        this.activeSessionId = sessionId;

        // Also update selected request to first request of this session
        const sessionRequests = (this.state?.pending_requests || []).filter(
            r => r.session_id === sessionId
        );
        if (sessionRequests.length > 0) {
            this.selectedRequestId = sessionRequests[0].id;
        } else {
            this.selectedRequestId = null;
        }

        // Notify server about active session selection
        try {
            await fetch('/api/session/active', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId })
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

    renderPendingRequests(requests) {
        // Keep track of existing request IDs to avoid unnecessary re-renders
        const existingIds = new Set();
        for (const child of this.pendingList.children) {
            existingIds.add(child.dataset.requestId);
        }

        const newIds = new Set(requests.map(r => r.id));

        // Remove items that are no longer pending
        for (const child of [...this.pendingList.children]) {
            if (!newIds.has(child.dataset.requestId)) {
                child.remove();
            }
        }

        // Add or update items
        for (const request of requests) {
            let item = this.pendingList.querySelector(`[data-request-id="${request.id}"]`);

            if (!item) {
                // Create new item
                item = document.createElement('div');
                item.className = 'pending-item';
                item.dataset.requestId = request.id;
                this.pendingList.appendChild(item);
            }

            // Update selection state
            if (request.id === this.selectedRequestId) {
                item.classList.add('selected');
            } else {
                item.classList.remove('selected');
            }

            // Get session display name (first 8 chars of session_id or project name)
            const sessionLabel = request.session_id
                ? request.session_id.substring(0, 8)
                : (request.project_name || 'unknown');

            item.innerHTML = `
                <div class="pending-item-header">
                    <span class="pending-item-session">${this.escapeHtml(sessionLabel)}</span>
                    <div class="pending-item-actions">
                        <button class="approve-btn" onclick="app.approveRequest('${request.id}')">Approve</button>
                        <button class="deny-btn" onclick="app.denyRequest('${request.id}')">Deny</button>
                    </div>
                </div>
                <div class="tool-info">
                    <span class="tool-name">${this.escapeHtml(request.tool_name)}</span>
                    <pre class="tool-input">${this.escapeHtml(this.formatToolInput(request))}</pre>
                </div>
            `;

            // Click to select (for keyboard shortcuts)
            item.onclick = (e) => {
                if (e.target.tagName !== 'BUTTON') {
                    this.selectRequest(request.id);
                }
            };
        }

        // Auto-select first request if none selected
        if (!this.selectedRequestId && requests.length > 0) {
            this.selectedRequestId = requests[0].id;
            this.render();
        }
    }

    selectRequest(requestId) {
        this.selectedRequestId = requestId;
        this.render();
    }

    async approveRequest(requestId) {
        try {
            const response = await fetch('/api/approve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ request_id: requestId })
            });
            if (!response.ok) {
                console.error('Failed to approve request');
            }
        } catch (error) {
            console.error('Error approving request:', error);
        }
    }

    async denyRequest(requestId) {
        try {
            const response = await fetch('/api/deny', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ request_id: requestId })
            });
            if (!response.ok) {
                console.error('Failed to deny request');
            }
        } catch (error) {
            console.error('Error denying request:', error);
        }
    }

    renderTodos(projectState) {
        // Get todos from project state, or fall back to global state
        const todos = projectState?.todos || this.state?.todos || [];
        this.todoCount.textContent = todos.length;

        // Hide section when empty
        if (todos.length === 0) {
            this.todoSection.classList.add('hidden');
            this.todoSection.classList.remove('all-completed');
            return;
        }

        this.todoSection.classList.remove('hidden');

        // Check if all todos are completed
        const allCompleted = todos.length > 0 && todos.every(t => t.status === 'completed');

        if (allCompleted) {
            // Collapse and show completion state
            this.todoSection.classList.add('all-completed');
            this.todoList.classList.add('hidden');
        } else {
            // Expand and show todos
            this.todoSection.classList.remove('all-completed');
            this.todoList.classList.remove('hidden');
        }

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

    toggleTodoExpand() {
        // Only toggle if all todos are completed
        if (this.todoSection.classList.contains('all-completed')) {
            this.todoSection.classList.toggle('expanded');
            // Show/hide the todos list
            if (this.todoSection.classList.contains('expanded')) {
                this.todoList.classList.remove('hidden');
            } else {
                this.todoList.classList.add('hidden');
            }
        }
    }

    renderCompleted(projectState) {
        // Get completed tasks from project state, or fall back to global state
        const tasks = projectState?.completed_tasks || this.state?.completed_tasks || [];
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
        // Use selected request ID
        if (!this.selectedRequestId) return;

        if (decision === 'approve') {
            await this.approveRequest(this.selectedRequestId);
            this.vibrate();
        } else {
            await this.denyRequest(this.selectedRequestId);
        }
        // Note: buttons will be re-enabled by the state update from WebSocket
    }

    // ==================== Terminal Methods ====================

    updateTerminalVisibility() {
        // Get the active Claude session to check if it's external
        const activeSessionId = this.activeSessionId || this.state?.active_session_id;
        const session = this.state?.claude_sessions?.[activeSessionId];

        // A session is internal if:
        // - is_external=false (started via claude-board chat)
        // - OR has a linked chat_session_id
        const isInternal = session && (!session.is_external || session.chat_session_id);
        const hasLinkedChatSession = session?.chat_session_id;

        if (session && !isInternal) {
            // External session with no linked chat - hide terminal completely
            this.terminalSection.classList.add('hidden');
            // Also hide prompt input bar
            this.promptInputBar.classList.add('hidden');
        } else if (hasLinkedChatSession) {
            // Internal session with linked chat - show terminal and auto-connect
            this.terminalSection.classList.remove('hidden');

            // Auto-expand terminal for internal sessions (if not already expanded)
            if (!this.terminalExpanded) {
                this.expandTerminalAutomatically();
            }

            // Auto-connect if not already connected to this chat session
            if (this.connectedSessionId !== hasLinkedChatSession) {
                this.autoConnectToSession(hasLinkedChatSession);
            }

            // Show prompt input bar when connected
            if (this.connectedSessionId) {
                this.promptInputBar.classList.remove('hidden');
            }
        } else {
            // No session selected - hide terminal
            this.terminalSection.classList.add('hidden');
            this.promptInputBar.classList.add('hidden');
        }

        // Update terminal status
        this.updateTerminalStatus();
    }

    expandTerminalAutomatically() {
        // Expand terminal without user interaction
        this.terminalExpanded = true;
        this.terminalSection.classList.remove('collapsed');
        this.terminalBody.classList.remove('hidden');

        // Initialize terminal on first expand (lazy load)
        if (!this.terminal) {
            this.initTerminal();
        }

        // Fit terminal after expand
        setTimeout(() => {
            if (this.terminalFitAddon) {
                this.terminalFitAddon.fit();
            }
        }, 100);
    }

    updateTerminalStatus() {
        if (this.connectedSessionId) {
            this.terminalStatus.textContent = '● Connected';
            this.terminalStatus.className = 'terminal-status connected';
        } else {
            this.terminalStatus.textContent = '';
            this.terminalStatus.className = 'terminal-status';
        }
    }

    async autoConnectToSession(chatSessionId) {
        // Check if already connected to this session
        if (this.connectedSessionId === chatSessionId) {
            return;
        }

        // Don't auto-connect while another connection is in progress
        if (this._autoConnecting) {
            return;
        }

        this._autoConnecting = true;

        try {
            // Sessions are now pushed via WebSocket, no need to refresh
            // Just check if this chat session exists and is running
            const chatSession = this.sessions.find(s => s.session_id === chatSessionId);
            if (chatSession && chatSession.state !== 'stopped') {
                // Auto-connect directly without using dropdown
                await this.connectToSessionById(chatSessionId);
            }
        } finally {
            this._autoConnecting = false;
        }
    }

    async connectToSessionById(sessionId) {
        // Disconnect from any existing session
        this.disconnectFromSession();

        // Connect to the terminal WebSocket
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/sessions/${sessionId}/terminal`;

        console.log('Auto-connecting to terminal WebSocket:', wsUrl);

        this.terminalWs = new WebSocket(wsUrl);

        this.terminalWs.onopen = () => {
            console.log('Terminal WebSocket connected');
            this.connectedSessionId = sessionId;

            // Update UI
            this.promptInput.disabled = false;
            this.promptSendBtn.disabled = false;
            this.sessionSelect.value = sessionId;

            // Show prompt input bar
            this.promptInputBar.classList.remove('hidden');

            // Update terminal status
            this.updateTerminalStatus();

            // Clear terminal and show connection message
            if (this.terminal) {
                this.terminal.clear();
                this.terminal.writeln(`\x1b[1;32mConnected to session: ${sessionId}\x1b[0m`);
                this.terminal.writeln('');
            }

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
                // Check for RESET marker: \x00RESET\x00 prefix
                const data = message.data;
                if (typeof data === 'string' && this.terminal) {
                    const RESET_MARKER = '\x00RESET\x00';
                    if (data.startsWith(RESET_MARKER)) {
                        // Full history redraw mode: clear terminal and write full history
                        this.terminal.reset();
                        this.terminal.write(data.substring(RESET_MARKER.length));
                    } else {
                        this.terminal.write(data);
                    }
                }
            } else if (message.type === 'history') {
                // Write history output (initial connection)
                if (message.data && this.terminal) {
                    this.terminal.reset();
                    this.terminal.write(message.data);
                }
            } else if (message.type === 'session_ended') {
                if (this.terminal) {
                    this.terminal.writeln('');
                    this.terminal.writeln('\x1b[1;33mSession ended.\x1b[0m');
                }
                this.disconnectFromSession();
            } else if (message.type === 'error') {
                if (this.terminal) {
                    this.terminal.writeln('');
                    this.terminal.writeln(`\x1b[1;31mError: ${message.message}\x1b[0m`);
                }
            }
        };

        this.terminalWs.onclose = () => {
            console.log('Terminal WebSocket disconnected');
            if (this.connectedSessionId === sessionId) {
                if (this.terminal) {
                    this.terminal.writeln('');
                    this.terminal.writeln('\x1b[1;33mDisconnected from session.\x1b[0m');
                }
                this.resetTerminalUI();
            }
        };

        this.terminalWs.onerror = (error) => {
            console.error('Terminal WebSocket error:', error);
            if (this.terminal) {
                this.terminal.writeln('');
                this.terminal.writeln('\x1b[1;31mConnection error.\x1b[0m');
            }
        };
    }

    toggleTerminal() {
        this.terminalExpanded = !this.terminalExpanded;

        if (this.terminalExpanded) {
            this.terminalSection.classList.remove('collapsed');
            this.terminalBody.classList.remove('hidden');

            // Initialize terminal on first expand (lazy load)
            if (!this.terminal) {
                this.initTerminal();
            }

            // Fit terminal after expand
            setTimeout(() => {
                if (this.terminalFitAddon) {
                    this.terminalFitAddon.fit();
                }
            }, 100);

            // Sessions are now pushed via WebSocket, just update the dropdown
            this.updateSessionSelect();
        } else {
            this.terminalSection.classList.add('collapsed');
            this.terminalBody.classList.add('hidden');

            // Disconnect from session when collapsing
            if (this.connectedSessionId) {
                this.disconnectFromSession();
            }
        }
    }

    initTerminal() {
        // Check if xterm.js is loaded
        if (typeof Terminal === 'undefined') {
            console.warn('xterm.js not loaded, terminal features disabled');
            return;
        }

        // Create terminal instance (READ-ONLY mode)
        // disableStdin: true makes the terminal read-only
        // Users interact via the prompt input box below
        //
        // IMPORTANT: scrollback is set to 0 to fix ANSI cursor control issues.
        // Claude Code uses ESC[1A (cursor up) and ESC[2K (erase line) for animations.
        // When content scrolls into the scrollback buffer, these sequences fail
        // because the cursor cannot move into the scrollback area.
        // With scrollback: 0, all content stays in the visible area.
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
            scrollback: 0,  // Disable scrollback to fix ANSI cursor control
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
            if (this.terminalFitAddon && this.terminalExpanded) {
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

                // Update session count in header (if element exists)
                if (this.terminalSessionCount) {
                    this.terminalSessionCount.textContent = `(${this.sessions.length})`;
                }

                // Only update select if terminal is expanded
                if (this.terminalExpanded) {
                    this.updateSessionSelect();
                }
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
        if (sessionId) {
            // Auto-connect when a session is selected
            this.connectToSessionById(sessionId);
        } else {
            // Disconnect when "Select session..." is chosen
            this.disconnectFromSession();
        }
    }

    // connectToSession is now replaced by connectToSessionById which is called
    // from onSessionSelectChange and autoConnectToSession

    disconnectFromSession() {
        if (this.terminalWs) {
            this.terminalWs.close();
            this.terminalWs = null;
        }
        this.resetTerminalUI();
    }

    resetTerminalUI() {
        this.connectedSessionId = null;
        this.promptInput.disabled = true;
        this.promptSendBtn.disabled = true;
        this.sessionSelect.value = '';

        // Hide prompt input bar
        this.promptInputBar.classList.add('hidden');

        // Update terminal status
        this.updateTerminalStatus();
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
