# Jira-Integration


## Health check example

End-to-end demo 

- Reserve the Jira Automatic Health Check or Jira Health Check blueprint
- If using Jira Health Check, run the sandbox command Run Health Checks - otherwise this will be performed by Setup
- One of the DUTs in the sandbox will fail its health check
- Because the Jira error handling service is present
- A Jira issue is automatically opened
- The resource is automatically removed from the reservation and placed in the "Support" domain
- In Jira, click "More>Open in Quali CloudShell"
- A new sandbox will be started by the Jira plugin
- The problematic resource is added to the sandbox
- This sandbox can be used to launch a connection to the resource and troubleshoot it
- A Jira service is also available in the sandbox with the command "Close issue" that automatically closes the Jira issue and moves the resource back from the Support domain to its original domains


## Components

### Jira Service

A CloudShell service that represents a Jira endpoint.

The service stores the endpoint URL and credentials and supports a few functions that call the Jira REST API. One function is a standard error handler so Jira can be used the pluggable issue tracker in sandboxes.

### Quali plugin for Jira

Adds a command to the Jira issue page: More>Open in Quali CloudShell

This connects to the CloudShell automation API to start a sandbox with the resource referencd by the Jira issue




## Development
- Jira plugin (Java)
  - Install JDK 8, ensure javac.exe is in PATH
  - Install Jira plugin SDK https://developer.atlassian.com/docs/getting-started/set-up-the-atlassian-plugin-sdk-and-build-a-project
  - Fix PATH and JAVA_HOME in Windows system properties if they were set incorrectly by the Jira SDK
  - Run Jira server in one command prompt:
    - cd QualiJiraPlugin
    - atlas-run
    - Leave open
    - Press Ctrl+C to shut down -- note that it uses an in-memory database so all user data will be lost when exiting
  - In another command prompt, reload the plugin every time the code is changed:
    - cd QualiJiraPlugin
    - atlas-mvn package
- CloudShell package
  - Double click build.cmd
  - Drag Jira Service Package.zip into the portal
  - To update:
	- Clone this repository
	- Go into the directory Jira Service Package in Explorer and create a zip file so that metadata.xml is at the root of the zip
  - When adding a Jira Service to your blueprint, update the password and URL to match any Jira account
  - If using the Jira plugin, update the default values of the Jira service to match your Jira server. The plugin will add the service to new sandboxes using the default credentials.
  - Call the functions manually from the portal or from your code using ExecuteCommand. Note that the raw API JSON is returned from the function.

## Functions provided
- jira_create_issue
    - PROJECT_NAME - project name or key; leave blank if you have only one project
    - ISSUE_TYPE - Task, Bug, Sub-task, Epic, Story, or a custom issue type defined ahead of time
    - TITLE - Headline of the issue
    - DESCRIPTION - Description of the issue
    - ADDITIONAL_FIELDS_JSON (can be omitted from the GUI inputs entirely) - text to be inserted into the JSON API request, e.g. {"fieldname1":"value1"}, {"fieldname2","value2"},
- jira_add_comment_to_issue
    - ISSUE_NAME - Issue id or key, returned by jira_create_issue
    - COMMENT - Text of the comment
    - ADDITIONAL_FIELDS_JSON (can be omitted from the GUI inputs entirely) - Additional text to insert in the JSON request, e.g. "visibility": {"type": "role","value": "Administrators"}\
- jira_close_issue - executes the transition to Done on the Jira issue
    - ISSUE_ID - The issue id or key of an existing issue. If blank, will attempt to take from sandbox_name.split(' - ')[1].
- jira_handle_resource_error - create a Jira issue for the specified resource and move the resource to the domain specified in Support Domain; called from the health checks in Setup
    - RESOURCE_NAME - name of the resource 
    - ERROR_MESSAGE - the reason for calling the error handler
