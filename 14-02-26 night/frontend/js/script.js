// Sample file data with extended properties
const files = [
    { name: 'Annual Report 2024.pdf', indicator: "sync", type: 'PDF Document', size: '2.4 MB', date: 'Jan 28, 2026', owner: 'You', icon: '📄', isFolder: false, created: 'Jan 15, 2026', accessed: 'Jan 30, 2026', path: '/Documents/Projects' },
    { name: 'Project Designs', indicator: "sync", type: 'Folder', size: '156 MB', date: 'Jan 27, 2026', owner: 'You', icon: '📁', isFolder: true, created: 'Dec 10, 2025', accessed: 'Jan 30, 2026', path: '/Documents/Projects', itemCount: '42 files, 8 folders' },
    { name: 'Presentation.pptx', indicator: "sync", type: 'PowerPoint', size: '8.7 MB', date: 'Jan 26, 2026', owner: 'You', icon: '📊', isFolder: false, created: 'Jan 20, 2026', accessed: 'Jan 29, 2026', path: '/Documents/Projects' },
    { name: 'Budget_Q1.xlsx', indicator: "sync", type: 'Excel', size: '1.2 MB', date: 'Jan 25, 2026', owner: 'Sarah', icon: '📈', isFolder: false, created: 'Jan 10, 2026', accessed: 'Jan 28, 2026', path: '/Documents/Projects' },
    { name: 'Team Photo.jpg', indicator: "sync", type: 'Image', size: '4.8 MB', date: 'Jan 24, 2026', owner: 'You', icon: '🖼️', isFolder: false, created: 'Jan 24, 2026', accessed: 'Jan 30, 2026', path: '/Documents/Projects' },
    { name: 'Meeting Notes', indicator: "sync", type: 'Folder', size: '42 MB', date: 'Jan 23, 2026', owner: 'You', icon: '📁', isFolder: true, created: 'Jan 5, 2026', accessed: 'Jan 29, 2026', path: '/Documents/Projects', itemCount: '18 files, 3 folders' },
    { name: 'Contract.docx', indicator: "sync", type: 'Word Document', size: '892 KB', date: 'Jan 22, 2026', owner: 'Legal', icon: '📝', isFolder: false, created: 'Jan 18, 2026', accessed: 'Jan 27, 2026', path: '/Documents/Projects' },
    { name: 'Marketing Assets', indicator: "sync", type: 'Folder', size: '234 MB', date: 'Jan 20, 2026', owner: 'Marketing', icon: '📁', isFolder: true, created: 'Dec 15, 2025', accessed: 'Jan 30, 2026', path: '/Documents/Projects', itemCount: '67 files, 12 folders' },
    { name: 'Marketing Assets', indicator: "sync", type: 'Folder', size: '234 MB', date: 'Jan 20, 2026', owner: 'Marketing', icon: '📁', isFolder: true, created: 'Dec 15, 2025', accessed: 'Jan 30, 2026', path: '/Documents/Projects', itemCount: '67 files, 12 folders' },
];

let currentView = 'grid';
let selectedFiles = new Set();
let detailsPanelOpen = false;

// Initialize
function init() {
    renderFiles();
    updateDetailsPanel();
}

