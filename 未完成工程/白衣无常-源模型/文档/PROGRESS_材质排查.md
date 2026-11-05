# 白衣无常移植 · 完整进度与关键记录

> **本文档是过程记录**，含大量试错历史。
> **当前最终方案请以同目录 `技术说明.md` 为准。**
> 已按最新状态校正：装配方案表、骷髅删除面数。

> 最后更新：2026-11-04 21:40
> 工作目录：`E:/steam/steamapps/common/PBZ/workbuddy/`
> 当前版本：**v23**（`builds/PBZ-白衣无常-金虎槽-v23.zip`，已部署 `~mods/zzzzzzzz_PBZ_Baiyi_3001_P`）

---

# 第一部分 · 任务与总体设计

## 1.1 目标

把《明末：渊虚之羽》主角无常的服装，移植成《影之刃零》(ProjectPBZ) 里**独立新增**的可穿外观，**不替换**原版服装。

## 1.2 四套计划

| 套装 | 服装来源 | 鞋 | 备注 |
|---|---|---|---|
| 流云织羽 | 明末 HD 套 | 原版长靴 | 已出包 v2 |
| **白衣无常** | 明末 | 细带高跟光腿 | **当前在做**，无内裤 |
| 婉若游龙 | 明末 LTZ 套 | 网鞋 | 已出包 v1 |
| 执念心魔 | 明末全套 | — | 含斗笠 + 脸部 DNA，排最后 |

通用要求：保留头部、发色黑、修地陷、四套各自独立可共存。

## 1.3 白衣无常的最终装配方案（用户逐条确认过）

| 部位 | 用的东西 | 关键参数 |
|---|---|---|
| 上装 | 明末白衣无常原件（肩甲、骷髅护肩、上臂骨饰、肘护臂、裙摆、腰间红穗） | 骷髅已删 |
| 腰带 | 同一件，但**正面骷髅 + 舌头 + 牙齿一起删** | 只删中轴 30 个连通块 / 2993 面，肋骨完好 |
| 小臂/手 | 明末**女眷套**的整只手：裸前臂 + 腕上红绳 + 长指甲 | **整件替换，不缩放**（rigid 模式：顶点只 ×100，权重按骨名映射） |
| 下装 | 细带高跟 + 光腿，**无内裤** | — |
| 鞋 | 白色细带高跟 | **未做抬高**，交由封包侧决定 |
| 头 | 影之刃零 Mod 的**海寇短发头** `SK_CorsairHead` | **独立 FBX 交付**，便于换成对方自己的头 |
| 外观槽 | 借用官方预留的 Codex 槽（第 6、7 个已解锁） | 名字显示「？？？？」属正常 |

---

# 第二部分 · 已经彻底解决的问题（**不要再回头怀疑**）

## 2.1 切外观必崩 `0xC0000005 @ PBZ.exe+0x306E8CD`

**现象**：衣柜里一切换到我们的服装，游戏立刻退。

**排查链**（可复用）：
1. `tools/dmp_parse.py` 手工解析 Minidump → 寄存器 + 栈 + 模块。
2. 反汇编 `tools/pe_dis.py <exe> <va> before after`（capstone + `.pdata` 取函数范围）→ 指令 `mov rdx,[rsi+rdx*8]`，`rsi=[r15+0x10]` 为 null、index=0 → 空数组索引。
3. 真正定位靠**横向对比**：给 izprobe 加 `REFB` 模式 dump 每个网格的 `ReferenceSkeleton`，对比 4 个能用的 mod：
   - 能用的全部 `COUNT=1134`，第 `0 root -1`
   - 我们 `COUNT=1135`，第 `0 HunSkinSkel -1` / `SK_SilkCorsairHead_ao -1` → **整套骨骼索引整体 +1**

**根因**（UE 官方行为，实测三条）：
- UE 只把**名字为 `Armature`** 的骨架容器节点跳过；
- 叫别的名字（`HunSkinSkel`）→ 额外生成一根骨头；
- 把骨架对象改名成 `root` → 更糟，得到 `root, root1`（重名自动加后缀）。

**修法**：`tools/bl_export_fbx.py` / `bl_export_head.py` 导出前 `arm.name = "Armature"`。

## 2.2 第二个崩溃根因：自建 base Material

