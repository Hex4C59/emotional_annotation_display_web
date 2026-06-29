/**
 * Simplified user manager
 * No authentication required, returns fixed user information
 */
class UserManager {
    constructor() {
        this.currentUsername = 'Liu Yang';
        this.isAuthenticated = true;
    }

    /**
     * Initialize authentication status
     * @returns {Promise<boolean>} Whether authentication is successful
     */
    async initAuth() {
        // Simplified version, directly return success
        console.log('User authentication successful:', this.currentUsername);
        return true;
    }

    /**
     * Get current username
     * @returns {string} Current username
     */
    getCurrentUsername() {
        return this.currentUsername;
    }

    /**
     * Check if authenticated
     * @returns {boolean} Whether authenticated
     */
    isAuth() {
        return this.isAuthenticated;
    }
}