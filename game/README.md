# R6 Tennis

A Roblox tennis game for classic R6 avatars. You can play singles against a Noob Bot or 1v1 against another player in a stadium styled after a big hard-court final (no real brands or logos). Every swing, serve and celebration was made for R6 and previewed in Blender.

**Open it:** `out/tennis_game/TennisR6.rbxl` opens in Roblox Studio, then press Play. To add the Blender-made stadium, follow `out/tennis_stadium_blender/SETUP.md`: import the models, then paste one line in the command bar. Before you publish, check that *Game Settings → Avatar* is set to **R6**. The place file already saves R6, but a published game uses its own setting.

## How to play

| | PC | Phone | Controller |
|---|---|---|---|
| Move | WASD | joystick | left stick |
| Hit / serve | Space or click, or the HIT button | HIT button | R2 / X / A |

- **Start a match:** stand on a pad. The yellow pad (*PLAY VS BOT*) starts a match against the Noob Bot. The blue and orange pads (*1v1*) need one player on each.
- **Serving:** press HIT to toss the ball, then press it again when the ball reaches the top of the toss. The meter's green zone means a perfect serve and yellow means a good one. Anything else is a fault, and two faults lose the point.
- **Rallies:** the game picks the shot for you: forehand or backhand by side, a volley near the net, a smash on high balls. Pressing early pulls the ball cross-court, and a cleaner hit sends it deeper and faster.
- **Scoring:** a game is first to 7 points and a match is first to 3 games.
- **Cash:** $1 per point won, plus $25 for beating the bot ($5 for losing) or $40 for winning a 1v1 ($10 for losing). Spend it in the **SHOP** on racket colours.

## Icons

The HUD uses icons from the FOLK icon pack: cash, shop cart, trophy, crown, close, back, and the SPACE / X keys. A Roblox game can only show uploaded images, so the place has a folder `ReplicatedStorage.TennisIcons` with one ImageLabel per icon. In Studio, click each one, then click its **Image** property and pick the matching file from the `TennisIcons` folder (each label's **File** attribute names it). Until an icon is set, the HUD draws a simple shape instead. The icon images aren't in this repository.

## How it's built

- `anim/`: the animations. `clips.py` poses each move with IK-style controls: where the feet stand, where the hands go, where the racket points, and what the eyes watch. `rig.py` solves those controls onto the six R6 Motor6Ds plus a `RacketGrip` wrist joint and bakes them at 30 fps. `preview_blender.py` renders the real R6 rig with the racket on a court (GIFs and MP4s in `anim/previews/`, plus `TennisR6Animations.blend` with every clip on one timeline). `export.py` writes `AnimData.lua` and the KeyframeSequences.
- `src/ReplicatedStorage/Tennis`: shared code. `Config` holds every number, `BallPhysics` gives exact ball flight split at each bounce, `Court` holds the rules and court geometry, `RigAnimator` plays the clips by writing `Motor6D.Transform` (nothing to upload), and `Rigs` builds the racket and the Noob Bot.
- `src/ServerScriptService/TennisServer`: courts and pads, `Match` (serve, faults, net, in/out, scoring, the bot, rewards) and `Data` (coins, wins and rackets, saved with DataStore).
- `src/StarterPlayer/StarterPlayerScripts/TennisClient`: draws the ball, animates every player on court, runs the TV camera, handles input, and builds the HUD and shop (`UI.lua`).
- `src/ServerStorage/TennisStadiumInstall.lua`: builds the Blender stadium from the imported models (and removes the fallback floors).
- `tools/build_place.luau`: assembles the place (game parts from `maps/tennis_gameplay.py`, scripts, lighting, the R6 setting, the icon slots, plus an animation rig with KeyframeSequences in ServerStorage for the Animation Editor).
- `tests/`: Luau tests run with [Lune](https://github.com/lune-org/lune): `lune run test_physics.luau`, `lune run test_anim.luau`, `lune run syntax.luau`.

Rebuild everything:

```
python3 game/anim/export.py                       # animations -> AnimData.lua + build/anims.json
python3 tools/build.py tennis_gameplay            # game parts + fallback floors -> out/tennis_gameplay
cd game/tools && lune run build_place.luau        # -> out/tennis_game/TennisR6.rbxl
python game/anim/preview_blender.py               # Blender previews (needs the bpy module)
```

The ball rules, animation data and place file are tested outside Roblox. Matches haven't been played in Studio yet, so try a game against the bot first.
