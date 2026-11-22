-- One tennis match on one court: vs the bot or 1v1. The server owns the rules: it keeps the current shot (exact
-- maths from BallPhysics), checks the net and every bounce, validates hits, plays the bot, and keeps the score.
-- Clients only draw the ball and animate the players from the events fired here.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local T = ReplicatedStorage.Tennis
local Config = require(T.Config)
local BP = require(T.BallPhysics)
local Court = require(T.Court)
local Rigs = require(T.Rigs)

local Match = {}
Match.__index = Match

local rand = Random.new()
local function now()
	return workspace:GetServerTimeNow()
end

-- court = { name, cf, netWall, exitCF, setBoard(match, message) }
-- a / b = { player = Player?, character = Model, name = string, isBot = bool }
-- ctx = { fire = function(payload), data = Data, onEnd = function(match) }
function Match.new(court, a, b, ctx)
	local self = setmetatable({}, Match)
	self.court, self.ctx = court, ctx
	a.side, b.side = 1, 2
	self.players = { a, b }
	self.mode = (a.isBot or b.isBot) and "bot" or "1v1"
	self.bot = a.isBot and a or (b.isBot and b or nil)
	self.points, self.games = { 0, 0 }, { 0, 0 }
	self.serverSide = rand:NextInteger(1, 2)
	self.faults = 0
	self.phase = "countdown"
	self.lastSwing = { 0, 0 }
	self.conns = {}
	return self
end

-- ---------------------------------------------------------------- helpers
function Match:toWorld(p)
	return self.court.cf:PointToWorldSpace(p)
end

function Match:toCourt(w)
	return self.court.cf:PointToObjectSpace(w)
end

function Match:fire(kind, data)
	data = data or {}
	data.kind = kind
	data.court = self.court.name
	self.ctx.fire(data)
end

function Match:scoreTable()
	return {
		points = { self.points[1], self.points[2] },
		games = { self.games[1], self.games[2] },
		serverSide = self.serverSide,
		names = { self.players[1].name, self.players[2].name },
	}
end

function Match:root(e)
	return e.character and e.character:FindFirstChild("HumanoidRootPart")
end

function Match:humanoid(e)
	return e.character and e.character:FindFirstChildOfClass("Humanoid")
end

function Match:place(e, spot)
	local hrp = self:root(e)
	if not hrp then
		return
	end
	local pos = self:toWorld(spot + Vector3.new(0, 3, 0))
	local look = self.court.cf:VectorToWorldSpace(Court.facing(e.side))
	e.character:PivotTo(CFrame.lookAt(pos, pos + look))
	hrp.AssemblyLinearVelocity = Vector3.zero
end

function Match:setFrozen(e, frozen)
	local hum = self:humanoid(e)
	if hum then
		hum.WalkSpeed = frozen and 0 or (e.isBot and Config.Bot.Speed or Config.Player.WalkSpeed)
	end
end

function Match:bouncesBefore(t)
	local n = 0
	if self.shot then
		for _, b in ipairs(BP.bounces(self.shot)) do
			if b.t <= t then
				n += 1
			end
		end
	end
	return n
end

-- ---------------------------------------------------------------- setup / teardown
function Match:setup(e)
	local hum, hrp = self:humanoid(e), self:root(e)
	if not (hum and hrp) then
		return
	end
	e.saved = { walk = hum.WalkSpeed, jp = hum.JumpPower, useJp = hum.UseJumpPower, auto = hum.AutoRotate }
	hum.UseJumpPower = true
	hum.JumpPower = 0
	hum.AutoRotate = false
	self:setFrozen(e, false)
	local item = e.player and self.ctx.data.equipped(e.player) or Config.Shop[1]
	Rigs.attachRacket(e.character, item.Color, item.Neon)
	-- always face the net: the player runs and side-steps, never turns away
	local att = Instance.new("Attachment")
	att.Name = "TennisFace"
	att.Parent = hrp
	local ao = Instance.new("AlignOrientation")
	ao.Name = "TennisFace"
	ao.Mode = Enum.OrientationAlignmentMode.OneAttachment
	ao.Attachment0 = att
	ao.RigidityEnabled = true
	ao.CFrame = CFrame.lookAt(Vector3.zero, self.court.cf:VectorToWorldSpace(Court.facing(e.side)))
	ao.Parent = hrp
	e.character:SetAttribute("TennisCourt", self.court.name)
	e.character:SetAttribute("TennisSide", e.side)
