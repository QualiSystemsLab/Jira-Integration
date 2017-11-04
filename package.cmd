mkdir pkg
mkdir pkg\Categories
mkdir pkg\DataModel
mkdir "pkg\Resource Scripts"
mkdir "pkg\Topology Scripts"
mkdir "pkg\Topologies"
mkdir "pkg\Resources"

copy "Jira Service Package\Resources\*" pkg\Resources
copy "Jira Service Package\Topologies\*" pkg\Topologies


copy "Jira Service Package\metadata.xml"                   pkg
copy "Jira Service Package\Categories\categories.xml"      pkg\Categories
copy "Jira Service Package\DataModel\datamodel.xml"        pkg\DataModel

copy "Jira Service Package\Resource Scripts\health_check.py" "pkg\Resource Scripts"
copy "Jira Service Package\Topology Scripts\Unquarantine.py" "pkg\Topology Scripts"

cd "Jira Service Package\Topology Scripts\hook_setup"
set fn="..\..\..\pkg\Topology Scripts\hook_setup.zip"
"c:\Program Files\7-Zip\7z.exe" a %fn% *
cd ..\..\..

cd "Jira Service Package\Topology Scripts\hook_teardown"
set fn="..\..\..\pkg\Topology Scripts\hook_teardown.zip"
"c:\Program Files\7-Zip\7z.exe" a %fn% *
cd ..\..\..


cd "Jira Service Package\Resource Scripts\health_check_orch_hook_post_setup"
set fn="..\..\..\pkg\Resource Scripts\health_check_orch_hook_post_setup.zip"
"c:\Program Files\7-Zip\7z.exe" a %fn% *
cd ..\..\..

cd "Jira Service Package\Resource Scripts\quarantine_resources_orch_hook_post_teardown"
set fn="..\..\..\pkg\Resource Scripts\quarantine_resources_orch_hook_post_teardown.zip"
"c:\Program Files\7-Zip\7z.exe" a %fn% *
cd ..\..\..

cd "Jira Service Package\Resource Scripts\quarantine_blueprint_orch_hook_post_teardown"
set fn="..\..\..\pkg\Resource Scripts\quarantine_blueprint_orch_hook_post_teardown.zip"
"c:\Program Files\7-Zip\7z.exe" a %fn% *
cd ..\..\..

cd "Jira Service Package\Resource Scripts\jira_quarantine_handler"
set fn="..\..\..\pkg\Resource Scripts\jira_quarantine_handler.zip"
"c:\Program Files\7-Zip\7z.exe" a %fn% *
cd ..\..\..



cd pkg
set fn="..\Jira_Package.zip"
del %fn%
"c:\Program Files\7-Zip\7z.exe" a %fn% *
cd ..

rmdir /s /q pkg
