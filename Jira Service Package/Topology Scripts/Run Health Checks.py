from cloudshell.api.cloudshell_api import InputNameValue
from cloudshell.api.common_cloudshell_api import CloudShellAPIError
from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers

NO_DRIVER_ERR = "129"
DRIVER_FUNCTION_ERROR = "151"
MISSING_COMMAND_ERROR = '101'


def _run_health_checks(api, reservation_id):
    api.WriteMessageToReservationOutput(reservation_id, 'Running health checks')
    rd = api.GetReservationDetails(reservation_id).ReservationDescription
    errors = []
    for r in rd.Resources:
        try:
            # logger.info("Executing health check command on resource {0}".format(r.Name))
            o = api.ExecuteCommand(reservation_id, r.Name, 'Resource', 'health_check', []).Output
            if 'fail' in o.lower():
                raise CloudShellAPIError(999, o, o)
            api.WriteMessageToReservationOutput(reservation_id, o)
        except CloudShellAPIError as exc:
            if exc.code not in (NO_DRIVER_ERR,
                                DRIVER_FUNCTION_ERROR,
                                MISSING_COMMAND_ERROR):
                # logger.error("Error executing health check command on resource {0}. Error: {1}".format(r.Name, exc.rawxml))
                errmsg = 'Health check failed on "{0}": {1}'.format(r.Name, exc.message)
                api.WriteMessageToReservationOutput(reservation_id, errmsg)
                errors.append(errmsg)

                for svc in rd.Services:
                    for c in api.GetServiceCommands(svc.ServiceName).Commands:
                        if 'handle_resource_error' in c.Name:
                            api.WriteMessageToReservationOutput(reservation_id,
                                                                'Running error handler on %s' % svc.Alias)
                            eo = api.ExecuteCommand(reservation_id, svc.Alias, 'Service', c.Name, [
                                InputNameValue('resource_name', r.Name),
                                InputNameValue('error_message', exc.message),
                            ], printOutput=True).Output
                            # api.WriteMessageToReservationOutput(self.reservation_id, eo)
    if errors:
        print 'Please terminate the sandbox and try again:\n' + '\n'.join(errors)
        exit(1)


_run_health_checks(helpers.get_api_session(), helpers.get_reservation_context_details().id)