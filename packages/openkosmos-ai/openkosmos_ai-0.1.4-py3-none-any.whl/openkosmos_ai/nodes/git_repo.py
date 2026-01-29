import os

from git import Repo

from openkosmos_ai.common.model import AIBaseConfig
from openkosmos_ai.nodes.base_node import BaseStateNode


class GitRepoConfig(AIBaseConfig):
    repo_dir: str
    remote_branch: str
    remote_url: str
    username: str
    email: str


class GitRepoNode(BaseStateNode[GitRepoConfig]):
    def __init__(self, config: GitRepoConfig):
        super().__init__(config)
        self.git_repo = GitRepoNode.init_repo(config)

    def repo(self) -> Repo:
        return self.git_repo

    def commit(self, commit_message: str):
        modified_files = [item.a_path for item in self.repo().index.diff(None)]
        changed_files = self.repo().untracked_files + modified_files

        self.repo().index.add(changed_files)

        if len(changed_files) > 0:
            self.repo().index.commit(commit_message)

        return changed_files

    def push(self, close=True):
        origin = self.repo().remote(name="origin")
        origin.push()

        if close:
            self.repo().close()

    def close(self):
        self.repo().close()

    @staticmethod
    def init_repo(config: GitRepoConfig):
        if os.path.exists(config.repo_dir):
            repo = Repo(config.repo_dir)
        else:
            repo = Repo.clone_from(config.remote_url, config.repo_dir)
            repo.git.config("user.name", config.username)
            repo.git.config("user.email", config.email)
            repo.git.checkout("-b", config.remote_branch, f"origin/{config.remote_branch}")

        return repo
