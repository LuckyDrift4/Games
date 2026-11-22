-- Tennis server: courts, pads, matches (vs the bot or 1v1), cash and the racket shop.
--
-- Each court is a Model in workspace.Courts with these parts (built by the map):
--   Origin     centre of the net on the court surface; its LookVector points at side 2 (court space +Z = side 1)
--   PadBot     stand here alone to play the Noob Bot
--   Pad1, Pad2 one player on each = a 1v1 match
--   NetWall    invisible wall in the net plane, solid only during a match
--   Exit       where players are put back after a match
--   Scoreboard (optional) a part whose front face shows the score
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local PhysicsService = game:GetService("PhysicsService")

local T = ReplicatedStorage:WaitForChild("Tennis")
local Config = require(T.Config)
local Rigs = require(T.Rigs)
local Data = require(script.Data)
local Match = require(script.Match)

-- remotes
local remotes = Instance.new("Folder")
remotes.Name = "TennisRemotes"
local Event = Instance.new("RemoteEvent")
Event.Name = "TennisEvent"
Event.Parent = remotes
local Action = Instance.new("RemoteEvent")
Action.Name = "TennisAction"
Action.Parent = remotes
remotes.Parent = ReplicatedStorage

Data.start()

-- the optional Blender-mesh stadium: if its models were imported but not built yet, build it now (the place already has
-- the stadium made of Parts, so normally nothing happens here)
do
	local ServerStorage = game:GetService("ServerStorage")
	local install = ServerStorage:FindFirstChild("TennisStadiumInstall")
	local kit = ServerStorage:FindFirstChild("TennisStadiumKit")
	local imported = kit and #kit:GetChildren() > 0 or workspace:FindFirstChild("Stand_w20_0") ~= nil
	if install and imported and not workspace:FindFirstChild("TennisStadium") then
		local ok, err = pcall(function()
			require(install).Install()
		end)
		if not ok then
			warn("[TennisStadium] could not build the stadium: " .. tostring(err))
		end
	end
end

-- the bot and players don't bump into each other's rackets; players never collide with each other on court
pcall(function()
	PhysicsService:RegisterCollisionGroup("TennisPlayers")
	PhysicsService:CollisionGroupSetCollidable("TennisPlayers", "TennisPlayers", false)
end)
local function setGroup(character)
	for _, p in ipairs(character:GetDescendants()) do
		if p:IsA("BasePart") then
			p.CollisionGroup = "TennisPlayers"
		end
	end
end
Players.PlayerAdded:Connect(function(pl)
	pl.CharacterAdded:Connect(function(c)
		task.defer(setGroup, c)
	end)
end)

-- ---------------------------------------------------------------- courts
local courts = {}
local busy = {} -- player -> match
local matches = {} -- court name -> match

local function scoreboardOn(model, part)
	local gui = Instance.new("SurfaceGui")
	gui.Name = "Board"
	gui.Face = Enum.NormalId.Front
	gui.CanvasSize = Vector2.new(800, 300)
	gui.LightInfluence = 0
	gui.Brightness = 1.6
	gui.Parent = part
	local bg = Instance.new("Frame")
	bg.Size = UDim2.fromScale(1, 1)
	bg.BackgroundColor3 = Color3.fromRGB(10, 18, 40)
	bg.Parent = gui
	local function label(name, pos, size, text, color)
		local l = Instance.new("TextLabel")
		l.Name = name
		l.Position, l.Size = pos, size
		l.BackgroundTransparency = 1
		l.Font = Enum.Font.GothamBlack
		l.TextScaled = true
		l.TextColor3 = color or Color3.new(1, 1, 1)
		l.Text = text
		l.Parent = bg
		return l
	end
	local rows = {}
	for i = 1, 2 do
		local y = 0.08 + (i - 1) * 0.36
		rows[i] = {
			name = label("Name" .. i, UDim2.fromScale(0.04, y), UDim2.fromScale(0.58, 0.3), "", i == 1 and Config.Colors.SideA or Config.Colors.SideB),
			games = label("Games" .. i, UDim2.fromScale(0.64, y), UDim2.fromScale(0.14, 0.3), ""),
			points = label("Points" .. i, UDim2.fromScale(0.8, y), UDim2.fromScale(0.16, 0.3), "", Color3.fromRGB(255, 220, 60)),
		}
		rows[i].name.TextXAlignment = Enum.TextXAlignment.Left
	end
	local msg = label("Message", UDim2.fromScale(0.04, 0.8), UDim2.fromScale(0.92, 0.16), model.Name:upper(), Color3.fromRGB(160, 220, 255))
	return function(match, text)
		if match then
			local s = match:scoreTable()
			for i = 1, 2 do
				rows[i].name.Text = (s.serverSide == i and "• " or "  ") .. s.names[i]
				rows[i].games.Text = tostring(s.games[i])
				rows[i].points.Text = tostring(s.points[i])
			end
		elseif text == "" then
			for i = 1, 2 do
				rows[i].name.Text, rows[i].games.Text, rows[i].points.Text = "", "", ""
			end
		end
		msg.Text = (text and text ~= "") and text or (match and "FIRST TO 7 POINTS - BEST OF 5 GAMES" or model.Name:upper())
	end
