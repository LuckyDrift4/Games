-- Tennis client: draws the ball from the server's shots, animates every player in a match with the Blender-made
-- R6 clips, runs the TV camera, and sends HIT presses (button, Space / click, R2 / X on a controller).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SoundService = game:GetService("SoundService")

local T = ReplicatedStorage:WaitForChild("Tennis")
local Config = require(T:WaitForChild("Config"))
local BP = require(T:WaitForChild("BallPhysics"))
local Court = require(T:WaitForChild("Court"))
local RigAnimator = require(T:WaitForChild("RigAnimator"))
local remotes = ReplicatedStorage:WaitForChild("TennisRemotes")
local Event = remotes:WaitForChild("TennisEvent")
local Action = remotes:WaitForChild("TennisAction")
local UI = require(script:WaitForChild("UI")).build()

local player = Players.LocalPlayer
local camera = workspace.CurrentCamera
local CLIPS = RigAnimator.Clips

local function now()
	return workspace:GetServerTimeNow()
end

-- ---------------------------------------------------------------- per-court state
local courts = {}

local function courtState(name)
	local s = courts[name]
	if s then
		return s
	end
	local model = workspace:WaitForChild("Courts"):WaitForChild(name)
	s = { name = name, cf = model:WaitForChild("Origin").CFrame, chars = {}, anims = {} }
	-- the ball: a bright ball with a trail and a soft shadow on the court
	local ball = Instance.new("Part")
	ball.Name = "TennisBall"
	ball.Shape = Enum.PartType.Ball
	ball.Size = Vector3.one * Config.Ball.Radius * 2
	ball.Color = Config.Colors.Ball
	ball.Material = Enum.Material.SmoothPlastic
	ball.Anchored, ball.CanCollide, ball.CanQuery, ball.CanTouch = true, false, false, false
	ball.Transparency = 1
	local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
	a0.Position, a1.Position = Vector3.new(0, 0.18, 0), Vector3.new(0, -0.18, 0)
	a0.Parent, a1.Parent = ball, ball
	local trail = Instance.new("Trail")
	trail.Attachment0, trail.Attachment1 = a0, a1
	trail.Lifetime = 0.12
	trail.Color = ColorSequence.new(Config.Colors.Ball)
	trail.Transparency = NumberSequence.new(0.35, 1)
	trail.LightEmission = 0.4
	trail.Parent = ball
	ball.Parent = workspace
	local shadow = Instance.new("Part")
	shadow.Name = "BallShadow"
	shadow.Shape = Enum.PartType.Cylinder
	shadow.Size = Vector3.new(0.05, 0.8, 0.8)
	shadow.Color = Color3.new(0, 0, 0)
	shadow.Transparency = 1
	shadow.Material = Enum.Material.SmoothPlastic
	shadow.Anchored, shadow.CanCollide, shadow.CanQuery, shadow.CanTouch, shadow.CastShadow = true, false, false, false, false
	shadow.Parent = workspace
	s.ball, s.trail, s.shadow = ball, trail, shadow
	courts[name] = s
	return s
end

local function animatorFor(s, char)
	if not char then
		return nil
	end
	local a = s.anims[char]
	if not a then
		a = RigAnimator.new(char)
		s.anims[char] = a
	end
	return a
end

local function sfx(id, vol, pitch)
	local snd = Instance.new("Sound")
	snd.SoundId = id
	snd.Volume = vol or 0.5
	snd.PlaybackSpeed = pitch or 1
	snd.Parent = SoundService
	snd:Play()
	snd.Ended:Connect(function()
		snd:Destroy()
	end)
end
-- built-in Roblox sounds (no uploads)
local HIT_SOUND = "rbxasset://sounds/swordlunge.wav"
local BOUNCE_SOUND = "rbxasset://sounds/bass.mp3"

-- ---------------------------------------------------------------- my match
local my = nil -- { court = name, side = 1/2, phase, serverSide, tossT, flight }

local function mySide()
	return my and my.side
end

local function myCourtPos()
	local hrp = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	if not (hrp and my) then
		return nil
	end
	return courts[my.court].cf:PointToObjectSpace(hrp.Position)
end

