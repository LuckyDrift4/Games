-- Plays the tennis clips (AnimData, made in Blender) on an R6 character by writing Motor6D.Transform every frame,
-- so nothing has to be uploaded. A base loop (Idle / Run / Shuffle) runs underneath and one action (a stroke, the
-- serve, a celebration) plays on top with a short crossfade. Call :Step(dt) from RunService.Stepped, which runs after
-- Roblox's own Animator, so these transforms win.
local AnimData = require(script.Parent.AnimData)

local RigAnimator = {}
RigAnimator.__index = RigAnimator

local JOINTS = AnimData.Joints

-- clip keys -> CFrames once
local CLIPS = {}
for name, clip in pairs(AnimData.Clips) do
	local keys = {}
	for i, k in ipairs(clip.Keys) do
		local poses = {}
		for j, c in ipairs(k.P) do
			poses[JOINTS[j]] = CFrame.new(table.unpack(c))
		end
		keys[i] = { t = k.T, e = k.E, p = poses }
	end
	CLIPS[name] = { length = clip.Length, loop = clip.Loop, contact = clip.Contact, toss = clip.Toss, keys = keys }
end
RigAnimator.Clips = CLIPS

local function ease(u, kind)
	u = math.clamp(u, 0, 1)
	if kind == "linear" then
		return u
	elseif kind == "in" then
		return u * u * u
	elseif kind == "out" then
		return 1 - (1 - u) ^ 3
	end
	return u * u * (3 - 2 * u)
end

local function sample(clip, t, joint)
	local keys = clip.keys
	if clip.loop then
		t = t % clip.length
	else
		t = math.clamp(t, 0, clip.length)
	end
	for i = 1, #keys - 1 do
		local a, b = keys[i], keys[i + 1]
		if t <= b.t then
			local u = ease((t - a.t) / math.max(1e-6, b.t - a.t), a.e)
			return a.p[joint]:Lerp(b.p[joint], u)
		end
	end
	return keys[#keys].p[joint]
end

local function findMotors(character)
	local torso = character:FindFirstChild("Torso")
	local root = character:FindFirstChild("HumanoidRootPart")
	local arm = character:FindFirstChild("Right Arm")
	local m = {}
	m.Root = root and root:FindFirstChild("RootJoint")
	if torso then
		m.Neck = torso:FindFirstChild("Neck")
		m.RS = torso:FindFirstChild("Right Shoulder")
		m.LS = torso:FindFirstChild("Left Shoulder")
		m.RH = torso:FindFirstChild("Right Hip")
		m.LH = torso:FindFirstChild("Left Hip")
	end
	m.W = arm and arm:FindFirstChild("RacketGrip")
	return m
end

function RigAnimator.new(character)
	local self = setmetatable({}, RigAnimator)
	self.Character = character
	self.Motors = findMotors(character)
	self.Base, self.BaseTime, self.BaseSpeed = "Idle", 0, 1
	self.PrevBase, self.BaseFade = nil, 1
	self.Action, self.ActionTime, self.ActionSpeed, self.ActionFade = nil, 0, 1, 0
	return self
end

function RigAnimator:Refresh()
	self.Motors = findMotors(self.Character)
end

-- locomotion loop: name = Idle / Run / Shuffle; speed scales the loop rate
function RigAnimator:SetBase(name, speed)
	if name ~= self.Base then
		self.PrevBase, self.PrevBaseTime = self.Base, self.BaseTime
		self.Base, self.BaseTime, self.BaseFade = name, 0, 0
	end
	self.BaseSpeed = speed or 1
end

-- play a one-shot clip; startAt lets a stroke begin part-way so its contact lines up with the ball
function RigAnimator:Play(name, startAt, speed)
	if not CLIPS[name] then
		return
	end
	self.Action, self.ActionTime, self.ActionSpeed = name, startAt or 0, speed or 1
	self.ActionFade = math.min(self.ActionFade, 0.5)
end

-- start a stroke so the racket reaches the ball `lead` seconds from now
function RigAnimator:PlayStroke(name, lead)
	local clip = CLIPS[name]
	if not clip then
		return
	end
	local start = (clip.contact or 0) - (lead or 0.06)
	self:Play(name, math.max(0, start), 1)
end

function RigAnimator:IsPlaying(name)
	return self.Action == name
end

function RigAnimator:Stop()
	self.Action = nil
end

function RigAnimator:Step(dt)
	local motors = self.Motors
	if not motors.Root or not motors.Root.Parent then
		self:Refresh()
		motors = self.Motors
		if not motors.Root then
			return
		end
	end
	if not motors.W or not motors.W.Parent then
		motors.W = nil
		local arm = self.Character:FindFirstChild("Right Arm")
		motors.W = arm and arm:FindFirstChild("RacketGrip")
	end
	self.BaseTime += dt * self.BaseSpeed
	self.BaseFade = math.min(1, self.BaseFade + dt / 0.15)
	if self.PrevBase then
		self.PrevBaseTime += dt
	end
	local actionClip = self.Action and CLIPS[self.Action]
	if actionClip then
		self.ActionTime += dt * self.ActionSpeed
		if self.ActionTime >= actionClip.length then
			self.Action = nil
		else
			self.ActionFade = math.min(1, self.ActionFade + dt / 0.08)
		end
	end
	if not self.Action then
		self.ActionFade = math.max(0, self.ActionFade - dt / 0.12)
	end
	local base, prev = CLIPS[self.Base], self.PrevBase and CLIPS[self.PrevBase]
	for _, j in ipairs(JOINTS) do
		local motor = motors[j]
		if motor then
			local cf = sample(base, self.BaseTime, j)
			if prev and self.BaseFade < 1 then
				cf = sample(prev, self.PrevBaseTime, j):Lerp(cf, self.BaseFade)
			end
			if self.ActionFade > 0 then
				local ac = actionClip or self.LastActionClip
				if ac then
					local at = actionClip and self.ActionTime or ac.length
					cf = cf:Lerp(sample(ac, at, j), self.ActionFade)
				end
			end
			motor.Transform = cf
		end
	end
	if actionClip then
		self.LastActionClip = actionClip
	end
	if self.BaseFade >= 1 then
		self.PrevBase = nil
	end
end

-- put every joint back to rest (when the match ends)
function RigAnimator:Reset()
	for _, j in ipairs(JOINTS) do
		local motor = self.Motors[j]
		if motor and motor.Parent then
			motor.Transform = CFrame.new()
		end
	end
end

return RigAnimator
