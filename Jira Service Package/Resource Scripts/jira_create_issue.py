import cloudshell.helpers.scripts.cloudshell_scripts_helpers as helpers

import os
import json
import requests

api = helpers.get_api_session()
rc = json.loads(os.environ['RESOURCECONTEXT'])

urlbase = rc['attributes']['Endpoint URL Base']
user = rc['attributes']['User']
password = api.DecryptPassword(rc['attributes']['Password']).Value

projname = os.environ['PROJECT_NAME']
issuetypename = os.environ['ISSUE_TYPE']
title = os.environ['TITLE']
descr = os.environ['DESCRIPTION']
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

defaultprojid = ''
projid = ''
projs = json.loads(req('get', '/rest/api/2/project'))
for proj in projs:
    if not defaultprojid:
        defaultprojid = proj['id']
    if proj['name'].lower() == projname.lower() or proj['key'].lower() == projname.lower():
        projid = proj['id']
        break

if projname:
    if not projid:
        raise Exception('Project name "%s" not found. Valid project names are %s' % (projname, ', '.join([proj['name'] for proj in projs])))
else:
    if not defaultprojid:
        raise Exception('You must define at least one project in Jira')
    projid = defaultprojid


issuetypeid = ''
its = json.loads(req('get', '/rest/api/2/issuetype'))
for it in its:
    if it['name'] == issuetypename:
        issuetypeid = it['id']
        break

if not issuetypeid:
    raise Exception('Issue type "%s" not found. Valid types are %s' % (issuetypename, ', '.join([it['name'] for it in its])))

print req('post', '/rest/api/2/issue', '''{
    "fields": {
        "project": {
            "id": %s
        },
        %s
        "summary": "%s",
        "description": "%s",
        "issuetype": {
            "id": %s
        }
    }
}''' % (projid, fields_json, title, descr, issuetypeid))
