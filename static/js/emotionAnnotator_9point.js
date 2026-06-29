/**
 * 情感标注模块 - 9点量表版本
 * 负责VA值标注和离散情感标注
 * A值范围：1-9，V值范围：-4到4
 */
class EmotionAnnotator {
    constructor(elements) {
        this.elements = elements;
        this.isModified = false;
        this.isVaLabelingMode = true;
        this.emotionType = 'neutral';
        this.selectedDiscreteEmotions = [];
        this.patientStatus = 'patient';
        this.vaScale = '9_point'; // 标识为9点量表
        
        this.initElements();
        this.initEventListeners();
    }

    initElements() {
        // 初始化V值滑动条 (-4到4)
        this.elements.vSlider.min = -4;
        this.elements.vSlider.max = 4;
        this.elements.vSlider.step = 1;
        // 不设置默认值，让用户主动选择

        // 初始化A值滑动条 (1到9)
        this.elements.aSlider.min = 1;
        this.elements.aSlider.max = 9;
        this.elements.aSlider.step = 1;
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
        
        // 离散情感事件（现在是复选框）
        this.elements.discreteEmotionRadios.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                if (checkbox.checked) {
                    if (!this.selectedDiscreteEmotions.includes(checkbox.value)) {
                        this.selectedDiscreteEmotions.push(checkbox.value);
                    }
                } else {
                    this.selectedDiscreteEmotions = this.selectedDiscreteEmotions.filter(emotion => emotion !== checkbox.value);
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
        valueElement.textContent = Number(slider.value);
        this.setModified(true);
    }

    /**
     * 更新滑动条显示
     */
    updateSliderDisplay() {
        this.elements.vValue.textContent = Number(this.elements.vSlider.value);
        this.elements.aValue.textContent = Number(this.elements.aSlider.value);
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
            this.elements.discreteEmotionRadios.forEach(checkbox => {
                checkbox.checked = false;
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
     * 切换到离散情感标注模式
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
        return fetch(`/api/get_label/${encodeURIComponent(username)}/${encodeURIComponent(speaker)}/${encodeURIComponent(filename)}?va_scale=9_point`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.data) {
                    const label = data.data;
                    
                    // 只加载9点量表的数据
                    if (label.va_scale && label.va_scale !== '9_point') {
                        // 如果是5点量表的数据，不加载，保持空白状态
                        this.reset();
                        return null;
                    }
                    
                    // 设置VA值
                    if (label.v_value !== undefined && label.v_value !== null) {
                        this.elements.vSlider.value = label.v_value;
                    } else {
                        this.elements.vSlider.value = '';
                    }
                    if (label.a_value !== undefined && label.a_value !== null) {
                        this.elements.aSlider.value = label.a_value;
                    } else {
                        this.elements.aSlider.value = '';
                    }
                    this.updateSliderDisplay();
                            //2025年9月12日
        //bcd：清理是否患者的相关代码
        //因为前端界面删除了患者选择的按钮，所以使用dom获取元素会报错，必须清理相关代码
                    // 设置患者状态
                    // if (label.patient_status && label.patient_status !== null) {
                    //     this.patientStatus = label.patient_status;
                    //     const patientRadio = document.getElementById(label.patient_status === 'patient' ? 'is-patient' : 'not-patient');
                    //     if (patientRadio) patientRadio.checked = true;
                    // } else {
                    //     this.patientStatus = null;
                    //     const patientRadios = document.querySelectorAll('input[name="patient-status"]');
                    //     patientRadios.forEach(radio => radio.checked = false);
                    // }
                    
                    // 设置情感类型
                    if (label.emotion_type && label.emotion_type !== null) {
                        this.emotionType = label.emotion_type;
                        const emotionRadio = document.getElementById(label.emotion_type === 'neutral' ? 'neutral-type' : 'non-neutral-type');
                        if (emotionRadio) emotionRadio.checked = true;
                        
                        this.handleEmotionTypeChange();
                        
                        // 设置具体情感（支持多选）
                        if (this.emotionType === 'non-neutral' && label.discrete_emotion && label.discrete_emotion !== null) {
                            let emotions = [];
                            if (typeof label.discrete_emotion === 'string') {
                                emotions = label.discrete_emotion.split(',').map(e => e.trim()).filter(e => e);
                            } else if (Array.isArray(label.discrete_emotion)) {
                                emotions = label.discrete_emotion;
                            } else {
                                emotions = [label.discrete_emotion];
                            }
                            
                            console.log('Loading discrete emotions:', emotions);
                            this.selectedDiscreteEmotions = emotions;
                            const discreteCheckboxes = document.querySelectorAll('input[name="discrete-emotion"]');
                            discreteCheckboxes.forEach(checkbox => checkbox.checked = false);
                            emotions.forEach(emotion => {
                                const discreteCheckbox = document.getElementById(`emotion-${emotion}`);
                                if (discreteCheckbox) {
                                    discreteCheckbox.checked = true;
                                }
                            });
                        } else {
                            this.selectedDiscreteEmotions = [];
                            if (this.emotionType === 'neutral') {
                                const discreteCheckboxes = document.querySelectorAll('input[name="discrete-emotion"]');
                                discreteCheckboxes.forEach(checkbox => checkbox.checked = false);
                            }
                        }
                    } else {
                        this.emotionType = 'neutral';
                        this.selectedDiscreteEmotions = [];
                        const emotionRadios = document.querySelectorAll('input[name="emotion-type"]');
                        emotionRadios.forEach(radio => radio.checked = false);
                        document.getElementById('neutral-type').checked = true;
                        this.handleEmotionTypeChange();
                    }
                    
                    this.setModified(false);
                    console.log('Loaded label:', label);
                    return label;
                }
            });
    }

    /**
     * 获取当前标注数据
     */
    getCurrentAnnotation() {
        const discreteEmotionStr = this.emotionType === 'neutral' ? null : 
            (this.selectedDiscreteEmotions.length > 0 ? this.selectedDiscreteEmotions.join(',') : null);
        
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
     */
    getAnnotationCompleteness() {
        const hasV = this.elements.vSlider.value !== '' && this.elements.vSlider.value !== null;
        const hasA = this.elements.aSlider.value !== '' && this.elements.aSlider.value !== null;
        const hasPatientStatus = this.patientStatus !== null;
        
        const hasEmotionType = this.emotionType !== null;
        const hasDiscreteEmotion = this.emotionType === 'neutral' || (this.emotionType === 'non-neutral' && this.selectedDiscreteEmotions.length > 0);
        
        const discreteComplete = hasPatientStatus && hasEmotionType && hasDiscreteEmotion;
        
        const result = [];
        if (hasV && hasA) result.push('va_complete');
        if (discreteComplete) result.push('discrete_complete');
        
        if (result.length === 0) {
            return ['none'];
        }
        
        return result;
    }

    /**
     * 重置标注
     */
    reset() {
        this.elements.vSlider.value = '';
        this.elements.aSlider.value = '';
        this.updateSliderDisplay();
                //2025年9月12日
        //bcd：清理是否患者的相关代码
        //因为前端界面删除了患者选择的按钮，所以使用dom获取元素会报错，必须清理相关代码
        // document.getElementById('is-patient').checked = true;
        // document.getElementById('not-patient').checked = false;
        this.patientStatus = 'patient';
        
        document.getElementById('neutral-type').checked = false;
        document.getElementById('non-neutral-type').checked = false;
        this.emotionType = null;
        this.elements.specificEmotions.style.display = 'none';
        
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