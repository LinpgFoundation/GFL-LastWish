from .character import *


class Gsh18(FriendlyCharacter):
    def __init__(self, characterData: dict, mode: str) -> None:
        super().__init__(characterData, mode)
        self._skill_type = 1

    def apply_skill(self, alliances: dict, enemies: dict, _targets: tuple[str, ...]) -> dict[str, int]:
        results: dict[str, int] = {}
        healed_hp: int = 0
        for key in _targets:
            healed_hp = round((alliances[key].max_hp - alliances[key].current_hp) * 0.3)
            alliances[key].heal(healed_hp)
            results[key] = healed_hp
        return results
