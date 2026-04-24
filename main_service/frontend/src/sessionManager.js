// src/sessionManager.js

let sessionFrames = [];
let isDirty = false;

export function addFrameToSession(frame) {
    sessionFrames.push(frame);
    isDirty = true;
    updateStatusDisplay();
}

export function getSessionFrames() {
    return sessionFrames;
}

export function clearSession() {
    sessionFrames = [];
    isDirty = false;
    updateStatusDisplay();
}

export function hasUnsavedFrames() {
    return isDirty && sessionFrames.length > 0;
}

function updateStatusDisplay() {
    const countBadge = document.getElementById('frame-count');
    if (countBadge) {
        countBadge.textContent = `${sessionFrames.length} captured`;
    }
}

/**
 * Uploads frames in chunks of 'batchSize' to the FastAPI backend.
 */
export async function uploadSession(onProgress) {
    const batchSize = 20;
    const total = sessionFrames.length;
    let processed = 0;

    for (let i = 0; i < total; i += batchSize) {
        const chunk = sessionFrames.slice(i, i + batchSize);
        const payload = {
            frames: chunk
        };

        try {
            // Pointing to main_service backend (port 8001)
            const response = await fetch("http://103.219.61.73/wrams_video/api/frames/batch", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || "Batch upload failed");
            }

            processed += chunk.length;
            if (onProgress) onProgress(processed, total);
        } catch (error) {
            console.error("Upload error at chunk", i, error);
            throw error;
        }
    }

    isDirty = false;
    return true;
}
