"""Git 命令组 - 代理到 Dulwich CLI + 镜像代理支持

直接调用 dulwich CLI，支持所有 git 命令。
注意：实际的 git 命令在 __main__.py 中直接处理，绕过 fire。

新增功能：GitHub 镜像代理支持（适用于国内网络环境）

Usage:
    maque git <command> [args...]

Examples:
    maque git status
    maque git add .
    maque git commit -m "message"
    maque git log
    maque git rebase main
    maque git stash push
    maque git cherry-pick <commit>
    maque git config -l

    # 镜像代理相关命令
    maque git clone https://github.com/user/repo --use_mirror=True
    maque git mirrors                           # 列出可用镜像
    maque git clone-mirror https://github.com/user/repo ./repo  # 使用默认镜像克隆
"""


class GitGroup:
    """Git 命令组 - 代理到 Dulwich CLI

    注意：此类仅作为占位符，实际的 git 命令处理在 __main__.py 中，
    直接调用 dulwich CLI 以避免 fire 参数解析问题。

    支持 GitHub 镜像代理功能，适用于国内网络环境加速 clone/fetch/pull。
    """

    def __init__(self, cli_instance):
        self.cli = cli_instance

    def mirrors(self):
        """列出所有可用的 GitHub 镜像代理

        Returns:
            镜像列表及其 URL
        """
        from maque.git import GIT_MIRRORS, DEFAULT_MIRROR

        print("可用的 GitHub 镜像代理:")
        print("-" * 60)
        for name, info in GIT_MIRRORS.items():
            default_mark = " (默认)" if name == DEFAULT_MIRROR else ""
            print(f"  {name:12} → {info['url']}{default_mark}")
            print(f"               {info['description']}")
        print("-" * 60)
        print("\n使用方法:")
        print("  maque git clone-mirror <url> <path> [--mirror=ghproxy]")
        print("  maque git fetch-mirror [--remote=origin] [--mirror=ghproxy]")
        print("  maque git pull-mirror [--remote=origin] [--mirror=ghproxy]")
        print("\n推荐: ghproxy 系列镜像速度最快 (ghproxy, ghproxy-cdn, ghproxy-hk)")
        print("注意: 镜像可用性可能随时间变化，如遇问题请尝试其他镜像")
        return GIT_MIRRORS

    def clone_mirror(
        self,
        url: str,
        path: str,
        mirror: str = None,
        username: str = None,
        password: str = None,
    ):
        """使用镜像代理克隆 GitHub 仓库

        Args:
            url: GitHub 仓库 URL (https://github.com/user/repo)
            path: 本地目标路径
            mirror: 镜像提供商 (gitclone, ghproxy, ghfast, gitmirror, bgithub)
            username: Git 用户名（可选）
            password: Git 密码/Token（可选）

        Returns:
            PureGitRepo 实例

        Examples:
            maque git clone-mirror https://github.com/pytorch/pytorch ./pytorch
            maque git clone-mirror https://github.com/user/repo ./repo --mirror=ghproxy
        """
        from maque.git import PureGitRepo, convert_to_mirror_url

        mirror_url = convert_to_mirror_url(url, mirror)
        print(f"使用镜像克隆: {mirror_url}")
        repo = PureGitRepo.clone(
            url, path, username=username, password=password,
            use_mirror=True, mirror_provider=mirror
        )
        print(f"克隆完成: {path}")
        return repo

    def fetch_mirror(
        self,
        remote: str = "origin",
        mirror: str = None,
        username: str = None,
        password: str = None,
        repo_path: str = ".",
    ):
        """使用镜像代理拉取远程更新（不合并）

        Args:
            remote: 远程仓库名
            mirror: 镜像提供商
            username: Git 用户名（可选）
            password: Git 密码/Token（可选）
            repo_path: 仓库路径，默认当前目录

        Examples:
            maque git fetch-mirror
            maque git fetch-mirror --mirror=ghproxy
        """
        from maque.git import PureGitRepo

        repo = PureGitRepo.open(repo_path)
        remote_url = repo.get_remote_url(remote)
        if remote_url:
            print(f"远程仓库: {remote_url}")
        repo.fetch(
            remote, username=username, password=password,
            use_mirror=True, mirror_provider=mirror
        )
        print("Fetch 完成")
        return repo

    def pull_mirror(
        self,
        remote: str = "origin",
        mirror: str = None,
        username: str = None,
        password: str = None,
        repo_path: str = ".",
    ):
        """使用镜像代理拉取并合并远程更新

        Args:
            remote: 远程仓库名
            mirror: 镜像提供商
            username: Git 用户名（可选）
            password: Git 密码/Token（可选）
            repo_path: 仓库路径，默认当前目录

        Examples:
            maque git pull-mirror
            maque git pull-mirror --mirror=ghproxy
        """
        from maque.git import PureGitRepo

        repo = PureGitRepo.open(repo_path)
        remote_url = repo.get_remote_url(remote)
        if remote_url:
            print(f"远程仓库: {remote_url}")
        repo.pull(
            remote, username=username, password=password,
            use_mirror=True, mirror_provider=mirror
        )
        print("Pull 完成")
        return repo

    def convert_url(self, url: str, mirror: str = None):
        """将 GitHub URL 转换为镜像 URL（不执行操作，仅输出）

        Args:
            url: 原始 GitHub URL
            mirror: 镜像提供商

        Examples:
            maque git convert-url https://github.com/user/repo
            maque git convert-url https://github.com/user/repo --mirror=ghproxy
        """
        from maque.git import convert_to_mirror_url

        mirror_url = convert_to_mirror_url(url, mirror)
        print(f"原始 URL: {url}")
        print(f"镜像 URL: {mirror_url}")
        return mirror_url

    # =========================================================================
    # Git 全局镜像配置（让原生 git clone 自动使用镜像）
    # =========================================================================

    def _get_known_mirror_urls(self) -> list:
        """获取所有已知镜像的 URL 列表"""
        from maque.git import GIT_MIRRORS
        urls = []
        for name, info in GIT_MIRRORS.items():
            urls.append(info["url"])
        return urls

    def _clear_all_mirror_configs(self):
        """清除所有 maque 设置的镜像配置"""
        import subprocess

        # 获取当前所有 insteadOf 配置
        result = subprocess.run(
            ['git', 'config', '--global', '--get-regexp', r'url\..*\.insteadOf'],
            capture_output=True, text=True
        )

        if not result.stdout.strip():
            return

        # 解析并清除与已知镜像相关的配置
        known_mirrors = self._get_known_mirror_urls()
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            # 格式: url.https://mirror/....insteadOf https://github.com/
            parts = line.split(' ', 1)
            if len(parts) < 2:
                continue
            key = parts[0]  # url.https://mirror/....insteadOf

            # 检查是否是我们设置的镜像配置
            for mirror_url in known_mirrors:
                if mirror_url in key:
                    subprocess.run(
                        ['git', 'config', '--global', '--unset', key],
                        capture_output=True
                    )
                    break

    def mirror_set(self, mirror: str = None):
        """设置 Git 全局镜像，让原生 git clone 自动使用镜像

        设置后，直接使用 git clone https://github.com/user/repo 就会自动走镜像。

        Args:
            mirror: 镜像名称 (ghproxy, ghproxy-cdn, ghproxy-hk, cors, kkgithub, ghfast)
                   默认使用 ghproxy

        Examples:
            maque git mirror-set                      # 使用默认镜像 (ghproxy)
            maque git mirror-set --mirror=ghproxy-cdn # 使用 CDN 镜像
            # 之后直接用 git clone https://github.com/user/repo 就会自动走镜像
        """
        import subprocess
        from maque.git import GIT_MIRRORS, DEFAULT_MIRROR

        if mirror is None:
            mirror = DEFAULT_MIRROR

        if mirror not in GIT_MIRRORS:
            print(f"未知镜像: {mirror}")
            print(f"可用镜像: {', '.join(GIT_MIRRORS.keys())}")
            return

        mirror_info = GIT_MIRRORS[mirror]
        mirror_url = mirror_info["url"]
        mirror_type = mirror_info["type"]

        # 先清除旧配置
        self._clear_all_mirror_configs()

        # 根据镜像类型设置
        if mirror_type == "prefix":
            # prefix 类型: https://mirror/https://github.com/user/repo
            insteadOf_key = f'url.{mirror_url}https://github.com/.insteadOf'
            insteadOf_value = 'https://github.com/'
        else:  # replace 类型
            # replace 类型: https://mirror.com/user/repo
            insteadOf_key = f'url.{mirror_url}.insteadOf'
            insteadOf_value = 'https://github.com/'

        result = subprocess.run(
            ['git', 'config', '--global', insteadOf_key, insteadOf_value],
            capture_output=True, text=True
        )

        if result.returncode == 0:
            print(f"✓ 已设置 Git 全局镜像: {mirror} ({mirror_url})")
            print(f"  现在可以直接使用: git clone https://github.com/user/repo")
        else:
            print(f"✗ 设置失败: {result.stderr}")

    def mirror_unset(self):
        """移除 Git 全局镜像配置，恢复直连 GitHub

        Examples:
            maque git mirror-unset
        """
        self._clear_all_mirror_configs()
        print("✓ 已移除 Git 镜像配置，恢复直连 GitHub")

    def mirror_status(self):
        """查看当前 Git 镜像配置状态

        Examples:
            maque git mirror-status
        """
        import subprocess
        from maque.git import GIT_MIRRORS

        result = subprocess.run(
            ['git', 'config', '--global', '--get-regexp', r'url\..*\.insteadOf'],
            capture_output=True, text=True
        )

        if not result.stdout.strip():
            print("当前未配置任何 URL 重写，使用直连 GitHub")
            return

        print("当前 Git URL 重写配置:")
        print("-" * 60)

        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split(' ', 1)
            if len(parts) < 2:
                continue
            key = parts[0]
            value = parts[1]

            # 尝试识别镜像名称
            mirror_name = None
            for name, info in GIT_MIRRORS.items():
                if info["url"] in key:
                    mirror_name = name
                    break

            if mirror_name:
                print(f"  镜像: {mirror_name}")
                print(f"  {value} → {key.replace('url.', '').replace('.insteadOf', '')}")
            else:
                print(f"  {key} = {value}")

        print("-" * 60)
        print("\n提示:")
        print("  移除镜像: maque git mirror-unset")
        print("  切换镜像: maque git mirror-set --mirror=<name>")
