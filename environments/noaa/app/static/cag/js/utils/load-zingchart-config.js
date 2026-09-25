import { base } from '../globals.js';

export async function loadZingChartConfig(type = null) {
    const safeType = encodeURIComponent(type);
    const url = `${base}/api/config/zingchart/${safeType}.json`;

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (err) {
        console.error(`Failed to load ZingChart template config ${url}:`, err);
        return {};
    }
}
