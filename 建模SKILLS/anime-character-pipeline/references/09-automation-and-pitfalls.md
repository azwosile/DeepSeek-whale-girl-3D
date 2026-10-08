# 09 自动化执行（MCP / 后台 Blender）与环境坑

## 9.1 执行模型
- 桥接（ShunCode bridge MCP）跑在 Windows x64 主机上，`run_command` 用 PortableGit bash（路径写成 `/c/…`、`/d/…`），**不要套一层 `bash -c`**。不要根据操作系统猜测 shell。
- 文件工具只能访问工作区根目录；`Blender DSH` 等目录要用 run_command 操作。
- 修改文本文件优先用 apply_patch，以保留 CRLF。
- 删除、覆盖等破坏性操作需要用户确认；覆盖前先备份到 `_backup_*`。
- `timeout_ms` 最大 120000；超时只说明请求返回了，命令可能还在跑，要用 get_command_output 继续读。
- 任务卡（set_todos）：每次对话先建（新任务用 `new_task: true`），同时只能有一个 in_progress；结束前发 `lifecycle: completed`（或如实标 blocked）快照，等待确认。
- 会话会**静默过期**（命令返回空）：先重新 init 再重跑，重新 init 后旧任务卡的所有权会丢失，要新建任务卡。
- 不在报告或文件里泄露 MCP URL 令牌或其他凭据。

## 9.2 Blender 后台脚本模板
```bash
B="/d/Steam/steamapps/common/Blender/blender.exe"
cd "/d/DeepSeek Harness WorkSpace/Arena反代/_arena_tmp/<工作目录>"     # 用绝对路径 cd
"$B" -b "<输入.blend>" --factory-startup --python-exit-code 1 -P script.py -- 参数 > job.log 2>&1
grep -E "^DONE|Error|Traceback" job.log
```
- 脚本末尾打印唯一完成标记（例如 `EX_DONE`），每一步把关键数字写进 `*_report.json`。
- 需要更新物理缓存的帧，**从第 1 帧逐帧 `frame_set`** 到目标帧，不要直接跳。
- 并行 ≤ 3 个进程；**同一工程不要同时开两个 EEVEE 进程**（实测贴图丢失，变成品红色）。
- 长任务（烘焙、视频）用 `nohup … &` 后台运行，再轮询日志。

## 9.3 API 坑（实测）
- 相机朝向：`cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()`（d 是从目标指向相机的方向）。
- `render.filepath` 要用**绝对路径**；相对路径不会按当前目录解析，图会找不到。
- BVH `ray_cast` 返回 `(location, normal, index, distance)`，没命中时全是 None。
- numpy 2 中没有 `ndarray.ptp()` 方法，要用 `np.ptp(a)`。
- 对 append 进来的对象改 `matrix_world` 可能不生效：先 link 到场景、更新 view_layer，再改；或者直接改网格。
- `Matrix(4x4) @ Matrix(3x3)` 会报错，要先 `.to_3x3()`。
- Tripo 法线不可靠；描边和内外判断都不要依赖法线。
- 4x4 矩阵乘 Vector(3) 可以直接用；批量处理顶点用 `foreach_get` 加 numpy。

## 9.4 传输坑（沙盒 ↔ 主机）
- 通过 stdout 传 base64 会损坏；二进制要分块写成 `*.b64.part_*`，在主机端 `cat | base64 -d` 拼回，再**核对 sha256**。
- 文本推送工具只接受 UTF-8，拒绝写入已存在的目标，参数长度上限约 128 KB；单个 patch 上限 262144 字节。
- 取回图片要求单文件约 400 KB 以下，大图先压缩或拆成多张。
- 输出会按 80 列换行，解析时要注意。
- 读图工具对同名文件可能返回旧内容：每次用新文件名。
- 通过 rc 内联 `python -c` 不可靠，先推送 .py 文件再执行。

## 9.5 依赖
- 沙盒导出视频需要：`pip install playwright imageio-ffmpeg && python -m playwright install --with-deps chromium`。
- 主机 Python 有 playwright 和 PIL，但没有 imageio-ffmpeg；不要擅自给用户主机装依赖，先问。