end

function Match:restore(e)
	local c = e.character
	if not (c and c.Parent) then
		return
	end
	Rigs.removeRacket(c)
	local hrp, hum = self:root(e), self:humanoid(e)
	if hrp then
		for _, n in ipairs({ "TennisFace" }) do
			for _, ch in ipairs(hrp:GetChildren()) do
				if ch.Name == n then
					ch:Destroy()
				end
			end
		end
	end
	if hum and e.saved then
		hum.WalkSpeed, hum.JumpPower, hum.UseJumpPower, hum.AutoRotate = e.saved.walk, e.saved.jp, e.saved.useJp, e.saved.auto
	end
	c:SetAttribute("TennisCourt", nil)
	c:SetAttribute("TennisSide", nil)
end

function Match:start()
	for _, e in ipairs(self.players) do
		self:setup(e)
	end
	self.court.netWall.CanCollide = true
	local deuce = true
	for _, e in ipairs(self.players) do
		self:place(e, Court.startSpot(e.side, e.side == self.serverSide and "server" or "receiver", deuce))
	end
	self:fire("start", {
		chars = { self.players[1].character, self.players[2].character },
		names = { self.players[1].name, self.players[2].name },
		mode = self.mode,
		score = self:scoreTable(),
		countdown = Config.Scoring.StartCountdown,
	})
	self.court.setBoard(self, "GET READY")
	for _, e in ipairs(self.players) do
		local hum = self:humanoid(e)
		if hum then
			table.insert(self.conns, hum.Died:Connect(function()
				self:forfeit(e.side)
			end))
		end
		if e.player then
			table.insert(self.conns, e.player.AncestryChanged:Connect(function(_, parent)
				if not parent then
					self:forfeit(e.side)
				end
			end))
		end
	end
	table.insert(self.conns, RunService.Heartbeat:Connect(function()
		self:update()
	end))
	task.delay(Config.Scoring.StartCountdown, function()
		if self.phase == "countdown" then
			self:beginPoint()
		end
	end)
end

function Match:cleanup()
	for _, c in ipairs(self.conns) do
		c:Disconnect()
	end
	self.conns = {}
	self.court.netWall.CanCollide = false
	for _, e in ipairs(self.players) do
		if e.isBot then
			if e.character then
				e.character:Destroy()
			end
		else
			self:restore(e)
			if e.character and e.character.Parent then
				e.character:PivotTo(self.court.exitCF * CFrame.new(rand:NextNumber(-4, 4), 3, rand:NextNumber(-3, 3)))
			end
		end
	end
	self.court.setBoard(nil, "")
	self.ctx.onEnd(self)
end

-- ---------------------------------------------------------------- points
function Match:beginPoint()
	if self.phase == "over" then
		return
	end
	self.phase = "ready"
	self.shot = nil
	local deuce = (self.points[1] + self.points[2]) % 2 == 0
	local srv = self.players[self.serverSide]
	local rcv = self.players[Court.other(self.serverSide)]
	local spot = Court.startSpot(srv.side, "server", deuce)
	self.serverX = spot.X
	self:place(srv, spot)
	if self.faults == 0 then
		self:place(rcv, Court.startSpot(rcv.side, "receiver", deuce))
	end
	self:setFrozen(srv, true)
	self:setFrozen(rcv, false)
	self:fire("ready", { serverSide = self.serverSide, faults = self.faults, score = self:scoreTable() })
	self.court.setBoard(self)
	if srv.isBot then
		local token = {}
		self.botToken = token
		task.delay(Config.Bot.ServeDelay, function()
			if self.phase == "ready" and self.botToken == token then
				self:toss()
				task.delay(Config.Serve.TossPeakTime + rand:NextNumber(-0.04, 0.05), function()
					if self.phase == "toss" and self.botToken == token then
						self:serveHit(true)
					end
				end)
			end
		end)
	end
end

