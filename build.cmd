cd "Health Check Sandbox Setup"
set fn="..\Jira Service Package\Topology Scripts\Health Check Sandbox Setup.zip"
del %fn%
"c:\Program Files\7-Zip\7z.exe" a %fn% *
cd ..

cd "Jira Service Package"
set fn="..\Jira Service Package.zip"
del %fn%
"c:\Program Files\7-Zip\7z.exe" a %fn% *
cd ..
