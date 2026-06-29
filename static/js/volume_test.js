// 音量测试页面JavaScript

class VolumeTest {
    constructor() {
        this.currentUser = null;
        this.volumeValue = null;
        this.init();
    }

    init() {
        // 检查用户登录状态
        this.checkLoginStatus();
        
        // 绑定事件监听器
        this.bindEvents();
        
        // 同步滑块和输入框
        this.syncVolumeControls();
    }

    checkLoginStatus() {
        // 从localStorage获取用户名
        const username = localStorage.getItem('emotion_labeling_username');
        if (!username) {
            // 用户未登录，跳转到登录页面
            window.location.href = '/login';
            return;
        }
        
        this.currentUser = username;
        document.getElementById('current-user').textContent = username;
    }

    bindEvents() {
        // 音量输入框事件
        const volumeInput = document.getElementById('volume-input');
        const volumeSlider = document.getElementById('volume-slider');
        const saveButton = document.getElementById('save-volume');

        // 输入框变化事件
        volumeInput.addEventListener('input', (e) => {
            const value = parseInt(e.target.value);
            if (value >= 0 && value <= 100) {
                volumeSlider.value = value;
                this.volumeValue = value;
                this.updateSaveButtonState();
            }
        });

        // 滑块变化事件
        volumeSlider.addEventListener('input', (e) => {
            const value = parseInt(e.target.value);
            volumeInput.value = value;
            this.volumeValue = value;
            this.updateSaveButtonState();
        });

        // 保存按钮事件
        saveButton.addEventListener('click', () => {
            this.saveVolumeSettings();
        });

        // 键盘事件
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && this.volumeValue !== null) {
                this.saveVolumeSettings();
            }
        });
    }

    syncVolumeControls() {
        const volumeInput = document.getElementById('volume-input');
        const volumeSlider = document.getElementById('volume-slider');
        
        // 设置初始值
        volumeSlider.value = 50;
        volumeInput.value = '';
    }

    updateSaveButtonState() {
        const saveButton = document.getElementById('save-volume');
        const isValid = this.volumeValue !== null && 
                       this.volumeValue >= 0 && 
                       this.volumeValue <= 100;
        
        saveButton.disabled = !isValid;
        
        if (isValid) {
            saveButton.textContent = `保存音量设置 (${this.volumeValue}%) 并继续`;
        } else {
            saveButton.textContent = '保存音量设置并继续';
        }
    }

    async saveVolumeSettings() {
        if (this.volumeValue === null || this.volumeValue < 0 || this.volumeValue > 100) {
            this.showMessage('请输入有效的音量值 (0-100)', 'error');
            return;
        }

        const saveButton = document.getElementById('save-volume');
        const originalText = saveButton.textContent;
        
        try {
            // 显示加载状态
            saveButton.disabled = true;
            saveButton.textContent = '保存中...';
            document.body.classList.add('loading');

            // 发送音量设置到服务器
            const response = await fetch('/api/volume-settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: this.currentUser,
                    volume: this.volumeValue
                })
            });

            const result = await response.json();

            if (result.success) {
                this.showMessage('音量设置保存成功！即将跳转...', 'success');
                
                // 延迟跳转到确认页面，让用户看到成功消息
                setTimeout(() => {
                    window.location.href = '/volume-test-confirmation';
                }, 1500);
            } else {
                throw new Error(result.message || '保存失败');
            }
        } catch (error) {
            console.error('保存音量设置失败:', error);
            this.showMessage('保存失败，请重试', 'error');
            
            // 恢复按钮状态
            saveButton.disabled = false;
            saveButton.textContent = originalText;
            document.body.classList.remove('loading');
        }
    }

    async redirectToNextPage() {
        try {
            // 获取用户的测试设置，决定下一步跳转
            const response = await fetch(`/api/user/test-settings/${this.currentUser}`);
            const data = await response.json();

            if (data.success) {
                // 根据用户设置决定跳转页面
                if (!data.skip_test) {
                    window.location.href = '/test';
                } else if (!data.skip_consistency_test) {
                    window.location.href = '/consistency-test';
                } else {
                    window.location.href = '/';
                }
            } else {
                // 默认跳转到测试页面
                window.location.href = '/test';
            }
        } catch (error) {
            console.error('获取用户设置失败:', error);
            // 默认跳转到测试页面
            window.location.href = '/test';
        }
    }

    showMessage(message, type = 'info') {
        // 移除现有的消息
        const existingMessage = document.querySelector('.message');
        if (existingMessage) {
            existingMessage.remove();
        }

        // 创建新消息
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        messageDiv.textContent = message;

        // 插入到内容区域顶部
        const content = document.querySelector('.content');
        content.insertBefore(messageDiv, content.firstChild);

        // 自动移除消息
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 5000);
    }
}

// 播放音频的全局函数
function playAudio(audioId) {
    const audio = document.getElementById(audioId);
    if (audio) {
        audio.currentTime = 0; // 重置到开始
        audio.play().catch(error => {
            console.error('播放音频失败:', error);
            alert('播放音频失败，请检查音频文件是否存在');
        });
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    new VolumeTest();
});

// 防止用户意外离开页面
window.addEventListener('beforeunload', (e) => {
    const volumeInput = document.getElementById('volume-input');
    if (volumeInput && volumeInput.value && !document.body.classList.contains('loading')) {
        e.preventDefault();
        e.returnValue = '您还没有保存音量设置，确定要离开吗？';
        return e.returnValue;
    }
});