local function setAnimateScript(enabled)
	local c = player.Character
	local a = c and c:FindFirstChild("Animate")
	if a then
		a.Disabled = not enabled
	end
	local hum = c and c:FindFirstChildOfClass("Humanoid")
	local animator = hum and hum:FindFirstChildOfClass("Animator")
	if animator and not enabled then
		for _, tr in ipairs(animator:GetPlayingAnimationTracks()) do
			tr:Stop(0.1)
		end
	end
end

-- ---------------------------------------------------------------- input
local lastPress = 0
local function pressHit()
	if not my then
		return
	end
	local t = os.clock()
	if t - lastPress < 0.15 then
		return
	end
	lastPress = t
	Action:FireServer("hit")
	local s = courts[my.court]
	local me = myCourtPos()
	if not me then
		return
	end
	-- show the swing right away (the server confirms the hit a moment later)
	if my.phase == "rally" and s.shot and s.shotSide ~= my.side then
		local tn = now()
		local ball = BP.positionAt(s.shot, tn)
		local bounced = false
		for _, b in ipairs(BP.bounces(s.shot)) do
			if b.t <= tn then
				bounced = true
			end
		end
		local stroke = Court.strokeFor(my.side, me, ball, bounced)
		local vel = BP.velocityAt(s.shot, tn)
		local dist = (Court.contactPoint(my.side, me, stroke) - ball).Magnitude
		local lead = math.clamp(dist / math.max(vel.Magnitude, 1), 0.02, 0.16)
		local a = animatorFor(s, player.Character)
		if a then
			a:PlayStroke(stroke, lead)
			my.predicted = { stroke = stroke, at = os.clock() }
		end
	elseif my.phase == "toss" and my.serverSide == my.side then
		local u = (now() - my.tossT) / (my.flight + 0.3)
		UI.meterSet(u)
		my.pressedAt = now()
	end
end

UI.hit.MouseButton1Down:Connect(pressHit)
UI.leave.MouseButton1Click:Connect(function()
	Action:FireServer("leave")
end)
UI.onBuy = function(id)
	Action:FireServer("buy", id)
end

UserInputService.InputBegan:Connect(function(input, processed)
	if input.UserInputType == Enum.UserInputType.Gamepad1 then
		UI.setInputHint("gamepad")
	elseif input.UserInputType == Enum.UserInputType.Touch then
		UI.setInputHint("touch")
	elseif input.UserInputType == Enum.UserInputType.Keyboard or input.UserInputType == Enum.UserInputType.MouseButton1 then
		UI.setInputHint("keyboard")
	end
	if processed then
		return
	end
	local k = input.KeyCode
	if k == Enum.KeyCode.Space or k == Enum.KeyCode.ButtonR2 or k == Enum.KeyCode.ButtonX or k == Enum.KeyCode.ButtonA then
		pressHit()
	elseif input.UserInputType == Enum.UserInputType.MouseButton1 and my then
		pressHit()
	end
end)
if UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled then
	UI.setInputHint("touch")
elseif UserInputService.GamepadEnabled and not UserInputService.KeyboardEnabled then
	UI.setInputHint("gamepad")
end

-- ---------------------------------------------------------------- events from the server
local function sideOfChar(char)
	return char and char:GetAttribute("TennisSide")
end

local function playFor(s, char, clipName, startAt)
	local a = animatorFor(s, char)
	if a and CLIPS[clipName] then
		a:Play(clipName, math.max(0, startAt or 0), 1)
	end
end

local handlers = {}

function handlers.start(d, s)
	s.chars = {}
	for i, c in ipairs(d.chars) do
		s.chars[i] = c
		animatorFor(s, c)
	end
	s.names = d.names
	s.score = d.score
	if d.chars[1] == player.Character or d.chars[2] == player.Character then
		my = { court = d.court, side = d.chars[1] == player.Character and 1 or 2, phase = "countdown" }
		setAnimateScript(false)
		UI.showMatch(true)
		UI.setScore(d.score, my.side)
		local n = d.countdown or 3
		task.spawn(function()
			for i = n, 1, -1 do
				UI.flash(tostring(i), UI.colors.WHITE, d.mode == "bot" and "VS NOOB BOT" or "1v1", 0.9)
				task.wait(1)
			end
			UI.flash("PLAY!", UI.colors.GREEN, nil, 0.8)
		end)
	end
end

