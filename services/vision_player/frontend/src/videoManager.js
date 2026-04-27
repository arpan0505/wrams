// src/videoManager.js
import { hasUnsavedFrames, clearSession } from './sessionManager.js';

export let currentVideoFilename = "unknown_video";

// Automatically detect if the webgis/external app passed 'e_id' in the URL
const urlParams = new URLSearchParams(window.location.search);
const externalEId = urlParams.get('e_id');
export let currentEId = externalEId ? parseInt(externalEId, 10) : 1; 


/**
 * Fetches asset name via the backend proxy (no direct Java API call from frontend).
 * Uses relative URL — works behind any reverse proxy.
 */
async function fetchAssetName(eid) {
    try {
        // Fetch config to get Java API base path
        const cfgResp = await fetch('/api/config');
        const cfg = await cfgResp.json();
        const basePath = cfg.java_api_base_path || '';
        
        const proxyUrl = `/api/java-proxy?path=${encodeURIComponent(`${basePath}/assets?e_id=${eid}`)}`;
        const response = await fetch(proxyUrl);
        const data = await response.json();
        const asset = Array.isArray(data) ? data[0] : (data.content ? data.content[0] : null);
        return asset ? asset.assetName : null;
    } catch (err) {
        console.warn("Could not fetch asset name:", err);
        return null;
    }
}

export async function initVideoPlayer(videoElement, sourceURL, filename) {
  // 1. Destructive action warning 
  if (hasUnsavedFrames()) {
    const proceed = window.confirm("You have unsaved captured frames. Loading a new video will clear this session. Proceed?");
    if (!proceed) return;
    clearSession();
  }

  if (filename) {
    currentVideoFilename = filename;
  }
  
  // Display the determined e_id and try to get the name
  const eidDisplay = document.getElementById('eid-display');
  if (eidDisplay) {
    eidDisplay.textContent = `E_ID: ${currentEId} (Loading...)`;
    const assetName = await fetchAssetName(currentEId);
    if (assetName) {
      eidDisplay.textContent = `Asset: ${assetName} (ID: ${currentEId})`;
    } else {
      eidDisplay.textContent = `E_ID: ${currentEId}`;
    }
  }
  
  videoElement.src = sourceURL;
  videoElement.load();
  
  // Reset UI components when new video is loaded
  const gallery = document.getElementById('frames-gallery');
  gallery.innerHTML = '';
  document.getElementById('frame-count').textContent = '0 frames';
  
  // Custom event so snatcher knows video restarted
  videoElement.dispatchEvent(new Event('videoLoaded'));
}