// Render files
function renderFiles() {
    const gridContent = document.getElementById('gridContent');
    const gridHeader = document.getElementById('gridHeader');

    if (currentView === 'list') {
        gridContent.className = 'grid-content list-view';
        gridHeader.style.display = 'grid';
        gridContent.innerHTML = files.map((file, index) => `
                    <div class="file-item-list ${selectedFiles.has(index) ? 'selected' : ''}" 
                         onclick="selectFile(${index}, event)" 
                         oncontextmenu="showContextMenu(event, ${index})"
                         ondblclick="openFileHandler('${file.name}')">
                        <div class="file-info">
                            <div class="file-icon-list">${file.icon}</div>
                            <div class="file-details">
                                <div class="file-name">${file.name}</div>
                                <div class="file-type">${file.type}</div>
                            </div>
                        </div>
                        <div class="file-size">${file.size}</div>
                        <div class="file-date">${file.date}</div>
                        <div class="file-owner">${file.owner}</div>
                        <div class="file-state file-indicator-grid">🟢</div>
                    </div>
                `).join('');
    } else {
        gridContent.className = 'grid-content grid-view';
        gridHeader.style.display = 'none';
        gridContent.innerHTML = files.map((file, index) => `
                   <div class="file-item-grid ${selectedFiles.has(index) ? 'selected' : ''}" 
                         onclick="selectFile(${index}, event)" 
                         oncontextmenu="showContextMenu(event, ${index})"
                         ondblclick="openFileHandler('${file.name}')">
    <div class="file-icon-grid-div">
        <div></div>
       <div class="file-icon-grid">${file.icon}</div>
        <div class="file-indicator-grid">${file.indicator}</div>
    </div>
   <div class="file-name-grid">${file.name}</div>
</div>
                `).join('');
        // gridContent.innerHTML = files.map((file, index) => `
        //     <div class="file-item-grid ${selectedFiles.has(index) ? 'selected' : ''}" 
        //          onclick="selectFile(${index}, event)" 
        //          oncontextmenu="showContextMenu(event, ${index})"
        //          ondblclick="openFileHandler('${file.name}')">
        //         <div class="file-icon-grid">${file.icon}</div>
        //         <div class="file-name-grid">${file.name}</div>
        //     </div>
        // `).join('');
    }
}