**证据**：`tools/pe_str.py` 扫调用栈上位函数 `0x143077310`，命中字符串
`no static UB struct with this hash - likely a per-material uniform buffer`
→ 崩在**材质 uniform buffer / uniform expression 求值**里。

**横向对比**：能用的 mod（金虎/方瑶/白赤练/FoxRain/SilkCorsair）材质**全是 `MaterialInstanceConstant`**，
父级指向游戏自带模板 `/AkashaEffects/MaterialLibrary/Template/Character/...`，着色器全由游戏提供。
我们从 v1 到 v10 一直是**自建 base Material**（自己烤着色器）—— 这是唯一贯穿所有失败版本的常量。

**结论：材质必须是「材质实例 + 游戏母材质」，不能自建 Material。**

## 2.3 摆大字 + 没头 = 骨架挂载路径错了根

游戏把角色内容做成了**插件**：`ProjectPBZ/Plugins/HuaShira/Content/...`
→ 运行时挂载点是 **`/HuaShira/...`**，不是 `/Game/HuaShira/...`。
我们工程把骨架放在 `Content/HuaShira/...`，cook 出来是 `/Game/HuaShira/...` → 游戏里不存在
→ SkeletalMesh 绑不到骨架 → 停在绑定姿势（大字），头部网格同样失效。

**正确做法**（与能用的 SilkCorsair 一致）：
1. 建占位插件 `Plugins/HuaShira/HuaShira.uplugin`（`CanContainContent=true`），把 `Hun_Skin_Skeleton.uasset` 放进 `Plugins/HuaShira/Content/Characters/Hero/Hero_Hun/`。
2. 导入网格时 `SKEL="/HuaShira/Characters/Hero/Hero_Hun/Hun_Skin_Skeleton"`，且**必须用 `unreal.load_asset()`**（`EditorAssetLibrary.does_asset_exist` 走 AssetRegistry，插件内容没被扫描时返回 None，UE 会**自动新建一个 `_Skeleton`**，白折腾）。
3. 校验：网格 uasset 名称表里出现 `/HuaShira/...Hun_Skin_Skeleton` 且不含 `/Game/HuaShira`。

## 2.4 头只有 1/100 大

glTF 是米制，`bl_export_head.py` 导出时没 ×100 → 包围盒只有 0.13cm。
修法：导出前 `arm.scale=(100,100,100)` 再 apply。校验：头 BOUNDS X ≈ 12.79（与官方头一致）。

## 2.5 衣柜看不到我们的服装 → 缺外观表

见第三部分 3.1。

## 2.6 界面文字全变成 `{ButtonText}`

见第三部分 3.2。

## 2.7 文件"自己消失"

`Data/games/phantom-blade-zero/mods.json` 是 UEModManager 的清单。我们那条 `PBZ-白衣无常-金虎槽-v16` 是 `enabled:false`，
所以**手动放进 ~mods 的文件会被它同步清掉**。对策：文件名换代（2402→3001）绕开旧记录，并让用户在管理器里删掉旧条目。

## 2.8 鞋底地陷

| | 鞋底 Zmin |
|---|---|
| 原 mod `SK_SilkCorsairBody` | −4.36 cm（作者按高跟姿态重建） |
| 我们最初的明末身体 | +1.98 cm（悬空） |

做法：`tools/bl_heel_fix.py` 只把 **Z < 25cm 的脚部顶点**沿踝做 smoothstep 下移；
后来累计再抬 13mm（`tools/bl_shift_z.py`，整体平移不影响蒙皮）。
当前 **Zmin = −4.360**，用户最新要求「再抬约 5mm」。

## 2.9 骷髅删除

`M_HWC_LianPI01` 段里骷髅是独立连通块，**精确删除 30 个连通块 / 2993 面**：
骷髅 1162 + 下颌 507 + 舌头 284 + 上牙 236 + 眼窝 256 + 牙床 180 + 26 个小碎块。

**关键：必须同时限定 `|x| < 2cm`（中轴）。**
只用 `y < -0.09` 会连**肋骨前半部分**一起切掉 —— 曾因此误删 5468 面，渲染时肋骨看着像整组消失。
限中轴后肋骨完整保留。

另外顺带删掉 `invisible` 材质（1088 面）。
脚本：`remake/scripts/build.py` 的 `cut_islands()`（`cx_abs_lt` 参数）。

## 2.10 iostore 挂载

