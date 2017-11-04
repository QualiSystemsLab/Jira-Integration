import json

import os
import requests
from cloudshell.core.logger.qs_logger import get_qs_logger
from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers

rc = json.loads(os.environ['RESOURCECONTEXT'])
destdomain = rc['attributes']['Support Domain']

api = helpers.get_api_session()
resid = helpers.get_reservation_context_details().id

logger = get_qs_logger(log_group=resid, log_file_prefix='BlueprintQuarantine')

urlbase = 'http://%s:82' % helpers.get_connectivity_context_details().server_address

token = requests.put('%s/api/login' % urlbase,
                     headers={
                         'Content-Type': 'application/json',
                     },
                     data=json.dumps({
                         'username': helpers.get_connectivity_context_details().admin_user,
                         'password': helpers.get_connectivity_context_details().admin_pass,
                         'domain': helpers.get_reservation_context_details().domain
                     })).text.replace('"', '')

activity = json.loads(requests.get('%s/api/v2/sandboxes/%s/activity?error_only=true' % (urlbase, resid)).text)

rd = api.GetReservationDetails(resid).ReservationDescription

found = False
for ev in activity['events']:
    if ev['event_type'] == 'error':
        if "'Setup'" in ev['event_text'] or "'Setup script'" in ev['event_text']:
            found = True
            break

if found:
    olddomain = rd.DomainName
    if olddomain != destdomain:
        api.AddTopologiesToDomain(destdomain, rd.Topologies)
        api.RemoveTopologiesFromDomain(olddomain, rd.Topologies)

    olddomains = olddomain
    for s in rd.Services:
        for command in api.GetServiceCommands(s.ServiceName).Commands:
            if 'quarantine_handler' in command.Name.lower():
                for topo in rd.Topologies:
                    errdet = json.dumps(activity, indent=4, separators=(',', ': '))
                    m = 'Executing %s.%s(%s, BLUEPRINT, %s, %s, %s)' % (
                        s.Alias,
                        command.Name,

                        topo,
                        errdet,
                        olddomains,
                        destdomain,
                    )
                    logger.info(m)
                    api.WriteMessageToReservationOutput(resid, m)
                    o = api.ExecuteServiceCommand(resid, s.Alias, command.Name, [
                        topo,
                        'BLUEPRINT',
                        errdet,
                        olddomains,
                        destdomain,
                    ]).Output
                    logger.info('Output: %s' % o)
                    api.WriteMessageToReservationOutput(resid, 'Output: %s' % o)
