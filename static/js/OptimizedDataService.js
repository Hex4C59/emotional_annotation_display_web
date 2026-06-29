/**
 * 优化的数据服务模块
 * 集成缓存管理、批量请求、预加载等性能优化功能
 */
class OptimizedDataService {
    constructor() {
        this.cache = window.cacheManager;
        this.batchQueue = new Map();
        this.batchTimeout = 50; // 批量请求延迟（毫秒）
        this.retryConfig = {
            maxRetries: 2, // 减少重试次数
            retryDelay: 300, // 减少重试延迟
            backoffMultiplier: 1.5 // 使用更温和的退避策略
        };
    }

    /**
     * 带重试机制的请求
     * @param {Function} requestFn - 请求函数
     * @param {number} retries - 剩余重试次数
     * @returns {Promise} 请求结果
     */
    async requestWithRetry(requestFn, retries = this.retryConfig.maxRetries) {
        try {
            return await requestFn();
        } catch (error) {
            if (retries > 0 && this.shouldRetry(error)) {
                const delay = this.retryConfig.retryDelay * 
                    Math.pow(this.retryConfig.backoffMultiplier, this.retryConfig.maxRetries - retries);
                await this.sleep(delay);
                return this.requestWithRetry(requestFn, retries - 1);
            }
            throw error;
        }
    }

    /**
     * 判断是否应该重试
     * @param {Error} error - 错误对象
     * @returns {boolean} 是否重试
     */
    shouldRetry(error) {
        // 网络错误或5xx服务器错误才重试
        return error.name === 'TypeError' || 
               (error.status && error.status >= 500);
    }

    /**
     * 延迟函数
     * @param {number} ms - 延迟毫秒数
     * @returns {Promise} Promise对象
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * 批量获取数据
     * @param {Array} requests - 请求列表
     * @returns {Promise<Array>} 批量结果
     */
    async batchRequest(requests) {
        const batchId = Date.now() + Math.random();
        
        return new Promise((resolve, reject) => {
            this.batchQueue.set(batchId, {
                requests,
                resolve,
                reject,
                timestamp: Date.now()
            });

            // 延迟执行，收集更多请求
            setTimeout(() => {
                this.processBatch(batchId);
            }, this.batchTimeout);
        });
    }

    /**
     * 处理批量请求
     * @param {string} batchId - 批次ID
     */
    async processBatch(batchId) {
        const batch = this.batchQueue.get(batchId);
        if (!batch) return;

        this.batchQueue.delete(batchId);
        
        try {
            const results = await Promise.allSettled(
                batch.requests.map(req => this.cache.fetch(req.url, req.options, req.cacheOptions))
            );
            
            const processedResults = results.map(result => {
                if (result.status === 'fulfilled') {
                    return result.value;
                } else {
                    console.warn('Batch request failed:', result.reason);
                    return { error: result.reason.message };
                }
            });
            
            batch.resolve(processedResults);
        } catch (error) {
            batch.reject(error);
        }
    }

