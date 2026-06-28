"""LOD scaling, animation culling, and BP despawn overrides for all entities."""

import json
import os
import sys

SKIP_IDS = {
    "minecraft:boat", "minecraft:chest_boat", "minecraft:minecart",
    "minecraft:hopper_minecart", "minecraft:tnt_minecart",
    "minecraft:command_block_minecart", "minecraft:bed",
    "minecraft:player", "minecraft:ender_crystal",
    "minecraft:eye_of_ender_signal", "minecraft:leash_knot",
    "minecraft:item", "minecraft:xp_orb",
    "minecraft:dragon_fireball", "minecraft:shot_arrow",
    "minecraft:arrow", "minecraft:snowball", "minecraft:egg",
    "minecraft:ender_pearl", "minecraft:lingering_potion",
    "minecraft:xp_bottle", "minecraft:trident",
    "minecraft:agent", "minecraft:npc",
}

MISSING_ENTITIES = {
    "evoker": {
        "identifier": "minecraft:evoker",
        "materials": {"default": "evoker"},
        "textures": {"default": "textures/entity/illager/evoker"},
        "geometry": {"default": "geometry.evoker.v1.8"},
        "spawn_egg": {"base_color": 0x7B7B7B, "overlay_color": 0x959595},
    },
    "pillager": {
        "identifier": "minecraft:pillager",
        "materials": {"default": "pillager"},
        "textures": {"default": "textures/entity/illager/pillager"},
        "geometry": {"default": "geometry.pillager"},
        "spawn_egg": {"base_color": 0x7B7B7B, "overlay_color": 0xC4C4C4},
    },
    "ravager": {
        "identifier": "minecraft:ravager",
        "materials": {"default": "ravager"},
        "textures": {"default": "textures/entity/illager/ravager"},
        "geometry": {"default": "geometry.ravager"},
        "spawn_egg": {"base_color": 0xCCCCCC, "overlay_color": 0x888888},
    },
    "vindicator": {
        "identifier": "minecraft:vindicator",
        "materials": {"default": "vindicator"},
        "textures": {"default": "textures/entity/illager/vindicator"},
        "geometry": {"default": "geometry.vindicator.v1.8"},
        "spawn_egg": {"base_color": 0x7B7B7B, "overlay_color": 0xCEB5A5},
    },
}

LOD_SCALE = "query.distance_from_camera < 24 ? 1.0 : (query.distance_from_camera < 48 ? 0.5 : 0.001)"
DISTANCE_FACTOR = "variable.distance_factor = query.camera_distance_range_lerp(0, 64);"


def is_nuisance(entity_data):
    components = entity_data.get("minecraft:entity", {}).get("components", {})
    component_groups = entity_data.get("minecraft:entity", {}).get("component_groups", {})

    def has_component(name):
        if name in components:
            return True
        for group in component_groups.values():
            if name in group:
                return True
        return False

    if has_component("minecraft:breedable") or has_component("minecraft:tameable"):
        return False

    health = components.get("minecraft:health", {}).get("max", 0)
    coll = components.get("minecraft:collision_box", {})
    area = coll.get("width", 1) * coll.get("height", 1)

    if area == 0:
        area = 999

    return health <= 10 and area <= 0.5


def get_despawn_params(identifier, entity_data):
    nuisance = is_nuisance(entity_data)
    if nuisance:
        return {
            "despawn_from_distance": {"min_distance": 32, "max_distance": 48},
            "despawn_from_inactivity": {
                "min_range_inactivity_timer": 10,
                "min_time": 20,
                "max_time": 60,
            },
            "remove_when_out_of_range": True,
        }, "nuisance"
    else:
        return {
            "despawn_from_distance": {"min_distance": 48, "max_distance": 64},
            "despawn_from_inactivity": {
                "min_range_inactivity_timer": 30,
                "min_time": 60,
                "max_time": 120,
            },
            "remove_when_out_of_range": True,
        }, "normal"


def optimize_rp_entity(in_path, out_path):
    with open(in_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    desc = data.get("minecraft:client_entity", {}).get("description", {})
    identifier = desc.get("identifier", "")
    animations = desc.get("animations", {})

    if identifier in SKIP_IDS or not animations:
        return None

    scripts = desc.setdefault("scripts", {})

    pre_anim = scripts.get("pre_animation", [])
    dist_var = DISTANCE_FACTOR
    if dist_var not in pre_anim:
        pre_anim.append(dist_var)
    scripts["pre_animation"] = pre_anim

    scripts["scale"] = LOD_SCALE

    animate = desc.get("animate", [])
    if animate:
        wrapped = []
        for entry in animate:
            if isinstance(entry, dict):
                for key in entry:
                    cond = entry[key]
                    if isinstance(cond, str) and "variable.distance_factor" in cond:
                        wrapped.append(entry)
                    else:
                        inner = cond if isinstance(cond, str) else key
                        wrapped.append(
                            {key: f"variable.distance_factor > 0.5 ? {inner} : 0"}
                        )
            elif isinstance(entry, str):
                wrapped.append(
                    {entry: f"variable.distance_factor > 0.5 ? {entry} : 0"}
                )
        desc["animate"] = wrapped

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))
    return identifier


