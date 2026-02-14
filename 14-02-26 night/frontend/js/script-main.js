let currentView = 'grid';
let selectedFiles = new Set();
let detailsPanelOpen = false;
let detailsPanelautoOpen = false;
let files = null;
let fs_state = 'ideal';
let cutcopy = new Set();
let quickAccess = null;
let quickActive = null;


async function Unpin() {
    await window.pywebview.api.unpin_to_quick(quickActive)
    refresh();

}
async function pin() {
    if (selectedFiles.size === 1) {
        const index = Array.from(selectedFiles)[0];
        await window.pywebview.api.pin_to_quick(files[index].path)
        refresh();
    } else if (selectedFiles.size === 0) {
        alert('Please select a file to rename.');
    } else {
        alert('Please select only one file to rename.');
    }

}
async function openFileQuick() {
    if (quickActive) {
        await navigateToBreadcrumb(null, quickActive)
    }

}

async function refresh() {
    setTimeout(() => {

    }, 1);
    files = await window.pywebview.api.show_list();
    quickAccess = await window.pywebview.api.get_quick();
    // await addressButton();
    await updateBreadcrumbButtons();
    console.log(files);
    fs_state = 'ideal';
    cutcopy.clear();
    selectedFiles.clear();
    await renderFiles();
    renderQuick();
    await updateDetailsPanel();
}

function renderQuick() {
    console.log(quickAccess);
    const sidepanel = document.getElementById('sidebar-quick-access');
    sidepanel.innerHTML = `<div class="sidebar-title">Quick Access</div>`;
    quickAccess.forEach(tuple => {
        const d = document.createElement('div');
        d.className = "sidebar-item" + `${quickActive == tuple[1] ? " active" : ""} `
        d.onclick = (e) => navigateToBreadcrumb(e, tuple[1]);
        d.oncontextmenu = (e) => contextMenuQuickAccess(e, tuple[0], tuple[1]);
        d.innerHTML = `<span class="sidebar-icon">🏠</span>
                        <span>${tuple[0]}</span>`;
        sidepanel.appendChild(d);

    })



}
async function openSearchWindow() {
    await window.pywebview.api.open_search()
}

// Show input field when breadcrumb is clicked
async function showBreadcrumbInput() {
    const input = document.getElementById('breadcrumbInput');
    const buttons = document.getElementById('breadcrumbButtons');

    // Set input value to current path
    const cwd = await window.pywebview.api.get_cwd();
    input.value = cwd;

    // Toggle visibility
    buttons.style.display = 'none';
    input.style.display = 'block';
    input.focus();
    input.select();
}

// Hide input and show buttons
async function hideBreadcrumbInput() {
    const input = document.getElementById('breadcrumbInput');
    const buttons = document.getElementById('breadcrumbButtons');

    // Parse the input value and update path
    const data = await window.pywebview.api.go_to_address(input.value);
    if (!data.isdone) {
        alert(data.msg);
    } else {

        await refresh();
    }

    // Toggle visibility
    setTimeout(() => {
        input.style.display = 'none';
        buttons.style.display = 'flex';
    }, 200);
}

// Handle Enter and Escape keys
function handleBreadcrumbKeydown(event) {
    if (event.key === 'Enter') {
        hideBreadcrumbInput();

    } else if (event.key === 'Escape') {
        // document.getElementById('breadcrumbInput').value = currentPath.join(' > ');
        hideBreadcrumbInput();
    }
}

// Update breadcrumb buttons from currentPath array
async function updateBreadcrumbButtons() {
    const data = await window.pywebview.api.path_breaker();
    const cwd = await window.pywebview.api.get_cwd();
    const keys = Object.keys(data);
    const buttonsContainer = document.getElementById('breadcrumbButtons');
    buttonsContainer.innerHTML = '';

    keys.forEach((filename, index) => {
        // Create breadcrumb item
        const item = document.createElement('span');
        item.className = 'breadcrumb-item';
        item.textContent = filename === "HOME" ? `🏠 ${filename}` : filename;
        item.onclick = (e) => navigateToBreadcrumb(e, data[filename]);
        buttonsContainer.appendChild(item);

        // Add separator if not last item
        if (index < keys.length - 1) {
            const separator = document.createElement('span');
            separator.className = 'breadcrumb-separator';
            separator.textContent = '›';
            buttonsContainer.appendChild(separator);
        }
    });
}


