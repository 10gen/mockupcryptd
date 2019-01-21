# Test mockupcryptd.

import mockupcryptd

def test_schema_parsing():
    schema = {
        "bsonType": "object",
        "properties":
            {
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
                        "keyVaultURI": "mongodb://localhost:27017/admin"
                    }
                }
            }

    }
    encrypt_map = {}
    import sys
    print("sys.path=")
    print(sys.path)
    mockupcryptd.build_encrypt_map(encrypt_map, schema)
    assert "ssn" in encrypt_map
    assert encrypt_map["ssn"] == schema["properties"]["ssn"]["encrypt"]

def main():
    test_schema_parsing()
    print("Tests pass")