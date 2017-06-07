import cloudshell.helpers.scripts.cloudshell_scripts_helpers as helpers

import os
import json
import requests

api = helpers.get_api_session()
rc = json.loads(os.environ['RESOURCECONTEXT'])

urlbase = rc['attributes']['Endpoint URL Base']
user = rc['attributes']['User']
password = api.DecryptPassword(rc['attributes']['Password']).Value

issueid = os.environ['ISSUE_ID']
comment = os.environ['COMMENT']
fields_json = os.environ['ADDITIONAL_FIELDS_JSON']


def log(s):
    try:
        with open(r'c:\temp\jira.log', 'a') as f:
            f.write(s+'\r\n')
    except:
        pass


def req(method, urlsuffix, body='', *args, **kwargs):
    url = '%s/%s' % (urlbase, urlsuffix)
    log('Request %s %s %s' % (method, url, body))
    r = requests.request(method, url,
                         auth=(user, password),
                         headers={
                             'Content-Type': 'application/json',
                             'Accept': 'application/json',
                         },
                         data=body if body else None)
    log('Result: %d: %s' % (r.status_code, r.text))
    if r.status_code >= 400:
        raise Exception('Error %d: %s' % (r.status_code, r.text))
    return r.text

print req('post', '/rest/api/2/issue/%s/comment' % issueid, '''{
    "body": "%s"
    %s
}''' % (comment, ','+fields_json if fields_json else ''))
