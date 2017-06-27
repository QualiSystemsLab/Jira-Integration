import urllib
import zipfile

import StringIO
import cloudshell.helpers.scripts.cloudshell_scripts_helpers as helpers
import re
import os
import json
import base64
from urllib2 import Request
from urllib2 import urlopen
from urllib import quote

import time

import requests
from cloudshell.api.cloudshell_api import AttributeNameValue

rc = json.loads(os.environ['RESOURCECONTEXT'])

api = helpers.get_api_session()

urlbase = rc['attributes']['Endpoint URL Base']
user = rc['attributes']['User']
password = api.DecryptPassword(rc['attributes']['Password']).Value
projname = rc['attributes']['Jira Project Name']
destdomain = rc['attributes']['Support Domain']
issuetypename = rc['attributes']['Issue Type']

resid = helpers.get_reservation_context_details().id

resource_name = os.environ['RESOURCE_NAME']
error_message = os.environ['ERROR_MESSAGE']

doms = api.GetResourceDetails(resource_name, True).Domains

api.RemoveResourcesFromReservation(resid, [resource_name])
api.AddResourcesToDomain(destdomain, [resource_name])

if doms and doms[0].Name:
    for dom in doms:
        if dom.Name != destdomain:
            api.RemoveResourcesFromDomain(dom.Name, [resource_name])

# newresid = api.CreateImmediateReservation().Reservation.Id
# api.AddResourcesToReservation(newresid, [resource_name])
# api.AddServiceToReservation(newresid, 'Jira Service', 'Jira Service', [
#     AttributeNameValue('Endpoint URL Base', urlbase),
#     AttributeNameValue('User', user),
#     AttributeNameValue('Password', password),
#
#     AttributeNameValue('Jira Project Name', projname),
#     AttributeNameValue('Support Domain', destdomain),
#     AttributeNameValue('Issue Type', issuetypename),
# ])
# bpname = 'Debug %s_%s' % (resource_name, str(time.time()))
# api.SaveReservationAsTopology(newresid, '', bpname)
# supportcat = 'Support'
# api.SetTopologyCategory(bpname, supportcat, '')
# api.Topolo
qr1 = requests.put('%s://%s:%s/API/Auth/Login' % (
    'http',
    helpers.get_connectivity_context_details().server_address,
    '9000'
), headers={'Content-Type': 'application/x-www-form-urlencoded'},
                   data='username=%s&password=%s&domain=%s' % (
                       urllib.quote(user),
                       urllib.quote(password),
                       destdomain
                   ))
token = qr1.text.replace('"', '')
sio = StringIO.StringIO()
# sio = BytesIO.BytesIO()
z = zipfile.ZipFile(sio, 'w')
bpname = 'Debug %s_%d' % (resource_name, int(time.time()))

z.writestr('metadata.xml', str('''<?xml version="1.0" encoding="utf-8"?>
<Metadata xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://schemas.qualisystems.com/PackageMetadataSchema.xsd">
  <CreationDate>26/06/2017 14:12:19</CreationDate>
  <ServerVersion>8.0.0</ServerVersion>
  <PackageType>CloudShellPackage</PackageType>
</Metadata>'''))

z.writestr('Topologies/%s.xml' % bpname, str('''<?xml version="1.0" encoding="utf-8"?>
<TopologyInfo xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <Details Name="%s" Alias="%s" Driver="" SetupDuration="0" TeardownDuration="0" Public="true" DefaultDuration="120">
    <Description>Blueprint for debugging resource %s</Description>
    <Categories>
      <Category Name="Support" SubCategory="" />
    </Categories>
    <Scripts>
    </Scripts>
    <Diagram Zoom="1" NodeSize="Medium" />
  </Details>
  <Resources>
    <Resource PositionX="581" PositionY="96" Name="%s" Shared="false" />
  </Resources>
  <Services>
    <Service PositionX="400" PositionY="204" Alias="Jira Service" ServiceName="Jira Service">
      <Attributes>
        <Attribute Name="Jira Project Name" Value="%s" />
        <Attribute Name="Support Domain" Value="%s" />
        <Attribute Name="Issue Type" Value="%s" />
        <Attribute Name="User" Value="%s" />
        <Attribute Name="Password" Value="%s" />
        <Attribute Name="Endpoint URL Base" Value="%s" />
      </Attributes>
    </Service>
  </Services>
  <Apps />
</TopologyInfo>
''' % (bpname, bpname, resource_name, resource_name,
       projname, destdomain, issuetypename, user, password, urlbase)))

z.writestr('Categories/categories.xml', str('''<?xml version="1.0" encoding="utf-8"?>
<CategoryList xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://schemas.qualisystems.com/ResourceManagement/CategorySchema.xsd">
  <Category Name="Support" Description="" Catalog="Environment">
    <ChildCategories />
  </Category>
</CategoryList>
'''))

z.close()

zipdata = sio.getvalue()

# with open(r'c:\temp\zzahc.zip', 'wb') as f:
#     f.write(zipdata)

boundary = b'''------------------------652c70c071862fc2'''
fd = b'''--''' + boundary + \
     b'''\r\nContent-Disposition: form-data; name="file"; filename="my_zip.zip"\r\nContent-Type: application/octet-stream\r\n\r\n''' + \
     zipdata + \
     b'''\r\n--''' + boundary + b'''--\r\n'''

qr2 = requests.post('%s://%s:%s/API/Package/ImportPackage' % (
    'http',
    'localhost',
    '9000'
), headers={
    'Authorization': 'Basic %s' % token,
    'Content-Type': 'multipart/form-data; boundary=' + boundary,
}, data=fd)


title = 'Error on resource %s' % resource_name
descr = '''Issue opened by CloudShell

%s

Click 'More>Open in Quali CloudShell' to open the resource in a debug sandbox.


Don't edit below this line
-----------------------------------
QS_RESOURCE(%s)
QS_DOMAIN(%s)
QS_ORIGINAL_DOMAINS(%s)
QS_BLUEPRINT_NAME(%s)
''' % (error_message, resource_name, destdomain, ','.join([x.Name for x in doms]), bpname)

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
print 'Created Jira issue %s: %s/browse/%s' % (oo['key'], urlbase, oo['key'])

