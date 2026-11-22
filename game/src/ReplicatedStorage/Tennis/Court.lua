-- Court rules and geometry in court space (see Config). Shared by server (rules) and clients (prediction, camera).
local Config = require(script.Parent.Config)
local AnimData = require(script.Parent.AnimData)

local Court = {}
local C = Config.Court

-- side 1 plays on +Z, side 2 on -Z
function Court.zSign(side)
	return side == 1 and 1 or -1
end

function Court.other(side)
	return side == 1 and 2 or 1
end

function Court.sideOf(z)
	return z >= 0 and 1 or 2
end

-- the direction a player on `side` looks (toward the net) and their right hand, both in court space
function Court.facing(side)
	return Vector3.new(0, 0, -Court.zSign(side))
end

function Court.rightOf(side)
	return Vector3.new(Court.zSign(side), 0, 0)
end

function Court.baselineZ(side)
	return Court.zSign(side) * C.Length / 2
end

-- did a bounce at court point p land inside the singles court on `side`?
function Court.inCourt(p, side, slack)
	slack = slack or Config.Ball.Radius
	local half = C.SinglesWidth / 2
	local z = p.Z * Court.zSign(side)
	return z >= -slack and z <= C.Length / 2 + slack and math.abs(p.X) <= half + slack
end

-- service box diagonal from a server standing at serverX on serverSide
function Court.inServiceBox(p, serverSide, serverX, slack)
	slack = slack or Config.Ball.Radius
	local recv = Court.other(serverSide)
	local z = p.Z * Court.zSign(recv)
	if z < -slack or z > C.ServiceLine + slack then
		return false
	end
	-- diagonal: the box on the opposite x side from the server
	local want = serverX >= 0 and -1 or 1
	local half = C.SinglesWidth / 2
	return p.X * want >= -slack and math.abs(p.X) <= half + slack
end

-- where a player stands for a point. role = "server" or "receiver"; deuce = even number of points played
function Court.startSpot(side, role, deuce)
	local zs = Court.zSign(side)
	local right = zs -- +x is the player's right on side 1, -x on side 2
	local x = (deuce and 1 or -1) * right
	if role == "server" then
		return Vector3.new(x * 4.5, 0, zs * (C.Length / 2 + 1.2))
	end
	return Vector3.new(x * 8.5, 0, zs * (C.Length / 2 + 2.5)) -- the deuce court is each player's own right half
end

-- the stroke a hitter uses for a ball at court point `ball`, given whether it has bounced
function Court.strokeFor(side, hitterPos, ball, bounced)
	local P = Config.Player
	local relRight = (ball.X - hitterPos.X) * Court.zSign(side)
	if not bounced and ball.Y >= P.SmashHeight then
		return "Smash"
	end
	if not bounced and math.abs(hitterPos.Z) < P.VolleyZone then
		return relRight >= 0 and "VolleyForehand" or "VolleyBackhand"
	end
	return relRight >= -0.4 and "Forehand" or "Backhand"
end

-- the point where the racket meets the ball for a stroke (court space), straight from the animation: AnimData
-- stores it relative to the HumanoidRootPart (x right, y up from the hip centre, z back), and the HRP stands 3 studs
-- above the court facing the net
local CONTACT = {}
for name, clip in pairs(AnimData.Clips) do
	if clip.ContactPoint then
		CONTACT[name] = Vector3.new(table.unpack(clip.ContactPoint))
	end
end
Court.Contact = CONTACT

function Court.contactPoint(side, hitterPos, stroke)
	local c = CONTACT[stroke] or CONTACT.Forehand
	local f, r = Court.facing(side), Court.rightOf(side)
	local base = Vector3.new(hitterPos.X, 0, hitterPos.Z)
	return base + r * c.X + f * -c.Z + Vector3.new(0, 3 + c.Y, 0)
end

-- the serve toss: where the ball leaves the hand (court space) and the velocity that brings it to the racket at
-- the contact moment of the Serve animation
function Court.serveToss(side, serverPos)
	local clip = AnimData.Clips.Serve
	local f, r = Court.facing(side), Court.rightOf(side)
	local base = Vector3.new(serverPos.X, 0, serverPos.Z)
	local function place(p)
		return base + r * p[1] + f * -p[3] + Vector3.new(0, 3 + p[2], 0)
	end
	local from, to = place(clip.TossPoint), place(clip.ContactPoint)
	local T = clip.Contact - clip.Toss
	local g = Config.Ball.Gravity
	local v = (to - from) / T + Vector3.new(0, 0.5 * g * T, 0)
	return from, v, T
end

return Court
