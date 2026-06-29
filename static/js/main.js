/**
 * 音频情感标注系统主文件（重构版）
 * 负责协调各个模块的工作
 */

class EmotionLabelingApp {
    constructor() {
        this.userManager = null;
        this.audioPlayer = null;
        this.audioListManager = null;
        this.emotionAnnotator = null;
        this.keyboardHandler = null;

        // 计时器相关属性
        this.timer = null;
        this.startTime = null;
        this.pausedTime = 0; // 累计暂停时间
        this.reminderInterval = 1; // 默认1分钟，将从API获取

        this.initApp();
    }

    async initApp() {
        // 初始化用户管理
        this.userManager = new UserManager();
        const isAuthenticated = await this.userManager.initAuth();
        if (!isAuthenticated) {
            return;
        }

        // 设置为全局变量，供其他模块使用
        window.userManager = this.userManager;

        // 获取DOM元素
        const elements = this.getDOMElements();

        //2025年9月9日,bcd：建立IndexDB数据库
        this.db = await this.initIndexedDB();
        // 初始化各个模块
        this.initModules(elements);

        // 设置事件监听
        this.setupEventListeners(elements);

        // 立即显示切换按钮（同步操作）
        this.showSwitchButton();

        console.log('Starting 5-point scale initialization with user:', this.userManager.getCurrentUsername());

        // 并行执行非关键初始化操作
        Promise.all([
            this.audioListManager.initSpeakers(),
            this.updateUserGroupInfo(elements),
            this.startTimer(elements),
            this.startRestReminder(),
            this.checkSecondConsistencyTest()
        ]).then(() => {
            console.log('5-point scale initialization completed successfully');
        }).catch(error => {
            console.error('Non-critical error during initialization:', error);
        });
    }

    getDOMElements() {
        return {
            // 主界面元素
            mainContainer: document.getElementById('main-container'),

            // 音频相关元素
            speakerSelect: document.getElementById('speaker-select'),
            audioListContainer: document.getElementById('audio-list-container'),
            audioPlayer: document.getElementById('audio-player'),
            playCountValue: document.getElementById('play-count-value'),
            playPauseButton: document.getElementById('play-pause-button'),

            // 标注相关元素
            vSlider: document.getElementById('v-slider'),
            aSlider: document.getElementById('a-slider'),
            vValue: document.getElementById('v-value'),
            aValue: document.getElementById('a-value'),

            // 情感类型元素
            neutralType: document.getElementById('neutral-type'),
            nonNeutralType: document.getElementById('non-neutral-type'),
            specificEmotions: document.getElementById('specific-emotions'),
            emotionTypeRadios: document.querySelectorAll('input[name="emotion-type"]'),

            // 患者状态和离散情感
            patientRadios: document.querySelectorAll('input[name="patient-status"]'),
            discreteEmotionRadios: document.querySelectorAll('input[name="discrete-emotion"]'),

            // 按钮元素
            saveVaButton: document.getElementById('save-va-button'),
            saveDiscreteButton: document.getElementById('save-discrete-button'),
            nextButton: document.getElementById('next-button'),
            continueButton: document.getElementById('continue-button'),
            backButton: document.getElementById('back-button'),
            prevButton: document.getElementById('prev-button'),

            // 标注模式区域
            vaLabeling: document.getElementById('va-labeling'),
            discreteLabeling: document.getElementById('discrete-labeling'),

            // 计时器相关元素
            timerSection: document.getElementById('timerSection'),
            timerValue: document.getElementById('timerValue')
        };
    }

    initModules(elements) {
        // Initialize standard answer service
        //2025年9月10日 bcd： 增加解释：调用标准答案服务
        window.standardAnswerService = new StandardAnswerService();

        // 初始化音频播放器
        this.audioPlayer = new AudioPlayer(elements.audioPlayer, elements.playCountValue);

        // 初始化音频列表管理器（5点量表版本）
        this.audioListManager = new AudioListManager(elements.speakerSelect, elements.audioListContainer, '5_point');

        // 初始化情感标注器
        this.emotionAnnotator = new EmotionAnnotator(elements);
        // 初始化键盘处理器
        this.keyboardHandler = new KeyboardHandler({
            togglePlayPause: () => this.audioPlayer.togglePlayPause(),
            previous: () => this.handlePrevious(),
            next: () => this.handleNext(),
            save: () => this.handleSaveByMode(),
            continueOrBack: () => this.handleContinueOrBack()
        });
    }

    setupEventListeners(elements) {
        // 音频选择回调
        this.audioListManager.setOnAudioSelectCallback((audioFile, index) => {
            this.handleAudioSelect(audioFile, index);
        });

        // 播放按钮事件
        if (elements.playPauseButton) {
            elements.playPauseButton.addEventListener('click', () => {
                this.audioPlayer.togglePlayPause();
            });
        }

        // 按钮事件
        elements.saveVaButton.addEventListener('click', () => this.handleSaveVa());
        elements.saveDiscreteButton.addEventListener('click', () => this.handleSaveDiscrete());
        elements.nextButton.addEventListener('click', () => this.handleNext());
        elements.continueButton.addEventListener('click', () => this.handleContinue());
        elements.backButton.addEventListener('click', () => this.handleBack());
        elements.prevButton.addEventListener('click', () => this.handlePrevious());

        // 切换量表按钮事件
        const switchTo9PointButton = document.getElementById('switch-to-9point');
        if (switchTo9PointButton) {
            switchTo9PointButton.addEventListener('click', () => this.handleSwitchTo9Point());
        }


    }

