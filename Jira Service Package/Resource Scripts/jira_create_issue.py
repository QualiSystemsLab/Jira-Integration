import cloudshell.helpers.scripts.cloudshell_scripts_helpers as helpers
import re
import os
import json
import base64
# import requests
from urllib2 import Request
from urllib2 import urlopen
from urllib import quote

api = helpers.get_api_session()
rc = json.loads(os.environ['RESOURCECONTEXT'])

urlbase = rc['attributes']['Endpoint URL Base']
user = rc['attributes']['User']
password = api.DecryptPassword(rc['attributes']['Password']).Value

projname = os.environ['PROJECT_NAME']
issuetypename = os.environ['ISSUE_TYPE']
title = os.environ['TITLE']
descr = os.environ['DESCRIPTION']
fields_json = os.environ.get('ADDITIONAL_FIELDS_JSON', '')

def bytes23(s):
    if isinstance(s, unicode):
        return s.encode('utf-8', 'replace')
    else:
        return s or b''

def log(s):
    try:
        with open(r'c:\temp\jira.log', 'a') as f:
            f.write(s+'\r\n')
    except:
        pass

def _request(method, path, data=None, headers=None, hide_result=False, **kwargs):
    if not headers:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Basic ' + base64.b64encode('%s:%s' % (user, password))
        }
    # if self._token:
        # headers['Authorization'] = 'Basic ' + self._token

    if path.startswith('/'):
        path = path[1:]

    url = '%s/%s' % (urlbase, path)

    if isinstance(url, unicode):
        url = url.encode('ascii')
    headers = dict((k.encode('ascii') if isinstance(k, unicode) else k,
                    v.encode('ascii') if isinstance(v, unicode) else v)
                   for k, v in headers.items())

    # pdata = data
    # pdata = re.sub(r':[^@]*@', ':(password hidden)@', pdata)
    # pdata = re.sub(r'"Password":\s*"[^"]*"', '"Password": "(password hidden)"', pdata)
    # pheaders = dict(headers)
    # if 'Authorization' in pheaders:
    #     pheaders['Authorization'] = '(token hidden)'

    # log('Request %d: %s %s headers=%s data=<<<%s>>>' % (counter, method, url, pheaders, pdata))

    request = Request(url, bytes23(data), headers)
    request.get_method = lambda: method.upper()
    response = urlopen(request)
    body = response.read()
    code = response.getcode()
    response.close()

    # if code >= 400:
        # raise Exception('Error: %d: %s' % (code, body))
    return code, body

# def req(method, urlsuffix, body='', *args, **kwargs):
#     url = '%s/%s' % (urlbase, urlsuffix)
#     log('Request %s %s %s' % (method, url, body))
#     r = requests.request(method, url,
#                          auth=(user, password),
#                          headers={
#                              'Content-Type': 'application/json',
#                              'Accept': 'application/json',
#                          },
#                          data=body if body else None)
#     log('Result: %d: %s' % (r.status_code, r.text))
#     if r.status_code >= 400:
#         raise Exception('Error %d: %s' % (r.status_code, r.text))
#     return r.text

defaultprojid = ''
projid = ''
_, bls = _request('get', '/rest/api/2/project')
projs = json.loads(bls)
for proj in projs:
    if not defaultprojid:
        defaultprojid = proj['id']
    if proj['name'].lower() == projname.lower() or proj['key'].lower() == projname.lower():
        projid = proj['id']
        break

if projname:
    if not projid:
        print 'Project name "%s" not found. Valid project names: %s' % (projname, ', '.join([proj['name'] for proj in projs]))
        exit(1)

else:
    if not defaultprojid:
        print 'You must define at least one project in Jira'
        exit(1)
    projid = defaultprojid


issuetypeid = ''
_, nn = _request('get', '/rest/api/2/issuetype')
its = json.loads(nn)
for it in its:
    if it['name'] == issuetypename:
        issuetypeid = it['id']
        break

if not issuetypeid:
    print 'Issue type "%s" not found. Valid types: %s' % (issuetypename, ', '.join([it['name'] for it in its]))
    exit(1)

code, rslt = _request('post', '/rest/api/2/issue', data='''{
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
if code >= 400:
    print 'Error: %d: %s' % (code, rslt)
    exit(1)

oo = json.loads(rslt)
print 'Created issue %s' % oo['key']

