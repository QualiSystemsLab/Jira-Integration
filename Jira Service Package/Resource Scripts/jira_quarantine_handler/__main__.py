import cloudshell.helpers.scripts.cloudshell_scripts_helpers as helpers
import os
import json

import requests
from cloudshell.core.logger.qs_logger import get_qs_logger

rc = json.loads(os.environ['RESOURCECONTEXT'])

resource_or_blueprint_name = os.environ['SUBJECT_NAME']
blueprint_or_resource = os.environ['BLUEPRINT_OR_RESOURCE'].upper()
error_details = os.environ['ERROR_DETAILS']
original_domains_csv = os.environ['ORIGINAL_DOMAINS_CSV']
destdomain = os.environ['SUPPORT_DOMAIN']

resid = helpers.get_reservation_context_details().id
api = helpers.get_api_session()
logger = get_qs_logger(log_group=resid, log_file_prefix='JiraQuarantine')

logger.info(os.environ['RESOURCECONTEXT'])

urlbase = rc['attributes']['Endpoint URL Base']
user = rc['attributes']['User']
password = api.DecryptPassword(rc['attributes']['Password']).Value
projname = rc['attributes']['Jira Project Name']
issuetypename = rc['attributes']['Issue Type']
# support_username = rc['attributes'].get('Issue Assignee', 'Support')
error_pattern = rc['attributes'].get('Live Status Error Regex', 'error')


projid = ''
issuetypeid = ''

title = 'Error on %s %s' % (blueprint_or_resource.lower(), resource_or_blueprint_name)
descr = '''Issue opened automatically by CloudShell

%s

Click 'Open in Quali CloudShell' to open the resource in a debug sandbox.


Don't edit below this line
-----------------------------------
QS_%s(%s)
QS_DOMAIN(%s)
QS_ORIGINAL_DOMAINS(%s)
''' % (error_details, blueprint_or_resource, resource_or_blueprint_name, destdomain, original_domains_csv)

descr = descr.replace('\n', '\\n').replace('\r', '\\r')

# fields_json = os.environ.get('ADDITIONAL_FIELDS_JSON', '')
fields_json = ''


def req(method, path, data=None, **kwargs):
    logger.info('%s %s %s user=%s' % (method, path, data, user))
    r = requests.request(method,
                     path,
                     auth=(user, password),
                     headers={
                         'Accept': 'application/json',
                         'Content-Type': 'application/json',
                     },
                         data=data,
                         **kwargs)

    logger.info('Response: %d %s' % (r.status_code, r.text))
    return r.status_code, r.text

    # if code >= 400:
    # raise Exception('Error: %d: %s' % (code, body))

if not projid:
    defaultprojid = ''
    _, bls = req('get', '%s/rest/api/2/project' % urlbase)
    projs = json.loads(bls)
    for proj in projs:
        if not defaultprojid:
            defaultprojid = proj['id']
        if proj['name'].lower() == projname.lower() or proj['key'].lower() == projname.lower():
            projid = proj['id']
            break

    if projname:
        if not projid:
            print 'Project name "%s" not found. Valid project names: %s' % (
            projname, ', '.join([proj['name'] for proj in projs]))
            exit(1)

    else:
        if not defaultprojid:
            print 'You must define at least one project in Jira'
            exit(1)
        projid = defaultprojid

if not issuetypeid:
    _, nn = req('get', '%s/rest/api/2/issuetype' % urlbase)
    its = json.loads(nn)
    for it in its:
        if it['name'] == issuetypename:
            issuetypeid = it['id']
            break

    if not issuetypeid:
        print 'Issue type "%s" not found. Valid types: %s' % (issuetypename, ', '.join([it['name'] for it in its]))
        exit(1)

code, rslt = req('post', '%s/rest/api/2/issue' % urlbase, data='''{
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
