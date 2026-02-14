let lastTarget = null;
function switchTab(name) {
    const currentSection = document.getElementById(`${name}-section`)
    if (lastTarget) {
        lastTarget.style.display = 'none';
    }
    lastTarget = currentSection;
    currentSection.style.display = 'block';
}

async function performSearch() {
    const searchText = document.getElementById('searchText').value;
    const fileExtension = document.getElementById('fileExtension').value;
    const substringSearch = document.getElementById('substringSearch').value;
    const searchFor = document.getElementById('searchFor').value;
    const searchWhere = document.getElementById('searchWhere').value;
    // const output = document.getElementById('output').value;
    // const pythonOutput = document.getElementById('pythonOutput').checked;
    const response = await window.pywebview.api.ultra_search(searchFor, searchWhere, searchText, fileExtension, substringSearch);
    console.log(response);
    const resultsList = document.getElementById('resultsList');
    resultsList.innerHTML = '';

    if (!response) {
        resultsList.innerHTML = '<div class="no-results">Please enter a search term, file extension, or substring.</div>';
        return;
    }

    response.forEach((file) => {
        const filename = file.name;
        const fullPath = file.path;
        const fileExt = filename.substring(filename.lastIndexOf('.'));

        // Determine icon based on file extension
        let icon = '📄';
        if (['.js', '.jsx', '.ts', '.tsx'].includes(fileExt)) icon = '📜';
        else if (['.json', '.xml', '.yaml', '.yml'].includes(fileExt)) icon = '📋';
        else if (['.md', '.txt', '.doc', '.docx'].includes(fileExt)) icon = '📝';
        else if (['.png', '.jpg', '.jpeg', '.gif', '.svg'].includes(fileExt)) icon = '🖼️';
        else if (['.py', '.java', '.cpp', '.c'].includes(fileExt)) icon = '💻';
        else if (['.html', '.css'].includes(fileExt)) icon = '🌐';
        else if (['.zip', '.rar', '.7z', '.tar'].includes(fileExt)) icon = '📦';
        else if (['.dll', '.exe', '.app'].includes(fileExt)) icon = '⚙️';

        const d = document.createElement('div');
        d.className = "result-item";
        d.onclick = () => navigateTo(`"${fullPath}"`, this);
        d.innerHTML = ` <div class="result-icon">${icon}</div>
                            <div class="result-content">
                                <div class="result-filename">${filename}</div>
                                <div class="result-path">${fullPath}</div>
                            </div>
                            <div class="result-status">✓ Copied</div>`;
        resultsList.appendChild(d);
    });
}
// }

async function navigateTo(path, element) {
    console.log(path);
    await window.pywebview.api.navigate_to(path);

}

async function duplicates() {
    const resultsList = document.getElementById('resultsList');
    resultsList.innerHTML = '';
    const data = await window.pywebview.api.get_duplicates();
    console.log(data);
    data.forEach(lst => {
        lst.forEach((file) => {
            const d = document.createElement('div');
            d.className = "result-item";
            d.onclick = () => navigateTo(`"${file[1]}"`, this);

            d.innerHTML = ` <div class="result-icon">${"icon"}</div>
                            <div class="result-content">
                                <div class="result-filename">${file[0]}</div>
                                <div class="result-path">${file[1]}</div>
                            </div>
                            <div class="result-status">✓ Copied</div>`;
            resultsList.appendChild(d);
        })
        const b = document.createElement('div');
        b.className = "seperator";
        resultsList.appendChild(b);
    })

}
async function tagsSearch() {
    const tagsentry = document.getElementById("tagsEntry");
    const resultsList = document.getElementById('resultsList');
    resultsList.innerHTML = '';

    const data = await window.pywebview.api.tag_search(tagsentry.value);
    console.log(data);
    data.forEach(file => {

        const d = document.createElement('div');
        d.className = "result-item";
        d.onclick = () => {
            navigateTo(`"${file.path}"`, this);
        };
        d.innerHTML = ` <div class="result-icon">${"icon"}</div>
                            <div class="result-content">
                                <div class="result-filename">${file.name}</div>
                                <div class="result-path">${file.path}</div>
                            </div>
                            <div class="result-status">✓ Copied</div>`;
        resultsList.appendChild(d);

    })



}

// Allow Enter key to trigger search
document.addEventListener('DOMContentLoaded', async function () {
    document.getElementById('searchText').addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
    document.getElementById('fileExtension').addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
    document.getElementById('substringSearch').addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    const cwd_field = document.getElementById('cwd-field');
    const cwd_path = await window.pywebview.api.get_cwd();
    cwd_field.innerText = cwd_path;

});
