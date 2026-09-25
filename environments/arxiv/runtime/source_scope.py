"""Official taxonomy aliases determine coverage; source category strings stay intact."""
from arxiv.taxonomy.definitions import ARCHIVES_SUBSUMED,CATEGORY_ALIASES,CATEGORIES,ARCHIVES,GROUPS


def equivalent_categories(category):
    result={category}
    changed=True
    while changed:
        before=len(result)
        for old,new in {**ARCHIVES_SUBSUMED,**CATEGORY_ALIASES}.items():
            if old in result or new in result:result.update((old,new))
        changed=len(result)>before
    return result


def groups(categories):
    return {g for c in categories.split() for e in equivalent_categories(c)
            for g in ('cs','math','stat') if e==g or e.startswith(g+'.')}


def primary_category(categories):
    first=categories.split()[0] if categories else ''
    return CATEGORY_ALIASES.get(first,ARCHIVES_SUBSUMED.get(first,first))


def classification(category):
    # Preserve the source's canonical category identity, as official search does.
    category=ARCHIVES_SUBSUMED.get(category,category)
    data=CATEGORIES.get(category,{})
    archive=data.get('in_archive',category.split('.')[0])
    arc=ARCHIVES.get(archive,{})
    group=arc.get('in_group')
    return {'category':{'id':category,'name':data.get('name',category)},
            'archive':{'id':archive,'name':arc.get('name',archive)},
            'group':{'id':group,'name':GROUPS.get(group,{}).get('name',group)} if group else None}


def announcement_month(paper_id):
    """Official identifier's announcement month; never a guessed announcement day.

    arxiv-search DocumentMapping declares year_month, not a daily timestamp.
    Old IDs use 1991..2007; new IDs begin April 2007.
    """
    import re
    bare=re.sub(r'v[1-9]\d*$','',paper_id)
    if '/' in bare:
        digits=bare.split('/')[-1]
        if not re.fullmatch(r'\d{7}',digits):raise ValueError('Invalid legacy identifier')
        yy=int(digits[:2]);year=1900+yy if yy>=91 else 2000+yy
    else:
        if not re.fullmatch(r'\d{4}\.\d{4,5}',bare):raise ValueError('Invalid identifier')
        digits=bare[:4];year=2000+int(digits[:2])
    month=int(digits[2:4])
    if not 1<=month<=12:raise ValueError('Invalid identifier month')
    return f'{year:04d}-{month:02d}'


def is_primary_context(categories,context):
    """Browse keeps primary listings ahead of crosses, including archive aliases."""
    if not categories:return False
    return any(c==context or c.startswith(context+'.') for c in equivalent_categories(categories.split()[0]))
