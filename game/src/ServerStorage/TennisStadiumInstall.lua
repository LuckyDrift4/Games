-- Puts the Blender-made stadium (out/tennis_stadium_blender) into the place.
--
-- In Studio: File > Import 3D, select every .glb in the stadium's kit/ and static/ folders plus AxisProbe.glb, import.
-- Then in the command bar (View > Command Bar):   require(game.ServerStorage.TennisStadiumInstall).Install()
--
-- It gathers the imported models into ServerStorage.TennisStadiumKit, works out which way the importer turned them
-- (AxisProbe), sets each mesh's collision shape, builds workspace.TennisStadium with TennisStadiumSetup, sets the
-- lighting and removes the plain fallback floors. Running it again rebuilds cleanly. If you only import and press
-- Play, the server runs it too (collision shapes can only be changed in Studio, so the command bar is better).
local ServerStorage = game:GetService("ServerStorage")
local RunService = game:GetService("RunService")
local AssetService = game:GetService("AssetService")

local M = {}

local function setup()
	return require(ServerStorage:WaitForChild("TennisStadiumSetup"))
end

-- move imported models (Workspace or ServerStorage) into ServerStorage.TennisStadiumKit
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
			if c ~= kit and want[c.Name] and (c:IsA("Model") or c:IsA("BasePart")) then
				local old = kit:FindFirstChild(c.Name)
				if old and old ~= c then
					old:Destroy()
				end
				c.Parent = kit
				moved += 1
			end
		end
	end
	return kit, moved
end

-- the importer may turn models half a turn; the AxisProbe's red cube sits on +X when it did not
function M.DetectYaw(kit)
	local probe = kit:FindFirstChild("AxisProbe")
	local cube = probe and probe:FindFirstChild("AxisProbe_PlusX", true)
	if not (probe and cube and cube:IsA("BasePart")) then
		return nil
	end
	local rel = probe:GetPivot():PointToObjectSpace(cube.Position)
	return rel.X >= 0 and 0 or 180
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
		for _, p in model:GetDescendants() do
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
	print(string.format("[TennisStadium] built: %d kit models (%d moved), yaw fix %d, %d collision shapes set",
		#kit:GetChildren(), moved, S.YAW_FIX, prepped))
	return root
end

return M
