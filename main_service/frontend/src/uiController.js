// src/uiController.js

const gallery = document.getElementById('frames-gallery');
const countBadge = document.getElementById('frame-count');
let framesSnatched = 0;

export function addFrameThumbnail(dataURI, timestamp) {
  framesSnatched++;
  
  if (framesSnatched === 1) {
    gallery.innerHTML = ''; // clear empty state
  }

  const card = document.createElement('div');
  card.className = 'thumbnail-card';

  const img = document.createElement('img');
  img.src = dataURI;
  img.loading = "lazy";

  const timeLabel = document.createElement('div');
  timeLabel.className = 'timestamp';
  timeLabel.textContent = formatTime(timestamp);

  const downloadBtn = document.createElement('a');
  downloadBtn.href = dataURI;
  downloadBtn.download = `frame-${formatTime(timestamp).replace(/:/g, '-')}.png`;
  downloadBtn.textContent = "Download ⬇";

  card.appendChild(img);
  card.appendChild(timeLabel);
  card.appendChild(downloadBtn);

  gallery.prepend(card);
  
  while (gallery.children.length > 5) {
    gallery.removeChild(gallery.lastChild);
  }

  countBadge.textContent = `${framesSnatched} frame${framesSnatched > 1 ? 's' : ''}`;
}

export function resetFrameCount() {
  framesSnatched = 0;
  countBadge.textContent = '0 frames';
}

function formatTime(seconds) {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0');
  const s = Math.floor(seconds % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}
