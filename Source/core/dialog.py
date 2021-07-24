from .ui import linpg, os


# 视觉小说系统
class DialogSystem(linpg.DialogSystem):
    # 保存数据
    def save_progress(self) -> None:
        super().save_progress()
        # 检查global.yaml配置文件
        if not os.path.exists(os.path.join(self.folder_for_save_file, "global.yaml")):
            DataTmp = {"chapter_unlocked": 1}
            linpg.config.save(os.path.join(self.folder_for_save_file, "global.yaml"), DataTmp)
