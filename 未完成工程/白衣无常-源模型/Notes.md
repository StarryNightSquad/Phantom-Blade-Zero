# 白衣无常（明末无常）→ 影之刃零 · 移植工程留档

最后更新：2026-11-05 05:10
用途：请人帮忙诊断 / 接手修正用。**不是可直接安装的 mod**，是可以直接导入 UE 的源资产 + 当前构建。

> 想快速了解全貌，先看 `文档/HANDOFF-影之刃零MOD技术总览.md`（15 章，含全部排查记录、外部资料、工具与结论）。
> 本文只写"这套东西是什么、现在到哪一步、卡在哪"。

---

## 一、这套东西是什么

把《明末：渊虚之羽》主角无常的服装，做成影之刃零的**独立新增外观**（不替换原版，且不依赖其他服装 mod）。

| 部位 | 来源 | 备注 |
|---|---|---|
| 上装 | 明末 白衣无常（内部材质名 `M_HWC_*`） | **肩上骷髅已删**（含舌头，52558 → 46002 面） |
| 小臂 / 手 | 明末 女眷套 | 裸前臂 + 腕上红绳 + 长指甲，按游戏骨架重绑，缩放 0.9384 |
| 下装 | 细带高跟 + 光腿 | 无内裤 |
| 鞋 | 白色细带高跟 | 鞋底 Zmin = −4.360（累计抬高 13mm，**还想再抬 5mm**） |
| 头 / 发型 | 织绣海寇的头部 | 马尾沿轴缩短到 k=0.34 |

> 关于缩写（我们踩过坑，写清楚）：海寇 = `Base`；**`HWC` = 夜行无常（黑衣）**；**`BWC` = 白衣无常**。
> `M_HWC_*` 这个材质槽名前缀是明末原版就有的（黑白无常共用同一套网格），不是我们起的。

---

## 二、目录结构

```
Baiyi_Final.fbx          身体（17 材质槽 / 54927 顶点）        ← 已删骷髅的版本
Baiyi_Head.fbx           头部（10 材质槽 / 42263 顶点）
tex/                     40 张贴图
    _D                    明末原版 albedo
    _N                    明末原版法线（本次新增，之前只有 _D）
    _R / _LPJS_R          明末原版粗糙-反射图（本次新增）
    T_BY_*                自己做的通用图（纯色 / 平法线 / ORM）
流云织羽-躯干/
    WuchangLiuyun_Body_fix.fbx    流云织羽（HD）躯干，骨架已改名 Armature、1134 根、顺序=游戏原序
婉若游龙-身体/
    WuchangLTZ_Wangxie.fbx        婉若游龙（LTZ）身体 + 龙纹网鞋/光腿/无内裤（保留长裙）
文档/
    HANDOFF-影之刃零MOD技术总览.md    ← 全量技术与排查记录（建议先读）
    PROGRESS_材质排查.md              ← 早期材质专项排查
    修复方案.md                       ← 你给的诊断，我们逐条实测后的对照
构建/
    PBZ-白衣无常-金虎槽-v25.zip       ← 当前可安装构建（~mods 三件套）
脚本/
    mats_mi.py            建 27 个材质实例（参数表在这里）
    make_master_mask2.py  建占位母材质（**含 Material Usage 标记，v25 新增**）
    build_dt.py           建 69 行外观表
    reimport_tex.py       强制重导贴图
```

三个 FBX 都已经：
- 骨架容器节点改名为 **`Armature`**（UE 只跳过叫这个名字的容器节点，否则会多生成一根假根骨 → 1135 而不是 1134 → 切外观必崩）
- 单位 ×100（glTF 米制 → UE 厘米）
- 导出参数：`axis_forward='Y'`, `axis_up='Z'`, `apply_scale_options='FBX_SCALE_ALL'`, `add_leaf_bones=False`

---

## 三、导入方式（我们用的）

- 骨架：`/HuaShira/Characters/Hero/Hero_Hun/Hun_Skin_Skeleton`（**插件根，不是** `/Game/HuaShira/...`）
  - 必须用 `unreal.load_asset()` 取骨架；`EditorAssetLibrary.load_asset` 对插件内容返回 None，
    结果 UE 会自动新建一个 `_Skeleton`，白折腾
