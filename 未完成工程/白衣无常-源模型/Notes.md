# 白衣无常 · 源模型（短发版）

明末《无常》白衣无常服装 → 影之刃零（Phantom Blade Zero）移植用的**源模型**。
已过 Blender 处理，可直接导入 UE 5.7。**只差材质着色**（原因见文末）。

最后更新：2026-11-05 12:00

> 想快速了解全貌，先看 `文档/HANDOFF-影之刃零MOD技术总览.md`（15 章，含全部排查记录、外部资料、工具与结论）。

---

## 文件

| 文件 | 大小 | 内容 |
|---|---|---|
| `Baiyi_Body_ShortHair.fbx` | 18.3 MB | 身体，3 mesh / 18 材质槽 / **1134 骨** |
| `HaiKou_ShortHair_Head.fbx` | 11.7 MB | 头部，取自作者「海寇·明末」包（**原生短发**）/ 10 槽 |
| `tex/` | 40 张 PNG | 明末原版贴图（`_D` albedo / `_N` 法线 / `_R` 粗糙反射），RGBA |
| `文档/` | — | 技术总览、材质排查记录、修复方案 |
| `脚本/` | — | 建材质实例 / 建表 / 重导贴图 |
| `构建/` | — | 历史可安装包（仅供参考，材质未解决） |

---

## 骨架（导入前必看）

```
骨架对象名 = Armature          1134 根
```

三条硬要求，缺一条就出问题：

1. **骨架容器对象必须叫 `Armature`**。UE 只跳过这个名字的容器节点；叫别的（如 `HunSkinSkel`）
   会让 `ReferenceSkeleton` 多生成一根假根骨 → **1135 根** → 切外观时崩
   `0xC0000005 @ +0x306E8CD`。
2. **缩放 ×100**。glTF 是米制、UE 是厘米，不放大头只有 1/100 大。
3. **骨骼顺序必须是游戏原序**：`root, pelvis, spine_01, spine_02, …`
   Blender 过一趟 glTF 会按 DFS 重排（`ik_weapon_root` 跑到第 1 位、`pelvis` 掉到第 16），
   蒙皮会把头顶歪 —— 看起来像「脸朝向错误」，本质是权重挂到了错的骨头上。

本文件已满足全部三条。导入后自检：`bones == 1134` 且第 0 根是 `root`。

---

## 身体材质槽（3 个 mesh，共 18 槽）

### `WuCh_BLYR_Pants` — 16,704 顶点 / 6 槽（下装 + 鞋）

| 槽 | 名称 | 含义 | Albedo | Normal | Mix |
|---|---|---|---|---|---|
| 0 | `MI_zhijia` | 趾甲小片 | — | — | — |
| 1 | `MI_Body.001` | 腿的皮肤 | `T_Skin_Body_D` | `T_BY_FlatNormal` | `T_BY_ORM` |
| 2 | `white` | 鞋面 / 白袜 | `T_BY_white` | 同上 | 同上 |
| 3 | `ih_insoles` | 鞋内底 | `T_BY_insoles` | 同上 | 同上 |
| 4 | `ih_soles` | 鞋外底 | `T_BY_soles` | 同上 | 同上 |
| 5 | `ih_metal` | 细带高跟的金属细带 | `T_BY_metal` | 同上 | 同上 |

### `WUCH_BWC_Jacket` — 31,541 顶点 / 9 槽（上装 + 腰带）

