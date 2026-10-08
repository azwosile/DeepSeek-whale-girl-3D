# 建模SKILLS

二次元角色建模的全流程经验，按使用对象分成两份：

| 文件 / 目录 | 给谁看 | 内容 |
|---|---|---|
| `二次元角色建模全流程经验.md` | 人 | 流程总览、三个工程的回顾、分阶段经验与坑、协作建议、上一轮与本轮经验对照、参考资料、检查清单、术语表 |
| `参考文档/` | 人和 AI | 上一轮 AI 的《通用手册》副本、大肥鱼第二版 GPT 拆图提示词副本 |
| `anime-character-pipeline/` | AI Agent（技能） | `SKILL.md` 是入口：主流程、门槛、硬规则、用户偏好；`references/` 是按阶段分的 10 章细节；`scripts/` 是已实测的 Blender 脚本；`templates/` 是任务描述、README 和运行清单模板 |

## 技能目录结构
```
anime-character-pipeline/
├─ SKILL.md
├─ references/
│  ├─ 01-contract-and-input-audit.md     交付合同、输入审计、参考优先级、坐标约定
│  ├─ 02-image-split-and-tripo.md        GPT Images 2.5 拆图、Tripo 生成与评估
│  ├─ 03-assembly-and-fit.md             装配贴合、消穿模、配件、修复轮、头发整理
│  ├─ 04-rig-pose-and-motion.md          骨架、权重、姿势测试、手臂比例、跑步动作
│  ├─ 05-physics-skirt-hair-tail.md      裙子布料流程、头发/尾巴骨链三代演进、指标
│  ├─ 06-toon-render-and-paperzhu.md     插画 Toon、描边、Paper朱插件实测范围
│  ├─ 07-qa-matrix.md                    验收矩阵、证据等级、症状排查
│  ├─ 08-export-and-delivery.md          导出回读、交付清单、展示视频
│  ├─ 09-automation-and-pitfalls.md      MCP / 后台 Blender 执行与环境坑
│  └─ 10-references.md                   参考仓库、渲染插件、参考文档
├─ scripts/
│  ├─ mesh_audit.py / compare_audit.py   结构审计 + 保护哈希 + 版本对比
│  ├─ multiview_render.py                自动取景的四视图 / 特写正交渲染（可直接导入 FBX）
│  └─ motion_metrics.py                  骨链抖动 / 折叠指标
└─ templates/
   ├─ stage_prompts.md                   各阶段任务描述（每轮复述约束用）
   ├─ delivery_README_template.md        每轮交付说明模板
   └─ run_manifest_template.json         运行清单模板
```

## 脚本实测记录（2026-10-07，Blender 5.2.2 LTS，大肥鱼第二版）
- `mesh_audit.py` + `compare_audit.py`：对比 `FISH2_rig_r002` 和 `FISH2_toon_t002`，9 个对象的拓扑、UV、坐标哈希全部一致；差异只有新增的 `SOLIDIFY:Outline` 修改器和 1 个描边顶点组，与卡通步骤的预期相符。
- `multiview_render.py`：
  - 原样导入 Tripo 女仆装 FBX（`--front +X`），渲染了 4 视图；
  - 对 t002 用 EEVEE 渲染了第 1 帧的 4 视图和脸部特写；
  - 两次的画面朝向都正确。
- `motion_metrics.py`：t002 跑步段 f100–228 的结果：

  | 骨链 | 加速度 p95 | 高频占比 | 弦长比 |
  |---|---|---|---|
  | hair_B0 | 17.1 | 0.028 | 0.998 |
  | hair_FR | 5.1 | 0.004 | 0.994 |
  | 尾巴 | 3.2 | 0.003 | 0.992 |

  三条链都在平滑范围内。

## 来源
- 上一轮 AI：《AI辅助角色建模_绑定_物理与验收通用手册》（2026-10-06）
- 本轮：OC 第五版后续、大肥鱼第一版、大肥鱼第二版
- 参考仓库：https://github.com/CheshireJCat/blender
- 参考渲染插件：https://github.com/PUBG11S1/paperzhu-anime-helper
- 参考文档：《TRIPO X GPT 6 ASTRA · 二次元少女角色全流程制作记录》、Tripo 开发者文档、Blender 手册、CMU 动捕库
