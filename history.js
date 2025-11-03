// History management JavaScript
let currentPage = 1;
let currentFilter = 'all';
let currentSearch = '';
let allHistory = [];

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
    loadHistory();
    initializeFilters();
});

// Initialize theme
function initializeTheme() {
    const savedTheme = localStorage.getItem('smartnotes-theme') || 'light';
    document.body.setAttribute('data-theme', savedTheme);
}

// Initialize filter buttons
function initializeFilters() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentFilter = this.dataset.filter;
            currentPage = 1;
            filterAndDisplay();
        });
    });
}

// Load history from server
async function loadHistory() {
    showLoading();
    
    try {
        const response = await fetch(`/api/history?page=${currentPage}&per_page=10&search=${currentSearch}`);
        const data = await response.json();
        
        if (data.success) {
            allHistory = data.summaries;
            displayHistory(data.summaries);
            updateStatistics();
            setupPagination(data.total, data.pages, data.current_page);
        } else {
            showToast('Failed to load history', 'error');
        }
    } catch (error) {
        console.error('Error loading history:', error);
        showToast('Error loading history', 'error');
    } finally {
        hideLoading();
    }
}

// Display history items
function displayHistory(items) {
    const grid = document.getElementById('historyGrid');
    
    if (!items || items.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <h3>No summaries found</h3>
                <p>Start creating summaries to see them here!</p>
                <a href="/" class="btn btn-primary" style="margin-top: 20px;">
                    <i class="fas fa-plus"></i> Create Summary
                </a>
            </div>
        `;
        return;
    }
    
    grid.innerHTML = items.map(item => createHistoryItemHTML(item)).join('');
}

// Create HTML for history item
function createHistoryItemHTML(item) {
    const date = new Date(item.created_at);
    const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    const isFavorite = item.is_favorite;
    
    return `
        <div class="history-item" data-id="${item.id}">
            <div class="history-item-header">
                <div class="history-item-title">
                    <h3>${item.title || 'Untitled Summary'}</h3>
                    <div class="history-item-meta">
                        <span><i class="fas fa-calendar"></i> ${formattedDate}</span>
                        <span><i class="fas fa-font"></i> ${item.original_word_count} words</span>
                        <span><i class="fas fa-compress"></i> ${item.compression_ratio}% compressed</span>
                        ${item.file_type ? `<span><i class="fas fa-file"></i> ${item.file_type.toUpperCase()}</span>` : ''}
                        ${item.language_name ? `<span><i class="fas fa-language"></i> ${item.language_name}</span>` : ''}
                    </div>
                </div>
                <div class="history-item-actions">
                    <button class="action-btn btn-view" onclick="viewDetails(${item.id})" title="View Details">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="action-btn btn-favorite ${isFavorite ? 'active' : ''}" onclick="toggleFavorite(${item.id}, event)" title="Toggle Favorite">
                        <i class="fas fa-star"></i>
                    </button>
                    <button class="action-btn btn-delete" onclick="deleteHistory(${item.id}, event)" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            <div class="history-item-preview">
                ${item.summary_text.substring(0, 200)}${item.summary_text.length > 200 ? '...' : ''}
            </div>
            ${item.tags && item.tags.length > 0 ? `
                <div class="history-item-tags">
                    ${item.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                </div>
            ` : ''}
        </div>
    `;
}

// View details
async function viewDetails(id) {
    showLoading();
    
    try {
        const response = await fetch(`/api/history/${id}`);
        const data = await response.json();
        
        if (data.success) {
            showDetailModal(data.summary);
        } else {
            showToast('Failed to load details', 'error');
        }
    } catch (error) {
        console.error('Error loading details:', error);
        showToast('Error loading details', 'error');
    } finally {
        hideLoading();
    }
}

// Show detail modal
function showDetailModal(summary) {
    const modal = document.getElementById('detailModal');
    const modalBody = document.getElementById('modalBody');
    
    document.getElementById('modalTitle').textContent = summary.title || 'Summary Details';
    
    modalBody.innerHTML = `
        <div class="modal-section">
            <h3><i class="fas fa-info-circle"></i> Summary Information</h3>
            <p><strong>Created:</strong> ${new Date(summary.created_at).toLocaleString()}</p>
            <p><strong>Original Words:</strong> ${summary.original_word_count}</p>
            <p><strong>Summary Words:</strong> ${summary.summary_word_count}</p>
            <p><strong>Compression:</strong> ${summary.compression_ratio}%</p>
            ${summary.language_name ? `<p><strong>Language:</strong> ${summary.language_name}</p>` : ''}
            ${summary.filename ? `<p><strong>File:</strong> ${summary.filename}</p>` : ''}
        </div>
        
        <div class="modal-section">
            <h3><i class="fas fa-align-left"></i> Summary</h3>
            <p>${summary.summary_text}</p>
        </div>
        
        ${summary.key_points && summary.key_points.length > 0 ? `
            <div class="modal-section">
                <h3><i class="fas fa-list-ul"></i> Key Points</h3>
                <ul>
                    ${summary.key_points.map(point => `<li>${point}</li>`).join('')}
                </ul>
            </div>
        ` : ''}
        
        <div class="modal-section">
            <h3><i class="fas fa-file-alt"></i> Original Text (Preview)</h3>
            <p>${summary.original_text}</p>
        </div>
        
        <div style="display: flex; gap: 10px; margin-top: 20px;">
            <button class="btn btn-primary" onclick="copyToClipboard('${summary.id}', 'summary')">
                <i class="fas fa-copy"></i> Copy Summary
            </button>
            <button class="btn btn-secondary" onclick="downloadSummary(${summary.id})">
                <i class="fas fa-download"></i> Download
            </button>
        </div>
    `;
    
    modal.classList.add('show');
}

// Close modal
function closeModal() {
    document.getElementById('detailModal').classList.remove('show');
}

// Toggle favorite
async function toggleFavorite(id, event) {
    event.stopPropagation();
    
    try {
        const response = await fetch(`/api/history/${id}/favorite`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(data.is_favorite ? 'Added to favorites' : 'Removed from favorites', 'success');
            loadHistory(); // Reload to update UI
        } else {
            showToast('Failed to update favorite', 'error');
        }
    } catch (error) {
        console.error('Error toggling favorite:', error);
        showToast('Error updating favorite', 'error');
    }
}

// Delete history item
async function deleteHistory(id, event) {
    event.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this summary?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/history/${id}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Summary deleted', 'success');
            loadHistory(); // Reload to update UI
        } else {
            showToast('Failed to delete summary', 'error');
        }
    } catch (error) {
        console.error('Error deleting history:', error);
        showToast('Error deleting summary', 'error');
    }
}

// Search history
function searchHistory() {
    currentSearch = document.getElementById('searchInput').value;
    currentPage = 1;
    loadHistory();
}

// Filter and display
function filterAndDisplay() {
    let filtered = [...allHistory];
    
    switch(currentFilter) {
        case 'favorites':
            filtered = filtered.filter(item => item.is_favorite);
            break;
        case 'today':
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            filtered = filtered.filter(item => new Date(item.created_at) >= today);
            break;
        case 'week':
            const weekAgo = new Date();
            weekAgo.setDate(weekAgo.getDate() - 7);
            filtered = filtered.filter(item => new Date(item.created_at) >= weekAgo);
            break;
        case 'month':
            const monthAgo = new Date();
            monthAgo.setMonth(monthAgo.getMonth() - 1);
            filtered = filtered.filter(item => new Date(item.created_at) >= monthAgo);
            break;
    }
    
    displayHistory(filtered);
}

// Update statistics
function updateStatistics() {
    const total = allHistory.length;
    const favorites = allHistory.filter(item => item.is_favorite).length;
    const totalWords = allHistory.reduce((sum, item) => sum + (item.original_word_count || 0), 0);
    
    const monthAgo = new Date();
    monthAgo.setMonth(monthAgo.getMonth() - 1);
    const thisMonth = allHistory.filter(item => new Date(item.created_at) >= monthAgo).length;
    
    document.getElementById('totalSummaries').textContent = total;
    document.getElementById('favoriteSummaries').textContent = favorites;
    document.getElementById('totalWords').textContent = totalWords.toLocaleString();
    document.getElementById('thisMonth').textContent = thisMonth;
}

// Setup pagination
function setupPagination(total, totalPages, currentPageNum) {
    const pagination = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Previous button
    html += `<button ${currentPageNum === 1 ? 'disabled' : ''} onclick="changePage(${currentPageNum - 1})">
        <i class="fas fa-chevron-left"></i> Previous
    </button>`;
    
    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= currentPageNum - 2 && i <= currentPageNum + 2)) {
            html += `<button class="${i === currentPageNum ? 'active' : ''}" onclick="changePage(${i})">${i}</button>`;
        } else if (i === currentPageNum - 3 || i === currentPageNum + 3) {
            html += `<button disabled>...</button>`;
        }
    }
    
    // Next button
    html += `<button ${currentPageNum === totalPages ? 'disabled' : ''} onclick="changePage(${currentPageNum + 1})">
        Next <i class="fas fa-chevron-right"></i>
    </button>`;
    
    pagination.innerHTML = html;
}

// Change page
function changePage(page) {
    currentPage = page;
    loadHistory();
}

// Copy to clipboard
async function copyToClipboard(id, type) {
    try {
        const response = await fetch(`/api/history/${id}`);
        const data = await response.json();
        
        if (data.success) {
            const text = type === 'summary' ? data.summary.summary_text : data.summary.original_text;
            await navigator.clipboard.writeText(text);
            showToast('Copied to clipboard!', 'success');
        }
    } catch (error) {
        console.error('Error copying:', error);
        showToast('Failed to copy', 'error');
    }
}

// Download summary
function downloadSummary(id) {
    // Implement download functionality
    showToast('Download feature coming soon!', 'info');
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

// Close modal when clicking outside
document.getElementById('detailModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeModal();
    }
});

// Search on enter key
document.getElementById('searchInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        searchHistory();
    }
});