-- OPTIONAL upgrade: the place already contains the stadium built from Parts (workspace.TennisStadiumParts). This swaps
-- it for the Blender meshes (out/tennis_stadium_blender), which are smoother but have to be imported first.
--
-- In Studio: File > Import 3D, select every .glb in the stadium's kit/ and static/ folders plus AxisProbe.glb, import.
-- Then in the command bar (View > Command Bar):   require(game.ServerStorage.TennisStadiumInstall).Install()
--
-- It finds the imported models (by name, or by the names of the parts inside when Studio called them "Scene"),
-- undoes any import scale, puts every model's pivot back on its file origin (TennisStadiumOffsets), works out which
-- way the importer turned them (AxisProbe), sets collision shapes, builds workspace.TennisStadium with
-- TennisStadiumSetup, sets the lighting and removes the Parts stadium and the fallback floors. Safe to run again.
local ServerStorage = game:GetService("ServerStorage")
local RunService = game:GetService("RunService")
local AssetService = game:GetService("AssetService")

local M = {}

local function setup()
	return require(ServerStorage:WaitForChild("TennisStadiumSetup"))
end

local function offsets()
	local m = ServerStorage:FindFirstChild("TennisStadiumOffsets")
	return m and require(m) or {}
end

-- "Stand_w20_0_Node" / "Stand_w20_0.001" -> "Stand_w20_0"
local function clean(name)
	name = string.gsub(name, "_Node$", "")
	name = string.gsub(name, "%.%d+$", "")
	return name
end

local function hasMesh(inst)
	if inst:IsA("MeshPart") then
		return true
	end
	return inst:FindFirstChildWhichIsA("MeshPart", true) ~= nil
end

-- which stadium model is this? by its own name, or by the parts inside it
local function identify(inst, want)
	local own = clean(inst.Name)
	if want[own] then
		return own
	end
	local list = inst:GetDescendants()
	table.insert(list, inst)
	for _, d in list do
		if d:IsA("BasePart") then
			local n = clean(d.Name)
			if want[n] then
				return n
			end
			local base = string.match(n, "^(.-)_Glow_")
			if base and want[base] then
				return base
			end
			if string.match(n, "^AxisProbe") then
				return "AxisProbe"
			end
		end
	end
	return nil
end

-- move imported models (Workspace or ServerStorage) into ServerStorage.TennisStadiumKit, named after their prop
function M.Gather()
	local S = setup()
	local kit = ServerStorage:FindFirstChild("TennisStadiumKit")
	if not kit then
		kit = Instance.new("Folder")
		kit.Name = "TennisStadiumKit"
		kit.Parent = ServerStorage
	end
	local want = { AxisProbe = true }
	for _, n in S.Props do
		want[n] = true
	end
	local moved = 0
	for _, where in { workspace, ServerStorage } do
		for _, c in where:GetChildren() do
			if c ~= kit and (c:IsA("Model") or c:IsA("MeshPart")) and hasMesh(c) then
				local prop = identify(c, want)
				if prop then
					for _, d in c:GetDescendants() do
						if d:IsA("BasePart") then
							d.Name = clean(d.Name)
						end
					end
					local old = kit:FindFirstChild(prop)
					if old and old ~= c then
						old:Destroy()
					end
					c.Name = prop
					c.Parent = kit
					moved += 1
				end
			end
		end
	end
	return kit, moved
end

local function mainPart(model, prop)
	if model:IsA("BasePart") then
		return model
	end
	for _, d in model:GetDescendants() do
		if d:IsA("BasePart") and d.Name == prop then
			return d
		end
	end
	return model:FindFirstChildWhichIsA("BasePart", true)
end

