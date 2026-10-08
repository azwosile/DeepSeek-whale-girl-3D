# 大肥鱼第二版：GPT Image 2.5 Sunburst 拆分立绘提示词

用途：把参考立绘拆成 3 份干净的生成图，再交给 Tripo 生成 3D 模型。
1. 素体（带头发），4 视图
2. 女仆装，4 视图
3. 配件合集，1 张

---

## 一、比例建议（在原图上实测）

| 项目 | 原图实测 | 建模目标 | 说明 |
|---|---|---|---|
| 头身比 | 约 7 头身（头高约 135–142 px，含鞋全身约 990 px） | **7 头身** | 偏成熟的米哈游成年女性比例 |
| 身高 | — | **1.62 m**（头高约 23 cm） | 第一版是 1.60 m，可以沿用 |
| 胯部高度 | 被裙子挡住 | **约身高的 48–50%** | 腿要长，原图小腿被画短了，不要照抄 |
| 腰线 | 束腰在全身约 68% 高处 | **高腰线**，在肚脐上方 | 视觉上显腿长 |
| 腰宽 | 约 0.78 个头高 | **约 0.75–0.8 个头高**（正面腰宽约 17–18 cm） | 你觉得腰粗，这里收紧 |
| 臀宽 | 被裙子挡住 | **不超过肩宽**，腰臀宽度比约 0.7 | 你觉得臀大，这里收窄 |
| 肩宽 | 约 1.1–1.2 个头高（裸肩点之间） | **约 1.2 个头高**，不算泡泡袖 | 窄肩，偏二次元 |
| 裙长 | 外层荷叶边下摆在膝盖上沿 | **下摆到膝盖**，最长到膝下 3–5 cm | 第一版裙摆在小腿中部（约身高 14% 处），太长了 |
| 胸部 | 丰满 | 和原图一致 | 素体和衣服必须一致，否则贴合困难 |

原图这类插画会把头画大、小腿画短，**不要在原图上量绝对高度**，用解剖位置来描述（"到膝盖""高腰线"）。

### 出图画幅
- **4 视图（第 1、2 张）**：选 **16:9，4K（3840×2160），质量 max**。四个视图横排，每格约 960×2160，人物高约 2000 px，细节足够。
  - 不要用 2×2 排列，人物会小一半。
- **配件图（第 3 张）**：**3:2（3840×2560）**，物件之间留很大的间隔。
- 生成后**把 4 视图裁成 4 张单独的图**再给 Tripo 的多视图模式。四张图要等高，人物居中，四周留白。

---

## 二、三张图通用的硬性要求（每条提示词都已经包含）

| 要求 | 原因 |
|---|---|
| 正交投影、无透视，四个视图同一比例，头顶和脚底在同一水平线 | Tripo 多视图需要严格对齐 |
| A-pose：手臂从身体两侧向下张开约 45°，手掌张开，手指微分开；双脚分开约一脚宽，平脚站立 | 方便绑定。腋下、腿间留出空隙，网格不会粘连 |
| 平光、无投影、无光泽高光，颜色接近固有色 | 贴图不烤进光影，后面做卡通着色更干净（第一版的油亮感就是贴图烤了高光） |
| 纯色中浅灰背景 #C8C8C8，不用白底 | 白色荷叶边、围裙在白底上会被抠掉 |
| 不要文字、标签、边框、地面阴影 | 避免被 Tripo 当成几何体 |
| 中性表情：闭嘴微笑，眼睛直视前方 | 张嘴的表情会被做成几何体，以后做口型更麻烦。小虎牙以后用贴图或形态键加 |

**左右视图的方向**（要和 Tripo 的输入对应，用之前请在 Tripo 界面确认它的 left/right 定义）：
- 第 2 格：**她的左侧朝向镜头**，脸朝画面左边。
- 第 4 格：**她的右侧朝向镜头**，脸朝画面右边。

---

## 三、提示词

使用方法：上传原立绘作为参考图 1，第 2、3 张另外加上述参考图，然后粘贴提示词。英文对模型的约束更精确，中文是给你看的说明。

### 1）素体（带头发，穿白色基础内衬），4 视图

> 第一版提示词被安全审核拦截了。很可能是这几处描述身体和"紧身/裸露"的用词，组合在一起被判定为敏感：
> skin-tight bodysuit、mannequin、full bust、crotch、gap between the thighs、hips、bare feet、white tights。
> 这一版的改法：
> - 改成"游戏角色设定图里的基础服装"：白色长袖高领上衣加白色打底裤，再加白色平底鞋；
> - 删掉所有身体部位尺寸，体型只用"苗条、成年、7 头身、长腿、细腰"这类中性描述。
>
> 3D 建模时这层内衬薄而贴身，相当于素体，后面套女仆装不受影响。