`.utoc/.ucas` **必须有同名 `.pak`** 才会被游戏挂载（内容可以是空的/只放一个占位文件）。
我们的 `.pak` 只有 521 字节（一个 `Pad.txt` 占位）。

---

# 第三部分 · 外观表 / UI / 打包（体系性结论）

## 3.1 外观表 `DT_PBZAppearanceTable`

- 路径 `/Game/PBZContent/DataTable/UI/DT_PBZAppearanceTable`，**原版 69 行 × 35 字段**，
  行结构 `/Script/ProjectPBZ.PBZAppearanceStruct`
- **每套服装 3 行一组**（v18 才彻底搞清）：

| 行名 | AppearanceType | 关键字段 |
|---|---|---|
| `Hun_OutFit_CodexXXX` | Outfit | 只写 `OutfitBodyItem` / `OutfitHairStyleItem` 指向另外两行，**自己不带网格** |
| `CodexXXX_Body` | Body | `BodyMeshAsset` = 身体网格 |
| `CodexXXX_Head` | Hairstyle | `HeadAsset` = 头部网格 |

- `EAppearanceType`：0 Body / 1 Hat / 2 Beard / 3 Hairstyle / 4 Outfit / 5 Neck / 6 MeshBand / 7 BrowLashCard
- 文字字段是 `FlowLocText { Namespace, Key, ValueCache }`，不是 FText
- **官方在 11-04 更新后本来就预留了 5 个 Codex 槽位**，资产路径写死为 `/Game/Mods/PBZWardrobe/...`
  （CodexFY / FoxRain / SilkCorsair / GoldenTiger / MuXiaoKui）。**这就是官方留给 mod 的接口**，不需要自己新增行。
- 未解锁的槽位渲染成**纯灰模 + 名字「？？？？」**（不是材质坏）
- 解锁状态存在存档的 `OwnedOutfits` 里，**数据表管不了，也无法离线判断哪几个已解锁**
- 名字是问号的原因：zh-Hans 的 `Game.locres` 里**没有任何 `Mod_Codex*` key**（提取 1.2MB locres 全文确认过）
- 纯内容工程造不出这张表（行结构是原生 C++）；`ueproj/` 里加了同名 C++ 模块复刻 35 字段，
  用 `ueproj/build_dt.py` 生成整表（69 行原样 + 我们附加的行），cook 后**整表覆盖**。
- ⚠️ **表里没有任何材质引用**：官方表 uasset 里 `OverrideMaterials`/`MI_` 字符串均为 -1，
  说明**外观系统不覆盖材质**，材质完全来自网格自己（已实测确认，见 4.3）

## 3.2 UI 文字变 `{ButtonText}`

**实测规律（4 个独立样本完全一致）**：

| mod | 带 UI/JS 数 | 是否损坏界面 |
|---|---|---|
| zzz_PBZ_WuchangVoice_999_P | 0 | ✅ 正常 |
| zzzzz_PBZ_FoxRain_2208_P | 4 | ❌ 坏 |
| zPBZCenteredShaChi_999_P | 1（只有一个 PlayerHpBar.js） | ❌ 坏 |
| zHuanGui_Outerwear_999_P | 0 | ✅ 正常 |
| 我们 v16 | 4 | ❌ 坏 |

- 字节比对：我们的 `MainStart.js` 与游戏当前版**前 77297 字节完全一致**，只多追加 280 字节 → 内容没问题
- 且 `ProjectPBZ/Saved/BaiyiAppearance.log` **根本没生成** → JS 从未执行
- **结论：只要 ~mods 的 pak 里出现 JavaScript 条目这件事本身，就会把整个 UI 顶成 {ButtonText}**
- 试过"打 UIFix 补丁盖回去"，**不生效**（pak 里 JS 的覆盖优先级不按文件名）
- **最终结论：彻底不发 JS。v23 的 pak 只有 521 字节的占位文件。**

## 3.3 打包链路（最终版，照着跑）