// Navigate to a specific breadcrumb level
// async function updateFiles(show_list) {
//     files = show_list;
//     await renderFiles();
// }
async function navigateToBreadcrumb(event, path) {
    if (event) {

        event.stopPropagation();
    }
    console.log(path)
    const data = await window.pywebview.api.go_to_address(path);
    if (!data.isdone) {
        alert(data.msg);

    } else {
        quickActive = path;
    }
    await refresh();
    console.log('Navigated to:', path);
}

// Updated file rendering with separate click handlers for icon and name

let renamingIndex = null;

function renderFiles() {
    if (currentView === 'list') {
        gridContent.className = 'grid-content list-view';
        gridHeader.style.display = 'grid';
        gridContent.innerHTML = files.map((file, index) => `
            <div class="file-item-list ${selectedFiles.has(index) ? 'selected' : ''} ${cutcopy.has(index) ? fs_state : ''} ${file.islock ? 'lock' : ''}" 
                 onclick="selectFile(${index}, event)" 
                 oncontextmenu="showContextMenuItems(event, ${index})">
                <div class="file-info">
                    <div class="file-icon-list" ondblclick="openFileHandler('${file.name}')">${file.icon}</div>
                    <div class="file-details">
                        <div class="file-name-wrapper">
                            <div class="file-name" 
                                 id="fileName-${index}"
                                 onclick="handleNameClick(event, ${index})"
                                 ondblclick="startRename(event, ${index})">${file.name}</div>
                            <input class="file-name-input" 
                                   id="fileNameInput-${index}"
                                   type="text" 
                                   value="${file.name}"
                                   style="display: none;"
                                 onclick="event.stopPropagation()"
                                   onkeydown="handleRenameKeydown(event, ${index})" >
                        </div>
                        <div class="file-type">${file.type == 'd' ? "folder" : "file"}</div>
                    </div>
                </div>
                <div class="file-size">${file.size}</div>
                <div class="file-date">${file.mdate}</div>
                <div class="file-typeD">${file.filetype}</div>
                <div class="file-state file-indicator-grid">${file.indicator}</div>
            </div>
        `).join('');
    } else {
        gridContent.className = 'grid-content grid-view';
        gridHeader.style.display = 'none';
        gridContent.innerHTML = files.map((file, index) => `
            <div class="file-item-grid ${selectedFiles.has(index) ? 'selected' : ''} ${cutcopy.has(index) ? fs_state : ''} ${file.islock ? 'lock' : ''}" 
                 onclick="selectFile(${index}, event)" 
                 oncontextmenu="showContextMenuItems(event, ${index})">
                <div class="file-icon-grid-div" ondblclick="openFileHandler('${file.name}')">
                    <div></div>
                    <div class="file-icon-grid">${file.icon}</div>
                    <div class="file-indicator-grid">${file.indicator}</div>
                </div>
                <div class="file-name-grid-wrapper">
                    <div class="file-name-grid" 
                         id="fileName-${index}"
                         onclick="handleNameClick(event, ${index})"
                         ondblclick="startRename(event, ${index})">${file.name}</div>
                    <input class="file-name-input-grid" 
                           id="fileNameInput-${index}"
                           type="text" 
                           value="${file.name}"
                           style="display: none;"
                             onclick="event.stopPropagation()"
                           onkeydown="handleRenameKeydown(event, ${index})">
                </div>
            </div>
        `).join('');
    }
    updateDetailsPanel()
}

let clickTimer = null;
let clickCount = 0;
// Handle single click on name (for selection or rename activation)

function handleNameClick(event, index) {
    event.stopPropagation();
    clickCount++;

    if (clickCount === 1) {
        clickTimer = setTimeout(() => {
            // Single click - just select if already selected and waiting
            if (selectedFiles.has(index)) {
                // File is already selected, prepare for rename on next click
            }
            clickCount = 0;
        }, 300);
    } else if (clickCount === 2) {
        // This is handled by ondblclick
        clearTimeout(clickTimer);
        clickCount = 0;
    }
}

