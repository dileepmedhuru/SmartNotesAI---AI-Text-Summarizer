// Admin Dashboard JavaScript
let allUsers = [];
let allSummaries = [];
let activityData = [];

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
    loadDashboardData();
});

// Initialize theme
function initializeTheme() {
    const savedTheme = localStorage.getItem('smartnotes-theme') || 'light';
    document.body.setAttribute('data-theme', savedTheme);
}

// Load all dashboard data
async function loadDashboardData() {
    showLoading();
    try {
        await Promise.all([
            loadUsers(),
            loadAllSummaries(),
            loadActivity(),
            loadStatistics()
        ]);
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showToast('Error loading dashboard data', 'error');
    } finally {
        hideLoading();
    }
}

// Load statistics
async function loadStatistics() {
    try {
        const response = await fetch('/api/admin/statistics');
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('totalUsers').textContent = data.total_users || 0;
            document.getElementById('totalSummaries').textContent = data.total_summaries || 0;
            document.getElementById('todayActivity').textContent = data.today_activity || 0;
            document.getElementById('avgCompression').textContent = (data.avg_compression || 0) + '%';
            
            // Analytics tab
            document.getElementById('totalWords').textContent = (data.total_words || 0).toLocaleString();
            document.getElementById('avgSummaryLength').textContent = data.avg_summary_length || 0;
            document.getElementById('mostActiveUser').textContent = data.most_active_user || '-';
            document.getElementById('popularLanguage').textContent = data.popular_language || '-';
        }
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

// Load users
async function loadUsers() {
    try {
        const response = await fetch('/api/admin/users');
        const data = await response.json();
        
        if (data.success) {
            allUsers = data.users;
            displayUsers(allUsers);
        }
    } catch (error) {
        console.error('Error loading users:', error);
        showToast('Error loading users', 'error');
    }
}

// Display users
function displayUsers(users) {
    const tbody = document.getElementById('usersTableBody');
    
    if (!users || users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px;">No users found</td></tr>';
        return;
    }
    
    tbody.innerHTML = users.map(user => `
        <tr>
            <td>
                <div class="user-info">
                    <div class="user-avatar">${user.username.charAt(0).toUpperCase()}</div>
                    <div class="user-details">
                        <h4>${user.username}</h4>
                        <p>ID: ${user.id}</p>
                    </div>
                </div>
            </td>
            <td>${user.email}</td>
            <td>${new Date(user.created_at).toLocaleDateString()}</td>
            <td>${user.summary_count || 0}</td>
            <td>${user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}</td>
            <td>
                <span class="status-badge ${user.is_active ? 'active' : 'inactive'}">
                    ${user.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td>
                <div class="action-buttons">
                    <button class="action-btn btn-view" onclick="viewUserDetails(${user.id})" title="View Details">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="action-btn btn-export" onclick="exportUserData(${user.id})" title="Export Data">
                        <i class="fas fa-download"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Load all summaries
async function loadAllSummaries() {
    try {
        const response = await fetch('/api/admin/summaries');
        const data = await response.json();
        
        if (data.success) {
            allSummaries = data.summaries;
            displaySummaries(allSummaries);
        }
    } catch (error) {
        console.error('Error loading summaries:', error);
        showToast('Error loading summaries', 'error');
    }
}

// Display summaries
function displaySummaries(summaries) {
    const tbody = document.getElementById('summariesTableBody');
    
    if (!summaries || summaries.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px;">No summaries found</td></tr>';
        return;
    }
    
    tbody.innerHTML = summaries.map(summary => `
        <tr>
            <td>${summary.title || 'Untitled'}</td>
            <td>${summary.username || 'Unknown'}</td>
            <td>${new Date(summary.created_at).toLocaleDateString()}</td>
            <td>${summary.original_word_count || 0}</td>
            <td>${summary.compression_ratio || 0}%</td>
            <td>${summary.language_name || '-'}</td>
            <td>
                <div class="action-buttons">
                    <button class="action-btn btn-view" onclick="viewSummaryDetails(${summary.id})" title="View">
                        <i class="fas fa-eye"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Load activity
async function loadActivity() {
    try {
        const response = await fetch('/api/admin/activity');
        const data = await response.json();
        
        if (data.success) {
            activityData = data.activities;
            displayActivity(activityData);
        }
    } catch (error) {
        console.error('Error loading activity:', error);
    }
}

// Display activity
function displayActivity(activities) {
    const activityList = document.getElementById('activityList');
    
    if (!activities || activities.length === 0) {
        activityList.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-secondary);">No recent activity</div>';
        return;
    }
    
    activityList.innerHTML = activities.map(activity => `
        <div class="activity-item">
            <div class="activity-icon">
                <i class="fas ${getActivityIcon(activity.type)}"></i>
            </div>
            <div class="activity-content">
                <h4>${activity.description}</h4>
                <p>${activity.username} • ${activity.details || ''}</p>
            </div>
            <div class="activity-time">
                ${getTimeAgo(activity.timestamp)}
            </div>
        </div>
    `).join('');
}

// Get activity icon
function getActivityIcon(type) {
    const icons = {
        'login': 'fa-sign-in-alt',
        'register': 'fa-user-plus',
        'summary': 'fa-file-alt',
        'download': 'fa-download',
        'delete': 'fa-trash'
    };
    return icons[type] || 'fa-circle';
}

// Get time ago
function getTimeAgo(timestamp) {
    const now = new Date();
    const time = new Date(timestamp);
    const diff = Math.floor((now - time) / 1000);
    
    if (diff < 60) return 'Just now';
    if (diff < 3600) return Math.floor(diff / 60) + ' min ago';
    if (diff < 86400) return Math.floor(diff / 3600) + ' hours ago';
    return Math.floor(diff / 86400) + ' days ago';
}

// Switch tabs
function switchAdminTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.admin-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tabName + '-tab').classList.add('active');
}

