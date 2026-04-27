// src/subtitleHandler.js

let gpsData = {}; // Maps timestamp (sec) to { latitude, longitude }

export function attachSubtitleEvents(file, videoElement, displayElement) {
  const reader = new FileReader();
  
  reader.onload = (e) => {
    const content = e.target.result;
    const extension = file.name.split('.').pop().toLowerCase();
    
    if (extension === 'srt') {
      gpsData = parseSRT(content);
    } else if (extension === 'gpx') {
      gpsData = parseGPX(content);
    } else {
      console.warn("Unsupported file format for GPS data");
      return;
    }
    
    videoElement.removeEventListener('timeupdate', updateSubtitle);
    videoElement.addEventListener('timeupdate', () => updateSubtitle(videoElement, displayElement));
  };
  
  reader.readAsText(file);
}

function updateSubtitle(videoElement, displayElement) {
  const currentTime = videoElement.currentTime;
  
  // Find closest timestamp in gpsData
  const timestamps = Object.keys(gpsData).map(Number).sort((a,b) => a - b);
  
  // Simple binary search or filter for closest timestamp within last 1 second
  const closestTimes = timestamps.filter(t => t <= currentTime && t > currentTime - 2);
  
  if (closestTimes.length > 0) {
    const lastTime = closestTimes[closestTimes.length - 1];
    const coords = gpsData[lastTime];
    displayElement.innerHTML = `LAT: ${coords.latitude.toFixed(6)} | LON: ${coords.longitude.toFixed(6)}<br><small>${coords.absTime || ''}</small>`;
    displayElement.style.opacity = '1';
  } else {
    displayElement.style.opacity = '0';
  }
}

export function getCurrentLocation(currentTime) {
  const timestamps = Object.keys(gpsData).map(Number).sort((a,b) => a - b);
  const closestTimes = timestamps.filter(t => t <= currentTime && t > currentTime - 2);
  
  if (closestTimes.length > 0) {
    const lastTime = closestTimes[closestTimes.length - 1];
    return gpsData[lastTime]; // Returns { latitude, longitude, absTime }
  }
  return null;
}

function parseSRT(fileContent) {
  const gps_data = {};
  const lines = fileContent.split('\n');
  
  const gpsPatterns = [
    /lat:([-\d.]+),lon:([-\d.]+)/i,
    /latitude:([-\d.]+),longitude:([-\d.]+)/i,
    /\[latitude:\s*([-\d.]+)\]\s*\[longitude:\s*([-\d.]+)\]/i,
    /GPS\(([-\d.]+),([-\d.]+)\)/i
  ];
  const timePattern = /(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->/;
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    let gpsMatch = null;
    
    for (const pattern of gpsPatterns) {
      gpsMatch = line.match(pattern);
      if (gpsMatch) break;
    }
    
    if (gpsMatch) {
      const lat = parseFloat(gpsMatch[1]);
      const lon = parseFloat(gpsMatch[2]);
      
      const startLookup = Math.max(0, i - 4);
      for (let j = startLookup; j < i; j++) {
        const timeMatch = lines[j].match(timePattern);
        if (timeMatch) {
          const h = parseInt(timeMatch[1], 10);
          const m = parseInt(timeMatch[2], 10);
          const s = parseInt(timeMatch[3], 10);
          const ms = parseInt(timeMatch[4], 10);
          const timestamp = (h * 3600) + (m * 60) + s + (ms / 1000.0);
          
          gps_data[timestamp] = { 
            latitude: lat, 
            longitude: lon,
            absTime: lines[j].split('-->')[0].trim() 
          };
          break;
        }
      }
    }
  }
  return gps_data;
}

function parseGPX(fileContent) {
  const gps_data = {};
  try {
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(fileContent, "text/xml");
    
    let trkpts = xmlDoc.getElementsByTagNameNS("http://www.topografix.com/GPX/1/1", "trkpt");
    if (!trkpts || trkpts.length === 0) {
      trkpts = xmlDoc.getElementsByTagName("trkpt");
    }
    
    if (!trkpts || trkpts.length === 0) return gps_data;
    
    let startTime = null;
    
    for (let i = 0; i < trkpts.length; i++) {
      const trkpt = trkpts[i];
      const lat = parseFloat(trkpt.getAttribute("lat"));
      const lon = parseFloat(trkpt.getAttribute("lon"));
      
      let timeElem = trkpt.getElementsByTagNameNS("http://www.topografix.com/GPX/1/1", "time")[0];
      if (!timeElem) {
        timeElem = trkpt.getElementsByTagName("time")[0];
      }
      
      if (timeElem && timeElem.textContent) {
        const timeObj = new Date(timeElem.textContent);
        if (!startTime) startTime = timeObj;
        const timestamp = (timeObj - startTime) / 1000.0; 
        gps_data[timestamp] = { 
          latitude: lat, 
          longitude: lon,
          absTime: timeObj.toISOString() 
        };
      }
    }
    return gps_data;
  } catch (e) {
    console.error("Error parsing GPX", e);
    return {};
  }
}
