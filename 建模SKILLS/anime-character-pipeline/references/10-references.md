# 10 参考仓库、插件与文档

> 链接出现在这里，不代表已经安装、购买或完成兼容性测试；每项都写明了“实际用到的范围”。

## 10.1 参考仓库
| 名称 | 地址 | 作用 | 本工作区实际用到的范围 |
|---|---|---|---|
| **CheshireJCat/blender**（dsh-blender，MIT） | https://github.com/CheshireJCat/blender ・ 中文说明 README.zh-CN.md ・ 总入口 skills/create-3d-model | DeepSeek Harness 插件：1 个总控 + 29 个技能（create-3d-model 技能栈）+ 26 个分析 helper + 13 个工具（blender_status / scene_info / object_info / import / python / preview / render / render_frames / export / validate_scene / validate_export / helper_catalog / helper_run）。每次调用起一个独立 `blender -b` 进程，要求 Blender 4.3+ | 借鉴其工程纪律：版本化保存、先检查后修改、多视图证据、导出后干净进程回读、渲染后必须看图。当前桥接**没有注册** blender_* 工具，所以用等价的后台脚本执行，不要声称调用过这些工具 |
| sixtysevenlf/dsh-blender-plugin（BSD-3） | https://github.com/sixtysevenlf/dsh-blender-plugin | 通过 TCP 驱动正在运行的 GUI Blender（实时视口） | 只作为学习笔记中的对照，没有在这几个工程中使用 |
| dsh-tripo-blender（DSH Desktop 社区插件，非 Tripo 官方） | 见工作区 `Arena反代/dsh-tripo-blender-intro/` | 在 DSH 里调用 Tripo 生成部件，预览 GLB 并下载 | 介绍视频的示例 1（OC5）和示例 2（大肥鱼第二版）就是用本技能的流程做出来的 |
| Tripo3d Blender Bridge（Tripo DCC Bridge） | 工作区 `Blender DSH/插件/Tripo3d_Blender_Bridge-latest.zip` | Tripo 官方的 Blender 侧边栏桥接 | 流程文章中用到；本工作区的 Tripo 模型以 FBX 文件导入 |

## 10.2 参考渲染插件
| 名称 | 地址 | 说明 |
|---|---|---|
| **Paper朱二次元渲染助手**（paperzhu-anime-helper，作者 Paper朱） | https://github.com/PUBG11S1/paperzhu-anime-helper | Blender 二次元风格化渲染插件，官方标注 4.1–5.0。功能：一键描边（可调粗细、可选“修复描边”）、高光皮肤材质、二次元色彩管理、一键辉光；面板在 N 面板 → Paper二次元渲染助手。**实测范围**：在 Blender 5.2.2 上临时调用 V2 `materials.py` 的描边修复和高光辅助函数，渲染成功；没有全局安装，UI 和辉光未验证。默认高光在深色制服上过亮，需要调低 |
| Goo Engine | https://github.com/dillongoostudios/goo-engine | 自定义的 Blender 构建，不是普通插件；未使用 |
| lilToon | https://lilxyzw.github.io/lilToon/ | Unity 侧的 Toon 方案；v018 只是借鉴其“插画式”观感，用 EEVEE 原生节点实现 |
| Komikaze | https://superhivemarket.com/products/komikaze | 商业插件；未购买、未使用 |

## 10.3 参考文档
| 文档 | 位置 | 用途 |
|---|---|---|
| 《TRIPO X GPT 6 ASTRA · 二次元少女角色全流程制作记录》 | https://fea97a90942247c7a9e64b984428ce9a.app.workbuddy.host/#s8 | 6 阶段流程：提示词 → 4 图抽卡 → 拆分 / 自动裁切 → DCC Bridge → 装配 → 绑定 + 动力学。要点：额度花在头发和裙子上、接缝藏起来、部件独立、以身体为尺度基准、每轮复述约束、姿势测试 f20/40/60/80、裙子被动布料、头发骨骼驱动 |
| 《AI辅助角色建模_绑定_物理与验收通用手册》 | 副本：`建模SKILLS/参考文档/AI辅助角色建模_绑定_物理与验收通用手册.md`（上一轮 AI 的复盘，2026-10-06） | 验收合同、自碰撞、亚帧、缓存、时间连续性、导出回读等通用纪律；本技能第 05、07 章引用了其中的要点 |
| 大肥鱼第二版 GPT 拆图提示词 | `Blender DSH/大肥鱼第二版/原图/大肥鱼第二版_GPT拆图提示词.md`（副本在 `建模SKILLS/参考文档/`） | 三张拆图的完整提示词、比例建议和修正指令 |
| AI操控Blender 学习笔记（00–07） | `Blender DSH/AI操控Blender-学习笔记/` | 双插件上手、十二阶段流水线、概念词典与排错 |
| Tripo 开发者文档 | https://developers.tripo3d.com/zh/docs/ ・ 多视图：https://developers.tripo3d.com/en/docs/generation-multiview-to-model/standard ・ 本地副本 `Blender DSH/docs_raw/` | 任务生命周期、计费、限流、多视图生成、绑定检查 |
| GPT Images 2.5 | 2026-09-08 发布 | Flare（快）/ Sunburst（精确，参考保持最好）；最高 4K（长边 3840）；比例 1:3–3:1；最多 16 张参考图；支持透明背景和局部重绘 |
| Blender 手册：Shader to RGB / EEVEE 节点支持与限制 | https://docs.blender.org/manual/en/latest/render/shader_nodes/color/shader_to_rgb.html ・ https://docs.blender.org/manual/en/latest/render/eevee/limitations/nodes_support.html | 卡通着色只在 EEVEE 内有效，不能随 GLB/FBX 迁移 |
| CMU Graphics Lab Motion Capture Database | http://mocap.cs.cmu.edu | subject 35（walk/run，120 fps）、subject 09（run）。必须署名：The data used in this project was obtained from mocap.cs.cmu.edu. The database was created with funding from NSF EIA-0196217. |
| MIHOYO（星铁）角色模型 | `Blender DSH/MIHOYO模型/` | 只量比例。使用规则：允许改造，禁止二次配布和商用 |

## 10.4 本技能的来源工程（证据位置）
- OC 第五版：`Blender DSH/OC 第五版/`，包括装配工作_20261005、骨骼与渲染_20261006（v016–v018）、精细绑定与物理、跑步动作 v094、手臂比例 v102、跑步布料 v101/v104。
- 大肥鱼第一版：`Blender DSH/大肥鱼/装配_20261007/`，包括 r001 点评、t002 头发整理、g005–g007 物理。
- 大肥鱼第二版：`Blender DSH/大肥鱼第二版/装配/`，包括 f001–f004、r001/r002、p001/p002、t001/t002，以及各自的 report.json 与验收图。
