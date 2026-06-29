// static/js/test.js
/**
 * 标注能力测试系统前端脚本
 * 主要功能:
 * 1. 加载测试音频和正确答案
 * 2. 处理用户答题逻辑
 * 3. 计算正确率并判断是否通过测试
 * 4. 跳转到正式标注页面或重新测试
 */

document.addEventListener('DOMContentLoaded', function() {
    
    //==============================================
    // 1. DOM元素获取与变量初始化
    //==============================================
    
    const testUsernameSpan = document.getElementById('test-username');
    const currentQuestionSpan = document.getElementById('current-question');
    const totalQuestionsSpan = document.getElementById('total-questions');
    // 移除了正确率显示元素的获取
    const progressBar = document.getElementById('progress-bar');
    const testQuestion = document.getElementById('test-question');
    const testAudio = document.getElementById('test-audio');
    const discreteOptions = document.getElementById('discrete-options');
    const vaOptions = document.getElementById('va-options');
    const testVSlider = document.getElementById('test-v-slider');
    const testASlider = document.getElementById('test-a-slider');
    const testVDisplay = document.getElementById('test-v-display');
    const testADisplay = document.getElementById('test-a-display');
    const submitAnswerBtn = document.getElementById('submit-answer-btn');
    const nextQuestionBtn = document.getElementById('next-question-btn');
    const finishTestBtn = document.getElementById('finish-test-btn');
    const testResult = document.getElementById('test-result');
    const testSection = document.getElementById('test-section');
    
    // 状态变量
    let testQuestions = [];
    let currentQuestionIndex = 0;
    let correctAnswers = 0;
    let userAnswers = [];
    let selectedAnswer = null;
    let isAnswerSubmitted = false;
    let testStarted = false; // 添加测试开始标志
    let testPassThreshold = 85; // 默认阈值，将从配置API获取
    
    //==============================================
    // 2. 初始化和用户验证
    //==============================================
    
    /**
     * 初始化测试页面
     */
    function initTest() {
        // 隐藏测试结果区域
        testResult.style.display = 'none';
        
        // 加载配置和测试题目
        loadConfig();
        loadTestQuestions();
    }
    
    /**
     * 加载配置信息
     */
    async function loadConfig() {
        try {
            const response = await fetch('/api/config/test-pass-threshold');
            const data = await response.json();
            
            if (data.success) {
                testPassThreshold = data.threshold;
                console.log('测试通过阈值已加载:', testPassThreshold + '%');
                // 更新页面显示的阈值
                const thresholdDisplay = document.getElementById('test-threshold-display');
                if (thresholdDisplay) {
                    thresholdDisplay.textContent = testPassThreshold;
                }
            } else {
                console.warn('获取测试通过阈值失败，使用默认值:', testPassThreshold + '%');
            }
        } catch (error) {
            console.error('加载配置失败:', error);
            console.warn('使用默认测试通过阈值:', testPassThreshold + '%');
        }
    }
    
    /**
     * 加载测试题目
     */
    async function loadTestQuestions() {
        try {
            const response = await fetch('/api/test/questions');
            const data = await response.json();
            
            if (data.success) {
                testQuestions = data.questions;
                
                if (testQuestions.length === 0) {
                    // 没有测试题目，显示错误信息
                    testResult.style.display = 'block';
                    testResult.className = 'test-result fail';
                    testResult.innerHTML = `
                        <h2>⚠️ 暂无测试题目</h2>
                        <p>测试音频文件尚未准备好，请联系管理员。</p>
                        <button class="test-button secondary" onclick="goToMainPage()">跳过测试，直接进入标注</button>
                    `;
                    
                    // 隐藏测试界面
                    testSection.style.display = 'none';
                    document.querySelector('.test-controls').style.display = 'none';
                    return;
                }
                
                totalQuestionsSpan.textContent = testQuestions.length;
                
                // 开始第一题
                testStarted = true;
                showQuestion(0);
            } else {
                throw new Error(data.error || '加载测试题目失败');
            }
        } catch (error) {
            console.error('加载测试题目失败:', error);
            
            // 显示错误信息
            testResult.style.display = 'block';
            testResult.className = 'test-result fail';
            testResult.innerHTML = `
                <h2>❌ 加载失败</h2>
                <p>无法加载测试题目，错误信息：${error.message}</p>
                <button class="test-button primary" onclick="location.reload()">重新加载</button>
                <button class="test-button secondary" onclick="goToMainPage()">跳过测试，直接进入标注</button>
            `;
            
            // 隐藏测试界面
            testSection.style.display = 'none';
            document.querySelector('.test-controls').style.display = 'none';
        }
    }
    
    /**
     * 显示指定题目
     * @param {number} index - 题目索引
     */
    function showQuestion(index) {
        if (!testStarted || index >= testQuestions.length) {
            showTestResult();
            return;
        }
        
        const question = testQuestions[index];
        currentQuestionIndex = index;
        isAnswerSubmitted = false;
        selectedAnswer = null;
        
        // 确保测试区域可见
        testSection.style.display = 'block';
        testResult.style.display = 'none';
        
        // 更新进度
        currentQuestionSpan.textContent = index + 1;
        const progress = ((index + 1) / testQuestions.length) * 100;
        progressBar.style.width = progress + '%';
        
        // 移除了实时正确率更新逻辑
        
        // 设置音频
        testAudio.src = `/api/test/audio/${question.filename}`;
        
        // 根据测试类型显示不同的选项
        if (question.type === 'discrete') {
            showDiscreteOptions(question);
        } else if (question.type === 'potency') {
            showPotencyOptions(question);
        } else if (question.type === 'arousal') {
            showArousalOptions(question);
        }
        
        // 重置按钮状态
        submitAnswerBtn.disabled = true;
        submitAnswerBtn.style.display = 'inline-block';
        nextQuestionBtn.style.display = 'none';
        finishTestBtn.style.display = 'none';
        
        // 清除之前的选择状态
        clearSelections();
    }
    
    /**
     * 显示离散情感选项
     * @param {Object} question - 题目对象
     */
    function showDiscreteOptions(question) {
        testQuestion.textContent = '请听音频并选择正确的情感类型：';
        discreteOptions.style.display = 'grid';
        vaOptions.style.display = 'none';
        
        // 为选项添加点击事件
        const options = discreteOptions.querySelectorAll('.test-option');
        options.forEach(option => {
            option.onclick = () => selectDiscreteOption(option);
        });
    }
    
    /**
     * 显示效价值选项（只有V滑动条）
     * @param {Object} question - 题目对象
     */
    function showPotencyOptions(question) {
        testQuestion.textContent = '请听音频并调整效价值(V值)到正确的位置：';
        discreteOptions.style.display = 'none';
        vaOptions.style.display = 'block';
        
        // 重置滑动条
        testVSlider.value = 0;
        testASlider.value = 1;
        updateVADisplay();
        
        // 隐藏A滑动条，只显示V滑动条
        testASlider.parentElement.style.display = 'none';
        testVSlider.parentElement.style.display = 'block';
        
        // 添加滑动条事件
        testVSlider.oninput = () => {
            updateVADisplay();
            checkPotencySelection();
        };
    }
    
    /**
     * 显示唤醒值选项（只有A滑动条）
     * @param {Object} question - 题目对象
     */
    function showArousalOptions(question) {
        testQuestion.textContent = '请听音频并调整唤醒值(A值)到正确的位置：';
        discreteOptions.style.display = 'none';
        vaOptions.style.display = 'block';
        
        // 重置滑动条
        testVSlider.value = 0;
        testASlider.value = 1;
        updateVADisplay();
        
        // 隐藏V滑动条，只显示A滑动条
        testVSlider.parentElement.style.display = 'none';
        testASlider.parentElement.style.display = 'block';
        
        // 添加滑动条事件
        testASlider.oninput = () => {
            updateVADisplay();
            checkArousalSelection();
        };
    }
    
    /**
     * 选择离散情感选项
     * @param {Element} option - 选中的选项元素
     */
    function selectDiscreteOption(option) {
        if (isAnswerSubmitted) return;
        
        // 清除其他选项的选中状态
        discreteOptions.querySelectorAll('.test-option').forEach(opt => {
            opt.classList.remove('selected');
        });
        
        // 设置当前选项为选中状态
        option.classList.add('selected');
        selectedAnswer = option.dataset.value;
        
        // 启用提交按钮
        submitAnswerBtn.disabled = false;
    }
    
    /**
     * 检查效价值选择
     */
    function checkPotencySelection() {
        if (isAnswerSubmitted) return;
        
        // 效价值测试中，只要用户移动了V滑动条就可以提交
        selectedAnswer = parseFloat(testVSlider.value);
        
        submitAnswerBtn.disabled = false;
    }
    
    /**
     * 检查唤醒值选择
     */
    function checkArousalSelection() {
        if (isAnswerSubmitted) return;
        
        // 唤醒值测试中，只要用户移动了A滑动条就可以提交
        selectedAnswer = parseFloat(testASlider.value);
        
        submitAnswerBtn.disabled = false;
    }
    
    /**
     * 更新VA值显示
     */
    function updateVADisplay() {
        if (testVDisplay) testVDisplay.textContent = parseInt(testVSlider.value);
        if (testADisplay) testADisplay.textContent = parseInt(testASlider.value);
    }
    
    /**
     * 清除选择状态
     */
    function clearSelections() {
        // 清除离散情感选项状态
        discreteOptions.querySelectorAll('.test-option').forEach(opt => {
            opt.classList.remove('selected', 'correct', 'incorrect');
        });
        
        // 不重置滑动条显示状态，保持当前测试类型的显示逻辑
        // 滑动条的显示状态由showPotencyOptions和showArousalOptions函数控制
    }
    
    /**
     * 提交答案
     */
    function submitAnswer() {
        if (selectedAnswer === null || isAnswerSubmitted) return;
        
        const question = testQuestions[currentQuestionIndex];
        let isCorrect = false;
        
        // 检查答案是否正确
        if (question.type === 'discrete') {
            isCorrect = selectedAnswer === question.correct_answer;
            
            // 只在答案错误时给出提示
            if (!isCorrect) {
                // 给用户选择的错误选项添加错误样式
                discreteOptions.querySelectorAll('.test-option').forEach(opt => {
                    if (opt.dataset.value === selectedAnswer) {
                        opt.classList.add('incorrect');
                    }
                });
                
                // 显示错误提示
                testQuestion.innerHTML = `
                    请听音频并选择正确的标注<br>
                    <small style="color: red">❌ 标注错误</small>
                `;
            } else {
                // 答案正确时的提示
                testQuestion.innerHTML = `
                    请听音频并选择正确的标注<br>
                    <small style="color: green">✓ 标注正确！</small>
                `;
            }
        } else if (question.type === 'potency') {
            // 效价值测试：允许一定的误差范围（±0.5）
            const vDiff = Math.abs(selectedAnswer - question.correct_answer);
            isCorrect = vDiff <= 0.5;
            
            // 只显示是否正确的提示，不显示正确答案
            if (!isCorrect) {
                testQuestion.innerHTML = `
                    请听音频并调整效价值(V值)到正确的位置：<br>
                    <small style="color: red">❌ 标注错误</small>
                `;
            } else {
                testQuestion.innerHTML = `
                    请听音频并调整效价值(V值)到正确的位置：<br>
                    <small style="color: green">✓ 标注正确！</small>
                `;
            }
        } else if (question.type === 'arousal') {
            // 唤醒值测试：允许一定的误差范围（±0.5）
            const aDiff = Math.abs(selectedAnswer - question.correct_answer);
            isCorrect = aDiff <= 0.5;
            
            // 只显示是否正确的提示，不显示正确答案
            if (!isCorrect) {
                testQuestion.innerHTML = `
                    请听音频并调整唤醒值(A值)到正确的位置：<br>
                    <small style="color: red">❌ 标注错误</small>
                `;
            } else {
                testQuestion.innerHTML = `
                    请听音频并调整唤醒值(A值)到正确的位置：<br>
                    <small style="color: green">✓ 标注正确！</small>
                `;
            }
        }
        
        // 记录答案
        userAnswers.push({
            question_index: currentQuestionIndex,
            question_type: question.type,
            user_answer: selectedAnswer,
            correct_answer: question.correct_answer,
            is_correct: isCorrect
        });
        
        if (isCorrect) {
            correctAnswers++;
        }
        
        isAnswerSubmitted = true;
        submitAnswerBtn.style.display = 'none';
        
        // 显示下一题或完成按钮
        if (currentQuestionIndex < testQuestions.length - 1) {
            nextQuestionBtn.style.display = 'inline-block';
        } else {
            finishTestBtn.style.display = 'inline-block';
        }
    }
    
    /**
     * 显示测试结果
     */
    function showTestResult() {
        if (!testStarted || testQuestions.length === 0) {
            return;
        }
        
        const accuracy = Math.round((correctAnswers / testQuestions.length) * 100);
        const passed = accuracy >= testPassThreshold;
        
        // 隐藏测试界面，显示结果
        testSection.style.display = 'none';
        document.querySelector('.test-controls').style.display = 'none';
        testResult.style.display = 'block';
        testResult.className = `test-result ${passed ? 'pass' : 'fail'}`;
        
        if (passed) {
            // 保存测试通过状态
            localStorage.setItem('test_passed_' + currentUsername, 'true');
            
            // 显示测试通过界面
            testResult.innerHTML = `
                <h2>🎉 恭喜通过测试！</h2>
                <p>您的正确率为 <strong>${accuracy}%</strong>，已达到${testPassThreshold}%的要求。</p>
                <p>现在将进入一致性测试环节。</p>
                <button class="test-button primary" onclick="goToConsistencyTest()">进入一致性测试</button>
            `;
        } else {
            // 测试失败的处理保持不变
            testResult.innerHTML = `
                <h2>❌ 测试未通过</h2>
                <p>您的正确率为 <strong>${accuracy}%</strong>，未达到${testPassThreshold}%的要求。</p>
                <p>请重新学习后再次尝试。</p>
                <button class="test-button" onclick="location.reload()">重新测试</button>
            `;
        }
    }
    
    // 更新用户测试设置的函数（仅供管理员使用）
    async function updateUserTestSettings(username, skipTest, skipConsistencyTest) {
        try {
            const response = await fetch('/admin/api/users/test-settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    skip_test: skipTest,
                    skip_consistency_test: skipConsistencyTest
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || '更新用户测试设置失败');
            }
            
            return data;
        } catch (error) {
            console.error('更新用户测试设置失败:', error);
            throw error;
        }
    }
    
    /**
     * 重新测试
     */
    function retakeTest() {
        // 重置所有状态
        currentQuestionIndex = 0;
        correctAnswers = 0;
        userAnswers = [];
        selectedAnswer = null;
        isAnswerSubmitted = false;
        testStarted = false;
        
        // 隐藏结果，显示控制按钮
        testResult.style.display = 'none';
        testSection.style.display = 'block';
        document.querySelector('.test-controls').style.display = 'block';
        
        // 重新加载题目
        loadTestQuestions();
    }
    
    /**
     * 进入主页面
     */
    function goToMainPage() {
        window.location.href = '/main?keep_login=true';
    }
    
    /**
     * 进入一致性测试页面
     */
    function goToConsistencyTest() {
        // 直接跳转到一致性测试页面
        window.location.href = '/consistency-test';
    }
    
    /**
     * 退出测试
     */
    function exitTest() {
        const confirmExit = confirm('确定要退出测试吗？当前进度将不会保存。');
        if (confirmExit) {
            // 跳转到主页面
            window.location.href = '/main';
        }
    }
    
    //==============================================
    // 3. 事件监听器
    //==============================================
    
    if (submitAnswerBtn) submitAnswerBtn.addEventListener('click', submitAnswer);
    if (nextQuestionBtn) nextQuestionBtn.addEventListener('click', () => showQuestion(currentQuestionIndex + 1));
    if (finishTestBtn) finishTestBtn.addEventListener('click', showTestResult);
    
    // 退出测试按钮事件监听器
    const exitTestBtn = document.getElementById('exit-test-btn');
    if (exitTestBtn) exitTestBtn.addEventListener('click', exitTest);
    
    // 全局函数（供HTML调用）
    window.goToMainPage = goToMainPage;
    window.goToConsistencyTest = goToConsistencyTest;
    window.retakeTest = retakeTest;
    window.exitTest = exitTest;
    
    //==============================================
    // 4. 初始化
    //==============================================
    
    initTest();
});