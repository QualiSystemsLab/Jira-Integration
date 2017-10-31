cd "Health Check Sandbox Setup"
set fn="..\Jira Service Package\Topology Scripts\Health Check Sandbox Setup.zip"
del %fn%
"c:\Program Files\7-Zip\7z.exe" a %fn% *
cd ..

cd "Error Handler Sandbox Teardown"
set fn="..\Jira Service Package\Topology Scripts\Error Handler Sandbox Teardown.zip"
del %fn%
"c:\Program Files\7-Zip\7z.exe" a %fn% *
cd ..


cd "health_check_orch_hook_post_setup"
set fn="..\Jira Service Package\Resource Scripts\health_check_orch_hook_post_setup.zip"
del %fn%
"c:\Program Files\7-Zip\7z.exe" a %fn% *
cd ..



cd "Jira Service Package"
set fn="..\Jira Service Package.zip"
del %fn%
"c:\Program Files\7-Zip\7z.exe" a %fn% *
cd ..


cd "Jira Support Domain Package"
set fn="..\Jira Support Domain Package.zip"
del %fn%
"c:\Program Files\7-Zip\7z.exe" a %fn% *
cd ..
