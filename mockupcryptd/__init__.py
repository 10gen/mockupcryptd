import logging
import os
import sys

from daemon import (DaemonContext, pidfile)
import bson
from mockupdb import interactive_server
from  bson import json_util

version = "pre-spec"
# The "pre-spec" version:
# - markings were just BSON documents.
# - schemas had a URI instead of an alias.
#
# The "spec" version is the latest described in the drivers spec.

def make_marking(encrypt_schema_doc, value):
    """
    Given the "encrypt" document of the JSON schema for a field and a BSON value, generate the FLE marking.
    """
    pass


def full_path(path_prefix, key):
    if path_prefix != "":
        return path_prefix + "." + key
    return key


def build_encrypt_map(map, schema, path_prefix=""):
    """
    Given a schema, build a map from a dotted field path to a dictionary with encryption info.
    If a property has an 'encrypt' field, it is considered encrypted.
    This *does not* support encryptMetadata in any way, nor does it recurse into arrays.
    """
    if "properties" in schema:
        for key, prop in schema["properties"].items():
            if "encrypt" in prop:
                encrypt_spec = prop["encrypt"]
                print(json_util.dumps(encrypt_spec))
                if "keyId" not in encrypt_spec and "keyAltName" not in encrypt_spec:
                    raise Exception(
                        "encrypt spec must have keyId or keyAltName: {}".format(encrypt_spec))
                if "keyVaultURI" not in encrypt_spec:
                    raise Exception(
                        "encrypt spec must have keyVaultURI: {}".format(encrypt_spec))
                if "algorithm" not in encrypt_spec:
                    raise Exception(
                        "encrypt spec must have algorithm: {}".format(encrypt_spec))
                map[full_path(path_prefix, key)] = encrypt_spec
            elif "bsonType" in prop and prop["bsonType"] == "object":
                build_encrypt_map(
                    map, prop, path_prefix=full_path(path_prefix, key))


def mark_recurse(doc, encrypt_map, path_prefix=""):
    if isinstance(doc, dict):
        for key in doc:
            path = full_path(path_prefix, key)
            print("processing {}".format(path))
            if path in encrypt_map:
                print("  ENCRYPT")
                # should be encrypted.
                encrypt_spec = encrypt_map[path]
                marking = {
                    "v": doc[key],
                    "a": encrypt_spec["algorithm"],
                    "u": encrypt_spec["keyVaultURI"]
                }
                if "keyId" in encrypt_spec:
                    marking["k"] = encrypt_map[path]["keyId"]
                elif "keyAltName" in encrypt_spec:
                    marking["k"] = encrypt_map[path]["keyAltName"]

                if "iv" in encrypt_spec:
                    marking["iv"] = encrypt_spec["iv"]

                data = bson.BSON.encode(marking, codec_options=bson.CodecOptions(
                    uuid_representation=bson.binary.UUID_SUBTYPE))
                doc[key] = bson.Binary(data, subtype=6)

            elif isinstance(doc[key], dict):
                mark_recurse(doc[key], encrypt_map,
                             path_prefix=full_path(path_prefix, key))
            elif isinstance(doc[key], list):
                mark_recurse(doc[key], encrypt_map,
                             path_prefix=full_path(path_prefix, key))
    elif isinstance(doc, list):
        i = 0
        for el in doc:
            if isinstance(el, dict):
                mark_recurse(el, encrypt_map,
                             path_prefix=full_path(path_prefix, i))
            elif isinstance(el, list):
                mark_recurse(el, encrypt_map,
                             path_prefix=full_path(path_prefix, i))
            i += 1
    else:
        raise Exception("Must recurse on list or dict")


def mark_fields(r):
    global version
    if "jsonSchema" in r.doc:
        version = "spec"
    else:
        version = "pre-spec"

    if version == "pre-spec":
        try:
            data = r.doc['data']
            schema = r.doc['schema']
        except KeyError as exc:
            r.command_err(errmsg="Missing argument {}".format(exc))
            return
        if not isinstance(data, list):
            r.command_err(errmsg="'data' must be array of documents")
            return
    elif version == "spec":
        data = r.doc.copy()
        del data["jsonSchema"]


    encrypt_map = {}
    build_encrypt_map(encrypt_map, schema)
    print("Encrypt map:", encrypt_map)

    if version == "pre-spec":
        try:
            for doc in data:
                mark_recurse(doc, encrypt_map)
                print("result={}".format(doc))
        except Exception as e:
            r.command_err(errmsg=str(e))
            return
    elif version == "spec":
        try:
            mark_recurse(data, encrypt_map)
            print("result={}".format(doc))
        except Exception as e:
            r.command_err(errmsg=str(e))
            return

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
                elif r.command_name == 'hasEncryptedFields':
                    pass  # TODO
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
