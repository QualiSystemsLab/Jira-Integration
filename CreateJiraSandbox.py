from cloudshell.api.cloudshell_api import InputNameValue, AttributeNameValue
from cloudshell.api.common_cloudshell_api import CloudShellAPIError
from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers
import os

resname = os.environ['RESERVATION_NAME']
dutname = os.environ['RESOURCE_NAME']
user = os.environ['USER']
duration = int(os.environ['DURATION_IN_MINUTES'])

jira_url = os.environ['JIRA_URL']
issue_type = os.environ['ISSUE_TYPE']
project_name = os.environ['PROJECT_NAME']
support_domain = os.environ['SUPPORT_DOMAIN']
jira_username = os.environ['JIRA_USERNAME']
jira_password = os.environ['JIRA_PASSWORD']

api = helpers.get_api_session()

resid = api.CreateImmediateReservation(resname, user, duration).Reservation.Id
'''        <Attribute Name="Jira Project Name" Value="" />
        <Attribute Name="Support Domain" Value="Support" />
        <Attribute Name="Issue Type" Value="Task" />
        <Attribute Name="User" Value="admin" />
        <Attribute Name="Password" Value="DxTbqlSgAVPmrDLlHvJrsA==" />
        <Attribute Name="Endpoint URL Base" Value="http://localhost:2990/jira" />'''
api.AddResourcesToReservation(resid, [dutname])
api.AddServiceToReservation(resid, 'Jira Service', 'Jira Service', [
    AttributeNameValue('Endpoint URL Base', jira_url),
    AttributeNameValue('Issue Type', issue_type),
    AttributeNameValue('Jira Project Name', project_name),
    AttributeNameValue('Support Domain', support_domain),
    AttributeNameValue('User', jira_username),
    AttributeNameValue('Password', jira_password),
])
api.SetReservationServicePosition(resid, 'Jira Service', 300, 500)
print resid