class VolumeTestConfirmation {
    constructor() {
        this.currentUser = null;
        this.init();
    }
    
    async init() {
        try {
            await this.checkLoginStatus();
            await this.loadVolumeData();
            this.setupAudioPlayers();
        } catch (error) {
            console.error('初始化失败:', error);
            this.showError('页面初始化失败，请刷新重试');
        }
    }
    
    async checkLoginStatus() {
        try {
            console.log('开始检查登录状态');
            const response = await fetch('/api/user/session-status');
            console.log('会话状态响应:', response.status, response.ok);
            
            if (!response.ok) {
                throw new Error('会话状态检查失败: ' + response.status);
            }
            
            const data = await response.json();
            console.log('会话状态数据:', data);
            
            if (data.authenticated) {
                this.currentUser = data.username;
                console.log('用户已登录:', this.currentUser);
            } else {
                throw new Error('用户未认证');
            }
        } catch (error) {
            console.error('登录状态检查失败:', error);
            console.error('即将跳转到登录页面');
            window.location.href = '/login';
        }
    }
    
    async loadVolumeData() {
        try {
            if (!this.currentUser) {
                throw new Error('用户未登录');
            }
            
            const response = await fetch(`/api/volume-settings/${this.currentUser}`);
            if (!response.ok) {
                throw new Error('获取音量数据失败');
            }
            const data = await response.json();
            
            if (data.success && data.volume_setting !== null) {
                document.getElementById('volumeValue').textContent = data.volume_setting;
            } else {
                document.getElementById('volumeValue').textContent = '未设置';
            }
        } catch (error) {
            console.error('加载音量数据失败:', error);
            document.getElementById('volumeValue').textContent = '加载失败';
        }
    }
    
    setupAudioPlayers() {
        const audioElements = document.querySelectorAll('audio');
        audioElements.forEach(audio => {
            // 设置音量为用户设置的音量
            const volumeValue = document.getElementById('volumeValue').textContent;
            if (volumeValue && volumeValue !== '未设置' && volumeValue !== '加载失败' && volumeValue !== '加载中...') {
                const volume = parseInt(volumeValue) / 100;
                audio.volume = Math.max(0, Math.min(1, volume));
            }
            
            // 添加播放事件监听
            audio.addEventListener('play', () => {
                console.log('开始播放音频:', audio.src);
            });
            
            audio.addEventListener('error', (e) => {
                console.error('音频播放错误:', e);
                this.showError('音频加载失败，请检查网络连接');
            });
        });
    }
    
    showError(message) {
        // 创建错误提示
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 5px;
            border: 1px solid #f5c6cb;
            z-index: 1000;
            max-width: 300px;
        `;
        errorDiv.textContent = message;
        
        document.body.appendChild(errorDiv);
        
        // 3秒后自动移除
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 3000);
    }
    
    showLoading(show = true) {
        const loadingIndicator = document.getElementById('loadingIndicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = show ? 'block' : 'none';
        }
    }
    

    

    

    

    

    

}

// 全局函数，供HTML按钮调用
function retakeTest() {
    const confirmation = window.volumeTestConfirmation;
    if (confirmation) {
        confirmation.showLoading(true);
    }
    
    // 跳转到音量测试页面
    setTimeout(() => {
        window.location.href = '/volume-test';
    }, 500);
}

async function continueToNext() {
    console.log('continueToNext 函数被调用');
    const confirmation = window.volumeTestConfirmation;
    console.log('confirmation 对象:', confirmation);
    
    if (confirmation) {
        confirmation.showLoading(true);
        console.log('currentUser:', confirmation.currentUser);
    }
    
    // 检查confirmation对象是否存在
    if (!confirmation || !confirmation.currentUser) {
        console.error('用户信息未找到，confirmation:', confirmation, 'currentUser:', confirmation?.currentUser);
        console.error('跳转到登录页面');
        window.location.href = '/login';
        return;
    }
    
    console.log('开始获取用户测试设置，用户名:', confirmation.currentUser);
    // 获取用户测试设置并跳转到相应页面
    try {
        console.log('开始获取用户设置，用户:', confirmation.currentUser);
        const response = await fetch(`/api/user/test-settings/${confirmation.currentUser}`);
        console.log('用户设置API响应状态:', response.status, response.ok);
        console.log('响应头:', response.headers);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('API响应错误:', response.status, errorText);
            throw new Error(`API请求失败: ${response.status} - ${errorText}`);
        }
        
        const data = await response.json();
        console.log('用户设置数据:', data);
        
        if (data.success) {
            console.log('设置详情 - skip_test:', data.skip_test, 'skip_consistency_test:', data.skip_consistency_test, 'scale_order:', data.scale_order);
            
            if (data.skip_test && data.skip_consistency_test) {
                 console.log('跳过测试和一致性测试，直接进入标注页面');
                 // 根据用户的量表顺序设置决定跳转到哪个页面
                 if (data.scale_order === '9_point_first') {
                     console.log('用户设置为9点量表优先，跳转到9点量表页面');
                     window.location.href = '/9point';
                 } else {
                     console.log('用户设置为5点量表优先或默认设置，跳转到5点量表页面');
                     window.location.href = '/main';
                 }
            } else if (data.skip_test) {
                console.log('跳过测试，进入一致性测试');
                window.location.href = '/consistency-test';
            } else {
                console.log('进入正式测试');
                window.location.href = '/test';
            }
        } else {
            console.error('获取用户设置失败:', data.message);
            confirmation.showError('获取用户设置失败: ' + data.message);
        }
    } catch (error) {
        console.error('Failed to get user settings:', error);
        confirmation.showError('获取用户设置失败: ' + error.message);
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    window.volumeTestConfirmation = new VolumeTestConfirmation();
});