// src/main.js
import { initVideoPlayer } from './videoManager.js';
import { attachSubtitleEvents } from './subtitleHandler.js';
import { setupFrameSnatcher } from './frameSnatcher.js';
import { uploadSession, getSessionFrames, clearSession, hasUnsavedFrames } from './sessionManager.js';

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const videoInput = document.getElementById('video-input');
  const srtInput = document.getElementById('srt-input');
  const videoPlayer = document.getElementById('main-video');
  const subtitleDisplay = document.getElementById('subtitle-display');
  const startBtn = document.getElementById('start-btn');
  const saveSessionBtn = document.getElementById('save-session-btn');
  
  // Modal Elements
  const modal = document.getElementById('review-modal');
  const modalSaveBtn = document.getElementById('modal-save-btn');
  const modalCancelBtn = document.getElementById('modal-cancel-btn');
  const modalFrameCount = document.getElementById('modal-frame-count');
  const progressContainer = document.getElementById('progress-container');
  const progressBarFill = document.getElementById('progress-bar-fill');
  const progressText = document.getElementById('progress-text');
  
  // State
  let objectURL = null;
  let hasVideo = false;
  let hasGPS = false;

  function updateStartButton() {
    startBtn.disabled = !(hasVideo && hasGPS);
    if (!startBtn.disabled) {
      startBtn.textContent = '▶ Start Playback (Ready)';
      startBtn.style.background = '#00c853'; // Make it pop visually
    }
  }

  // 1. Initialize Video File Input
  videoInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
      if (objectURL) URL.revokeObjectURL(objectURL);
      objectURL = URL.createObjectURL(file);
      initVideoPlayer(videoPlayer, objectURL, file.name);
      hasVideo = true;
      updateStartButton();
    }
  });

  // 2. Initialize Subtitle Selection
  srtInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
      attachSubtitleEvents(file, videoPlayer, subtitleDisplay);
      hasGPS = true;
      updateStartButton();
    }
  });

  // Playback initialization lock
  startBtn.addEventListener('click', () => {
    if (hasVideo && hasGPS) {
      videoPlayer.play().catch(console.warn);
      startBtn.textContent = '▶ Playing...';
    }
  });

  // 4. Session Saving Workflow
  saveSessionBtn.addEventListener('click', () => {
    const frames = getSessionFrames();
    if (frames.length === 0) {
      alert("No frames captured yet!");
      return;
    }
    
    // Prepare Modal
    modalFrameCount.textContent = frames.length;
    progressContainer.style.display = 'none';
    modalSaveBtn.style.display = 'inline-block';
    modalCancelBtn.style.display = 'inline-block';
    modal.style.display = 'flex';
  });

  modalCancelBtn.addEventListener('click', () => {
    modal.style.display = 'none';
  });

  modalSaveBtn.addEventListener('click', async () => {
    modalSaveBtn.style.display = 'none';
    modalCancelBtn.style.display = 'none';
    progressContainer.style.display = 'block';

    try {
      await uploadSession((processed, total) => {
        const percent = (processed / total) * 100;
        progressBarFill.style.width = `${percent}%`;
        progressText.textContent = `Saving frames: ${processed} / ${total}`;
      });

      // Cleanup on Success
      alert("Session saved successfully!");
      clearSession();
      modal.style.display = 'none';
    } catch (err) {
      alert("Error saving session. Please try again.");
      modalSaveBtn.style.display = 'inline-block';
      modalCancelBtn.style.display = 'inline-block';
      progressContainer.style.display = 'none';
    }
  });

  // Browser Exit Warning
  window.addEventListener('beforeunload', (e) => {
    if (hasUnsavedFrames()) {
      e.preventDefault();
      e.returnValue = ''; // Required for Chrome
    }
  });

  // 3. Initialize Frame Snatcher System
  setupFrameSnatcher(videoPlayer);
});
