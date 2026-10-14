# SunThroughGrates

A Valheim BepInEx plugin that lets sunlight reach crops through iron cage
floors and grates, so you can farm under an iron ceiling.

## How it works

Vanilla `Plant.HaveRoof()` casts one ray 100 m straight up against the
`Default`, `static_solid` and `piece` layers. Any hit counts as a roof, and the
plant stops growing with "No sun". This plugin replaces that check with a
Harmony prefix that casts the same ray but skips colliders belonging to the
ignored prefabs. A cage-floor ceiling lets light through, while a wood or
stone roof above it still blocks it.

The approach (prefix-replace `HaveRoof` with a custom raycast) is the same idea
as kaaremai's [Better plant sky](https://thunderstore.io/c/valheim/p/kaaremai/Better_plant_sky/);
this is an independent implementation.

## Configuration

`BepInEx/config/nickweedon.SunThroughGrates.cfg`:

| Section | Key | Default |
|---------|-----|---------|
| General | Ignored prefabs | `iron_floor_1x1,iron_floor_2x2,iron_grate,iron_wall_1x1,iron_wall_2x2` |

Comma-separated prefab names. `iron_floor_*` are the iron cage floors.

## Installation

Install on the dedicated server **and on every client**. Plant growth is
evaluated by whoever owns the plant's ZDO, which is often a nearby player, not
the server. The config is not synced, so keep the list identical everywhere.

Copy `SunThroughGrates.dll` into `BepInEx/plugins/`.

## Building

Needs the .NET 8 SDK. Point `VALHEIM_INSTALL` at a folder laid out like a
Valheim install (`BepInEx/core/` and `valheim_Data/Managed/`; a dedicated
server's `valheim_server_Data/Managed` works when copied there):

```bash
VALHEIM_INSTALL=/path/to/valheim dotnet build SunThroughGrates/SunThroughGrates.csproj -c Release
```

Output: `SunThroughGrates/bin/Release/SunThroughGrates.dll`.

Built against Valheim l-1.0.17 and BepInExPack 5.4.2351.
