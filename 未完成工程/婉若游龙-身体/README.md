# 婉若游龙（LTZ）· 身体 + 龙纹网鞋

《明末：渊虚之羽》的「婉若游龙」套装，按"下装换成龙纹网鞋 + 光腿 + 无内裤、保留长裙"改造后的**身体网格**。

## 文件

```
WuchangLTZ_Wangxie.fbx    身体（上装 + 长裙 + 光腿 + 龙纹高跟网鞋）
```

## 它是怎么来的

明末原版「婉若游龙」拆成两件：

```
WuCh_LTZ_Jacket   13 材质槽（含 [8] MI_Head9 / [9] MI_Body9 / [11] MI_Body10）
WuCh_LTZ_Pants     4 材质槽（Xiasheng / Shangsheng / Shoubi / MI_Body）
```

网鞋来自明末侧的第三方 mod `Dragon heels NSFW_p.pak` —— 它不是一双鞋，而是**整件下装的替换**，
只提供 `WuCh_LTZ_Pants.uexp`（没有独立鞋子资产）。所以我们把替换后的下装几何 dump 出来
（28212 顶点 / 76695 索引 / 3 段），按骨名映射到游戏骨架后并进身体：

```
SDtui_* / SHip* / Hip*   → thigh_l / thigh_r
Knee_* / SKnee*          → calf_l / calf_r
Ankle_* / SFoot*         → foot_l / foot_r
Toes_* / ToesEnd_*       → ball_l / ball_r
中线骨（Root/Spine/Chest）→ pelvis
```

实际落到：thigh_l 7174、thigh_r 7583、calf_l 8083、calf_r 8313、pelvis 5705、foot_l 3292、foot_r 3348、ball_l 393、ball_r 368

## 校验结果

- `ReferenceSkeleton` = **1134 根**，无假根骨
- 骨骼顺序 = 游戏原序（`root, pelvis, spine_01 …`）
- 长裙 `Quzi` 段保留；裙下为光腿 + 龙纹网鞋，无内裤
- 鞋底最低点 Z ≈ 1.2 cm（mod 原始网格本身的起点；如果站姿上有点飘，需要整体下压）

## 状态：几何完成，材质未接

- 材质槽按槽名指到作者 mod 里的 `MI_YL_*`（`Shangsheng / Xiasheng / Shoubi / Quzi / ZhuangBei1-3`），
  这些资产**不打包**，运行时从作者的包里解析。
- 但把它作为覆盖包放进 `~mods` 后**不生效**（改成 9 个 z / `zzz0_` 前缀都试过）。
  最可能的原因：作者的包是 `ProjectPBZ/Plugins/GameFeatures/PBZCollectionWardrobe/` 下的
  **GameFeature + Blueprint 组件**（`BPC_CollectionVisual*`），会在运行时把网格改回去；
  单纯在 pak 层抢同名路径没有意义。
  详见 `未完成工程/白衣无常-源模型/文档/HANDOFF-影之刃零MOD技术总览.md` §4 / §8.3。

## 注意

- 材质前缀是 `M_WuCh_LTZ_*`（LTZ = 婉若游龙），不要和 `M_HD_*`（流云织羽，见 `未完成工程/流云织羽-躯干/`）混。
- 骨架容器必须叫 `Armature`，否则 1135 根 → 切外观崩。
