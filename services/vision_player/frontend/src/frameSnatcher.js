import { addFrameThumbnail, resetFrameCount } from './uiController.js';
import { currentVideoFilename, currentEId } from './videoManager.js';
import { getCurrentLocation } from './subtitleHandler.js';
import { addFrameToSession } from './sessionManager.js';

export function setupFrameSnatcher(videoElement) {
  const canvas = document.getElementById('processing-canvas');
  const ctx = canvas.getContext('2d');
  
  let lastSnatchedSecond = -0.5;

  videoElement.addEventListener('play', () => {
    canvas.width = videoElement.videoWidth || 640;
    canvas.height = videoElement.videoHeight || 360;
  });
  
  videoElement.addEventListener('timeupdate', () => {
    if (videoElement.paused || videoElement.ended) return;
    const intervalMark = Math.floor(videoElement.currentTime / 0.5) * 0.5;
    
    if (intervalMark !== lastSnatchedSecond) {
      lastSnatchedSecond = intervalMark;
      
      if (videoElement.videoWidth > 0 && canvas.width !== videoElement.videoWidth) {
        canvas.width = videoElement.videoWidth;
        canvas.height = videoElement.videoHeight;
      }
      
      try {
        ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
        const dataURI = canvas.toDataURL('image/jpeg', 0.7); 
        addFrameThumbnail(dataURI, videoElement.currentTime);
        
        const location = getCurrentLocation(videoElement.currentTime);
        if (location) {
          const now = new Date();
          const pad = (n, l = 2) => n.toString().padStart(l, '0');
          const timeStr = `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}_${pad(now.getMilliseconds(), 3)}`;
          
          const frameRecord = {
            latitude: location.latitude,
            longitude: location.longitude,
            e_id: currentEId,
            timestamp: Math.floor(videoElement.currentTime),
            image_base64: dataURI,
            filename: `frame_${timeStr}.jpg`,
            video_filename: currentVideoFilename
          };
          addFrameToSession(frameRecord);
        }
      } catch(e) {
        console.warn("Could not extract frame", e);
      }
    }
  });

  videoElement.addEventListener('videoLoaded', () => {
    lastSnatchedSecond = -0.5;
    resetFrameCount();
  });
}
