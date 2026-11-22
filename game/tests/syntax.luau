-- compile every Luau file in game/src (syntax check)
local fs = require("@lune/fs")
local luau = require("@lune/luau")
local n, bad = 0, 0
local function walk(dir)
	for _, name in ipairs(fs.readDir(dir)) do
		local p = dir .. "/" .. name
		if fs.isDir(p) then
			walk(p)
		elseif name:match("%.lua$") or name:match("%.luau$") then
			n += 1
			local ok, err = pcall(luau.compile, fs.readFile(p))
			if not ok then
				bad += 1
				print("SYNTAX " .. p .. ": " .. tostring(err))
			end
		end
	end
end
walk("../src")
print(string.format("SYNTAX %d files, %d bad", n, bad))
if bad > 0 then
	error("syntax errors")
end
