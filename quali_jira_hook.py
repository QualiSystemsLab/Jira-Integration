# Usage:
#
# export FLASK_APP=quali_jira_hook.py
# flask run
#
# Runs at http://127.0.0.1:5000 by default
#
# Web hook URL verbatim: http://127.0.0.1:5000/done/${issue.id}


from flask import Flask, request, make_response
import requests
import json
import re
from time import sleep
app = Flask(__name__)

quali_url_base = 'http://172.20.7.177:82'
quali_user = 'admin'
quali_password = 'admin'
quali_domain = 'Global'
worker_blueprint_name = 'UnquarantineWorker'

# a Jira account that has read access to issues
jira_url_base = 'http://127.0.0.1:2990/jira'
jira_user = 'admin'
jira_password = 'admin'


@app.route('/done/<issue_id>', methods=['POST'])
def done(issue_id):
    print (issue_id)

    r = requests.get('%s/rest/api/2/issue/%s' % (jira_url_base, issue_id),
                     auth=(jira_user, jira_password),
                     verify=False)
    rslt = json.loads(r.text)['fields']['description']


    m = re.search(r'QS_RESOURCE\(([^)]*)\)', rslt)
    if m:
        subject_name = m.groups()[0]
	blueprint_or_resource = 'RESOURCE'
    else:
        m = re.search(r'QS_BLUEPRINT\(([^)]*)\)', rslt)
	if m:
	    subject_name = m.groups()[0]
	    blueprint_or_resource = 'BLUEPRINT'
	else:
            return make_response('QS_RESOURCE or QS_BLUEPRINT not found in body', 501)
    orgdoms_csv = re.search(r'QS_ORIGINAL_DOMAINS\(([^)]*)\)', rslt).groups()[0]
    support_domain = re.search(r'QS_DOMAIN\(([^)]*)\)', rslt).groups()[0]
    

    r = requests.put('%s/api/login' % quali_url_base,
                     headers={'Content-Type': 'application/json'},
                     data='{"username":"%s","password":"%s","domain":"%s"}' % (quali_user, quali_password, quali_domain),
                     verify=False)
    if r.status_code >= 400:
        return make_response('Login failed: %d: %s' % (r.status_code, r.text), 500)

    token = r.text.replace('"', '').strip()

    r = requests.post('%s/api/v2/blueprints/%s/start' % (quali_url_base, worker_blueprint_name),
                      headers={'Content-Type': 'application/json', 'Authorization': 'Basic ' + token},
                      data=json.dumps({
                          'duration': 'PT1M',
                          'name': 'jiraworker',
                          'params': []
                      }), verify=False)
    if r.status_code >= 400:
        return make_response('Start sandbox failed: %d: %s' % (r.status_code, r.text), 500)

    o = json.loads(r.text)
    resid = o['id']
    r = requests.post('%s/api/v2/sandboxes/%s/commands/Unquarantine/start' % (quali_url_base, resid),
                      headers={'Content-Type': 'application/json', 'Authorization': 'Basic ' + token},
                      data=json.dumps({
                          'params': [
                              {
                                  'name': 'subject_name',
                                  'value': subject_name,
                              },
                              {
                                  'name': 'blueprint_or_resource',
                                  'value': blueprint_or_resource,
                              },
                              {
                                  'name': 'original_domains_csv',
                                  'value': orgdoms_csv,
                              },
                              {
                                  'name': 'support_domain',
                                  'value': support_domain,
                              },
                          ],
                          'printOutput': True,
                      }), verify=False)

    if r.status_code >= 400:
        print r.status_code, r.text
        return make_response('jira_close_issue failed: %d: %s' % (r.status_code, r.text), 502)
    exid = json.loads(r.text)['executionId']
    r = None
    for _ in range(30):
        r = requests.get('%s/api/v2/executions/%s' % (quali_url_base, exid),
                         headers={'Content-Type': 'application/json', 'Authorization': 'Basic ' + token},
                         verify=False
                         )
        if r.status_code >= 400:
            raise Exception('jira_close_issue failed: %d: %s' % (r.status_code, r.text))
        o = json.loads(r.text)
        if o['status'] != 'Pending' and o['status'] != 'Running':
            s = 'Finished with status %s, output %s' % (o['status'], o['output'])
            print (s)
            r2 = requests.post('%s/api/v2/sandboxes/%s/stop' % (quali_url_base, resid),
                               headers={'Content-Type': 'application/json', 'Authorization': 'Basic ' + token},
                               verify=False
            )
            #print (r2.text)
            return make_response(s, 200)
        sleep(5)

    return make_response('jira_close_issue did not complete', 503)