    /**
     * 保存标注数据（不缓存POST请求）
     */
    async saveLabel(labelData) {
        return this.requestWithRetry(() => 
            fetch('/api/save_label', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(labelData)
            }).then(response => response.json())
        );
    }

    /**
     * 获取标注数据（带缓存）
     */
    async getLabel(username, speaker, filename, vaScale = '5_point') {
        const url = `/api/get_label/${encodeURIComponent(username)}/${encodeURIComponent(speaker)}/${encodeURIComponent(filename)}?va_scale=${vaScale}`;
        return this.cache.fetch(url, {}, { ttl: 2 * 60 * 1000 }); // 2分钟缓存
    }

    /**
     * 获取说话人列表（带缓存）
     */
    async getSpeakers() {
        const url = '/api/speakers';
        return this.cache.fetch(url, {}, { ttl: 10 * 60 * 1000 }); // 10分钟缓存
    }

    /**
     * 获取音频列表（带缓存）
     */
    async getAudioList(speaker, vaScale = '5_point') {
        const url = `/api/audio_list/${speaker}?va_scale=${vaScale}`;
        return this.cache.fetch(url, {}, { ttl: 5 * 60 * 1000 }); // 5分钟缓存
    }

    /**
     * 获取所有音频列表（不按说话人分组，带缓存）
     */
    async getAllAudioList(vaScale = '5_point') {
        const url = `/api/all_audio_list?va_scale=${vaScale}`;
        return this.cache.fetch(url, {}, { ttl: 5 * 60 * 1000 }); // 5分钟缓存
    }

    /**
     * 批量获取音频列表
     * @param {Array} speakers - 说话人列表
     * @param {string} username - 用户名
     * @param {string} vaScale - VA量表类型
     * @returns {Promise<Array>} 批量结果
     */
    async batchGetAudioLists(speakers, username, vaScale = '5_point') {
        const requests = speakers.map(speaker => ({
            url: `/api/audio_list/${speaker}?username=${encodeURIComponent(username)}&va_scale=${vaScale}`,
            options: {},
            cacheOptions: { ttl: 5 * 60 * 1000 }
        }));
        
        return this.batchRequest(requests);
    }

    /**
     * 保存播放计数
     */
    async savePlayCount(username, speaker, audioFile) {
        const result = await this.requestWithRetry(() => 
            fetch('/api/save_play_count', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username,
                    speaker,
                    audio_file: audioFile
                })
            }).then(response => response.json())
        );
        
        // 播放计数更新后，使相关缓存失效
        this.cache.invalidate(`/api/get_play_count/${encodeURIComponent(username)}/${encodeURIComponent(speaker)}`);
        
        return result;
    }

    /**
     * 获取播放计数（带缓存）
     */
    async getPlayCount(username, speaker, filename, vaScale = '5_point') {
        const url = `/api/get_play_count/${encodeURIComponent(username)}/${encodeURIComponent(speaker)}/${encodeURIComponent(filename)}?va_scale=${vaScale}`;
        return this.cache.fetch(url, {}, { ttl: 1 * 60 * 1000 }); // 1分钟缓存
    }

    /**
     * 获取用户分组信息（带缓存）
     */
    async getUserGroupInfo(username) {
        const url = `/api/group/user-assignment?username=${encodeURIComponent(username)}`;
        return this.cache.fetch(url, {}, { ttl: 30 * 60 * 1000 }); // 30分钟缓存
    }

    // ==================== 管理员API方法 ====================

    /**
     * 获取分组列表
     */
    async getGroups() {
        return this.cache.fetch('/admin/api/groups', {}, { ttl: 15 * 60 * 1000 });
    }

    /**
     * 获取质量分析数据
     */
    async getQualityData() {
        return this.cache.fetch('/admin/api/quality', {}, { ttl: 5 * 60 * 1000 });
    }

    /**
     * 获取用户列表
     */
    async getUsers() {
        return this.cache.fetch('/admin/api/users', {}, { ttl: 10 * 60 * 1000 });
    }

    /**
     * 获取用户详情
     */
    async getUserDetails(username) {
        const url = `/admin/api/users/${encodeURIComponent(username)}/details`;
        return this.cache.fetch(url, {}, { ttl: 1 * 60 * 1000 }); // 1分钟缓存
    }

    /**
     * 获取一致性数据
     */
    async getConsistencyData() {
        return this.cache.fetch('/admin/api/consistency', {}, { ttl: 10 * 60 * 1000 });
    }

    /**
     * 获取一致性测试用户列表
     */
    async getConsistencyUsers() {
        return this.cache.fetch('/admin/api/consistency/users', {}, { ttl: 15 * 60 * 1000 });
    }

    /**
     * 获取第二次一致性测试用户列表
     */
    async getSecondConsistencyUsers() {
        return this.cache.fetch('/admin/api/second-consistency/users', {}, { ttl: 15 * 60 * 1000 });
    }

    // ==================== 预加载和批量优化方法 ====================

    /**
     * 预加载用户相关数据
     * @param {string} username - 用户名
     */
    async preloadUserData(username) {
        const urls = [
            `/api/speakers?username=${encodeURIComponent(username)}`,
            `/api/group/user-assignment?username=${encodeURIComponent(username)}`
        ];
        
        await this.cache.preload(urls, { concurrent: 2, ttl: 15 * 60 * 1000 });
    }

    /**
     * 预加载管理员数据
     */
    async preloadAdminData() {
        const urls = [
            '/admin/api/groups',
            '/admin/api/users',
            '/admin/api/quality',
            '/admin/api/consistency/users',
            '/admin/api/second-consistency/users'
        ];
        
        await this.cache.preload(urls, { concurrent: 3, ttl: 10 * 60 * 1000 });
    }

    /**
     * 智能预加载下一批音频数据
     * @param {string} username - 用户名
     * @param {string} speaker - 说话人
     * @param {number} currentIndex - 当前音频索引
     * @param {Array} audioList - 音频列表
     * @param {string} vaScale - VA量表类型
     */
    async preloadNextAudioData(username, speaker, currentIndex, audioList, vaScale = '5_point') {
        const preloadCount = 5; // 预加载接下来5个音频的数据
        const startIndex = currentIndex + 1;
        const endIndex = Math.min(startIndex + preloadCount, audioList.length);
        
        const filenames = audioList.slice(startIndex, endIndex).map(audio => audio.filename);
        
        if (filenames.length > 0) {
            const requests = filenames.map(filename => ({
                url: `/api/get_label/${encodeURIComponent(username)}/${encodeURIComponent(speaker)}/${encodeURIComponent(filename)}?va_scale=${vaScale}`,
                options: {},
                cacheOptions: { ttl: 10 * 60 * 1000 }
            }));
            
            // 异步预加载，不阻塞当前操作
            this.batchRequest(requests).catch(error => {
                console.warn('Preload failed:', error);
            });
        }
    }

    // ==================== 缓存管理方法 ====================

    /**
     * 清除用户相关缓存
     * @param {string} username - 用户名
     */
    clearUserCache(username) {
        this.cache.invalidate(new RegExp(`username=${encodeURIComponent(username)}`));
    }

    /**
     * 清除管理员相关缓存
     */
    clearAdminCache() {
        this.cache.invalidate('/admin/api/');
    }

    /**
     * 获取缓存统计信息
     */
    getCacheStats() {
        return this.cache.getStats();
    }

    /**
     * 强制刷新指定数据
     * @param {string} url - 要刷新的URL
     */
    async forceRefresh(url) {
        return this.cache.fetch(url, {}, { forceRefresh: true });
    }
    async getUserGroupInfo(username) {
        const url = `/api/group/user-assignment?username=${encodeURIComponent(username)}`;
        return this.cache.fetch(url, {}, { ttl: 30 * 60 * 1000 }); // 30分钟缓存
    }

    /**
     * 管理员API - 获取分组列表（带缓存）
     */
    async getGroups() {
        const url = '/admin/api/groups';
        return this.cache.fetch(url, {}, { ttl: 15 * 60 * 1000 }); // 15分钟缓存
    }

    /**
     * 管理员API - 获取质量分析数据（带缓存）
     */
    async getQualityData() {
        const url = '/admin/api/quality';
        return this.cache.fetch(url, {}, { ttl: 3 * 60 * 1000 }); // 3分钟缓存
    }

    /**
     * 管理员API - 获取用户列表（带缓存）
     */
    async getUsers() {
        const url = '/admin/api/users';
        return this.cache.fetch(url, {}, { ttl: 5 * 60 * 1000 }); // 5分钟缓存
    }

    /**
     * 管理员API - 获取一致性数据（带缓存）
     */
    async getConsistencyData() {
        const url = '/admin/api/consistency';
        return this.cache.fetch(url, {}, { ttl: 10 * 60 * 1000 }); // 10分钟缓存
    }

    /**
     * 管理员API - 获取一致性用户列表（带缓存）
     */
    async getConsistencyUsers() {
        const url = '/admin/api/consistency/users';
        return this.cache.fetch(url, {}, { ttl: 10 * 60 * 1000 }); // 10分钟缓存
    }

    /**
     * 预加载常用数据
     * @param {string} username - 用户名
     * @param {Object} options - 预加载选项
     */
    async preloadUserData(username, options = {}) {
        const { loadAudioLists = true, loadGroupInfo = true } = options;
        
        const preloadUrls = [];
        
        // 预加载说话人列表
        preloadUrls.push({
            url: `/api/speakers?username=${encodeURIComponent(username)}`,
            cacheOptions: { ttl: 10 * 60 * 1000 }
        });
        
        if (loadGroupInfo) {
            // 预加载用户分组信息
            preloadUrls.push({
                url: `/api/group/user-assignment?username=${encodeURIComponent(username)}`,
                cacheOptions: { ttl: 30 * 60 * 1000 }
            });
        }
        
        // 先加载说话人列表，然后预加载音频列表
        if (loadAudioLists) {
            try {
                const speakersResult = await this.getSpeakers(username);
                if (speakersResult.success && speakersResult.speakers) {
                    const audioListUrls = speakersResult.speakers.slice(0, 5).map(speaker => ({
                        url: `/api/audio_list/${speaker}?username=${encodeURIComponent(username)}&va_scale=5_point`,
                        cacheOptions: { ttl: 5 * 60 * 1000 }
                    }));
                    preloadUrls.push(...audioListUrls);
                }
            } catch (error) {
                console.warn('Failed to preload audio lists:', error);
            }
        }
        
        return this.cache.preload(preloadUrls, { concurrent: 3 });
    }

    /**
     * 预加载管理员数据
     */
    async preloadAdminData() {
        const preloadUrls = [
            {
                url: '/admin/api/groups',
                cacheOptions: { ttl: 15 * 60 * 1000 }
            },
            {
                url: '/admin/api/users',
                cacheOptions: { ttl: 5 * 60 * 1000 }
            },
            {
                url: '/admin/api/quality',
                cacheOptions: { ttl: 3 * 60 * 1000 }
            },
            {
                url: '/admin/api/consistency',
                cacheOptions: { ttl: 10 * 60 * 1000 }
            }
        ];
        
        return this.cache.preload(preloadUrls, { concurrent: 2 });
    }

    /**
     * 清除用户相关缓存
     * @param {string} username - 用户名
     */
    clearUserCache(username) {
        const patterns = [
            `/api/speakers?username=${encodeURIComponent(username)}`,
            `/api/audio_list/.*username=${encodeURIComponent(username)}`,
            `/api/all_audio_list/${encodeURIComponent(username)}`,
            `/api/get_label/${encodeURIComponent(username)}`,
            `/api/get_play_count/${encodeURIComponent(username)}`,
            `/api/group/user-assignment?username=${encodeURIComponent(username)}`
        ];
        
        patterns.forEach(pattern => {
            this.cache.invalidate(new RegExp(pattern));
        });
        
        console.log(`Cleared cache for user: ${username}`);
    }

    /**
     * 清除管理员相关缓存
     */
    clearAdminCache() {
        const patterns = [
            '/admin/api/groups',
            '/admin/api/users',
            '/admin/api/quality',
            '/admin/api/consistency'
        ];
        
        patterns.forEach(pattern => {
            this.cache.invalidate(pattern);
        });
    }

    /**
     * 获取服务统计信息
     * @returns {Object} 统计信息
     */
    getStats() {
        return {
            cache: this.cache.getStats(),
            batchQueue: {
                pending: this.batchQueue.size
            }
        };
    }
}

// 创建全局优化数据服务实例
window.optimizedDataService = new OptimizedDataService();