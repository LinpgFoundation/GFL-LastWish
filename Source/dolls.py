from typing import Callable
from .character import *


class Dolls:
    """
    特殊角色的实现
    """

    class gsh18(FriendlyCharacter):
        def __init__(self, characterData: dict, mode: str) -> None:
            super().__init__(characterData, mode)
            self._skill_type = 1

        def apply_skill(
            self, alliances: dict, enemies: dict, _targets: tuple[str, ...]
        ) -> dict[str, int]:
            results: dict[str, int] = {}
            for key in _targets:
                healed_hp: int = round(
                    (alliances[key].max_hp - alliances[key].current_hp) * 0.3
                )
                alliances[key].heal(healed_hp)
                results[key] = healed_hp
            return results

    # 工厂方法
    @classmethod
    def new(cls, characterData: dict, mode: str, _type: str) -> FriendlyCharacter:
        # 获取构建器
        _func: Optional[Callable[[dict, str], FriendlyCharacter]] = cls.__dict__.get(
            _type
        )
        # 如果没有对应的构建器
        if _func is None:
            return FriendlyCharacter(characterData, mode)
        # 返回对应的实体
        return _func(characterData, mode)
