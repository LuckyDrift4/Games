-- Builds the R6 noob bot and the racket from plain Parts (no assets to load), and attaches the racket to a
-- character's right hand with the "RacketGrip" Motor6D that the animations drive.
local Config = require(script.Parent.Config)
local AnimData = require(script.Parent.AnimData)

local Rigs = {}

local HAND = CFrame.new(0, -1.15, 0)

local function part(name, size, cf, color, parent, material)
	local p = Instance.new("Part")
	p.Name = name
	p.Size = size
	p.CFrame = cf
	p.Color = color
	p.Material = material or Enum.Material.SmoothPlastic
	p.TopSurface, p.BottomSurface = Enum.SurfaceType.Smooth, Enum.SurfaceType.Smooth
	p.Parent = parent
	return p
end

-- racket in its own frame: origin = the hand, +Y = toward the head, +Z = string face normal. 3 studs long.
function Rigs.buildRacket(accent, neon)
	local model = Instance.new("Model")
	model.Name = "Racket"
	local root = part("Racket", Vector3.new(0.2, 0.2, 0.2), CFrame.new(), Color3.new(1, 1, 1), model)
	root.Transparency = 1
	model.PrimaryPart = root
	local black = Color3.fromRGB(18, 18, 22)
	local white = Color3.fromRGB(236, 238, 241)
	local pieces = {}
	local function add(name, size, cf, color, material)
		local p = part(name, size, cf, color, model, material)
		table.insert(pieces, p)
		return p
	end
	add("Grip", Vector3.new(0.34, 0.86, 0.36), CFrame.new(0, 0.13, 0), white, Enum.Material.Fabric)
	add("ButtCap", Vector3.new(0.4, 0.1, 0.42), CFrame.new(0, -0.32, 0), black)
	add("Tape", Vector3.new(0.38, 0.08, 0.4), CFrame.new(0, 0.58, 0), black)
	local frameMat = neon and Enum.Material.Neon or Enum.Material.SmoothPlastic
	-- throat: two arms from the handle to the head, and the bridge
	for _, s in ipairs({ -1, 1 }) do
		local a, b = Vector3.new(s * 0.07, 0.6, 0), Vector3.new(s * 0.46, 1.28, 0)
		local mid, len = (a + b) / 2, (b - a).Magnitude
		add("Throat", Vector3.new(0.09, len, 0.14), CFrame.lookAt(mid, mid + Vector3.zAxis, (b - a).Unit), accent, frameMat)
	end
	add("Bridge", Vector3.new(0.9, 0.08, 0.13), CFrame.new(0, 1.26, 0), black)
	-- head: an egg-shaped hoop of 22 segments, accent on the sides
	local cy, ha, hb = 1.98, 0.74, 0.55
	local N = 22
	local function hoop(t)
		local x = hb * math.sin(t)
		local y = ha * math.cos(t)
		x *= 1 + 0.07 * y / ha
		return Vector3.new(x, cy + y, 0)
	end
	for i = 0, N - 1 do
		local a, b = hoop(i / N * math.pi * 2), hoop((i + 1) / N * math.pi * 2)
		local mid, len = (a + b) / 2, (b - a).Magnitude
		local side = math.abs(math.sin((i + 0.5) / N * math.pi * 2)) > 0.55
		add("Frame", Vector3.new(0.08, len + 0.03, 0.15), CFrame.lookAt(mid, mid + Vector3.zAxis, (b - a).Unit),
			side and accent or black, side and frameMat or Enum.Material.SmoothPlastic)
	end
	-- strings: 8 mains and 10 crosses
	local strColor = Color3.fromRGB(232, 228, 210)
	for i = 1, 8 do
		local x = (i - 4.5) * 0.11
		local half = ha * math.sqrt(math.max(0, 1 - (x / (hb - 0.03)) ^ 2)) - 0.02
		add("String", Vector3.new(0.025, half * 2, 0.025), CFrame.new(x, cy, 0), strColor)
	end
	for i = 1, 10 do
		local y = (i - 5.5) * 0.13
		local half = hb * math.sqrt(math.max(0, 1 - (y / (ha - 0.03)) ^ 2)) - 0.02
		add("String", Vector3.new(half * 2, 0.025, 0.025), CFrame.new(0, cy + y, 0), strColor)
	end
	add("Dampener", Vector3.new(0.12, 0.08, 0.06), CFrame.new(0, 1.38, 0), Color3.fromRGB(255, 130, 30))
	for _, p in ipairs(pieces) do
		p.CanCollide, p.CanQuery, p.CanTouch, p.Massless = false, false, false, true
		p.CastShadow = p.Name ~= "String"
		local w = Instance.new("WeldConstraint")
		w.Part0, w.Part1 = root, p
		w.Parent = p
	end
	root.CanCollide, root.CanQuery, root.CanTouch, root.Massless = false, false, false, true
	return model
end

function Rigs.attachRacket(character, accent, neon)
	Rigs.removeRacket(character)
	local arm = character:FindFirstChild("Right Arm")
	if not arm then
		return nil
	end
	local model = Rigs.buildRacket(accent, neon)
	model:PivotTo(arm.CFrame * HAND)
	model.Parent = character
	local m = Instance.new("Motor6D")
	m.Name = "RacketGrip"
	m.Part0, m.Part1 = arm, model.PrimaryPart
	m.C0, m.C1 = HAND, CFrame.new()
	m.Parent = arm
	return model