function handlers.ready(d, s)
	s.shot = nil
	s.score = d.score
	if my and my.court == d.court then
		my.phase, my.serverSide = "ready", d.serverSide
		UI.setScore(d.score, my.side)
		UI.meterHide()
		if d.serverSide == my.side then
			UI.setHint(d.faults > 0 and "SECOND SERVE - press HIT to toss" or "YOUR SERVE - press HIT to toss")
		else
			UI.setHint(nil)
		end
	end
end

function handlers.toss(d, s)
	s.shot = BP.unpack(d.shot)
	s.shotSide = d.side
	s.showBall = true
	local clip = CLIPS.Serve
	playFor(s, d.char, "Serve", clip.toss + (now() - s.shot.t0))
	if my and my.court == d.court then
		my.phase = "toss"
		if d.side == my.side then
			my.tossT, my.flight = s.shot.t0, clip.contact - clip.toss
			my.pressedAt = nil
			UI.setHint("press HIT when the ball is at the top")
			UI.meterShow(my.flight, my.flight + 0.3)
		end
	end
end

function handlers.shot(d, s)
	s.shot = BP.unpack(d.shot)
	s.shotSide = d.side
	s.showBall = true
	sfx(HIT_SOUND, 0.6, 1.4 + math.random() * 0.2)
	local late = now() - s.shot.t0
	local isMe = d.char == player.Character
	if d.stroke ~= "Serve" then
		local a = animatorFor(s, d.char)
		local predicted = isMe and my and my.predicted and os.clock() - my.predicted.at < 0.6
		if not (predicted and a and a:IsPlaying(my.predicted.stroke)) then
			playFor(s, d.char, d.stroke, (CLIPS[d.stroke] and CLIPS[d.stroke].contact or 0) + late)
		end
	end
	if my and my.court == d.court then
		my.phase = "rally"
		my.predicted = nil
		UI.setHint(nil)
		UI.meterHide()
	end
end

function handlers.swing(d, s)
	if d.char == player.Character and my and my.predicted and os.clock() - my.predicted.at < 0.6 then
		return
	end
	local clip = CLIPS[d.stroke]
	playFor(s, d.char, d.stroke, clip and math.max(0, (clip.contact or 0) - 0.12) or 0)
end

function handlers.bounce(d, s)
	sfx(BOUNCE_SOUND, 0.25, 2.2)
end

function handlers.ballStop(d, s)
	s.shot = nil
	s.stopAt = Vector3.new(table.unpack(d.at))
	s.hideAt = os.clock() + 1.2
end

local REASON = {
	ACE = "ACE!",
	WINNER = "WINNER!",
	OUT = "OUT",
	NET = "NET",
	["DOUBLE FAULT"] = "DOUBLE FAULT",
}

function handlers.point(d, s)
	s.score = d.score
	s.hideAt = os.clock() + 1.2
	if not my or my.court ~= d.court then
		return
	end
	my.phase = "point"
	UI.setScore(d.score, my.side)
	UI.meterHide()
	UI.setHint(nil)
	local won = d.side == my.side
	local txt = REASON[d.reason] or d.reason
	if d.matchWon then
		return
	end
	if d.game then
		UI.flash("GAME " .. (won and "YOU" or string.upper(d.score.names[d.side] or "")), won and UI.colors.GREEN or UI.colors.RED,
			string.format("GAMES %d - %d", d.score.games[my.side], d.score.games[3 - my.side]), 1.8)
		playFor(s, s.chars[d.side], "Celebrate", 0)
	else
		UI.flash(txt, won and UI.colors.GREEN or UI.colors.RED, won and "POINT TO YOU" or "POINT LOST", 1.3)
	end
end

function handlers.message(d, s)
	if my and my.court == d.court then
		UI.flash(d.text, UI.colors.YELLOW, nil, 1.2)
	end
end

function handlers.finish(d, s)
	s.shot = nil
	s.hideAt = os.clock()
	local winChar = s.chars[d.winner]
	local loseChar = s.chars[3 - d.winner]
	task.delay(0.2, function()
		playFor(s, winChar, "Celebrate", 0)
		playFor(s, loseChar, "Upset", 0)
	end)
	if my and my.court == d.court then
		local won = d.winner == my.side
		local sc = d.score
		UI.showResult(won, string.format("GAMES %d - %d%s", sc.games[my.side], sc.games[3 - my.side], d.forfeit and " (FORFEIT)" or ""),
			d.rewards and d.rewards[my.side] or 0)
		my.phase = "over"
		task.delay(4.4, function()
			if my and my.phase == "over" then
				my = nil
				UI.showMatch(false)
				setAnimateScript(true)
				camera.CameraType = Enum.CameraType.Custom
			end
		end)
	end
	task.delay(4.6, function()
		for char, a in pairs(s.anims) do
			if not char.Parent or not char:GetAttribute("TennisCourt") then
				a:Reset()
				s.anims[char] = nil
			end
		end
	end)