```
1) UE:  build_baiyi2 → head_import → head_mats → mats_mi → make_vt3 → fix_phys2
2) cook: UnrealEditor-Cmd -run=cook -targetplatform=Windows -unattended -nop4 -stdout
   （必须重定向临时目录：TMP/TEMP=D:/UETemp，UE-LocalDataCachePath=D:/UEDDC）
3) 移到树外（**每一条都必要**）：
     mv Cooked/Windows/Engine                                   → 树外
     mv Cooked/Windows/ProjectPBZ/Plugins                       → 树外
     mv Cooked/Windows/ProjectPBZ/Content/ShaderArchive-*       → 树外
     mv Cooked/Windows/ProjectPBZ/Content/ShaderAssetInfo-*     → 树外
     rm -rf Saved/StagedBuilds
4) RunUAT BuildCookRun -skipcook -stage -pak -iostore -utf8output -unattended
5) 取 StagedBuilds/Windows/ProjectPBZ/Content/Paks/ProjectPBZ-Windows.utoc/.ucas
   改名成 zzzzzzzz_PBZ_Baiyi_<版本号>_P.utoc/.ucas
6) UnrealPak 另打一个只有占位文件的 legacy .pak（同名）
7) tools/pack_baiyi16.py 封 zip
```

**校验标准**：
- 容器里 `Engine/*` 条目数必须为 **0**
- 容器里 `AkashaEffects` 条目数必须为 **0**
- ucas 应 ≈19MB；若 139MB 说明 shader archive 没移走
- 111 条资产左右

**UnrealPak 打 legacy .pak 的正确姿势**（踩过很多次）：
- 清单文件用 **LF 换行**（不能 CRLF，否则 0 files）
- 源路径写**绝对路径**
- dest 写 `..\..\..\ProjectPBZ\...`
- **首行必须放一个 `..\..\..\Engine\Pad.txt` 占位**，否则 mount point 推断错
- 输出文件先删，否则报 `File already exists`
- 本机 UE5.7 的 `-iostore` 参数**不生效**，只会出 legacy pak；iostore 容器必须走 UAT

## 3.4 材质体系（前面几轮的结论，仍然成立）

- 母材质只有两个真能用：
  - `/AkashaEffects/MaterialLibrary/Template/Character/MAI_Equipment_Mask` ← **装备类用这个**
  - `/AkashaEffects/MaterialLibrary/Template/Character/MAI_Skin` ← 皮肤
  - （`MAI_Equipment` 少了 `_Mask`，是基础模板，用它 = 灰）
- `bShareMaterialShaderCode` **必须是 `True`**，且**两个 ini 都要改**：
  - `ueproj/ProjectPBZ/Config/DefaultGame.ini` → `[/Script/UnrealEd.ProjectPackagingSettings]`
  - `ueproj/ProjectPBZ/Config/DefaultEngine.ini` 里也有一份会覆盖
- 判定着色器是否被内联：看 MI 的 uasset 体积。官方 MI ≈1.4KB/3.2KB；我们 v21 是 **9,695 字节**（内联了），v22 起降到 2.6KB 级
- 占位插件 `Plugins/AkashaEffects`（`make_master_mask.py` 建的假母材质，**只为 cook 时路径对得上，绝不随包发**）
- 编辑器里 `EditorAssetLibrary.does_asset_exist("/AkashaEffects/...")` 会返回 False（AssetRegistry 没扫到），**必须用 `unreal.load_asset()`**

---

# 第四部分 · 唯一未解决问题：材质不生效（全灰）

## 4.1 现象（v23 实机）

- 模型能出、位置对、解锁槽对、动作正常
- **只有头发有颜色，而且是棕色**（不是我们指定的黑色）
- 其余全部灰，包括裙摆的白色纸钱（表现为灰方块）
- 附带两个非材质问题：面部朝向/五官错乱、前臂错乱

## 4.2 关键推断：我们的 MI 一个都没生效

头发是 **Groom**，走的是游戏自带那套 `MA_HairSheet` 材质 —— 这正是它是全场唯一有颜色的东西的原因。
我们给头发配的 `MI_BY_MI_BlackBraid` 贴的是 `T_BY_black`（实测 avg = 24,24,26 的真纯黑）；
**它要是生效了，头发就该是黑的，而不是现在这个棕色。**

→ 所以**不是"材质部分可用"，而是"我们的 MI 全都没被用上"**。

## 4.3 这一轮离线验证的硬事实（**全部没有启动游戏**）

### ① 我们有 AES key，可以完整读取游戏本体资产
- key：`0x4BC8A51E5381325073F2BC7D4E3089CD557C4E9B7D453901C2C795518867E01D`
- **`UnrealPak.exe -cryptokeys=Crypto.json` 读不了**（它按 KeyChain 格式解析，报 `Key.Num() == 32` 断言）
- **但 `tools/izprobe`（CUE4Parse）能读**，路径写成不带前导 `/` 的
  `ProjectPBZ/Content/...` 相对路径，共可见 **312,820 个文件**
