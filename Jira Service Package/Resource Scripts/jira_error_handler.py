import cloudshell.helpers.scripts.cloudshell_scripts_helpers as helpers
import os
import json
import base64
from urllib2 import Request
from urllib2 import urlopen

import re

rc = json.loads(os.environ['RESOURCECONTEXT'])

api = helpers.get_api_session()

urlbase = rc['attributes']['Endpoint URL Base']
user = rc['attributes']['User']
password = api.DecryptPassword(rc['attributes']['Password']).Value
projname = rc['attributes']['Jira Project Name']
destdomain = rc['attributes']['Support Domain']
issuetypename = rc['attributes']['Issue Type']
# support_username = rc['attributes'].get('Issue Assignee', 'Support')
error_pattern = rc['attributes'].get('Live Status Error Regex', 'error')

resid = helpers.get_reservation_context_details().id

rd = api.GetReservationDetails(resid).ReservationDescription

projid = ''
issuetypeid = ''

for r in rd.Resources:
    resource_name = r.Name
    ls = api.GetResourceLiveStatus(resource_name)
    status = str(ls.liveStatusName) + ': ' + str(ls.liveStatusDescription)
    if re.search(error_pattern, status, re.IGNORECASE):
        doms = api.GetResourceDetails(resource_name, True).Domains

        api.RemoveResourcesFromReservation(resid, [resource_name])
        api.AddResourcesToDomain(destdomain, [resource_name])

        if doms and doms[0].Name:
            for dom in doms:
                if dom.Name != destdomain:
                    api.RemoveResourcesFromDomain(dom.Name, [resource_name])

        api.WriteMessageToReservationOutput(resid, 'Moved resource %s to domain %s' % (resource_name, destdomain))

        title = 'Error on resource %s' % resource_name
        descr = '''Issue opened automatically by CloudShell
        
%s
        
Click 'Open in Quali CloudShell' to open the resource in a debug sandbox.
        
        
Don't edit below this line
-----------------------------------
QS_RESOURCE(%s)
QS_DOMAIN(%s)
QS_ORIGINAL_DOMAINS(%s)
''' % (status, resource_name, destdomain, ','.join([x.Name for x in doms]))

        descr = descr.replace('\n', '\\n').replace('\r', '\\r')

        # fields_json = os.environ.get('ADDITIONAL_FIELDS_JSON', '')
        fields_json = ''

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
                    'Authorization': 'Basic ' + base64.b64encode('%s:%s' % (user, password))
                }

            if path.startswith('/'):
                path = path[1:]

            url = '%s/%s' % (urlbase, path)

            if isinstance(url, unicode):
                url = url.encode('ascii')
            headers = dict((k.encode('ascii') if isinstance(k, unicode) else k,
                            v.encode('ascii') if isinstance(v, unicode) else v)
                           for k, v in headers.items())
            log('Request: %s %s %s %s' % (method, path, data, headers))
            # log('Request %d: %s %s headers=%s data=<<<%s>>>' % (counter, method, url, pheaders, pdata))

            request = Request(url, bytes23(data), headers)
            request.get_method = lambda: method.upper()
            response = urlopen(request)
            body = response.read()
            code = response.getcode()
            response.close()

            log('Response: %d %s' % (code, body))

            # if code >= 400:
                # raise Exception('Error: %d: %s' % (code, body))
            return code, body

        if not projid:
            defaultprojid = ''
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

        if not issuetypeid:
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
        # "assignee": {
        #                 "name": "%s"
        #             },

        if code >= 400:
            print 'Error: %d: %s' % (code, rslt)
            exit(1)

        oo = json.loads(rslt)
        rv = 'Created Jira issue %s: %s/browse/%s' % (oo['key'], urlbase, oo['key'])
        api.WriteMessageToReservationOutput(resid, rv)
        print rv

