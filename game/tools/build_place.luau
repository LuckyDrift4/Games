-- Builds the playable place file: lune run build_place.luau  (from game/tools)
--   map      out/tennis_stadium/TennisStadium.rbxmx  (python3 tools/build.py tennis_stadium)
--   scripts  game/src (Rojo layout: init.server.lua = Script, init.client.lua = LocalScript, *.lua = ModuleScript)
--   anims    game/build/anims.json (python3 game/anim/export.py) -> KeyframeSequences for the Animation Editor
-- Writes out/tennis_game/TennisR6.rbxl.
local fs = require("@lune/fs")
local serde = require("@lune/serde")
local roblox = require("@lune/roblox")
local Instance = roblox.Instance
local Vector3 = roblox.Vector3
local CFrame = roblox.CFrame
local Color3 = roblox.Color3
local Enum = roblox.Enum
local UDim2 = roblox.UDim2

local ROOT = "../.."
local SRC = "../src"
local OUT = ROOT .. "/out/tennis_game/TennisR6.rbxl"

local game = Instance.new("DataModel")
local Workspace = game:GetService("Workspace")
local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")
local ServerStorage = game:GetService("ServerStorage")
local StarterPlayer = game:GetService("StarterPlayer")
local Players = game:GetService("Players")
game:GetService("StarterGui")
game:GetService("SoundService")

-- ---------------------------------------------------------------- scripts
local count = 0
local function scriptFor(path, name, class)
	local s = Instance.new(class)
	s.Name = name
	s.Source = fs.readFile(path)
	count += 1
	return s
end

local function mount(dir, parent)
	for _, entry in ipairs(fs.readDir(dir)) do
		local p = dir .. "/" .. entry
		if fs.isDir(p) then
			local holder
			if fs.isFile(p .. "/init.server.lua") then
				holder = scriptFor(p .. "/init.server.lua", entry, "Script")
			elseif fs.isFile(p .. "/init.client.lua") then
				holder = scriptFor(p .. "/init.client.lua", entry, "LocalScript")
			elseif fs.isFile(p .. "/init.lua") then
				holder = scriptFor(p .. "/init.lua", entry, "ModuleScript")
			else
				holder = Instance.new("Folder")
				holder.Name = entry
			end
			mount(p, holder)
			holder.Parent = parent
		elseif not entry:match("^init%.") then
			local base, kind = entry:match("^(.-)%.(%a+)%.lua$")
			if base and kind == "server" then
				scriptFor(p, base, "Script").Parent = parent
			elseif base and kind == "client" then
				scriptFor(p, base, "LocalScript").Parent = parent
			else
				local mod = entry:match("^(.-)%.lua$")
				if mod then
					scriptFor(p, mod, "ModuleScript").Parent = parent
				end
			end
		end
	end
end

mount(SRC .. "/ReplicatedStorage", ReplicatedStorage)
mount(SRC .. "/ServerScriptService", ServerScriptService)
mount(SRC .. "/ServerStorage", ServerStorage)
-- the Blender stadium's generated setup module (out/tennis_stadium_blender); its models are imported in Studio
do
	local p = ROOT .. "/out/tennis_stadium_blender/roblox/TennisStadiumSetup.lua"
	if fs.isFile(p) then
		scriptFor(p, "TennisStadiumSetup", "ModuleScript").Parent = ServerStorage
	end
end
local sps = StarterPlayer:FindFirstChild("StarterPlayerScripts") or Instance.new("StarterPlayerScripts")
sps.Parent = StarterPlayer
mount(SRC .. "/StarterPlayer/StarterPlayerScripts", sps)

