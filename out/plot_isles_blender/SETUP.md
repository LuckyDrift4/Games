# Plot Isles (Blender version): putting it in Roblox Studio

This version was modelled in Blender (bevelled meshes, rounded beaches, curved palms) instead of plain Parts.
It comes as 3D model files plus a setup script that places everything.

- `roblox/kit/`: 96 props, one `.glb` each (pads, gates, conveyors, palms, huts, lighthouse ...).
- `roblox/static/`: the main island ground, the sea and the seabed.
- `roblox/AxisProbe.glb`: a small arrow used once to check that props face the right way.
- `roblox/PlotIslesSetup.lua`: places all 890 props, sets collision, makes glow parts Neon with lights, and sets the lighting.
- `roblox/PlotIslesKitPrep.lua`: sets the right collision shape on every prop (run once).
- `roblox/report.md`: the checks it passed (404,844 triangles, no clipping or floating props).

## Steps

1. **Import the models.** In Studio, go to **File > Import 3D**. Select every file in `roblox/kit/` and `roblox/static/`,
   plus `AxisProbe.glb`. In the import settings:
   - choose **studs** as the unit
   - set the pivot to the **scene origin**
   - turn on **Anchored**

   Import them into **ServerStorage**, then put them all in one Folder named **`PlotIslesKit`**.
2. **Add the setup script.** In ServerStorage, insert a **ModuleScript** named **`PlotIslesSetup`** and paste in the
   contents of `PlotIslesSetup.lua`.
3. **Set the collision.** Paste `PlotIslesKitPrep.lua` into the command bar (View > Command Bar) and press Enter, once.
4. **Check which way props face.** Drag `AxisProbe` from the kit into Workspace. If its arrow points the same way as
   the model's front (LookVector), leave `M.YAW_FIX = 0` in `PlotIslesSetup`. If it points backwards, set
   `M.YAW_FIX = 180`. Then delete the probe from Workspace.
5. **Build the map.** Paste this into the command bar:

```lua
require(game.ServerStorage.PlotIslesSetup).Build(game.ServerStorage.PlotIslesKit, workspace)
require(game.ServerStorage.PlotIslesSetup).ApplyLook()
```

Running it again replaces the old map; it only ever deletes the map it built.

6. **Spawn point and see-through water.** Paste this into the command bar:

```lua
local map = workspace:WaitForChild("PlotIsles")
for _, p in map:GetDescendants() do
	if p:IsA("BasePart") and string.match(p.Name, "^Sea_Water") then
		p.Transparency = 0.35
		p.CanCollide = false
	end
end
local spawn = Instance.new("SpawnLocation")
spawn.Name = "Spawn"
spawn.Size = Vector3.new(8, 0.4, 8)
spawn.Position = Vector3.new(-272, 3.3, 0)
spawn.Anchored = true
spawn.Transparency = 1
spawn.Neutral = true
spawn.Duration = 0
spawn.Parent = map
```

For the PointLights on lamps and torches, set **Lighting > Technology** to **Future**.

## Where things are (studs)

- Spawn pad: (-272, 3, 0). The hub's lighthouse, coin fountain and Shop / Index / Rebirth huts surround it.
- Main road: runs east along z = 0 from x = -219 to x = 228.
- Plots 1 to 4 (north) and 5 to 8 (south): centred at x = -165, -55, 55 and 165, with z = -95 (north) and +95 (south).
  Each one is reached by a plank bridge from the road.

The models were checked by re-importing every `.glb` in Blender, but this map has not been opened in Roblox Studio yet.