// Start rename mode (double-click on name or F2)
function startRename(event, index) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    // Cancel any pending click timers
    if (clickTimer) {
        clearTimeout(clickTimer);
        clickCount = 0;
    }
    // If already renaming, finish that first
    if (renamingIndex !== null && renamingIndex !== index) {
        closeRename(renamingIndex);
    }

    renamingIndex = index;
    console.log(renamingIndex);
    const nameElement = document.getElementById(`fileName-${index}`);
    const inputElement = document.getElementById(`fileNameInput-${index}`);

    if (nameElement && inputElement) {
        nameElement.style.display = 'none';
        inputElement.style.display = 'block';
        inputElement.focus();

        // Select filename without extension
        const dotIndex = inputElement.value.lastIndexOf('.');
        if (dotIndex > 0) {
            inputElement.setSelectionRange(0, dotIndex);
        } else {
            inputElement.select();
        }
    }
}

// Finish rename and save
async function closeRename(index, save = true) {
    console.log("close start")
    if (renamingIndex === null) return;

    const nameElement = document.getElementById(`fileName-${index}`);
    const inputElement = document.getElementById(`fileNameInput-${index}`);

    if (nameElement && inputElement) {
        const newName = inputElement.value.trim();

        let isdone = await window.pywebview.api.rename(files[index].name, newName);
        console.log(isdone);
        let status_ = isdone.status;
        let msg = isdone.msg;
        if (!status_) {
            alert(msg);
        } else {

            nameElement.innerText = newName;
        }

        // Switch back to display mode
        inputElement.style.display = 'none';
        nameElement.style.display = 'block';
        renamingIndex = null;
        await refresh();
    }
}

// Handle keyboard events during rename
function handleRenameKeydown(event, index) {
    if (event.key === 'Enter') {
        event.preventDefault();
        closeRename(index);
    } else if (event.key === 'Escape') {
        event.preventDefault();
        const inputElement = document.getElementById(`fileNameInput-${index}`);
        const nameElement = document.getElementById(`fileName-${index}`);

        if (inputElement && nameElement) {
            // Restore original name
            inputElement.value = files[index].name;
            inputElement.style.display = 'none';
            nameElement.style.display = 'block';
            renamingIndex = null;
        }
    }
}

// Add F2 key support for rename
document.addEventListener('keydown', function (event) {
    if (event.key === 'F2' && selectedFiles.size === 1) {
        event.preventDefault();
        const index = Array.from(selectedFiles)[0];
        startRename(null, index);
    }
});

// Update the existing renameFile function to use the new rename system
function renameFile() {
    if (selectedFiles.size === 1) {
        const index = Array.from(selectedFiles)[0];
        console.log("start renaming")
        startRename(null, index);
    } else if (selectedFiles.size === 0) {
        alert('Please select a file to rename.');
    } else {
        alert('Please select only one file to rename.');
    }
}
document.addEventListener('click', function (event) {
    if (renamingIndex !== null) {
        const inputElement = document.getElementById(`fileNameInput-${renamingIndex}`);
        const menu = document.getElementById(`contextMenu-items`);
        const details_btn_rename = document.getElementById(`details-btn-rename`);

        if (inputElement && !inputElement.contains(event.target) && !menu.contains(event.target) && !details_btn_rename.contains(event.target)) {
            closeRename(renamingIndex, true);
        }
    }
});
// async function renderFiles() {
//         const gridContent = document.getElementById('gridContent');
//         const gridHeader = document.getElementById('gridHeader');

//         // console.log("data");
//         // console.log(files);
//         console.log(cutcopy);
//         // console.log(files);

