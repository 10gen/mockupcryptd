# Test mockupcryptd.

import pymongo
import mockupcryptd
import os
import sys
import signal

example_schema = {
    "bsonType": "object",
    "properties": {
        "ssn": {
                "encrypt": {
                    "type": "string",
                    "algorithm": "Randomized",
                    "keyId": {
                        "$binary": {
                            "base64": "1+niXaxyRL6AB6xRzUp/Ew==",
                            "subType": "04"
                        }
                    },
                    "keyVaultAlias": "default"
                }
        }
    }
}


def test_schema_parsing():
    encrypt_map = {}
    mockupcryptd.build_encrypt_map(encrypt_map, example_schema)
    assert "ssn" in encrypt_map
    assert encrypt_map["ssn"] == example_schema["properties"]["ssn"]["encrypt"]


def test_marking():
    mockupcryptd.version = "spec"
    marking = mockupcryptd.make_marking(
        {"algorithm": "det", "keyVaultAlias": "kva", "iv": "an iv", "keyId": "my key id"}, "test")
    parsed = mockupcryptd.parse_marking(marking)
    assert parsed == {'v': 'test', 'a': 'det',
                      'va': 'kva', 'iv': 'an iv', 'ki': 'my key id'}

def live_test (test_fn):
    started_mockupcryptd = False
    if not os.path.exists("/tmp/mongocryptd.sock"):
        print("mockupcryptd not detected to be running, starting for test")
        newpid = os.fork()
        if newpid == 0:
            print("Child starting mockupcryptd")
            mockupcryptd.main()
            sys.exit(0)
        started_mockupcryptd = True
    client = pymongo.MongoClient("mongodb://%2Ftmp%2Fmongocryptd.sock")
    test_fn(client)
    if started_mockupcryptd:
        os.kill(newpid, signal.SIGINT)
        os.wait()

def test_find_cmd(client):
    db = client["admin"]
    resp = db.command({
        "find": "collection",
        "filter": {
            "ssn": "123-45-6789",
        },
        "jsonSchema": example_schema
    })
    print(resp)

def main():
    test_schema_parsing()
    test_marking()
    live_test(test_find_cmd)
    print("All tests pass")
