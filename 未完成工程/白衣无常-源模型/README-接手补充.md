# 接手补充（2026-11-11）

> 给下一位接手者 / 23 套服装 mod 作者看的**新增资料**。
> 本目录下原有的 `Notes.md`、`tex/`、`文档/`、`构建/`、`脚本/`、`视图/` **一个都没改**，
> 只在对应文件夹里新增了文件。原文档与实物有出入的地方，请看
> [`文档/00-源工程核对报告.md`](文档/00-源工程核对报告.md)。

---

## 一句话现状

**衣柜里能出现并装备「白衣无常」条目，但格子里面是空的**——身上仍是游戏默认服装、
头是光头（我们只在表里填了 `Hun_Body_Simple` + 光头 `Hun_Head_New` 两个占位资产）。

**槽位跑通 ≠ 服装 mod。** 主体工作（cooked 网格 / 贴图 / 材质）还没做完。

反证：发型消失恰好说明「表 → 网格 → 渲染」链是通的；如果游戏没读我们的行，
会显示带头发、带默认衣服的原版外观，而不是现在这个「默认衣服 + 光头」。

---

## 接手者最该先拿走的 6 条（都是实测，能省几天）

1. **骨架不用重绑。** 本体 `/HuaShira/Characters/Hero/Hero_Hun/Hun_Skin_Skeleton`
   的 `BoneCount = 1134`；源 FBX 也是 1134 根，逐根比对 **0 缺失**，
   前 3 根 `root / pelvis / spine_01` 一致。注意是插件根 `/HuaShira/...`，
   **不是** `/Game/HuaShira/...`。
   源 FBX 的骨架容器实际叫 `HunSkinSkel`（`Notes.md` 说必须叫 `Armature` 且「已满足」，
   实际没满足），导出前要改名，否则多一根假根骨 → 切外观崩 `0xC0000005`。

2. **本体外观表当前是 54 行、0 个 Codex 行**，不是旧文档写的「69 行 + 5 个官方 Codex 预留槽」。
   9 个 `Hun_OutFit_*` 里没有 `CodexGoldenTiger`。全量 dump 在
   `报告/s7_orig_table_dump.txt`（GBK）。行结构 `PBZAppearanceStruct` 35 字段，
   **Outfit 行靠 `OutfitBodyItem` / `OutfitHairStyleItem` / `OutfitHatItem` / … 引用其它行的
   `ItemId`（不是行名）**，头发在 `HeadClothDataArray` 的 `CA_Hun_Hair01`。
   只填 `BodyMeshAsset` + `HeadAsset` 两个字段 = 默认衣服 + 光头。

3. **解锁与命名**：纯资源包没有 GameFeature 授予组件，新增行会「未解锁，无法装备」；
   `bObtainableInGame = False` 会让条目**彻底消失**（已实测证伪，别再试）。
   可行做法是保留原版行、只替换一套（行名 / `ItemId` 不变 → 继承解锁）。
   中文名**不能**靠 `FlowLocText.ValueCache`，运行时按
   `FTextId(Namespace, Key)` 查 `Game.locres`（UE 5.7 源码确认）。
   本机 `PBZModLoader 2.1.0` 已绕过 `{ButtonText}` 的 JS 校验，旧文档「彻底不发 JS」不是铁律。

4. **现成的 cooked 网格就在 `构建/PBZ-白衣无常-金虎槽-v25.zip` 里**，不必重做 UE 导入 + cook：
   118 条路径 = 27 个 `MI_BY_*` + 7 个 Meshes（含 `SK_GoldenTigerBody` / `SK_GoldenTigerHead`）
   + 82 个 Textures + 1 张外观表；无 `Engine/`、无 `ShaderArchive`、无 Akasha 母材质。
   两个网格的骨架引用实测正确，材质槽全指向包内 `MI_BY_*`。
   `retoc to-legacy` 对 UAT 产物 0/76 全失败，但
   `UnrealPak <utoc> -Extract <dir>` 能抽出 193 个 `.uheader/.uexp/.ubulk` 供离线分析。

