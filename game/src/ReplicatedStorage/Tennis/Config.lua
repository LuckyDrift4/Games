-- Tennis config: every number the game uses, in one place. Units are studs and seconds.
-- Court space: origin at the centre of the net on the court surface, +Y up, the court runs along Z.
-- Side 1 is the +Z half (south), side 2 the -Z half (north). Each player faces the net.

local Config = {}

Config.Court = {
	Length = 78, -- baseline to baseline
	Width = 36, -- doubles width (the blue area)
	SinglesWidth = 27, -- singles lines: the ball must land inside these
	ServiceLine = 21, -- distance from the net
	NetCenter = 3.0, -- net height in the middle
	NetPost = 3.5, -- net height at the posts
	PostX = 21, -- net posts stand outside the doubles lines
	RunBack = 21, -- run-off behind each baseline
	RunSide = 15, -- run-off beside the doubles lines
}

Config.Ball = {
	Radius = 0.35, -- shown a bit bigger than real so it reads on a phone
	Gravity = 38,
	Restitution = 0.72, -- vertical speed kept after a bounce
	Friction = 0.84, -- horizontal speed kept after a bounce
	MaxBounces = 5,
}

Config.Player = {
	WalkSpeed = 20,
	Reach = 5.6, -- max distance from the hit point to the ball for a hit
	SmashHeight = 7.2, -- a ball above this (not bounced yet) is smashed
	VolleyZone = 22, -- closer than this to the net without a bounce = volley
	HitWindowBack = 0.28, -- lag compensation: look back this far for the ball
	HitWindowAhead = 0.08,
	SwingCooldown = 0.45,
}

Config.Bot = {
	Speed = 19,
	Reaction = 0.2, -- seconds before the bot starts moving to a new ball
	QualityMean = 0.62,
	QualitySpread = 0.18,
	ErrorChance = 0.07, -- unforced errors
	FirstServeFault = 0.12,
	SecondServeFault = 0.04,
	ServeDelay = 1.4,
}

Config.Serve = {
	HandHeight = 4.4,
	TossPeakTime = 0.56, -- matches the Serve animation (toss 0.30 -> contact 0.86)
	TossHeight = 11.2,
	PerfectWindow = 0.07, -- seconds around the top of the toss for a perfect serve
	GoodWindow = 0.2, -- outside this the serve is a fault
	MaxFaults = 2,
	ResetAfter = 1.6, -- re-toss if nobody hits it
}

Config.Scoring = {
	PointsToWinGame = 7,
	GamesToWinMatch = 3,
	PointPause = 2.2,
	StartCountdown = 3,
}

Config.Rewards = {
	WinBot = 25,
	LoseBot = 5,
	Win1v1 = 40,
	Lose1v1 = 10,
	PointWon = 1,
}

-- racket colours for the shop (Classic is free)
Config.Shop = {
	{ Id = "Classic", Name = "Classic Blue", Price = 0, Color = Color3.fromRGB(22, 88, 214) },
	{ Id = "Volt", Name = "Volt", Price = 100, Color = Color3.fromRGB(212, 240, 40) },
	{ Id = "Pink", Name = "Hot Pink", Price = 150, Color = Color3.fromRGB(255, 70, 160) },
	{ Id = "Fire", Name = "Fire Red", Price = 200, Color = Color3.fromRGB(230, 40, 40) },
	{ Id = "Mint", Name = "Mint", Price = 300, Color = Color3.fromRGB(60, 220, 170) },
	{ Id = "Gold", Name = "Gold", Price = 500, Color = Color3.fromRGB(245, 190, 40) },
	{ Id = "Void", Name = "Void Purple", Price = 750, Color = Color3.fromRGB(130, 60, 240), Neon = true },
}

Config.Colors = {
	Ball = Color3.fromRGB(214, 240, 60),
	SideA = Color3.fromRGB(70, 150, 255),
	SideB = Color3.fromRGB(255, 120, 70),
}

return Config
