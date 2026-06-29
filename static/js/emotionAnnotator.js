/**
 * 情感标注模块
 * Responsible for VA value annotation and discrete emotion annotation
 */
class EmotionAnnotator {
    constructor(elements) {
        this.elements = elements;
        this.isModified = false;
        this.isVaLabelingMode = true;
        this.emotionType = 'neutral';
        this.selectedDiscreteEmotions = [];
        this.patientStatus = 'patient';
        this.vaScale = '5_point'; // 标识为5点量表
        
        this.initElements();
        this.initEventListeners();
    }

    initElements() {
        // 初始化滑动条默认值
        this.elements.vSlider.min = -2;
        this.elements.vSlider.max = 2;
        this.elements.vSlider.step = 0.5;
        // 不设置默认值，让用户主动选择

        this.elements.aSlider.min = 1;
        this.elements.aSlider.max = 5;
        this.elements.aSlider.step = 0.5;
        // 不设置默认值，让用户主动选择

        // 更新显示值
        this.updateSliderDisplay();
    }

    initEventListeners() {
        // VA滑动条事件
        this.elements.vSlider.addEventListener('input', (e) => this.handleSliderChange(e));
        this.elements.aSlider.addEventListener('input', (e) => this.handleSliderChange(e));
        
        // 患者状态事件
        this.elements.patientRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                this.patientStatus = radio.value;
                this.setModified(true);
            });
        });
        
        // 情感类型事件
        this.elements.emotionTypeRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                this.emotionType = radio.value;
                this.handleEmotionTypeChange();
                this.setModified(true);
            });
        });
        
        // Discrete emotion events (now radio buttons)
        this.elements.discreteEmotionRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                if (radio.checked) {
                    // 单选：只保留当前选中的情感
                    this.selectedDiscreteEmotions = [radio.value];
                }
                this.setModified(true);
            });
        });
    }

    /**
     * 处理滑动条变化
     */
    handleSliderChange(event) {
        const slider = event.target;
        const valueElement = slider.id === 'v-slider' ? this.elements.vValue : this.elements.aValue;
        valueElement.textContent = Number(slider.value).toFixed(2);
        this.setModified(true);
    }

    /**
     * 更新滑动条显示
     */
    updateSliderDisplay() {
        this.elements.vValue.textContent = Number(this.elements.vSlider.value).toFixed(2);
        this.elements.aValue.textContent = Number(this.elements.aSlider.value).toFixed(2);
    }

    /**
     * 处理情感类型变化
     */
    handleEmotionTypeChange() {
        if (this.emotionType === 'non-neutral') {
            this.elements.specificEmotions.style.display = 'block';
        } else {
            this.elements.specificEmotions.style.display = 'none';
            this.selectedDiscreteEmotions = [];
            // 清除所有具体情感的选择
            this.elements.discreteEmotionRadios.forEach(radio => {
                radio.checked = false;
            });
        }
    }

    /**
     * 切换到VA标注模式
     */
    switchToVaMode() {
        this.isVaLabelingMode = true;
        this.elements.vaLabeling.style.display = 'block';
        this.elements.discreteLabeling.style.display = 'none';
        this.elements.continueButton.style.display = 'inline-block';
        this.elements.backButton.style.display = 'none';
    }

    /**
     * Switch to discrete emotion annotation mode
     */
    switchToDiscreteMode() {
        this.isVaLabelingMode = false;
        this.elements.vaLabeling.style.display = 'none';
        this.elements.discreteLabeling.style.display = 'block';
        this.elements.continueButton.style.display = 'none';
        this.elements.backButton.style.display = 'inline-block';
        this.setModified(false);
    }

    /**
     * 加载已保存的标注数据
     */
    loadSavedLabel(username, speaker, filename) {
        return window.optimizedDataService.getLabel(username, speaker, filename, '5_point')
            .then(data => {
                if (data.success && data.data) {
                    const label = data.data;
                    
                    // 只加载5点量表的数据
                    if (label.va_scale && label.va_scale !== '5_point') {
                        // 如果是9点量表的数据，不加载，保持空白状态
                        this.reset();
                        return null;
                    }
                    
                    // 设置VA值
                    if (label.v_value !== undefined && label.v_value !== null) {
                        this.elements.vSlider.value = label.v_value;
                    } else {
                        this.elements.vSlider.value = ''; // 或者设置为一个合适的默认值，例如0
                    }
                    if (label.a_value !== undefined && label.a_value !== null) {
                        this.elements.aSlider.value = label.a_value;
                    } else {
                        this.elements.aSlider.value = ''; // 或者设置为一个合适的默认值，例如3
                    }
                    this.updateSliderDisplay();
                    
                    //2025年9月12日
                    //bcd：注释掉患者状态的加载，因为无需此功能
                    //因为前端界面删除了患者选择的按钮，所以使用dom获取元素会报错，必须清理相关代码
                    // 设置患者状态
                    // if (label.patient_status && label.patient_status !== null) {
                    //     this.patientStatus = label.patient_status;
                    //     const patientRadio = document.getElementById(label.patient_status === 'patient' ? 'is-patient' : 'not-patient');
                    //     if (patientRadio) patientRadio.checked = true;
                    // } else {
                    //     this.patientStatus = null; // 或者设置为默认值 'patient'
                    //     // 清除所有患者状态选择或设置默认选中
                    //     const patientRadios = document.querySelectorAll('input[name="patient-status"]');
                    //     patientRadios.forEach(radio => radio.checked = false);
                    //     // document.getElementById('is-patient').checked = true; // 可选：默认选中患者
                    // }
                    
                    // 设置情感类型
                    if (label.emotion_type && label.emotion_type !== null) {
                        this.emotionType = label.emotion_type;
                        const emotionRadio = document.getElementById(label.emotion_type === 'neutral' ? 'neutral-type' : 'non-neutral-type');
                        if (emotionRadio) emotionRadio.checked = true;
                        
                        this.handleEmotionTypeChange(); // 确保在设置具体情感之前调用
                        
                        // 设置具体情感（单选）
                        if (this.emotionType === 'non-neutral' && label.discrete_emotion && label.discrete_emotion !== null) {
                            // 处理单个情感，可能是逗号分隔的字符串或数组（取第一个）
                            let emotion = null;
                            if (typeof label.discrete_emotion === 'string') {
                                const emotions = label.discrete_emotion.split(',').map(e => e.trim()).filter(e => e);
                                emotion = emotions[0]; // 取第一个情感
                            } else if (Array.isArray(label.discrete_emotion)) {
                                emotion = label.discrete_emotion[0]; // 取第一个情感
                            } else {
                                emotion = label.discrete_emotion;
                            }
                            
                            console.log('Loading discrete emotion:', emotion); // 调试日志
                            this.selectedDiscreteEmotions = emotion ? [emotion] : [];
                            // 清除所有选择
                            const discreteRadios = document.querySelectorAll('input[name="discrete-emotion"]');
                            discreteRadios.forEach(radio => radio.checked = false);
                            // 设置选中的情感
                            if (emotion) {
                                const discreteRadio = document.getElementById(`emotion-${emotion}`);
                                console.log(`Looking for radio: emotion-${emotion}, found:`, discreteRadio); // 调试日志
                                if (discreteRadio) {
                                    discreteRadio.checked = true;
                                    console.log(`Set ${emotion} radio to checked`); // 调试日志
                                } else {
                                    console.warn(`Radio not found for emotion: ${emotion}`); // 警告日志
                                }
                            }
                        } else {
                            this.selectedDiscreteEmotions = [];
                             // 如果是中性，清除具体情感选择
                            if (this.emotionType === 'neutral') {
                                const discreteRadios = document.querySelectorAll('input[name="discrete-emotion"]');
                                discreteRadios.forEach(radio => radio.checked = false);
                            }
                        }
                    } else {
                        this.emotionType = 'neutral'; // 或者设置为默认值 'neutral'
                        this.selectedDiscreteEmotions = [];
                        // 清除所有情感类型选择或设置默认选中
                        const emotionRadios = document.querySelectorAll('input[name="emotion-type"]');
                        emotionRadios.forEach(radio => radio.checked = false);
                        document.getElementById('neutral-type').checked = true; // 可选：默认选中中性
                        this.handleEmotionTypeChange(); // 更新UI
                    }
                    
                    this.setModified(false);
                    console.log('Loaded label:', label); // 添加日志，确认加载的数据
                    return label;
                }
            });
    }

    /**
     * 获取当前标注数据
     */
    getCurrentAnnotation() {
        // 单选：只取第一个情感（如果有的话）
        const discreteEmotionStr = this.emotionType === 'neutral' ? null : 
            (this.selectedDiscreteEmotions.length > 0 ? this.selectedDiscreteEmotions[0] : null);
        
        return {
            v_value: this.elements.vSlider.value === '' ? null : parseFloat(this.elements.vSlider.value),
            a_value: this.elements.aSlider.value === '' ? null : parseFloat(this.elements.aSlider.value),
            emotion_type: this.emotionType,
            discrete_emotion: discreteEmotionStr,
            patient_status: this.patientStatus,
            va_scale: this.vaScale // 添加量表类型标识
        };
    }

    /**
     * 判断标注完整性
     * 返回格式与后端calculate_annotation_completeness保持一致
     */
    getAnnotationCompleteness() {
        // 检查用户是否实际设置了值（不为空字符串）
        const hasV = this.elements.vSlider.value !== '' && this.elements.vSlider.value !== null;
        const hasA = this.elements.aSlider.value !== '' && this.elements.aSlider.value !== null;
        const hasPatientStatus = this.patientStatus !== null;
        
        const hasEmotionType = this.emotionType !== null;
        const hasDiscreteEmotion = this.emotionType === 'neutral' || (this.emotionType === 'non-neutral' && this.selectedDiscreteEmotions.length > 0);
        
        // 检查离散情感标注是否完整
        const discreteComplete = hasPatientStatus && hasEmotionType && hasDiscreteEmotion;
        
        // 构建结果数组 - 始终检查所有标注类型的完整性，不受当前模式影响
        const result = [];
        // VA标注完整性：V和A都有值时才算完整
        if (hasV && hasA) result.push('va_complete');
        if (discreteComplete) result.push('discrete_complete');
        
        // 如果什么都没有标注，返回['none']
        if (result.length === 0) {
            return ['none'];
        }
        
        return result;
    }

    /**
     * 重置标注
     */
    reset() {
        // 清空滑块值，不设置默认值
        this.elements.vSlider.value = '';
        this.elements.aSlider.value = '';
        this.updateSliderDisplay();
                //2025年9月12日
        //bcd：清理是否患者的相关代码
        //因为前端界面删除了患者选择的按钮，所以使用dom获取元素会报错，必须清理相关代码
        
        // 重置患者状态 - 默认选中患者
        // document.getElementById('is-patient').checked = true;
        // document.getElementById('not-patient').checked = false;
        this.patientStatus = 'patient';
        
        // 重置情感类型 - 清空选择
        document.getElementById('neutral-type').checked = false;
        document.getElementById('non-neutral-type').checked = false;
        this.emotionType = null;
        this.elements.specificEmotions.style.display = 'none';
        
        // 重置离散情感
        this.elements.discreteEmotionRadios.forEach(checkbox => {
            checkbox.checked = false;
        });
        this.selectedDiscreteEmotions = [];
        
        this.setModified(false);
    }

    /**
     * 设置修改状态
     */
    setModified(modified) {
        this.isModified = modified;
    }

    /**
     * 获取修改状态
     */
    getModified() {
        return this.isModified;
    }
}

