-- Cash, wins and racket colours per player, saved with DataStoreService (falls back to memory in Studio when API
-- access is off). The client reads everything from player attributes: Cash, Wins, Equipped, Owned ("A,B,C").
local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Tennis.Config)

local Data = {}
local store
pcall(function()
	store = DataStoreService:GetDataStore("TennisData_v1")
end)
local profiles = {}

local function default()
	return { Cash = 0, Wins = 0, Owned = { Classic = true }, Equipped = "Classic" }
end

local function shopItem(id)
	for _, item in ipairs(Config.Shop) do
		if item.Id == id then
			return item
		end
	end
	return nil
end
Data.shopItem = shopItem

local function publish(player)
	local p = profiles[player]
	if not p then
		return
	end
	local owned = {}
	for id in pairs(p.Owned) do
		table.insert(owned, id)
	end
	player:SetAttribute("Cash", p.Cash)
	player:SetAttribute("Wins", p.Wins)
	player:SetAttribute("Equipped", p.Equipped)
	player:SetAttribute("Owned", table.concat(owned, ","))
	local ls = player:FindFirstChild("leaderstats")
	if ls then
		ls.Cash.Value = p.Cash
		ls.Wins.Value = p.Wins
	end
end

function Data.load(player)
	local saved
	if store then
		local ok, result = pcall(function()
			return store:GetAsync("u" .. player.UserId)
		end)
		if ok then
			saved = result
		end
	end
	local p = default()
	if type(saved) == "table" then
		p.Cash = tonumber(saved.Cash) or tonumber(saved.Coins) or 0 -- older saves called it Coins
		p.Wins = tonumber(saved.Wins) or 0
		if type(saved.Owned) == "table" then
			for id in pairs(saved.Owned) do
				if shopItem(id) then
					p.Owned[id] = true
				end
			end
		end
		if saved.Equipped and p.Owned[saved.Equipped] then
			p.Equipped = saved.Equipped
		end
	end
	profiles[player] = p
	local ls = Instance.new("Folder")
	ls.Name = "leaderstats"
	local cash = Instance.new("IntValue")
	cash.Name = "Cash"
	cash.Parent = ls
	local wins = Instance.new("IntValue")
	wins.Name = "Wins"
	wins.Parent = ls
	ls.Parent = player
	publish(player)
end

function Data.save(player)
	local p = profiles[player]
	if not (p and store) then
		return
	end
	pcall(function()
		store:SetAsync("u" .. player.UserId, { Cash = p.Cash, Wins = p.Wins, Owned = p.Owned, Equipped = p.Equipped })
	end)
end

function Data.get(player)
	return profiles[player]
end

function Data.addCash(player, n)
	local p = profiles[player]
	if p then
		p.Cash += n
		publish(player)
	end
end

function Data.addWin(player)
	local p = profiles[player]
	if p then
		p.Wins += 1
		publish(player)
	end
end

-- returns ok, message
function Data.buy(player, id)
	local p, item = profiles[player], shopItem(id)
	if not (p and item) then
		return false, "Unknown item"
	end
	if p.Owned[id] then
		p.Equipped = id
		publish(player)
		return true, "Equipped"
	end
	if p.Cash < item.Price then
		return false, "Not enough cash"
	end
	p.Cash -= item.Price
	p.Owned[id] = true
	p.Equipped = id
	publish(player)
	Data.save(player)
	return true, "Bought " .. item.Name
end

function Data.equipped(player)
	local p = profiles[player]
	return shopItem(p and p.Equipped or "Classic") or Config.Shop[1]
end

function Data.remove(player)
	Data.save(player)
	profiles[player] = nil
end

function Data.start()
	Players.PlayerAdded:Connect(Data.load)
	for _, pl in ipairs(Players:GetPlayers()) do
		task.spawn(Data.load, pl)
	end
	Players.PlayerRemoving:Connect(Data.remove)
	game:BindToClose(function()
		for pl in pairs(profiles) do
			Data.save(pl)
		end
	end)
	task.spawn(function()
		while true do
			task.wait(120)
			for pl in pairs(profiles) do
				Data.save(pl)
			end
		end
	end)
end

return Data