    async handleAudioSelect(audioFile, index) {
        // 检查是否有未保存的修改
        if (this.emotionAnnotator.getModified()) {
            if (!confirm('Current annotation is not saved, continue?')) {
                return;
            }
        }

        // 加载音频
        await this.loadAudioFile(audioFile, index); // 调用新的 loadAudioFile 方法
        this.keyboardHandler.resetFocus();
    }

    /**
     * 加载音频文件并处理相关逻辑
     * @param {object} audioFile - 音频文件对象
     * @param {number} index - 音频文件在列表中的索引
     */
    async loadAudioFile(audioFile, index) {
        if (!audioFile || !audioFile.path) {
            console.error('Invalid audioFile object in loadAudioFile:', audioFile);
            return;
        }
        console.log(`Loading audio file: ${audioFile.file_name}, Index: ${index}, Labeled: ${audioFile.labeled}, Path: ${audioFile.path}`);

        this.currentAudioFile = audioFile; // 使用 this.currentAudioFile
        this.currentAudioIndex = index;   // 使用 this.currentAudioIndex

        if (!this.audioPlayer) {
            console.error('audioPlayer is not initialized in loadAudioFile');
            return;
        }
        if (!this.emotionAnnotator) {
            console.error('emotionAnnotator is not initialized in loadAudioFile');
            return;
        }

        try {
            // 注意：原始的 audioPlayer.loadAudio 接受三个参数，这里只传递了路径
            // Need to confirm if audioPlayer.loadAudio implementation is compatible with path-only calls, or adjust parameters
            await this.audioPlayer.loadAudio(
                audioFile, // 传递完整的 audioFile 对象
                audioFile.speaker || this.audioListManager.currentSpeaker,
                this.userManager.getCurrentUsername()
            );
            this.emotionAnnotator.reset();
            this.emotionAnnotator.switchToVaMode(); // 确保切换到VA模式
            this.updateButtonStates(); // 更新按钮状态

            if (audioFile.labeled) {
                console.log(`File ${audioFile.file_name} is marked as labeled. Attempting to load saved label.`);
                try {

                    //2025年9月9日 
                    //bcd：
                    //注释掉这段代码，因为要将逻辑修改为从indexDB中获取标注信息，而不是从服务器中获取
                    // 
                    //修复：添加缺失的 username 参数，正确调用数据库API
                    // const labelData = await window.optimizedDataService.getLabel(
                    //     this.userManager.getCurrentUsername(),
                    //     audioFile.speaker || this.audioListManager.currentSpeaker, 
                    //     audioFile.file_name,
                    //     '5_point'
                    // ); 
                    // if (labelData && labelData.success && labelData.data) {
                    //     console.log(`Successfully received label data for ${audioFile.file_name}:`, JSON.stringify(labelData.data));

                    //     // 修复：直接使用数据库返回的数据更新UI，避免重复API调用
                    //     const label = labelData.data;

                    //     // 设置VA值
                    //     if (label.v_value !== undefined && label.v_value !== null) {
                    //         this.emotionAnnotator.elements.vSlider.value = label.v_value;
                    //     }
                    //     if (label.a_value !== undefined && label.a_value !== null) {
                    //         this.emotionAnnotator.elements.aSlider.value = label.a_value;
                    //     }
                    //     this.emotionAnnotator.updateSliderDisplay();

                    //     // 设置患者状态
                    //     if (label.patient_status) {
                    //         this.emotionAnnotator.patientStatus = label.patient_status;
                    //         const patientRadio = document.getElementById(label.patient_status === 'patient' ? 'is-patient' : 'not-patient');
                    //         if (patientRadio) patientRadio.checked = true;
                    //     }

                    //     // 设置情感类型
                    //     if (label.emotion_type) {
                    //         this.emotionAnnotator.emotionType = label.emotion_type;
                    //         const emotionRadio = document.getElementById(label.emotion_type === 'neutral' ? 'neutral-type' : 'non-neutral-type');
                    //         if (emotionRadio) emotionRadio.checked = true;

                    //         this.emotionAnnotator.handleEmotionTypeChange();

                    //         // 设置具体情感（单选）
                    //         if (this.emotionAnnotator.emotionType === 'non-neutral' && label.discrete_emotion) {
                    //             // 处理单个情感，可能是逗号分隔的字符串或数组（取第一个）
                    //             let emotion = null;
                    //             if (typeof label.discrete_emotion === 'string') {
                    //                 const emotions = label.discrete_emotion.split(',').map(e => e.trim()).filter(e => e);
                    //                 emotion = emotions[0]; // 取第一个情感
                    //             } else if (Array.isArray(label.discrete_emotion)) {
                    //                 emotion = label.discrete_emotion[0]; // 取第一个情感
                    //             } else {
                    //                 emotion = label.discrete_emotion;
                    //             }

                    //             console.log('Loading discrete emotion in main.js:', emotion);
                    //             this.emotionAnnotator.selectedDiscreteEmotions = emotion ? [emotion] : [];

                    //             // 清除所有选择
                    //             const discreteRadios = document.querySelectorAll('input[name="discrete-emotion"]');
                    //             discreteRadios.forEach(radio => radio.checked = false);

                    //             // 设置选中的情感
                    //             if (emotion) {
                    //                 const discreteRadio = document.getElementById(`emotion-${emotion}`);
                    //                 console.log(`Looking for radio in main.js: emotion-${emotion}, found:`, discreteRadio);
                    //                 if (discreteRadio) {
                    //                     discreteRadio.checked = true;
                    //                     console.log(`Set ${emotion} radio to checked in main.js`);
                    //                 } else {
                    //                     console.warn(`Radio not found for emotion in main.js: ${emotion}`);
                    //                 }
                    //             }
                    //         }
                    //     }

                    //     // 根据加载的标注数据更新保存按钮状态
                    //     this.updateSaveButtonStatus(true);
                    // } else {
                    //     console.warn(`optimizedDataService.getLabel returned no data for ${audioFile.file_name} (marked as labeled). UI remains reset.`);
                    //     this.updateSaveButtonStatus(false);
                    // }

                    console.log(audioFile.file_name);
                    const labelData = await this.getFromIndexedDB(audioFile.file_name);

                    console.log("====Attempting to load labelData from IndexedDB in main.js====");
                    console.log("labelData from IndexedDB:", labelData);
                    console.log("...And the value of labelData.success:", labelData.success);
                    console.log("...And the value of labelData.data:", labelData.data);

                    if (labelData) {
                        console.log(`Loaded label data from IndexedDB for ${audioFile.file_name}:`, labelData);

                        // 设置VA值
                        if (labelData.v_value !== undefined && labelData.v_value !== null) {
                            this.emotionAnnotator.elements.vSlider.value = labelData.v_value;
                        }
                        if (labelData.a_value !== undefined && labelData.a_value !== null) {
                            this.emotionAnnotator.elements.aSlider.value = labelData.a_value;
                        }
                        this.emotionAnnotator.updateSliderDisplay();

                        // 设置患者状态
                        //2025年9月11日 
                        //bcd：注释掉患者状态的设置
                        // if (labelData.patient_status) {
                        //     this.emotionAnnotator.patientStatus = labelData.patient_status;
                        //     const patientRadio = document.getElementById(labelData.patient_status === 'patient' ? 'is-patient' : 'not-patient');
                        //     if (patientRadio) patientRadio.checked = true;
                        // }

                        // 设置情感类型
                        if (labelData.emotion_type) {
                            this.emotionAnnotator.emotionType = labelData.emotion_type;
                            const emotionRadio = document.getElementById(labelData.emotion_type === 'neutral' ? 'neutral-type' : 'non-neutral-type');
                            if (emotionRadio) emotionRadio.checked = true;

                            this.emotionAnnotator.handleEmotionTypeChange();

                            // 设置具体情感（单选）
                            if (this.emotionAnnotator.emotionType === 'non-neutral' && labelData.discrete_emotion) {
                                const emotion = Array.isArray(labelData.discrete_emotion)
                                    ? labelData.discrete_emotion[0]
                                    : labelData.discrete_emotion;

                                this.emotionAnnotator.selectedDiscreteEmotions = emotion ? [emotion] : [];

                                // 清除所有选择
                                const discreteRadios = document.querySelectorAll('input[name="discrete-emotion"]');
                                discreteRadios.forEach(radio => (radio.checked = false));

                                // 设置选中的情感
                                if (emotion) {
                                    const discreteRadio = document.getElementById(`emotion-${emotion}`);
                                    if (discreteRadio) {
                                        discreteRadio.checked = true;
                                    }
                                }
                            }
                        }

                        // 更新保存按钮状态
                        this.updateSaveButtonStatus(true);
                    } else {
                        console.log(`No label data found in IndexedDB for ${audioFile.file_name}.`);
                        this.updateSaveButtonStatus(false);
                    }

                    this.updateSaveButtonVisibility(); // 统一更新保存按钮可见性
                } catch (error) {
                    console.error(`Error in optimizedDataService.getLabel for ${audioFile.file_name}:`, error);
                    this.updateSaveButtonStatus(false);
                }
            } else {
                console.log(`File ${audioFile.file_name} is not marked as labeled. UI remains reset. Not calling optimizedDataService.getLabel.`);
                this.updateSaveButtonStatus(false);
            }
            this.updateSaveButtonVisibility(); // 统一更新保存按钮可见性

        } catch (error) {
            console.error(`Error loading audio or processing labels for ${audioFile.file_name}:`, error);
        }

        // 更新播放次数显示，确保在音频加载和标签处理之后
        // 原始逻辑中 getPlayCount 是在 audioPlayer.loadAudio 内部调用的，这里移到外部确保顺序
        // 并且，optimizedDataService.getPlayCount 的调用移到了 audioPlayer.loadAudio 内部，这里不再重复调用

        // 更新UI元素，例如当前音频文件显示
        const currentAudioDisplay = document.getElementById('currentAudioFileDisplay');
        if (currentAudioDisplay) {
            currentAudioDisplay.textContent = audioFile.file_name;
        }
    }