function Match:toss()
	local srv = self.players[self.serverSide]
	local hrp = self:root(srv)
	if not hrp then
		return
	end
	local p = self:toCourt(hrp.Position)
	-- the toss leaves the left hand and meets the racket exactly when the Serve animation does
	local from, v, T = Court.serveToss(srv.side, p)
	local t = now()
	self.shot = BP.make(from, v, t, 0)
	self.tossT, self.tossFlight = t, T
	self.phase = "toss"
	self:fire("toss", { shot = BP.pack(self.shot), side = srv.side, char = srv.character })
	local token = {}
	self.tossToken = token
	task.delay(Config.Serve.ResetAfter, function()
		if self.phase == "toss" and self.tossToken == token then
			self:fire("message", { text = "LET" })
			self:beginPoint()
		end
	end)
end

function Match:serveHit(isBot)
	local srv = self.players[self.serverSide]
	local S = Config.Serve
	local t = now()
	local off = math.abs(t - (self.tossT + self.tossFlight))
	local q
	if isBot then
		q = rand:NextNumber(0.45, 0.95)
	elseif off <= S.PerfectWindow then
		q = 1
	elseif off <= S.GoodWindow then
		q = 1 - (off - S.PerfectWindow) / (S.GoodWindow - S.PerfectWindow) * 0.75
	else
		q = 0.05
	end
	local contact = BP.positionAt(self.shot, t)
	local rs = Court.zSign(Court.other(srv.side))
	local want = self.serverX >= 0 and -1 or 1
	local second = self.faults > 0
	local C = Config.Court
	local target = Vector3.new(want * rand:NextNumber(1.5, 12.2), 0, rs * (second and rand:NextNumber(12, 18) or rand:NextNumber(14, 20.2)))
	local flight = second and (1.12 - 0.25 * q) or (1.0 - 0.38 * q)
	local spin = second and 0.6 or 0.25
	local faultChance
	if isBot then
		faultChance = second and Config.Bot.SecondServeFault or Config.Bot.FirstServeFault
	else
		faultChance = q >= 0.3 and 0 or (0.75 - q)
		if second then
			faultChance *= 0.6
		end
	end
	if rand:NextNumber() < faultChance then
		local k = rand:NextInteger(1, 3)
		if k == 1 then
			target = Vector3.new(target.X, 0, rs * (C.ServiceLine + rand:NextNumber(1.5, 5)))
		elseif k == 2 then
			target = Vector3.new(want * (C.SinglesWidth / 2 + rand:NextNumber(1, 3)), 0, target.Z)
		else
			return self:launch(srv.side, contact, Vector3.new(target.X * 0.3, 0, rs * 2), 0.42, 0, "Serve", true, true)
		end
	end
	self:launch(srv.side, contact, target, flight, spin, "Serve", true)
end

function Match:launch(side, from, target, flight, spin, stroke, isServe, noClear)
	local landing = Vector3.new(target.X, Config.Ball.Radius, target.Z)
	local v = BP.solve(from, landing, flight, spin, noClear and -1e9 or (isServe and 0.25 or 0.6))
	local t = now()
	self.shot = BP.make(from, v, t, spin)
	self.shotSide, self.shotServe = side, isServe and true or false
	self.netChecked, self.bounceIdx = false, 0
	self.phase = "rally"
	if isServe then
		self:setFrozen(self.players[side], false)
	end
	self:fire("shot", { shot = BP.pack(self.shot), side = side, stroke = stroke, char = self.players[side].character })
end

-- the receiving player pressed HIT (or the bot decided to swing)
function Match:action(e)
	if self.phase == "ready" and e.side == self.serverSide and not e.isBot then
		return self:toss()
	end
	if self.phase == "toss" and e.side == self.serverSide and not e.isBot then
		return self:serveHit(false)
	end
	if self.phase == "rally" then
		return self:tryHit(e)
	end
end