- 模式：`LIST / DTLS / MESH / REFB / MAT / PARAM / RAW / TEX / EXPORT / GET / LS / ROWJSON / ENUM / TAGS`

### ② 网格的材质挂载完全正确
```
izprobe MESH ProjectPBZ/Content/Mods/PBZWardrobe/Meshes/SK_GoldenTigerBody
  CLASS SkeletalMesh
  SKELETON Hun_Skin_Skeleton
  REFBONES 1134
  PHYSICS  null
  MATSLOTS 17
    slot[0] MI_BY_M_HWC_Qunzi      slot[1] MI_BY_M_HWC_XiongGu
    slot[2] MI_BY_M_HWC_YaoDai01   slot[3] MI_BY_M_HWC_LianPI01
    slot[4] MI_BY_M_HWC_shoubi     slot[5] MI_BY_M_HWC_TouGu
    slot[6] MI_BY_MI_Head          slot[7] MI_BY_MI_Body_7
    slot[8] MI_BY_MI_zhijia        slot[9] MI_BY_MI_Body_9
    slot[10] MI_BY_white           slot[11] MI_BY_ih_insoles
    slot[12] MI_BY_ih_soles        slot[13] MI_BY_ih_metal
    slot[14] MI_BY_M_WCNJ_Jacket   slot[15] MI_BY_MI_ZhiJia_base_15
    slot[16] MI_BY_MI_Body_16
  LOD0 verts=54927 sections=17
  BOUNDS X=54.338 Y=20.998 Z=85.084
  Skeleton = /HuaShira/Characters/Hero/Hero_Hun/Hun_Skin_Skeleton
```
→ **17 个槽全部指着我们的 MI**，没有一个是占位材质 `M_BY_*`。**"网格指向错误"这条线排除了。**

### ③ MI 本身也是对的
```
izprobe RAW ProjectPBZ/Content/Mods/PBZWardrobe/MaterialInstances/MI_BY_M_HWC_Qunzi
  Parent  = /AkashaEffects/MaterialLibrary/Template/Character/MAI_Equipment_Mask   ✅
  贴图     = T_BY_FlatNormal / T_BY_ORM / T_BWC_QZ_D                                ✅
  参数     = Albedo, Albedo Controls, Albedo Overlay, AO Min, Metallic Max/Min,
             Mix, Normal, Normal Strength, OpacityThreshold, Roughness Channel,
             Roughness Exponent/Max/Min, Specular
```

### ④ 我们的参数名**大部分确实存在**于真母材质里
直接 dump 游戏本体的 `MAI_Equipment_Mask`（388,645 字节，自带完整 shader map）：
```
存在：Albedo / Mix / Normal / Albedo Controls / Albedo Overlay / AO Min /
      Metallic Max / Metallic Min / Normal Strength / Roughness Channel /
      Roughness Exponent / Roughness Max / Roughness Min / Specular /
      Snow_masks / RefractionDepthBias / Placeholder_Mask / Placeholder_Normal
不存在：OpacityThreshold (-1)  OpacityMaskClipValue (-1)
```
→ `OpacityThreshold` 是 UE 早期版本的属性，现在叫 `OpacityMaskClipValue` 且是 MI 级属性；
两个名字在母材质里都找不到，**我们设的这个参数完全无效（无害但无用）**。

### ⑤ ⚠️ 官方 MI 在同一个母材质上只设 4 个参数
```
izprobe RAW .../Hun_New_V2b/Material/MI_ZeroHun_Cloth_01_b   →  1,392 字节
  参数：Albedo / Mix / Normal / RefractionDepthBias
  贴图：T_ZeroHun_Cloth_01_ARM / _BC / _N
  父级：/AkashaEffects/MaterialLibrary/Template/Character/MAI_Equipment_Mask
```
对照 `MI_ZeroHun_Cloth_02_b` / `04_b` 的参数名表：
`Albedo, BaseColor Intensity, ColorTiling, DetailColor, DetailNormal(VT)/(NonVT), Disable VT,
 Mix, Normal, NormalIntensity, NormalTiling, Overlay, Placeholder_Mask_VT, RefractionDepthBias`

