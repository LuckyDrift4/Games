-- The tennis HUD: big colourful buttons that work with touch, mouse and gamepad. HIT button, scoreboard, banners,
-- serve timing meter, coins, the racket shop and the end-of-match card.
local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local GuiService = game:GetService("GuiService")

local Config = require(ReplicatedStorage:WaitForChild("Tennis"):WaitForChild("Config"))

local UI = {}
local player = Players.LocalPlayer

local FONT = Enum.Font.GothamBlack
local WHITE = Color3.new(1, 1, 1)
local YELLOW = Color3.fromRGB(255, 214, 51)
local GREEN = Color3.fromRGB(76, 217, 100)
local BLUE = Color3.fromRGB(56, 140, 255)
local PINK = Color3.fromRGB(255, 82, 160)
local RED = Color3.fromRGB(255, 76, 76)
local NAVY = Color3.fromRGB(16, 26, 58)

local function corner(o, r)
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(0, r or 14)
	c.Parent = o
	return c
end

local function stroke(o, t, color)
	local s = Instance.new("UIStroke")
	s.Thickness = t or 3
	s.Color = color or Color3.fromRGB(0, 0, 0)
	s.Transparency = 0.15
	s.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	s.Parent = o
	return s
end

local function gradient(o, a, b)
	local g = Instance.new("UIGradient")
	g.Color = ColorSequence.new(a, b)
	g.Rotation = 90
	g.Parent = o
	return g
end

local function label(parent, text, size, pos, color, anchor)
	local l = Instance.new("TextLabel")
	l.BackgroundTransparency = 1
	l.Font = FONT
	l.TextScaled = true
	l.Text = text
	l.TextColor3 = color or WHITE
	l.Size = size
	l.Position = pos or UDim2.new()
	l.AnchorPoint = anchor or Vector2.zero
	l.Parent = parent
	local s = Instance.new("UIStroke")
	s.Thickness = 2
	s.Transparency = 0.3
	s.Parent = l
	return l
end

-- a big chunky button: colour, darker bottom edge, bounces when pressed
local function button(parent, text, color, size, pos, anchor)
	local b = Instance.new("TextButton")
	b.AutoButtonColor = false
	b.Size = size
	b.Position = pos
	b.AnchorPoint = anchor or Vector2.zero
	b.BackgroundColor3 = color
	b.Text = ""
	b.Parent = parent
	corner(b, 16)
	stroke(b, 3)
	gradient(b, WHITE, Color3.fromRGB(200, 200, 200))
	local l = label(b, text, UDim2.fromScale(0.86, 0.62), UDim2.fromScale(0.5, 0.5), WHITE, Vector2.new(0.5, 0.5))
	l.Name = "Label"
	local base = size
	local function squash(k)
		TweenService:Create(b, TweenInfo.new(0.08), {
			Size = UDim2.new(base.X.Scale * k, base.X.Offset * k, base.Y.Scale * k, base.Y.Offset * k),
		}):Play()
	end
	b.MouseButton1Down:Connect(function()
		squash(0.92)
	end)
	b.MouseButton1Up:Connect(function()
		squash(1)
	end)
	b.MouseLeave:Connect(function()
		squash(1)
	end)
	return b, l
end

