from cloudshell.helpers.scripts import cloudshell_scripts_helpers as helpers
import os

resname = os.environ['RESERVATION_NAME']
dutname = os.environ['RESOURCE_NAME']
user = os.environ['USER']
duration = int(os.environ['DURATION_IN_MINUTES'])

api = helpers.get_api_session()

resid = api.CreateImmediateReservation(resname, user, duration).Reservation.Id

api.AddResourcesToReservation(resid, [dutname])

print resid