end

-- every part named Scoreboard in the court model shows the score on its front face
local function scoreboard(model)
	local boards = {}
	for _, d in ipairs(model:GetDescendants()) do
		if d:IsA("BasePart") and d.Name == "Scoreboard" then
			table.insert(boards, scoreboardOn(model, d))
		end
	end
	if #boards == 0 then
		return nil
	end
	return function(match, text)
		for _, b in ipairs(boards) do
			b(match, text)
		end
	end
end

local function padLabel(pad, courtName, text, color)
	local bb = Instance.new("BillboardGui")
	bb.Name = "PadLabel"
	bb.Size = UDim2.fromOffset(240, 84)
	bb.StudsOffsetWorldSpace = Vector3.new(0, 5, 0)
	bb.AlwaysOnTop = false
	bb.MaxDistance = 120
	bb.Parent = pad
	local l = Instance.new("TextLabel")
	l.Size = UDim2.fromScale(1, 1)
	l.BackgroundTransparency = 1
	l.Font = Enum.Font.GothamBlack
	l.TextScaled = true
	l.TextColor3 = color
	l.TextStrokeTransparency = 0.2
	l.Text = text
	l.Size = UDim2.fromScale(1, 0.66)
	l.Position = UDim2.fromScale(0, 0.34)
	l.Parent = bb
	local top = Instance.new("TextLabel")
	top.Size = UDim2.fromScale(1, 0.32)
	top.BackgroundTransparency = 1
	top.Font = Enum.Font.GothamBold
	top.TextScaled = true
	top.TextColor3 = Color3.new(1, 1, 1)
	top.TextStrokeTransparency = 0.3
	top.Text = courtName:upper()
	top.Parent = bb
	return l
end

local function addCourt(model)
	local origin = model:WaitForChild("Origin")
	local c = {
		name = model.Name,
		model = model,
		cf = origin.CFrame,
		netWall = model:FindFirstChild("NetWall"),
		padBot = model:FindFirstChild("PadBot"),
		pad1 = model:FindFirstChild("Pad1"),
		pad2 = model:FindFirstChild("Pad2"),
		exitCF = (model:FindFirstChild("Exit") or origin).CFrame,
		waitSince = {},
	}
	if not c.netWall then
		local w = Instance.new("Part")
		w.Name = "NetWall"
		w.Anchored = true
		w.Transparency = 1
		w.CanCollide = false
		w.Size = Vector3.new(Config.Court.Width + 2 * Config.Court.RunSide, 14, 0.6)
		w.CFrame = origin.CFrame * CFrame.new(0, 7, 0)
		w.Parent = model
		c.netWall = w
	end
	c.netWall.CanCollide = false
	c.setBoard = scoreboard(model) or function() end
	c.setBoard(nil, "")
	if c.padBot then
		c.botLabel = padLabel(c.padBot, model.Name, "PLAY VS BOT", Color3.fromRGB(255, 220, 60))
	end
	if c.pad1 then
		c.l1 = padLabel(c.pad1, model.Name, "1v1", Config.Colors.SideA)
	end
	if c.pad2 then
		c.l2 = padLabel(c.pad2, model.Name, "1v1", Config.Colors.SideB)
	end
	courts[model.Name] = c
end

local folder = workspace:WaitForChild("Courts")
for _, m in ipairs(folder:GetChildren()) do
	addCourt(m)
end
folder.ChildAdded:Connect(addCourt)

-- ---------------------------------------------------------------- matches
local function fire(payload)
	Event:FireAllClients(payload)
end

