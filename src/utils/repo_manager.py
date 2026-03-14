from __future__ import annotations

import logging
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from git import Repo


logger = logging.getLogger(__name__)


class RepositoryManager:
	"""Prepare local or remote repositories for analysis workflows."""

	@staticmethod
	def is_github_url(target: str) -> bool:
		"""Return True when *target* points to a GitHub repository URL."""
		if not target:
			return False

		parsed = urlparse(target.strip())
		if parsed.scheme in {"http", "https", "ssh", "git"} and parsed.netloc:
			return parsed.netloc.lower().endswith("github.com")

		# Handle SCP-style Git URLs such as: git@github.com:owner/repo.git
		if parsed.scheme == "" and "@" in target and ":" in target:
			ssh_like_target = f"ssh://{target.replace(':', '/', 1)}"
			ssh_like = urlparse(ssh_like_target)
			return ssh_like.netloc.lower().endswith("github.com")

		return False

	@staticmethod
	def prepare_repo(target: str) -> str:
		"""
		Prepare a repository path.

		- If *target* is a GitHub URL, clone into a temporary directory.
		- If *target* is a local directory path, return its absolute path.
		"""
		if RepositoryManager.is_github_url(target):
			temp_path = tempfile.mkdtemp(prefix="brownfield-cartographer-")
			logger.info("Starting remote clone from %s into %s", target, temp_path)
			try:
				Repo.clone_from(target, temp_path)
			except Exception:
				# Prevent leaking temporary directories when clone fails.
				shutil.rmtree(temp_path, ignore_errors=True)
				raise
			return temp_path

		local_path = Path(target).expanduser().resolve()
		if not local_path.is_dir():
			raise ValueError(f"Target is not a valid local directory: {target}")

		return str(local_path)

	@staticmethod
	def cleanup(temp_path: str | None) -> None:
		"""Safely remove a temporary directory created by :meth:`prepare_repo`."""
		if not temp_path:
			return

		path = Path(temp_path).expanduser().resolve()
		temp_root = Path(tempfile.gettempdir()).resolve()

		# Only remove directories inside the OS temp root.
		if not path.is_dir() or temp_root not in path.parents:
			return

		logger.info("Cleaning up temporary repository at %s", path)
		shutil.rmtree(path, ignore_errors=True)
