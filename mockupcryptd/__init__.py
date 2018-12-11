import logging
import os
import sys

from daemon import (DaemonContext, pidfile)
import mockupdb._bson as bson
from mockupdb import interactive_server


def mark_recurse (doc):
    if isinstance (doc, dict):
        for key in doc:
            if key == "encryptMe":
                data = bson.BSON.encode({
                    "k": "123",
                    "v": doc[key],
                    "iv": bson.Binary(b"\x00\x01\x02\x03\x00\x01\x02\x03\x00\x01\x02\x03\x00\x01\x02\x03")
                })
                bin = bson.Binary(data, subtype=7)
                doc[key] = bin

            elif isinstance(doc[key], dict):
                mark_recurse(doc[key])
            elif isinstance (doc[key], list):
                mark_recurse(doc[key])
    elif isinstance (doc, list):
        for el in doc:
            if isinstance(el, dict):
                mark_recurse(el)
            elif isinstance (el, list):
                mark_recurse(el)
    else:
        raise Exception("Must recurse on list or dict")


def mark_fields(r):
    try:
        data = r.doc['data']
        schema = r.doc['schema']
    except KeyError as exc:
        r.command_err(errmsg="Missing argument {}".format(exc))
        return

    if not isinstance(data, list):
        r.command_err(errmsg="'data' must be array of documents")
        return

    for doc in data:
        mark_recurse (doc)

    logging.info('markFields with {n} documents'.format(n=len(data)))
    r.ok(data=data)


def start_server():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    uds_path = '/tmp/mongocryptd.sock'
    server = interactive_server(uds_path=uds_path, name='mockupcryptd')
    server.run()
    print('Listening with domain socket %s' % (uds_path,))
    print('URI is %s' % (server.uri,))

    try:
        # Process each request.
        for r in server:
            try:
                if r.command_name == 'markFields':
                    mark_fields(r)
                elif r.command_name == 'shutdown':
                    return
                else:
                    r.command_err(
                        errmsg='Unrecognized request: {r}'.format(r=r))
            except Exception as exc:
                logging.exception('Processing %s' % (r,))
                r.command_err(
                    errmsg='Internal error processing {r}: {exc!r}'.format(
                        r=r, exc=exc))
    except KeyboardInterrupt:
        pass
    finally:
        logging.info('Shutting down')
        server.stop()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--daemonize":
        base_dir = "/usr/local"
        # PID lock file acts as a mutex, only allowing one daemon to run.
        pid_file = pidfile.TimeoutPIDLockFile(
            base_dir + "/var/run/mockupcryptd.pid")
        log_file = open(base_dir + "/var/log/mockupcryptd.log", "w")

        if pid_file.is_locked():
            with open(pid_file.path, "r") as f:
                print("Daemon already running with PID=%s" % f.read())
                sys.exit(0)

        print("Running as a background process")
        print("PID=%s" % os.getpid())
        print("Logging to %s" % log_file.name)
        with DaemonContext(
                pidfile=pid_file,
                stdout=log_file,
                stderr=log_file):
            start_server()
    else:
        start_server()
