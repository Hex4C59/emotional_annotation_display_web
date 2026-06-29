/**
 * 数据服务模块
 * 负责与后端API的数据交互
 */
class DataService {
    /**
     * 保存标注数据
     */
    static saveLabel(labelData) {
        return fetch('/api/save_label', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(labelData)
        })
        .then(response => response.json());
    }

    /**
     * 获取标注数据
     */
    static getLabel(username, speaker, filename, vaScale = '5_point') {
        return fetch(`/api/get_label/${encodeURIComponent(username)}/${encodeURIComponent(speaker)}/${encodeURIComponent(filename)}?va_scale=${vaScale}`)
            .then(response => response.json());
    }

    /**
     * 获取说话人列表
     */
    static getSpeakers() {
        return fetch('/api/speakers')
            .then(response => response.json());
    }

    /**
     * 获取音频列表
     */
    static getAudioList(speaker, vaScale = '5_point') {
        return fetch(`/api/audio_list/${speaker}?va_scale=${vaScale}`)
            .then(response => response.json());
    }

    /**
     * 保存播放计数
     */
    static savePlayCount(username, speaker, audioFile) {
        return fetch('/api/save_play_count', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username,
                speaker,
                audio_file: audioFile
            })
        })
        .then(response => response.json());
    }

    /**
     * 获取播放计数
     */
    static getPlayCount(username, speaker, filename, vaScale = '5_point') {
        return fetch(`/api/get_play_count/${encodeURIComponent(username)}/${encodeURIComponent(speaker)}/${encodeURIComponent(filename)}?va_scale=${vaScale}`)
            .then(response => response.json());
    }

    /**
     * 获取用户分组信息
     */
    static getUserGroupInfo(username) {
        return fetch(`/api/group/user-assignment?username=${encodeURIComponent(username)}`)
            .then(response => response.json());
    }
}

