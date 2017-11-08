mkdir pkg
mkdir pkg\Categories
mkdir pkg\DataModel
mkdir "pkg\Resource Scripts"
mkdir "pkg\Topology Scripts"
mkdir "pkg\Topologies"
mkdir "pkg\Resources"

copy "Jira Main Package\Resources\*" pkg\Resources
copy "Jira Main Package\Topologies\*" pkg\Topologies


copy "Jira Main Package\metadata.xml"                   pkg
copy "Jira Main Package\Categories\categories.xml"      pkg\Categories
copy "Jira Main Package\DataModel\datamodel.xml"        pkg\DataModel

copy "Jira Main Package\Resource Scripts\health_check.py" "pkg\Resource Scripts"
copy "Jira Main Package\Topology Scripts\Unquarantine.py" "pkg\Topology Scripts"

cd "Jira Main Package\Topology Scripts\hook_setup"
set fn="..\..\..\pkg\Topology Scripts\hook_setup.zip"
"c:\Program Files\7-Zip\7z.exe" a %fn% *
cd ..\..\..

cd "Jira Main Package\Topology Scripts\hook_teardown"
set fn="..\..\..\pkg\Topology Scripts\hook_teardown.zip"
"c:\Program Files\7-Zip\7z.exe" a %fn% *
cd ..\..\..


cd "Jira Main Package\Resource Scripts\health_check_orch_hook_post_setup"
set fn="..\..\..\pkg\Resource Scripts\health_check_orch_hook_post_setup.zip"
"c:\Program Files\7-Zip\7z.exe" a %fn% *
cd ..\..\..

cd "Jira Main Package\Resource Scripts\quarantine_resources_orch_hook_post_teardown"
set fn="..\..\..\pkg\Resource Scripts\quarantine_resources_orch_hook_post_teardown.zip"
"c:\Program Files\7-Zip\7z.exe" a %fn% *
cd ..\..\..

cd "Jira Main Package\Resource Scripts\quarantine_blueprint_orch_hook_post_teardown"
set fn="..\..\..\pkg\Resource Scripts\quarantine_blueprint_orch_hook_post_teardown.zip"
"c:\Program Files\7-Zip\7z.exe" a %fn% *
cd ..\..\..

cd "Jira Main Package\Resource Scripts\jira_quarantine_handler"
set fn="..\..\..\pkg\Resource Scripts\jira_quarantine_handler.zip"
"c:\Program Files\7-Zip\7z.exe" a %fn% *
cd ..\..\..



cd pkg
set fn="..\Jira_Main_Package.zip"
del %fn%
"c:\Program Files\7-Zip\7z.exe" a %fn% *
cd ..

rmdir /s /q pkg


mkdir pkg
mkdir pkg\Categories
mkdir pkg\DataModel
mkdir "pkg\Topology Scripts"
mkdir "pkg\Topologies"

copy "Jira Support Domain Package\Topologies\*" pkg\Topologies
copy "Jira Support Domain Package\Topology Scripts\*" "pkg\Topology Scripts"


copy "Jira Support Domain Package\metadata.xml"                   pkg
copy "Jira Support Domain Package\Categories\categories.xml"      pkg\Categories
copy "Jira Support Domain Package\DataModel\datamodel.xml"        pkg\DataModel


cd pkg
set fn="..\Jira_Support_Domain_Package.zip"
del %fn%
"c:\Program Files\7-Zip\7z.exe" a %fn% *
cd ..

rmdir /s /q pkg
