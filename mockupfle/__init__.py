import logging
import sys

from bson import Binary
from mockupdb import interactive_server


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
        if 'encryptMe' in doc:
            # Let's say subtype 7 means "marked for encryption."
            doc['encryptMe'] = Binary(b'', subtype=7)

    logging.info('markFields with {n} documents'.format(n=len(data)))
    r.ok(data=data)


def main():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    uds_path = '/tmp/mongofle.sock'
    server = interactive_server(uds_path=uds_path, name='mockupfle')
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
