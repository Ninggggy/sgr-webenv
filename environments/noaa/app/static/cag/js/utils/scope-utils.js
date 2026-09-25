const ScopeUtil = {
    is: {
        global:          scope => scope === 'global',
        national:        scope => scope === 'national',
        regional:        scope => scope === 'regional',
        statewide:       scope => scope === 'statewide',
        divisional:      scope => scope === 'divisional',
        county:          scope => scope === 'county',
        city:            scope => scope === 'city',
        substate:        scope => ['divisional', 'county', 'city'].includes(scope),
        stateToNational: scope => ['national', 'regional', 'statewide'].includes(scope)
    }
};

export default ScopeUtil;