    /**
     * 根据当前模式调用相应的保存方法
     */
    handleSaveByMode() {
        if (this.emotionAnnotator.isVaLabelingMode) {
            this.handleSaveVa();
        } else {
            this.handleSaveDiscrete();
        }
    }

    /**
     * 保存VA标注
     */
    async handleSaveVa() {
        const currentAudio = this.audioListManager.getCurrentAudio();
        if (!currentAudio) return;

        const annotation = this.emotionAnnotator.getCurrentAnnotation();
        //LabelData:需要保存的标签信息
        const labelData = {
            speaker: currentAudio.speaker || this.audioListManager.currentSpeaker,
            audio_file: currentAudio.file_name,
            username: this.userManager.getCurrentUsername(),
            va_scale: '5_point', // 明确标识为5点量表
            ...annotation
        };

        const saveButton = document.getElementById('save-va-button');
        saveButton.disabled = true;
        saveButton.textContent = 'Saving...';
        //2025年9月9日
        //bcd：
        // 以下代码块的功能为：保存标签信息到服务器数据库中
        // 注释的原因为：改为使用IndexedDB存储到本地浏览器
        //
        // try {
        //     // 立即更新UI状态，提供即时反馈
        //     const completeness = this.emotionAnnotator.getAnnotationCompleteness();
        //     this.audioListManager.updateAudioLabelStatus(
        //         this.audioListManager.currentAudioIndex, 
        //         true, 
        //         completeness
        //     );
        //     this.emotionAnnotator.setModified(false);
        //     this.updateSaveButtonStatus(true);

        //     // 异步保存，不阻塞UI
        //     const result = await window.optimizedDataService.saveLabel(labelData);
        //     if (result.success) {
        //         // Save successful, execute subsequent checks asynchronously
        //         this.performPostSaveChecks();
        //     } else {
        //         throw new Error(result.error || 'Save failed');
        //     }
        // } catch (error) {
        //     console.error('Save VA annotation failed:', error);
        //     alert('Save VA annotation failed, please try again');
        //     saveButton.textContent = 'Save VA(W)';
        //     saveButton.disabled = false;
        // }

        // this.keyboardHandler.resetFocus();

        //2025年9月9日
        //bcd：保存annotation到IndexedDB中的annotationLabel表中
        try {
            //更新audioListManager中的音频标注状态
            this.audioListManager.updateAudioLabelStatus(
                this.audioListManager.currentAudioIndex,
                true,
                this.emotionAnnotator.getAnnotationCompleteness()
            );
            //更新修改状态
            this.emotionAnnotator.setModified(false);
            await this.saveToIndexedDB(labelData);
            console.log('Label saved to IndexedDB:', labelData);
            //更新前端保存按钮状态
            this.updateSaveButtonStatus(true);
        } catch (error) {
            console.error('Failed to save label to IndexedDB:', error);
            alert('Save VA annotation failed, please try again');
            saveButton.textContent = 'Save VA(W)';
            saveButton.disabled = false;
        }

    }

