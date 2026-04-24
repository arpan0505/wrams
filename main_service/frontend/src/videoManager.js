// src/videoManager.js
import { hasUnsavedFrames, clearSession } from './sessionManager.js';

export let currentVideoFilename = "unknown_video";

// Automatically detect if the webgis/external app passed 'e_id' natively in the URL
const urlParams = new URLSearchParams(window.location.search);
const externalEId = urlParams.get('e_id');
export let currentEId = externalEId ? parseInt(externalEId, 10) : 1; 

export async function initVideoPlayer(videoElement, sourceURL, filename) {
  // 1. Destructive action warning 
  if (hasUnsavedFrames()) {
    const proceed = window.confirm("You have unsaved captured frames. Loading a new video will clear this session. Proceed?");
    if (!proceed) return; // User cancelled
    clearSession(); // Safe to proceed
  }

  if (filename) {
    currentVideoFilename = filename;
  }
  
  // Display the determined e_id above the video
  const eidDisplay = document.getElementById('eid-display');
  if (eidDisplay) {
    eidDisplay.textContent = `E_ID: ${currentEId}`;
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
