// src/sessionManager.js
import { getConfig } from './config.js';

let sessionFrames = [];
let isDirty = false;
let totalUploaded = 0;

export function addFrameToSession(frame) {
    sessionFrames.push(frame);
    isDirty = true;
    updateStatusDisplay();
}

export function getSessionFrames() {
    return sessionFrames;
}

export function clearSession() {
    totalUploaded += sessionFrames.length;
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
        countBadge.textContent = `${totalUploaded + sessionFrames.length} captured`;
    }
}

/**
 * Uploads frames in chunks to the FastAPI backend.
 * Upload URL comes from config — works behind any reverse proxy.
 */
export async function uploadSession(onProgress) {
    const config = getConfig();
    const uploadUrl = config.upload_url || '/api/frames/batch';

    const batchSize = 20;
    const total = sessionFrames.length;
    let processed = 0;

    for (let i = 0; i < total; i += batchSize) {
        const chunk = sessionFrames.slice(i, i + batchSize);
        const payload = { frames: chunk };

        try {
            const response = await fetch(uploadUrl, {
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