    /**
     * 执行保存后的检查（异步）
     */
    async performPostSaveChecks() {
        try {
            // 并行执行检查，减少总时间
            await Promise.allSettled([
                this.checkSecondConsistencyTest(),
                this.checkCompletionAndRedirect()
            ]);
        } catch (error) {
            console.error('Post-save check failed:', error);
        }
    }

    /**
     * 保存离散情感标注
     */
    async handleSaveDiscrete() {
        const currentAudio = this.audioListManager.getCurrentAudio();
        if (!currentAudio) return;

        const annotation = this.emotionAnnotator.getCurrentAnnotation();
        const labelData = {
            speaker: currentAudio.speaker || this.audioListManager.currentSpeaker,
            audio_file: currentAudio.file_name,
            username: this.userManager.getCurrentUsername(),
            va_scale: '5_point', // 明确标识为5点量表
            ...annotation
        };

        const saveButton = document.getElementById('save-discrete-button');
        saveButton.disabled = true;
        saveButton.textContent = 'Saving...';
        //2025年9月9日
        //bcd：
        // 以下代码块的功能为：保存标签信息到服务器数据库中
        // 注释的原因为：改为使用IndexedDB存储到本地浏览器
        //
        // try {
        //     // 立即更新UI状态，提供即时反馈
        //     const completeness = this.emotionAnnotator.getAnnotationCompleteness();
        //     this.audioListManager.updateAudioLabelStatus(
        //         this.audioListManager.currentAudioIndex, 
        //         true, 
        //         completeness
        //     );
        //     this.emotionAnnotator.setModified(false);
        //     this.updateSaveButtonStatus(true);

        //     // 异步保存，不阻塞UI
        //     const result = await window.optimizedDataService.saveLabel(labelData);
        //     if (result.success) {
        //         // Save successful, execute subsequent checks asynchronously
        //         this.performPostSaveChecks();
        //     } else {
        //         throw new Error(result.error || 'Save failed');
        //     }
        // } catch (error) {
        //     console.error('Save discrete emotion annotation failed:', error);
        //     alert('Save discrete emotion annotation failed, please try again');
        //     saveButton.textContent = 'Save Discrete(W)';
        //     saveButton.disabled = false;
        // }

        // this.keyboardHandler.resetFocus();
        try {
            // 保存到 IndexedDB
            const completeness = this.emotionAnnotator.getAnnotationCompleteness();
            this.audioListManager.updateAudioLabelStatus(
                 this.audioListManager.currentAudioIndex, 
                 true, 
                 completeness
             );
              this.emotionAnnotator.setModified(false);
               this.updateSaveButtonStatus(true);
            await this.saveToIndexedDB(labelData);

            console.log('Label saved to IndexedDB:', labelData);
            this.updateSaveButtonStatus(true);
        } catch (error) {
            console.error('Failed to save label to IndexedDB:', error);
            alert('Save discrete emotion annotation failed, please try again');
            saveButton.textContent = 'Save Discrete(W)';
            saveButton.disabled = false;
        }
    }

