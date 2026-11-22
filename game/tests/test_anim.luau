-- The baked animations load and sample, and the court helpers agree with them.
local H = require("./harness")
local roblox = require("@lune/roblox")
local Vector3 = roblox.Vector3
local RA = H.load(H.SHARED, "RigAnimator")
local Court = H.load(H.SHARED, "Court")
local Config = H.load(H.SHARED, "Config")
local AnimData = H.load(H.SHARED, "AnimData")
local check = H.check

for name, clip in pairs(RA.Clips) do
	check(#clip.keys >= 10, name .. " has baked frames")
	for _, j in ipairs(AnimData.Joints) do
		local a = RA.Sample(clip, 0, j)
		local b = RA.Sample(clip, clip.length * 0.37, j)
		check(a ~= nil and b ~= nil, name .. " samples " .. j)
	end
	if clip.loop then
		local a = RA.Sample(clip, 0, "RS")
		local b = RA.Sample(clip, clip.length - 1e-4, "RS")
		check((a.Position - b.Position).Magnitude < 0.05 and a.LookVector:Dot(b.LookVector) > 0.98, name .. " loops smoothly")
	end
end
-- forehand contact is out to the right and in front, at about waist height
local fh = Court.contactPoint(1, Vector3.new(0, 0, 40), "Forehand")
check(fh.X > 2.5 and fh.Z < 40 and fh.Y > 1.5 and fh.Y < 3.5, "forehand contact point " .. tostring(fh))
local bh = Court.contactPoint(1, Vector3.new(0, 0, 40), "Backhand")
check(bh.X < -1.5, "backhand on the left " .. tostring(bh))
-- side 2 is mirrored: its right is -X and it faces +Z
local fh2 = Court.contactPoint(2, Vector3.new(0, 0, -40), "Forehand")
check(fh2.X < -2.5 and fh2.Z > -40, "side 2 forehand mirrored " .. tostring(fh2))
-- the serve toss reaches the serve contact point when the animation hits it
local from, v, T = Court.serveToss(1, Vector3.new(4, 0, 40))
local g = Config.Ball.Gravity
local at = from + v * T - Vector3.new(0, 0.5 * g * T * T, 0)
local want = Court.contactPoint(1, Vector3.new(4, 0, 40), "Serve")
check((at - want).Magnitude < 0.01, "toss meets the racket " .. tostring(at) .. " vs " .. tostring(want))
check(want.Y > 6.5, "serve contact is high " .. tostring(want))
check(math.abs(T - Config.Serve.TossPeakTime) < 1e-6, "toss time matches config")
H.done()
