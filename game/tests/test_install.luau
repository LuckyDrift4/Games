-- TennisStadiumInstall against a simulated Studio import: every model named "Scene", parts named "<prop>_Node",
-- the file's axes kept (yaw 180) or turned (yaw 0), dropped somewhere else in the world. After Gather / DetectYaw /
-- FixPivots, placing a model like TennisStadiumSetup.Build does must put its main mesh where the design wants it.
local fs = require("@lune/fs")
local luau = require("@lune/luau")
local roblox = require("@lune/roblox")
local Vector3, CFrame = roblox.Vector3, roblox.CFrame
local H = require("./harness")
local check = H.check

-- a tiny fake instance tree (names, parents, a few Roblox methods)
local Inst = {}
Inst.__index = function(self, k)
	if Inst[k] then return Inst[k] end
	if k == "Position" then return rawget(self, "CFrame").Position end
	return nil
end
function Inst.new(class, name, parent)
	local o = setmetatable({ ClassName = class, Name = name or class, _kids = {} }, Inst)
	if parent then o:SetParent(parent) end
	return o
end
function Inst:SetParent(p)
	local old = rawget(self, "_parent")
	if old then
		for i, c in ipairs(old._kids) do if c == self then table.remove(old._kids, i) break end end
	end
	rawset(self, "_parent", p)
	if p then table.insert(p._kids, self) end
end
Inst.__newindex = function(self, k, v)
	if k == "Parent" then self:SetParent(v) else rawset(self, k, v) end
end
function Inst:IsA(c)
	if c == "BasePart" then return self.ClassName == "MeshPart" or self.ClassName == "Part" end
	return self.ClassName == c
end
function Inst:GetChildren() return table.clone(self._kids) end
function Inst:GetDescendants()
	local out = {}
	local function walk(o) for _, c in ipairs(o._kids) do table.insert(out, c); walk(c) end end
	walk(self)
	return out
end
function Inst:FindFirstChild(n) for _, c in ipairs(self._kids) do if c.Name == n then return c end end return nil end
function Inst:FindFirstChildWhichIsA(c, rec)
	for _, d in ipairs(rec and self:GetDescendants() or self._kids) do if d:IsA(c) then return d end end
	return nil
end
function Inst:Destroy() self:SetParent(nil) end
function Inst:WaitForChild(n) return self:FindFirstChild(n) end

local OFF = H.load("../src/ServerStorage/", "TennisStadiumOffsets")
local PROPS = { "Stand_w20_0", "LampPost", "Ground_Main_0", "TreeCanopy_1", "StandCorner_0" }

local function run(keepAxes, drop)
	local ws = Inst.new("Workspace", "Workspace")
	local ss = Inst.new("ServerStorage", "ServerStorage")
	local setup = { Props = PROPS, YAW_FIX = 0, Collision = {} }
	Inst.new("ModuleScript", "TennisStadiumSetup", ss)
	Inst.new("ModuleScript", "TennisStadiumOffsets", ss)
	-- simulate the import: a "Scene" model per file, parts at the mesh centres
	for _, name in ipairs({ "AxisProbe", "AxisProbe_PlusX" }) do end
	local function import(prop, partNames)
		local m = Inst.new("Model", "Scene", ws)
		for _, pn in ipairs(partNames) do
			local key = pn
			local o = OFF[key] or OFF[prop]
			local c = o.c
			if key == "AxisProbe_PlusX" then c = Vector3.new(-4, 0, 0) end
			if not keepAxes then c = Vector3.new(-c.X, c.Y, -c.Z) end
			local p = Inst.new("MeshPart", pn .. "_Node", m)
			p.CFrame = CFrame.new(c + drop)
			p.Size = o.size
		end
		return m
	end
	import("AxisProbe", { "AxisProbe", "AxisProbe_PlusX" })
	for _, prop in ipairs(PROPS) do
		import(prop, prop == "LampPost" and { "LampPost", "LampPost_Glow_lamp" } or { prop })
	end
	-- an unrelated model with no meshes must be left alone
	local other = Inst.new("Model", "TennisStadiumParts", ws)
	Inst.new("Part", "Stand_w20_0", other)
	local env = {
		game = { GetService = function(_, n)
			if n == "ServerStorage" then return ss end
			return { IsEdit = function() return false end }
		end },
		workspace = ws,
		require = function(m)
			if m.Name == "TennisStadiumSetup" then return setup end
			if m.Name == "TennisStadiumOffsets" then return OFF end
			return nil
		end,
		Instance = { new = function(c) return Inst.new(c) end },
		Vector3 = Vector3, CFrame = CFrame, Enum = roblox.Enum,
	}
	local src = fs.readFile("../src/ServerStorage/TennisStadiumInstall.lua")
	local M = luau.load(src, { debugName = "Install", environment = env, injectGlobals = true })()
	local kit, moved = M.Gather()
	check(moved == #PROPS + 1, "gathered " .. moved)
	check(rawget(other, "_parent") == ws, "left the Parts stadium alone")
	for _, prop in ipairs(PROPS) do
		check(kit:FindFirstChild(prop) ~= nil, "found " .. prop)
	end
	check(kit:FindFirstChild("LampPost"):FindFirstChild("LampPost_Glow_lamp") ~= nil, "glow part renamed")
	local yaw = M.DetectYaw(kit)
	check(yaw == (keepAxes and 180 or 0), "yaw " .. tostring(yaw))
	M.FixPivots(kit, yaw)
	-- place like Setup.Build: clone pivot -> row CFrame * yaw fix; the main mesh must land at row * design centre
	local row = CFrame.new(33, 0, -50) * CFrame.Angles(0, math.rad(90), 0)
	for _, prop in ipairs(PROPS) do
		local m = kit:FindFirstChild(prop)
		local part = m:FindFirstChild(prop)
		local placed = row * CFrame.Angles(0, math.rad(yaw), 0) * m.WorldPivot:Inverse() * part.CFrame
		local c = OFF[prop].c
		local want = row * Vector3.new(-c.X, c.Y, -c.Z)
		check((placed.Position - want).Magnitude < 1e-3, prop .. " lands at " .. tostring(placed.Position) .. " want " .. tostring(want))
	end
end

run(true, Vector3.new(0, 0, 0))
run(true, Vector3.new(120, 4, -35))
run(false, Vector3.new(-60, 0, 10))
H.done()
