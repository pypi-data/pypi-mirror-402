from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter, FuzzyCompleter
from prompt_toolkit.validation import Validator, ValidationError
import requests
from datetime import datetime
from ..dgx import DGX
from .softwares import SOFTWARE_CONFIG


class PRESET:
    def __init__(self):
        self.api_failed = False
        self.software = SOFTWARE_CONFIG
        repo_url = self.select_software()
        download_url = self.select_software_release(repo_url)
        use_proxy = self.ask_use_proxy()
        DGX(download_url, proxy=use_proxy)

    def select_software(self):
        """让用户选择软件并返回仓库地址"""
        base_completer = WordCompleter(list(self.software.keys()), ignore_case=True)

        # 创建验证器，只允许输入 self.software.keys() 中的内容
        class SoftwareValidator(Validator):
            def __init__(self, valid_options):
                self.valid_options = valid_options

            def validate(self, document):
                text = document.text.strip()
                if text and text not in self.valid_options:
                    raise ValidationError(
                        message=f"无效的选项，请从以下选项中选择: {', '.join(self.valid_options)}"
                    )

        completer = FuzzyCompleter(base_completer)
        validator = SoftwareValidator(list(self.software.keys()))

        selected = prompt(
            "请选择软件 (支持模糊搜索TAB补全): ",
            completer=completer,
            validator=validator,
            validate_while_typing=False,
        ).strip()

        if selected in self.software:
            repo_url = self.software[selected]["url"]
            print(f"\n软件: {selected}")
            print(f"仓库地址: {repo_url}")
            return repo_url
        else:
            print(f"\n错误: 未找到软件 '{selected}'")
            print(f"可用选项: {', '.join(self.software.keys())}")
            return None

    def select_software_release(self, repo_url):
        """
        通过 https://api.github.com/repos/{owner}/{repo}/releases 接口获取 软件release信息
        然后 让用户选择 release 版本(用 FuzzyCompleter)
        然后让用户选择 该release 版本当中的文件(用 FuzzyCompleter)
        然后 生成所需要下载文件的链接
        """
        # 从仓库URL提取owner和repo
        parts = repo_url.rstrip("/").split("/")
        owner, repo = parts[-2], parts[-1]

        # 获取releases信息
        api_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            releases = response.json()

            # 显示API请求频率限制信息
            rate_limit = response.headers.get("X-RateLimit-Limit", "N/A")
            rate_remaining = response.headers.get("X-RateLimit-Remaining", "N/A")
            rate_reset = response.headers.get("X-RateLimit-Reset", "N/A")

            # 将Unix时间戳转换为人类可读的时间格式
            if rate_reset != "N/A":
                try:
                    reset_time = datetime.fromtimestamp(int(rate_reset))
                    rate_reset = reset_time.strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError):
                    pass

            print(
                f"\nAPI请求成功 | 频率限制: {rate_remaining}/{rate_limit} 剩余 | 重置时间: {rate_reset}"
            )
        except Exception as e:
            print(f"\n错误: API请求失败 - {e}")
            print("将使用默认版本和文件列表")
            self.api_failed = True
            return self._select_default_version_and_files(owner, repo)

        if not releases:
            print("\n错误: 该仓库没有releases")
            return None

        # 让用户选择release版本
        release_names = [r["tag_name"] for r in releases]
        release_meta = {
            r["tag_name"]: f"预发布: {r['prerelease']} | 发布时间: {r['published_at']}"
            for r in releases
        }
        release_completer = FuzzyCompleter(
            WordCompleter(release_names, meta_dict=release_meta, ignore_case=True)
        )

        # 创建验证器，只允许输入有效的release版本
        class ReleaseValidator(Validator):
            def __init__(self, valid_releases):
                self.valid_releases = valid_releases

            def validate(self, document):
                text = document.text.strip()
                if text and text not in self.valid_releases:
                    raise ValidationError(
                        message="无效的release版本，请从列表中选择有效的版本"
                    )

        release_validator = ReleaseValidator(release_names)

        selected_release = prompt(
            "请选择release版本 (支持模糊搜索TAB补全): ",
            completer=release_completer,
            validator=release_validator,
            validate_while_typing=False,
        ).strip()

        # 找到选中的release
        release = next((r for r in releases if r["tag_name"] == selected_release), None)
        if not release:
            print(f"\n错误: 未找到版本 '{selected_release}'")
            return None

        # 获取该release的所有文件
        assets = release.get("assets", [])
        
        # 添加 GitHub 自动生成的 Source code 压缩包
        source_code_assets = [
            {
                "name": f"Source code ({selected_release}.zip)",
                "size": 0,  # GitHub API 不提供 source code 的大小信息
                "download_count": 0,
                "browser_download_url": f"https://github.com/{owner}/{repo}/archive/refs/tags/{selected_release}.zip",
                "is_source_code": True
            },
            {
                "name": f"Source code ({selected_release}.tar.gz)",
                "size": 0,
                "download_count": 0,
                "browser_download_url": f"https://github.com/{owner}/{repo}/archive/refs/tags/{selected_release}.tar.gz",
                "is_source_code": True
            }
        ]
        
        # 将 source code 添加到 assets 列表尾部
        assets = assets + source_code_assets
        
        if not assets:
            print(f"\n错误: 版本 '{selected_release}' 没有可下载的文件")
            return None

        # 按下载次数降序排序（source code 会排在最后）
        assets = sorted(assets, key=lambda x: (x.get("is_source_code", False), -x.get("download_count", 0)))

        # 让用户选择文件
        asset_names = [asset["name"] for asset in assets]
        asset_meta = {}
        for asset in assets:
            if asset.get("is_source_code"):
                asset_meta[asset["name"]] = "GitHub 自动生成的源代码压缩包"
            else:
                asset_meta[asset["name"]] = f"大小: {asset['size'] / 1024 / 1024:.2f} MB | 下载次数: {asset['download_count']}"
        asset_completer = FuzzyCompleter(
            WordCompleter(asset_names, meta_dict=asset_meta, ignore_case=True)
        )

        # 创建验证器，只允许输入有效的文件名
        class AssetValidator(Validator):
            def __init__(self, valid_assets):
                self.valid_assets = valid_assets

            def validate(self, document):
                text = document.text.strip()
                if text and text not in self.valid_assets:
                    raise ValidationError(
                        message="无效的文件名，请从列表中选择有效的文件"
                    )

        asset_validator = AssetValidator(asset_names)

        selected_asset = prompt(
            "请选择要下载的文件 (支持模糊搜索TAB补全): ",
            completer=asset_completer,
            validator=asset_validator,
            validate_while_typing=False,
        ).strip()

        # 找到选中的文件
        asset = next((a for a in assets if a["name"] == selected_asset), None)
        if not asset:
            print(f"\n错误: 未找到文件 '{selected_asset}'")
            return None

        download_url = asset["browser_download_url"]
        print(f"\n版本: {selected_release}")
        print(f"文件: {selected_asset}")
        print(f"下载链接: {download_url}")

        return download_url

    def _select_default_version_and_files(self, owner, repo):
        """当API请求失败时，让用户从默认版本和文件中选择"""
        # 根据repo名称找到对应的软件配置
        software_config = None
        for name, config in self.software.items():
            if repo in config["url"]:
                software_config = config
                break

        if not software_config:
            print(f"\n错误: 未找到 {repo} 的默认配置")
            return None

        default_version = software_config.get("default_version")
        default_files = software_config.get("default_files", [])

        if not default_version:
            print(f"\n错误: {repo} 没有配置默认版本")
            return None

        # 如果 default_files 为空，自动生成 source code 下载链接
        if not default_files:
            print(f"\n注意: {repo} 没有配置默认文件，将使用 GitHub 自动生成的源代码压缩包")
            default_files = [
                f"Source code ({default_version}.tar.gz)",
                f"Source code ({default_version}.zip)"
            ]

        print(f"\n默认版本: {default_version}")

        # 让用户选择默认文件
        file_completer = FuzzyCompleter(WordCompleter(default_files, ignore_case=True))

        # 创建验证器，只允许输入有效的文件名
        class FileValidator(Validator):
            def __init__(self, valid_files):
                self.valid_files = valid_files

            def validate(self, document):
                text = document.text.strip()
                if text and text not in self.valid_files:
                    raise ValidationError(
                        message="无效的文件名，请从列表中选择有效的文件"
                    )

        file_validator = FileValidator(default_files)

        selected_file = prompt(
            "请从默认文件列表中选择 (支持模糊搜索TAB补全): ",
            completer=file_completer,
            validator=file_validator,
            validate_while_typing=False,
        ).strip()

        if selected_file not in default_files:
            print(f"\n错误: 未找到文件 '{selected_file}'")
            return None

        # 构造下载链接
        # 如果是 source code 压缩包，使用 archive 链接格式
        if selected_file.startswith("Source code"):
            if selected_file.endswith(".tar.gz)"):
                download_url = f"https://github.com/{owner}/{repo}/archive/refs/tags/{default_version}.tar.gz"
            elif selected_file.endswith(".zip)"):
                download_url = f"https://github.com/{owner}/{repo}/archive/refs/tags/{default_version}.zip"
            else:
                download_url = f"https://github.com/{owner}/{repo}/releases/download/{default_version}/{selected_file}"
        else:
            download_url = f"https://github.com/{owner}/{repo}/releases/download/{default_version}/{selected_file}"
        
        print(f"\n版本: {default_version}")
        print(f"文件: {selected_file}")
        print(f"下载链接: {download_url}")

        return download_url

    def ask_use_proxy(self):
        """询问用户是否使用国内代理下载"""
        proxy_completer = FuzzyCompleter(WordCompleter(["yes", "no"], ignore_case=True))

        class ProxyValidator(Validator):
            def validate(self, document):
                text = document.text.strip().lower()
                if text and text not in ["yes", "no"]:
                    raise ValidationError(message="请输入 'yes' 或 'no'")

        choice = (
            prompt(
                "是否使用国内代理下载? (yes/no): ",
                completer=proxy_completer,
                validator=ProxyValidator(),
                validate_while_typing=False,
            )
            .strip()
            .lower()
        )

        use_proxy = choice == "yes"
        if use_proxy:
            print("\n将使用国内代理下载")
        else:
            print("\n将直接从GitHub下载")

        return use_proxy