- 导入后校验：`ReferenceSkeleton` 应为 **1134 根、第 0 根是 `root`**
- 外观：`DT_PBZAppearanceTable` **三行一组**（Outfit 行只写 ItemId，Body 行给 `BodyMeshAsset`，Head 行给 `HeadAsset`）
- 材质：每槽一个 `MaterialInstanceConstant`，父级
  `/AkashaEffects/MaterialLibrary/Template/Character/MAI_Equipment_Mask`
- 打包：`~mods` 三件套（`.pak` 几百字节 + `.utoc` + `.ucas`），文件名带 `_P`

---

## 四、材质参数（照 `PBZ_WanRuoYouLong_3800` 的 `MI_YL_Shangsheng` 填）

```
Scalar(19): ReplaceAlpha=0  Normal Strength=1  AO Min=0  AO Exponent=1
            Roughness Min=0  Roughness Max=1  Roughness Exponent=1
            Metallic Min=0   Metallic Max=1   Specular=0.5
            Mask Sharpness=0 Mask Bias=0      Mask Final Multiply=1
            Tile=1 Tile_U=1 Tile_V=1 Tile ApplyObjectScale=0
            Use UV2 (For Scene Materials)=0   OpacityThreshold=0.3333
Vector(5):  AO Channel=0000FF  Roughness Channel=00FF00  Metallic Channel=FF0000
            Albedo Controls=FFFFFF  Albedo Overlay=BCBCBC
Texture(3): Albedo / Normal / Mix
```

`T_BY_ORM` 按 **MRA** 打包（R=Metallic(0)、G=Roughness(179)、B=AO(255)），与通道向量一致。
原版各部位的 D/N/R 对应关系（从明末原包读出来的）：

| 部位 | Albedo | Normal | Mix |
|---|---|---|---|
| 裙 | BWC_QZ_D | BWC_QZ_N | BWC_QZ_R |
| 胸骨 | BWC_XG_D | BWC_XG_N | BWC_XG_R |
| 腰带 | BWC_YD_D | BWC_YD_N | BWC_YD_R |
| 脸皮 | BWC_LP_D | BWC_LP_N | **BWC_LPJS_R** |
| 手臂 | BWC_SB_D | BWC_SB_N | BWC_SB_R |
| 头骨 | BWC_TG_D | BWC_TG_N | BWC_TG_R |

---

## 五、当前卡住的问题（重点）

### 1. 材质不生效 —— 游戏里是整体均匀灰白（有高光），只有头发有颜色

**已经逐条排除、不用再查的**（都有工具输出为证，详见 `文档/HANDOFF…md` §5/§7）：

- 贴图内容：从成品 pak 解出来的 RGB 与源图逐像素一致；alpha 全 255
- UV：身体 17 段逐段验过，U/V 都在 0~1，唯一值 86~2536 个
- 材质挂载：运行时实测 17 槽 / 10 槽全部指向我们的 `MI_BY_*`，类型是 `MaterialInstanceConstant`（不是 DefaultMaterial）
- MI 参数：从成品里读出来，与 `MI_YL_Shangsheng` 逐项一致（19 标量 / 5 向量 / 3 贴图）
- 父级路径：游戏里真实存在 `ProjectPBZ/Plugins/AkashaEffects/Content/.../MAI_Equipment_Mask.uasset`，与我们 MI 里的引用逐字相同
- 外观表不覆盖材质：官方表里 `OverrideMaterials`、`MI_` 字符串都是 -1
- 虚拟纹理：官方服装贴图 `T_ZeroHun_Cloth_01_ARM` 的 uasset 里**没有** `VirtualTextureStreaming`（不是 VT），
  而作者的贴图**是** VT。两种都能用，不是关键
- 占位母材质没被打进包：容器清单 119 条，`Akasha` 命中 0

**v25 刚做的一处改动（重点，请帮忙判断对不对）**

`make_master_mask2.py` 里以前只设了 `blend_mode` 和 `opacity_mask_clip_value`，
**从来没有设过 Material Usage**，所以占位母材质的 `bUsedWithSkeletalMesh = False`。

我们的理解是：cook 时这个标记会写进每个 MIC 的 `FMaterialCachedExpressionData.RuntimeMaterialUsage`，
运行时组件判"该材质能否用于骨骼网格"，拿到 false 就退回 `DefaultMaterial`——现象正好对得上
（不报错、无紫红格子、一片均匀灰白、参数怎么改都不生效）。

已补：

