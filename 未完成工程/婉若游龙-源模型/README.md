# 婉若游龙 · 源模型（龙纹网鞋 + 光腿 + 无内裤）

《明末：渊虚之羽》的「婉若游龙」（内部代号 `LTZ`）套装，按
**「下装换成龙纹网鞋 + 光腿 + 无内裤、保留长裙」**改造后的身体网格。

已过 Blender 处理，可直接导入 UE 5.7。**只差材质着色**（见文末）。

最后更新：2026-11-05 12:00

---

## 文件

| 文件 | 大小 | 内容 |
|---|---|---|
| `WuchangLTZ_Wangxie.fbx` | 23.0 MB | 身体，2 mesh / 15 材质槽 / **1134 骨** / 137,850 顶点 |
| `HaiKou_ShortHair_Head.fbx` | 11.7 MB | 头部，取自作者「海寇·明末」包（**原生短发**）/ 10 槽 |

> **本目录没有贴图**。作者 `PBZ_WanRuoYouLong_3800` 包里有 24 张 (`_D` / `_N` / `_MR`)，
> 可用 `izprobe TEX` 或 `retoc to-legacy` 提取。

---

## 这一版改了什么

明末原版婉若游龙是「长裙 + 长裤 + 长靴」。这一版：

- **长裙 `WuCh_LTZ_Quzi` 保留**
- 裙下的**长裤、内裤、长靴全部删掉**，换成 `Dragon heels NSFW` 那个 mod 的**龙纹网鞋 + 光腿**
- 手部沿用原版

网鞋的来源是明末社区的一个 mod：

```
~mods/婉若游龙 网鞋/Dragon heels NSFW_p.pak
  → 它只替换 Project_Plague/.../cloth/LTZ/WuCh_LTZ_Pants.uexp
  → 不是「一双鞋资产」，而是「整个下装的网格数据」
```

提取方式：把游戏原包与该 mod 放进同一目录（硬链接即可，不用复制 60GB），
用 `wcdump EXPORT` 导出顶点/三角面/骨骼权重，再在 Blender 里按骨名映射搬权重。

---

## 骨架

```
骨架对象名 = Armature          1134 根          顺序 = 游戏原序
```

三条硬要求（与白衣无常相同）：

1. 骨架容器对象必须叫 `Armature` —— 否则 1135 根假根骨 → 切外观崩 `0xC0000005`
2. 缩放 ×100
3. 骨骼顺序必须是 `root, pelvis, spine_01, spine_02, …`

---

## 材质槽（2 mesh / 15 槽 / 137,850 顶点）

### `WuCh_LTZ_Jacket` — 76,892 顶点 / 10 槽

| 槽 | 名称 | 含义 |
|---|---|---|
| 0 | `M_WuCh_LTZ_Shoubi` | 手臂 |
| 1 | `M_WuCh_LTZ_ZhuangBei1` | 装饰 1 |
| 2 | `M_WuCh_LTZ_Quzi` | 长裙（**保留**） |
| 3 | `M_WuCh_LTZ_ZhuangBei2` | 装饰 2 |
| 4 | `M_WuCh_LTZ_Shangsheng` | 上装 |
| 5 | `MI_Head` | 头部（由 HeadAsset 提供，可忽略） |
| 6 | `MI_Body` | 身体皮肤 |
| 7 | `invisible` | 隐藏段 |
| 8 | `MI_Body1` | 皮肤（第二段） |
| 9 | `M_WuCh_LTZ_Xiasheng` | 下装 |

### `WuCh_LTZ_Hands` — 13,752 顶点 / 5 槽

| 槽 | 名称 | 含义 |
|---|---|---|
| 0 | `M_WuCh_LTZ_Shangsheng.002` | 上装（袖口） |
| 1 | `M_WuCh_LTZ_ZhuangBei` | 装饰 |
| 2 | `M_WuCh_LTZ_Shoubi.001` | 手臂 |
| 3 | `MI_Body.002` | 手部皮肤 |
| 4 | `MI_ZhiJia_base` | 指甲 |

> 材质前缀是 `M_WuCh_LTZ_*`。**不要和流云织羽的 `M_HD_*` 混**。

---

## 网鞋段的骨骼映射（从明末骨名搬到游戏骨架）

明末腿部骨名与影之刃零不同，按规则搬并合并权重：

| 明末骨名 | 游戏骨架 |
|---|---|
| `SDtui_*` / `SHip*` / `Hip*` | `thigh_l` / `thigh_r` |
| `Knee_*` / `SKnee*` | `calf_l` / `calf_r` |
| `Ankle_*` / `SFoot*` | `foot_l` / `foot_r` |
| `Toes_*` / `ToesEnd_*` | `ball_l` / `ball_r` |
| 中线骨（`Root` / `Spine` / `Chest`） | `pelvis` |

实际分到的顶点数：

```
thigh_l 7174  thigh_r 7583  calf_l 8083  calf_r 8313
pelvis  5705  foot_l  3292  foot_r  3348  ball_l 393  ball_r 368
```

鞋底最低点 Z ≈ 1.2 cm（mod 原始网格的起点）；若站姿飘，整体下压即可。

---

## 外观表

每套 3 行：

```
Hun_OutFit_CodexWanRuoYouLong     AppearanceType = Outfit
CodexWanRuoYouLong_Body           AppearanceType = Body        BodyMeshAsset = SK_WanRuoYouLongBody
CodexWanRuoYouLong_Head           AppearanceType = Hairstyle   HeadAsset     = SK_WanRuoYouLongHead
```

作者原版表是 **108 行**，比游戏原版 69 行多出 25 套服装 × 3 行。

---

## 已知问题

**材质不着色。** 与白衣无常同一根因：

```
作者可用的 MI   uexp 682 字节
我们 cook 的    uexp 214 字节   ← 没有材质参数，也没有着色器缓存
```

**但这一套有一个额外的好消息**：作者的 `MI_YL_*` 是**完好的**（父级指向游戏真母材质，
参数齐全）。所以最省事的做法不是自己造 MI，而是：

1. `retoc to-legacy` 从作者包提取 9 个 `MI_YL_*` + 24 张贴图 + 头部
2. 用 `retoc to-zen` 单独打一个「素材包」
3. 我们自己的网格 + 外观表用 UAT 打另一个包
4. 两个包放一起（素材包名字排在后面，覆盖网格包里的占位 MI）

**这就是我们目前采用的方案**，两个包各自用各自可靠的工具，互不混用文件。

---

## 工具链硬边界（实测，别白试）

- UE 的 UnrealPak **读不了** retoc 产出的 uasset（`String is too long` / `Header.Len != 0`）
- retoc **读不了** UE cook 产物（`Extracted 0 (78 failed)`，缺 `ScriptObjects`）
- → 两条链路不能混，必须各自独立打包
- UAT 打 iostore 会往 `.pak` 里塞 `Config/DefaultEngine.ini`、`MainStart.js` 等 698 个文件，
  顶掉游戏本体 → 启动崩 `Missing global shader`。**`.pak` 必须只留 456 字节占位**。
