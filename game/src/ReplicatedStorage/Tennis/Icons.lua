-- Icons from the FOLK icon pack. Roblox can only show uploaded images, so the place has a folder
-- ReplicatedStorage.TennisIcons with one ImageLabel per icon (Cash, Shop, Trophy ...). In Studio, click each one and
-- set its Image to the matching picture from the TennisIcons folder (each ImageLabel's "File" attribute names it).
-- Until an icon is set, the HUD draws its own simple shape instead, so the game always works.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Icons = {}

Icons.List = {
	{ Name = "Cash", File = "Cash.png" },
	{ Name = "CashBundle", File = "CashBundle.png" },
	{ Name = "Shop", File = "Shop.png" },
	{ Name = "Trophy", File = "Trophy.png" },
	{ Name = "Crown", File = "Crown.png" },
	{ Name = "Close", File = "Close.png" },
	{ Name = "Back", File = "Back.png" },
	{ Name = "KeySpace", File = "KeySpace.png" },
	{ Name = "KeyX", File = "KeyX.png" },
}

-- the uploaded image for an icon, or nil when it has not been set yet
function Icons.get(name)
	local folder = ReplicatedStorage:FindFirstChild("TennisIcons")
	local i = folder and folder:FindFirstChild(name)
	if not i then
		return nil
	end
	local id
	if i:IsA("ImageLabel") or i:IsA("ImageButton") then
		id = i.Image
	elseif i:IsA("Decal") or i:IsA("Texture") then
		id = i.Texture
	elseif i:IsA("StringValue") then
		id = i.Value
	end
	if id and id ~= "" then
		return id
	end
	return nil
end

return Icons