function Match:tryHit(e)
	local t = now()
	if t - self.lastSwing[e.side] < Config.Player.SwingCooldown then
		return
	end
	self.lastSwing[e.side] = t
	local hrp = self:root(e)
	if not hrp then
		return
	end
	local me = self:toCourt(hrp.Position)
	local P = Config.Player
	if not self.shot or self.shotSide == e.side then
		self:fire("swing", { side = e.side, char = e.character, stroke = "Forehand" })
		return
	end
	local best, bestT, bestStroke, bestBall
	for i = 0, 18 do
		local tt = t - P.HitWindowBack + (P.HitWindowBack + P.HitWindowAhead) * i / 18
		if tt >= self.shot.t0 then
			local ball = BP.positionAt(self.shot, tt)
			local bounced = self:bouncesBefore(tt)
			if ball.Z * Court.zSign(e.side) > -1 and bounced < 2 and not (self.shotServe and bounced == 0) then
				local stroke = Court.strokeFor(e.side, me, ball, bounced > 0)
				local d = (ball - Court.contactPoint(e.side, me, stroke)).Magnitude
				if not best or d < best then
					best, bestT, bestStroke, bestBall = d, tt, stroke, ball
				end
			end
		end
	end
	if not best or best > P.Reach then
		local ball = BP.positionAt(self.shot, t)
		self:fire("swing", { side = e.side, char = e.character, stroke = Court.strokeFor(e.side, me, ball, self:bouncesBefore(t) > 0) })
		return
	end
	local q = math.clamp(1 - best / P.Reach, 0, 1) ^ 0.7
	local vel = BP.velocityAt(self.shot, bestT)
	local early = 0
	if vel.Magnitude > 1 then
		early = math.clamp((Court.contactPoint(e.side, me, bestStroke) - bestBall):Dot(vel.Unit) / 2.5, -1, 1)
	end
	self:returnShot(e.side, me, bestBall, bestStroke, q, early, false)
end

-- where the ball goes: better contact = deeper, faster, closer to the lines; early = pulled cross-court
function Match:returnShot(side, me, ball, stroke, q, early, forceError)
	local zs = Court.zSign(side)
	local opp = -zs
	local C = Config.Court
	local half = C.SinglesWidth / 2
	local target, flight, spin
	if stroke == "Smash" then
		target = Vector3.new(rand:NextNumber(-half + 2, half - 2), 0, opp * rand:NextNumber(16, 33))
		flight, spin = 0.5, 0.1
	elseif stroke == "VolleyForehand" or stroke == "VolleyBackhand" then
		local dirX = (stroke == "VolleyForehand" and -zs or zs) * early
		target = Vector3.new(math.clamp(dirX * 10 + rand:NextNumber(-3, 3), -half + 1.5, half - 1.5), 0, opp * rand:NextNumber(14, 30))
		flight, spin = 0.95 - 0.2 * q, -0.25
	else
		local deep = math.min(21 + 13 * q + rand:NextNumber(-2.5, 2.5), C.Length / 2 - 1)
		local dirX = (stroke == "Forehand" and -zs or zs) * early
		local x = dirX * (4 + 7.5 * q) + rand:NextNumber(-2.5, 2.5)
		target = Vector3.new(math.clamp(x, -half + 0.8, half - 0.8), 0, opp * deep)
		flight, spin = 1.38 - 0.42 * q, 0.3 + 0.45 * q
		if math.abs(me.Z) > C.Length / 2 + 6 and q < 0.45 then -- deep and stretched: lob it
			target = Vector3.new(target.X, 0, opp * rand:NextNumber(30, 37))
			flight, spin = 2.15, -0.1
		end
	end
	local wild = (1 - q) * 5
	target += Vector3.new(rand:NextNumber(-wild, wild), 0, rand:NextNumber(-wild, wild) * 0.8)
	if forceError or (q < 0.22 and rand:NextNumber() < 0.45) then
		local k = rand:NextInteger(1, 3)
		if k == 1 then
			target = Vector3.new(target.X, 0, opp * (C.Length / 2 + rand:NextNumber(2, 7)))
		elseif k == 2 then
			target = Vector3.new((target.X >= 0 and 1 or -1) * (half + rand:NextNumber(1.5, 4)), 0, target.Z)
		else
			return self:launch(side, ball, Vector3.new(target.X, 0, opp * 3), 0.45, 0, stroke, false, true)
		end
	end
	self:launch(side, ball, target, flight, spin, stroke, false)
end