**参考图**：
- 原立绘
- 原图右上角的脸部特写，单独裁出来上传

```
Game character design turnaround sheet for a 3D modeling team. Using the uploaded character sheet as the reference for her face, hair and colors, draw the SAME character wearing only her plain white base costume, so the modelers can build the base model before adding the maid outfit.

LAYOUT: one row of four full-body views on a 16:9 canvas, left to right: (1) front, (2) left side — she faces image-left, (3) back, (4) right side — she faces image-right. Orthographic projection, no perspective, same scale in all four views, top of head and soles aligned on the same horizontal lines, empty space between views, nothing overlapping. No text, no labels, no frames, no ground shadow. Solid flat light-gray background (#C8C8C8).

POSE: neutral standing A-pose. Arms straight and angled about 45 degrees down from the shoulders, clearly away from the body; hands relaxed and open, fingers slightly apart. Legs straight, feet flat and about one foot-width apart. Head level, looking straight ahead.

FIGURE: adult young woman, slim and elegant, about 7 heads tall, long legs, slender high waist, narrow shoulders, figure consistent with the reference character design.

BASE COSTUME: a plain matte white long-sleeve turtleneck top that reaches the wrists, plain matte white full-length leggings that reach the ankles, and simple white flat slippers. All fitted and smooth, like a dance rehearsal outfit, with no seams, buttons, logos, folds or decorations. No maid outfit, no headband, no hair bows, no tail.

HEAD AND FACE: keep her exact identity from the reference — big bright blue eyes, the same eye shape and lashes, small nose, soft round chin, and the dark-blue whale-fin ears with white fluffy inner edges on both sides of the head. Clean Genshin Impact / HoYoverse-style anime face. Calm expression, mouth closed with a gentle slight smile.

HAIR (most important): same hair design and colors as the reference — deep navy blue at the roots fading smoothly to light sky blue at the tips, the single ahoge, the side-swept bangs, and the thin braid circling the back of the head like a crown. Restyle it as clean HoYoverse-style 3D game hair: about 15 to 20 large, smooth, clearly defined hair clumps with tapered tips. The upper two-thirds hang straight and orderly; only the lower third has a few gentle large waves. No small curls, no frizz, no stray strands. The back hair hangs to hip length as one tidy fan-shaped mass, slightly apart from the back. Two long front locks hang in front of the shoulders, with a little space between them and the arms.

RENDERING: clean cel-shaded anime illustration, flat even lighting, minimal soft shading, no cast shadows, no glossy highlights, true base colors, crisp silhouette, consistent design across all four views.
```

**如果仍然被拦截，按顺序试：**
1. **换参考图。** 不传整张立绘，只传**脸部特写**和**背面全身**两张裁图，原图正面的服装领口可能也会被审核计入。提示词里的 `uploaded character sheet` 改成 `uploaded reference images`。
2. **服装再保守一点。** 把 BASE COSTUME 整段换成：
   `BASE COSTUME: a loose-fitting plain white long-sleeve sweatshirt and plain white straight trousers, simple white flat shoes, no decorations.`
   衣服宽松后建模会不太准，但身材比例可以靠第二张女仆装图和后期调整补回来。
3. **新开一个对话。** 被拦截过的对话，后续请求更容易继续被拦截。

### 2）女仆装，4 视图

**参考图**：
- 原立绘
- **第 1 张生成好的素体（白色内衬）4 视图**（必须）。这样衣服和身体的比例、姿势完全一致，后面贴合才好做。

