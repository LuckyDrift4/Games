-- Court rules and geometry in court space (see Config). Shared by server (rules) and clients (prediction, camera).
local Config = require(script.Parent.Config)

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

-- the point on the hitter's body where the racket meets the ball for a stroke (court space)
function Court.contactPoint(side, hitterPos, stroke)
	local f, r = Court.facing(side), Court.rightOf(side)
	local base = Vector3.new(hitterPos.X, 0, hitterPos.Z)
	if stroke == "Backhand" then
		return base - r * 2.6 + f * 0.8 + Vector3.new(0, 2.6, 0)
	elseif stroke == "VolleyForehand" then
		return base + r * 2.2 + f * 1.8 + Vector3.new(0, 4.0, 0)
	elseif stroke == "VolleyBackhand" then
		return base - r * 2.2 + f * 1.8 + Vector3.new(0, 4.0, 0)
	elseif stroke == "Smash" or stroke == "Serve" then
		return base + r * 0.6 + f * 0.6 + Vector3.new(0, 8.2, 0)
	end
	return base + r * 2.8 + f * 0.8 + Vector3.new(0, 2.6, 0)
end

return Court