5. **材质变灰的可疑点（尚未实机验证）**：包内 `MI_BY_M_HWC_Qunzi.uexp` 实测 8,095 B，
   含 **19 标量 + 5 向量 + 3 纹理**参数，其中
   **`Albedo Overlay = (0.5,0.5,0.5)` 仍在** —— 而包内 README / `PROGRESS_材质排查.md` §7.1
   都声称「v24 已砍到只剩 Albedo/Normal/Mix」。文档与成品不符。
   另外：作者**能跑**的 MI（如 `MI_WC_01ba586b5746`）父级是游戏 MI
   `/Game/PBZContent/Characters/Hero/Hun_New_V2b/Material/MI_ZeroHun_Cloth_01_b`
   （再继承 `/AkashaEffects/MaterialLibrary/Template/Character/MAI_Equipment_Mask`），
   而本工程 `脚本/mats_mi.py` 直接把 MI 挂在母材质上，少一级继承。

6. **打包 / 安装**：三件套平铺放 `ProjectPBZ/Content/Paks/~mods/` **根部**、不要建子目录；
   包名用 9 个 `z` 前缀排最后加载。`.pak` 只留几百字节占位，
   **绝不能含 `Engine/` 任何文件**（会顶掉游戏配置 → `Missing global shader`）。
   材质自带着色器：`DefaultGame.ini` 的
   `[/Script/UnrealEd.ProjectPackagingSettings] bShareMaterialShaderCode=False`
   （写 `DefaultEngine.ini` 无效，Epic 官方文档 + modding.wiki + 本地实测三方一致）。

---

## 本目录新增了什么

| 路径 | 内容 |
|---|---|
| `README-接手补充.md` | 本文件（入口） |
| `文档/00-源工程核对报告.md` | 原四份文档 ↔ 实物逐项核对：18 条硬不符、缺失脚本清单、工具链修正 |
| `文档/01-方案-白衣无常独立外观.md` | 完整方案 v21（P0–P4、安装路径定案、已确认事实、踩坑记录） |
| `脚本/接手补充/` | 可复现工具源码（放在子目录，避免和原有 4 个 `*.py` 混淆） |
| `脚本/接手补充/pbzprobe/` | .NET 10 + CUE4Parse `1.2.2.202611`，命令 `wcls/wextract/umap/bpa/slot/pcls/dt/skel` |
| `脚本/接手补充/mipatch/` | .NET 8 + UAssetAPI 1.1.0，命令 `read/patch/tojson/fromjson` |
| `报告/` | 只读分析的 JSON / dump（本体 54 行表、23 套新旧版 hash 对比、布料参数汇总等） |
| `脚本/接手补充/toolchain.json` | 工具版本、校验值、命令写法 |

原有 4 个脚本（`build_dt.py` / `make_master_mask2.py` / `mats_mi.py` / `reimport_tex.py`）
全部硬编码作者本机 `E:/.../workbuddy/ueproj/...`，且该工程目录**未随仓库分发**，
换机器跑不起来；复现请用 `脚本/接手补充/` 里的版本。

## 环境依赖（本仓库不含）

UE 5.7.4（Launcher 版）、Blender 4.2.9、.NET SDK 8.0.412 / 10.0.100、
retoc 0.1.5、UnrealPak（UE 自带）、UE4SS（只用于生成 usmap）、游戏本体（需自行合法持有）。
**两把 AES key 不写入仓库**，脚本里以参数传入（公开可查）。

## 上游素材来源（分发衍生内容时请保留）

白衣无常上装 / 明末本体；女眷手 / 明末本体；细带高跟腿 + 鞋 / NexusMods mod 328；
海寇头 / PBZ `Corsair_3304` 作者 mod。详见 `技术说明.md` 与 `文档/00-源工程核对报告.md`。
