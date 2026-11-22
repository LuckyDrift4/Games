# Tennis stadium (Blender version): putting it in your game

The stadium was modelled in Blender: stands with about 3,800 fans, curved corners, a roof ring with floodlights, the court with a see-through net, the umpire chair and players' benches, hanging video screens, the plaza with its fountain, kiosks, lamps and planters, two outer courts with fences and bleachers, and trees. It's 264k triangles across 44 reusable models.

`out/tennis_game/TennisR6.rbxl` already has the game parts and plain fallback floors, so it plays even before the stadium is imported. These steps add the real stadium.

## Steps (about 2 minutes)

1. Open **TennisR6.rbxl** in Roblox Studio.
2. **File > Import 3D**. Select every file in `roblox/kit/`, both files in `roblox/static/`, and `roblox/AxisProbe.glb`, then click **Import**. Multi-select works, so select them all at once.
3. Open **View > Command Bar**, paste this line and press Enter:

```lua
require(game.ServerStorage.TennisStadiumInstall).Install()
```

The script gathers the models, checks which way they face, sets their collision, builds `workspace.TennisStadium`, sets the lighting and removes the plain floors. If you run it again, it rebuilds the stadium cleanly.

4. Press **Play**.

If you skip step 3 and just press Play, the game builds the stadium itself. Step 3 is better because collision shapes can only be set in Studio.

## What's where (studs)

- **Center Court:** the net is at (0, 0, 0) and the court runs north–south. The stands rise to about y = 42, with screens at the north and south ends.
- **Entrance:** a tunnel on the south side at z = 60–112, then the plaza (z = 114–330) with the play pads at z = 136.
- **Spawn and fountain:** the spawn is at (0, 0, 200) and the fountain at (0, 0, 262).
- **Outer courts:** Court 2 is at (-140, 0, 230) and Court 3 at (140, 0, 230). Their pads are at x = ±88.

The models passed the exporter's checks (no clipping or floating props), but this map hasn't been opened in Roblox Studio yet.
