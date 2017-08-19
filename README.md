# Jira-Integration


## Health check example

End-to-end demo 

Summary:
- Reserve the Jira Automatic Health Check or Jira Health Check blueprint
- If using Jira Health Check, run the sandbox command Run Health Checks. If using Jira Automatic Health Check, the health checks will be run automatically during Setup.
- DUT 2 will fail its health check
- End the sandbox
- Teardown calls the Jira error handler because the service is present in the reservation
  - A Jira issue is automatically opened
  - The resource is automatically removed from the reservation and moved to the "Support" domain
  - A link to the Jira issue is printed in the Output window and Activity feed
- On the Jira issue page, click "Open in Quali CloudShell" in the top right
- A new sandbox will be started by the Jira plugin
- The problematic resource is added to the sandbox
- This sandbox can be used to launch a connection to the resource and troubleshoot it
- When the Jira issue is closed (e.g. transition to Done), the Quali web hook can move the resource from Support to its original domain(s), returning it to circulation


Details:

Configure the Jira plugin:
![](screenshots/jira_plugin_settings_full.png)

Open the CloudShell blueprint:
![](screenshots/blueprint.png)

One-time setup: Enter Jira server settings:
![](screenshots/edit_jira_error_handler_settings1.png)
![](screenshots/edit_jira_error_handler_settings2.png)

Reserve the blueprint:
![](screenshots/reserve_blueprint.png)

Sandbox based on the blueprint (note: Jira service would be hidden for a non-admin user):
![](screenshots/sandbox1.png)

Run the health checks:
![](screenshots/run_health_check.png)

See that the health check failed for DUT 2:
![](screenshots/health_check_failed.png)
![](screenshots/health_check_failed2.png)

End the sandbox:
![](screenshots/teardown.png)

The Jira error handler in the sandbox creates a Jira issue for problematic resources and quarantines them:
![](screenshots/jira_issue_created.png)

New issue in Jira:
![](screenshots/jira_issue.png)

Click the button provided by the Jira plugin to open the quarantined resource in a debug sandbox:
![](screenshots/open_in_cloudshell.png)

Access to the debug sandbox:
![](screenshots/debug_sandbox_created.png)
![](screenshots/debug_sandbox.png)

Starting the web hook:


Creating a Quali web hook in Jira:
![](screenshots/create_web_hook_1.png)
![](screenshots/create_web_hook_2.png)
![](screenshots/create_web_hook_3.png)

Attaching the Quali web hook to Jira transitions:
![](screenshots/edit_transition.png)
![](screenshots/attach_web_hook_1.png)
![](screenshots/attach_web_hook_2.png)
![](screenshots/attach_web_hook_3.png)



## Components

### Jira Service

A CloudShell service that represents a Jira endpoint.

The service stores the endpoint URL and credentials and supports a few functions that call the Jira REST API. One function is a standard error handler so Jira can be used the pluggable issue tracker in sandboxes.

### Quali plugin for Jira

Adds a command to the Jira issue page: Open in Quali CloudShell

This connects to the CloudShell sandbox API to reserve a Jira worker blueprint and run a function that in turn creates a debug sandbox containing the resource referenced by the Jira issue. The link to the debug sandbox (in the Support domain) 


### Web hook

Attached to issue transitions in Jira, e.g. To Do -> Done.

When triggered, it will log in to CloudShell and restore the resource in the issue
back to its original CloudShell domains and return it to circulation.

Add the web hook to Jira according to the screenshots above.


Implemented as a Flask-based Python web server.

  pip install requests flask
  export FLASK_APP=quali_jira_hook.py
  flask run

It is recommended to run the web server on the Jira host, listening on 127.0.0.1 port 5000 only.

For other configurations, set the listening addresses and port according to the Flask documentation.



## Development
- Jira plugin (Java)
  - SDK
    - Windows
      - Install JDK 8, ensure javac.exe is in PATH
      - Install Jira plugin SDK https://developer.atlassian.com/docs/getting-started/set-up-the-atlassian-plugin-sdk-and-build-a-project
      - Fix PATH and JAVA_HOME in Windows system properties if they were set incorrectly by the Jira SDK
      - In Git Bash:
        - git clone https://github.com/QualiSystemsLab/Jira-Integration.git
        - cd Jira-Integration
    - Ubuntu 16
      - apt-get update
      - apt-get install openjdk-8-jdk
      - export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
      - sh -c 'echo "deb https://sdkrepo.atlassian.com/debian/ stable contrib" >>/etc/apt/sources.list'
      - apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys B07804338C015B73
      - apt-get install apt-transport-https
      - apt-get update
      - apt-get install atlassian-plugin-sdk
      - atlas-version
      - git clone https://github.com/QualiSystemsLab/Jira-Integration.git
      - cd Jira-Integration/
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
  - In non-Support domain, drag Jira Service Package.zip into the portal
  - In Support domain, drag Jira Service Domain Package.zip into the portal
  - To update:
	- In Git Bash: git clone https://github.com/QualiSystemsLab/Jira-Integration.git
	- Edit files
	- Double click build.cmd
  - When adding a Jira Error Handler Service to your blueprint, update the password and URL to match any Jira account

## Functions provided

### Jira Error Handler Service
- jira_error_handler - (run by Error Handler Sandbox Teardown) check all sandbox resources for a pattern such as 'Error' in the live status, as set by health_check; for each resource with a problem, create a Jira issue and quarantine the resource by moving it to the domain specified in Support Domain