-- icon slots: one ImageLabel per icon. In Studio, set each one's Image to the matching file from TennisIcons/
-- (its File attribute says which). The HUD reads them through Tennis.Icons.
local ICONS = {
	{ "Cash", "Cash.png" },
	{ "CashBundle", "CashBundle.png" },
	{ "Shop", "Shop.png" },
	{ "Trophy", "Trophy.png" },
	{ "Crown", "Crown.png" },
	{ "Close", "Close.png" },
	{ "Back", "Back.png" },
	{ "KeySpace", "KeySpace.png" },
	{ "KeyX", "KeyX.png" },
}
local iconFolder = Instance.new("Folder")
iconFolder.Name = "TennisIcons"
for _, ic in ipairs(ICONS) do
	local im = Instance.new("ImageLabel")
	im.Name = ic[1]
	im.Image = ""
	im.Size = UDim2.fromOffset(100, 100)
	im.BackgroundTransparency = 1
	im:SetAttribute("File", ic[2])
	im.Parent = iconFolder
end
iconFolder.Parent = ReplicatedStorage

-- ---------------------------------------------------------------- the map
local map = roblox.deserializeModel(fs.readFile(ROOT .. "/out/tennis_gameplay/TennisGameplay.rbxmx"))[1]
local parts = 0
for _, child in ipairs(map:GetChildren()) do
	child.Parent = Workspace
end
for _, d in ipairs(Workspace:GetDescendants()) do
	if d:IsA("BasePart") then
		parts += 1
	end
end
-- sign text on the entrance arch (plain words, no logos)
for _, d in ipairs(Workspace:GetDescendants()) do
	if d:IsA("BasePart") and d.Name == "Sign" then
		local gui = Instance.new("SurfaceGui")
		gui.Face = Enum.NormalId.Front
		gui.CanvasSize = roblox.Vector2.new(900, 110)
		gui.LightInfluence = 0
		local l = Instance.new("TextLabel")
		l.Size = UDim2.fromScale(1, 1)
		l.BackgroundTransparency = 1
		l.FontFace = roblox.Font.fromEnum(Enum.Font.GothamBlack)
		l.TextScaled = true
		l.TextColor3 = Color3.fromRGB(255, 255, 255)
		l.Text = "CENTER COURT"
		l.Parent = gui
		gui.Parent = d
	end
end
Workspace.Gravity = 196.2

-- ---------------------------------------------------------------- lighting: bright afternoon, soft haze
Lighting.Technology = Enum.Technology.Future
Lighting.ClockTime = 14.3
Lighting.GeographicLatitude = 30
Lighting.Brightness = 2.6
Lighting.Ambient = Color3.fromRGB(70, 74, 84)
Lighting.OutdoorAmbient = Color3.fromRGB(128, 132, 140)
Lighting.EnvironmentDiffuseScale = 1
Lighting.EnvironmentSpecularScale = 0.6
Lighting.GlobalShadows = true
Lighting.ShadowSoftness = 0.15
local atmo = Instance.new("Atmosphere")
atmo.Density = 0.22
atmo.Offset = 0.15
atmo.Color = Color3.fromRGB(205, 225, 245)
atmo.Decay = Color3.fromRGB(110, 140, 175)
atmo.Glare = 0.2
atmo.Haze = 1.2
atmo.Parent = Lighting
local cc = Instance.new("ColorCorrectionEffect")
cc.Saturation = 0.12
cc.Contrast = 0.06
cc.Brightness = 0.01
cc.Parent = Lighting
local bloom = Instance.new("BloomEffect")
bloom.Intensity = 0.35
bloom.Size = 22
bloom.Threshold = 1.6
bloom.Parent = Lighting
local rays = Instance.new("SunRaysEffect")
rays.Intensity = 0.04
rays.Spread = 0.6
rays.Parent = Lighting

-- ---------------------------------------------------------------- players: classic R6
local okAvatar = pcall(function()
	StarterPlayer.GameSettingsAvatar = Enum.GameAvatarType.R6
end)
StarterPlayer.CharacterWalkSpeed = 18
StarterPlayer.LoadCharacterAppearance = true
Players.CharacterAutoLoads = true

-- ---------------------------------------------------------------- animation rig + KeyframeSequences (optional editing)
local anims = serde.decode("json", fs.readFile("../build/anims.json"))
local function cf(c)
	return CFrame.new(c[1], c[2], c[3], c[4], c[5], c[6], c[7], c[8], c[9], c[10], c[11], c[12])
