# Tennis racket (realistic, Blender)

A realistic tennis racket modelled from real proportions: 68.6 cm long, a 100 sq in head, a 23 mm beam and a 4 3/8 grip.
It has a 16 x 19 string pattern woven over and under, grommets where every string enters the frame, a bumper guard,
a throat bridge, a wound overgrip with finishing tape, a butt cap and a string dampener. The paint is gloss black with
an electric-blue throat and sides and a silver pinstripe.

Made by [`models/tennis_racket/racket.py`](../../models/tennis_racket/racket.py) (runs in Blender or with its `bpy` module).

| File | What it is |
|---|---|
| `TennisRacket.glb` | the model: 13 parts, 3 studs long, about 48k triangles (every part under the 20k MeshPart limit) |
| `MakeRacketTool.lua` | command-bar script that turns the imported model into a Tool in StarterPack |
| `previews/` | studio renders |

## Put it in Roblox

1. In Studio, go to **File > Import 3D** and pick `TennisRacket.glb`. Use **studs** as the unit, then insert it into
   **Workspace**. It arrives as a Model named `TennisRacket` with 13 MeshParts.
2. Paste `MakeRacketTool.lua` into the command bar and press Enter. The script:
   - sets each part's colour and material (Fabric grip, Metal pinstripe ...)
   - makes the grip the Handle and welds the other parts to it
   - turns off collision and moves the Tool into StarterPack
3. Press Play. The racket is in your backpack.

If the racket sits wrong in the hand, change `GRIP` at the top of the script.
To make it bigger or smaller, call `Model:ScaleTo()` on the model before step 2.

Not tested in Roblox Studio yet. The model was checked by re-importing the GLB in Blender.