function Match:update()
	local t = now()
	if self.phase == "rally" and self.shot then
		self:checkRally(t)
	end
	if self.bot then
		self:botStep(t)
	end
end

function Match:checkRally(t)
	local shot = self.shot
	local r = Config.Ball.Radius
	if not self.netChecked then
		local tn, yn, xn = BP.netCrossing(shot)
		if not tn then
			self.netChecked = true
		elseif t >= tn then
			self.netChecked = true
			if yn < BP.netHeight(xn) + r * 0.5 then
				self:fire("ballStop", { at = { xn, math.max(yn, 0.6), 0 } })
				if self.shotServe then
					return self:fault("NET")
				end
				return self:pointTo(Court.other(self.shotSide), "NET")
			end
		end
	end
	local bounces = BP.bounces(shot)
	while self.bounceIdx < #bounces and bounces[self.bounceIdx + 1].t <= t do
		self.bounceIdx += 1
		local b = bounces[self.bounceIdx]
		local recv = Court.other(self.shotSide)
		if self.bounceIdx == 1 then
			self:fire("bounce", { at = { b.p.X, b.p.Y, b.p.Z } })
			if Court.sideOf(b.p.Z) == self.shotSide then
				if self.shotServe then
					return self:fault("FAULT")
				end
				return self:pointTo(recv, "OUT")
			end
			if self.shotServe then
				if not Court.inServiceBox(b.p, self.shotSide, self.serverX) then
					return self:fault("FAULT")
				end
			elseif not Court.inCourt(b.p, recv) then
				return self:pointTo(recv, "OUT")
			end
		else
			return self:pointTo(self.shotSide, self.shotServe and "ACE" or "WINNER")
		end
	end
	if t > shot.t0 + 7 then
		return self:pointTo(self.shotSide, "WINNER")
	end
end

function Match:fault(reason)
	self.phase = "point"
	self.faults += 1
	if self.faults >= Config.Serve.MaxFaults then
		self.faults = 0
		return self:pointTo(Court.other(self.serverSide), "DOUBLE FAULT")
	end
	self:fire("message", { text = reason == "NET" and "NET - SECOND SERVE" or "FAULT - SECOND SERVE" })
	task.delay(1.4, function()
		if self.phase == "point" then
			self:beginPoint()
		end
	end)
end

function Match:pointTo(side, reason)
	if self.phase == "over" then
		return
	end
	self.phase = "point"
	self.faults = 0
	self.points[side] += 1
	local winner = self.players[side]
	if winner.player then
		self.ctx.data.addCash(winner.player, Config.Rewards.PointWon)
	end
	local gameWon = self.points[side] >= Config.Scoring.PointsToWinGame
	if gameWon then
		self.games[side] += 1
		self.points = { 0, 0 }
		self.serverSide = Court.other(self.serverSide)
	end
	local matchWon = self.games[side] >= Config.Scoring.GamesToWinMatch
	self:fire("point", { side = side, reason = reason, score = self:scoreTable(), game = gameWon, matchWon = matchWon })
	self.court.setBoard(self)
	if matchWon then
		task.delay(1.2, function()
			self:finish(side, false)
		end)
	else
		task.delay(Config.Scoring.PointPause, function()
			if self.phase == "point" then
				self:beginPoint()
			end
		end)
	end
end

function Match:finish(winnerSide, forfeit)
	if self.phase == "over" then
		return
	end
	self.phase = "over"
	self.shot = nil
	local R = Config.Rewards
	local rewards = {}
	for _, e in ipairs(self.players) do
		if e.player and e.player.Parent then
			local won = e.side == winnerSide
			local amount
			if self.mode == "bot" then
				amount = won and R.WinBot or R.LoseBot
			else
				amount = won and R.Win1v1 or R.Lose1v1
			end
			if forfeit and not won then
				amount = 0
			end
			self.ctx.data.addCash(e.player, amount)
			if won then
				self.ctx.data.addWin(e.player)
			end
			rewards[e.side] = amount
		end
	end
	self:fire("finish", { winner = winnerSide, rewards = rewards, score = self:scoreTable(), forfeit = forfeit })
	self.court.setBoard(self, string.upper(self.players[winnerSide].name) .. " WINS")
	task.delay(4.5, function()
		self:cleanup()
	end)
