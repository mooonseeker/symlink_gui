import ctypes
import os


def create_symlink(source_path: str, target_folder: str):
    """
    在目标文件夹中为源文件/文件夹创建一个符号链接。

    :param source_path: 源文件或文件夹的绝对路径。
    :param target_folder: 要在其中创建链接的目标文件夹的绝对路径。
    :return: 一个元组 (bool, str)，表示操作是否成功以及相应的消息。
    """
    if not os.path.exists(source_path):
        return False, f"源路径不存在: {source_path}"

    if not os.path.isdir(target_folder):
        return False, f"目标位置不是一个有效的文件夹: {target_folder}"

    link_name = os.path.join(target_folder, os.path.basename(source_path))

    try:
        # 在Windows上，os.symlink需要知道目标是目录还是文件
        # target_is_directory=True 适用于文件夹链接
        target_is_directory = os.path.isdir(source_path)
        os.symlink(source_path, link_name, target_is_directory=target_is_directory)
        return True, f"成功创建链接:\n{link_name}\n -> {source_path}"
    except FileExistsError:
        return (
            False,
            f"错误: 文件或文件夹 '{os.path.basename(source_path)}' 已在目标位置存在。",
        )
    except OSError as e:
        # 检查是否为权限错误 (ERROR_PRIVILEGE_NOT_HELD)
        if e.winerror == 1314:
            return (
                False,
                "权限错误: 创建符号链接需要管理员权限。请以管理员身份运行此程序。",
            )
        return False, f"创建链接时发生操作系统错误: {e}"
    except Exception as e:
        return False, f"发生未知错误: {e}"


def is_admin():
    """检查当前用户是否拥有管理员权限。"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
