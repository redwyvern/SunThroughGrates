# Contributing

Thanks for helping out! Bug reports, fixes and small features are all welcome.

## Reporting bugs

Open an issue with:

- your Valheim and BepInExPack versions, and the SunThroughGrates version
- whether it's single-player, a hosted game or a dedicated server, and which
  side has the mod installed
- what you expected and what happened (for example, which piece is overhead
  and what the crop's hover text says)
- the relevant part of `BepInEx/LogOutput.log`, if there's an error
- your other mods, especially any that touch plants, farming or building

## Before you start

For anything bigger than a small fix, open an issue first to agree on the
approach. This mod deliberately does one thing, so features that grow its
scope (new mechanics, extra UI) may be better as a separate mod.

## Pull requests

- **Keep it focused.** One change per PR. No unrelated refactoring or
  reformatting.
- **Match the existing style.** Follow the surrounding code's naming,
  structure and comment density.
- **Test in game.** Build it, load it in Valheim and check the actual
  behaviour (see [Testing](#testing)). Say in the PR description what you
  tested and how.
- **Don't break vanilla behaviour.** With an empty `Ignored prefabs` list, the
  mod must behave exactly like vanilla Valheim.
- **Watch performance.** `Plant.HaveRoof` runs for every plant every few
  seconds. Avoid per-call allocations (use non-alloc physics queries and
  cached data) and expensive lookups.
- **Think about multiplayer.** Plant logic runs on whichever machine owns the
  plant, which is usually a nearby client. Changes have to make sense when
  players and the server have different settings.
- **Add a changelog entry.** Add a line under `## [Unreleased]` in
  [CHANGELOG.md](CHANGELOG.md) for any change players would notice.
- **Don't commit build output or game files.** That includes `bin/`, `obj/`,
  `build/` and Valheim or BepInEx DLLs. Game assemblies can't be
  redistributed.

## Documentation

Document what a player or the next contributor needs to know, and nothing more.

- Update [README.md](README.md) when you change behaviour, config or
  compatibility. Keep it short and practical. It's also the mod's
  Thunderstore page.
- In code, comment *why* something is done when it isn't obvious, such as a
  vanilla quirk or a multiplayer constraint. Don't comment *what* the code
  plainly does.
- Commit messages and PR descriptions: one clear summary line, then a short
  explanation of why if it isn't obvious. No essays.

## AI-assisted contributions

AI-assisted contributions are welcome. Treat them like any other PR: **you**
are responsible for them. Before submitting:

- read and understand every line, and be able to explain it in review
- trim AI verbosity: remove redundant comments, boilerplate and over-long docs
- build it and test it in game yourself. "The AI said it works" isn't testing.
- check that any APIs, method names and game behaviour it relied on actually
  exist in the current Valheim version

You don't have to disclose AI use, but you're welcome to.

## Testing

There are no automated tests, because the behaviour depends on Unity physics in
a running game. A good manual check:

1. Plant crops on cultivated ground under an iron cage floor. Within about 10
   seconds, hovering should show them as healthy, not "No sun".
2. Plant crops under a wood or stone roof. They should still show "No sun".
3. Clear `Ignored prefabs` in the Configuration Manager (F1). The crops under
   the cage floor should switch to "No sun" within about 10 seconds. This
   confirms the vanilla fallback.
4. Check `BepInEx/LogOutput.log` for errors.

## Building

See [Building from source](README.md#building-from-source).

## Releasing

Maintainers only. Versions follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: breaking changes, such as a renamed config key or a removed
  behaviour
- **MINOR**: new features that don't break anything
- **PATCH**: bug fixes, and rebuilds for a new Valheim version

To release:

1. Bump the version in `SunThroughGrates/SunThroughGrates.csproj`,
   `SunThroughGrates/Plugin.cs` (`PluginVersion`) and `thunderstore.toml`.
2. In `CHANGELOG.md`, move the `[Unreleased]` entries under
   `## [X.Y.Z] - YYYY-MM-DD` and update the compare links at the bottom.
3. Commit to `main`, then run:

   ```bash
   tools/release.sh X.Y.Z             # tag + GitHub release
   tools/release.sh X.Y.Z --publish   # ...and publish to Thunderstore
   ```

   The script checks that the versions match and the changelog has an entry.
   It then builds, packages with [tcli](https://github.com/thunderstore-io/thunderstore-cli),
   tags `vX.Y.Z`, creates the GitHub release (zip and DLL attached, notes from
   the changelog), and with `--publish` uploads to Thunderstore. Publishing
   needs `TCLI_AUTH_TOKEN` set to a Thunderstore service-account token.

To regenerate the icon, run `python3 tools/icon_gen.py` (needs Pillow and
numpy).
