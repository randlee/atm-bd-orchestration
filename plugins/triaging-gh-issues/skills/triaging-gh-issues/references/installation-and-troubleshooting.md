# Installation and Troubleshooting

## Check First

```bash
command -v bd && bd version
command -v gh && gh --version
```

Stop when both print a version and `bd` is at least 1.3.0.

## Find Existing Install

```bash
for p in "$HOME/.local/bin" /usr/local/bin /opt/homebrew/bin; do
  [ -x "$p/bd" ] && echo "bd $p/bd"
  [ -x "$p/gh" ] && echo "gh $p/gh"
done
```

## Install

- `bd`: https://github.com/steveyegge/beads#installation
- `gh`: https://cli.github.com/

## Minimum Version

`bd` 1.3.0. `gh` current release.

## PATH Troubleshooting

Claude Code's shell may omit the interactive `PATH`. When the binary is found
above, `export PATH="<dir>:$PATH"` for the session.

## Validation

```bash
command -v bd && bd version
command -v gh && gh --version
```

## Known Issues

A `bd` on `PATH` older than 1.3.0 fails the check. Install 1.3.0 or newer and
run the validation commands again.
