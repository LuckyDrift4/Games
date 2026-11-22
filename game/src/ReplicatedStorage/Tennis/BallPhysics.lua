-- Ball flight in court space, worked out exactly (no physics engine): a shot is a list of parabola segments split at
-- each bounce. The server and every client compute the same positions from the same shot table, so the ball looks
-- smooth everywhere and the server decides points from the same numbers.
local Config = require(script.Parent.Config)

local BallPhysics = {}

local B = Config.Ball

local function gravityFor(spin)
	-- topspin dips the ball, backspin floats it
	return B.Gravity * (1 + 0.22 * (spin or 0))
end
BallPhysics.gravityFor = gravityFor

-- build a shot: p0 / v0 are Vector3 in court space, t0 = workspace:GetServerTimeNow() at p0
function BallPhysics.build(p0, v0, t0, spin)
	spin = spin or 0
	local g = gravityFor(spin)
	local r = B.Radius
	local segs = {}
	local p, v, t = p0, v0, t0
	for i = 1, B.MaxBounces + 1 do
		segs[i] = { t = t, p = p, v = v, g = g }
		if i > B.MaxBounces then
			break
		end
		-- solve p.Y + v.Y*dt - g/2*dt^2 = r for the later root
		local a, b, c = -0.5 * g, v.Y, p.Y - r
		local disc = b * b - 4 * a * c
		if disc < 0 then
			break
		end
		local dt = (-b - math.sqrt(disc)) / (2 * a)
		if dt <= 1e-4 then
			dt = (-b + math.sqrt(disc)) / (2 * a)
		end
		if dt <= 1e-4 then
			break
		end
		local hit = Vector3.new(p.X + v.X * dt, r, p.Z + v.Z * dt)
		local vy = -(v.Y - g * dt) * B.Restitution * (1 - 0.08 * spin)
		local keep = B.Friction * (1 + 0.1 * spin)
		v = Vector3.new(v.X * keep, vy, v.Z * keep)
		p, t = hit, t + dt
		g = B.Gravity -- spin is mostly used up by the first bounce
		spin = 0
		if vy < 1.2 then
			-- dead ball: it rolls
			segs[i + 1] = { t = t, p = p, v = Vector3.new(v.X, 0, v.Z), g = 0, rolling = true }
			break
		end
	end
	return { t0 = t0, p0 = p0, v0 = v0, spin = spin, segs = segs }
end

local function segAt(shot, t)
	local segs = shot.segs
	local s = segs[1]
	for i = 2, #segs do
		if segs[i].t <= t then
			s = segs[i]
		else
			break
		end
	end
	return s
end

function BallPhysics.positionAt(shot, t)
	local s = segAt(shot, t)
	local dt = math.max(0, t - s.t)
	if s.rolling then
		local slow = math.exp(-1.5 * dt)
		local d = (1 - slow) / 1.5
		return Vector3.new(s.p.X + s.v.X * d, B.Radius, s.p.Z + s.v.Z * d)
	end
	return Vector3.new(s.p.X + s.v.X * dt, s.p.Y + s.v.Y * dt - 0.5 * s.g * dt * dt, s.p.Z + s.v.Z * dt)
end

function BallPhysics.velocityAt(shot, t)
	local s = segAt(shot, t)
	local dt = math.max(0, t - s.t)
	if s.rolling then
		local slow = math.exp(-1.5 * dt)
		return Vector3.new(s.v.X * slow, 0, s.v.Z * slow)
	end
	return Vector3.new(s.v.X, s.v.Y - s.g * dt, s.v.Z)
end

-- bounce points: { {t = time, p = Vector3}, ... }
function BallPhysics.bounces(shot)
	local out = {}
	for i = 2, #shot.segs do
		local s = shot.segs[i]
		out[#out + 1] = { t = s.t, p = s.p }
	end
	return out
end

function BallPhysics.netHeight(x)
	local C = Config.Court
	local k = math.clamp(math.abs(x) / C.PostX, 0, 1)
	return C.NetCenter + (C.NetPost - C.NetCenter) * k
end

-- first time the ball crosses z = 0 (the net plane) and its height there; nil if it never does before landing
function BallPhysics.netCrossing(shot)
	local s = shot.segs[1]
	if math.abs(s.v.Z) < 1e-3 then
		return nil
	end
	local dt = -s.p.Z / s.v.Z
	if dt <= 0 then
		return nil -- moving away from the net
	end
	local land = shot.segs[2]
	if land and s.t + dt > land.t then
		return nil -- lands on its own side first
	end
	local y = s.p.Y + s.v.Y * dt - 0.5 * s.g * dt * dt
	return s.t + dt, y, s.p.X + s.v.X * dt
end

-- velocity that carries the ball from p0 to land on `target` (court surface) after time T, raised until it clears
-- the net with `margin`. Returns v0, T (T may grow so the ball clears the net).
function BallPhysics.solve(p0, target, T, spin, margin)
	margin = margin or 0.6
	local g = gravityFor(spin)
	local r = B.Radius
	for _ = 1, 24 do
		local vx = (target.X - p0.X) / T
		local vz = (target.Z - p0.Z) / T
		local vy = (r - p0.Y + 0.5 * g * T * T) / T
		local v = Vector3.new(vx, vy, vz)
		if (p0.Z > 0) == (target.Z > 0) or math.abs(vz) < 1e-3 then
			return v, T
		end
		local dt = -p0.Z / vz
		local y = p0.Y + vy * dt - 0.5 * g * dt * dt
		local x = p0.X + vx * dt
		if y >= BallPhysics.netHeight(x) + r + margin then
			return v, T
		end
		T = T + 0.06
	end
	local vx = (target.X - p0.X) / T
	local vz = (target.Z - p0.Z) / T
	return Vector3.new(vx, (r - p0.Y + 0.5 * g * T * T) / T, vz), T
end

-- a shot as plain numbers (for RemoteEvents)
function BallPhysics.pack(shot)
	return {
		p = { shot.p0.X, shot.p0.Y, shot.p0.Z },
		v = { shot.v0.X, shot.v0.Y, shot.v0.Z },
		t = shot.t0,
		s = shot.spinIn or 0,
	}
end

function BallPhysics.unpack(d)
	local shot = BallPhysics.build(Vector3.new(d.p[1], d.p[2], d.p[3]), Vector3.new(d.v[1], d.v[2], d.v[3]), d.t, d.s)
	shot.spinIn = d.s
	return shot
end

function BallPhysics.make(p0, v0, t0, spin)
	local shot = BallPhysics.build(p0, v0, t0, spin)
	shot.spinIn = spin or 0
	return shot
end

return BallPhysics