// Search users
function searchUsers() {
    const searchTerm = document.getElementById('userSearch').value.toLowerCase();
    const filtered = allUsers.filter(user => 
        user.username.toLowerCase().includes(searchTerm) ||
        user.email.toLowerCase().includes(searchTerm)
    );
    displayUsers(filtered);
}

// Search summaries
function searchSummaries() {
    const searchTerm = document.getElementById('summarySearch').value.toLowerCase();
    const filtered = allSummaries.filter(summary => 
        (summary.title || '').toLowerCase().includes(searchTerm) ||
        (summary.username || '').toLowerCase().includes(searchTerm)
    );
    displaySummaries(filtered);
}

// View user details
async function viewUserDetails(userId) {
    try {
        const response = await fetch(`/api/admin/users/${userId}`);
        const data = await response.json();
        
        if (data.success) {
            const user = data.user;
            alert(`User Details:\n\nUsername: ${user.username}\nEmail: ${user.email}\nJoined: ${new Date(user.created_at).toLocaleString()}\nTotal Summaries: ${user.summary_count}\nTotal Words Processed: ${user.total_words_processed.toLocaleString()}`);
        }
    } catch (error) {
        console.error('Error loading user details:', error);
        showToast('Error loading user details', 'error');
    }
}

// View summary details
async function viewSummaryDetails(summaryId) {
    try {
        const response = await fetch(`/api/admin/summaries/${summaryId}`);
        const data = await response.json();
        
        if (data.success) {
            const summary = data.summary;
            alert(`Summary Details:\n\nTitle: ${summary.title || 'Untitled'}\nUser: ${summary.username}\nCreated: ${new Date(summary.created_at).toLocaleString()}\nOriginal Words: ${summary.original_word_count}\nSummary Words: ${summary.summary_word_count}\nCompression: ${summary.compression_ratio}%\n\nSummary:\n${summary.summary_text.substring(0, 200)}...`);
        }
    } catch (error) {
        console.error('Error loading summary details:', error);
        showToast('Error loading summary details', 'error');
    }
}

// Export users
async function exportUsers() {
    try {
        showLoading();
        const response = await fetch('/api/admin/export/users');
        const blob = await response.blob();
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `users_export_${new Date().getTime()}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showToast('Users exported successfully', 'success');
    } catch (error) {
        console.error('Error exporting users:', error);
        showToast('Error exporting users', 'error');
    } finally {
        hideLoading();
    }
}

// Export summaries
async function exportSummaries() {
    try {
        showLoading();
        const response = await fetch('/api/admin/export/summaries');
        const blob = await response.blob();
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `summaries_export_${new Date().getTime()}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showToast('Summaries exported successfully', 'success');
    } catch (error) {
        console.error('Error exporting summaries:', error);
        showToast('Error exporting summaries', 'error');
    } finally {
        hideLoading();
    }
}

// Export user data
async function exportUserData(userId) {
    try {
        showLoading();
        const response = await fetch(`/api/admin/export/user/${userId}`);
        const blob = await response.blob();
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `user_${userId}_data_${new Date().getTime()}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showToast('User data exported successfully', 'success');
    } catch (error) {
        console.error('Error exporting user data:', error);
        showToast('Error exporting user data', 'error');
    } finally {
        hideLoading();
    }
}

// Refresh activity
function refreshActivity() {
    loadActivity();
    showToast('Activity refreshed', 'success');
}

// Utility functions
function showLoading() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');
    
    toastMessage.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}