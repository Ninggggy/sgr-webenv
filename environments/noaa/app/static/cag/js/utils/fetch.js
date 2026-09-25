export async function fetchJson(url, {
    fallback = null,
    context = '',
    throwOnError = false
} = {}) {
    try {
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();

    } catch (error) {
        console.error(`[fetchJson] ${context}: ${url}`, error);

        if (throwOnError) {
            throw error;
        }

        return fallback;
    }
}