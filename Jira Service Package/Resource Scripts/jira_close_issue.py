import cloudshell.helpers.scripts.cloudshell_scripts_helpers as helpers
import re
import os
import json
import base64
from urllib2 import Request
from urllib2 import urlopen
from urllib import quote

rc = json.loads(os.environ['RESOURCECONTEXT'])

api = helpers.get_api_session()

urlbase = rc['attributes']['Endpoint URL Base']
user = rc['attributes']['User']
password = api.DecryptPassword(rc['attributes']['Password']).Value
projname = rc['attributes']['Jira Project Name']
supportdomain = rc['attributes']['Support Domain']
issuetypename = rc['attributes']['Issue Type']

resid = helpers.get_reservation_context_details().id

issue_id = os.environ['ISSUE_ID']

if not issue_id:
    resname = api.GetReservationDetails(resid).ReservationDescription.Name
    try:
        issue_id = resname.split(' - ')[1].replace('issue ', '')
    except:
        print 'Issue id was not input and was not found in the reservation name, e.g. MyResource debug session - xyz-9'
        exit(1)


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

defaultprojid = ''
projid = ''
_, bls = _request('get', '/rest/api/2/project')
transitions = json.loads(bls)
for transition in transitions:
    if not defaultprojid:
        defaultprojid = transition['id']
    if transition['name'].lower() == projname.lower() or transition['key'].lower() == projname.lower():
        projid = transition['id']
        break

if projname:
    if not projid:
        print 'Project name "%s" not found. Valid project names: %s' % (projname, ', '.join([transition['name'] for transition in transitions]))
        exit(1)

else:
    if not defaultprojid:
        print 'You must define at least one project in Jira'
        exit(1)
    projid = defaultprojid

code, rslt = _request('get', '/rest/api/2/issue/%s' % issue_id)
if code >= 400:
    print 'Error: %d: %s' % (code, rslt)
    exit(1)

# oissue = json.loads(rslt)

orgdoms = re.search(r'QS_ORIGINAL_DOMAINS\(([^)]*)\)', rslt).groups()[0].split(',')
resource_name = re.search(r'QS_RESOURCE\(([^)]*)\)', rslt).groups()[0]

try:
    api.RemoveResourcesFromReservation(resid, [resource_name])
except:
    pass

api.RemoveResourcesFromDomain(supportdomain, [resource_name])

for dom in orgdoms:
    if dom != supportdomain:
        api.AddResourcesToDomain(dom, [resource_name])

_, bls = _request('get', '/rest/api/2/issue/%s/transitions' % issue_id)
transitions = json.loads(bls)['transitions']
transitionid = ''
for transition in transitions:
    if transition['name'].lower() == 'done':
        transitionid = transition['id']
        break

_, bls = _request('post', '/rest/api/2/issue/%s/transitions' % issue_id, json.dumps({
    'transition': {'id': transitionid}
}))
                  # '''{
                  #       "update":{
                  #           "comment":[
                  #               {
                  #                   "add":{"body":"Bug has been fixed."}
                  #               }
                  #           ]
                  #       },
                  #       "fields":{
                  #           "assignee":{"name":"bob"},
                  #           "resolution":{"name":"Fixed"}
                  #       },
                  #       "transition":{"id":"%s"},
                  #       "historyMetadata":{"type":"myplugin:type","description":"text description",
                  #       "descriptionKey":"plugin.changereason.i18.key",
                  #       "activityDescription":"text description",
                  #       "activityDescriptionKey":"plugin.activity.i18.key",
                  #       "actor":{
                  #           "id":"tony","displayName":"Tony","type":"mysystem-user",
                  #           "avatarUrl":"http://mysystem/avatar/tony.jpg",
                  #           "url":"http://mysystem/users/tony"
                  #       },
                  #       "generator":{
                  #           "id":"mysystem-1",
                  #           "type":"mysystem-application"
                  #       },
                  #       "cause":{"id":"myevent","type":"mysystem-event"},
                  #       "extraData":{"keyvalue":"extra data","goes":"here"}
                  #   }}
                  #
                  # {"id":"https://docs.atlassian.com/jira/REST/schema/issue-update#","title":"Issue Update","type":"object","properties":{"transition":{"title":"Transition","type":"object","properties":{"id":{"type":"string"},"name":{"type":"string"},"to":{"title":"Status","type":"object","properties":{"statusColor":{"type":"string"},"description":{"type":"string"},"iconUrl":{"type":"string"},"name":{"type":"string"},"id":{"type":"string"},"statusCategory":{"title":"Status Category","type":"object","properties":{"id":{"type":"integer"},"key":{"type":"string"},"colorName":{"type":"string"},"name":{"type":"string"}},"additionalProperties":false}},"additionalProperties":false},"fields":{"type":"object","patternProperties":{".+":{"title":"Field Meta","type":"object","properties":{"required":{"type":"boolean"},"schema":{"title":"Json Type","type":"object","properties":{"type":{"type":"string"},"items":{"type":"string"},"system":{"type":"string"},"custom":{"type":"string"},"customId":{"type":"integer"}},"additionalProperties":false},"name":{"type":"string"},"autoCompleteUrl":{"type":"string"},"hasDefaultValue":{"type":"boolean"},"operations":{"type":"array","items":{"type":"string"}},"allowedValues":{"type":"array","items":{}}},"additionalProperties":false,"required":["required"]}},"additionalProperties":false}},"additionalProperties":false},"fields":{"type":"object","patternProperties":{".+":{}},"additionalProperties":false},"update":{"type":"object","patternProperties":{".+":{"type":"array","items":{"title":"Field Operation","type":"object"}}},"additionalProperties":false},"historyMetadata":{"title":"History Metadata","type":"object","properties":{"type":{"type":"string"},"description":{"type":"string"},"descriptionKey":{"type":"string"},"activityDescription":{"type":"string"},"activityDescriptionKey":{"type":"string"},"emailDescription":{"type":"string"},"emailDescriptionKey":{"type":"string"},"actor":{"$ref":"#/definitions/history-metadata-participant"},"generator":{"$ref":"#/definitions/history-metadata-participant"},"cause":{"$ref":"#/definitions/history-metadata-participant"},"extraData":{"type":"object","patternProperties":{".+":{"type":"string"}},"additionalProperties":false}},"additionalProperties":false},"properties":{"type":"array","items":{"title":"Entity Property","type":"object","properties":{"key":{"type":"string"},"value":{}},"additionalProperties":false}}},"definitions":{"history-metadata-participant":{"title":"History Metadata Participant","type":"object","properties":{"id":{"type":"string"},"displayName":{"type":"string"},"displayNameKey":{"type":"string"},"type":{"type":"string"},"avatarUrl":{"type":"string"},"url":{"type":"string"}},"additionalProperties":false}},"additionalProperties":false}''' % transitionid)

print 'Closed Jira issue %s' % issue_id

