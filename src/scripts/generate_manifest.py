import json
import argparse
from uuid import uuid4

RP_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
BP_UUID = "b3c4d5e6-f7a8-9012-bcde-f34567890123"
RP_MODULE_UUID = "b2c3d4e5-f6a7-8901-bcde-f23456789012"
BP_MODULE_UUID = "c4d5e6f7-a8b9-0123-cdef-456789012345"


def make_manifest(pack_type, version_str, pack_uuid, module_uuid, is_rp):
    parts = version_str.split(".")
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

    manifest = {
        "format_version": 2,
        "header": {
            "name": "Clearleaf Optimized",
            "description": "Bedrock performance optimization pack - entity culling, particle reduction, rendering optimization & despawn tuning. Maintains vanilla gameplay while reducing lag.",
            "uuid": pack_uuid,
            "version": [major, minor, patch],
            "min_engine_version": [major, minor, patch],
        },
        "modules": [
            {
                "type": pack_type,
                "uuid": module_uuid,
                "version": [major, minor, patch],
            }
        ],
    }

    if not is_rp:
        manifest["dependencies"] = [
            {"uuid": RP_UUID, "version": [major, minor, patch]}
        ]

    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--rp", action="store_true")
    parser.add_argument("--bp", action="store_true")
    parser.add_argument("--output", default=".")
    args = parser.parse_args()

    if args.rp:
        m = make_manifest("resources", args.version, RP_UUID, RP_MODULE_UUID, True)
        path = f"{args.output}/resource_pack/manifest.json"
        with open(path, "w") as f:
            json.dump(m, f, indent=2)
        print(f"RP manifest written: {path}")

    if args.bp:
        m = make_manifest("data", args.version, BP_UUID, BP_MODULE_UUID, False)
        path = f"{args.output}/behavior_pack/manifest.json"
        with open(path, "w") as f:
            json.dump(m, f, indent=2)
        print(f"BP manifest written: {path}")