//         if (currentView === 'list') {
//             gridContent.className = 'grid-content list-view';
//             gridHeader.style.display = 'grid';
//             gridContent.innerHTML = files.map((file, index) => `
//                         <div class="file-item-list ${selectedFiles.has(index) ? 'selected' : ''} ${cutcopy.has(index) ? fs_state : ''}" 
//                              onclick="selectFile(${index}, event)" 
//                              oncontextmenu="showContextMenu(event, ${index})"
//                              ondblclick="openFileHandler('${file.name}')">
//                             <div class="file-info">
//                                 <div class="file-icon-list">${file.icon}</div>
//                                 <div class="file-details">
//                                     <div class="file-name">${file.name}</div>
//                                     <div class="file-type">${file.type}</div>
//                                 </div>
//                             </div>
//                             <div class="file-size">${file.size}</div>
//                             <div class="file-date">${file.date}</div>
//                             <div class="file-typeD">${file.filetype}</div>
//                             <div class="file-state file-indicator-grid">${file.indicator}</div>
//                         </div>
//                     `).join('');
//         } else {
//             gridContent.className = 'grid-content grid-view';
//             gridHeader.style.display = 'none';
//             gridContent.innerHTML = files.map((file, index) => `
//                        <div class="file-item-grid ${selectedFiles.has(index) ? 'selected' : ''} ${cutcopy.has(index) ? fs_state : ''}" 
//                              onclick="selectFile(${index}, event)" 
//                              oncontextmenu="showContextMenu(event, ${index})"
//                              ondblclick="openFileHandler('${file.name}')">
//                             <div class="file-icon-grid-div">
//                                 <div></div>
//                                <div class="file-icon-grid">${file.icon}</div>
//                                 <div class="file-indicator-grid">${file.indicator}</div>
//                             </div>
//                            <div class="file-name-grid" id="fileName-${index}"
//                                          ondblclick="startRename(event, ${index})">${file.name}</div>
//                            <input class="file-name-input" 
//                                            id="fileNameInput-${index}"
//                                            type="text" 
//                                            value="${file.name}"
//                                            style="display: none;"
//                                            onblur="finishRename(${index})"
//                                            onkeydown="handleRenameKeydown(event, ${index})">
//                         </div>
//             `).join('');
//         }
//     }

