/**
 * Standard Answer Service
 * Handles fetching and displaying standard answers for audio files
 */
class StandardAnswerService {
    constructor() {
        this.currentAnswer = null;
        this.elements = {
            container: document.getElementById('standard-answers'),
            vValue: document.getElementById('standard-v-value'),
            // v9PValue: document.getElementById('standard-v-value9P'),
            //2025年9月11日
            //bcd：增加9分值的A值和V值
            //又去掉了，因为发现9分值和5分值是两个不同的网页，若要以dom区分必定会有一个因为无法找到渲染目标而冲突
            aValue: document.getElementById('standard-a-value'),
            // a9PValue: document.getElementById('standard-a-value9P'),
            discreteEmotion: document.getElementById('standard-discrete-emotion'),
            // patientStatus: document.getElementById('standard-patient-status')
        };
    }

    /**
     * Fetch standard answer for an audio file
     * @param {string} audioFile - Audio file name
     * @returns {Promise<Object|null>} Standard answer or null if not found
     */
    async fetchStandardAnswer(audioFile) {
        try {
            const response = await fetch(`/api/standard_answer/${encodeURIComponent(audioFile)}`);
            const data = await response.json();
            if (data.success && data.answer) {
                this.currentAnswer = data.answer;
                return data.answer;
            } else {
                this.currentAnswer = null;
                return null;
            }
        } catch (error) {
            console.error('Failed to fetch standard answer:', error);
            this.currentAnswer = null;
            return null;
        }
    }

    /**
     * Display standard answer in the UI
     * @param {string} audioFile - Audio file name
     */
    async displayStandardAnswer(audioFile) {
        console.log('displayStandardAnswer called for:', audioFile);
        
        if (!this.elements.container) {
            console.warn('Standard answers container not found');
            return;
        }

        // Show loading state
        this.showLoading();
        console.log('Standard answer loading state shown');

        try {
            const answer = await this.fetchStandardAnswer(audioFile);
            console.log('Fetched standard answer:', answer);
            
            if (answer) {
                this.updateDisplay(answer);
                this.showContainer();
                console.log('Standard answer displayed successfully');
            } else {
                this.hideContainer();
                console.log('No standard answer found, container hidden');
            }
        } catch (error) {
            console.error('Error displaying standard answer:', error);
            this.hideContainer();
        }
    }

    /**
     * Update the display with answer data
     * @param {Object} answer - Standard answer data
     */
    updateDisplay(answer) {
        // if (!this.elements.vValue || !this.elements.aValue || 
        //     !this.elements.discreteEmotion || !this.elements.patientStatus) {
        //     console.warn('Standard answer elements not found');
        //     return;
        // }
        if (!this.elements.vValue || !this.elements.aValue || 
            !this.elements.discreteEmotion) {
            console.warn('Standard answer elements not found');
            return;
        }
        // Update V value
        this.elements.vValue.textContent = answer.v_value !== null ? 
            this.convertIntoV9P(answer.v_value).toString() : '-';
        // Update V 9-point value
        // console.log('***Object v9PValue:', Object.prototype.toString.call(v9PValue));
        // if(v9PValue){
        // this.elements.v9PValue.textContent = answer.v_value !== null ? 
        // (this.convertIntoV9P(answer.v_value)).toString() : '-';
        // }
        // Update A value  
        this.elements.aValue.textContent = answer.a_value !== null ? 
            this.convertIntoA9P(answer.a_value).toString() : '-';

        // if(a9PValue){
        // this.elements.a9PValue.textContent = answer.a_value !== null ? 
        //     this.convertIntoA9P(answer.a_value).toString() : '-';
        // }
        // Update discrete emotion
        const emotion = answer.discrete_emotion || answer.emotion_type || '-';
        this.elements.discreteEmotion.textContent = emotion;
        this.elements.discreteEmotion.className = 'answer-value';
        if (emotion !== '-') {
            this.elements.discreteEmotion.className += ' emotion';
        }
        //2025年9月11日
        //bcd：
        //去掉病人状态的显示

        // Update patient status
        // const patientStatus = answer.patient_status || '-';
        // this.elements.patientStatus.textContent = patientStatus;
        // this.elements.patientStatus.className = 'answer-value';
        // if (patientStatus === 'patient') {
        //     this.elements.patientStatus.className += ' patient';
        // } else if (patientStatus === 'non-patient') {
        //     this.elements.patientStatus.className += ' non-patient';
        // }
    }

    /**
     * Show loading state
     */
    showLoading() {
        if (this.elements.vValue) this.elements.vValue.textContent = 'Loading...';
        if (this.elements.aValue) this.elements.aValue.textContent = 'Loading...';
        if (this.elements.discreteEmotion) this.elements.discreteEmotion.textContent = 'Loading...';
        // if (this.elements.patientStatus) this.elements.patientStatus.textContent = 'Loading...';
        this.showContainer();
    }

    /**
     * Show the standard answers container
     */
    showContainer() {
        if (this.elements.container) {
            this.elements.container.style.display = 'block';
            console.log('Standard answers container shown');
        }
    }

    /**
     * Hide the standard answers container
     */
    hideContainer() {
        if (this.elements.container) {
            this.elements.container.style.display = 'none';
            console.log('Standard answers container hidden');
        }
        this.currentAnswer = null;
    }

    /**
     * Clear the display
     */
    clearDisplay() {
        if (this.elements.vValue) this.elements.vValue.textContent = '-';
        if (this.elements.aValue) this.elements.aValue.textContent = '-';
        if (this.elements.discreteEmotion) {
            this.elements.discreteEmotion.textContent = '-';
            this.elements.discreteEmotion.className = 'answer-value';
        }
        //2025年9月11日
        //bcd：
        //去掉病人状态的显示
        // if (this.elements.patientStatus) {
        //     this.elements.patientStatus.textContent = '-';
        //     this.elements.patientStatus.className = 'answer-value';
        // }
        this.hideContainer();
    }

    /**
     * Get the current standard answer
     * @returns {Object|null} Current answer or null
     */
    getCurrentAnswer() {
        return this.currentAnswer;
    }
    convertIntoA9P(x) {
        return Math.round((x - 1) / 0.5 + 1);
    }
    convertIntoV9P(x) {
        return Math.round(x * 2);
    }
}