end
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
	Racket = Vector3.new(0.2, 0.2, 0.2),
}
local rig = Instance.new("Model")
rig.Name = "TennisAnimRig"
local rp = {}
for name, size in pairs(SIZES) do
	local p = Instance.new("Part")
	p.Name = name
	p.Size = size
	p.Color = NOOB[name] or Color3.fromRGB(255, 255, 255)
	p.Material = Enum.Material.SmoothPlastic
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	p.Transparency = (name == "HumanoidRootPart" or name == "Racket") and 1 or 0
	p.Parent = rig
	rp[name] = p
end
rp.HumanoidRootPart.Anchored = true
local mesh = Instance.new("SpecialMesh")
mesh.MeshType = Enum.MeshType.Head
mesh.Scale = Vector3.new(1.25, 1.25, 1.25)
mesh.Parent = rp.Head
local face = Instance.new("Decal")
face.Name = "face"
face.Texture = "rbxasset://textures/face.png"
face.Parent = rp.Head
local hum = Instance.new("Humanoid")
hum.RigType = Enum.HumanoidRigType.R6
hum.Parent = rig
rp.HumanoidRootPart.CFrame = CFrame.new(0, 3, 0)
for _, key in ipairs(anims.order) do
	local j = anims.joints[key]
	local m = Instance.new("Motor6D")
	m.Name = j.motor
	m.Part0, m.Part1 = rp[j.part0], rp[j.part1]
	m.C0, m.C1 = cf(j.c0), cf(j.c1)
	m.Parent = rp[j.part0]
	rp[j.part1].CFrame = rp[j.part0].CFrame * m.C0 * m.C1:Inverse()
end
rig.PrimaryPart = rp.HumanoidRootPart
rig.Parent = ServerStorage

local saves = Instance.new("Folder")
saves.Name = "RBX_ANIMSAVES"
local holder = Instance.new("ObjectValue")
holder.Name = rig.Name
holder.Value = rig
holder.Parent = saves
saves.Parent = ServerStorage
-- pose tree: HumanoidRootPart > Torso > Head / arms / legs, Right Arm > Racket
local TREE = { Torso = "Root", Head = "Neck", ["Right Arm"] = "RS", ["Left Arm"] = "LS", ["Right Leg"] = "RH", ["Left Leg"] = "LH", Racket = "W" }
local CHILDREN = {
	HumanoidRootPart = { "Torso" },
	Torso = { "Head", "Right Arm", "Left Arm", "Right Leg", "Left Leg" },
	["Right Arm"] = { "Racket" },
}
local nkeys = 0
for _, name in ipairs({ "Idle", "Run", "Shuffle", "Forehand", "Backhand", "Serve", "VolleyForehand", "VolleyBackhand", "Smash", "Celebrate", "Upset" }) do
	local clip = anims.clips[name]
	local seq = Instance.new("KeyframeSequence")
	seq.Name = name
	seq.Loop = clip.loop
	seq.Priority = Enum.AnimationPriority[clip.priority]
	for _, k in ipairs(clip.keys) do
		local kf = Instance.new("Keyframe")
		kf.Time = k.t
		local function pose(part, parent)
			local p = Instance.new("Pose")
			p.Name = part
			p.EasingStyle = Enum.PoseEasingStyle.Linear
			local j = TREE[part]
			p.CFrame = j and cf(k.p[j]) or CFrame.new()
			p.Weight = j and 1 or 0
			for _, c in ipairs(CHILDREN[part] or {}) do
				pose(c, p)
			end
			p.Parent = parent
		end
		pose("HumanoidRootPart", kf)
		kf.Parent = seq
		nkeys += 1
	end
	seq.Parent = holder
end

fs.writeFile(OUT, roblox.serializePlace(game))
print(string.format("PLACE_OK %s: %d scripts, %d map parts, %d animation keyframes, R6 setting %s",
	OUT, count, parts, nkeys, okAvatar and "saved" or "NOT available (set Avatar to R6 in Game Settings)"))