function UI.build()
	local gui = Instance.new("ScreenGui")
	gui.Name = "TennisHUD"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui.Parent = player:WaitForChild("PlayerGui")
	UI.gui = gui

	-- coins + shop (top left, under the Roblox top bar)
	local coins = Instance.new("Frame")
	coins.Size = UDim2.fromOffset(190, 54)
	coins.Position = UDim2.fromOffset(14, 64)
	coins.BackgroundColor3 = NAVY
	coins.BackgroundTransparency = 0.15
	coins.Parent = gui
	corner(coins, 14)
	stroke(coins, 3, YELLOW)
	local coin = Instance.new("Frame")
	coin.Size = UDim2.fromOffset(34, 34)
	coin.Position = UDim2.fromOffset(10, 10)
	coin.BackgroundColor3 = YELLOW
	coin.Parent = coins
	corner(coin, 17)
	stroke(coin, 2, Color3.fromRGB(180, 120, 0))
	UI.coins = label(coins, "0", UDim2.fromOffset(130, 38), UDim2.fromOffset(52, 8), YELLOW)
	UI.coins.TextXAlignment = Enum.TextXAlignment.Left
	UI.shopButton = button(gui, "SHOP", PINK, UDim2.fromOffset(190, 58), UDim2.fromOffset(14, 126))
	UI.shopButton.Name = "ShopButton"

	-- scoreboard (top centre)
	local sb = Instance.new("Frame")
	sb.Name = "Score"
	sb.Size = UDim2.fromOffset(420, 96)
	sb.Position = UDim2.new(0.5, 0, 0, 58)
	sb.AnchorPoint = Vector2.new(0.5, 0)
	sb.BackgroundColor3 = NAVY
	sb.BackgroundTransparency = 0.1
	sb.Visible = false
	sb.Parent = gui
	corner(sb, 16)
	stroke(sb, 3, BLUE)
	UI.score = sb
	UI.rows = {}
	for i = 1, 2 do
		local y = 6 + (i - 1) * 44
		local serveDot = Instance.new("Frame")
		serveDot.Size = UDim2.fromOffset(14, 14)
		serveDot.Position = UDim2.fromOffset(12, y + 14)
		serveDot.BackgroundColor3 = Config.Colors.Ball
		serveDot.Parent = sb
		corner(serveDot, 7)
		local name = label(sb, "", UDim2.fromOffset(230, 36), UDim2.fromOffset(34, y + 2), i == 1 and Config.Colors.SideA or Config.Colors.SideB)
		name.TextXAlignment = Enum.TextXAlignment.Left
		local games = label(sb, "0", UDim2.fromOffset(60, 36), UDim2.fromOffset(276, y + 2), WHITE)
		local pts = label(sb, "0", UDim2.fromOffset(64, 36), UDim2.fromOffset(344, y + 2), YELLOW)
		UI.rows[i] = { dot = serveDot, name = name, games = games, points = pts }
	end

	-- banner + countdown
	UI.banner = label(gui, "", UDim2.new(0.8, 0, 0, 90), UDim2.fromScale(0.5, 0.3), YELLOW, Vector2.new(0.5, 0.5))
	UI.banner.Visible = false
	UI.sub = label(gui, "", UDim2.new(0.6, 0, 0, 40), UDim2.new(0.5, 0, 0.3, 62), WHITE, Vector2.new(0.5, 0.5))
	UI.sub.Visible = false
	UI.hint = label(gui, "", UDim2.new(0.7, 0, 0, 34), UDim2.new(0.5, 0, 1, -150), WHITE, Vector2.new(0.5, 0.5))
	UI.hint.Visible = false

	-- HIT button (bottom right) - big for thumbs
	local hit, hitLabel = button(gui, "HIT", GREEN, UDim2.fromOffset(150, 150), UDim2.new(1, -36, 1, -46), Vector2.new(1, 1))
	hit.Name = "HitButton"
	corner(hit, 75)
	UI.hit = hit
	UI.hitLabel = hitLabel
	local key = label(hit, "SPACE", UDim2.fromOffset(110, 22), UDim2.new(0.5, 0, 1, 10), WHITE, Vector2.new(0.5, 0))
	UI.hitKey = key
	hit.Visible = false

	-- serve timing meter
	local meter = Instance.new("Frame")
	meter.Name = "ServeMeter"
	meter.Size = UDim2.fromOffset(340, 30)
	meter.Position = UDim2.new(0.5, 0, 1, -100)
	meter.AnchorPoint = Vector2.new(0.5, 0.5)
	meter.BackgroundColor3 = NAVY
	meter.Visible = false
	meter.Parent = gui
	corner(meter, 15)
	stroke(meter, 3)
	local good = Instance.new("Frame")
	good.BackgroundColor3 = YELLOW
	good.BorderSizePixel = 0
	good.Parent = meter
	local perfect = Instance.new("Frame")
	perfect.BackgroundColor3 = GREEN
	perfect.BorderSizePixel = 0
	perfect.Parent = meter
	local needle = Instance.new("Frame")
	needle.Size = UDim2.new(0, 6, 1, 10)
	needle.AnchorPoint = Vector2.new(0.5, 0.5)
	needle.Position = UDim2.fromScale(0, 0.5)
	needle.BackgroundColor3 = WHITE
	needle.Parent = meter
	corner(needle, 3)
	UI.meter = { frame = meter, good = good, perfect = perfect, needle = needle }

	-- leave match
	UI.leave = button(gui, "LEAVE", RED, UDim2.fromOffset(120, 44), UDim2.new(1, -14, 0, 64), Vector2.new(1, 0))
	UI.leave.Visible = false

	UI.buildShop()
	UI.buildResult()
	UI.watchData()
	UI.setInputHint("keyboard")
	return UI
end

