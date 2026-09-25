const SectionUtil = {
    is: {
        mapping: section => section === 'mapping',
        timeSeries: section => section === 'time-series',
        rankings: section => section === 'rankings',
        haywood: section => section === 'haywood',
        home: section => ['home', 'data-info', 'background'].includes(section)
    }
};

export default SectionUtil;