def create_missing_entity(name, info, out_dir):
    anim_names = ["setup", "walk", "look_at_target", "attack"]
    geoms = [f"geometry.{name}"]
    if name == "evoker":
        geoms = ["geometry.evoker.v1.8"]
    elif name == "vindicator":
        geoms = ["geometry.vindicator.v1.8"]

    entity = {
        "format_version": "1.10.0",
        "minecraft:client_entity": {
            "description": {
                "identifier": info["identifier"],
                "min_engine_version": "1.8.0",
                "materials": info["materials"],
                "textures": info["textures"],
                "geometry": {"default": geoms[0]},
                "animations": {
                    a: f"animation.{name}.{a}" for a in anim_names
                },
                "animation_controllers": [
                    {a: f"controller.animation.{name}.{a}" for a in anim_names}
                ],
                "render_controllers": [f"controller.render.{name}"],
                "spawn_egg": info["spawn_egg"],
                "scripts": {
                    "pre_animation": [DISTANCE_FACTOR],
                    "animate": [
                        {a: "variable.distance_factor > 0.5"} for a in anim_names
                    ],
                    "scale": LOD_SCALE,
                },
            }
        },
    }

    path = os.path.join(out_dir, f"{name}.entity.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entity, f, separators=(",", ":"))
    print(f"Created: {path}")
    return info["identifier"]


def generate_bp_entity(identifier, entity_data, out_dir):
    despawn, kind = get_despawn_params(identifier, entity_data)

    short_name = identifier.split(":")[-1]
    bp_entity = {
        "format_version": "1.19.80",
        "minecraft:entity": {
            "description": {
                "identifier": identifier,
                "is_spawnable": True,
                "is_summonable": True,
                "is_experimental": False,
            },
            "component_groups": {},
            "components": {
                "minecraft:despawn": despawn,
                "minecraft:type_family": {
                    "family": ["mob", short_name]
                },
            },
            "events": {},
        },
    }

    path = os.path.join(out_dir, f"{short_name}.entity.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(bp_entity, f, separators=(",", ":"))
    return kind


def process_rp(rp_dir):
    entity_dir = os.path.join(rp_dir, "entity")
    if not os.path.isdir(entity_dir):
        print(f"Entity dir not found: {entity_dir}")
        return

    files = sorted(f for f in os.listdir(entity_dir) if f.endswith(".json"))
    processed = 0
    skipped_no_anim = 0
    created = 0
    override_dir = os.path.join(os.path.dirname(__file__), "..", "overrides", "RP", "entity")

    for fname in files:
        in_path = os.path.join(entity_dir, fname)
        identifier = optimize_rp_entity(in_path, in_path)
        if identifier:
            processed += 1
        else:
            skipped_no_anim += 1

    for name, info in MISSING_ENTITIES.items():
        out_path = os.path.join(entity_dir, f"{name}.entity.json")
        if not os.path.exists(out_path):
            create_missing_entity(name, info, entity_dir)
            created += 1

    print(f"RP entities: {processed} with animations optimized, {skipped_no_anim} skipped (no animations), {created} missing created")


def process_bp(bp_dir):
    entity_dir = os.path.join(bp_dir, "entities")
    if not os.path.isdir(entity_dir):
        print(f"Entity dir not found: {entity_dir}")
        return

    files = sorted(f for f in os.listdir(entity_dir) if f.endswith(".json"))
    overrides_dir = os.path.join(bp_dir, "entities")

    nuisance = 0
    normal = 0

    for fname in files:
        fpath = os.path.join(entity_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            print(f"  Skipping {fname}: {e}")
            continue

        entity = data.get("minecraft:entity", {})
        identifier = entity.get("description", {}).get("identifier", "")
        if not identifier:
            continue

        kind = generate_bp_entity(identifier, data, overrides_dir)
        if kind == "nuisance":
            nuisance += 1
        else:
            normal += 1

    print(f"BP entities: {normal} normal + {nuisance} nuisance = {normal + nuisance} overrides")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("samples_dir", help="Path to bedrock-samples root")
    parser.add_argument("--rp", action="store_true")
    parser.add_argument("--bp", action="store_true")
    args = parser.parse_args()

    if args.rp:
        process_rp(os.path.join(args.samples_dir, "resource_pack"))

    if args.bp:
        process_bp(os.path.join(args.samples_dir, "behavior_pack"))

    if not args.rp and not args.bp:
        parser.print_help()
