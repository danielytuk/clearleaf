"""Halve emission rates on all particle JSON files."""

import json
import os
import re

RATE_FIELDS = {
    "minecraft:emitter_rate_steady": ["spawn_rate", "max_particles"],
    "minecraft:emitter_rate_instant": ["num_particles"],
    "minecraft:emitter_rate_manual": ["max_particles"],
}


def has_expr_value(components, field):
    val = components.get(field)
    if isinstance(val, dict):
        return True
    if isinstance(val, str) and ("expression" in val or "Math.random" in val or "math.random" in val):
        return True
    return False


def halve_particle(in_path):
    with open(in_path, "r", encoding="utf-8") as f:
        raw = f.read()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None

    particle = data.get("particle_effect", {})
    components = particle.get("components", {})

    changed_fields = []

    for rate_type, fields in RATE_FIELDS.items():
        rate_block = components.get(rate_type, {})
        if not rate_block:
            continue

        for field in fields:
            if field not in rate_block:
                continue

            if has_expr_value(rate_block, field):
                continue

            val = rate_block[field]
            if not isinstance(val, (int, float)):
                continue

            new_val = max(1, int(val // 2))
            if new_val != val:
                rate_block[field] = new_val
                changed_fields.append(f"{field}:{val}->{new_val}")

    if not changed_fields:
        return None

    with open(in_path, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))
    return changed_fields


MANUAL_CAPS = {
    "biome_tinted_leaves_particle": {"minecraft:emitter_rate_manual": {"max_particles": 500}},
    "pale_oak_leaves_particle": {"minecraft:emitter_rate_manual": {"max_particles": 500}},
    "cherry_leaves_particle": {"minecraft:emitter_rate_manual": {"max_particles": 500}},
    "snowflake": {"minecraft:emitter_rate_manual": {"max_particles": 25}},
}


def apply_manual_caps(in_path, fname):
    if fname not in MANUAL_CAPS:
        return None

    with open(in_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    caps = MANUAL_CAPS[fname]
    components = data.get("particle_effect", {}).get("components", {})
    changed = []

    for rate_type, fields in caps.items():
        rate_block = components.get(rate_type, {})
        if not rate_block:
            continue
        for field, target in fields.items():
            current = rate_block.get(field)
            if current is not None and current != target:
                rate_block[field] = target
                changed.append(f"{field}:{current}->{target}")

    if not changed:
        return None

    with open(in_path, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))
    return changed


def process_rp(rp_dir):
    particle_dir = os.path.join(rp_dir, "particles")
    if not os.path.isdir(particle_dir):
        print(f"Particles dir not found: {particle_dir}")
        return

    files = sorted(f for f in os.listdir(particle_dir) if f.endswith(".json"))

    modified = 0
    skipped_expr = 0
    capped = 0

    for fname in files:
        in_path = os.path.join(particle_dir, fname)

        result = apply_manual_caps(in_path, fname.replace(".json", ""))
        if result:
            capped += 1

        result = halve_particle(in_path)
        if result is None:
            with open(in_path, "r", encoding="utf-8") as f:
                raw = f.read()
            if any(
                re.search(r'"' + field + r'"\s*:', raw)
                for fields in RATE_FIELDS.values()
                for field in fields
            ):
                skipped_expr += 1
            continue

        modified += 1

    print(
        f"Particles: {modified} modified (rates halved), "
        f"{skipped_expr} skipped (expression-based), "
        f"{capped} manually capped"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("samples_dir", help="Path to bedrock-samples root")
    args = parser.parse_args()

    process_rp(os.path.join(args.samples_dir, "resource_pack"))