local function entityFor(player)
	return { player = player, character = player.Character, name = player.DisplayName, isBot = false }
end

local function startMatch(c, a, b)
	local m
	m = Match.new(c, a, b, {
		fire = fire,
		data = Data,
		onEnd = function()
			matches[c.name] = nil
			for _, e in ipairs({ a, b }) do
				if e.player then
					busy[e.player] = nil
				end
			end
		end,
	})
	matches[c.name] = m
	for _, e in ipairs({ a, b }) do
		if e.player then
			busy[e.player] = m
		end
	end
	m:start()
end

local function makeBot(c)
	local side2 = c.cf * CFrame.new(0, 3, -Config.Court.Length / 2 - 3)
	local bot = Rigs.buildNoob("Noob Bot", side2)
	bot.Parent = workspace
	setGroup(bot)
	local hrp = bot.HumanoidRootPart
	pcall(function()
		hrp:SetNetworkOwner(nil)
	end)
	return { character = bot, name = "Noob Bot", isBot = true }
end

local function standingOn(pad)
	if not pad then
		return {}
	end
	local out = {}
	local half = pad.Size / 2
	for _, pl in ipairs(Players:GetPlayers()) do
		local hrp = pl.Character and pl.Character:FindFirstChild("HumanoidRootPart")
		local hum = pl.Character and pl.Character:FindFirstChildOfClass("Humanoid")
		if hrp and hum and hum.Health > 0 and not busy[pl] then
			local p = pad.CFrame:PointToObjectSpace(hrp.Position)
			if math.abs(p.X) <= half.X + 0.5 and math.abs(p.Z) <= half.Z + 0.5 and p.Y > -1 and p.Y < 8 then
				table.insert(out, pl)
			end
		end
	end
	return out
end

local HOLD = 1.0 -- seconds to stand on a pad before a match starts
task.spawn(function()
	while true do
		task.wait(0.25)
		local now = os.clock()
		for name, c in pairs(courts) do
			if not matches[name] and c.model.Parent then
				local onBot = standingOn(c.padBot)
				local on1, on2 = standingOn(c.pad1), standingOn(c.pad2)
				local p1, p2 = on1[1], on2[1]
				if p1 and p2 and p1 ~= p2 then
					c.waitSince.duel = c.waitSince.duel or now
					if now - c.waitSince.duel >= HOLD then
						c.waitSince = {}
						startMatch(c, entityFor(p1), entityFor(p2))
					end
				else
					c.waitSince.duel = nil
				end
				if not matches[name] and onBot[1] then
					c.waitSince.bot = c.waitSince.bot or now
					if now - c.waitSince.bot >= HOLD then
						c.waitSince = {}
						startMatch(c, entityFor(onBot[1]), makeBot(c))
					end
				elseif not onBot[1] then
					c.waitSince.bot = nil
				end
				if c.botLabel then
					c.botLabel.Text = "PLAY VS BOT"
				end
				if c.l1 then
					c.l1.Text = p1 and ("1v1 • " .. p1.DisplayName) or "1v1 • WAITING"
				end
				if c.l2 then
					c.l2.Text = p2 and ("1v1 • " .. p2.DisplayName) or "1v1 • WAITING"
				end
			elseif c.botLabel then
				c.botLabel.Text = "MATCH IN PLAY"
				if c.l1 then
					c.l1.Text = "MATCH IN PLAY"
				end
				if c.l2 then
					c.l2.Text = "MATCH IN PLAY"
				end
			end
		end
	end
end)

-- ---------------------------------------------------------------- client actions
local lastAction = {}
Action.OnServerEvent:Connect(function(player, kind, arg)
	local t = os.clock()
	if lastAction[player] and t - lastAction[player] < 0.08 then
		return
	end
	lastAction[player] = t
	if kind == "hit" then
		local m = busy[player]
		if m then
			for _, e in ipairs(m.players) do
				if e.player == player then
					m:action(e)
				end
			end
		end
	elseif kind == "buy" and type(arg) == "string" then
		local ok, msg = Data.buy(player, arg)
		Event:FireClient(player, { kind = "shop", ok = ok, text = msg })
	elseif kind == "leave" then
		local m = busy[player]
		if m then
			for _, e in ipairs(m.players) do
				if e.player == player then
					m:forfeit(e.side)
				end
			end
		end
	end
end)

Players.PlayerRemoving:Connect(function(pl)
	lastAction[pl] = nil
end)
