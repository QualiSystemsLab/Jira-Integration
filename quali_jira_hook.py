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
from time import sleep
app = Flask(__name__)

quali_url_base = 'https://demo.quali.com:3443'
quali_user = 'jira_admin'
quali_password = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxx'
quali_domain = 'Quali Product'
worker_blueprint_name = 'JiraSupport2'

@app.route('/done/<issue_id>', methods=['POST'])
def done(issue_id):
    print (issue_id)
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
    r = requests.get('%s/api/v2/sandboxes/%s/components' % (quali_url_base, resid),
                     headers={'Content-Type': 'application/json', 'Authorization': 'Basic ' + token},
                     verify=False
                     )
    jiraserviceid = ''
    for component in json.loads(r.text):
        if 'jira' in component['name'].lower():
            jiraserviceid = component['id']
            break
    if not jiraserviceid:
        return make_response('Jira service not found in reservation %s' % resid, 501)
    r = requests.post('%s/api/v2/sandboxes/%s/components/%s/commands/%s/start' % (quali_url_base, resid, jiraserviceid, 'jira_close_issue'),
                      headers={'Content-Type': 'application/json', 'Authorization': 'Basic ' + token},
                      data=json.dumps({
                          'params': [
                              {
                                  'name': 'issue_id',
                                  'value': issue_id,
                              }
                          ],
                          'printOutput': True,
                      }), verify=False)

    if r.status_code >= 400:
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
            return make_response(s, 200)
        sleep(5)

    return make_response('jira_close_issue did not complete', 503)
