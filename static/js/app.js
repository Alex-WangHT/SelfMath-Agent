const App = {
    sessionId: null,
    isProcessing: false,
    currentFile: null,
    uploadModal: null,
    questionsModal: null,

    init() {
        this.sessionId = this.generateSessionId();
        this.initModals();
        this.initEventListeners();
        this.loadStatistics();
        this.renderMathInElement(document.body);
    },

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    },

    initModals() {
        const uploadModalEl = document.getElementById('uploadModal');
        const questionsModalEl = document.getElementById('questionsModal');
        
        if (uploadModalEl) {
            this.uploadModal = new bootstrap.Modal(uploadModalEl);
        }
        if (questionsModalEl) {
            this.questionsModal = new bootstrap.Modal(questionsModalEl);
        }
    },

    initEventListeners() {
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        
        if (messageInput) {
            messageInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            messageInput.addEventListener('input', () => {
                this.autoResizeTextarea(messageInput);
                this.updateSendButton();
            });
        }

        if (sendBtn) {
            sendBtn.addEventListener('click', () => {
                this.sendMessage();
            });
        }

        const newChatBtn = document.getElementById('newChatBtn');
        if (newChatBtn) {
            newChatBtn.addEventListener('click', () => {
                this.startNewChat();
            });
        }

        const clearChatBtn = document.getElementById('clearChatBtn');
        if (clearChatBtn) {
            clearChatBtn.addEventListener('click', () => {
                this.clearChat();
            });
        }

        const attachPdfBtn = document.getElementById('attachPdfBtn');
        const uploadPdfBtn = document.getElementById('uploadPdfBtn');
        const pdfInput = document.getElementById('pdfInput');
        
        [attachPdfBtn, uploadPdfBtn].forEach(btn => {
            if (btn) {
                btn.addEventListener('click', () => {
                    this.openUploadModal('pdf');
                });
            }
        });

        if (pdfInput) {
            pdfInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleFileSelect(e.target.files[0], 'pdf');
                }
            });
        }

        const attachImageBtn = document.getElementById('attachImageBtn');
        const uploadImageBtn = document.getElementById('uploadImageBtn');
        const imageInput = document.getElementById('imageInput');
        
        [attachImageBtn, uploadImageBtn].forEach(btn => {
            if (btn) {
                btn.addEventListener('click', () => {
                    this.openUploadModal('image');
                });
            }
        });

        if (imageInput) {
            imageInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleFileSelect(e.target.files[0], 'image');
                }
            });
        }

        const viewQuestionsBtn = document.getElementById('viewQuestionsBtn');
        if (viewQuestionsBtn) {
            viewQuestionsBtn.addEventListener('click', () => {
                this.loadQuestions();
            });
        }

        const searchQuestionsBtn = document.getElementById('searchQuestionsBtn');
        if (searchQuestionsBtn) {
            searchQuestionsBtn.addEventListener('click', () => {
                this.questionsModal.show();
                document.getElementById('questionSearchInput').focus();
            });
        }

        const agentSelector = document.getElementById('agentSelector');
        if (agentSelector) {
            agentSelector.addEventListener('change', (e) => {
                console.log('Agent selected:', e.target.value);
            });
        }

        const sidebarToggle = document.getElementById('sidebarToggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                document.querySelector('.sidebar').classList.toggle('open');
            });
        }

        const quickBtns = document.querySelectorAll('.quick-btn');
        quickBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.dataset.action;
                this.handleQuickAction(action);
            });
        });

        const uploadArea = document.getElementById('uploadArea');
        const selectFileBtn = document.getElementById('selectFileBtn');
        const startProcessBtn = document.getElementById('startProcessBtn');
        
        if (uploadArea) {
            uploadArea.addEventListener('click', () => {
                this.triggerFileInput();
            });

            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });

            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                if (e.dataTransfer.files.length > 0) {
                    this.handleFileSelect(e.dataTransfer.files[0], this.detectFileType(e.dataTransfer.files[0]));
                }
            });
        }

        if (selectFileBtn) {
            selectFileBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.triggerFileInput();
            });
        }

        if (startProcessBtn) {
            startProcessBtn.addEventListener('click', () => {
                this.processUploadedFile();
            });
        }

        const searchQuestionBtn = document.getElementById('searchQuestionBtn');
        const questionSearchInput = document.getElementById('questionSearchInput');
        
        if (searchQuestionBtn) {
            searchQuestionBtn.addEventListener('click', () => {
                this.searchQuestions();
            });
        }

        if (questionSearchInput) {
            questionSearchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    this.searchQuestions();
                }
            });
        }

        const questionTypeFilter = document.getElementById('questionTypeFilter');
        if (questionTypeFilter) {
            questionTypeFilter.addEventListener('change', () => {
                this.loadQuestions();
            });
        }
    },

    autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    },

    updateSendButton() {
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        
        if (messageInput && sendBtn) {
            const hasContent = messageInput.value.trim().length > 0;
            sendBtn.disabled = !hasContent || this.isProcessing;
        }
    },

    detectFileType(file) {
        const ext = file.name.split('.').pop().toLowerCase();
        if (ext === 'pdf') return 'pdf';
        if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(ext)) return 'image';
        return 'unknown';
    },

    triggerFileInput() {
        const fileType = this.currentUploadType || 'pdf';
        const input = document.getElementById(fileType === 'pdf' ? 'pdfInput' : 'imageInput');
        if (input) {
            input.click();
        }
    },

    openUploadModal(type) {
        this.currentUploadType = type;
        const uploadModal = document.getElementById('uploadModal');
        const uploadArea = document.getElementById('uploadArea');
        const uploadProgress = document.getElementById('uploadProgress');
        const uploadResult = document.getElementById('uploadResult');
        const uploadOptions = document.getElementById('uploadOptions');
        
        if (uploadArea) uploadArea.style.display = 'flex';
        if (uploadProgress) uploadProgress.style.display = 'none';
        if (uploadResult) uploadResult.style.display = 'none';
        if (uploadOptions) uploadOptions.style.display = 'none';
        
        if (uploadModal) {
            const modalTitle = uploadModal.querySelector('.modal-title');
            if (modalTitle) {
                modalTitle.innerHTML = `<i class="bi bi-upload"></i> 上传${type === 'pdf' ? 'PDF' : '图片'}`;
            }
            
            const uploadHint = uploadModal.querySelector('.upload-hint');
            if (uploadHint) {
                uploadHint.textContent = type === 'pdf' ? 
                    '支持 PDF 格式（最大 100MB）' : 
                    '支持 JPG、PNG、GIF、BMP、WebP 格式';
            }
        }
        
        if (this.uploadModal) {
            this.uploadModal.show();
        }
    },

    handleFileSelect(file, type) {
        if (type === 'unknown') {
            this.showToast('不支持的文件格式', 'error');
            return;
        }

        const maxSize = type === 'pdf' ? 100 * 1024 * 1024 : 10 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showToast(`文件过大，最大支持 ${type === 'pdf' ? '100MB' : '10MB'}`, 'error');
            return;
        }

        this.currentFile = file;
        this.currentUploadType = type;
        
        this.showUploadOptions(file);
    },

    showUploadOptions(file) {
        const uploadArea = document.getElementById('uploadArea');
        const uploadOptions = document.getElementById('uploadOptions');
        const uploadProgress = document.getElementById('uploadProgress');
        const uploadResult = document.getElementById('uploadResult');
        
        if (uploadArea) uploadArea.style.display = 'none';
        if (uploadProgress) uploadProgress.style.display = 'none';
        if (uploadResult) uploadResult.style.display = 'none';
        if (uploadOptions) uploadOptions.style.display = 'block';
        
        const fileName = document.getElementById('uploadFileName');
        const fileSize = document.getElementById('uploadFileSize');
        
        if (fileName) fileName.textContent = file.name;
        if (fileSize) fileSize.textContent = this.formatFileSize(file.size);
        
        const pageRangeInput = document.querySelector('.page-range-input');
        if (pageRangeInput) {
            pageRangeInput.style.display = this.currentUploadType === 'pdf' ? 'block' : 'none';
        }
    },

    async processUploadedFile() {
        if (!this.currentFile) return;

        const uploadOptions = document.getElementById('uploadOptions');
        const uploadProgress = document.getElementById('uploadProgress');
        const uploadArea = document.getElementById('uploadArea');
        const uploadResult = document.getElementById('uploadResult');
        
        if (uploadOptions) uploadOptions.style.display = 'none';
        if (uploadProgress) uploadProgress.style.display = 'block';
        if (uploadArea) uploadArea.style.display = 'none';
        if (uploadResult) uploadResult.style.display = 'none';

        const progressBar = document.getElementById('uploadProgressBar');
        const uploadStatus = document.getElementById('uploadStatus');
        
        try {
            const formData = new FormData();
            formData.append('file', this.currentFile);
            formData.append('session_id', this.sessionId);
            
            if (this.currentUploadType === 'pdf') {
                const startPage = document.getElementById('startPage')?.value;
                const endPage = document.getElementById('endPage')?.value;
                const crossPageMerge = document.getElementById('crossPageMerge')?.checked;
                
                if (startPage) formData.append('start_page', startPage);
                if (endPage) formData.append('end_page', endPage);
                if (crossPageMerge) formData.append('cross_page_merge', crossPageMerge);
            }

            if (progressBar) progressBar.style.width = '10%';
            if (uploadStatus) uploadStatus.textContent = '正在上传文件...';

            const url = this.currentUploadType === 'pdf' ? 
                '/api/upload/pdf' : '/api/upload/image';

            const response = await fetch(url, {
                method: 'POST',
                body: formData
            });

            if (progressBar) progressBar.style.width = '50%';
            if (uploadStatus) uploadStatus.textContent = '正在处理文件...';

            const result = await response.json();

            if (progressBar) progressBar.style.width = '80%';

            if (response.ok && result.success) {
                if (progressBar) progressBar.style.width = '100%';
                if (uploadStatus) uploadStatus.textContent = '处理完成！';
                
                await this.delay(500);
                this.showUploadResult(result);
                this.loadStatistics();
                
                if (this.currentUploadType === 'pdf') {
                    const extractedCount = result.extracted_count || 0;
                    const crossPageCount = result.cross_page_count || 0;
                    const totalCount = extractedCount + crossPageCount;
                    
                    this.addMessage('assistant', 
                        `📄 PDF 文件处理完成！\n\n` +
                        `- 文件名：${this.currentFile.name}\n` +
                        `- 提取题目：${extractedCount} 道\n` +
                        `- 跨页合并：${crossPageCount} 道\n` +
                        `- 总计：${totalCount} 道\n\n` +
                        `题目已存入题库，您可以在左侧菜单查看或搜索题目。`
                    );
                } else {
                    this.addMessage('assistant', 
                        `🖼️ 图片识别完成！\n\n` +
                        `文件名：${this.currentFile.name}\n\n` +
                        `${result.content || '图片内容已解析。'}`
                    );
                }
            } else {
                throw new Error(result.error || '上传失败');
            }
        } catch (error) {
            console.error('Upload error:', error);
            if (uploadStatus) uploadStatus.textContent = '上传失败';
            if (progressBar) {
                progressBar.style.width = '100%';
                progressBar.classList.add('bg-danger');
            }
            this.showToast('上传失败: ' + error.message, 'error');
        }
    },

    showUploadResult(result) {
        const uploadProgress = document.getElementById('uploadProgress');
        const uploadResult = document.getElementById('uploadResult');
        const uploadStats = document.getElementById('uploadStats');
        
        if (uploadProgress) uploadProgress.style.display = 'none';
        if (uploadResult) uploadResult.style.display = 'flex';
        
        if (uploadStats) {
            if (this.currentUploadType === 'pdf') {
                const extractedCount = result.extracted_count || 0;
                const crossPageCount = result.cross_page_count || 0;
                const totalCount = extractedCount + crossPageCount;
                
                uploadStats.innerHTML = `
                    <div class="result-stat">
                        <div class="result-stat-value">${extractedCount}</div>
                        <div class="result-stat-label">提取题目</div>
                    </div>
                    <div class="result-stat">
                        <div class="result-stat-value">${crossPageCount}</div>
                        <div class="result-stat-label">跨页合并</div>
                    </div>
                    <div class="result-stat">
                        <div class="result-stat-value">${totalCount}</div>
                        <div class="result-stat-label">总计</div>
                    </div>
                `;
            } else {
                uploadStats.innerHTML = `
                    <div class="result-stat">
                        <div class="result-stat-value">✓</div>
                        <div class="result-stat-label">识别完成</div>
                    </div>
                `;
            }
        }
    },

    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput?.value.trim();
        
        if (!message || this.isProcessing) return;

        this.isProcessing = true;
        this.updateSendButton();
        
        const welcomeScreen = document.getElementById('welcomeScreen');
        const messagesContainer = document.getElementById('messagesContainer');
        
        if (welcomeScreen) welcomeScreen.style.display = 'none';
        if (messagesContainer) messagesContainer.style.display = 'block';

        this.addMessage('user', message);
        
        messageInput.value = '';
        this.autoResizeTextarea(messageInput);

        this.showTypingIndicator();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId,
                    agent_role: this.getSelectedAgent()
                })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                this.addMessage('assistant', result.response);
            } else {
                throw new Error(result.error || '请求失败');
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.addMessage('assistant', `抱歉，发生了错误：${error.message}。请稍后重试。`);
            this.showToast('发送失败', 'error');
        } finally {
            this.hideTypingIndicator();
            this.isProcessing = false;
            this.updateSendButton();
        }
    },

    getSelectedAgent() {
        const agentSelector = document.getElementById('agentSelector');
        return agentSelector?.value || 'question_bank';
    },

    addMessage(role, content) {
        const messagesContainer = document.getElementById('messagesContainer');
        if (!messagesContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const avatarHtml = role === 'user' 
            ? '<div class="message-avatar"><i class="bi bi-person"></i></div>'
            : '<div class="message-avatar"><i class="bi bi-robot"></i></div>';

        const formattedContent = this.formatMessage(content);

        messageDiv.innerHTML = `
            ${avatarHtml}
            <div class="message-content">
                <div class="message-bubble">${formattedContent}</div>
            </div>
        `;

        messagesContainer.appendChild(messageDiv);
        
        this.renderMathInElement(messageDiv);
        this.scrollToBottom();
    },

    formatMessage(content) {
        if (typeof marked !== 'undefined') {
            marked.setOptions({
                breaks: true,
                gfm: true,
                sanitize: false
            });
            return marked.parse(content);
        }
        return content.replace(/\n/g, '<br>');
    },

    renderMathInElement(element) {
        if (typeof renderMathInElement !== 'undefined') {
            renderMathInElement(element, {
                delimiters: [
                    {left: '$$', right: '$$', display: true},
                    {left: '$', right: '$', display: false},
                    {left: '\\(', right: '\\)', display: false},
                    {left: '\\[', right: '\\]', display: true}
                ],
                throwOnError: false,
                displayMode: true
            });
        }
    },

    showTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.style.display = 'block';
            this.scrollToBottom();
        }
    },

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.style.display = 'none';
        }
    },

    scrollToBottom() {
        const chatContainer = document.getElementById('chatContainer');
        if (chatContainer) {
            setTimeout(() => {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }, 100);
        }
    },

    startNewChat() {
        this.sessionId = this.generateSessionId();
        this.clearChat();
    },

    clearChat() {
        const welcomeScreen = document.getElementById('welcomeScreen');
        const messagesContainer = document.getElementById('messagesContainer');
        
        if (welcomeScreen) welcomeScreen.style.display = 'flex';
        if (messagesContainer) {
            messagesContainer.innerHTML = '';
            messagesContainer.style.display = 'none';
        }
        
        this.hideTypingIndicator();
        this.isProcessing = false;
        this.updateSendButton();
    },

    async loadStatistics() {
        try {
            const response = await fetch('/api/questions/stats');
            const result = await response.json();
            
            if (result.success) {
                const stats = result.stats;
                this.updateStatsDisplay(stats);
            }
        } catch (error) {
            console.error('Failed to load statistics:', error);
        }
    },

    updateStatsDisplay(stats) {
        const totalEl = document.getElementById('totalQuestions');
        const exampleEl = document.getElementById('exampleCount');
        const exerciseEl = document.getElementById('exerciseCount');
        
        if (totalEl) totalEl.textContent = stats.total || 0;
        if (exampleEl) exampleEl.textContent = stats.examples || 0;
        if (exerciseEl) exerciseEl.textContent = stats.exercises || 0;
    },

    async loadQuestions(questionType = null) {
        if (!questionType) {
            questionType = document.getElementById('questionTypeFilter')?.value || '';
        }

        try {
            let url = '/api/questions';
            if (questionType) {
                url += `?question_type=${questionType}`;
            }
            
            const response = await fetch(url);
            const result = await response.json();
            
            if (result.success) {
                this.renderQuestionsList(result.questions);
                if (this.questionsModal) {
                    this.questionsModal.show();
                }
            }
        } catch (error) {
            console.error('Failed to load questions:', error);
            this.showToast('加载题目失败', 'error');
        }
    },

    async searchQuestions() {
        const query = document.getElementById('questionSearchInput')?.value;
        if (!query?.trim()) {
            this.loadQuestions();
            return;
        }

        try {
            const response = await fetch('/api/questions/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    n_results: 20
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.renderQuestionsList(result.results);
            }
        } catch (error) {
            console.error('Failed to search questions:', error);
            this.showToast('搜索失败', 'error');
        }
    },

    renderQuestionsList(questions) {
        const questionsList = document.getElementById('questionsList');
        if (!questionsList) return;

        if (!questions || questions.length === 0) {
            questionsList.innerHTML = `
                <div class="text-center py-5">
                    <i class="bi bi-inbox" style="font-size: 48px; color: var(--text-muted);"></i>
                    <p class="mt-3" style="color: var(--text-secondary);">暂无题目</p>
                </div>
            `;
            return;
        }

        questionsList.innerHTML = questions.map((q, index) => {
            const question = q.question || q;
            const metadata = q.metadata || {};
            const questionType = metadata.question_type || 'exercise';
            const page = metadata.page || '-';
            const source = metadata.source || '';
            
            return `
                <div class="question-item" data-index="${index}">
                    <div class="question-header">
                        <span class="question-number">题目 ${index + 1}</span>
                        <span class="question-type-badge ${questionType}">
                            ${questionType === 'example' ? '例题' : '习题'}
                        </span>
                    </div>
                    <div class="question-content">
                        ${this.formatMessage(question)}
                    </div>
                    <div class="question-actions">
                        <button class="btn btn-sm btn-outline-primary" onclick="App.copyQuestion(${index})">
                            <i class="bi bi-clipboard"></i> 复制
                        </button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="App.sendToChat(${index})">
                            <i class="bi bi-chat"></i> 发送到对话
                        </button>
                        ${page !== '-' ? `<span class="text-muted small ms-auto">页码: ${page} ${source ? `| 来源: ${source}` : ''}</span>` : ''}
                    </div>
                </div>
            `;
        }).join('');

        this.renderMathInElement(questionsList);
    },

    copyQuestion(index) {
        const questionsList = document.getElementById('questionsList');
        const item = questionsList?.querySelector(`[data-index="${index}"]`);
        const content = item?.querySelector('.question-content')?.innerText;
        
        if (content) {
            navigator.clipboard.writeText(content).then(() => {
                this.showToast('已复制到剪贴板', 'success');
            });
        }
    },

    sendToChat(index) {
        const questionsList = document.getElementById('questionsList');
        const item = questionsList?.querySelector(`[data-index="${index}"]`);
        const content = item?.querySelector('.question-content')?.innerText;
        
        if (content) {
            if (this.questionsModal) {
                this.questionsModal.hide();
            }
            
            const messageInput = document.getElementById('messageInput');
            if (messageInput) {
                messageInput.value = content;
                this.autoResizeTextarea(messageInput);
                this.updateSendButton();
                messageInput.focus();
            }
        }
    },

    handleQuickAction(action) {
        const messageInput = document.getElementById('messageInput');
        
        switch (action) {
            case 'upload_pdf':
                this.openUploadModal('pdf');
                break;
            case 'explain_concept':
                if (messageInput) {
                    messageInput.value = '请解释一下极限的概念';
                    this.autoResizeTextarea(messageInput);
                    this.updateSendButton();
                    messageInput.focus();
                }
                break;
            case 'search_question':
                this.loadQuestions();
                break;
        }
    },

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) return;

        const toastId = 'toast_' + Date.now();
        const toastEl = document.createElement('div');
        toastEl.id = toastId;
        toastEl.className = `toast ${type}`;
        
        let icon = 'info-circle';
        switch (type) {
            case 'success': icon = 'check-circle'; break;
            case 'error': icon = 'exclamation-circle'; break;
            case 'warning': icon = 'exclamation-triangle'; break;
        }

        toastEl.innerHTML = `
            <div class="toast-icon">
                <i class="bi bi-${icon}"></i>
            </div>
            <div class="toast-message">${message}</div>
            <button class="toast-close" onclick="App.closeToast('${toastId}')">
                <i class="bi bi-x"></i>
            </button>
        `;

        toastContainer.appendChild(toastEl);

        setTimeout(() => {
            this.closeToast(toastId);
        }, 5000);
    },

    closeToast(toastId) {
        const toastEl = document.getElementById(toastId);
        if (toastEl) {
            toastEl.style.animation = 'toastIn 0.3s ease reverse';
            setTimeout(() => {
                toastEl.remove();
            }, 300);
        }
    },

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
};

document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
