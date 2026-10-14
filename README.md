# SunThroughGrates

Let sunlight through iron cage floors and grates, so you can farm under an
iron ceiling.

In vanilla Valheim, crops won't grow under anything you've built ("No sun"),
even see-through iron cage floors. With this mod, iron cage floors, walls and
grates let the sun through. Wood, stone and every other roof still block it as
usual.

## Installation

Install with [r2modman](https://thunderstore.io/c/valheim/p/ebkr/r2modman/) or
another Thunderstore mod manager, or copy `SunThroughGrates.dll` into
`BepInEx/plugins/`.

**Install it on every client, and on the dedicated server if you use one.**
Plant growth is calculated by whoever owns the plant, which is usually the
nearest player rather than the server. A player without the mod sees
"No sun" under the grate.

## Configuration

`BepInEx/config/nickweedon.SunThroughGrates.cfg`:

| Section | Key | Default | Description |
|---------|-----|---------|-------------|
| General | Ignored prefabs | `iron_floor_1x1,iron_floor_2x2,iron_grate,iron_wall_1x1,iron_wall_2x2` | Comma-separated prefab names that let sunlight through |

You can add other building pieces by prefab name. Changes apply live, for
example from the in-game Configuration Manager. The config isn't synced
between server and clients, so keep the list the same for everyone.

## How it works

Vanilla `Plant.HaveRoof()` casts one ray 100 m straight up against the
`Default`, `static_solid` and `piece` layers. Any hit counts as a roof. This
mod replaces that check with a Harmony prefix that casts the same ray but
skips colliders that belong to an ignored prefab. With an empty list, it
behaves exactly like vanilla.

The idea of replacing `HaveRoof` with a custom raycast comes from kaaremai's
[Better plant sky](https://thunderstore.io/c/valheim/p/kaaremai/Better_plant_sky/).
This is an independent implementation. The two mods patch the same method,
so don't install both.

## Compatibility

- Built against Valheim 1.0.17 and BepInExPack 5.4.2351.
- Conflicts with any other mod that replaces `Plant.HaveRoof`, such as
  Better plant sky.

## Building from source

Requires the .NET 8 SDK. `VALHEIM_INSTALL` must point at a folder laid out like
a Valheim install, containing `BepInEx/core/` and `valheim_Data/Managed/`:

```bash
VALHEIM_INSTALL=/path/to/Valheim \
  dotnet build SunThroughGrates/SunThroughGrates.csproj -c Release
```

Output: `SunThroughGrates/bin/Release/SunThroughGrates.dll`. To build the
Thunderstore package, see [CONTRIBUTING.md](https://github.com/redwyvern/SunThroughGrates/blob/main/CONTRIBUTING.md#releasing).

## Links

- Source and issues: <https://github.com/redwyvern/SunThroughGrates>
- Contributing: [CONTRIBUTING.md](https://github.com/redwyvern/SunThroughGrates/blob/main/CONTRIBUTING.md)
- Changelog: [CHANGELOG.md](https://github.com/redwyvern/SunThroughGrates/blob/main/CHANGELOG.md)
- License: MIT