end

function handlers.shop(d)
	UI.flash(d.text, d.ok and UI.colors.GREEN or UI.colors.RED, nil, 1.1)
	UI.refreshShop()
end

Event.OnClientEvent:Connect(function(d)
	local h = handlers[d.kind]
	if not h then
		return
	end
	local s = d.court and courtState(d.court)
	h(d, s)
end)

-- ---------------------------------------------------------------- every frame
local camX = 0
RunService.Stepped:Connect(function(_, dt)
	for _, s in pairs(courts) do
		for char, a in pairs(s.anims) do
			if char.Parent then
				local hrp = char:FindFirstChild("HumanoidRootPart")
				if hrp then
					-- locomotion: idle / run (forward or backpedal) / side shuffle, relative to facing the net
					local v = hrp.AssemblyLinearVelocity
					local side = sideOfChar(char) or 1
					local f = s.cf:VectorToWorldSpace(Court.facing(side))
					local r = s.cf:VectorToWorldSpace(Court.rightOf(side))
					local fwd, lat = v:Dot(f), v:Dot(r)
					local speed = math.sqrt(fwd * fwd + lat * lat)
					if speed < 1.5 then
						a:SetBase("Idle", 1)
					elseif math.abs(lat) > math.abs(fwd) * 1.1 then
						a:SetBase("Shuffle", math.clamp(speed / 14, 0.7, 1.5))
					else
						a:SetBase("Run", (fwd >= 0 and 1 or -1) * math.clamp(speed / 18, 0.6, 1.4))
					end
				end
				a:Step(dt)
			else
				s.anims[char] = nil
			end
		end
	end
end)

RunService.RenderStepped:Connect(function(dt)
	local tn = now()
	for _, s in pairs(courts) do
		local pos
		if s.shot then
			pos = BP.positionAt(s.shot, tn)
		elseif s.stopAt and s.hideAt and os.clock() < s.hideAt then
			pos = s.stopAt
		end
		if pos and s.hideAt and os.clock() > s.hideAt and not s.shot then
			pos = nil
		end
		if pos then
			local w = s.cf:PointToWorldSpace(pos)
			s.ball.CFrame = CFrame.new(w)
			s.ball.Transparency = 0
			s.trail.Enabled = true
			local g = s.cf:PointToWorldSpace(Vector3.new(pos.X, 0.04, pos.Z))
			s.shadow.CFrame = CFrame.new(g) * s.cf.Rotation * CFrame.Angles(0, 0, math.rad(90))
			s.shadow.Transparency = math.clamp(0.45 + pos.Y / 30, 0.45, 0.9)
		else
			s.ball.Transparency = 1
			s.trail.Enabled = false
			s.shadow.Transparency = 1
		end
	end
	-- TV camera behind my baseline, sliding with me
	if my and courts[my.court] then
		local s = courts[my.court]
		local me = myCourtPos()
		if me then
			camera.CameraType = Enum.CameraType.Scriptable
			local zs = Court.zSign(my.side)
			camX += (math.clamp(me.X * 0.5, -9, 9) - camX) * math.min(1, dt * 4)
			local L = Config.Court.Length
			local eye = s.cf:PointToWorldSpace(Vector3.new(camX, 19, zs * (L / 2 + 30)))
			local look = s.cf:PointToWorldSpace(Vector3.new(camX * 0.4, 0, zs * -4))
			camera.CFrame = CFrame.lookAt(eye, look)
			camera.FieldOfView = 52
		end
		if my.phase == "toss" and my.serverSide == my.side and my.tossT and not my.pressedAt then
			UI.meterSet((tn - my.tossT) / (my.flight + 0.3))
		end
	end
end)

player.CharacterAdded:Connect(function()
	if my then
		my = nil
		UI.showMatch(false)
		camera.CameraType = Enum.CameraType.Custom
	end
end)
