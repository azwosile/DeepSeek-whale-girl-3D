# 更衣室大战 · r033 动画案例

双角色 Blender 动画修复与有声成片归档。发布的是可打开、播放和再次渲染的最终工程，不是从原图一键重建角色的流水线。

## 入口

- 工程：`project/GYS_release_r033.blend`
- 有声视频：`video/locker-room-r033-1080p-with-audio.mp4`
- 无声母版：`video/locker-room-r033-1080p-silent.mp4`
- 依赖清单和 SHA256：`manifests/dependencies.json`
- 发布验证：`reports/validation.json`、`reports/relocation-validation.json`
- 音画验证记录：`reports/av-delivery.json`
- 许可与素材声明：`LICENSE_AND_SOURCES.md`

## 下载与打开

PC2 缓存、MP4 音视频及 `.blend` 全部使用 Git LFS。缓存不是可随意丢弃的临时文件；它们是此最终工程的必要依赖。

```bash
git lfs install --local
git lfs pull --include="动画案例/更衣室大战/**" --exclude=""
git lfs fsck
```

克隆贡献分支的读者需先切到该分支；合并后直接使用 `main`。LFS 指针只有几行文本，不能作为 Blender 工程或缓存打开。完整案例的数据量超过 6 GB，请确认磁盘、LFS 下载配额和预算。

使用制作时实测的 **Blender 5.2.2 LTS** 打开 `project/GYS_release_r033.blend`。选择帧 1–2483 播放。工程使用相对路径读取同目录层级的 `cache/` 和 `audio/`，文件贴图内嵌。不要只下载 `.blend`。

工程输出路径是 `//../renders/locker-room-r033`，不会覆盖随包的成片。默认输出 H.264 / AAC；重新渲染前检查输出设置和 Blender 版本。Blender 5.2 的视频格式需要 `image_settings.media_type='VIDEO'` 后设置 `file_format='FFMPEG'`。

## 内容和验收边界

- 1920×1080、30 fps、2483 帧，约 82.77 秒。
- 保留原动作和镜头；按允许轻微穿模的要求修复，**不是零穿透物理认证**。
- 完整音画解码通过；有声与无声母版的压缩视频包哈希一致，合音没有重新编码画面。
- 成片按约每秒一帧做过 83 张抽查，关键接触动作另外做过原生渲染连续样本检查；不是每帧逐三角形碰撞验收。
- 口型是原脸面上的可动画 Toon 着色，非完整实体口腔。
- 冗余开发中间版本、残缺缓存、传输分片、全部原始渲染帧、便携编码工具与凭据均不纳入本发布。
- 发布包包含最终工程实际引用的完整 PC2，不只包含最新 r033 的五份缓存。

## 验证

下面均为 Bash；命令中的 `blender` 可替换为本机 Blender 可执行文件的带引号路径。

```bash
blender -b --factory-startup --disable-autoexec --python-exit-code 1 \
  --python "动画案例/更衣室大战/scripts/verify_package.py" -- \
  --root "动画案例/更衣室大战"
```

加 `--render-qa` 会生成六张独立发布工程的检查图。该验证会检查依赖文件大小/SHA256、相对路径、缓存是否位于发布目录、部分整数/半帧求值与驱动器。不会把抽查提升为完整物理验收。

`collect_dependencies.py` 是发布整理工具，输入必须是已经完成的制作工程及成片。它不会覆盖来源工程；它也不能替代历史建模、口型修复和接触缓存重建步骤。

根目录 `建模SKILLS/参考文档/更衣室大战_r033_缓存与成片交付.md` 记录本案例的可复用经验，不改写原有通用 SKILL 入口。