→ **官方从不设 `Albedo Controls` / `Albedo Overlay` / `Roughness Channel` / `AO Min` /
`Metallic Max,Min` / `Normal Strength` / `Roughness Exponent,Max,Min` / `Specular`。**
我们那 11 个额外参数是 v12 在"还是用错了 `MAI_Equipment`"的前提下推出来的，结论已经过期。
其中 `Albedo Overlay = (0.5, 0.5, 0.5)` 是**把 50% 灰叠到反照率上**的语义 —— 这本身就能把画面压成灰。

### ⑥ 贴图结构和能跑的 mod 完全一致
```
我们的  T_BWC_QZ_D  ：uasset 1,446 + ubulk 1,701,640   PF_DXT5  VirtualTextureStreaming(Bool)
金虎的  T_FY_White  ：uasset 1,531 + ubulk   110,980   PF_DXT1  VirtualTextureStreaming(Bool)
```
→ VT 设置、`.ubulk` 落盘、压缩格式都同构。**"贴图不是 VT / 数据没进包"这条线基本排除。**

### ⑦ 源贴图是好的
27 张 TGA 逐张读过：裙面 1024²、皮肤 4096²、`T_BY_black` = (24,24,26)、`T_BY_white` = (240,238,232)。
**所有 alpha 全 255**，不会被遮罩材质裁掉。

### ⑧ 19 个 FBX 导入器占位材质被打进了包
`Mods/PBZWardrobe/Materials/` 下 `M_BY_MI_Body` / `M_BY_M_HWC_Qunzi` / `M_BY_Head_Hair` … 共 19 个。
其中 `M_BY_ih_metal` 在 utoc 里占 66KB（自带完整着色器）。
实测**没有任何槽位引用它们**（见 ②），所以是纯冗余，应该从 cook 里剔掉，但不是花屏原因。

### ⑨ 新线索：能跑的 mod 都带一份改过的 `global.utoc/global.ucas`
```
BaiChiLian_full / FangYao_full / GoldenTiger_full / MuXiaoKui_full
        global.ucas 4,477,088 + global.utoc 410
游戏本体 global.ucas 4,479,008 + global.utoc 410
我们的 mod：**没有 global.***
```
两者都是"没有目录索引"的纯数据容器（UnrealPak 报 `Missing directory index`），
mod 那份比游戏那份小 1,920 字节，说明是在游戏原件基础上改写加了自己的东西。
**含义未定，但这是"能跑的 mod 都有、我们没有"的一个确定差异，列为待查。**

## 4.4 下一步（按性价比排序）

1. **【最可能，改动最小】把 MI 的参数砍到官方那套**：只留 `Albedo / Mix / Normal`
   （`RefractionDepthBias` 可不设）。删掉 `Albedo Controls` / `Albedo Overlay` /
   `Roughness Channel` / `AO Min` / `Metallic Max,Min` / `Normal Strength` /
   `Roughness Exponent,Max,Min` / `Specular` / `OpacityThreshold`。
   → 改 `ueproj/mats_mi.py`，重建 27 个 MI，重走 cook+打包。
2. 若仍灰：查 ⑨ 的 `global.utoc`，把游戏那份拷一份到 mod 目录里试
   （四个能跑的 mod 都这么做）。
3. 若仍灰：再上 UE4SS 只读探针，看运行时 MI 的 `Parent` 是否为 null、
   贴图 `GetSizeX/Y` 是否为 0。

## 4.5 剩下两个非材质问题（等材质解决了再动）

- **面部朝向 / 五官错乱**：头部网格的旋转基准或材质槽顺序错位
  （`bl_export_head.py` 只做了 ×100 + 改名 Armature，没处理朝向）
- **前臂错乱**：`tools/bl_conform_hands.py` 的权重搬运只做了肘→腕的相似变换（缩放 0.9384），
  肘-腕链可能少了一节；映射规则见 2.x
- **鞋底再抬 5mm**：改 `tools/bl_shift_z.py` 的偏移量重导

---

# 第五部分 · 工具与路径索引

## 5.1 自建工具

