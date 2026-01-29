# Pykrieg

[![PyPI Version](https://img.shields.io/pypi/v/pykrieg?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/pykrieg/)
[![Documentation](https://img.shields.io/badge/docs-RTD-blue?style=for-the-badge&logo=readthedocs&logoColor=white)](https://pykrieg.readthedocs.io/)
[![License](https://img.shields.io/badge/License-GPL%20v3-blue?style=for-the-badge)](LICENSE)

A Pythonic wargame engine for Guy Debord's *Le Jeu de la Guerre* (A Game of War).

## About

Pykrieg is a Python library that implements the complex rules of Guy Debord's strategic tabletop game, providing a clean, extensible API for developers to build custom interfaces, AI opponents, and analysis tools. The project is inspired by the successful **python-chess** library and follows similar design principles.

## Planned Features

- **Complete Game Engine**: Full implementation of Debord's strategic game rules
- **Clean API**: Intuitive Pythonic interface modeled after python-chess
- **Extensible Design**: Easy to create custom variants, unit types, and victory conditions
- **Format Support**: Game record and position formats for saving/sharing games
- **Console Interface**: Interactive terminal-based gameplay (v0.2.0)
- **Well-Tested**: Comprehensive test suite with 89%+ code coverage

## Installation

```bash
pip install pykrieg
```

For console interface with mouse support:

```bash
pip install pykrieg[console]
```

## Quick Start

### Console Interface (Casual Players)

Launch the interactive console game:

```bash
python -m pykrieg.console
```

Play using simple commands:
- `move 5,10 6,10` - Move a unit
- `attack 5,12` - Attack a target
- `pass` - Skip attack phase
- `end` - End turn
- `help` - Show all commands

### Python API (Developers)

```python
from pykrieg import Board

# Create a board
board = Board()

# Add units
board.create_and_place_unit(5, 10, 'INFANTRY', 'NORTH')

# Move a unit
board.make_turn_move(5, 10, 6, 10)

# Attack
board.switch_to_battle_phase()
result = board.make_turn_attack(1, 12)

# End turn
board.end_turn()
```

## Donations

If you like the project and want to support future development, consider donating!

[![Donate with PayPal](https://img.shields.io/badge/PayPal-Donate-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://www.paypal.com/donate/?hosted_button_id=V444RPNWZTNXQ)

## License

This project is licensed under the GNU General Public License v3.0 - see [LICENSE](LICENSE) for details.

The GPL v3 license ensures that:
- The software remains free for all users
- Derivative works must be shared under the same license (copyleft)
- Commercial use is prohibited (requires separate commercial license)
- Users have the freedom to study, modify, and distribute the software
