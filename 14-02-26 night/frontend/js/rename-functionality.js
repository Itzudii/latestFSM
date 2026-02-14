// Updated file rendering with separate click handlers for icon and name

let renamingIndex = null;

function renderFiles() {
    if (currentView === 'list') {
        gridContent.className = 'grid-content list-view';
        gridHeader.style.display = 'grid';
        gridContent.innerHTML = files.map((file, index) => `
            <div class="file-item-list ${selectedFiles.has(index) ? 'selected' : ''} ${cutcopy.has(index) ? fs_state : ''}" 
                 onclick="selectFile(${index}, event)" 
                 oncontextmenu="showContextMenu(event, ${index})">
                <div class="file-info">
                    <div class="file-icon-list" ondblclick="openFileHandler('${file.name}', ${index})">${file.icon}</div>
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
                        <div class="file-type">${file.type}</div>
                    </div>
                </div>
                <div class="file-size">${file.size}</div>
                <div class="file-date">${file.date}</div>
                <div class="file-typeD">${file.filetype}</div>
                <div class="file-state file-indicator-grid">${file.indicator}</div>
            </div>
        `).join('');
    } else {
        gridContent.className = 'grid-content grid-view';
        gridHeader.style.display = 'none';
        gridContent.innerHTML = files.map((file, index) => `
            <div class="file-item-grid ${selectedFiles.has(index) ? 'selected' : ''} ${cutcopy.has(index) ? fs_state : ''}" 
                 onclick="selectFile(${index}, event)" 
                 oncontextmenu="showContextMenu(event, ${index})">
                <div class="file-icon-grid-div" ondblclick="openFileHandler('${file.name}', ${index})">
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
    if (renamingIndex === null) return;
    
    const nameElement = document.getElementById(`fileName-${index}`);
    const inputElement = document.getElementById(`fileNameInput-${index}`);
    
    if (nameElement && inputElement) {
        const newName = inputElement.value.trim();
         
       let isdone = await window.pywebview.api.rename(files[index].name,newName);
       console.log(isdone);
       let status_ = isdone.status;
       let msg = isdone.msg;
        if (!status_) {
            alert(msg);
        }else{

            nameElement.innerText = newName;
        }
        refresh();
        
        // Switch back to display mode
        inputElement.style.display = 'none';
        nameElement.style.display = 'block';
        renamingIndex = null;
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
document.addEventListener('keydown', function(event) {
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
        startRename(null, index);
    } else if (selectedFiles.size === 0) {
        alert('Please select a file to rename.');
    } else {
        alert('Please select only one file to rename.');
    }
}
document.addEventListener('click', function(event) {
    if (renamingIndex !== null) {
        const inputElement = document.getElementById(`fileNameInput-${renamingIndex}`);
        
        if (inputElement && !inputElement.contains(event.target)) {
            closeRename(renamingIndex, true);
        }
    }
});