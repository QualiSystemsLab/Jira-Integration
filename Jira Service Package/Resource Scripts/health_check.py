import cloudshell.helpers.scripts.cloudshell_scripts_helpers as helpers

api = helpers.get_api_session()
fullname = helpers.get_resource_context_details().fullname

if 'DUT 2' in fullname:
    rv = 'Health check on resource %s failed: Device not responding' % fullname
    api.SetResourceLiveStatus(fullname, 'Error', rv)
else:
    rv = 'Health check on resource %s passed' % fullname
    api.SetResourceLiveStatus(fullname, 'Online', rv)
print rv