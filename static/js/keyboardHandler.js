/**
 * 键盘快捷键处理模块
 */
class KeyboardHandler {
    constructor(callbacks) {
        this.callbacks = callbacks;
        this.initEventListeners();
    }

    initEventListeners() {
        document.addEventListener('keydown', (event) => {
            this.handleKeyDown(event);
        });
    }

    handleKeyDown(event) {
        // 检查是否在输入元素中
        const isInputElement = 
            document.activeElement.tagName === 'INPUT' && 
            (document.activeElement.type === 'text' || 
             document.activeElement.type === 'password' || 
             document.activeElement.type === 'email' ||
             document.activeElement.type === 'search') ||
            document.activeElement.tagName === 'TEXTAREA' || 
            (document.activeElement.tagName === 'SELECT') ||
            document.activeElement.isContentEditable;

        if (!isInputElement) {
            // 空格控制播放/暂停
            if (event.code === 'Space') {
                event.preventDefault();
                if (this.callbacks.togglePlayPause) {
                    this.callbacks.togglePlayPause();
                }
            }
            
            // E键 - 上一条
            if (event.key === 'e' || event.key === 'E') {
                event.preventDefault();
                if (this.callbacks.previous) {
                    this.callbacks.previous();
                }
            }
            
            // R键 - 下一条
            if (event.key === 'r' || event.key === 'R') {
                event.preventDefault();
                if (this.callbacks.next) {
                    this.callbacks.next();
                }
            }
            
            // W键 - 保存
            if (event.key === 'w' || event.key === 'W') {
                event.preventDefault();
                if (this.callbacks.save) {
                    this.callbacks.save();
                }
            }
            
            // Q键 - 继续/返回
            if (event.key === 'q' || event.key === 'Q') {
                event.preventDefault();
                if (this.callbacks.continueOrBack) {
                    this.callbacks.continueOrBack();
                }
            }
        }
    }

    /**
     * 重置焦点到主容器
     */
    resetFocus() {
        const mainContainer = document.getElementById('main-container');
        if (mainContainer) {
            mainContainer.focus();
        }
    }
}

