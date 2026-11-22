-- MakeRacketTool: run once in the Studio command bar (Edit mode) after importing TennisRacket.glb into Workspace.
-- Styles every part, makes the grip the Handle, welds the rest to it and puts the Tool in StarterPack.
-- If the racket points the wrong way in your hand, change GRIP below (the hand's frame in Handle space).

local MODEL_NAME = "TennisRacket"
local GRIP = CFrame.fromMatrix(
	Vector3.new(0, -0.08, 0),   -- hand slightly below the middle of the grip
	Vector3.new(0, 0, 1),       -- hand right    = racket face normal (string bed faces sideways)
	Vector3.new(-1, 0, 0),      -- hand up       = across the racket head
	Vector3.new(0, -1, 0)       -- hand back     = toward the butt cap (the head points forward)
)

local DARK = Color3.fromRGB(16, 16, 18)
local ACCENT = Color3.fromRGB(22, 88, 214)
local STYLE = {
	Frame = { DARK, Enum.Material.SmoothPlastic, 0.08 },
	FrameAccent = { ACCENT, Enum.Material.SmoothPlastic, 0.12 },
	FrameStripe = { Color3.fromRGB(226, 228, 232), Enum.Material.Metal, 0 },
	Bumper = { Color3.fromRGB(42, 42, 46), Enum.Material.Plastic, 0 },
	GrommetStrip = { Color3.fromRGB(28, 28, 31), Enum.Material.Plastic, 0 },
	Grommets = { Color3.fromRGB(28, 28, 31), Enum.Material.Plastic, 0 },
	StringsMains = { Color3.fromRGB(233, 227, 206), Enum.Material.SmoothPlastic, 0 },
	StringsCrosses = { Color3.fromRGB(233, 227, 206), Enum.Material.SmoothPlastic, 0 },
	Grip = { Color3.fromRGB(236, 238, 241), Enum.Material.Fabric, 0 },
	GripTape = { DARK, Enum.Material.SmoothPlastic, 0.05 },
	ButtCap = { DARK, Enum.Material.SmoothPlastic, 0.08 },
	ButtLogo = { ACCENT, Enum.Material.SmoothPlastic, 0.12 },
	Dampener = { Color3.fromRGB(240, 120, 24), Enum.Material.Plastic, 0 },
}

local model = workspace:FindFirstChild(MODEL_NAME)
assert(model, "Import TennisRacket.glb into Workspace first (File > Import 3D), named " .. MODEL_NAME)

local parts, handle = {}, nil
for _, p in model:GetDescendants() do
	if p:IsA("BasePart") then
		local s = STYLE[p.Name]
		if s then
			if p:IsA("MeshPart") then p.TextureID = "" end
			p.Color, p.Material, p.Reflectance = s[1], s[2], s[3]
		end
		p.Anchored = false
		p.CanCollide = false
		p.Massless = true
		p.CanTouch = (p.Name == "StringsMains" or p.Name == "StringsCrosses")   -- string bed can detect a ball
		table.insert(parts, p)
		if p.Name == "Grip" then handle = p end
	end
end
assert(handle, "No part named Grip in the imported model")

local tool = Instance.new("Tool")
tool.Name = MODEL_NAME
tool.CanBeDropped = false
tool.RequiresHandle = true
handle.Name = "Handle"
handle.Massless = false
for _, p in parts do
	p.Parent = tool
	if p ~= handle then
		local w = Instance.new("WeldConstraint")
		w.Part0, w.Part1 = handle, p
		w.Parent = handle
	end
end
tool.Grip = GRIP
tool.Parent = game:GetService("StarterPack")
model:Destroy()
print("TennisRacket tool is in StarterPack with " .. #parts .. " parts")
