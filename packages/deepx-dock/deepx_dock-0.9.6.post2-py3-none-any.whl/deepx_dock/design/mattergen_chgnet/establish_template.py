from pathlib import Path
import shutil

def copy_templates_folder(target_path="."):
    target_path = Path(target_path)
    current_dir = Path(__file__).resolve().parent
    source_folder = current_dir / "_templates"
    #
    if not target_path.exists():
        raise ValueError(f"The target path {target_path} does not exist!")
    #
    shutil.copytree(source_folder, target_path / ".prog")
    (target_path / "run.sh").symlink_to(target_path / ".prog" / "run.sh")
    (target_path / "config.sh").symlink_to(target_path / ".prog" / "config.sh")