    handleNext() {
        if (this.emotionAnnotator.getModified()) {
            if (!confirm('Current annotation is not saved, continue?')) {
                return;
            }
        }

        // 获取当前音频的已保存标注状态，而不是界面当前状态
        const currentAudio = this.audioListManager.getCurrentAudio();
        if (currentAudio && currentAudio.labeled && Array.isArray(currentAudio.annotation_completeness)) {
            const hasDiscrete = currentAudio.annotation_completeness.includes('discrete_complete');
            const hasVA = currentAudio.annotation_completeness.includes('va_complete');

            // 如果离散情感完整，或者VA都完整，则可以继续
            if (hasDiscrete || hasVA) {
                this.audioListManager.nextAudio();
            } else {
                alert('Please complete the annotation for the current audio before continuing');
            }
        } else {
            // 如果没有保存的标注，检查当前界面状态
            const completeness = this.emotionAnnotator.getAnnotationCompleteness();
            const hasDiscrete = completeness.includes('discrete_complete');
            const hasVA = completeness.includes('va_complete');

            if (hasDiscrete || hasVA) {
                this.audioListManager.nextAudio();
            } else {
                alert('Please complete the annotation for the current audio before continuing');
            }
        }
        this.keyboardHandler.resetFocus();
    }

    handlePrevious() {
        if (this.emotionAnnotator.getModified()) {
            if (!confirm('Current annotation is not saved, continue?')) {
                return;
            }
        }

        this.audioListManager.previousAudio();
        this.keyboardHandler.resetFocus();
    }

    handleContinue() {
        if (this.emotionAnnotator.getModified() && this.emotionAnnotator.isVaLabelingMode) {
            if (!confirm('VA annotation has been modified but not saved, continue? You can save first, then continue')) {
                return;
            }
        }

        this.emotionAnnotator.switchToDiscreteMode();
        this.updateSaveButtonVisibility();
        this.keyboardHandler.resetFocus();
    }

    handleBack() {
        if (this.emotionAnnotator.getModified() && !this.emotionAnnotator.isVaLabelingMode) {
            if (!confirm('Discrete emotion annotation not saved, return to VA annotation?')) {
                return;
            }
        }

        this.emotionAnnotator.switchToVaMode();
        this.updateSaveButtonVisibility();
        this.keyboardHandler.resetFocus();
    }

    handleContinueOrBack() {
        if (this.emotionAnnotator.isVaLabelingMode) {
            this.handleContinue();
        } else {
            this.handleBack();
        }
    }

    updateButtonStates() {
        const audioList = this.audioListManager.getAudioList();
        const currentIndex = this.audioListManager.currentAudioIndex;

        document.getElementById('prev-button').disabled = currentIndex <= 0;
        document.getElementById('next-button').disabled = currentIndex >= audioList.length - 1;
        document.getElementById('continue-button').disabled = false;
        document.getElementById('save-va-button').disabled = false;
        document.getElementById('save-discrete-button').disabled = false;
    }

    /**
     * 更新保存按钮状态
     * @param {boolean} isSaved - 是否已保存
     */
    updateSaveButtonStatus(isSaved = false) {
        const saveVaButton = document.getElementById('save-va-button');
        const saveDiscreteButton = document.getElementById('save-discrete-button');

        // 清除所有状态类
        saveVaButton.classList.remove('saved');
        saveDiscreteButton.classList.remove('saved');

        if (isSaved) {
            const completeness = this.emotionAnnotator.getAnnotationCompleteness();

            // completeness现在总是返回数组
            if (completeness.includes('none')) {
                // 未标注
                saveVaButton.textContent = 'Save VA(W)';
                saveVaButton.disabled = false;
                saveDiscreteButton.textContent = 'Save Discrete(W)';
                saveDiscreteButton.disabled = false;
            } else {
                // 数组格式的完整性状态
                const hasVA = completeness.includes('va_complete');
                const hasDiscrete = completeness.includes('discrete_complete');

                // 更新VA保存按钮状态
                if (hasVA) {
                    saveVaButton.textContent = 'VA Saved(W)';
                    saveVaButton.classList.add('saved');
                } else {
                    saveVaButton.textContent = 'Save VA(W)';
                }
                saveVaButton.disabled = false;

                // 更新离散情感保存按钮状态
                if (hasDiscrete) {
                    saveDiscreteButton.textContent = 'Discrete Saved(W)';
                    saveDiscreteButton.classList.add('saved');
                } else {
                    saveDiscreteButton.textContent = 'Save Discrete(W)';
                }
                saveDiscreteButton.disabled = false;
            }
        } else {
            // 未保存状态
            saveVaButton.textContent = 'Save VA(W)';
            saveVaButton.disabled = false;
            saveDiscreteButton.textContent = 'Save Discrete(W)';
            saveDiscreteButton.disabled = false;
        }

        // 根据当前模式显示/隐藏相应的保存按钮
        this.updateSaveButtonVisibility();
    }

    /**
     * 根据当前标注模式更新保存按钮的可见性
     */
    updateSaveButtonVisibility() {
        const saveVaButton = document.getElementById('save-va-button');
        const saveDiscreteButton = document.getElementById('save-discrete-button');

        if (this.emotionAnnotator.isVaLabelingMode) {
            // VA标注模式：显示VA保存按钮，隐藏离散情感保存按钮
            saveVaButton.style.display = 'inline-block';
            saveDiscreteButton.style.display = 'none';
        } else {
            // 离散情感标注模式：隐藏VA保存按钮，显示离散情感保存按钮
            saveVaButton.style.display = 'none';
            saveDiscreteButton.style.display = 'inline-block';
        }
    }

    /**
     * 启动计时器
     */
    async startTimer(elements) {
        try {
            // 获取休息提醒间隔配置
            await this.startRestReminder();

            // 显示计时器区域
            elements.timerSection.style.display = 'block';

            // 记录开始时间
            this.startTime = Date.now();

            // 启动计时器更新
            this.timer = setInterval(() => {
                this.updateTimer(elements);
            }, 1000);

            console.log('计时器已启动');
        } catch (error) {
            console.error('Failed to start timer:', error);
        }
    }