| 工具 | 用途 |
|---|---|
| `tools/izprobe` | C#/CUE4Parse 读取器。模式 `LIST/DTLS/MESH/REFB/MAT/PARAM/RAW/TEX/EXPORT/GET/LS/ROWJSON/ENUM/TAGS`。**能读游戏本体（有 AES key）** |
| `tools/lsp` | 读 pak 文件列表（多引擎版本可切） |
| `tools/dmp_parse.py` | Minidump 手工解析 |
| `tools/pe_dis.py` / `pe_str.py` | 反汇编 / 扫函数内字符串 |
| `tools/bl_export_fbx.py` / `bl_export_head.py` | 导出 FBX（**负责改名 Armature、头部 ×100**）|
| `tools/bl_kill_skull.py` | 删骷髅 + 舌头 + 碎块 + invisible 段 |
| `tools/bl_shift_z.py` | **只改 blend**，整体抬 Z |
| `tools/bl_clean_export.py` | **清理源物体后导 FBX**（必须用它，否则 FBX 混入临时物体导致导入失败）|
| `tools/bl_conform_hands.py` | 明末手 → 游戏骨架的权重搬运 |
| `tools/bl_heel_fix.py` | 脚部下移对齐高跟 |
| `ueproj/build_dt.py` | 生成整张外观表（69 行原样 + 附加行）|
| `ueproj/mats_mi.py` | 建 27 个材质实例（**当前嫌疑点，见 4.4**）|
| `ueproj/make_master.py` / `make_master_mask.py` | 建占位插件与假母材质（**不随包发**）|
| `ueproj/make_vt3.py` | 用 `set_virtual_texture_streaming()` 处理 27 张贴图 |
| `tools/pack_baiyi16.py` | 打包 + 封 zip |

## 5.2 路径

```
游戏根目录   E:/steam/steamapps/common/PBZ/
游戏 pak     ProjectPBZ/Content/Paks/          （AES 加密，izprobe 可读）
mod 安装     ProjectPBZ/Content/Paks/~mods/
UE4SS        platform/steam/ue4ss/            （v3.0.1，通过 platform/steam/dwmapi.dll 注入）
usmap        platform/steam/ue4ss/ProjectPBZ-5.7.4-301524+42ecbfa37f78-1ceefac8.usmap
工作目录     workbuddy/
引擎         D:/Epic Games/UE_5.7（游戏本体 5.7.4）
Blender      D:/Blender/blender.exe
```

## 5.3 版本履历

| 版本 | 解决/改动 |
|---|---|
| v1–v9 | 摸索链路，反复白模/崩溃 |
| v10 | 骨架多一根假根骨 → 1134 骨 |
| v11 | 崩溃真因 = 自建 base Material → 全改材质实例 |
| v11 | 删骷髅 + 舌头（52558→46002 面）|
| v12 | 补 3 个 VectorParameter（**后来证明是错的，见 4.3⑤**）|
| v13 | 骨架路径 `/HuaShira/`；贴图改 VT |
| v14 | 头 ×100；鞋底 +0.8cm |
| v15 | 女眷手重绑；外观表结论 |
| v16 | 自建整表（C++ 模块路线）成功 |
| v18 | 发现 JS pak = 文字元凶；外观表是**三行一组** |
| v19 | 官方 5 个 Codex 槽位 = mod 接口；灰模 = 未解锁预览 |
| v20 | 贴图 VT 顺序修正；补头部 6 张贴图；身体网格真导入 |
| v21 | 父材质改 `MAI_Equipment_Mask` |
| v22 | `bShareMaterialShaderCode=True`；albedo alpha 全改 255 |
| v23 | 不发任何 JS；VT 用专用 API 重建 → **材质仍灰** |
| **v24** | ①材质实例砍到官方那套（只设 Albedo/Mix/Normal）②眉毛/睫毛贴图修正 ③剔除 24 个无人引用的占位材质 |

---

# 第七部分 · v24 已完成的改动（待实机验证）

## 7.1 材质实例：砍到官方那套

`ueproj/mats_mi.py` 里删掉了全部 11 个官方不用的参数 + `OpacityThreshold`，
现在每个 MI 只设 `Albedo` / `Normal` / `Mix`。

验证（从**成品容器**里读出来的）：
```
izprobe RAW .../MaterialInstances/MI_BY_M_HWC_Qunzi
  SIZE 2730（v23 是 6720）
  Albedo Overlay/Controls/Roughness Channel/Specular/AO Min/Metallic Max/OpacityThreshold 全部 -1
  Parent = /AkashaEffects/.../MAI_Equipment_Mask
  贴图   = T_BY_FlatNormal / T_BY_ORM / T_BWC_QZ_D
```

