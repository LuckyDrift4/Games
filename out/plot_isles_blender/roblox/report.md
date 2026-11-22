# PlotIsles - Roblox export report

| Check | Value | Limit / target |
|---|---|---|
| Kit props | 96 | reuse: fewer unique meshes = less memory |
| Placed props | 890 (1285 MeshParts) | under ~5k parts per area for phones |
| Static chunks | 4 | each <= 20000 tris, <= 2048 studs |
| Oversize faces -> Parts | 0 | sea / skirt planes |
| Total placed tris | 404,844 | hard budget 450,000 (--budget) |
| Largest prop | PlotGround (4384 tris) | <= 20000 per MeshPart |
| Footprint | x -420..343, z -269..265 | keep under 2,048 from origin for float precision comfort |
| Palette | PlotIsles_Palette.png | <= 1024 px |
| Placement checks | clip 0, float 0, water 0, falls 0, collision 0, buffer 0 | all 0 (clip, float, water, falls, collision, buffer) |

## Collision per prop

| Prop | Collision | Tris |
|---|---|---|
| Barrel | box | 156 |
| BeachBits_0 | none | 138 |
| BeachBits_1 | none | 138 |
| BeachUmbrella_0 | none | 170 |
| BeachUmbrella_1 | none | 170 |
| BeachUmbrella_2 | none | 170 |
| BeachUmbrella_3 | none | 170 |
| BeachUmbrella_4 | none | 170 |
| BeachUmbrella_5 | none | 170 |
| BeachUmbrella_6 | none | 170 |
| BeachUmbrella_7 | none | 170 |
| Bench | box | 308 |
| Bin | box | 112 |
| Boat_0 | hull | 256 |
| Boat_2 | hull | 256 |
| Boat_4 | hull | 256 |
| Boat_6 | hull | 256 |
| Buoy | hull | 88 |
| Bush_0 | none | 250 |
| Bush_1 | none | 250 |
| Bush_2 | none | 226 |
| CoinFountain | precise | 1184 |
| CollectButton | box | 240 |
| Conveyor_0 | precise | 3680 |
| Conveyor_1 | precise | 3680 |
| Conveyor_2 | precise | 3680 |
| Conveyor_3 | precise | 3680 |
| Conveyor_4 | precise | 3680 |
| Conveyor_5 | precise | 3680 |
| Conveyor_6 | precise | 3680 |
| Conveyor_7 | precise | 3680 |
| Crate | box | 116 |
| CrateSmall | box | 116 |
| Flowers_0 | none | 560 |
| Flowers_1 | none | 560 |
| Flowers_2 | none | 560 |
| Gate_0 | precise | 944 |
| Gate_1 | precise | 944 |
| Gate_2 | precise | 944 |
| Gate_3 | precise | 944 |
| Gate_4 | precise | 944 |
| Gate_5 | precise | 944 |
| Gate_6 | precise | 944 |
| Gate_7 | precise | 944 |
| GrassTuft_0 | none | 70 |
| GrassTuft_1 | none | 70 |
| GrassTuft_2 | none | 70 |
| IndexHut | precise | 1012 |
| Islet_0 | precise | 596 |
| Islet_1 | precise | 548 |
| Islet_2 | precise | 932 |
| Islet_3 | precise | 560 |
| LampPost | box | 222 |
| LifebuoyStand | box | 344 |
| Lighthouse | precise | 1628 |
| LockButton | box | 240 |
| OwnerBoard_0 | box | 320 |
| OwnerBoard_1 | box | 320 |
| OwnerBoard_2 | box | 320 |
| OwnerBoard_3 | box | 320 |
| OwnerBoard_4 | box | 320 |
| OwnerBoard_5 | box | 320 |
| OwnerBoard_6 | box | 320 |
| OwnerBoard_7 | box | 320 |
| Pad_0 | box | 668 |
| Pad_1 | box | 668 |
| Pad_2 | box | 668 |
| Pad_3 | box | 668 |
| Pad_4 | box | 668 |
| Pad_5 | box | 668 |
| Pad_6 | box | 668 |
| Pad_7 | box | 668 |
| PalmCanopy_0 | none | 572 |
| PalmCanopy_1 | none | 576 |
| PalmCanopy_2 | none | 568 |
| PalmCanopy_3 | none | 576 |
| PalmTrunk_0 | hull | 328 |
| PalmTrunk_1 | hull | 328 |
| PalmTrunk_2 | hull | 328 |
| PalmTrunk_3 | hull | 328 |
| Pier | precise | 1112 |
| PlankBridge | precise | 1532 |
| Planter_0 | box | 612 |
| Planter_1 | box | 612 |
| Planter_2 | box | 612 |
| PlotGround | precise | 4384 |
| PlotPaths | precise | 2368 |
| RebirthHut | precise | 1178 |
| Rock_0 | hull | 80 |
| Rock_1 | hull | 84 |
| Rock_2 | hull | 76 |
| ShopHut | precise | 1068 |
| SpawnPad | box | 272 |
| Surfboards | box | 208 |
| TikiTorch | box | 176 |
| WelcomeArch | precise | 952 |

## Where the triangles go (cut here first)

| Prop | Copies | Tris each | Placed tris | Share |
|---|---|---|---|---|
| PlotGround | 8 | 4384 | 35,072 | 9% |
| PalmCanopy_0 | 36 | 572 | 20,592 | 5% |
| PalmCanopy_1 | 35 | 576 | 20,160 | 5% |
| PlotPaths | 8 | 2368 | 18,944 | 5% |
| CollectButton | 64 | 240 | 15,360 | 4% |
| PalmCanopy_3 | 25 | 576 | 14,400 | 4% |
| PalmCanopy_2 | 24 | 568 | 13,632 | 3% |
| PlankBridge | 8 | 1532 | 12,256 | 3% |
| PalmTrunk_0 | 36 | 328 | 11,808 | 3% |
| PalmTrunk_1 | 35 | 328 | 11,480 | 3% |
| TikiTorch | 64 | 176 | 11,264 | 3% |
| Flowers_0 | 18 | 560 | 10,080 | 2% |

## Budget (ok)

- within budget: total <= 450000, prop <= 12000 (hero <= 30000), static <= 150000

## Warnings (10)

- PalmCanopy_0: lowest point y=10.84 above its origin (floats when placed)
- note PalmCanopy_0: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- PalmCanopy_1: lowest point y=13.07 above its origin (floats when placed)
- note PalmCanopy_1: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- PalmCanopy_2: lowest point y=14.80 above its origin (floats when placed)
- PalmCanopy_3: lowest point y=9.42 above its origin (floats when placed)
- note PalmCanopy_3: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note Pier: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- note PlankBridge: pivot is off the footprint centre (fine if intended, e.g. a gate pivot on its wall line)
- PlotPaths: lowest point y=0.90 above its origin (floats when placed)

## Next steps

1. Studio: File > Import 3D > select every file in kit/ and static/ plus AxisProbe (Scale unit: studs; set pivot to scene origin; anchored; insert into ServerStorage, folder `PlotIslesKit`).
2. Insert `PlotIslesSetup.lua` as ModuleScript ServerStorage.PlotIslesSetup, run `PlotIslesKitPrep.lua` once in the command bar.
3. Orientation check with AxisProbe (references/roblox_pipeline.md); set `M.YAW_FIX`.
4. Command bar: `require(game.ServerStorage.PlotIslesSetup).Build(game.ServerStorage.PlotIslesKit, workspace)`, then `.ApplyLook()`.