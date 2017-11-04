from cloudshell.core.logger.qs_logger import get_qs_logger
from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers
from cloudshell.api.common_cloudshell_api import CloudShellAPIError

api = helpers.get_api_session()
resid = helpers.get_reservation_context_details().id

logger = get_qs_logger(log_group=resid, log_file_prefix='HealthCheck')

api.WriteMessageToReservationOutput(resid, 'Running health checks...')
rd = api.GetReservationDetails(resid).ReservationDescription
errors = []
for r in rd.Resources:
    try:
        logger.info("Executing health check command on resource {0}".format(r.Name))
        o = api.ExecuteCommand(resid, r.Name, 'Resource', 'health_check', []).Output
        if 'fail' in o.lower():
            raise CloudShellAPIError(999, o, o)
        api.WriteMessageToReservationOutput(resid, o)
    except CloudShellAPIError as exc:
        if exc.code not in ('129', '151', '101'):
            logger.error("Error executing health check command on resource {0}. Error: {1}".format(r.Name, exc.rawxml))
            errmsg = 'Health check failed on "{0}": {1}'.format(r.Name, exc.message)
            api.WriteMessageToReservationOutput(resid, errmsg)
            errors.append(errmsg)

if errors:
    print 'Please terminate the sandbox and try again:\n' + '\n'.join(errors)
    exit(1)
