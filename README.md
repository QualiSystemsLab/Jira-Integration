# Jira-Integration

This Jira integration has been refactored into a general-purpose error handling infrastructure:
- Automatically call the standard `health_check` function
- Quarantine bad resources or blueprints based on live status or Activity feed
- Support quick implementation of platform-specific post-quarantine handlers, such as a handler that creates a new Jira issue for a bad resource
- Start a debug sandbox containing a quarantined resource, triggered from a third-party tool
- Unquarantine a resource or sandbox, triggered from a third-party tool (or CloudShell if operating without any third-party tool)

This example for Jira also includes:
- a Jira plugin written in Java that launches a debug sandbox for a resource
- a web hook that unquarantines a resource or blueprint in CloudShell when a Jira issue moves to the `Done` state

## Health check demo

### Components
- CloudShell
    - A dedicated domain for the support user, e.g. `Support`
    - Demo blueprints, services, and a worker blueprint for the main domain, in draggable package **Jira_Main_Package.zip**
    - Worker blueprint in the `Support` domain, in draggable package **Jira_Support_Domain_Package.zip**
- Jira
    - Plugin for starting sandboxes from Jira
    - Web hook to restore the CloudShell resource on issue transitions  

### Demo summary

- **Reserve the Jira Automatic Health Check or Jira Health Check blueprint**
- Post-Setup health check
    - If using Jira Automatic Health Check, the health checks will be run automatically at the end of Setup by a hook on service `Post Setup Health Check` called `health_check_orch_hook_post_setup` (friendly name `Run Health Checks`)
    - If using Jira Manual Health Check, you must **run `Run Health Checks` on `Manual Health Check Service`**. 
    - DUT 1 and DUT 2 both have a script `health_check` attached. Most resources with official shells have a `health_check` driver function.
    - Resource DUT 2 will fail its health check
- Automatic quarantine
    - **Manually end the sandbox**
    - `hook_teardown` finds a teardown hook on `Resource Quarantine Service` and calls it
      - DUT 2 is found to have a live status containing "Error", triggering quarantine  
        - The resource is automatically removed from the reservation and moved to the `Support` domain
        - All quarantine handlers in the reservation are called
            - The Jira quarantine handler is found
                - Opens a Jira issue for DUT 2
                - Prints a link to the Jira issue in the Output window and the Activity feed
- Jira-based troubleshooting
    - **On the Jira issue page, click `Open in Quali CloudShell` in the top right**
    - The Jira plugin starts a new sandbox in the `Support` domain
    - The problematic resource DUT 2 is added to the sandbox
    - This sandbox can be used to launch a connection to the resource and troubleshoot it
- Unquarantine
    - **Mark the Jira issue as Done**
    - When the Jira issue is closed (i.e. transitions to `Done`), the Quali web hook moves the resource from `Support` to its original domain(s), returning it to circulation



## Demo details

Install the Jira plugin from the Atlassian marketplace, or run a development mode Jira server as described later.
  
Configure the Jira plugin:
![](screenshots/jira_plugin_settings_full.png)

Open the CloudShell blueprint:
![](screenshots/blueprint.png)

One-time setup: Enter Jira server settings:
![](screenshots/edit_jira_error_handler_settings1.png)
![](screenshots/edit_jira_error_handler_settings2.png)

Reserve the blueprint:
![](screenshots/reserve_blueprint.png)

Sandbox based on the blueprint (note: services could be hidden for a non-admin user):
![](screenshots/sandbox1.png)

See that the post-Setup health check failed for DUT 2:
![](screenshots/health_check_failed.png)

End the sandbox:
![](screenshots/teardown.png)

The resource quarantine service in the sandbox quarantines DUT 2 and calls the Jira quarantine handler service, which creates a new Jira issue:
![](screenshots/jira_issue_created.png)

New issue in Jira:
![](screenshots/jira_issue.png)

Click the button provided by the Jira plugin to open the quarantined resource in a debug sandbox:
![](screenshots/open_in_cloudshell.png)

Access the debug sandbox:
![](screenshots/debug_sandbox_created.png)
![](screenshots/debug_sandbox.png)


Setting up the Quali custom `Done` transition web hook in Jira:

Go to the System section of Administration:
![](screenshots/create_web_hook_m1.png)

Scroll down to WebHooks under ADVANCED:
![](screenshots/create_web_hook_0.png)

Create a WebHook:
![](screenshots/create_web_hook_1.png)
![](screenshots/create_web_hook_2.png)
![](screenshots/create_web_hook_3.png)

Attaching the Quali web hook to Jira `->Done` transitions:
![](screenshots/edit_transition.png)
![](screenshots/attach_web_hook_1.png)
![](screenshots/attach_web_hook_2.png)
![](screenshots/attach_web_hook_3.png)

