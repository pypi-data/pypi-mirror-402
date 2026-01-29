from pathlib import Path
import shutil

def copy_petsc_install_folder(target_path="."):
    current_dir = Path(__file__).resolve().parent
    source_folder = current_dir / "_template_petsc_install"
    target_path_obj = Path(target_path)
    if not target_path_obj.is_dir():
        target_path_obj.mkdir(exist_ok=False)
    dest_folder = target_path_obj / "PETSc"
    shutil.copytree(source_folder, dest_folder)
