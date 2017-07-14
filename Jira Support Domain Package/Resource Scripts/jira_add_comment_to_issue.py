import cloudshell.helpers.scripts.cloudshell_scripts_helpers as helpers
import re
import os
import base64
import json
# import requests
from urllib2 import Request
from urllib2 import urlopen
from urllib import quote

api = helpers.get_api_session()
csuser = helpers.get_reservation_context_details().owner_user

rc = json.loads(os.environ['RESOURCECONTEXT'])

urlbase = rc['attributes']['Endpoint URL Base']
user = rc['attributes']['User']
password = api.DecryptPassword(rc['attributes']['Password']).Value

# issueid = os.environ['ISSUE_NAME']
resid = helpers.get_reservation_context_details().id
resname = api.GetReservationDetails(resid).ReservationDescription.Name
try:
    issueid = resname.split(' - ')[1].replace('issue ', '')
except:
    print 'Issue id not found in the reservation name, e.g. MyResource debug session - xyz-9'
    exit(1)

comment = os.environ['COMMENT']
fields_json = os.environ.get('ADDITIONAL_FIELDS_JSON', '')

def bytes23(s):
    if isinstance(s, unicode):
        return s.encode('utf-8', 'replace')
    else:
        return s or b''

def log(s):
    try:
        with open(r'c:\ProgramData\QualiSystems\jira.log', 'a') as f:
            f.write(s+'\r\n')
    except:
        pass

def _request(method, path, data=None, headers=None, hide_result=False, **kwargs):
    if not headers:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Basic ' + base64.b64encode('%s:%s' % (user, password)),
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

try:
    rscode, rs = _request('post', '/rest/api/2/issue/%s/comment' % issueid,
                  data='''{
        "body": "%s --%s"
        %s
    }''' % (comment, csuser, ','+fields_json if fields_json else ''))
except Exception as e:
    print 'Error adding comment. Check the issue name. %d: %s' % (e.code, e.msg)
    exit(1)
# if rscode >= 400:
    # print 'Failed to add comment. Check the issue name.: %d: %s' % (rscode, rs)
    # exit(1)

oo = json.loads(rs)
print 'Comment was added successfully'

# print rs

# print req('post', '/rest/api/2/issue/%s/comment' % issueid, '''{
#     "body": "%s"
#     %s
# }''' % (comment, ','+fields_json if fields_json else ''))
