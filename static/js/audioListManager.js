/**
 * 音频列表管理器模块
 * 负责管理说话人选择和音频列表显示
 */
class AudioListManager {
    constructor(speakerSelect, audioListContainer, vaScale = '5_point') {
        this.speakerSelect = speakerSelect;
        this.audioListContainer = audioListContainer;
        this.currentSpeaker = null;
        this.audioList = [];
        this.currentAudioIndex = -1;
        this.onAudioSelectCallback = null;
        this.vaScale = vaScale; // 添加va_scale支持
        
        this.initEventListeners();
    }

    /**
     * 初始化事件监听器
     */
    initEventListeners() {
        this.speakerSelect.addEventListener('change', (e) => {
            this.handleSpeakerChange(e.target.value);
        });
    }

    /**
     * 初始化音频列表（直接加载所有音频，不需要选择说话人）
     */
    async initSpeakers() {
        console.log(`AudioListManager.initSpeakers called with vaScale: ${this.vaScale}`);
        
        // 隐藏说话人选择区域
        const speakerSection = this.speakerSelect.closest('.speaker-section');
        if (speakerSection) {
            speakerSection.style.display = 'none';
        }
        
        // 直接加载所有音频
        await this.loadAllAudioList();
        
        console.log(`AudioListManager.initSpeakers completed for ${this.vaScale} scale, loaded ${this.audioList.length} audio files`);
    }

    /**
     * 处理说话人选择变化
     */
    async handleSpeakerChange(speaker) {
        if (!speaker) {
            this.clearAudioList();
            return;
        }
        
        this.currentSpeaker = speaker;
        await this.loadAudioList(speaker);
    }

    /**
     * 加载音频列表
     */
    async loadAudioList(speaker) {
        try {
            const username = window.userManager?.getCurrentUsername();
            if (!username) {
                console.error('User not logged in');
                return;
            }
            
            const audioList = await window.optimizedDataService.getAudioList(speaker, username, this.vaScale);
            
            this.audioList = audioList;
            this.renderAudioList();
        } catch (error) {
            console.error('Failed to load audio list:', error);
        }
    }

    /**
     * 加载所有音频列表（不按说话人分组）
     */
    async loadAllAudioList() {
        try {
            console.log(`Loading audio list for vaScale: ${this.vaScale}`);
            
            // 使用优化的数据服务获取所有音频
            const audioList = await window.optimizedDataService.getAllAudioList(this.vaScale);
            
            console.log(`Received audio list:`, audioList);
            
            if (!audioList || audioList.length === 0) {
                console.warn('No audio list data received or list is empty');
                this.audioList = [];
            } else {
                this.audioList = audioList;
            }
            
            this.renderAudioList();
        } catch (error) {
            console.error('Failed to load all audio list:', error);
            // 显示错误信息给用户
            this.audioListContainer.innerHTML = '<div class="error-message">Failed to load audio list, please refresh the page and try again</div>';
        }
    }

    /**
     * 渲染音频列表
     */
    renderAudioList() {
        this.audioListContainer.innerHTML = '';
        
        this.audioList.forEach((audio, index) => {
            const audioItem = document.createElement('div');
            audioItem.className = 'audio-item';
            
            // 根据标注完整性添加样式类
            // annotation_completeness现在总是数组格式
            if (Array.isArray(audio.annotation_completeness)) {
                const hasVA = audio.annotation_completeness.includes('va_complete');
                const hasDiscrete = audio.annotation_completeness.includes('discrete_complete');
                
                if (hasDiscrete && hasVA) {
                    // Has discrete emotion annotation - green
                    audioItem.classList.add('labeled-complete');
                } else if (hasVA && !hasDiscrete) {
                    // Only has VA annotation, no discrete emotion - red
                    audioItem.classList.add('labeled-va');
                } 
            }
            
            audioItem.innerHTML = `
                <span class="audio-name">${audio.file_name}</span>
            `;
            
            audioItem.addEventListener('click', () => {
                this.selectAudio(index);
            });
            
            this.audioListContainer.appendChild(audioItem);
        });
    }

    /**
     * 选择音频
     */
    selectAudio(index) {
        if (index < 0 || index >= this.audioList.length) {
            return;
        }
        
        this.currentAudioIndex = index;
        this.updateAudioSelection();
        
        const currentAudio = this.audioList[index];
        
        if (this.onAudioSelectCallback) {
            this.onAudioSelectCallback(currentAudio, index);
        }
        
        // Display standard answer with a delay to ensure it happens after all other DOM operations
        if (window.standardAnswerService && currentAudio) {
            setTimeout(() => {
                window.standardAnswerService.displayStandardAnswer(currentAudio.file_name);
            }, 100); // Small delay to ensure other operations complete first
        }
    }

    /**
     * 更新音频选择状态
     */
    updateAudioSelection() {
        const audioItems = this.audioListContainer.querySelectorAll('.audio-item');
        audioItems.forEach((item, index) => {
            item.classList.toggle('active', index === this.currentAudioIndex);
        });
    }

    /**
     * 设置音频选择回调
     */
    setOnAudioSelectCallback(callback) {
        this.onAudioSelectCallback = callback;
    }

    /**
     * 获取当前音频
     */
    getCurrentAudio() {
        if (this.currentAudioIndex >= 0 && this.currentAudioIndex < this.audioList.length) {
            return this.audioList[this.currentAudioIndex];
        }
        return null;
    }

    /**
     * 获取音频列表
     */
    getAudioList() {
        return this.audioList;
    }

    /**
     * Next audio
     */
    nextAudio() {
        if (this.currentAudioIndex < this.audioList.length - 1) {
            this.selectAudio(this.currentAudioIndex + 1);
        }
    }

    /**
     * Previous audio
     */
    previousAudio() {
        if (this.currentAudioIndex > 0) {
            this.selectAudio(this.currentAudioIndex - 1);
        }
    }

    /**
     * 更新音频标注状态
     * @param {number} index - 音频索引
     * @param {boolean} labeled - 是否已标注
     * @param {Array} completeness - 标注完整性数组
     */
    updateAudioLabelStatus(index, labeled, completeness = []) {
        if (index >= 0 && index < this.audioList.length) {
            this.audioList[index].labeled = labeled;
            this.audioList[index].annotation_completeness = completeness;
            
            // Store current audio file name for re-displaying standard answer
            const currentAudioFile = this.audioList[this.currentAudioIndex]?.file_name;
            
            this.renderAudioList();
            this.updateAudioSelection();
            
            // Re-display standard answer if it was showing for the current audio
            if (window.standardAnswerService && currentAudioFile && this.currentAudioIndex === index) {
                setTimeout(() => {
                    window.standardAnswerService.displayStandardAnswer(currentAudioFile);
                }, 50); // Short delay to ensure DOM updates are complete
            }
        }
    }

    /**
     * 清空音频列表
     */
    clearAudioList() {
        this.audioList = [];
        this.currentAudioIndex = -1;
        this.audioListContainer.innerHTML = '';
        this.currentSpeaker = null;
    }
}