```python
for _flag in ("used_with_skeletal_mesh", "used_with_static_mesh",
              "used_with_instanced_static_meshes",
              "used_with_particle_sprites", "used_with_morph_targets"):
    mat.set_editor_property(_flag, True)
```

重建后重新 cook，成品里 MIC 的体积变了，可作为"改动确实落进 cooked 资产"的旁证：

```
MI_BY_M_HWC_Qunzi.uexp     4687 → 8095 字节  (+3408)
MI_BY_M_HWC_Qunzi.uheader  2033 → 2310 字节
```

（此前 v13~v24 这个文件一直是 4687 字节纹丝不动，说明那些版本的改动根本没进到资产里。）

**这一版尚未实机验证。** 如果还是灰，我们下一个怀疑对象是"MIC 是编辑器里从空 MI 新建、父级指向自建占位母材质"
——也就是你 `修复方案.md` 第 2.4 节说的那条。我们正在按那个方向改用 `retoc to-legacy → UAssetGUI → retoc to-zen`
直接复制游戏自带的 `MI_ZeroHun_Cloth_01_b` 改名换贴图。

### 2. 头部朝向错 —— 游戏里面朝身体右侧（马尾方向是对的参照）

原因已定位为**骨骼顺序被打乱**（不是位置、不是权重）：

```
我们的头 SK_GoldenTigerHead    0 root 1 ik_weapon_root 2 ik_weapon_r … 16 pelvis   ❌
海寇原头 SK_SilkCorsairHead    0 root 1 pelvis 2 spine_01 …                        ✅
我们的身体 SK_GoldenTigerBody  0 root 1 pelvis 2 spine_01 …                        ✅
```

骨骼总数都是 1134。头部走的是 glb 自带骨架（Blender/glTF 按 DFS 重排），
身体走的是 `Hun_Skin_Skeleton.fbx` 的原始顺序。
另外用 Kabsch 配准验过：**绑定姿势下几何与海寇原头逐顶点一致（rms < 0.1）**，
蒙皮权重的支配骨分布也完全相同——所以**几何没问题，纯粹是骨骼索引错位**。

### 3. 前臂错乱

女眷手是按"肘→腕相似变换"搬的权重（缩放 0.9384），可能少了一节。

### 4. 鞋底还想再抬约 5mm

（目前是改网格顶点；你建议过"不要动网格"，我们想听听更好的做法。）

---

## 六、想请教的三件事

1. **我们这套 MI 为什么在游戏里不上色？**
   除了"父级是自建占位母材质"，还有别的差异吗？
   你们的 MI 名称表里带着 `MI_ZeroHun_Cloth_01_b` 和 `T_ZeroHun_Cloth_01_ARM/_BC/_N`，
   看起来是**拿游戏自带 MI 复制改名再换贴图**。是不是必须这么做，编辑器里新建的 MI 一定不行？
   （也想确认：是不是只要 MI 的 `FMaterialCachedExpressionData` 来自非真母材质，就必然绑不上参数。）

2. **头部怎么做才能保证导入后骨骼顺序和游戏骨架一致？**
   我们目前是"网格来自 glb、骨架来自 `Hun_Skin_Skeleton.fbx`、按骨名搬权重"，
   Blender 侧只要经过 glb 往返就会把骨骼按 DFS 重排。有没有更稳的做法
   （比如直接 PSK 链路，或者导入 UE 后用 Skeleton 重建）？

3. **同一个外观表被多个包提供时，你们的合并规则是什么？**
   我们在 `~mods` 里同时放了你们的 9 个辅助包（`PBZCollectionWardrobe` 系列）和我们自己的表，
   怀疑互相覆盖。说明里写"本批次共用相同外观表 + 通过各包自己的标记只显示已安装的新外观"，
   这个"标记"是指 `Content/Mods/PBZCollectionWardrobe/DT_CollectionGrants` 吗？

---

## 七、其他备注

- 运行环境：Steam 版，UE **5.7.4**
- 我们自己写的两个读取工具（CUE4Parse）：PBZ 侧 `izprobe`、明末侧 `wcdump`，
  能读游戏本体全部资产（AES key 见 `文档/HANDOFF…md` §2.2）。需要哪个资产的具体数值，我们可以直接给。
- 已确认：`~mods` 里**任何含 JavaScript 的 .pak** 都会让 UI 文字变成 `{ButtonText}`（游戏 11-04 更新后）。
  所以我们的包一个 JS 都不带。
