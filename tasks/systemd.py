"""
Systemd test
"""
import contextlib
import logging

from cStringIO import StringIO
from teuthology.orchestra import run

log = logging.getLogger(__name__)


@contextlib.contextmanager
def task(ctx, config):
    """
      - tasks:
          ceph-deploy:
          systemd:

    Test ceph systemd services can start, stop and restart and
    check for any failed services and report back errors
    """   
    for remote, roles in ctx.cluster.remotes.iteritems():
        remote.run(args=['sudo', 'ps', '-eaf', run.Raw('|'),
                         'grep', 'ceph'])
        r = remote.run(args=['sudo', 'systemctl', 'list-units', run.Raw('|'),
                             'grep', 'ceph'], stdout=StringIO(),
                       check_status=False)
        if r.stdout.getvalue().find('failed'):
            log.info("Ceph services in failed state")

        # test overall service stop and start
        log.info("Stopping all Ceph services")
        remote.run(args=['sudo', 'systemctl', 'stop', 'ceph.target'])
        r = remote.run(args=['sudo', 'systemctl', 'status', 'ceph.target'],
                       stdout=StringIO(), check_status=False)
        if r.stdout.getvalue().find('Active: inactive'):
            log.info("Sucessfully stopped all ceph services")
        else:
            log.info("Failed to stop ceph services")
        log.info("Starting all Ceph services")
        remote.run(args=['sudo', 'systemctl', 'start', 'ceph.target'])
        r = remote.run(args=['sudo', 'systemctl', 'status', 'ceph.target'],
                       stdout=StringIO())
        if r.stdout.getvalue().find('Active: active'):
            log.info("Sucessfully started all Ceph services")
        else:
            log.info("info", "Failed to start Ceph services")
        remote.run(args=['sudo', 'ps', '-eaf', run.Raw('|'),
                         'grep', 'ceph'])

        # test individual services start stop
        name = remote.shortname
        mon_name = 'ceph-mon@' + name + '.service'
        mds_name = 'ceph-mds@' + name + '.service'
        if 'osd.0' in roles:
            remote.run(args=['sudo', 'systemctl', 'status',
                             'ceph-osd@0.service'])
            remote.run(args=['sudo', 'systemctl', 'stop',
                             'ceph-osd@0.service'])
            r = remote.run(args=['sudo', 'systemctl', 'status', 'ceph.target'],
                           stdout=StringIO(), check_status=False)
            if r.stdout.getvalue().find('Active: inactive'):
                log.info("Sucessfully stopped single osd ceph service")
            else:
                log.info("Failed to stop ceph osd services")
            remote.run(args=['sudo', 'systemctl', 'start',
                             'ceph-osd@0.service'])
        elif mon_name in roles:
            remote.run(args=['sudo', 'systemctl', 'status', mon_name])
            remote.run(args=['sudo', 'systemctl', 'stop', mon_name])
            r = remote.run(args=['sudo', 'systemctl', 'status', 'ceph.target'],
                           stdout=StringIO(), check_status=False)
            if r.stdout.getvalue().find('Active: inactive'):
                log.info("Sucessfully stopped single mon ceph service")
            else:
                log.info("Failed to stop ceph mon service")
            remote.run(args=['sudo', 'systemctl', 'start', mon_name])
        elif mds_name in roles:
            remote.run(args=['sudo', 'systemctl', 'status', mds_name])
            remote.run(args=['sudo', 'systemctl', 'stop', mds_name])
            r = remote.run(args=['sudo', 'systemctl', 'status', 'ceph.target'],
                           stdout=StringIO(), check_status=False)
            if r.stdout.getvalue().find('Active: inactive'):
                log.info("Sucessfully stopped single ceph mds service")
            else:
                log.info("Failed to stop ceph mds service")
            remote.run(args=['sudo', 'systemctl', 'start', mds_name])

    yield