end

function Match:forfeit(side)
	if self.phase ~= "over" then
		self:finish(Court.other(side), true)
	end
end

-- ---------------------------------------------------------------- the bot (one fair level)
function Match:botMove(pos)
	local hum = self:humanoid(self.bot)
	if not hum then
		return
	end
	local w = self:toWorld(pos + Vector3.new(0, 3, 0))
	if not self.botTarget or (self.botTarget - w).Magnitude > 0.6 then
		self.botTarget = w
		hum:MoveTo(w)
	end
end

function Match:botPlanFor(side, me)
	local zs = Court.zSign(side)
	local shot = self.shot
	local bounces = BP.bounces(shot)
	local first = bounces[1]
	if first then
		local landsOut
		if self.shotServe then
			landsOut = not Court.inServiceBox(first.p, self.shotSide, self.serverX, 0)
		else
			landsOut = not Court.inCourt(first.p, side, 0)
		end
		if landsOut and rand:NextNumber() < 0.88 then
			return { letGo = true }
		end
	end
	-- take it after the bounce, as it drops back to about hip height
	local t0 = first and first.t or shot.t0
	local tHit, ball
	for i = 1, 100 do
		local tt = t0 + i * 0.02
		local p, v = BP.positionAt(shot, tt), BP.velocityAt(shot, tt)
		if bounces[2] and tt >= bounces[2].t then
			break
		end
		if v.Y < 0 and p.Y <= Court.contactPoint(side, Vector3.zero, "Forehand").Y + 0.4 then
			tHit, ball = tt, p
			break
		end
	end
	if not tHit then
		tHit = t0 + 0.4
		ball = BP.positionAt(shot, tHit)
	end
	local stroke = (ball.X - me.X) * zs >= -1 and "Forehand" or "Backhand"
	local contact = Court.contactPoint(side, Vector3.zero, stroke)
	local stand = Vector3.new(ball.X - contact.X, 0, ball.Z - contact.Z)
	return { t = tHit, stand = stand, stroke = stroke }
end

function Match:botStep(t)
	local bot = self.bot
	local hrp = self:root(bot)
	if not hrp then
		return
	end
	local side = bot.side
	local zs = Court.zSign(side)
	local me = self:toCourt(hrp.Position)
	local B = Config.Bot
	if self.phase == "rally" and self.shot and self.shotSide ~= side then
		if self.botShot ~= self.shot then
			self.botShot, self.botPlan, self.botHit = self.shot, nil, false
			self.botPlanAt = t + B.Reaction
		end
		if not self.botPlan and t >= self.botPlanAt then
			self.botPlan = self:botPlanFor(side, me)
		end
		local plan = self.botPlan
		if plan and plan.letGo then
			self:botMove(Vector3.new(me.X, 0, zs * (Config.Court.Length / 2 + 2)))
		elseif plan then
			self:botMove(plan.stand)
			if not self.botHit and t >= plan.t - 0.12 then
				local ball = BP.positionAt(self.shot, t)
				local bounced = self:bouncesBefore(t) > 0
				local stroke = Court.strokeFor(side, me, ball, bounced)
				local d = (ball - Court.contactPoint(side, me, stroke)).Magnitude
				if bounced and (d <= Config.Player.Reach * 0.85 or t >= plan.t + 0.06) then
					self.botHit = true
					if d <= Config.Player.Reach then
						local q = B.QualityMean + rand:NextNumber(-1, 1) * B.QualitySpread - d / Config.Player.Reach * 0.2
						self:returnShot(side, me, ball, stroke, math.clamp(q, 0.15, 1), rand:NextNumber(-0.8, 0.8), rand:NextNumber() < B.ErrorChance)
					else
						self:fire("swing", { side = side, char = bot.character, stroke = stroke })
					end
				end
			end
		end
	elseif self.phase == "rally" and self.shot then
		-- our ball is on its way: recover toward the middle of the baseline
		local x = BP.positionAt(self.shot, t).X * 0.35
		self:botMove(Vector3.new(x, 0, zs * (Config.Court.Length / 2 + 1.5)))
	end
end

return Match