end

function Rigs.removeRacket(character)
	local r = character:FindFirstChild("Racket")
	if r then
		r:Destroy()
	end
	local arm = character:FindFirstChild("Right Arm")
	local m = arm and arm:FindFirstChild("RacketGrip")
	if m then
		m:Destroy()
	end
end

-- classic R6 noob, built from parts with the standard R6 joints
local NOOB = {
	Head = Color3.fromRGB(245, 205, 48),
	Torso = Color3.fromRGB(13, 105, 172),
	["Left Arm"] = Color3.fromRGB(245, 205, 48),
	["Right Arm"] = Color3.fromRGB(245, 205, 48),
	["Left Leg"] = Color3.fromRGB(164, 189, 71),
	["Right Leg"] = Color3.fromRGB(164, 189, 71),
}
local SIZES = {
	HumanoidRootPart = Vector3.new(2, 2, 1),
	Torso = Vector3.new(2, 2, 1),
	Head = Vector3.new(2, 1, 1),
	["Left Arm"] = Vector3.new(1, 2, 1),
	["Right Arm"] = Vector3.new(1, 2, 1),
	["Left Leg"] = Vector3.new(1, 2, 1),
	["Right Leg"] = Vector3.new(1, 2, 1),
}
-- joint C0 / C1 of the standard R6 rig (same numbers the animations were made with)
local R6J = {
	{ "RootJoint", "HumanoidRootPart", "Torso", CFrame.new(0, 0, 0, -1, 0, 0, 0, 0, 1, 0, 1, 0), CFrame.new(0, 0, 0, -1, 0, 0, 0, 0, 1, 0, 1, 0) },
	{ "Neck", "Torso", "Head", CFrame.new(0, 1, 0, -1, 0, 0, 0, 0, 1, 0, 1, 0), CFrame.new(0, -0.5, 0, -1, 0, 0, 0, 0, 1, 0, 1, 0) },
	{ "Right Shoulder", "Torso", "Right Arm", CFrame.new(1, 0.5, 0, 0, 0, 1, 0, 1, 0, -1, 0, 0), CFrame.new(-0.5, 0.5, 0, 0, 0, 1, 0, 1, 0, -1, 0, 0) },
	{ "Left Shoulder", "Torso", "Left Arm", CFrame.new(-1, 0.5, 0, 0, 0, -1, 0, 1, 0, 1, 0, 0), CFrame.new(0.5, 0.5, 0, 0, 0, -1, 0, 1, 0, 1, 0, 0) },
	{ "Right Hip", "Torso", "Right Leg", CFrame.new(1, -1, 0, 0, 0, 1, 0, 1, 0, -1, 0, 0), CFrame.new(0.5, 1, 0, 0, 0, 1, 0, 1, 0, -1, 0, 0) },
	{ "Left Hip", "Torso", "Left Leg", CFrame.new(-1, -1, 0, 0, 0, -1, 0, 1, 0, 1, 0, 0), CFrame.new(-0.5, 1, 0, 0, 0, -1, 0, 1, 0, 1, 0, 0) },
}
Rigs.R6Joints = R6J

function Rigs.buildNoob(name, at)
	local model = Instance.new("Model")
	model.Name = name or "Noob"
	local parts = {}
	for pname, size in pairs(SIZES) do
		local p = part(pname, size, CFrame.new(), NOOB[pname] or Color3.new(1, 1, 1), model, Enum.Material.Plastic)
		p.CanCollide = pname == "HumanoidRootPart" or pname == "Torso" or pname == "Head"
		parts[pname] = p
	end
	parts.HumanoidRootPart.Transparency = 1
	local mesh = Instance.new("SpecialMesh")
	mesh.MeshType = Enum.MeshType.Head
	mesh.Scale = Vector3.new(1.25, 1.25, 1.25)
	mesh.Parent = parts.Head
	local face = Instance.new("Decal")
	face.Name = "face"
	face.Texture = "rbxasset://textures/face.png"
	face.Face = Enum.NormalId.Front
	face.Parent = parts.Head
	for _, j in ipairs(R6J) do
		local m = Instance.new("Motor6D")
		m.Name = j[1]
		m.Part0, m.Part1 = parts[j[2]], parts[j[3]]
		m.C0, m.C1 = j[4], j[5]
		m.MaxVelocity = 0.1
		m.Parent = parts[j[2]]
	end
	local hum = Instance.new("Humanoid")
	hum.RigType = Enum.HumanoidRigType.R6
	hum.DisplayName = "Noob Bot"
	hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.Viewer
	hum.WalkSpeed = Config.Bot.Speed
	hum.UseJumpPower = true
	hum.JumpPower = 0
	hum.AutoRotate = false
	hum.Parent = model
	model.PrimaryPart = parts.HumanoidRootPart
	-- lay the rig out in its rest pose before anything is welded by physics
	parts.HumanoidRootPart.CFrame = at or CFrame.new(0, 3, 0)
	for _, j in ipairs(R6J) do
		parts[j[3]].CFrame = parts[j[2]].CFrame * j[4] * j[5]:Inverse()
	end
	return model
end

Rigs.AnimJoints = AnimData.Joints

return Rigs