| 槽 | 名称 | 明末原版材质 | Albedo | Normal | Mix |
|---|---|---|---|---|---|
| 0 | `M_HWC_Qunzi` | `M_HWC_Qunzi` | `T_BWC_QZ_D` | `T_BWC_QZ_N` | `T_BWC_QZ_R` |
| 1 | `M_HWC_XiongGu` | `M_HWC_XiongGu` | `T_BWC_XG_D` | `T_BWC_XG_N` | `T_BWC_XG_R` |
| 2 | `M_HWC_YaoDai01` | `M_HWC_YaoDai01` | `T_BWC_YD_D` | `T_BWC_YD_N` | `T_BWC_YD_R` |
| 3 | `M_HWC_LianPI01` | `M_HWC_LianPI01` | `T_BWC_LP_D` | `T_BWC_LP_N` | **`T_BWC_LPJS_R`** |
| 4 | `M_HWC_shoubi` | `M_HWC_shoubi` | `T_BWC_SB_D` | `T_BWC_SB_N` | `T_BWC_SB_R` |
| 5 | `M_HWC_TouGu` | `M_HWC_TouGu` | `T_BWC_TG_D` | `T_BWC_TG_N` | `T_BWC_TG_R` |
| 6 | `MI_Head` | — | 头部由 HeadAsset 提供，此槽可忽略 | | |
| 7 | `MI_Body` | — | `T_Skin_Body_D` | `T_BY_FlatNormal` | `T_BY_ORM` |
| 8 | `invisible` | — | 隐藏段 | | |

> `M_HWC_LianPI01` 的反射图是 `T_BWC_LPJS_R`，不是 `T_BWC_LP_R`。
> 这是明末原版的真实分配，从原包 `wcdump MAT` 逐条读出来的。

### `WUCH_NvJuan_Hands` — 7,127 顶点 / 3 槽（女眷手：裸前臂 + 红绳 + 长指甲）

| 槽 | 名称 | Albedo |
|---|---|---|
| 0 | `M_WCNJ_Jacket` | `T_NVJ_COAT_D` |
| 1 | `MI_ZhiJia_base` | 指甲 |
| 2 | `MI_Body.002` | 手部皮肤 → `T_Skin_Body_D` |

---

## 头部材质槽（`HaiKou_ShortHair_Head.fbx`）

取自作者 `PBZ_Corsair_3304` 包的 `SK_CorsairHead`，**原生短发**，游戏骨架导出
（所以不存在 DFS 重排问题）。原版 13 槽去重后 10 槽：

| 槽 | 名称 | 含义 |
|---|---|---|
| 0 | `MI_FO_bfa4d791a5f2` | 头发（占原版 5 个槽） |
| 1 | `MI_FO_934b31c540d2` | 发饰 |
| 2 | `MI_Wuchang_Brows_67630add` | 眉毛 |
| 3 | `MI_Wuchang_Eye_7f573563` | 眼球 |
| 4 | `MI_Wuchang_Eyelash_5157e96a` | 睫毛 |
| 5 | `MI_Wuchang_Head_eedd7a66` | 脸部皮肤 |
| 6 | `MI_Wuchang_Tear_7427bc8b` | 泪痕 |
| 7 | `MI_teeth_low_2e7ba38b` | 下牙 |
| 8 | `MI_teeth_up_9d491ce7` | 上牙 |
| 9 | `MI_tongue_8777624a` | 舌头 |

原版 13 槽完整顺序（要精确复刻时用）：

```
[0][1][2][4] MI_FO_bfa4d791a5f2   [3] MI_FO_934b31c540d2
[5] Brows  [6] Eye  [7] Eyelash  [8] Head  [9] Tear
[10] teeth_low  [11] teeth_up  [12] tongue
```

---

## 外观表（`DT_PBZAppearanceTable`）

每套服装 **3 行**，靠 ItemId 互相引用：

```
Hun_OutFit_CodexXXX          AppearanceType = Outfit      ← 只声明 ItemId
CodexXXX_Body                AppearanceType = Body        BodyMeshAsset = <身体网格>
CodexXXX_Head                AppearanceType = Hairstyle   HeadAsset     = <头部网格>
```

`EAppearanceType`：0 Body / 1 Hat / 2 Beard / 3 Hairstyle / 4 Outfit / 5 Neck / 6 MeshBand / 7 BrowLashCard

官方预留 5 个 Codex 槽位，资产路径写死 `/Game/Mods/PBZWardrobe/`：

