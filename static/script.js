async function fetchVideo() {
    const urlInput = document.getElementById('videoUrl');
    const downloadBtn = document.getElementById('downloadBtn');
    const errorMsg = document.getElementById('errorMsg');
    const errorText = document.getElementById('errorText');
    const videoResult = document.getElementById('videoResult');
    const thumbImg = document.getElementById('thumbImg');
    const videoTitle = document.getElementById('videoTitle');
    const saveBtn = document.getElementById('saveBtn');

    if (!urlInput) return;
    const url = urlInput.value.trim();

    if (!url) {
        if (errorText && errorMsg) {
            errorText.textContent = 'Please paste a valid video URL.';
            errorMsg.style.display = 'flex';
        }
        return;
    }

    if (errorMsg) errorMsg.style.display = 'none';
    if (videoResult) videoResult.style.display = 'none';

    const originalBtnText = downloadBtn.innerHTML;
    downloadBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
    downloadBtn.disabled = true;

    try {
        const response = await fetch('/get-video', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url: url })
        });

        const data = await response.json();

        if (response.ok && data.download_url) {
            if (thumbImg) thumbImg.src = data.thumbnail || '';
            if (videoTitle) videoTitle.textContent = data.title || 'Ready to Download';
            if (saveBtn) {
                saveBtn.href = `/download-file?url=${encodeURIComponent(data.download_url)}`;
            }
            if (videoResult) videoResult.style.display = 'flex';
        } else {
            if (errorText && errorMsg) {
                errorText.textContent = data.error || 'Could not fetch this video. Please verify the link.';
                errorMsg.style.display = 'flex';
            }
        }
    } catch (err) {
        if (errorText && errorMsg) {
            errorText.textContent = 'Server connection error. Please try again.';
            errorMsg.style.display = 'flex';
        }
    } finally {
        downloadBtn.innerHTML = originalBtnText;
        downloadBtn.disabled = false;
    }
}