Setting up the web hook:


    Edit quali_jira_hook.py:

    quali_url_base = 'http://172.20.7.177:82'
    quali_user = 'admin'
    quali_password = 'admin'
    quali_domain = 'Global'
    worker_blueprint_name = 'UnquarantineWorker'
    
    # a Jira account that has read access to issues
    jira_url_base = 'http://127.0.0.1:2990/jira'
    jira_user = 'admin'
    jira_password = 'admin'


Running the web hook:

    pip install requests flask
    export FLASK_APP=quali_jira_hook.py
    flask run


## Component details

### hook_setup, hook_teardown

General-purpose 8.1-compliant Setup and Teardown scripts that execute any hook functions found on 
resources and services in the reservation, based on keywords in the name:

    orch_hook_pre_setup
    orch_hook_during_preparation
    orch_hook_post_preparation
    orch_hook_during_provisioning
    orch_hook_post_provisioning
    orch_hook_during_connectivity
    orch_hook_post_connectivity
    orch_hook_during_configuration
    orch_hook_post_configuration
    orch_hook_post_setup
    orch_hook_pre_teardown
    orch_hook_during_teardown
    orch_hook_post_teardown

Must be attached to any sandbox where hooks will be used. Can safely replace the default 
Setup and Teardown.

### Jira Auto Health Check Demo and Jira Manual Health Check Demo blueprints

Jira Auto Health Check Demo has `hook_setup` and `hook_teardown` attached.

Jira Manual Health Check Demo has `Default Sandbox Setup 2.0` and `hook_teardown` attached. 
This means the health checks must be run manually on `Manual Health Check Service`. 

#### DUTs

Two abstract resource requests for `Example Model` that will match resources `DUT 1` and `DUT 2`.

`Example Model` has a script `health_check` attached that is hard-coded to fail on `DUT 2`.

#### Post Setup Health Check Service

Contains a hook `health_check_orch_hook_post_setup`.

When included in a blueprint, at the end of Setup it will search for a `health_check` function
on every resource in the reservation and automatically execute any `health_check` found.

`health_check` is expected to set the live status of the resource, with "Error" indicating
a failure.
 
#### Resource Quarantine Service

Contains a hook `quarantine_resources_orch_hook_post_teardown`:
- Searches for resources with "Error" live status
- For each bad resource:
    - Moves the bad resource to the `Support` domain
    - Calls any platform-specific quarantine handlers that exist in the reservation:
        - Looks for services with functions with `quarantine_handler` in the name
        - Runs the `quarantine_handler` with inputs:
            - `subject_name`: the name of the resource that was quarantined
            - `blueprint_or_resource`: "RESOURCE"
            - `error_details`: the live status name and description
            - `original_domains_csv`: comma-separated list of domains the resource has been removed from
            - `support_domain`: the support domain where the resource has been quarantined, e.g. `Support`

Settings:
- `Support Domain` - the domain where bad resources should be moved, e.g. `Support`
- `Live Status Error Regex` - a pattern that indicates a bad live status if found in the live status name or description, default "Error"

This service is platform-independent and can be used even without platform-specific handlers.

#### Blueprint Quarantine Service

(Not used in this demo, may need further work)

Contains a hook `quarantine_blueprint_orch_hook_post_teardown`:
- Searches for errors in the Activity feed
- If errors are found:
    - Moves the blueprint to the `Support` domain
    - Calls platform-specific quarantine handlers:
        - Looks for services with functions with `quarantine_handler` in the name
        - Runs the `quarantine_handler` with inputs:
            - `subject_name`: the name of the resource that was quarantined
            - `blueprint_or_resource`: "BLUEPRINT"
            - `error_details`: the error(s) from the Activity feed
            - `original_domains_csv`: today, only the current domain where the blueprint ran -- **TODO**
            - `support_domain`: the support domain where the blueprint has been quarantined, e.g. `Support`

Settings:
- `Support Domain` - the domain where a bad blueprint should be moved, e.g. `Support`

This service is platform-independent and can be used even without platform-specific handlers.

#### Jira Quarantine Handler Service

Creates a Jira issue to track a resource or blueprint that has just been quarantined during teardown.

Called by `Resource Quarantine Service` or `Blueprint Quarantine Service` hooks, which run during Teardown.

Handles all Jira-specific aspects of the quarantine process. The generic 
`Resource Quarantine Service` and/or 
`Blueprint Quarantine Service` must be added to the blueprint in 
addition to `Jira Quarantine Handler Service`. 


Contains a function `jira_quarantine_handler` with inputs:
- `subject_name`: the name of the resource or blueprint that was quarantined
- `blueprint_or_resource`: "BLUEPRINT" or "RESOURCE"
- `error_details`: for a blueprint, the error(s) from the Activity feed; for a resource, the live status name and description 
- `original_domains_csv`: the domains the item has been removed from
- `support_domain`: the support domain where the item has been quarantined, e.g. `Support`