```
CodexFY / CodexFoxRain / CodexSilkCorsair / CodexGoldenTiger / CodexMuXiaoKui
```

---

## 已解决的问题（别再重走）

| 问题 | 原因 | 修法 |
|---|---|---|
| 切外观必崩 `0xC0000005` | 骨架容器名不是 `Armature` → 1135 根假根骨 | 改名 |
| 第二个崩溃原因 | 自建 base Material 的 uniform buffer 求值失败 | 改用 MaterialInstance 指向游戏母材质 |
| 摆大字 + 没动作 + 没头 | 骨架挂载路径写成 `/Game/HuaShira/…` | 应为 `/HuaShira/…`（插件根） |
| 头只有 1/100 大 | glTF 米制未 ×100 | 整体缩放 ×100 |
| 衣柜里看不到新服装 | 缺外观表 | 自建 69 行 `DT_PBZAppearanceTable` |
| 界面文字变 `{ButtonText}` | `~mods` 里任何含 JS 的 pak 都会触发 | 彻底不发 JS |
| 手/前臂在动作里塌陷 | 完全没有 twist 骨权重（作者占 14049 顶点，我们 0） | 按肘→腕参数 t 拆分权重，**每顶点限 4 骨** |
| 启动崩 `Missing global shader` | UAT 把 `Config/DefaultEngine.ini`、`MainStart.js` 等 698 个文件塞进了 `.pak`，顶掉游戏本体 | `.pak` 只留 456 字节占位，资产全走 `.utoc/.ucas` |

---

## 已知问题 / 卡在哪

**唯一未解决：材质实例不着色。** 游戏里表现为均匀金属灰。

已排除（都验证过，不用重走）：贴图内容、alpha、UV、槽位挂载、参数名、表指向。

**根因（有实测数据）：我们的 MI 是空壳**

```
作者可用的 MI   uexp 682 字节
我们 cook 的    uexp 214 字节   ← 没有材质参数，也没有着色器缓存
```

父级指向我们自己造的「同路径但节点是空的」占位母材质。两条可行路径：

1. **在编辑器里复刻母材质** `MAI_Equipment_Mask` 的节点连线：
   `TextureSample(Albedo) → BaseColor`、`Mix 的 R/G/B → Metallic/Roughness/AO`、
   `Normal → Normal`、`Albedo.a → OpacityMask`
2. **复制游戏原版 MI 改名换贴图**（社区标准做法，需 UAssetGUI 手工操作）

---

## 其他已知但未处理

- 手比作者的小约 7%（女眷手为使前臂长度对上骨架做了 `0.9384` 缩放）
- 鞋底已累计抬高 13 mm，若仍偏低需再调
- 手臂已补 `upperarm_twist_01/02`、`lowerarm_twist_01/02` 权重

---

## 工具链的硬边界（实测，别白试）

- **UE 的 UnrealPak 读不了 retoc 产出的 uasset**：把 legacy MI 塞进 Cooked 再 UAT 打包 →
  `LogUnrealNames: Error: String is too long` + `Assertion failed: Header.Len != 0` (UnrealNames.cpp:2422)
- **retoc 读不了 UE cook 产物**：`Extracted 0 (78 failed)`，报缺 `ScriptObjects` chunk，
  加 `--no-script-objects` 也一样
- → **两条链路不能混，必须各自独立打包**

## 另一个坑：UAT 打 iostore 会往 `.pak` 里塞垃圾

```
ProjectPBZ/Config/DefaultEngine.ini       ← 顶掉游戏渲染设置 → skin cache 重置 → 全局 shader 缺失
ProjectPBZ/Content/JavaScript/MainStart.js ← 顶掉游戏主脚本 → UI 文字异常
ProjectPBZ/AssetRegistry.bin
Engine/Content/...（icu 语言包）
698 个文件 / 2.93 MB
```

**必须**用 456 字节的占位 `.pak` 替换（iostore 容器需要同名 `.pak` 才会挂载，但内容不能有东西）。
