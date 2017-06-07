# Jira-Integration

A service that represents a Jira SaaS endpoint.

The service stores the endpoint URL and credentials and supports a few functions that call the Jira REST API.


## Instructions
- Drag Jira Service Package.zip into the portal
- To update:
	- Clone this repository
	- Go into the directory Jira Service Package in Explorer and create a zip file so that metadata.xml is at the root of the zip
- When adding a Jira Service to your blueprint, update the password and URL to match your Jira account
- Call the functions manually from the portal or from your code using ExecuteCommand. Note that the raw API JSON is returned from the function.

## Functions provided
- jira_create_issue
    - PROJECT_NAME - project name or key; leave blank if you have only one project
    - ISSUE_TYPE - Task, Bug, Sub-task, Epic, Story, or a custom issue type defined ahead of time
    - TITLE - Headline of the issue
    - DESCRIPTION - Description of the issue
    - ADDITIONAL_FIELDS_JSON - text to be inserted into the JSON API request, e.g. {"fieldname1":"value1"}, {"fieldname2","value2"},
- jira_add_comment_to_issue
    - ISSUE_ID - Issue id or key, returned by jira_create_issue
    - COMMENT - Text of the comment
    - ADDITIONAL_FIELDS_JSON - Additional text to insert in the JSON request, e.g. "visibility": {"type": "role","value": "Administrators"}\
