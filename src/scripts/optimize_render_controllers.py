"""Add part_visibility distance culling to all render controllers."""

import json
import os
import re

PART_VIS_RULE = [{"*": "query.distance_from_camera < 48.0"}]

# Override RCs for missing entities
MISSING_RCS = {
    "evoker": {
        "format_version": "1.10.0",
        "render_controllers": {
            "controller.render.evoker": {
                "geometry": "Geometry.default",
                "materials": [{"*": "Material.default"}],
                "textures": ["Texture.default"],
                "part_visibility": PART_VIS_RULE,
            }
        },
    },
    "pillager": {
        "format_version": "1.10.0",
        "render_controllers": {
            "controller.render.pillager": {
                "geometry": "Geometry.default",
                "materials": [{"*": "Material.default"}],
                "textures": ["Texture.default"],
                "part_visibility": PART_VIS_RULE,
            }
        },
    },
    "ravager": {
        "format_version": "1.10.0",
        "render_controllers": {
            "controller.render.ravager": {
                "geometry": "Geometry.default",
                "materials": [{"*": "Material.default"}],
                "textures": ["Texture.default"],
                "part_visibility": PART_VIS_RULE,
            }
        },
    },
    "vindicator": {
        "format_version": "1.10.0",
        "render_controllers": {
            "controller.render.vindicator": {
                "geometry": "Geometry.default",
                "materials": [{"*": "Material.default"}],
                "textures": ["Texture.default"],
                "part_visibility": PART_VIS_RULE,
            }
        },
    },
}


def try_json_parse(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def try_jsonc_parse(text):
    stripped = re.sub(r"//.*?(\n|$)", "\n", text)
    stripped = re.sub(r"/\*.*?\*/", "", stripped, flags=re.DOTALL)
    return try_json_parse(stripped)


def process_rp(rp_dir):
    rc_dir = os.path.join(rp_dir, "render_controllers")
    if not os.path.isdir(rc_dir):
        print(f"Render controllers dir not found: {rc_dir}")
        return

    files = sorted(f for f in os.listdir(rc_dir) if f.endswith(".json"))
    modified = 0

    for fname in files:
        fpath = os.path.join(rc_dir, fname)

        with open(fpath, "r", encoding="utf-8") as f:
            raw = f.read()

        data = try_json_parse(raw)
        is_jsonc = False
        if data is None:
            data = try_jsonc_parse(raw)
            is_jsonc = True

        if data is None:
            print(f"  Skipping unparseable: {fname}")
            continue

        rcs = data.get("render_controllers", {})
        if not isinstance(rcs, dict):
            continue

        changed = False
        for rc_name, rc_data in rcs.items():
            existing = rc_data.get("part_visibility", [])
            target = [{"*": "query.distance_from_camera < 48.0"}]
            if existing != target:
                rc_data["part_visibility"] = target
                # Remove any other keys that already had part_visibility
                changed = True

        if changed:
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(data, f, separators=(",", ":"))
            modified += 1

    override_dir = os.path.join(
        os.path.dirname(__file__), "..", "overrides", "RP", "entity"
    )
    for name, rc_data in MISSING_RCS.items():
        out_path = os.path.join(rc_dir, f"{name}.render_controllers.json")
        if not os.path.exists(out_path):
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(rc_data, f, separators=(",", ":"))
            print(f"Created: {out_path}")

    print(f"Render controllers: {modified} modified, {len(MISSING_RCS)} missing created")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("samples_dir", help="Path to bedrock-samples root")
    args = parser.parse_args()

    process_rp(os.path.join(args.samples_dir, "resource_pack"))