function UI.setInputHint(kind)
	UI.inputKind = kind
	if not UI.hitKey then
		return
	end
	UI.hitKey.Text = kind == "gamepad" and "R2 / X" or (kind == "touch" and "" or "SPACE / CLICK")
	UI.hitKey.Visible = kind ~= "touch"
end

function UI.setScore(s, mySide)
	UI.score.Visible = true
	for i = 1, 2 do
		local r = UI.rows[i]
		r.name.Text = (s.names[i] or "") .. (mySide == i and "  (YOU)" or "")
		r.games.Text = tostring(s.games[i])
		r.points.Text = tostring(s.points[i])
		r.dot.Visible = s.serverSide == i
	end
end

function UI.hideScore()
	UI.score.Visible = false
end

local bannerToken
function UI.flash(text, color, sub, duration)
	local token = {}
	bannerToken = token
	local b = UI.banner
	b.Text = text
	b.TextColor3 = color or YELLOW
	b.Visible = true
	b.Size = UDim2.new(0.5, 0, 0, 50)
	TweenService:Create(b, TweenInfo.new(0.25, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {
		Size = UDim2.new(0.8, 0, 0, 90),
	}):Play()
	UI.sub.Text = sub or ""
	UI.sub.Visible = sub ~= nil
	task.delay(duration or 1.4, function()
		if bannerToken == token then
			b.Visible = false
			UI.sub.Visible = false
		end
	end)
end

function UI.setHint(text)
	UI.hint.Text = text or ""
	UI.hint.Visible = text ~= nil and text ~= ""
end

function UI.showMatch(on)
	UI.hit.Visible = on
	UI.leave.Visible = on
	if not on then
		UI.hideScore()
		UI.meter.frame.Visible = false
		UI.setHint(nil)
	end
end

-- serve meter: the needle runs over the toss; green = perfect, yellow = good, the rest = fault
function UI.meterShow(flight, span)
	local m = UI.meter
	local S = Config.Serve
	local function x(t)
		return math.clamp(t / span, 0, 1)
	end
	m.good.Position = UDim2.fromScale(x(flight - S.GoodWindow), 0)
	m.good.Size = UDim2.fromScale(x(flight + S.GoodWindow) - x(flight - S.GoodWindow), 1)
	m.perfect.Position = UDim2.fromScale(x(flight - S.PerfectWindow), 0)
	m.perfect.Size = UDim2.fromScale(x(flight + S.PerfectWindow) - x(flight - S.PerfectWindow), 1)
	m.frame.Visible = true
end

function UI.meterSet(u)
	UI.meter.needle.Position = UDim2.fromScale(math.clamp(u, 0, 1), 0.5)
end

function UI.meterHide()
	UI.meter.frame.Visible = false
end

-- ---------------------------------------------------------------- shop
function UI.buildShop()
	local gui = UI.gui
	local panel = Instance.new("Frame")
	panel.Name = "Shop"
	panel.Size = UDim2.new(0, 560, 0, 400)
	panel.Position = UDim2.fromScale(0.5, 0.5)
	panel.AnchorPoint = Vector2.new(0.5, 0.5)
	panel.BackgroundColor3 = NAVY
	panel.Visible = false
	panel.Parent = gui
	corner(panel, 22)
	stroke(panel, 4, PINK)
	local scale = Instance.new("UIScale")
	scale.Parent = panel
	UI.shopScale = scale
	label(panel, "RACKET SHOP", UDim2.new(0.7, 0, 0, 50), UDim2.new(0.5, 0, 0, 14), PINK, Vector2.new(0.5, 0))
	local close = button(panel, "X", RED, UDim2.fromOffset(54, 54), UDim2.new(1, -12, 0, 12), Vector2.new(1, 0))
	close.MouseButton1Click:Connect(function()
		panel.Visible = false
	end)
	local grid = Instance.new("ScrollingFrame")
	grid.Size = UDim2.new(1, -28, 1, -96)
	grid.Position = UDim2.fromOffset(14, 82)
	grid.BackgroundTransparency = 1
	grid.ScrollBarThickness = 8
	grid.AutomaticCanvasSize = Enum.AutomaticSize.Y
	grid.CanvasSize = UDim2.new()
	grid.Parent = panel
	local layout = Instance.new("UIGridLayout")
	layout.CellSize = UDim2.fromOffset(166, 140)
	layout.CellPadding = UDim2.fromOffset(12, 12)
	layout.Parent = grid
	UI.shopItems = {}
	for i, item in ipairs(Config.Shop) do
		local card = Instance.new("Frame")
		card.LayoutOrder = i
		card.BackgroundColor3 = Color3.fromRGB(28, 42, 86)
		card.Parent = grid
		corner(card, 14)
		stroke(card, 2, Color3.fromRGB(70, 90, 150))
		local swatch = Instance.new("Frame")
		swatch.Size = UDim2.new(1, -20, 0, 40)
		swatch.Position = UDim2.fromOffset(10, 10)
		swatch.BackgroundColor3 = item.Color
		swatch.Parent = card
		corner(swatch, 10)
		if item.Neon then
			gradient(swatch, item.Color, WHITE)
		end
		label(card, item.Name, UDim2.new(1, -16, 0, 26), UDim2.fromOffset(8, 54), WHITE)
		local b, l = button(card, "", GREEN, UDim2.new(1, -20, 0, 42), UDim2.new(0, 10, 1, -50))
		b.MouseButton1Click:Connect(function()
			if UI.onBuy then
				UI.onBuy(item.Id)
			end
		end)
		UI.shopItems[item.Id] = { item = item, button = b, label = l, card = card }
	end
	UI.shop = panel
	UI.shopButton.MouseButton1Click:Connect(function()
		panel.Visible = not panel.Visible
		UI.refreshShop()
	end)
end

function UI.refreshShop()
	local owned = {}
	for id in string.gmatch(player:GetAttribute("Owned") or "Classic", "[^,]+") do
		owned[id] = true
	end
	local equipped = player:GetAttribute("Equipped") or "Classic"
	local coins = player:GetAttribute("Coins") or 0
	for id, s in pairs(UI.shopItems) do
		if equipped == id then
			s.label.Text = "EQUIPPED"
			s.button.BackgroundColor3 = BLUE
		elseif owned[id] then
			s.label.Text = "EQUIP"
			s.button.BackgroundColor3 = GREEN
		else
			s.label.Text = s.item.Price .. " COINS"
			s.button.BackgroundColor3 = coins >= s.item.Price and YELLOW or Color3.fromRGB(110, 110, 120)
		end
	end
	-- fit small screens
	local vp = workspace.CurrentCamera.ViewportSize
	UI.shopScale.Scale = math.min(1, (vp.X - 30) / 560, (vp.Y - 60) / 400)
end

function UI.watchData()
	local function update()
		UI.coins.Text = tostring(player:GetAttribute("Coins") or 0)
		if UI.shop and UI.shop.Visible then
			UI.refreshShop()
		end
	end
	for _, a in ipairs({ "Coins", "Owned", "Equipped" }) do
		player:GetAttributeChangedSignal(a):Connect(update)
	end
	update()
end

-- ---------------------------------------------------------------- end of match card
function UI.buildResult()
	local card = Instance.new("Frame")
	card.Name = "Result"
	card.Size = UDim2.fromOffset(420, 230)
	card.Position = UDim2.fromScale(0.5, 0.5)
	card.AnchorPoint = Vector2.new(0.5, 0.5)
	card.BackgroundColor3 = NAVY
	card.Visible = false
	card.Parent = UI.gui
	corner(card, 22)
	UI.resultStroke = stroke(card, 5, GREEN)
	UI.resultTitle = label(card, "YOU WIN!", UDim2.new(0.9, 0, 0, 70), UDim2.new(0.5, 0, 0, 18), GREEN, Vector2.new(0.5, 0))
	UI.resultScore = label(card, "", UDim2.new(0.8, 0, 0, 34), UDim2.new(0.5, 0, 0, 98), WHITE, Vector2.new(0.5, 0))
	UI.resultCoins = label(card, "", UDim2.new(0.8, 0, 0, 40), UDim2.new(0.5, 0, 0, 148), YELLOW, Vector2.new(0.5, 0))
	UI.result = card
end

function UI.showResult(won, scoreText, coins)
	UI.resultTitle.Text = won and "YOU WIN!" or "YOU LOSE"
	UI.resultTitle.TextColor3 = won and GREEN or RED
	UI.resultStroke.Color = won and GREEN or RED
	UI.resultScore.Text = scoreText
	UI.resultCoins.Text = "+" .. tostring(coins or 0) .. " COINS"
	UI.result.Visible = true
	UI.result.Size = UDim2.fromOffset(200, 110)
	TweenService:Create(UI.result, TweenInfo.new(0.35, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {
		Size = UDim2.fromOffset(420, 230),
	}):Play()
	task.delay(4, function()
		UI.result.Visible = false
	end)
end

UI.colors = { YELLOW = YELLOW, GREEN = GREEN, BLUE = BLUE, PINK = PINK, RED = RED, WHITE = WHITE }
UI.GuiService = GuiService

return UI
