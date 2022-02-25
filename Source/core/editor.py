from .ui import linpg

# 地图编辑器系统
class MapEditor(linpg.AbstractMapEditor):

    # 加载角色的数据
    def _load_characters_data(self, mapFileData: dict) -> None:
        # 生成进程并开始加载角色信息
        self._start_loading_characters(mapFileData["character"], mapFileData["sangvisFerri"], "dev")
        # 类似多线程的join，待完善
        while self._is_characters_loader_alive():
            pass