## 7.2 头部贴图：眉毛 / 睫毛套错了（这是「五官错乱」的直接原因）

`mats_mi.py` 原来的前缀匹配是「按字典顺序找第一个 startswith」，
而 `MI_Wuchang_Eye` 正好是 `MI_Wuchang_Eyelash` 的**前缀** → 睫毛抢到了眼球贴图；
眉毛则被直接写成纯棕色块 `T_BY_darkbrown`。

而两张专用贴图**一直都打好包了**，只是没用上：
`T_HeadLash.tga 128²`、`T_HeadBrow.tga 256²`。

修法：
```python
"MI_Wuchang_Eyelash": "T_HeadLash",   # 原来是 MI_Wuchang_Eye（眼球贴图）
"MI_Wuchang_Brows":   "T_HeadBrow",   # 原来是 T_BY_darkbrown（纯色块）
```
并把前缀匹配改成 **最长优先**（`sorted(table.keys(), key=len, reverse=True)`），
这类「短名抢长名」的坑以后不会再犯。

验证（从已装进 `~mods` 的容器里读出来的）：
```
MESH SK_GoldenTigerHead
  slot[2] MI_BY_MI_Wuchang_Brows
  slot[3] MI_BY_MI_Wuchang_Eye
  slot[4] MI_BY_MI_Wuchang_Eyelash     ← 原来是 MI_BY_MI_Wuchang_Eye
RAW MI_BY_MI_Wuchang_Eyelash
  贴图 = T_BY_FlatNormal / T_HeadLash / T_BY_ORM
```

## 7.3 顺手清掉 24 个占位材质

`Content/Mods/PBZWardrobe/Materials/` 下的 `M_BY_*`（FBX 导入器自动生成）已挪到
`ueproj/_held_v24/Materials_unused/`（先扫过全工程，**0 个资产引用它们**）。

因为它们采样的是**普通 Color 采样器**，而我们的贴图是**虚拟纹理**，cook 时报了 64 条
`Sampler type is 颜色, should be 虚拟颜色 … Failed to compile Material … Default Material will be used in game`。
虽然它们不被任何槽位引用、不影响画面，但会让 cook 日志一直有红字、也是排查干扰源。

容器校验：
```
89 条目 = 25 MaterialInstances + 7 Meshes + 54 Textures(27 uasset + 27 ubulk) + 1 外观表
Engine/ 0 条   Akasha 0 条   ShaderArchive 0 条   Materials/ 0 条
ucas 17.93MB
```

## 7.4 产物与部署

- `builds/PBZ-白衣无常-金虎槽-v24.zip`（17.85MB）
- 已直接部署到 `ProjectPBZ/Content/Paks/~mods/`：
  `zzzzzzzz_PBZ_Baiyi_3002_P.pak / .utoc / .ucas`
- 旧 v23（`3001`）已挪到 `ProjectPBZ/Content/Paks/_old_baiyi/`，不会抢占

## 7.5 还没解决（等 v24 实机结果再动）

- **面部朝向**：贴图已确认 100% 匹配（`T_HeadSkin` 与海寇原头 `T_T_Head_D` 逐像素完全相同，
  `T_HeadEye` 与 `T_T_Eye_D` 也完全相同），所以「脸乱」不是贴图错——如果修完眉毛睫毛还乱，
  就是**几何/蒙皮**问题（导出时的朝向基准或 head 骨绑定）
- **前臂错乱**：`bl_conform_hands.py` 只做了肘→腕的相似变换
- **鞋底再抬 5mm**


---

# 第六部分 · 用户偏好（必须遵守）

1. **遇到未知问题先查官方文档 / 看别人 mod 怎么做**，不要闷头猜、不要反复试配置。
2. 官方有说法就按官方做；官方没覆盖时再自己分析，且要说明「这是我自己推的，依据是什么」。
3. 汇报时区分清楚：哪部分是**官方文档确认**的、哪部分是**实测**的、哪部分是**推断**的。
4. 交付封 zip，用户自己部署（后期因为 UEModManager 冲突改为手放 `~mods`）。
5. 判断效果**以游戏内实际画面为准**，Blender 预览只用于看几何。
6. 不要长篇解释，直接给结果；出错先承认再修，不要辩解。
