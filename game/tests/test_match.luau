-- Shot planning in Match: good hits clear the net and land in; serves land in the right box.
local H = require("./harness")
local fs = require("@lune/fs")
local luau = require("@lune/luau")
local roblox = require("@lune/roblox")
local Vector3 = roblox.Vector3
local check = H.check

local BP = H.load(H.SHARED, "BallPhysics")
local Court = H.load(H.SHARED, "Court")
local Config = H.load(H.SHARED, "Config")

-- load Match.lua with fake Roblox services; `require(T.X)` resolves to the shared modules
local T = setmetatable({}, { __index = function(_, k) return k end })
local fakeGame = {
	GetService = function(_, name)
		if name == "ReplicatedStorage" then
			return { Tennis = T }
		end
		return {}
	end,
}
local src = fs.readFile(H.SERVER .. "Match.lua")
local Match = luau.load(src, {
	debugName = "Match",
	environment = {
		game = fakeGame,
		require = function(name)
			return H.load(H.SHARED, name)
		end,
		Vector3 = Vector3,
		CFrame = roblox.CFrame,
		Random = { new = function() return { NextNumber = function(_, a, b) a = a or 0; b = b or 1; return a + math.random() * (b - a) end,
			NextInteger = function(_, a, b) return math.random(a, b) end } end },
		workspace = { GetServerTimeNow = function() return 0 end },
	},
	injectGlobals = true,
})()

local function fakeMatch()
	local m = setmetatable({}, Match)
	m.launched = nil
	m.serverX = 4.5
	m.faults = 0
	m.players = { { side = 1 }, { side = 2 } }
	m.launch = function(self, side, from, target, flight, spin, stroke, isServe, noClear)
		local landing = Vector3.new(target.X, Config.Ball.Radius, target.Z)
		local v = BP.solve(from, landing, flight, spin, noClear and -1e9 or (isServe and 0.25 or 0.6))
		self.launched = BP.make(from, v, 0, spin)
		self.noClear = noClear
	end
	return m
end

local function outcome(shot, hitterSide)
	local tn, yn, xn = BP.netCrossing(shot)
	if not tn or yn < BP.netHeight(xn) + Config.Ball.Radius * 0.5 then
		return "net"
	end
	local b = BP.bounces(shot)[1]
	if not b then
		return "none"
	end
	return Court.inCourt(b.p, Court.other(hitterSide)) and "in" or "out"
end

math.randomseed(3)
for _, side in ipairs({ 1, 2 }) do
	local zs = Court.zSign(side)
	for _, stroke in ipairs({ "Forehand", "Backhand", "VolleyForehand", "Smash" }) do
		local good, total = 0, 0
		for i = 1, 200 do
			local m = fakeMatch()
			local deep = (stroke == "Forehand" or stroke == "Backhand") and 40 or 14
			local me = Vector3.new(math.random() * 16 - 8, 3, zs * deep)
			local ball = Court.contactPoint(side, me, stroke)
			m:returnShot(side, me, ball, stroke, 0.75 + math.random() * 0.25, math.random() * 2 - 1, false)
			total += 1
			if outcome(m.launched, side) == "in" then
				good += 1
			end
		end
		check(good / total > 0.85, string.format("side %d %s good hits land in: %d/%d", side, stroke, good, total))
	end
	-- forced errors really are errors
	local errs = 0
	for i = 1, 100 do
		local m = fakeMatch()
		local me = Vector3.new(0, 3, zs * 40)
		m:returnShot(side, me, Court.contactPoint(side, me, "Forehand"), "Forehand", 0.6, 0, true)
		if outcome(m.launched, side) ~= "in" then
			errs += 1
		end
	end
	check(errs >= 95, string.format("side %d forced errors miss: %d/100", side, errs))
end
H.done()