// Switch view
function switchView(view) {
    currentView = view;
    document.querySelectorAll('.view-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    renderFiles();
}

// Select file
function selectFile(index, event) {
    if (event.ctrlKey || event.metaKey) {
        if (selectedFiles.has(index)) {
            selectedFiles.delete(index);
        } else {
            selectedFiles.add(index);
        }
    } else {
        selectedFiles.clear();
        selectedFiles.add(index);
    }
    renderFiles();
    updateDetailsPanel();

    // Auto-open details panel if a file is selected
    if (selectedFiles.size > 0 && !detailsPanelOpen) {
        toggleDetailsPanel();
    }
}

// Update details panel
function updateDetailsPanel() {
    if (selectedFiles.size === 0) {
        // No file selected
        document.getElementById('detailsIconLarge').textContent = '📄';
        document.getElementById('detailsFileName').textContent = 'Select a file';
        document.getElementById('detailsFileType').textContent = 'No file selected';
        document.getElementById('detailsSize').textContent = '-';
        document.getElementById('detailsLocation').textContent = '-';
        document.getElementById('detailsCreated').textContent = '-';
        document.getElementById('detailsModified').textContent = '-';
        document.getElementById('detailsOwner').textContent = '-';
        document.getElementById('detailsStorageSection').style.display = 'none';
    } else {
        // Get first selected file
        const fileIndex = Array.from(selectedFiles)[0];
        const file = files[fileIndex];

        // Update preview
        document.getElementById('detailsIconLarge').textContent = file.icon;
        document.getElementById('detailsFileName').textContent = file.name;
        document.getElementById('detailsFileType').textContent = file.type;

        // Update general info
        document.getElementById('detailsSize').textContent = file.size;
        document.getElementById('detailsLocation').textContent = file.path;
        document.getElementById('detailsCreated').textContent = file.created;
        document.getElementById('detailsModified').textContent = file.date;
        document.getElementById('detailsOwner').textContent = file.owner;

        // Show/hide storage section for folders
        const storageSection = document.getElementById('detailsStorageSection');
        if (file.isFolder) {
            storageSection.style.display = 'block';
            document.getElementById('detailsTotalSize').textContent = file.size;
            document.getElementById('detailsItemCount').textContent = file.itemCount || '-';

            // Random progress for demo
            const progress = Math.floor(Math.random() * 40 + 50);
            document.getElementById('detailsProgressBar').style.width = progress + '%';
        } else {
            storageSection.style.display = 'none';
        }
    }
}

// Toggle details panel
function toggleDetailsPanel() {
    const panel = document.getElementById('detailsPanel');
    detailsPanelOpen = !detailsPanelOpen;

    if (detailsPanelOpen) {
        panel.classList.add('show');
    } else {
        panel.classList.remove('show');
    }
}

// Context menu
function showContextMenu(event, index) {
    event.preventDefault();
    const menu = document.getElementById('contextMenu');
    menu.style.left = event.pageX + 'px';
    menu.style.top = event.pageY + 'px';
    menu.classList.add('show');

    if (!selectedFiles.has(index)) {
        selectedFiles.clear();
        selectedFiles.add(index);
        renderFiles();
        updateDetailsPanel();
    }
}

// Hide context menu
document.addEventListener('click', () => {
    document.getElementById('contextMenu').classList.remove('show');
});

// Navigation functions
function navigateTo(location) {
    document.querySelectorAll('.sidebar-item').forEach(item => item.classList.remove('active'));
    event.target.closest('.sidebar-item')?.classList.add('active');
    console.log('Navigating to:', location);
}

function goBack() {
    console.log('Going back');
}

function goForward() {
    console.log('Going forward');
}

function goUp() {
    console.log('Going up');
}

function refresh() {
    renderFiles();
    console.log('Refreshing...');
}

// File operations
function openFileHandler(fileName) {
    console.log('Opening:', fileName);
    alert(`Opening: ${fileName}`);
}

function openFile() {
    if (selectedFiles.size > 0) {
        const fileIndex = Array.from(selectedFiles)[0];
        openFileHandler(files[fileIndex].name);
    } else {
        alert('Please select a file first');
    }
}

function renameFile() {
    if (selectedFiles.size === 0) {
        alert('Please select a file first');
        return;
    }
    const fileName = prompt('Enter new name:');
    if (fileName) {
        console.log('Renaming to:', fileName);
        alert(`File renamed to: ${fileName}`);
    }
}

function copyFile() {
    if (selectedFiles.size === 0) {
        alert('Please select a file first');
        return;
    }
    console.log('Copying file');
    alert('File(s) copied to clipboard');
}

function cutFile() {
    if (selectedFiles.size === 0) {
        alert('Please select a file first');
        return;
    }
    console.log('Cutting file');
    alert('File(s) cut to clipboard');
}

function deleteFile() {
    if (selectedFiles.size === 0) {
        alert('Please select a file first');
        return;
    }
    if (confirm('Are you sure you want to delete the selected file(s)?')) {
        console.log('Deleting file');
        alert('File(s) moved to trash');
    }
}

function shareFile() {
    if (selectedFiles.size === 0) {
        alert('Please select a file first');
        return;
    }
    console.log('Sharing file');
    alert('Share dialog opened');
}

function showNewFileDialog() {
    const fileName = prompt('Enter file name:');
    if (fileName) {
        console.log('Creating new file:', fileName);
        alert(`Created: ${fileName}`);
    }
}

function pasteFile() {
    console.log('Pasting file');
    alert('File(s) pasted');
}

function exitApp() {
    if (confirm('Are you sure you want to exit?')) {
        console.log('Exiting application');
        alert('Application closed');
    }
}

// Search function
function searchFiles(query) {
    console.log('Searching for:', query);
}

// Menu functions
let currentOpenMenu = null;

function openMenu(menuItem) {
    if (currentOpenMenu && currentOpenMenu !== menuItem) {
        currentOpenMenu.classList.remove('active');
    }
    menuItem.classList.add('active');
    currentOpenMenu = menuItem;
}

function closeMenu(menuItem) {
    setTimeout(() => {
        if (!menuItem.matches(':hover')) {
            menuItem.classList.remove('active');
            if (currentOpenMenu === menuItem) {
                currentOpenMenu = null;
            }
        }
    }, 100);
}

// Close menus when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.menu-item')) {
        document.querySelectorAll('.menu-item').forEach(item => {
            item.classList.remove('active');
        });
        currentOpenMenu = null;
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl+D or Cmd+D - Toggle details panel
    if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
        e.preventDefault();
        toggleDetailsPanel();
    }

    // Escape - Close details panel
    if (e.key === 'Escape' && detailsPanelOpen) {
        toggleDetailsPanel();
    }
});

// Initialize on load
document.addEventListener("DOMContentLoaded",init)
