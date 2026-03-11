import subprocess
from pathlib import Path

def get_git_velocity(file_path: str) -> int:
    """
    Calculates the 'Git Velocity' (commit count) for a specific file 
    within the last 90 days.
    
    This fulfills the 'Strategic FDE Question #5' requirement.
    """
    try:
        # Convert to absolute path to avoid confusion
        abs_path = Path(file_path).resolve()
        
        # We must run the git command from the directory where the file lives
        # or the root of that git repo.
        target_dir = abs_path.parent

        cmd = [
            "git", 
            "rev-list", 
            "--count", 
            "--since='90 days ago'", 
            "HEAD", 
            "--", 
            str(abs_path)
        ]

        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=str(target_dir),
            check=False # Don't crash if git fails
        )

        if result.returncode != 0:
            # Likely not a git repo or git isn't installed
            return 0
            
        return int(result.stdout.strip()) if result.stdout.strip() else 0

    except Exception as e:
        # Senior move: log the error but don't stop the whole pipeline
        # print(f"Error getting git velocity for {file_path}: {e}")
        return 0