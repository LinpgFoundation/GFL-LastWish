from .character import *


class Gsh18(FriendlyCharacter):
    def apply_skill(self, alliances: dict, enemies: dict, area: int, _targets: tuple[str, ...]) -> dict[str, tuple[int, int]]:
        results: dict[str, tuple[int, int]] = {}
        healed_hp: int = 0
        for key in _targets:
            healed_hp = round((alliances[key].max_hp - alliances[key].current_hp) * 0.3)
            alliances[key].heal(healed_hp)
            results[key] = (1, healed_hp)
        return results
