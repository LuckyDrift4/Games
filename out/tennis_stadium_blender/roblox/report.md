# TennisStadium - Roblox export report

| Check | Value | Limit / target |
|---|---|---|
| Kit props | 44 | reuse: fewer unique meshes = less memory |
| Placed props | 283 (333 MeshParts) | under ~5k parts per area for phones |
| Static chunks | 2 | each <= 20000 tris, <= 2048 studs |
| Oversize faces -> Parts | 0 | sea / skirt planes |
| Total placed tris | 264,122 | hard budget 450,000 (--budget) |
| Largest prop | StandCorner_1 (8406 tris) | <= 20000 per MeshPart |
| Footprint | x -200..200, z -173..352 | keep under 2,048 from origin for float precision comfort |
| Palette | TennisStadium_Palette.png | <= 1024 px |
| Placement checks | clip 0, float 0, water 0, falls 0, collision 0, buffer 0 | all 0 (clip, float, water, falls, collision, buffer) |

## Collision per prop

| Prop | Collision | Tris |
|---|---|---|
| Bench | box | 396 |
| Bin | box | 112 |
| Bleacher_0 | precise | 1404 |
| Bleacher_1 | precise | 1734 |
| ConeTree_0 | hull | 148 |
| ConeTree_1 | hull | 148 |
| CourtSurface | box | 346 |
| EntranceGate | precise | 304 |
| FlowerBed_0 | hull | 492 |
| FlowerBed_1 | hull | 492 |
| Fountain | hull | 1992 |
| HangingScreen_40 | box | 132 |
| Hedge_20 | box | 172 |
| Kiosk_drinks | box | 144 |
| Kiosk_food | box | 144 |
| Kiosk_tickets | box | 144 |
| LampPost | box | 160 |
| Net | box | 1262 |
| PadRing_padB | none | 416 |
| PadRing_padO | none | 416 |
| PadRing_padY | none | 416 |
| PlanterTree_0 | hull | 292 |
| PlanterTree_1 | hull | 292 |
| PlayerBench | box | 730 |
| SmallScreen | box | 96 |
| SpawnPlate | none | 768 |
| StandCorner_0 | precise | 8286 |
| StandCorner_1 | precise | 8406 |
| StandPortal | precise | 4120 |
| Stand_w20_0 | precise | 7224 |
| Stand_w20_1 | precise | 7194 |
| Stand_w20_2 | precise | 7234 |
| Stand_w22_3 | precise | 7554 |
| Stand_w22_4 | precise | 7294 |
| Stand_w25_5 | precise | 8006 |
| TreeCanopy_0 | none | 160 |
| TreeCanopy_1 | none | 160 |
| TreeCanopy_2 | none | 160 |
| TreeTrunk_0 | hull | 162 |
| TreeTrunk_1 | hull | 162 |
| TreeTrunk_2 | hull | 162 |
| UmpireChair | box | 1052 |
| Windscreen_20 | box | 88 |
| Windscreen_22 | box | 88 |

## Where the triangles go (cut here first)

| Prop | Copies | Tris each | Placed tris | Share |
|---|---|---|---|---|
| StandCorner_1 | 4 | 8406 | 33,624 | 13% |
| StandCorner_0 | 4 | 8286 | 33,144 | 13% |
| Stand_w20_2 | 4 | 7234 | 28,936 | 11% |
| Stand_w20_0 | 4 | 7224 | 28,896 | 11% |
| Stand_w20_1 | 4 | 7194 | 28,776 | 11% |
| Stand_w25_5 | 2 | 8006 | 16,012 | 6% |
| Stand_w22_3 | 2 | 7554 | 15,108 | 6% |
| Stand_w22_4 | 1 | 7294 | 7,294 | 3% |
| Hedge_20 | 28 | 172 | 4,816 | 2% |
| PlayerBench | 6 | 730 | 4,380 | 2% |
| StandPortal | 1 | 4120 | 4,120 | 2% |
| Net | 3 | 1262 | 3,786 | 1% |

## Budget (ok)

- within budget: total <= 450000, prop <= 12000 (hero <= 30000), static <= 150000

## Warnings (14)

- note Bleacher_0: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Bleacher_1: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note StandCorner_0: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note StandCorner_1: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note StandPortal: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Stand_w20_0: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Stand_w20_1: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Stand_w20_2: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Stand_w22_3: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Stand_w22_4: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Stand_w25_5: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- TreeCanopy_0: lowest point y=5.53 above its origin (floats when placed)
- TreeCanopy_1: lowest point y=7.58 above its origin (floats when placed)
- TreeCanopy_2: lowest point y=8.98 above its origin (floats when placed)

## Next steps

1. Studio: File > Import 3D > select every file in kit/ and static/ plus AxisProbe (Scale unit: studs; set pivot to scene origin; anchored; insert into ServerStorage, folder `TennisStadiumKit`).
2. Insert `TennisStadiumSetup.lua` as ModuleScript ServerStorage.TennisStadiumSetup, run `TennisStadiumKitPrep.lua` once in the command bar.
3. Orientation check with AxisProbe (references/roblox_pipeline.md); set `M.YAW_FIX`.
4. Command bar: `require(game.ServerStorage.TennisStadiumSetup).Build(game.ServerStorage.TennisStadiumKit, workspace)`, then `.ApplyLook()`.