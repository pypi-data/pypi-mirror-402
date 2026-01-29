# Smash Up CLI

Smash Up CLI is a terminal utility for building Smash Up decks. It lets you
select expansions in a TUI and randomly assign factions to each player.

## Features

- TUI configuration to enable or disable expansions.
- Randomized faction assignment per player.
- Config stored at `~/.smashup/factions.toml`.

## Installation

```bash
pip install smashup-cli
```

## Usage

Configure which expansions are available:

```bash
smashup configure
```

<img width="566" height="340" alt="image" src="https://github.com/user-attachments/assets/b35eb626-b904-430a-86c9-76a074509b5a" />


Randomize factions for a game:

```bash
smashup randomize
```

<img width="400" height="220" alt="image" src="https://github.com/user-attachments/assets/59a56c2e-2e40-4654-ad0c-e1adad11a0fa" />


## Development

```bash
pip install -e .
```

## License

MIT
