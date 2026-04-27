/**
 * config.js — Runtime configuration loader.
 * Fetches all URLs and labels from the backend /api/config endpoint.
 * Every other JS module imports from here instead of hardcoding URLs.
 */

let _config = null;

export async function loadConfig() {
    if (_config) return _config;
    try {
        const response = await fetch('/api/config');
        _config = await response.json();
    } catch (err) {
        console.error('Failed to load runtime config, using defaults:', err);
        _config = {
            service_name: 'unknown',
            display_name: 'VisionPlayer',
            player_title: 'VisionPlayer',
            player_subtitle: '',
            id_field: 'e_id',
            id_label: 'E_ID',
            java_api_base_path: '',
            upload_url: '/api/frames/batch',
            filter_service_url: '/filter',
            vision_player_url: '/',
        };
    }
    return _config;
}

export function getConfig() {
    if (!_config) {
        throw new Error('Config not loaded yet. Call loadConfig() first.');
    }
    return _config;
}
