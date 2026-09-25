"""Uniform, paper-independent capability limits for the current-metadata release."""
HISTORY = 'Historical-version contents and historical-content search are outside the offline scope of this release. Complete version numbers and submission times remain available on the current paper page.'
DAILY = 'Daily announcements, new/recent listings and catchup are outside the offline scope of this release. Year and month browsing remain available.'
IDENTIFIERS = 'ORCID, author identifiers and MSC/ACM field searches are outside the offline scope of this release. Author-name searches remain available.'
EXCLUDED = 'PDF, full text, source downloads, accounts and third-party services are outside the offline scope of this release.'


def unsupported(message, paper_id=None):
    from flask import request,render_template
    if request.path == '/api/query':
        from search.routes.classic_api.exceptions import respond
        return respond(message, link='/offline', status=501)
    return render_template('notice.html', message=message, current_paper=paper_id),501