-- the importer may turn models half a turn: the AxisProbe's +X cube tells which way
function M.DetectYaw(kit)
	local probe = kit:FindFirstChild("AxisProbe")
	if not probe then
		return nil
	end
	local arrow, cube
	for _, d in probe:GetDescendants() do
		if d:IsA("BasePart") then
			if d.Name == "AxisProbe" then
				arrow = d
			elseif d.Name == "AxisProbe_PlusX" then
				cube = d
			end
		end
	end
	if not (arrow and cube) then
		return nil
	end
	-- in the file the cube sits at -X (glTF faces +Z); if it is still there, the importer kept the file's axes
	return (cube.Position.X - arrow.Position.X) < 0 and 180 or 0
end

-- every kit model: right scale, pivot on its file origin
function M.FixPivots(kit, yaw)
	local OFF = offsets()
	local fixed = 0
	for _, model in kit:GetChildren() do
		local o = OFF[model.Name]
		local part = o and mainPart(model, model.Name)
		if o and part then
			local ratio = part.Size.Magnitude / o.size.Magnitude
			if model:IsA("Model") and math.abs(ratio - 1) > 0.03 then
				model:ScaleTo(model:GetScale() / ratio)
			end
			local c = o.c
			if yaw == 0 then
				c = Vector3.new(-c.X, c.Y, -c.Z) -- the importer already turned the file's axes into Roblox's
			end
			local origin = CFrame.new(part.Position - c)
			if model:IsA("Model") then
				model.WorldPivot = origin
			else
				model.PivotOffset = part.CFrame:ToObjectSpace(origin)
			end
			fixed += 1
		end
	end
	return fixed
end

-- collision shapes per prop (only possible in Studio, not in a running game)
function M.PrepCollision(kit)
	local S = setup()
	local FID = {
		none = Enum.CollisionFidelity.Box,
		box = Enum.CollisionFidelity.Box,
		hull = Enum.CollisionFidelity.Hull,
		precise = Enum.CollisionFidelity.PreciseConvexDecomposition,
	}
	local done = 0
	for _, model in kit:GetChildren() do
		local kind = S.Collision[model.Name] or "hull"
		local list = model:GetDescendants()
		table.insert(list, model)
		for _, p in list do
			if p:IsA("MeshPart") then
				local want = string.find(p.Name, "_Glow_") and Enum.CollisionFidelity.Box or FID[kind]
				if p.CollisionFidelity ~= want and not pcall(function()
					p.CollisionFidelity = want
				end) then
					local ok, fresh = pcall(AssetService.CreateMeshPartAsync, AssetService, p.MeshId, {
						CollisionFidelity = want,
						RenderFidelity = Enum.RenderFidelity.Automatic,
					})
					if ok then
						p:ApplyMesh(fresh)
						done += 1
					end
				end
			end
		end
	end
	return done
end

function M.Install()
	local S = setup()
	local kit, moved = M.Gather()
	if #kit:GetChildren() == 0 then
		warn("[TennisStadium] nothing imported yet: File > Import 3D, pick every .glb of the stadium, then run this again")
		return nil
	end
	local yaw = M.DetectYaw(kit)
	if yaw then
		S.YAW_FIX = yaw
	end
	local pivots = M.FixPivots(kit, S.YAW_FIX)
	local prepped = 0
	if RunService:IsEdit() then
		prepped = M.PrepCollision(kit)
	end
	local root = S.Build(kit, workspace)
	pcall(S.ApplyLook)
	local world = workspace:FindFirstChild("World")
	local fallback = world and world:FindFirstChild("Fallback")
	if fallback then
		fallback:Destroy()
	end
	local partsStadium = workspace:FindFirstChild("TennisStadiumParts") -- the built-in Parts version
	if partsStadium then
		partsStadium:Destroy()
	end
	local missing = {}
	for _, n in S.Props do
		if not kit:FindFirstChild(n) then
			table.insert(missing, n)
		end
	end
	print(string.format("[TennisStadium] built: %d models (%d gathered, %d pivots fixed), yaw fix %d, %d collision shapes set%s",
		#kit:GetChildren(), moved, pivots, S.YAW_FIX, prepped,
		#missing > 0 and (", MISSING: " .. table.concat(missing, ", ")) or ""))
	return root
end

return M