// Switch view
function switchView(view) {
    currentView = view;
    document.querySelectorAll('.view-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    renderFiles();
}

async function updateDetailsPanel() {
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
        document.getElementById('detailsTags').innerHTML = "";
    } else {
        // Get first selected file
        const fileIndex = Array.from(selectedFiles)[0];
        const file = files[fileIndex];

        // Update preview
        document.getElementById('detailsIconLarge').innerHTML = file.icon;
        document.getElementById('detailsFileName').textContent = file.name;
        document.getElementById('detailsFileType').textContent = file.type == 'd' ? "folder" : "file";

        // Update general info
        document.getElementById('detailsSize').textContent = file.size;
        document.getElementById('detailsLocation').textContent = file.path;
        document.getElementById('detailsCreated').textContent = file.cdate;
        document.getElementById('detailsModified').textContent = file.mdate;
        // document.getElementById('detailsOwner').textContent = file.owner;
        // mode
        console.log(file.mode);
        document.getElementById("owner-permission").innerText = file.mode.owner.join(" ");
        document.getElementById("group-permission").innerText = file.mode.owner.join(" ");
        document.getElementById("other-permission").innerText = file.mode.owner.join(" ");
        // tags
        console.log(file.tags);
        if (file.tags) {
            document.getElementById('detailsTags').innerHTML = file.tags.map(tag => `
                <div class="details-tag">${tag}</div>
                `).join("");

        } else {
            document.getElementById('detailsTags').innerHTML = "";

        }



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

function toggleDetailsPanel() {
    const panel = document.getElementById('detailsPanel');
    detailsPanelOpen = !detailsPanelOpen;

    if (detailsPanelOpen) {
        panel.classList.add('show');
    } else {
        panel.classList.remove('show');
    }
}


// Select File
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
    if (selectedFiles.size > 0 && !detailsPanelOpen && detailsPanelautoOpen) {
        toggleDetailsPanel();
    }
}

function selectAll() {
    files.forEach((file, index) => {
        selectedFiles.add(index);
    });
    renderFiles();
}

async function openFileHandler(fileName) {
    console.log('Opening:', fileName);
    // alert(`Opening: ${fileName}`);
    await window.pywebview.api.open(fileName);
    refresh();
}
async function goBack() {
    console.log('Going back');
    await window.pywebview.api.backward();
    refresh();
}

async function goForward() {
    console.log('Going forward');
    await window.pywebview.api.forward();
    refresh();
}

async function goUp() {
    console.log('Going up');
    await window.pywebview.api.go_root()
    refresh();
}

function openFile() {
    if (selectedFiles.size > 0) {
        const fileIndex = Array.from(selectedFiles)[0];
        openFileHandler(files[fileIndex].name);
    } else {
        alert('Please select a file first');
    }
}

// function renameFile() {
//     if (selectedFiles.size === 0) {
//         alert('Please select a file first');
//         return;
//     }
//     const fileName = prompt('Enter new name:');
//     if (fileName) {
//         console.log('Renaming to:', fileName);
//         alert(`File renamed to: ${fileName}`);
//     }
// }


async function copyFile() {
    if (selectedFiles.size === 0) {
        alert('Please select a file first');
        return;
    }
    let result = [];
    cutcopy.clear();
    selectedFiles.forEach((index) => {
        let f = files[index];
        result.push(f.name);
        cutcopy.add(index)
    });
    await window.pywebview.api.copy(result);
    fs_state = 'copy';
    await renderFiles();


}
async function cutFile() {
    if (selectedFiles.size === 0) {
        alert('Please select a file first');
        return;
    }
    let result = [];
    cutcopy.clear();
    selectedFiles.forEach((index) => {
        let f = files[index];
        result.push(f.name);
        cutcopy.add(index)
    });
    await window.pywebview.api.cut(result);
    fs_state = 'cut';
    await renderFiles();

}
async function pasteFile() {
    await window.pywebview.api.paste();
    cutcopy.clear();
    fs_state = "ideal"
    refresh();
}


async function deleteFile() {
    if (selectedFiles.size === 0) {
        alert('Please select a file first');
        return;
    }
    if (confirm('Are you sure you want to delete the selected file(s)?')) {

        let result = [];
        selectedFiles.forEach((index) => {
            let f = files[index];
            result.push(f.name);

        });
        await window.pywebview.api.delete(result);
        await refresh();
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

function _get_index(filename) {
    const index = files.findIndex(file => file.name === filename);
    return index; // -1 if not found
}



async function createFolder() {
    let name = await window.pywebview.api.create_folder('New_Folder');
    await refresh();
    const index = _get_index(name);
    if (index !== -1) {
        console.log("Found at", index);
        selectedFiles.clear();
        selectedFiles.add(index);
        renderFiles();
        startRename(null, index);
    }

}
async function createTxt() {
    let name = await window.pywebview.api.create_file('New_File.txt');
    await refresh();
    const index = _get_index(name);
    if (index !== -1) {
        console.log("Found at", index);
        selectedFiles.clear();
        selectedFiles.add(index);
        renderFiles();
        startRename(null, index);
    }
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
async function lockItem() {
    if (selectedFiles.size === 0) {
        alert('Please select a file first');
        return;
    }
    let paths = [];
    selectedFiles.forEach((index) => {
        let f = files[index];
        paths.push(f.path);
    });
    await window.pywebview.api.lock_files(paths);
    console.log("lock");
    await refresh();
}
async function unLockItem() {
    if (selectedFiles.size === 0) {
        alert('Please select a file first');
        return;
    }
    let paths = [];
    selectedFiles.forEach((index) => {
        let f = files[index];
        paths.push(f.path);
    });
    await window.pywebview.api.unlock_files(paths);
    console.log("unlock");
    await refresh();
}

// Context menu
function showContextMenuItems(event, index) {
    const lockbtn = document.getElementById("menu-lockbtn");
    const unlockbtn = document.getElementById("menu-unlockbtn");
    const file = files[index];

    if (file.islock) {
        unlockbtn.style.display = "block";
        lockbtn.style.display = "none";


    } else {
        unlockbtn.style.display = "none";
        lockbtn.style.display = "block";

    }

    event.preventDefault();
    const menu = document.getElementById('contextMenu-items');
    menu.classList.add('show');

    let menu_x = event.pageX;
    let menu_y = event.pageY;
    const window_w = window.innerWidth;
    const window_h = window.innerHeight;
    const menu_w = menu.clientWidth;
    const menu_h = menu.clientHeight;
    const offset = 10;

    const dx = menu_x + menu_w - window_w;
    if (dx > 0) {
        menu_x = menu_x - dx - offset;
    }

    const dy = menu_y + menu_h - window_h;
    if (dy > 0) {
        menu_y = menu_y - dy - offset;
    }

    menu.style.left = menu_x + 'px';
    menu.style.top = menu_y + 'px';

    if (!selectedFiles.has(index)) {
        selectedFiles.clear();
        selectedFiles.add(index);
        renderFiles();
        updateDetailsPanel();
    }
    //  for hide area menu when item menu show
    setTimeout(() => { document.getElementById('contextMenuContentArea').classList.remove('show'); }, 1);
}

// Context menu
function showContextMenuArea(event, index) {
    event.preventDefault();
    const menu = document.getElementById('contextMenuContentArea');
    menu.classList.add('show');
    let menu_x = event.pageX;
    let menu_y = event.pageY;
    const window_w = window.innerWidth;
    const window_h = window.innerHeight;
    const menu_w = menu.clientWidth;
    const menu_h = menu.clientHeight;
    const offset = 10;

    const dx = menu_x + menu_w - window_w;
    if (dx > 0) {
        menu_x = menu_x - dx - offset;
    }

    const dy = menu_y + menu_h - window_h;
    if (dy > 0) {
        menu_y = menu_y - dy - offset;
    }

    menu.style.left = menu_x + 'px';
    menu.style.top = menu_y + 'px';
    console.log("show")


    // if (!selectedFiles.has(index)) {
    //     selectedFiles.clear();
    //     selectedFiles.add(index);
    //     renderFiles();
    //     updateDetailsPanel();
    // }
}
// Context menu
function contextMenuQuickAccess(event, name, path) {
    event.preventDefault();
    const menu = document.getElementById('contextMenuQuickAccess');
    menu.classList.add('show');
    let menu_x = event.pageX;
    let menu_y = event.pageY;
    const window_w = window.innerWidth;
    const window_h = window.innerHeight;
    const menu_w = menu.clientWidth;
    const menu_h = menu.clientHeight;
    const offset = 10;

    const dx = menu_x + menu_w - window_w;
    if (dx > 0) {
        menu_x = menu_x - dx - offset;
    }

    const dy = menu_y + menu_h - window_h;
    if (dy > 0) {
        menu_y = menu_y - dy - offset;
    }

    menu.style.left = menu_x + 'px';
    menu.style.top = menu_y + 'px';
    console.log("show")


    if (quickActive !== path) {
        quickActive = path
        renderQuick();
        // renderFiles();
        // updateDetailsPanel();
    }
}

// Hide context menu
document.addEventListener('click', () => {
    document.getElementById('contextMenu-items').classList.remove('show');
    document.getElementById('contextMenuContentArea').classList.remove('show');
    document.getElementById('contextMenuQuickAccess').classList.remove('show');
});
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
document.addEventListener('keydown', async (e) => {
    // Ctrl+D or Cmd+D - Toggle details panel
    if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
        e.preventDefault();
        toggleDetailsPanel();
    }

    if ((e.ctrlKey || e.metaKey) && e.key === 'c') {
        e.preventDefault();
        await copyFile();
    }
    if ((e.ctrlKey || e.metaKey) && e.key === 'x') {
        e.preventDefault();
        await cutFile();
    }
    if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
        e.preventDefault();
        selectAll();
    }

    // Escape - Close details panel
    if (e.key === 'Escape' && detailsPanelOpen) {
        toggleDetailsPanel();
    }
});
async function copyText(text) {
    await window.pywebview.api.copy_text(text);
}

function closeDupWindow() {
    const dupWindow = document.getElementById("contextMenuDup");
    dupWindow.style.display = "none";
}

async function similarFiles() {
    const index = Array.from(selectedFiles)[0];
    const paths = await window.pywebview.api.find_dup(files[index].path);
    console.log(paths);

    const dupWindow = document.getElementById("contextMenuDup");
    const dupResultContainer = document.getElementById("menu-resultdup");
    dupResultContainer.innerHTML = "";

    // dupResultContainer.innerHTML += paths.paths.map(path => `
    //     <div class="context-item">
    //             <span>${path}</span>
    //             <span><button onclick="copyText(${path})">copy</button></span>
    //         </div>
    //     `).join("");

    dupWindow.style.display = "block";
    paths.paths.forEach(path => {

        const d = document.createElement('div');
        d.className = "context-item"
        const span1 = document.createElement('span');
        span1.innerText = path;
        const span2 = document.createElement('span');
        const copyBtn = document.createElement('button');
        copyBtn.innerText = "Copy"
        copyBtn.onclick = (e) => copyText(path);
        span2.appendChild(copyBtn);
        d.appendChild(span1);
        d.appendChild(span2);
        dupResultContainer.appendChild(d);

    });
}

window.addEventListener("pywebviewready", refresh)