```
Using the uploaded character sheet for the outfit design, and the uploaded white-base-costume turnaround for the exact figure, proportions and pose, create a 3D-modeling turnaround sheet of ONLY her maid outfit, shown on an invisible body (ghost mannequin style).

LAYOUT: identical to the white-base-costume turnaround — one row of four full-body views on a 16:9 canvas: front, left side (facing image-left), back, right side (facing image-right). Strict orthographic projection, same scale and same vertical alignment as the white-base-costume sheet, so the outfit fits that figure exactly. Empty space between views. No text, no labels, no ground shadow. Solid flat light-gray background (#C8C8C8).

SHOW ONLY THE CLOTHES: no head, no hair, no hands, no legs, no feet, no person. The garments hold the shape of the A-posed figure from the white-base-costume sheet; the inside is hollow and visible through the neck opening and sleeve ends.

OUTFIT (same design and colors as the reference):
- White frilled blouse front with dark buttons, the white collar, the black bow tie with the round blue gem brooch and the black hanging ribbons.
- Dark navy corset waist with the row of gold buttons, cinched tightly.
- Off-shoulder look: the detached dark-navy puffed sleeves with the small gold cross ornaments and the white frilled cuffs, positioned on the arms of the A-pose, separated from the torso.
- Dark navy skirt with the gold embroidered border, the small black-and-gold bows, and the layered white ruffled petticoat at the hem.
- White apron with the frilled edge and the small dark-blue whale logo; at the back, the large white bow with long hanging tails.

FIT CORRECTIONS (important):
- Skirt length: the bottom of the white ruffles ends AT THE KNEE, not lower.
- Waist: slim and tightly cinched, the narrowest point clearly visible.
- Silhouette: no extra volume in the upper part of the skirt. The skirt flares smoothly from the waist in a clean A-line, with the fullness coming from the petticoat in the lower half.

RENDERING: clean cel-shaded anime illustration, flat even lighting, minimal soft shading, no cast shadows, no glossy highlights, true base colors, crisp edges. Consistent design across all four views.
```

### 3）配件合集，1 张

**参考图**：
- 原立绘
- 第 1 张素体图（可选，用来统一尺寸）

```
Using the uploaded character sheet as the design reference, create one clean product-style reference sheet showing ONLY her separate accessories, for image-to-3D reconstruction. 3:2 canvas, solid flat light-gray background (#C8C8C8), all items at the same real-world scale, each item isolated with large empty space around it, nothing touching or overlapping. No text, no labels, no frames, no shadows. Each item in a clear three-quarter front view unless stated otherwise:

1. The white frilled maid headdress (headband with layered ruffles), as if worn, without a head.
2. The two blue satin hair bows: the bow worn on the right side of the head, and the bow at the back of the braid.
3. Her whale tail, detached at the base, in a clean side view showing the full S-curve: deep navy blue on top, fading to light sky blue towards the wide two-lobed fluke, with small light speckles near the fluke.
4. The pair of glossy dark-navy Mary Jane high-heel shoes with gold round buckles and chunky heels, side by side, empty, no feet.

RENDERING: clean cel-shaded anime illustration, flat even lighting, no cast shadows, no glossy highlights except a subtle shine on the shoes, true base colors, crisp silhouettes.
```

---

## 四、出图后的检查和修正

Sunburst 擅长多轮"只改一处"的编辑。不满意时不要重新生成，在同一个对话里追加修改指令。

| 检查项 | 不合格时追加的修改指令（示例） |
|---|---|
| 四个视图不等高，或有透视 | `Keep everything identical, but make all four views exactly the same height and strictly orthographic.` |
| 脸不像原图 | `Keep everything else unchanged; make the face match the uploaded close-up exactly: eye shape, eye color, lashes, face shape.` |
| 头发又出现碎发或小卷 | `Keep everything else unchanged; simplify the hair into fewer, larger, smooth clumps; remove all small curls and stray strands.` |
| 手臂贴着身体，腋下没空隙 | `Keep everything else unchanged; move the arms further from the torso so there is a clear gap at the armpits.` |
| 裙子还是太长 | `Keep everything else unchanged; shorten the skirt so the ruffle hem ends exactly at the knee.` |
| 衣服图里露出身体 | `Remove all visible skin, hair and body parts; keep only the garments, hollow inside.` |
| 有光泽高光或投影 | `Keep everything identical but flatten the lighting: no specular highlights, no cast shadows, flat base colors.` |

**交给 Tripo 之前**：
- 把 4 视图裁成 4 张。
- 文件名标清楚 `front / left / back / right`。
- 放进 `大肥鱼第二版/生成参考图/`，我可以帮你核对对齐和比例。

---

## 五、风险提示
- **素体带头发**：这次头发是做成大块发束、和后背分开的，Tripo 生成后在 Blender 里比较容易按连通区域把头发和身体分开。如果粘在一起，我可以按颜色和区域切开。
- **鱼尾在配件图里只有一个视图**，单视图重建的质量可能一般。如果效果差，再单独给鱼尾出一张 4 视图。
- **鞋子这次先不用**。先生成出来备用，跑步动作暂时按平脚做。
- 白色内衬（高领上衣和打底裤）在 3D 里直接当作素体表面。原图的白色裤袜正好对应打底裤的腿部；上半身被女仆装盖住，露肩的部分以后在 Blender 里按原图改成皮肤色。