Inputs:
- `Endpoint URL Base`: Jira endpoint URL, e.g. `http://localhost:2990/jira`
- `User`: Jira username
- `Password`: Jira password
- `Jira Project Name`: Jira project where issues should be opened. Can be blank if there is only one project. 
- `Issue Type`: issue type to create, e.g. Task

Creates a Jira issue with a specially formatted description, e.g.

    Issue opened automatically by CloudShell
    Error: Health check on resource DUT 2 failed: Device not responding
    Click 'Open in Quali CloudShell' to open the resource in a debug sandbox.
    
    Don't edit below this line
    -----------------------------------
    QS_RESOURCE(DUT 2)
    QS_DOMAIN(Support)
    QS_ORIGINAL_DOMAINS(User1, User2)


### DebugSandboxWorker blueprint
**!!! MUST BE MARKED PUBLIC !!!**

Contains a function `CreateSandbox` with inputs:
- `reservation_name`: name of the debug sandbox to create
- `resource_name`: name of the quarantined resource to add to the sandbox 
- `duration_in_minutes`: duration of the sandbox in minutes
- `user`: CloudShell owner to set as the owner of the sandbox

`CreateSandbox` creates an immediate reservation containing the specified resource using the CloudShell automation API.

A third-party tool is expected to reserve this blueprint and execute `CreateSandbox` using the sandbox API.


### UnquarantineWorker blueprint
**!!! MUST BE MARKED PUBLIC !!!**

Contains a function `Unquarantine` with inputs:
- `subject_name`: resource or blueprint name
- `blueprint_or_resource`: "BLUEPRINT" or "RESOURCE"
- `original_domains_csv`: comma-separated list of domains the resource or blueprint should be moved back to 
- `support_domain`: the domain where the resource or blueprint is currently quarantined, e.g. `Support`

`Unquarantine` moves the resource or blueprint from the `Support` domain to the specified domains.

A third-party tool is expected to reserve this blueprint and execute `Unquarantine` using the sandbox API.


### Quali plugin for Jira

Adds a button to the Jira issue page: `Open in Quali CloudShell`

`Open in Quali CloudShell`:
- Connects to the CloudShell sandbox API under the `Support` domain
- Reserves a Jira worker blueprint that must exist in the `Support` domain
- Runs a function `CreateSandbox` that creates a debug sandbox containing the resource referenced by the Jira issue
- Displays a link to the new debug sandbox (valid in the `Support` domain) 


### Issue transition web hook

Attached to issue transitions in Jira, e.g. `To Do -> Done`.

Must be registered in the Jira GUI according to the screenshots above.

When triggered, it will log in to CloudShell and restore the resource named in the issue
back to its original CloudShell domains, thus returning it to circulation.

Implemented as a Flask-based Python web server.

Edit the top of `quali_jira_hook.py`:

    quali_url_base = 'http://172.20.7.177:82'
    quali_user = 'admin'
    quali_password = 'admin'
    quali_domain = 'Global'
    worker_blueprint_name = 'UnquarantineWorker'
    
    # a Jira account that has read access to issues
    jira_url_base = 'http://127.0.0.1:2990/jira'
    jira_user = 'admin'
    jira_password = 'admin'


Requires a worker blueprint with a name like `UnquarantineWorker` with script `Unquarantine` attached. This is included in the installable package.

*Be sure to "Publish" the blueprint*, or it can't be used by the sandbox API. 

It is recommended to run the web server on the Jira host, listening on 127.0.0.1 only (port 5000).

Start the web hook:

    pip install requests flask
    export FLASK_APP=quali_jira_hook.py
    flask run

For special situations, set the listening addresses and port according to the Flask documentation.


## Development
- Jira plugin (Java)
  - SDK
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
      - git checkout hooks_refactor
    - Windows
      - Install JDK 8, ensure javac.exe is in PATH
      - Install Jira plugin SDK https://developer.atlassian.com/docs/getting-started/set-up-the-atlassian-plugin-sdk-and-build-a-project
      - Fix PATH and JAVA_HOME in Windows system properties if they were set incorrectly by the Jira SDK
      - In Git Bash:
        - git clone https://github.com/QualiSystemsLab/Jira-Integration.git
        - cd Jira-Integration
        - git checkout hooks_refactor
  - Run Jira server in one command prompt:
    - cd QualiJiraPlugin
    - atlas-run
    - Leave open
    - On Linux, press Ctrl+D (on Windows Ctrl+C), to shut down -- note that it uses an in-memory database so all user data may be lost when exiting
  - In another command prompt, reload the plugin every time the code is changed:
    - cd QualiJiraPlugin
    - atlas-mvn package
- CloudShell package
  - Double click package.cmd
  - In non-`Support` domain, drag Jira_Main_Package.zip into the portal
  - In `Support` domain, drag Jira_Support_Domain_Package.zip into the portal
  - To update:
	- In Git Bash: git clone https://github.com/QualiSystemsLab/Jira-Integration.git
	- Edit files
	- Double click package.cmd
