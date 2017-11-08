import json
import re

import os

from cloudshell.api.cloudshell_api import InputNameValue
from cloudshell.core.logger.qs_logger import get_qs_logger
from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers

api = helpers.get_api_session()
resid = helpers.get_reservation_context_details().id

rc = json.loads(os.environ['RESOURCECONTEXT'])
destdomain = rc['attributes']['Support Domain']
error_pattern = rc['attributes'].get('Live Status Error Regex', 'error')

logger = get_qs_logger(log_group=resid, log_file_prefix='ResourceQuarantine')

rd = api.GetReservationDetails(resid).ReservationDescription

logger.info('Error pattern: %s' % error_pattern)

for r in rd.Resources:
    resource_name = r.Name
    logger.info('Resource: %s' % resource_name)
    ls = api.GetResourceLiveStatus(resource_name)
    status = str(ls.liveStatusName) + ': ' + str(ls.liveStatusDescription)
    if re.search(error_pattern, status, re.IGNORECASE):
        logger.info('Matched')
        doms = api.GetResourceDetails(resource_name, True).Domains

        logger.info('Current domains: ' % [dom.Name for dom in doms])

        logger.info('Removing %s from reservation %s' % (resource_name, resid))
        api.RemoveResourcesFromReservation(resid, [resource_name])

        logger.info('Adding %s to domain %s' % (resource_name, destdomain))
        api.AddResourcesToDomain(destdomain, [resource_name])

        if doms and doms[0].Name:
            for dom in doms:
                if dom.Name != destdomain:
                    logger.info('Removing %s from domain %s' % (resource_name, dom.Name))
                    api.RemoveResourcesFromDomain(dom.Name, [resource_name])
        else:
            logger.info('No domains to remove from')

        api.WriteMessageToReservationOutput(resid, 'Moved resource %s from domain(s) %s to quarantine domain %s' % (resource_name, [dom.Name for dom in doms], destdomain))

        for s in rd.Services:
            for command in api.GetServiceCommands(s.ServiceName).Commands:
                if 'quarantine_handler' in command.Name.lower():
                    logger.info('Executing %s.%s(%s, %s, %s)' % (
                        s.Alias,
                        command.Name,
                        resource_name,
                        ','.join([dom.Name for dom in doms]),
                        destdomain,
                    ))
                    api.WriteMessageToReservationOutput(resid, 'Executing %s.%s(%s)' % (s.Alias, command.Name, resource_name))
                    o = api.ExecuteCommand(resid, s.Alias, 'Service', command.Name, [
                        InputNameValue('subject_name', resource_name),
                        InputNameValue('blueprint_or_resource', 'RESOURCE'),
                        InputNameValue('error_details', status),
                        InputNameValue('original_domains_csv', ','.join([dom.Name for dom in doms])),
                        InputNameValue('support_domain', destdomain),
                    ]).Output
                    logger.info('Output: %s' % o)
                    api.WriteMessageToReservationOutput(resid, 'Output: %s' % o)
