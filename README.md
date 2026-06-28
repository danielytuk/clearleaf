# Clearleaf

Minecraft Bedrock performance optimization addon. Automatically builds from latest
[Mojang/bedrock-samples](https://github.com/Mojang/bedrock-samples) releases.

## What it does

- **Entity LOD scaling** — entities scale down at distance, invisible past 48 blocks
- **Animation culling** — animations play fully within 24 blocks, partially at 24-48, disabled past 48
- **Part visibility culling** — entities become invisible past 48 blocks (render controller)
- **Particle rate halving** — all particle emitter rates reduced by 50%
- **Rendering optimizations** — point filtering, FP16 precision, 512 shadow map, 4 point lights
- **Fog distance reduction** — tighter fog start/end in all dimensions
- **Block culling** — grass sides hidden against opaque blocks, water/lava bottoms hidden
- **Texture atlas config** — mipmap level 3, padding 8
- **Flipbook slowdown** — water/lava 8 ticks, fire/portal 4 ticks per frame
- **Mob despawn tuning** — normal mobs despawn at 48-64 blocks, nuisance mobs (bat, bee, silverfish, endermite) at 32-48
- **Spawn density reduction** — 8 overworld, 12 nether, 8 end
- **Disabled PBR, color grading, water caustics**
- **Custom block culling** — grass, tallgrass, double plants, water, lava

## CI Pipeline

A GitHub Actions workflow at `.github/workflows/build.yml` runs daily at 6 AM UTC
and on manual trigger. It:

1. Clones the latest `Mojang/bedrock-samples`
2. Runs all optimization Python scripts
3. Applies config files and overrides
4. Packages into a `.mcaddon` file
5. Creates a GitHub Release with the artifact

## Manual Build

```bash
# Clone latest samples
git clone --depth 1 https://github.com/Mojang/bedrock-samples.git _samples

# Build everything
python src/scripts/generate_manifest.py --version $(python3 -c "import json; print(json.load(open('_samples/version.json'))['latest.version'])") --rp --bp --output _samples
python src/scripts/optimize_entities.py --rp _samples
python src/scripts/optimize_render_controllers.py _samples
python src/scripts/optimize_particles.py _samples
python src/scripts/optimize_entities.py --bp _samples

# Apply configs
cp src/configs/*.json _samples/resource_pack/
cp src/configs/fogs/*.json _samples/resource_pack/fogs/
cp src/configs/terrain.material _samples/resource_pack/materials/
cp src/overrides/RP/entity/*.entity.json _samples/resource_pack/entity/
cp src/overrides/BP/spawn_rules/*.json _samples/behavior_pack/spawn_rules/

# Package
cd _samples && zip -r ../clearleaf.mcaddon resource_pack/ behavior_pack/
```

## Project Structure

```
.github/workflows/build.yml   CI pipeline
src/
  configs/                     Static optimization config files
    fogs/                       Dimension fog profiles
    water.json, atmospherics.json, ...
    terrain.material, ...
  overrides/                   Static override files
    BP/spawn_rules/            Spawn density overrides
    RP/entity/                 Missing entity definitions
  scripts/
    generate_manifest.py       Creates manifest.json from version
    optimize_entities.py       LOD scaling, animation culling, BP overrides
    optimize_render_controllers.py  Part visibility distance culling
    optimize_particles.py      Halve all particle emission rates
```

## License

MIT
