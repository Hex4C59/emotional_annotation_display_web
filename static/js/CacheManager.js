/**
 * 前端缓存管理器
 * 负责管理API数据缓存，减少重复请求，提升页面切换速度
 */
class CacheManager {
    constructor() {
        this.cache = new Map();
        this.cacheExpiry = new Map();
        this.defaultTTL = 5 * 60 * 1000; // 默认5分钟过期
        this.maxCacheSize = 100; // 最大缓存条目数
        this.requestQueue = new Map(); // 防止重复请求
    }

    /**
     * 生成缓存键
     * @param {string} url - 请求URL
     * @param {Object} params - 请求参数
     * @returns {string} 缓存键
     */
    generateKey(url, params = {}) {
        const paramStr = Object.keys(params)
            .sort()
            .map(key => `${key}=${params[key]}`)
            .join('&');
        return `${url}${paramStr ? '?' + paramStr : ''}`;
    }

    /**
     * 检查缓存是否过期
     * @param {string} key - 缓存键
     * @returns {boolean} 是否过期
     */
    isExpired(key) {
        const expiry = this.cacheExpiry.get(key);
        return !expiry || Date.now() > expiry;
    }

    /**
     * 获取缓存数据
     * @param {string} key - 缓存键
     * @returns {*} 缓存的数据或null
     */
    get(key) {
        if (!this.cache.has(key) || this.isExpired(key)) {
            this.delete(key);
            return null;
        }
        return this.cache.get(key);
    }

    /**
     * 设置缓存数据
     * @param {string} key - 缓存键
     * @param {*} data - 要缓存的数据
     * @param {number} ttl - 过期时间（毫秒）
     */
    set(key, data, ttl = this.defaultTTL) {
        // 如果缓存已满，删除最旧的条目
        if (this.cache.size >= this.maxCacheSize) {
            const firstKey = this.cache.keys().next().value;
            this.delete(firstKey);
        }

        this.cache.set(key, data);
        this.cacheExpiry.set(key, Date.now() + ttl);
    }

    /**
     * 删除缓存条目
     * @param {string} key - 缓存键
     */
    delete(key) {
        this.cache.delete(key);
        this.cacheExpiry.delete(key);
    }

    /**
     * 清空所有缓存
     */
    clear() {
        this.cache.clear();
        this.cacheExpiry.clear();
        this.requestQueue.clear();
    }

    /**
     * 清理过期缓存
     */
    cleanup() {
        for (const [key] of this.cache) {
            if (this.isExpired(key)) {
                this.delete(key);
            }
        }
    }

    /**
     * 带缓存的fetch请求
     * @param {string} url - 请求URL
     * @param {Object} options - fetch选项
     * @param {Object} cacheOptions - 缓存选项
     * @returns {Promise} 请求结果
     */
    async fetch(url, options = {}, cacheOptions = {}) {
        const {
            ttl = this.defaultTTL,
            forceRefresh = false,
            preventDuplicate = true
        } = cacheOptions;

        // 只缓存GET请求
        const method = (options.method || 'GET').toUpperCase();
        if (method !== 'GET') {
            return fetch(url, options).then(response => response.json());
        }

        const cacheKey = this.generateKey(url, options.params);

        // 检查缓存
        if (!forceRefresh) {
            const cachedData = this.get(cacheKey);
            if (cachedData) {
                return Promise.resolve(cachedData);
            }
        }

        // 防止重复请求
        if (preventDuplicate && this.requestQueue.has(cacheKey)) {
            return this.requestQueue.get(cacheKey);
        }

        // 发起请求
        const requestPromise = fetch(url, options)
            .then(response => response.json())
            .then(data => {
                // 缓存成功的响应
                if (data && !data.error) {
                    this.set(cacheKey, data, ttl);
                }
                return data;
            })
            .catch(error => {
                console.error('Cache fetch error:', error);
                throw error;
            })
            .finally(() => {
                // 清理请求队列
                this.requestQueue.delete(cacheKey);
            });

        if (preventDuplicate) {
            this.requestQueue.set(cacheKey, requestPromise);
        }

        return requestPromise;
    }

    /**
     * 预加载数据
     * @param {Array} urls - 要预加载的URL列表
     * @param {Object} options - 预加载选项
     */
    async preload(urls, options = {}) {
        const { concurrent = 3, ttl = this.defaultTTL } = options;
        
        // 分批并发加载
        for (let i = 0; i < urls.length; i += concurrent) {
            const batch = urls.slice(i, i + concurrent);
            const promises = batch.map(url => {
                if (typeof url === 'string') {
                    return this.fetch(url, {}, { ttl });
                } else {
                    return this.fetch(url.url, url.options || {}, { ttl, ...url.cacheOptions });
                }
            });
            
            try {
                await Promise.allSettled(promises);
            } catch (error) {
                console.warn('Preload batch failed:', error);
            }
        }
    }

    /**
     * 获取缓存统计信息
     * @returns {Object} 缓存统计
     */
    getStats() {
        const now = Date.now();
        let expiredCount = 0;
        
        for (const [key] of this.cache) {
            if (this.isExpired(key)) {
                expiredCount++;
            }
        }

        return {
            totalEntries: this.cache.size,
            expiredEntries: expiredCount,
            activeEntries: this.cache.size - expiredCount,
            maxSize: this.maxCacheSize,
            usage: (this.cache.size / this.maxCacheSize * 100).toFixed(2) + '%'
        };
    }

    /**
     * 使缓存失效（支持模式匹配）
     * @param {string|RegExp} pattern - 要失效的缓存键模式
     */
    invalidate(pattern) {
        const keysToDelete = [];
        
        for (const [key] of this.cache) {
            if (typeof pattern === 'string') {
                if (key.includes(pattern)) {
                    keysToDelete.push(key);
                }
            } else if (pattern instanceof RegExp) {
                if (pattern.test(key)) {
                    keysToDelete.push(key);
                }
            }
        }
        
        keysToDelete.forEach(key => this.delete(key));
        return keysToDelete.length;
    }
}

// 创建全局缓存管理器实例
window.cacheManager = new CacheManager();

// 定期清理过期缓存
setInterval(() => {
    window.cacheManager.cleanup();
}, 60000); // 每分钟清理一次

// 添加startPeriodicCleanup方法以兼容模板调用
window.cacheManager.startPeriodicCleanup = function() {
    console.log('CacheManager periodic cleanup started');
    // 这个方法已经在上面通过setInterval实现了
};