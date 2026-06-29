/**
 * 音频播放器模块
 * 负责音频播放控制和播放计数
 */
class AudioPlayer {
    constructor(audioElement, playCountElement) {
        this.audioElement = audioElement;
        this.playCountElement = playCountElement;
        this.currentPlayCount = 0;
        this.currentAudioFile = null;
        this.currentSpeaker = null;
        this.currentUsername = null;
        
        // 定义播放结束事件处理函数，保持引用一致
        this.handleAudioEnded = () => {
            this.incrementPlayCount();
        };
        
        this.initEventListeners();
    }

    initEventListeners() {
        this.audioElement.addEventListener('loadedmetadata', () => {
            const duration = this.audioElement.duration;
            console.log(`音频时长: ${duration.toFixed(2)}秒`);
        });
    }

    /**
     * 播放/暂停切换
     */
    togglePlayPause() {
        if (this.audioElement.src) {
            if (this.audioElement.paused) {
                // 如果音频已经播放到结尾，重置到开头
                if (this.audioElement.currentTime >= this.audioElement.duration) {
                    this.audioElement.currentTime = 0;
                }
                this.audioElement.play();
            } else {
                this.audioElement.pause();
            }
        }
    }

    /**
     * 加载音频文件
     */
    loadAudio(audioFile, speaker, username) {
        console.log('=== 开始加载音频文件 ===');
        console.log('加载音频参数:', {
            audioFile: audioFile,
            speaker: speaker,
            username: username
        });
        
        // Save current audio information
        this.currentAudioFile = audioFile;
        this.currentSpeaker = speaker;
        this.currentUsername = username;
        
        console.log('Saved current audio information:', {
            currentAudioFile: this.currentAudioFile,
            currentSpeaker: this.currentSpeaker,
            currentUsername: this.currentUsername
        });
        
        // 移除之前的播放结束事件监听器
        console.log('移除之前的播放结束事件监听器');
        this.audioElement.removeEventListener('ended', this.handleAudioEnded);
        
        // 设置音频源并加载
        console.log('设置音频源:', audioFile.path);
        this.audioElement.src = audioFile.path;
        this.audioElement.load();
        
        // 添加播放结束事件监听器
        console.log('添加播放结束事件监听器');
        this.audioElement.addEventListener('ended', this.handleAudioEnded);
        
        // 立即加载播放次数，不等待音频元数据
        console.log('立即加载播放次数');
        this.loadPlayCount();
        
        // 等待音频元数据加载完成后处理
        console.log('设置元数据加载完成后的回调');
        this.audioElement.addEventListener('loadedmetadata', () => {
            console.log('音频元数据加载完成，当前播放次数:', this.currentPlayCount);
            
            // 重置播放位置到开头（在元数据加载完成后）
            this.audioElement.currentTime = 0;
            console.log('重置音频播放位置到开头');
            
            // 如果播放次数显示为0，再次尝试加载
            if (this.currentPlayCount === 0) {
                console.log('播放次数为0，再次尝试加载');
                this.loadPlayCount();
            }
        }, { once: true });
        
        console.log('=== 音频加载完成 ===');
        // 不自动播放，让用户手动控制
        return Promise.resolve();
    }

    /**
     * 增加播放次数（音频播放完成后调用）
     */
    incrementPlayCount() {
        if (!this.currentAudioFile || !this.currentSpeaker || !this.currentUsername) {
            return;
        }
        
        const requestData = {
            username: this.currentUsername,
            speaker: this.currentSpeaker,
            audio_file: this.currentAudioFile.file_name
        };
        
        fetch('/api/save_play_count', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.currentPlayCount = data.play_count;
                this.updatePlayCountDisplay();
            }
        })
        .catch(error => {
            console.error('Failed to save play count:', error);
        });
    }

    /**
     * 加载播放次数
     */
    loadPlayCount() {
        console.log('=== 开始加载播放次数 ===');
        console.log('当前参数:', {
            username: this.currentUsername,
            speaker: this.currentSpeaker,
            audioFile: this.currentAudioFile?.file_name,
            audioFileObject: this.currentAudioFile
        });
        
        if (!this.currentUsername || !this.currentSpeaker || !this.currentAudioFile) {
            console.warn('缺少必要参数，设置播放次数为0');
            console.log('参数检查结果:', {
                hasUsername: !!this.currentUsername,
                hasSpeaker: !!this.currentSpeaker,
                hasAudioFile: !!this.currentAudioFile,
                hasFileName: !!this.currentAudioFile?.file_name
            });
            this.currentPlayCount = 0;
            this.updatePlayCountDisplay();
            return;
        }
        
        const url = `/api/get_play_count/${encodeURIComponent(this.currentUsername)}/${encodeURIComponent(this.currentSpeaker)}/${encodeURIComponent(this.currentAudioFile.file_name)}`;
        console.log('构建的请求URL:', url);
        console.log('URL参数详情:', {
            原始username: this.currentUsername,
            编码后username: encodeURIComponent(this.currentUsername),
            原始speaker: this.currentSpeaker,
            编码后speaker: encodeURIComponent(this.currentSpeaker),
            原始filename: this.currentAudioFile.file_name,
            编码后filename: encodeURIComponent(this.currentAudioFile.file_name)
        });
        
        fetch(url)
            .then(response => {
                console.log('API响应状态:', response.status);
                console.log('API响应头:', response.headers);
                if (!response.ok) {
                    console.error('API响应不正常:', response.status, response.statusText);
                }
                return response.json();
            })
            .then(data => {
                console.log('API响应数据:', data);
                console.log('数据类型检查:', {
                    dataType: typeof data,
                    hasSuccess: 'success' in data,
                    successValue: data.success,
                    hasPlayCount: 'play_count' in data,
                    playCountValue: data.play_count,
                    playCountType: typeof data.play_count
                });
                
                if (data.success) {
                    this.currentPlayCount = data.play_count || 0;
                    console.log('成功设置播放次数为:', this.currentPlayCount);
                    this.updatePlayCountDisplay();
                } else {
                    console.warn('API返回失败，设置播放次数为0');
                    console.log('失败原因:', data.error || '未知错误');
                    this.currentPlayCount = 0;
                    this.updatePlayCountDisplay();
                }
            })
            .catch(error => {
                console.error('获取播放计数失败:', error);
                console.error('错误详情:', {
                    name: error.name,
                    message: error.message,
                    stack: error.stack
                });
                this.currentPlayCount = 0;
                this.updatePlayCountDisplay();
            });
        
        console.log('=== loadPlayCount 方法执行完毕 ===');
    }

    /**
     * 更新播放次数显示
     */
    updatePlayCountDisplay() {
        console.log('更新播放次数显示:', this.currentPlayCount);
        if (this.playCountElement) {
            this.playCountElement.textContent = this.currentPlayCount;
            console.log('播放次数元素已更新，当前文本:', this.playCountElement.textContent);
        } else {
            console.error('播放次数显示元素未找到');
        }
    }

    /**
     * 重置播放器
     */
    reset() {
        this.audioElement.src = '';
        this.currentPlayCount = 0;
        this.updatePlayCountDisplay();
    }
}

