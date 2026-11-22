-- Loads the game's ModuleScripts outside Roblox (Lune): `require(script.Parent.X)` -> the file X.lua next to it.
local fs = require("@lune/fs")
local luau = require("@lune/luau")
local roblox = require("@lune/roblox")

local H = {}
local cache = {}
local function load(dir, name)
	local key = dir .. name
	if cache[key] then
		return cache[key]
	end
	local src = fs.readFile(dir .. name .. ".lua")
	src = src:gsub("require%(script%.Parent%.(%w+)%)", function(m)
		return '__req("' .. m .. '")'
	end)
	local env = {
		__req = function(m)
			return load(dir, m)
		end,
		Vector3 = roblox.Vector3,
		CFrame = roblox.CFrame,
		Color3 = roblox.Color3,
	}
	local chunk = luau.load(src, { debugName = name, environment = env, injectGlobals = true })
	cache[key] = chunk()
	return cache[key]
end
H.load = load
H.SHARED = "../src/ReplicatedStorage/Tennis/"
H.SERVER = "../src/ServerScriptService/TennisServer/"

local fails, passes = 0, 0
function H.check(cond, msg)
	if cond then
		passes += 1
	else
		fails += 1
		print("FAIL: " .. msg)
	end
end
function H.done()
	print(string.format("TESTS %d passed, %d failed", passes, fails))
	if fails > 0 then
		error("tests failed")
	end
end
return H