    /**
     * 更新计时器显示
     */
    updateTimer(elements) {
        if (!this.startTime) return;

        // 计算总的运行时间：当前时间段 + 之前累计的暂停时间
        const currentElapsed = Date.now() - this.startTime;
        const totalElapsed = currentElapsed + this.pausedTime;
        const minutes = Math.floor(totalElapsed / 60000);
        const seconds = Math.floor((totalElapsed % 60000) / 1000);

        const timeString = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        elements.timerValue.textContent = timeString;

        // 检查是否需要显示休息提醒
        this.checkRestReminder();
    }

    /**
     * 重置计时器
     */
    resetTimer(elements) {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
        this.startTime = null;
        this.pausedTime = 0;
        if (elements && elements.timerValue) {
            elements.timerValue.textContent = '00:00';
        }
    }

    /**
     * 停止计时器
     */
    stopTimer() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }

    /**
     * 暂停计时器
     */
    pauseTimer() {
        if (this.timer && this.startTime) {
            // 累计当前时间段到pausedTime
            this.pausedTime += Date.now() - this.startTime;
            clearInterval(this.timer);
            this.timer = null;
            this.startTime = null; // 清空startTime表示暂停状态
            console.log('计时器已暂停，累计时间:', this.pausedTime);
        }
    }

    /**
     * 恢复计时器
     */
    resumeTimer() {
        if (!this.timer && this.pausedTime >= 0) {
            // 重新设置开始时间为当前时间
            this.startTime = Date.now();

            const elements = this.getDOMElements();
            this.timer = setInterval(() => {
                this.updateTimer(elements);
            }, 1000);
            console.log('计时器已恢复，累计时间:', this.pausedTime);
        }
    }

    /**
     * 启动休息提醒
     */
    async startRestReminder() {
        try {
            const response = await fetch('/api/config/rest-reminder-interval');
            if (response.ok) {
                const data = await response.json();
                this.reminderInterval = data.interval_minutes || 1;
            }
        } catch (error) {
            console.error('Failed to get rest reminder interval:', error);
            this.reminderInterval = 1; // 使用默认值
        }

        console.log('休息提醒间隔设置为:', this.reminderInterval, '分钟');
    }

    /**
     * 检查是否需要显示休息提醒
     */
    checkRestReminder() {
        if (!this.startTime) return; // 计时器未运行时不检查

        const currentElapsed = Date.now() - this.startTime;
        const totalElapsed = currentElapsed + this.pausedTime;
        const totalMinutes = Math.floor(totalElapsed / 60000);

        // 每达到提醒间隔就显示提醒
        if (totalMinutes > 0 && totalMinutes % this.reminderInterval === 0) {
            // 避免重复提醒，检查是否刚好到达整分钟
            const seconds = Math.floor((totalElapsed % 60000) / 1000);
            if (seconds === 0) {
                this.showRestReminder();
            }
        }
    }

    /**
     * 显示休息提醒弹窗
     */
    showRestReminder() {
        // 计算当前总时间
        const currentElapsed = this.startTime ? Date.now() - this.startTime : 0;
        const totalElapsed = currentElapsed + this.pausedTime;
        const totalMinutes = Math.floor(totalElapsed / 60000);

        // 暂停计时器
        this.pauseTimer();

        // 创建弹窗HTML
        const popupHtml = `
            <div id="restReminderPopup" style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10000;
            ">
                <div style="
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                    max-width: 400px;
                    width: 90%;
                ">
                    <h3 style="color: #007bff; margin-bottom: 15px;">💡 休息提醒</h3>
                    <p style="margin-bottom: 20px; line-height: 1.6;">您已经连续测试了 ${totalMinutes} 分钟，建议您稍作休息，保护听力健康。</p>
                    <button id="closeRestReminder" style="
                        background-color: #007bff;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 16px;
                    ">我知道了</button>
                </div>
            </div>
        `;

        // 添加弹窗到页面
        document.body.insertAdjacentHTML('beforeend', popupHtml);

        // 添加关闭事件
        document.getElementById('closeRestReminder').addEventListener('click', () => {
            document.getElementById('restReminderPopup').remove();

            // 恢复计时器
            this.resumeTimer();

            console.log('休息提醒关闭，计时器已恢复');
        });

        console.log('显示休息提醒，当前总时间:', totalMinutes, '分钟，计时器已暂停');
    }

    /**
     * 检查是否需要进行第二次一致性测试
     */
    async checkSecondConsistencyTest() {
        try {
            const username = this.userManager.getCurrentUsername();
            const response = await fetch(`/api/check-second-consistency-test/${username}`);
            const result = await response.json();

            if (result.success && result.data.needs_second_test) {
                // 显示提示弹窗
                this.showSecondConsistencyTestPrompt(result.data.annotated_count);
            }
        } catch (error) {
            console.error('Failed to check second consistency test:', error);
        }
    }

    /**
     * 显示第二次一致性测试提示弹窗
     */
    showSecondConsistencyTestPrompt(annotatedCount) {
        // 暂停计时器
        this.pauseTimer();

        const popupHtml = `
            <div id="secondConsistencyTestPopup" style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10000;
            ">
                <div style="
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                    max-width: 500px;
                    width: 90%;
                ">
                    <h3 style="color: #007bff; margin-bottom: 15px;">🎯 第二次一致性测试</h3>
                    <p style="margin-bottom: 20px; line-height: 1.6;">
                        恭喜您！您已经完成了 ${annotatedCount} 个音频的标注。<br>
                        现在需要进行第二次一致性测试来验证标注质量。
                    </p>
                    <div style="display: flex; gap: 15px; justify-content: center;">
                        <button id="startSecondTest" style="
                            background-color: #007bff;
                            color: white;
                            border: none;
                            padding: 12px 24px;
                            border-radius: 5px;
                            cursor: pointer;
                            font-size: 16px;
                        ">开始测试</button>
                        <button id="laterSecondTest" style="
                            background-color: #6c757d;
                            color: white;
                            border: none;
                            padding: 12px 24px;
                            border-radius: 5px;
                            cursor: pointer;
                            font-size: 16px;
                        ">稍后进行</button>
                    </div>
                </div>
            </div>
        `;

        // 添加弹窗到页面
        document.body.insertAdjacentHTML('beforeend', popupHtml);

        // 添加事件监听
        document.getElementById('startSecondTest').addEventListener('click', () => {
            document.getElementById('secondConsistencyTestPopup').remove();
            // 跳转到一致性测试页面，并标记为第二次测试
            window.location.href = `/consistency-test?username=${this.userManager.getCurrentUsername()}&second_test=true`;
        });

        document.getElementById('laterSecondTest').addEventListener('click', () => {
            document.getElementById('secondConsistencyTestPopup').remove();
            // 恢复计时器
            this.resumeTimer();
        });
    }

    /**
     * 更新用户分组信息显示
     */
    async updateUserGroupInfo(elements) {
        try {
            const username = this.userManager.getCurrentUsername();
            const response = await window.optimizedDataService.getUserGroupInfo(username);

            // 注释掉分组信息显示，但保留获取分组信息的逻辑供其他功能使用
            // const groupInfoElement = document.getElementById('group-info');
            if (response.success && response.assignment && response.assignment.group_id) {
                // const groupId = response.assignment.group_id;
                // groupInfoElement.textContent = `分组: 第${groupId}组`;
                // groupInfoElement.style.color = '#28a745'; // 绿色表示已分配

                // 存储用户分组信息供其他模块使用
                window.userGroupInfo = response.assignment;
            } else {
                // groupInfoElement.textContent = '未分配分组，请联系管理员';
                // groupInfoElement.style.color = '#dc3545'; // 红色表示未分配

                // 清除分组信息
                window.userGroupInfo = null;
            }
        } catch (error) {
            console.error('Failed to get user group information:', error);
            // const groupInfoElement = document.getElementById('group-info');
            // groupInfoElement.textContent = '分组信息获取失败';
            // groupInfoElement.style.color = '#ffc107'; // 黄色表示错误

            // 清除分组信息
            window.userGroupInfo = null;
        }
    }

    /**
     * 检查是否完成了所有标注，如果完成则跳转到另一个量表
     */
    async checkCompletionAndRedirect() {
        try {
            const username = this.userManager.getCurrentUsername();
            const response = await fetch(`/api/check-completion-status/${username}`);
            const result = await response.json();

            if (result.success && result.data.all_completed) {
                // 显示完成提示弹窗
                this.showCompletionPrompt(result.data);
            }
        } catch (error) {
            console.error('Failed to check completion status:', error);
        }
    }

    /**
     * 显示完成提示弹窗
     */
    showCompletionPrompt(data) {
        // 暂停计时器
        this.pauseTimer();

        const popupHtml = `
            <div id="completionPromptPopup" style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10000;
            ">
                <div style="
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                    max-width: 500px;
                    width: 90%;
                ">
                    <h3 style="color: #28a745; margin-bottom: 15px;">🎉 恭喜完成！</h3>
                    <p style="margin-bottom: 20px; line-height: 1.6;">
                        您已经完成了当前量表的所有标注任务！<br>
                        现在可以继续进行另一个量表的标注。
                    </p>
                    <div style="display: flex; gap: 15px; justify-content: center;">
                        <button id="continueToOtherScale" style="
                            background-color: #28a745;
                            color: white;
                            border: none;
                            padding: 12px 24px;
                            border-radius: 5px;
                            cursor: pointer;
                            font-size: 16px;
                        ">继续标注</button>
                        <button id="stayCurrentScale" style="
                            background-color: #6c757d;
                            color: white;
                            border: none;
                            padding: 12px 24px;
                            border-radius: 5px;
                            cursor: pointer;
                            font-size: 16px;
                        ">稍后进行</button>
                    </div>
                </div>
            </div>
        `;

        // 添加弹窗到页面
        document.body.insertAdjacentHTML('beforeend', popupHtml);

        // 添加事件监听
        document.getElementById('continueToOtherScale').addEventListener('click', () => {
            document.getElementById('completionPromptPopup').remove();
            // 跳转到另一个量表
            const currentScale = data.current_scale || '5_point';
            if (currentScale === '5_point') {
                // 当前是5点量表，跳转到9点量表
                window.location.href = '/9point';
            } else {
                // 当前是9点量表，跳转到5点量表
                window.location.href = '/5point';
            }
        });

        document.getElementById('stayCurrentScale').addEventListener('click', () => {
            document.getElementById('completionPromptPopup').remove();
            // 恢复计时器
            this.resumeTimer();
        });
    }

    /**
     * 显示切换量表按钮（同步操作）
     */
    showSwitchButton() {
        const switchButton = document.getElementById('switch-to-9point');
        if (switchButton) {
            switchButton.classList.remove('switch-button-hidden');
            switchButton.classList.add('switch-button-visible');
        }
    }

    /**
     * 检查并控制切换量表按钮的显示
     * 修改为手动切换模式，按钮始终可见
     */
    async checkAndControlSwitchButton() {
        try {
            const switchButton = document.getElementById('switch-to-9point');
            console.log('切换按钮元素:', switchButton);

            if (switchButton) {
                // 手动切换模式：按钮始终可见
                console.log('手动切换模式 - 显示切换按钮');
                switchButton.classList.remove('switch-button-hidden');
                switchButton.classList.add('switch-button-visible');
                console.log('按钮类名:', switchButton.className);
            } else {
                console.error('未找到切换按钮元素');
            }
        } catch (error) {
            console.error('Failed to check switch button display conditions:', error);
            // 出错时也显示按钮
            const switchButton = document.getElementById('switch-to-9point');
            if (switchButton) {
                switchButton.classList.remove('switch-button-hidden');
                switchButton.classList.add('switch-button-visible');
            }
        }
    }

    /**
     * 处理切换到9点量表
     */
    handleSwitchTo9Point() {
        // 检查是否有未保存的修改
        if (this.emotionAnnotator && this.emotionAnnotator.getModified()) {
            if (!confirm('当前标注未保存，是否继续切换？')) {
                return;
            }
        }

        console.log('Switching from 5-point to 9-point scale');

        // 清理资源
        this.cleanupBeforeSwitch();

        // 添加小延迟确保清理完成
        setTimeout(() => {
            // 直接跳转到9点量表
            window.location.href = '/9point';
        }, 100);
    }

    /**
     * 切换前清理资源
     */
    cleanupBeforeSwitch() {
        // 停止计时器
        if (this.stopTimer) {
            this.stopTimer();
        }

        // 停止音频播放
        if (this.audioPlayer && this.audioPlayer.pause) {
            this.audioPlayer.pause();
        }

        // 清理缓存（特别是音频列表相关的缓存）
        if (window.cacheManager) {
            window.cacheManager.clear();
        }

        // 清理保存优化器
        if (window.saveOptimizer) {
            window.saveOptimizer.clearQueue();
        }

        // 清理加载管理器
        if (window.loadingManager) {
            window.loadingManager.clearAllLoading();
        }

        // 清理用户相关缓存（特别清理va_scale相关的缓存）
        if (window.optimizedDataService && this.userManager) {
            window.optimizedDataService.clearUserCache(this.userManager.getCurrentUsername());
            // 根据内存建议，清理特定va_scale参数的缓存
            if (window.cacheManager) {
                window.cacheManager.clearPattern('va_scale=5_point');
            }
        }
    }
    //2025年9月9日 bcd：初始化IndexedDB
    async initIndexedDB() {
        return new Promise((resolve, reject) => {
            // 数据库名称为 annotationLabel，版本号为 1
            const request = indexedDB.open('annotationLabel', 1);

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                if (!db.objectStoreNames.contains('annotations')) {
                    const objectStore = db.createObjectStore('annotations', { keyPath: 'audio_file' });
                    objectStore.createIndex('v_value', 'v_value', { unique: false });
                    objectStore.createIndex('a_value', 'a_value', { unique: false });
                    objectStore.createIndex('emotion_type', 'emotion_type', { unique: false });
                    objectStore.createIndex('discrete_emotion', 'discrete_emotion', { unique: false });
                    objectStore.createIndex('username', 'username', { unique: false });
                    objectStore.createIndex('patient_status', 'patient_status', { unique: false });
                    objectStore.createIndex('audio_duration', 'audio_duration', { unique: false });
                    objectStore.createIndex('timestamp', 'timestamp', { unique: false });
                }
            };

            request.onsuccess = (event) => {
                console.log('IndexedDB initialized');
                resolve(event.target.result);
            };

            request.onerror = (event) => {
                console.error('Failed to initialize IndexedDB:', event.target.error);
                reject(event.target.error);
            };
        });
    }
    //2025年9月9日
    // bcd：保存标签数据到IndexedDB
    async saveToIndexedDB(data) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['annotations'], 'readwrite');
            const store = transaction.objectStore('annotations');

            // 检查是否存在相同主键的记录
            const getRequest = store.get(data.audio_file);

            getRequest.onsuccess = () => {
                if (getRequest.result) {
                    // 如果存在，更新记录
                    const updateRequest = store.put(data);
                    updateRequest.onsuccess = () => resolve();
                    updateRequest.onerror = (event) => reject(event.target.error);
                } else {
                    // 如果不存在，添加新记录
                    const addRequest = store.add(data);
                    addRequest.onsuccess = () => resolve();
                    addRequest.onerror = (event) => reject(event.target.error);
                }
            };

            getRequest.onerror = (event) => reject(event.target.error);
        });
    }

    //2025年9月9日
    // bcd：从IndexedDB获取标签数据
    async getFromIndexedDB(id) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['annotations'], 'readonly');
            const store = transaction.objectStore('annotations');
            const request = store.get(id);

            request.onsuccess = (event) => resolve(event.target.result);
            request.onerror = (event) => reject(event.target.error);
        });
    }
}

// 当DOM加载完成时初始化应用
document.addEventListener('DOMContentLoaded', () => {
    const app = new EmotionLabelingApp();

    // 页面卸载时停止计时器
    window.addEventListener('beforeunload', () => {
        if (app.stopTimer) {
            app.stopTimer();
        }
    });

    // 页面可见性变化时处理计时器
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            // 页面隐藏时暂停计时器
            if (app.pauseTimer) {
                app.pauseTimer();
            }
        } else {
            // 页面重新可见时恢复计时器
            if (app.resumeTimer) {
                app.resumeTimer();
            }
        }
    });
});