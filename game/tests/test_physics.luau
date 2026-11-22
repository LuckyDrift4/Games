local H = require("./harness")
local roblox = require("@lune/roblox")
local Vector3 = roblox.Vector3
local Config = H.load(H.SHARED, "Config")
local BP = H.load(H.SHARED, "BallPhysics")
local Court = H.load(H.SHARED, "Court")
local r = Config.Ball.Radius

-- 1. a first serve from the deuce side of side 1 into the diagonal box on side 2
local from = Vector3.new(4.5, 10.5, 40.2)
local target = Vector3.new(-6, r, -15)
local v, T = BP.solve(from, target, 0.9, 0.2)
local shot = BP.make(from, v, 100, 0.2)
local b = BP.bounces(shot)
H.check(#b >= 2, "serve bounces at least twice")
H.check((b[1].p - target).Magnitude < 0.05, "serve lands on its target (" .. tostring(b[1].p) .. ")")
H.check(math.abs(b[1].t - (100 + T)) < 1e-3, "serve flight time matches T")
local tn, yn = BP.netCrossing(shot)
H.check(tn ~= nil and yn > BP.netHeight(0) + r, "serve clears the net (y = " .. tostring(yn) .. ")")
H.check(Court.inServiceBox(b[1].p, 1, from.X), "serve is in the diagonal service box")
H.check(not Court.inServiceBox(Vector3.new(6, r, -15), 1, from.X), "wrong box is out")

-- 2. positions are continuous across every bounce
for i, bb in ipairs(b) do
	local before = BP.positionAt(shot, bb.t - 1e-4)
	local after = BP.positionAt(shot, bb.t + 1e-4)
	H.check((before - after).Magnitude < 0.02, "continuous at bounce " .. i)
	H.check(math.abs(bb.p.Y - r) < 1e-6, "bounce " .. i .. " on the court surface")
end

-- 3. a low drive into the net is detected
local low = BP.make(Vector3.new(0, 2.5, 30), Vector3.new(0, 0.5, -90), 0, 0)
local t2, y2 = BP.netCrossing(low)
H.check(t2 ~= nil and y2 < BP.netHeight(0), "low ball hits the net (y = " .. tostring(y2) .. ")")

-- 4. solve() raises the arc until the ball clears the net
local v3 = BP.solve(Vector3.new(2, 2.4, 30), Vector3.new(-3, r, -8), 0.5, 0.5)
local s3 = BP.make(Vector3.new(2, 2.4, 30), v3, 0, 0.5)
local _, y3 = BP.netCrossing(s3)
H.check(y3 and y3 > BP.netHeight(0) + r, "solve lifts a short low shot over the net")

-- 5. pack / unpack round trip
local again = BP.unpack(BP.pack(shot))
H.check((BP.positionAt(again, 100.37) - BP.positionAt(shot, 100.37)).Magnitude < 1e-6, "pack/unpack is exact")

-- 6. court rules are mirror-symmetric between the sides
for _, side in ipairs({ 1, 2 }) do
	local zs = Court.zSign(side)
	H.check(Court.inCourt(Vector3.new(0, r, zs * 20), side), "mid court is in (side " .. side .. ")")
	H.check(not Court.inCourt(Vector3.new(0, r, zs * 41), side), "behind baseline is out (side " .. side .. ")")
	H.check(not Court.inCourt(Vector3.new(16, r, zs * 20), side), "doubles alley is out in singles (side " .. side .. ")")
	for _, deuce in ipairs({ true, false }) do
		local s = Court.startSpot(side, "server", deuce)
		local rcv = Court.startSpot(Court.other(side), "receiver", deuce)
		-- the receiver stands diagonally across from the server and inside the box the serve must land in
		H.check(Court.inServiceBox(Vector3.new(rcv.X * 0.8, r, -zs * 15), side, s.X), "receiver box is the target box")
		H.check(s.X * rcv.X < 0, "server and receiver are diagonal")
	end
	local hp = Vector3.new(0, 0, zs * 36)
	H.check(Court.strokeFor(side, hp, Vector3.new(zs * 2.5, 2.5, zs * 35), true) == "Forehand", "ball on the right = forehand")
	H.check(Court.strokeFor(side, hp, Vector3.new(-zs * 2.5, 2.5, zs * 35), true) == "Backhand", "ball on the left = backhand")
	H.check(Court.strokeFor(side, Vector3.new(0, 0, zs * 8), Vector3.new(zs * 2, 4, zs * 7), false) == "VolleyForehand", "net ball = volley")
	H.check(Court.strokeFor(side, hp, Vector3.new(0, 9, zs * 34), false) == "Smash", "high ball = smash")
end
H.done()
