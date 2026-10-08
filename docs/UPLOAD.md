# 首次上传 GitHub（PowerShell）

本地已经初始化 `main`、配置 `origin`、安装仓库级 Git LFS 钩子，并准备大文件规则。**没有自动提交，也没有推送任何文件。**

## 1. 发布前检查

- 确认 `LICENSING.md` 中的许可和素材来源事项；当前已添加 `LICENSE-MIT` 与 `LICENSE-CC-BY-NC-SA-4.0`，发布前仍需确认你有权将对应内容按这两种许可分发。
- 阅读 `KNOWN_LIMITATIONS.md`；在本地副本中测试主要 Blender 工程，尤其是 `外部参考/OC第五版/OC5_anime_toon_v018.blend`。
- 检查是否愿意公开历史脚本和报告中的本机路径；本次保留源文件，不擅自修改制作记录。
- 确认 GitHub 账户的 Git LFS 存储、下载配额与预算；这里没有启用付费预算。

## 2. 提交并推送

```powershell
Set-Location 'D:\DeepSeek Harness WorkSpace\DeepSeek-whale-girl-3D'
git status --short
git remote -v
git lfs install --local
git add .
git diff --cached --stat
git lfs ls-files
git commit -m "Initial release: Whale Girl v2 assets and modeling skills"
git lfs fsck
git push -u origin main
```

逐条执行；任何命令报错都应先处理，不要在提交失败后直接继续推送。首次推送会通过 Git LFS 钩子上传对应的大文件对象，无需先手工 `git lfs push --all`。不要跳过 LFS 钩子。

如果提交提示身份未配置，仅在本仓库设置身份；使用你的真实 Git 提交身份或 GitHub 页面提供的 noreply 邮箱（不要照抄占位符）：

```powershell
git config user.name "YOUR_NAME"
git config user.email "YOUR_GITHUB_NOREPLY_EMAIL"
```

然后重新执行 `git commit`。若推送要求登录，完成 Git 凭据管理器的认证，不要把访问令牌写入文件或远程 URL。

## 3. 常见问题

- 远程仓库后来添加了 README / LICENSE：先 `git fetch origin` 并检查两边历史；不要直接 `--force` 覆盖远程。
- LFS 配额/预算或认证错误：在账户中解决后重新推送，不要把大文件改成普通 Git 以绕过限制。
- 网页下载 ZIP 后工程不能打开：建议改用 Git LFS 克隆，或配置仓库的 LFS 归档选项。
- 提交前更改许可/文档后：重新 `git add .`，再提交。

## 4. 上传后验证

在一个新的、尚不存在的目录克隆仓库：

```powershell
Set-Location 'D:\DeepSeek Harness WorkSpace'
git clone https://github.com/azwosile/DeepSeek-whale-girl-3D.git DeepSeek-whale-girl-3D-check
Set-Location DeepSeek-whale-girl-3D-check
git lfs pull
git lfs fsck
```

之后实际打开 `大肥鱼第二版/装配/FISH2_toon_t002.blend` 检查。

## 官方参考

- https://docs.github.com/en/repositories/working-with-files/managing-large-files/configuring-git-large-file-storage
- https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage
