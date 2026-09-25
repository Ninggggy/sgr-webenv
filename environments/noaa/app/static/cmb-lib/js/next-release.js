async function getNextRelease() {
    const path = '/monitoring-content/lib/reference/monthly-releases.json';
    const noRelease = 'Next Monthly Release not yet scheduled';

    try {
        const response = await fetch(path);
        if (!response.ok) throw new Error('Failed to load Monthly Release JSON');
        const data = await response.json();

        const now = Date.now() / 1000;
        const sortedTimestamps = Object.keys(data).map(Number).sort((a, b) => a - b);

        for (const timestamp of sortedTimestamps) {
            if (timestamp >= now) {
                const entry = data[timestamp];
                const dateStr = entry.date;
                const hasTime = /\d{1,2}:\d{2}:\d{2}/.test(dateStr);

                const date = new Date(dateStr);
                if (isNaN(date)) continue;

                const dateOptions = {
                    weekday: 'short',
                    day: 'numeric',
                    month: hasTime ? 'short' : 'long',
                    year: 'numeric',
                    ...(hasTime && {
                        hour: 'numeric',
                        minute: 'numeric',
                        timeZone: 'America/New_York',
                        hour12: true,
                        timeZoneName: 'short'
                    })
                };

                const label = entry.report === 'National' ? 'U.S.' : 'Global';
                const formatter = new Intl.DateTimeFormat('en-US', dateOptions);
                const dateText = formatter.format(date);

                return `${entry.release} ${label} Release: ${dateText}`;
            }
        }

        return noRelease;
    } catch (error) {
        console.error('Error:', error);
        return noRelease;
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    const nextRelease = await getNextRelease();
    const releaseElement = document.querySelector('#next-release a');
    if (releaseElement) {
        releaseElement.textContent = nextRelease;
    }
});
