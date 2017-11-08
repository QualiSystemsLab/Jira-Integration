import cloudshell.helpers.scripts.cloudshell_scripts_helpers as helpers
import os

api = helpers.get_api_session()

csuser = helpers.get_reservation_context_details().owner_user

resid = helpers.get_reservation_context_details().id

resource_or_blueprint_name = os.environ['SUBJECT_NAME']
blueprint_or_resource = os.environ['BLUEPRINT_OR_RESOURCE'].upper()
original_domains_csv = os.environ['ORIGINAL_DOMAINS_CSV']
supportdomain = os.environ['SUPPORT_DOMAIN']

orgdoms = [x.strip() for x in original_domains_csv.split(',')]
if orgdoms and not orgdoms[0]:
    orgdoms = []


if blueprint_or_resource == 'RESOURCE':
    resource_name = resource_or_blueprint_name
    print 'Found domains=%s, resource name=%s' % (orgdoms, resource_name)

    for r in api.FindResources('', '', [], True, resource_name, True, False).Resources:
        for rr in r.Reservations:
            try:
                api.RemoveResourcesFromReservation(rr.ReservationId, [resource_name])
                print 'Removed resource from sandbox %s\n' % rr.ReservationId
            except:
                print 'Warning: Failed to remove resource from sandbox %s\n' % rr.ReservationId
    try:
        api.RemoveResourcesFromReservation(resid, [resource_name])
        print 'Removed resource from sandbox %s\n' % resid

    except:
        print 'Warning: Failed to remove resource from sandbox %s' % resid

    api.RemoveResourcesFromDomain(supportdomain, [resource_name])
    print 'Removed resource %s from domain %s\n' % (resource_name, supportdomain)

    for dom in orgdoms:
        api.AddResourcesToDomain(dom, [resource_name])
        print 'Added resource %s to domain %s\n' % (resource_name, dom)

    api.SetResourceLiveStatus(resource_name, 'Online', '')
else:
    bp_name = resource_or_blueprint_name
    print 'Found domains=%s, blueprint name=%s' % (orgdoms, bp_name)
    for dom in orgdoms:
        if dom != supportdomain:
            api.AddTopologiesToDomain(dom, [bp_name])
            api.RemoveTopologiesFromDomain(supportdomain, [bp_name])
            print 'Added blueprint %s to domain %s\n' % (bp_name, dom)

print 'Unquarantined %s' % resource_or_blueprint_name

