/**
 * 工具函数模块
 * 提供通用的辅助方法和工具函数
 */
class Utils {
    /**
     * 格式化日期
     * @param {Date|string} date - 日期对象或字符串
     * @param {string} format - 格式字符串，默认 'YYYY-MM-DD HH:mm:ss'
     * @returns {string} 格式化后的日期字符串
     */
    static formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
        if (!date) return '';
        
        const d = new Date(date);
        if (isNaN(d.getTime())) return '';
        
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        const seconds = String(d.getSeconds()).padStart(2, '0');
        
        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day)
            .replace('HH', hours)
            .replace('mm', minutes)
            .replace('ss', seconds);
    }

    /**
     * 格式化文件大小
     * @param {number} bytes - 字节数
     * @returns {string} 格式化后的文件大小
     */
    static formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * 格式化数字
     * @param {number} num - 数字
     * @param {number} decimals - 小数位数
     * @returns {string} 格式化后的数字
     */
    static formatNumber(num, decimals = 2) {
        if (isNaN(num)) return '0';
        return Number(num).toFixed(decimals);
    }

    /**
     * 格式化百分比
     * @param {number} value - 值
     * @param {number} total - 总数
     * @param {number} decimals - 小数位数
     * @returns {string} 格式化后的百分比
     */
    static formatPercentage(value, total, decimals = 1) {
        if (total === 0) return '0%';
        const percentage = (value / total) * 100;
        return this.formatNumber(percentage, decimals) + '%';
    }

    /**
     * 防抖函数
     * @param {Function} func - 要防抖的函数
     * @param {number} wait - 等待时间（毫秒）
     * @param {boolean} immediate - 是否立即执行
     * @returns {Function} 防抖后的函数
     */
    static debounce(func, wait, immediate = false) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    }

    /**
     * 节流函数
     * @param {Function} func - 要节流的函数
     * @param {number} limit - 限制时间（毫秒）
     * @returns {Function} 节流后的函数
     */
    static throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    /**
     * 深拷贝对象
     * @param {any} obj - 要拷贝的对象
     * @returns {any} 拷贝后的对象
     */
    static deepClone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj.getTime());
        if (obj instanceof Array) return obj.map(item => this.deepClone(item));
        if (typeof obj === 'object') {
            const clonedObj = {};
            for (const key in obj) {
                if (obj.hasOwnProperty(key)) {
                    clonedObj[key] = this.deepClone(obj[key]);
                }
            }
            return clonedObj;
        }
    }

    /**
     * 生成随机ID
     * @param {number} length - ID长度
     * @returns {string} 随机ID
     */
    static generateId(length = 8) {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let result = '';
        for (let i = 0; i < length; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return result;
    }

    /**
     * 验证邮箱格式
     * @param {string} email - 邮箱地址
     * @returns {boolean} 是否有效
     */
    static isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    /**
     * 验证密码强度
     * @param {string} password - 密码
     * @returns {Object} 验证结果
     */
    static validatePassword(password) {
        const result = {
            isValid: false,
            score: 0,
            feedback: []
        };

        if (!password) {
            result.feedback.push('密码不能为空');
            return result;
        }

        if (password.length < 6) {
            result.feedback.push('密码长度至少6位');
        } else {
            result.score += 1;
        }

        if (password.length >= 8) {
            result.score += 1;
        }

        if (/[a-z]/.test(password)) {
            result.score += 1;
        }

        if (/[A-Z]/.test(password)) {
            result.score += 1;
        }

        if (/\d/.test(password)) {
            result.score += 1;
        }

        if (/[^\w\s]/.test(password)) {
            result.score += 1;
        }

        result.isValid = result.score >= 3 && password.length >= 6;

        if (result.score < 3) {
            result.feedback.push('密码强度不够，建议包含大小写字母、数字和特殊字符');
        }

        return result;
    }

    /**
     * 转义HTML字符
     * @param {string} text - 要转义的文本
     * @returns {string} 转义后的文本
     */
    static escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    /**
     * 获取URL参数
     * @param {string} name - 参数名
     * @param {string} url - URL字符串，默认为当前页面URL
     * @returns {string|null} 参数值
     */
    static getUrlParameter(name, url = window.location.href) {
        const urlObj = new URL(url);
        return urlObj.searchParams.get(name);
    }

    /**
     * 设置URL参数
     * @param {string} name - 参数名
     * @param {string} value - 参数值
     * @param {string} url - URL字符串，默认为当前页面URL
     * @returns {string} 新的URL
     */
    static setUrlParameter(name, value, url = window.location.href) {
        const urlObj = new URL(url);
        urlObj.searchParams.set(name, value);
        return urlObj.toString();
    }

    /**
     * 删除URL参数
     * @param {string} name - 参数名
     * @param {string} url - URL字符串，默认为当前页面URL
     * @returns {string} 新的URL
     */
    static removeUrlParameter(name, url = window.location.href) {
        const urlObj = new URL(url);
        urlObj.searchParams.delete(name);
        return urlObj.toString();
    }

    /**
     * 复制文本到剪贴板
     * @param {string} text - 要复制的文本
     * @returns {Promise<boolean>} 是否成功
     */
    static async copyToClipboard(text) {
        try {
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(text);
                return true;
            } else {
                // 降级方案
                const textArea = document.createElement('textarea');
                textArea.value = text;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                textArea.style.top = '-999999px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                const result = document.execCommand('copy');
                document.body.removeChild(textArea);
                return result;
            }
        } catch (error) {
            console.error('复制失败:', error);
            return false;
        }
    }

    /**
     * 下载文件
     * @param {string} url - 文件URL
     * @param {string} filename - 文件名
     */
    static downloadFile(url, filename) {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    /**
     * 创建Blob URL
     * @param {any} data - 数据
     * @param {string} type - MIME类型
     * @returns {string} Blob URL
     */
    static createBlobUrl(data, type = 'application/octet-stream') {
        const blob = new Blob([data], { type });
        return URL.createObjectURL(blob);
    }

    /**
     * 释放Blob URL
     * @param {string} url - Blob URL
     */
    static revokeBlobUrl(url) {
        URL.revokeObjectURL(url);
    }

    /**
     * 检测是否为移动设备
     * @returns {boolean} 是否为移动设备
     */
    static isMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    /**
     * 获取浏览器信息
     * @returns {Object} 浏览器信息
     */
    static getBrowserInfo() {
        const ua = navigator.userAgent;
        const result = {
            name: 'Unknown',
            version: 'Unknown',
            os: 'Unknown'
        };

        // 检测浏览器
        if (ua.includes('Chrome')) {
            result.name = 'Chrome';
            const match = ua.match(/Chrome\/(\d+)/);
            if (match) result.version = match[1];
        } else if (ua.includes('Firefox')) {
            result.name = 'Firefox';
            const match = ua.match(/Firefox\/(\d+)/);
            if (match) result.version = match[1];
        } else if (ua.includes('Safari')) {
            result.name = 'Safari';
            const match = ua.match(/Version\/(\d+)/);
            if (match) result.version = match[1];
        } else if (ua.includes('Edge')) {
            result.name = 'Edge';
            const match = ua.match(/Edge\/(\d+)/);
            if (match) result.version = match[1];
        }

        // 检测操作系统
        if (ua.includes('Windows')) {
            result.os = 'Windows';
        } else if (ua.includes('Mac')) {
            result.os = 'macOS';
        } else if (ua.includes('Linux')) {
            result.os = 'Linux';
        } else if (ua.includes('Android')) {
            result.os = 'Android';
        } else if (ua.includes('iOS')) {
            result.os = 'iOS';
        }

        return result;
    }

    /**
     * 本地存储操作
     */
    static storage = {
        /**
         * 设置本地存储
         * @param {string} key - 键
         * @param {any} value - 值
         */
        set(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
            } catch (error) {
                console.error('设置本地存储失败:', error);
            }
        },

        /**
         * 获取本地存储
         * @param {string} key - 键
         * @param {any} defaultValue - 默认值
         * @returns {any} 值
         */
        get(key, defaultValue = null) {
            try {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            } catch (error) {
                console.error('获取本地存储失败:', error);
                return defaultValue;
            }
        },

        /**
         * 删除本地存储
         * @param {string} key - 键
         */
        remove(key) {
            try {
                localStorage.removeItem(key);
            } catch (error) {
                console.error('删除本地存储失败:', error);
            }
        },

        /**
         * 清空本地存储
         */
        clear() {
            try {
                localStorage.clear();
            } catch (error) {
                console.error('清空本地存储失败:', error);
            }
        }
    };

    /**
     * 会话存储操作
     */
    static sessionStorage = {
        /**
         * 设置会话存储
         * @param {string} key - 键
         * @param {any} value - 值
         */
        set(key, value) {
            try {
                sessionStorage.setItem(key, JSON.stringify(value));
            } catch (error) {
                console.error('设置会话存储失败:', error);
            }
        },

        /**
         * 获取会话存储
         * @param {string} key - 键
         * @param {any} defaultValue - 默认值
         * @returns {any} 值
         */
        get(key, defaultValue = null) {
            try {
                const item = sessionStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            } catch (error) {
                console.error('获取会话存储失败:', error);
                return defaultValue;
            }
        },

        /**
         * 删除会话存储
         * @param {string} key - 键
         */
        remove(key) {
            try {
                sessionStorage.removeItem(key);
            } catch (error) {
                console.error('删除会话存储失败:', error);
            }
        },

        /**
         * 清空会话存储
         */
        clear() {
            try {
                sessionStorage.clear();
            } catch (error) {
                console.error('清空会话存储失败:', error);
            }
        }
    };
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Utils;
}