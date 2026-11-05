# 影之刃零（Phantom Blade Zero / PBZ）MOD 技术总览与交接文档

> 生成时间：2026-11-05 04:50（UTC+8）
> 用途：把本项目十几天积累的全部结论、外部资料、未完成需求，一次性交给下一个接手的人/模型。
> 阅读顺序建议：先读 §0、§1、§4、§6、§9，再回头查细节。

---

## §0 给接手者的话（先读这段）

> **本文档写的是「封包/材质/外观表」层面的技术总览，仍然有效。**
> **模型层面（三套服装怎么拼、材质怎么映射、有什么已知限制）请看同目录 `技术说明.md`。**
> 两者不冲突：本文解决「怎么打包进游戏」，`技术说明.md` 解决「模型本身是怎么做的」。


1. **本文档区分三类信息**，请务必按标记区别对待：
   - `【实测】`：我在本机用工具跑出来的结果，有命令和输出为证，可以直接采信。
   - `【官方】/【社区】`：外部资料原文，标了来源 URL。注意其中一部分是**别的游戏**的通用做法，未在 PBZ 上验证。
   - `【推断】`：我的推理，**没有直接证据**，不要当结论用。
2. **这个项目之前最大的错误是「在错误的层级上反复试参数」**。真正的问题很可能不在材质参数，而在 **MOD 架构选错了**（见 §4、§6）。接手时请先把 §4 读懂，再动任何代码。
3. 用户明确要求过：**遇未知问题先查官方文档、对照能跑的 mod，不要闷头猜**。这条优先级最高。
4. 用户已经很疲劳，反复启动游戏测试的容忍度很低。**任何需要他启动一次的改动，都必须先能说明「这一次能判定什么」**，并且优先做成运行时（Alt+F5 热重载）而不是重新 cook。

---

## §1 项目一句话现状

**目标**：把《明末：渊虚之羽》的「白衣无常」套装移植进《影之刃零》，作为**独立新增外观**（不替换原版、不依赖其他 mod）。

**已完成**：模型拼装、骨骼/崩溃、外观表、解锁槽位、iostore 打包、UI 文字兼容全部打通，衣柜里能看到并穿上「白衣无常」。

**卡住的地方（唯一一个）**：**衣服渲染出来是一片均匀的灰白色，只有头发有颜色。**

**次要问题**：头部朝向偏转、五官错乱、前臂错乱（已定位到"骨骼顺序"这一层，方案明确但未实施）。

**还有一条支线**：把作者的「婉若游龙」改成"龙纹网鞋+光腿+无内裤"的覆盖包，反复失败（覆盖不生效）。

---

## §2 环境与关键路径速查

### 2.1 游戏与引擎

| 项 | 值 |
|---|---|
| 游戏根目录 | `E:\steam\steamapps\common\PBZ` |
| 可执行文件 | `E:\steam\steamapps\common\PBZ\platform\steam\PBZ.exe` |
| 游戏内容根 | `E:\steam\steamapps\common\PBZ\ProjectPBZ\Content` |
| mod 安装目录 | `E:\steam\steamapps\common\PBZ\ProjectPBZ\Content\Paks\~mods` |
| 引擎版本 | **UE 5.7.4**（UE4SS 包说明里写明 `Unreal Engine 5.7.4`）【社区】 |
| 编辑器 | `D:\Epic Games\UE_5.7`（UnrealEditor-Cmd.exe / UnrealPak.exe / RunUAT.bat） |
| 临时目录约定 | `TMP=D:\UETemp`、`TEMP=D:\UETemp`、`UE-LocalDataCachePath=D:\UEDDC` |

### 2.2 解密密钥（三个来源互相印证）

```
0x4BC8A51E5381325073F2BC7D4E3089CD557C4E9B7D453901C2C795518867E01D
（Base64 形式）S8ilHlOBMlBz8rx9TjCJzVV8Tpt9RTkBwseVUYhn4B0=
```
- `【社区】` 3DM 教程帖原文给出上面两行：<https://bbs.3dmgame.com/thread-6716842-1-1.html>
- `【实测】` 本机用该 key 成功读取游戏本体 312,820 个文件（`izprobe` / `wcdump`）。

### 2.3 工具（本机已有）

| 工具 | 路径 | 作用 |
|---|---|---|
| `izprobe`（自研，C#/CUE4Parse） | `workbuddy/tools/izprobe/bin/Release/net10.0/izprobe.exe` | 读 PBZ 容器：`LS / MESH / RAW / ROWJSON / PARAM / TEX / EXPORT` |
| `wcdump`（自研，C#/CUE4Parse） | `Wuchang Fallen Feathers/workbuddy/tools/wcdump` | 读**明末**资产：`LS / MESH / MAT / EXPORT`（带明末 AES key） |
| UnrealPak | `D:\Epic Games\UE_5.7\Engine\Binaries\Win64\UnrealPak.exe` | 列/解 iostore（`-List`、`-Extract <dir>` 用**空格**不用 `=`） |
| UAT / BuildCookRun | `D:\Epic Games\UE_5.7\Engine\Build\BatchFiles\RunUAT.bat` | 打包 iostore |
| PBZModLoader | `PBZ\ProjectPBZ\PBZModLoader\` | TS/JS mod 框架，热重载 **Alt+F5**（游侠写的 Ctrl+F5 是错的）【实测】 |
| PBZModLoader TS SDK | `workbuddy/sdk/PBZModLoader-TS-Template/vendor/game-api/types/` | 367 个 `.d.ts`，34593 类型 / 49386 函数 |
| UE4SS | `PBZ\platform\steam\`（`dwmapi.dll` + `ue4ss\`） | Lua 脚本框架；**本机已证明 `LoadAsset` 在该游戏拿不到资产对象** |

### 2.4 本地没有、但社区方案需要的工具（**重要，接手第一件事就是装它们**）

| 工具 | 地址 | 说明 |
|---|---|---|
| **retoc** | <https://github.com/trumank/retoc> | **核心**。iostore ↔ legacy 双向转换。已支持 **UE5.7**（commit `Add UE5.7 support #48`） |
| repak | <https://github.com/trumank/repak> | 只处理 .pak，需要 Oodle 库；不支持 utoc/ucas |
| FModel | <https://fmodel.app/> / <https://github.com/iAmAsval/FModel> | 资产浏览、导出、看父级链 |
| UModel | <https://www.gildor.org/en/projects/umodel> | 模型/贴图提取、动画预览 |
| **UAssetGUI** | <https://github.com/atenfyr/UAssetGUI> | 直接编辑 .uasset（改材质实例参数/改名）。配 UAssetAPI |
| Blender PSK 插件 | <https://github.com/DarklightGames/io_scene_psk_psa> | 明末/PBZ 的骨骼网格可用 PSK 链路 |
| UnrealLocres | <https://github.com/akintos/UnrealLocres> | locres 文本读写 |
| usmap（PBZ） | 本机：`platform\steam\ue4ss\ProjectPBZ-5.7.4-301524+42ecbfa37f78-1ceefac8.usmap` | FModel/UAssetGUI 必需 |

---

## §3 外部资料全量清单（本次搜集的所有教学性内容）

### 3.1 影之刃零专属

#### (1) 3DM《【解包】影之刃零 ucas 解包打包工具--AESKEY》——**目前唯一一份 PBZ 专属流程帖**
<https://bbs.3dmgame.com/thread-6716842-1-1.html>（2026-11-01，作者 古剑玩家）

原文要点（几乎逐字）：
- 流程：`先解包 → 修改资源（模型，贴图，代码）→ 保存 → 烘焙打包 → 得到 mod 文件`；`打包后文件名改成 _P.xxx，即可分享发布`
- 工具清单：retoc（打包/解包 IoStore 容器）、repak（pak，多线程，不支持 ucas/utoc）、FModel、UModel、Blender PSK/PSA 插件、UnrealLocres
- 依赖：repak 解 pak 需要 Oodle `liboo2corelinux64.so.9`
- AES KEY：见 §2.2
- 对话资源路径：`/ProjectPBZ/Content/Localization/Game/zh-Hans/Game.locres`
- **模型路径（关键）**：`ProjectPBZ/Plugins/HuaShira/Content/Characters/Hero/Hero_Hun/SkinParts/Hun_Body.uasset`，导 **PSK** 格式，Blender + PSK 插件编辑
- 讨论区里有人问"下一步做 mod 没有教程"，作者也没给——**说明 PBZ 的**资产级**制作流程确实没有公开教程**，只能套通用 UE 流程。

#### (2) 官方 ModLoader 前置工具（游侠 / 3DM 转载）
<https://3g.ali213.net/patch/319865.html>、<https://patch.ali213.net/showpatch/319865.html>
- JS/TS MOD 加载框架，内置 TypeScript 编译器，玩家无需 Node/npm
- 自动发现 `mods/<名字>/main.ts` 或 `main.js`（TS 优先）
- `mods.ini` 开关；Ctrl+F5 热重载（**实测是 Alt+F5**）
- 安装：ZIP 直接解压到含 `ProjectPBZ` 的根目录，合并 `ProjectPBZ` 和 `platform`，**不要多一层 PBZModLoader 父文件夹**
- `version.dll` 必须在 `PBZ.exe` 同级（Steam 布局为 `platform/steam/version.dll`）

#### (3) UE4SS for PBZ（VG Times / Nexus mods/5）
<https://vgtimes.com/games/phantom-blade-zero/files/99510-...>、<https://www.nexusmods.com/phantombladezero/mods/5>
- 测试于 **Steam build 26266538 / UE 5.7.4**
- 安装到 `PBZ\platform\steam`（`dwmapi.dll` + `ue4ss\` 与 `PBZ.exe` 同目录）
- **重要**：`Blueprint modifications using this loader are placed in PAK format into PBZ\ProjectPBZ\Content\Paks\LogicMods`
  → 存在 `LogicMods` 目录这一回载入口，与 `~mods` 不同。`【未验证】`本项目从未试过。

#### (4) 服装包系列（同一作者批次，"明末系"）——**最有参考价值的一类**
金虎祥瑞：<https://3g.ali213.net/patch/319915.html>
织绣海寇：<https://patch.ali213.net/showpatch/319917.html>
黑丝方瑶：<https://patch.ali213.net/showpatch/319911.html>
说明里反复出现的**关键条款**（原文）：
> 本批次共用相同的外观表和菜单逻辑，并通过各包自己的标记，仅显示已安装的新外观。
> 与其他覆盖外观表 / 启动脚本 / 外观菜单的 Mod 混用，**可能需要额外合并**；不要将不同批次文件直接混装。
> 无需 UE 编辑器、Blender、UE4SS 或明末 Mod Enabler。
> 裙摆和配饰具有动态适配，帽子两侧悬挂部分使用**有约束的布料模拟**。
> 保留无常身体比例、红眼和**原生身体受击碰撞**。

**这三条直接解释了我们踩的坑**：他们不是"一个包搞定一切"，而是**一张共享外观表 + 每包一个"标记"**；不同批次的表混装会互相覆盖。

#### (5) 角色替换系（bilibili:夜曲_flac 等）
沐小葵：<https://patch.ali213.net/showpatch/319905.html> / Nexus <https://www.nexusmods.com/phantombladezero/mods/137> / 踩蘑菇 <https://www.caimogu.cc/post/2513688.html>
幻鬼：<https://dl.3dmgame.com/patch/399671.html>
终极瓦尔比：<https://patch.ali213.net/showpatch/319949.html>
伊芙：<https://3g.ali213.net/patch/319919.html>
共同特征（**架构层面的证据**）：
- 前置 **UE4SS**，mod 文件夹放 `platform\steam\ue4ss\Mods\`
- 包内同时含 `ue4ss` 与 `pakmod` 两部分，**pak 放 `ProjectPBZ\Content\Paks\`**
- **F6 打开 mod 菜单**，可切换外观 / 开关衣服 / 关闭高成本毛发
- 瓦尔比那条写得更明确：`支持自动应用人物，也可按 F6 手动应用`；卸载要删 `~mods` 的三件套 **以及** `Mods` 下的 `ValbyMat / ValbyFit / ValbyHide2` 并从 `mods.txt` 移除三行
  → **`Mat`（材质）/ `Fit`（适配）/ `Hide2`（隐藏原身）是拆成三个独立 UE4SS 模块的**

#### (6) 孙悟空替换 mod（ZOL 报道）
<https://ucwap.zol.com.cn/article/article.php?id=12670193>
- 技术核心：**UE 内置 IK Retargeter 做动画实时重定向**，规避颈部拉伸、肩部穿模
- 覆盖序章/青年/主线演出/引擎内过场；武器与杀气系统不动
- 两档模型（87.7 万面 / 21.1 万面）
- 安装：三个文件放 `~mods`，命名 `zzz_RyuSoul_P.pak/.ucas/.utoc`

#### (7) 全结局服装解锁 mod
<https://patch.ali213.net/showpatch/319883.html>
- 证明"解锁"是在运行时做的，且会**写存档记录**：`%LOCALAPPDATA%\ProjectPBZ\Saved\PBZUnlockAppearances-record.txt`
- 卸载后服装保持解锁（与正常获得相同）→ 说明解锁写进了存档

#### (8) 玩法增强整合包（含外观，带中文说明与排错）
<https://3g.ali213.net/patch/319945.html>
- 37 个组件 / 9 分类，`安装.bat` 自动找目录
- **排错经验（可直接用）**：
  - `消除迷雾` 与 `全物品菜单` 都占 `version.dll`，只能留一个
  - 装完没效果：先看文件有没有出现在 `~mods` 或 `ue4ss\Mods`
  - 启动闪退：依次改名 `dxgi.dll`、`version.dll`、`dwmapi.dll` 定位
  - 日志：`platform\steam\ue4ss\UE4SS.log`、`platform\steam\ReShade.log`

### 3.2 通用 UE4/5 Modding 教材（**PBZ 没有专属教程时，这是唯一成体系的路**）

#### (1) 小莫的维基库（Dmgvol/UE_Modding 中文镜像）——**首选教材**
<https://wiki.aoe.top/ModTutorial/UE_Modding/README.html>
上游：<https://github.com/Dmgvol/UE_Modding>

目录与本次问题相关的三篇：
- 创建 Pak 文件 - IoStore：`/1.BasicModding/IoStorePacking.html`
- **为材质实例创建替代材质**：`/3.AdvancedModding/ReplicatingMI.html` ← **必读**
- 更改骨骼网格：`/2.IntermediateModding/ChangingSK.html`
- 烘焙/编译带区块内容：`/2.IntermediateModding/CookingContent.html`
- 编辑 UAsset 值（UAssetGUI）：`/1.BasicModding/UAssetGUI.html`
- Hex 编辑（UAssetGUI 失效时）：`/1.BasicModding/HexEditing.html`

`ReplicatingMI.html` 原文要点（这条几乎是为我们量身写的）：
> 主要用于那些不接受自定义/普通材质的游戏，或者模组制作者希望**继承材质行为而不破坏它**并调整参数。
> 步骤：FModel 里打开目标 `MaterialInstanceConstant` → 沿父级链向下找到**基础材质**（类型不再是 MI，而是普通 Material）→ 在工程里建**完全相同路径和名字**的材质、复制参数（名字完全一致，并连到 Material 节点，"不必有意义，只要连上能编译"）→ 从它建 MI、放到原 MI 所在文件夹 → 再从这个 MI 建**第二级 MI**，这一级才设自己的贴图/数值，挂给网格。

#### (2) modding.wiki《Common Asset Replacement Recipes》——**最重要的"一条铁律"**
<https://modding.wiki/en/UnrealEngineModdingGuides/CommonAssetReplacementRecipes>

关于材质的部分与上条一致，但多了一条**变体方案**和一条**铁律**：
> **变体**：如果做完还是不渲染自己的贴图，某些游戏还需要再变一次——不要沿真实继承链走下去，而是找**参数集最接近的现成 MI**（视觉简单的小配件往往最合适），用**那一个 MI 的确切名字和路径**直接造一个普通 Material（不碰它真正的父链），再从它实例化。
>
> **铁律**：**永远不要**把任何"占位/复刻"资产打进包，除非你就是要用它替换真实资产。占位物只是为了让你自己的工程能编译。误打包 = 用空壳静默覆盖真资产。

#### (3) Taleframe《Changing SkeletalMesh(SK)》
<https://github.com/Taleframe/UE_Modding/blob/main/IntermediateModding/ChangingSK.md>
- 导出前确认：材质正确、UV 正确、权重可用、**根对象命名 `Armature`**
- 导出缩放 **0.01**（米制→厘米）
- 工程里建**与游戏完全相同的目录结构**，网格**命名必须与游戏一致**
- 复制 PhysicsAsset / ShadowPhysics 并**改成游戏里的名字**
- **只打包新的 SK + 用到的材质和贴图。不要打包 Skeleton、PhysicsAsset、ShadowAsset**

#### (4) UAssetGUI 工作流（中文整理）
<http://www.mfbz.cn/news/47166/>
- `UAssetGUI tojson X.uasset X.json VER_UE5_x` → 改 JSON → `UAssetGUI fromjson X.json X.uasset`
- 常见错误 `failed to maintain binary equality`：先检查引擎版本是否匹配

### 3.3 retoc 完整命令（**从 README 抄的，未经本机验证**）

```text
retoc.exe --aes-key <AES_KEY> [OPTIONS] <COMMAND>

Commands:
  manifest / info / list / verify
  unpack          # 从 .utoc 提取 chunks（文件）
  unpack-raw      # 提取原始 chunks
  pack-raw        # 把原始 chunk 目录打回容器
  to-legacy       # Zen(iostore) → Legacy(.pak/.uasset/.uexp)
  to-zen          # Legacy → Zen(iostore)
  get / dump-test / gen-script-objects / print-script-objects
Options:
  -a, --aes-key <AES_KEY>
  --override-container-header-version <...>
  --override-toc-version <...>
```

典型 mod 循环（来自 Blood of Dawnwalker 教程，同一作者体系）：
```bat
:: 1) 解出目标资产（只解需要的，--no-shaders 跳过着色器库）
retoc.exe -a 0x4BC8...E01D to-legacy -f "ProjectPBZ/Content/Mods/.../XXX.uasset" --no-shaders --version UE5_5 -v "<游戏Paks目录>" "C:\out"

:: 2) 用 UAssetGUI 打开 C:\out\...\XXX.uasset（设引擎版本、导入 usmap、选中映射）改参数，Ctrl+S

:: 3) 回打成 iostore（三件套）
retoc.exe to-zen --version UE5_7 -v "C:\out" "C:\out\MyMod_P.utoc"
:: 产出 MyMod_P.pak + .ucas + .utoc
```
**坑（原文）**：若 retoc 报 `missing ScriptObjects chunk`，不要只指向 mod 的 .utoc，**要指向整个游戏 Paks 目录并用 `-f` 选资产**，这样它才能用游戏本体的 ScriptObjects。

另一个已被验证的 UE5.7 组合（Far Far West 指南）：
```bat
UnrealPak.exe Mod_P.pak -Create=PakList.txt
retoc.exe to-zen Mod_P.pak Mod_P.utoc --version UE5_7
```
→ **确认 `UE5_7` 是合法版本 token**【社区】

### 3.4 关于"材质变灰/丢贴图"的官方与社区结论（**决定我们该往哪走**）

| 来源 | 结论 | 对项目的意义 |
|---|---|---|
| Epic 论坛《Failed to find shader map for default material WorldGridMaterial》<https://forums.unrealengine.com/t/282824> | 打包设置里**关闭 Share Material Shader Code** 可解决一半情况；另有 `bGenerateChunks=False`、只留一个 SM 平台等解法 | **我们的 v22 把 `bShareMaterialShaderCode` 改成了 True，方向可能反了** |
| 博客园《Unreal: Dynamic load map from Pak file》<https://www.cnblogs.com/psklf/14778289.html> | 日志 `LogMaterial: Can't compile X with cooked content, will use default material instead` 的原因是启用了 Share Material Shader Code → **外部 pak 里的材质找不到 shader** | 与上条一致 |
| CSDN《UE5 热更新(Pak 包的 Cook,打包,加载,踩过的一些坑)》<https://blog.csdn.net/xialuhui/article/details/126729195> | UE5 默认勾选 Share Material Shader Code，**导致加载出来的 Actor 材质丢失，取消勾选可解决**；另外 IoStore 未勾选时 Mount 会因缺 .utoc 失败 | 同上；且解释了 `-iostore` 与 `.utoc` 必须三件套齐全 |
| 犀跃设计《UE5 打包给甲方演示…丢贴图》<https://www.xiyuesheji.com/3d/news/detail-2010.html> | 贴图丢失常见于：材质引用了工程目录外的贴图、Cook 没包含、**路径大小写不一致** | 提醒检查 `Textures/` 大小写与 Cook 清单 |
| CSDN《UE 蓝图 Actor 拆分 Mesh 导出材质丢失全解析》<https://blog.csdn.net/weixin_32382335/article/details/164580709> | 开发期不要开 Share Material Shader Code；用 `GetMaterial()->GetPathName()` 反查，不以 `/Game/` 开头就重新 LoadAsset | 运行时兜底思路 |

> **一句话总结**：**"加了新材质的 mod"必须让材质的 shader 跟着材质包走（关闭共享着色器代码，或自带着色器库），否则引擎会用 `DefaultMaterial` 顶上——表现就是"不报错、但一片均匀灰白"。**
> 这和本项目长期观察到的现象**完全吻合**。

---

## §4 三种 MOD 架构（**这是本文档最重要的认知**）

### 架构 A：纯资源包 + 外观表（"明末系"服装包走这条）
```
~mods/XXXAppearance/
  zzzzzz_PBZ_XXX_2302_P.pak   (几百字节，仅挂载壳)
  .utoc / .ucas               (网格 + 贴图 + 材质实例 + DT_PBZAppearanceTable)
```
- 不需要 UE4SS
- 外观表**每批共享一张**，用"每包自己的标记"决定显示哪些行
- 布料/物理靠"原服装布料遮罩 + 有约束的布料模拟"

### 架构 B：UE4SS Lua/TS + pak（"角色替换系"走这条）
```
platform/steam/ue4ss/Mods/<Mod名>/Scripts/main.lua    ← 运行时逻辑（F6 菜单、自动应用）
ProjectPBZ/Content/Paks/（或 ~mods）/xxx.pak           ← 资产
```
- 运行时 `SetSkeletalMeshAsset` / `SetMaterial` / 建 MID，**完全绕开 cook 期的材质问题**
- 典型拆分：`XXXMat`（材质）、`XXXFit`（体型适配）、`XXXHide2`（隐藏原身）
- 缺点：`F6` 要手动按；有闪退风险

### 架构 C：GameFeature 插件 + Blueprint Component（**作者的真实做法，本次新发现**）
```
ProjectPBZ/Plugins/GameFeatures/PBZCollectionWardrobe/Content/
    PBZCollectionWardrobe.uasset          ← GameFeature 数据
    BPC_PBZModLoader.uasset               ← 加载器组件（含 Options/BPC_PBZOutfitOptions）
    BPC_CollectionVisual.uasset           ← 视觉（视觉主体）
    BPC_CollectionVisualFix.uasset        ← 视觉修正（引用 /Game/Mods/PBZFY/... 等路径）
    BPC_CollectionAttachedBody.uasset     ← 附加身体
    BPC_CollectionHeadCloth.uasset        ← 头部布料
    BPC_CollectionBaiParts.uasset         ← 白赤练部件（引用 /HuaShira/Characters/NPC/ChiLian_P2/...）
    BPC_CollectionWardrobePanel.uasset    ← UI 面板
    ABP_FYBodyPose.uasset                 ← 姿态（引用 Hun_Skin_Skeleton）
ProjectPBZ/Content/Mods/PBZCollectionWardrobe/DT_CollectionGrants.uasset   ← **每包自己的"标记"**
ProjectPBZ/Content/PBZContent/DataTable/UI/DT_PBZAppearanceTable.uasset   ← 共享外观表
```
证据来源【实测】：把 `~mods` 里作者的 9 个辅助包（`CollectionVisuals_9940`、`CollectionWardrobe_9920`、`WardrobeReopen_9941`、`BaiScopedRepair_9942`、`CollectionRelease_9943`、`MuHeadVisibility_9944`、`ClimaxPreviewHair_9945`、`OutfitCoexistence_9900`）用 UnrealPak 解包并读名字表得到。

**要点**：
1. 作者不是"一个资源包"，而是 **GameFeature + 蓝图组件**；材质、姿态、挂接、遮罩全部由蓝图在运行时处理。
2. `DT_CollectionGrants` 就是说明里说的"**各包自己的标记**"。
3. `OutfitCoexistence_9900` 这个包**只改 `DT_PBZAppearanceTable` 一个资产** → 证实"表是可以被单独替换/合并的"。
4. `ABP_FYBodyPose` 说明他们连**姿态**都用 AnimBP 处理（对应"原生身体受击碰撞""体型适配"）。

### 附带：PBZModLoader（架构 B 的 TS 版，本机已装可用）
- 自动发现 `ProjectPBZ/PBZModLoader/mods/<name>/main.ts`
- 日志：`ProjectPBZ/PBZModLoader/evidence/<本次运行>/loader.log`；**`console.log` 必须以 `[PBZMOD]` 开头才会被捕获**【实测】
- 必须导出 `stop()`，否则热重载被阻塞
- 热重载 **Alt+F5**

---

## §5 本项目已确认的技术事实（**不要再推翻**）【实测】

1. **切外观崩溃的真因**：`ReferenceSkeleton` 多出一根假根骨。UE 只跳过名为 **`Armature`** 的骨架容器节点；否则 1135 根 vs 1134 根，整套骨骼索引 +1 → 访问越界崩溃。
   → Blender 导出前必须 `armature.name = "Armature"`。
2. **摆大字 / 没头 / 没动作**：骨架挂载路径必须是 `/HuaShira/...`（插件根），不是 `/Game/HuaShira/...`；且要用 `unreal.load_asset` 取骨架。
3. **头只有 1/100 大**：glTF 米制未 ×100（UE 是厘米）。
4. **衣柜看不到服装**：缺 `DT_PBZAppearanceTable`；我们从未发过这张表。
5. **表的结构**：`/Script/ProjectPBZ.PBZAppearanceStruct`，35 字段；**每套服装 3 行**：`Outfit`（只声明 ItemId）+ `Body`（BodyMeshAsset）+ `Hairstyle`（HeadAsset）。文字字段是 `FlowLocText { Namespace, Key, ValueCache }`，不是 `FText`。
   `EAppearanceType`：0 Body / 1 Hat / 2 Beard / 3 Hairstyle / 4 Outfit / 5 Neck / 6 MeshBand / 7 BrowLashCard。
6. **游戏原版表 69 行**；官方预留 5 个 Codex 槽，资产路径写死 `/Game/Mods/PBZWardrobe/`；**第 6、7 个槽默认已解锁**（用户实测）。
7. **UI 文字变 `{ButtonText}`**：游戏 11-04 更新后，**`~mods` 里任何含 JavaScript 的 .pak 都会触发**。→ 结论：**彻底不发 JS**。
8. **iostore 容器必须三件套同名**（`.pak` 几百字节 + `.utoc` + `.ucas`），`.pak` 是挂载入口。
9. **UnrealPak 打 legacy pak 的正确姿势**：清单 LF 换行、绝对源路径、dest 写 `..\..\..\ProjectPBZ\...`、首行放 `..\..\..\Engine\Pad.txt` 占位、输出先删。
10. **`UnrealPak <utoc> -Extract <dir>` 用空格**，不能用 `-Extract=`；输出是 `.uheader` + `.uexp`。
11. **`.uheader` 不是磁盘 uasset**：首 4 字节是 `0x00000001`（容器包头版本号）+ 文件总长 + 条目数 + 偏移表；磁盘 uasset 首 4 字节是 `0x9E2A83C1` + 版本链 + CustomVersion + 名称/导入/导出表。**所以"改扩展名回写"不成立**。
12. **UAT `-skipcook -stage -pak -iostore` 需要 `Cooked/Windows/ProjectPBZ/Metadata/packagestore.manifest`**，否则报 `A package store manifest or project store is required when staging to IoStore`。→ 手搓目录再打包走不通。
13. **cook 树必须剔掉的东西**：`Engine/`、`ProjectPBZ/Plugins/`、`ShaderArchive-*`、`ShaderAssetInfo-*`、`ShaderTypeInfo-*`。带上就会顶掉游戏自带同名文件 → 渲染设置被重置 / `Missing global shader`。
14. **外观表 35 个字段里没有任何位移/旋转/缩放字段**（逐条核对过）。
15. **明末原版 `WUCH_BWC_Jacket` 17 个槽 → 只有 8 个不同材质**：
    ```
    [0] WUCH_HWC_Qunzi_1 → M_HWC_Qunzi      [1] M_HWC_YaoDai    → M_HWC_Qunzi
    [2] WUCH_HWC_Qunzi   → M_HWC_Qunzi      [3] WUCH_HWC_Xionggu → M_HWC_XiongGu
    [4] WUCH_HWC_Yaodai_1→ M_HWC_YaoDai01   [5] WUCH_HWC_Renlian → M_HWC_LianPI01
    [6] WUCH_HWC_Shoubi  → M_HWC_shoubi     [7] WUCH_HWC_Tougu   → M_HWC_TouGu
    [8] WUCH_HWC_Renlian_1→M_HWC_LianPI01   [9] WUCH_HWC_Yaodai  → M_HWC_YaoDai01
    [10]WUCH_HWC_shoubi_2→ M_HWC_shoubi     [11]Wuchang_Head8    → MI_Head
    [12]WUCH_HWC_Shenti  → MI_Body          [13/14/15]inv1/lambert1/inv3 → invisible
    [16]M_HWC_LianPI03   → M_HWC_LianPI01
    ```
    原版材质父级是 `.../BaseCharacterMat_SP/M_B_CharacterMask_SP_14`，贴图是 **D / N / R 三件套**（29 张）。我们最初只导了 `_D`，把 Normal 换成通用平法线、Mix 换成通用 ORM → 全身无细节、粗糙金属一致 → 看起来像塑料壳。
16. **缩写表（用户提供，勿再搞错）**：海寇 = `Base`；**HWC = 夜行无常（黑衣）**；**BWC = 白衣无常**。`M_HWC_*` 这个槽名前缀是原版就有的（黑白无常共用同一套网格）。
17. **婉若游龙 = `LTZ`**（`WuCh_LTZ_Jacket` 13 槽 + `WuCh_LTZ_Pants` 4 槽）；流云织羽 = `HD`（`M_HD_*`）。两者别混。
18. **脖子/领口在明末是"上装"的一部分，不在头上**（`WuCh_LTZ_Jacket` 里有 `MI_Head9 → MI_Head` 段，310 顶点，Y 1.408~1.656）。作者把整颗头删了只留这段颈部。
19. **骨骼顺序才是头部问题的真因**：我们的头 `root, ik_weapon_root, ik_weapon_r, ...`（Blender/glTF DFS 重排），游戏/身体/作者的头都是 `root, pelvis, spine_01...`。**几何与权重完全一致（Kabsch 配准 rms<0.1，权重分布逐顶点相同）**，所以"头往前移"是在修一个不存在的位置误差。
20. **运行时实测：材质挂载是对的**。`BP_Renewal_Hun_C.CharacterMesh0` → 17 槽全指向我们的 `MI_BY_*`，类型 `MaterialInstanceConstant`（不是 DefaultMaterial）。

---

## §6 材质"全灰"问题的三条解法（按推荐度排序）

> 先把现象钉死：**不报错、无紫红格子、无 checkerboard，就是一片均匀的灰白（有高光）；只有头发（Groom，走游戏自带 `MA_HairSheet`）有颜色。** 这个组合 = 材质最终落到 `DefaultMaterial` 或材质输出与 Albedo 无关。

### 路线 1（**最推荐**）：retoc to-legacy → UAssetGUI 改 → retoc to-zen
**理由**：这是社区里对"游戏不接受自定义材质"的**标准解法**，而且完全绕开"占位母材质"这一层。作者本人在《修复方案》里给的也是这条（"从游戏 pak 复制 `MI_ZeroHun_Cloth_01_b` 改名换贴图"）。

步骤草案：
1. 装 retoc（`cargo install` 或 release 二进制）。
2. 用 retoc 把**游戏本体**的 `MI_ZeroHun_Cloth_01_b`（或织绣 mod 里的 `MI_WC_*`）解成 legacy：
   ```bat
   retoc.exe -a 0x4BC8...E01D to-legacy -f "ProjectPBZ/Content/PBZContent/Characters/Hero/Hun_New_V2b/Material/MI_ZeroHun_Cloth_01_b.uasset" --no-shaders --version UE5_7 -v "<游戏Paks目录>" "<out>"
   ```
3. UAssetGUI 打开，**改包名/资产名 + 换三张贴图引用**（Albedo / Normal tex / Mix）。必要时逐参数对齐作者的 `MI_YL_*`。
4. `retoc to-zen --version UE5_7 <out> <out>\MyMod_P.utoc` → 三件套 → 放进 `~mods`。
5. **只发 MI + 贴图 + 网格 + 外观表；绝不发 Skeleton / PhysicsAsset / 母材质**（见 §3.2(3)(2) 的铁律）。

**风险**：UAssetGUI 改包名后名称表/导入表可能不一致；`failed to maintain binary equality` 属常见警告可忽略，但要验证回打后资产能加载（可用 `izprobe RAW` 验）。

### 路线 2：完全按"复刻母材质"的正统做法重做 MI
（`ReplicatingMI` + modding.wiki 的变体方案）
我们在 v24~v25 做过一半：自建了同路径 `MAI_Equipment_Mask` 占位母材质，声明了 19 标量 + 5 向量 + 3 贴图，从它派生 MI。
**但可能漏了三件事**：
1. 母材质必须**从基础 Material 开始复刻**（不能是"空材质 + 一堆参数节点随便连"），参数要**逐个连到 Material 节点**；
2. 要做**两级 MI**：`占位母材质 → 中间 MI（放到原 MI 的文件夹）→ 我们的 MI（设贴图）`；我们直接一级 MI，可能不够；
3. 若仍不生效，走**变体方案**：找参数集最接近的现成 MI（作者包里 `MI_YL_*` 就是），用**它的名字和路径**造普通 Material，再从它实例化。
**注意铁律**：占位母材质**不能进包**（我们目前确实没进包，`~mods` 容器里 0 条 `Akasha` 记录【实测】）。

### 路线 3：运行时兜底（**最快见效，可作为 A/B 对照**）
用 PBZModLoader 的 TS（或 UE4SS Lua）在运行时：
```
找 Character → 取 SkeletalMeshComponent → 逐槽
  → KismetMaterialLibrary.CreateDynamicMaterialInstance(WorldContext, 真母材质)
  → SetTextureParameterValue('Albedo'|'Normal'|'Mix', 我们包里 LoadAsset 来的贴图)
  → SetVectorParameterValue('Metallic Channel'=R / 'Roughness Channel'=G / 'AO Channel'=B)
  → SetMaterial(slot, MID)
```
`【实测】` 我们已写好 `ProjectPBZ/PBZModLoader/mods/baiyi-probe/main.ts`（v4），SDK 类型检查 0 错误，**但直到最后一版都没能真正执行到组件层**：
- v3 的 bug：用了 `GameplayStatics.GetPlayerPawn`，而 SDK 里**根本没有这个函数**（全库只有 `GetPlayerController / GetPlayerState / GetPlayerName / GetPlayerId`）→ 每秒静默返回，60 次心跳 `applied=0`。
- v4 已改成 `GetAllActorsOfClass(gi, UE.Character.StaticClass(), $ref(out))` + `$unref`，并加了全程显式日志。**尚未在游戏里跑过。**

**若这条路成功，会立刻分辨出三件事**：真母材质能否加载 / MID 能否建 / 贴图能否绑定。

### ⚠️ v25 补的关键一环：**占位母材质从来没设过 Material Usage**
`ueproj/make_master_mask2.py` 里只设了 `blend_mode` 和 `opacity_mask_clip_value`，
**从未设 `used_with_skeletal_mesh`** → 占位母材质的 `bUsedWithSkeletalMesh = False`。
cook 时这个标记会写进每个 MIC 的 `FMaterialCachedExpressionData.RuntimeMaterialUsage`；
运行时组件判"该材质是否可用于骨骼网格"时如果拿到 false，就会**直接退回 `DefaultMaterial`**——
表现正是"不报错、无紫红格子、一片均匀灰白、参数怎么改都不生效"。

v25 已补：
```python
for _flag in ("used_with_skeletal_mesh", "used_with_static_mesh",
              "used_with_instanced_static_meshes", "used_with_particle_sprites",
              "used_with_morph_targets"):
    mat.set_editor_property(_flag, True)
```
重建后 MIC 的 uexp 体积变化（4687 → 8095）是这条改动确实落到了 cooked 资产里的间接证据。

### 顺带：v22 把 `bShareMaterialShaderCode` 改成 **True** 可能是**方向错误**
- 社区一致结论是**关闭**（False）才能让"包里带的材质"自带 shader，否则外部材质找不到 shader → `DefaultMaterial`。
- 我们改成 True 的依据是"官方 MI 只有 4 个参数、uexp 4687 字节等长"，属于**间接推断**，`【推断】`且有反证。
- 但注意：改成 False 时**必须只把材质打进包，绝不能发 `ShaderArchive-*`**（发过一次，导致 `Missing global shader`）。这两点不矛盾：False 是"shader 内联进材质包"，不是"发全局着色器库"。

---

## §7 已排除的错误方向（**别再走一遍**）

| 方向 | 为什么排除 |
|---|---|
| 源贴图有问题 | 27 张 TGA 逐张验过：颜色正确、alpha 全 255、成品包内解出的 RGB 与源图逐像素一致 |
| UV 丢了/塌了 | 身体 17 段逐段验：U/V 都在 0~1，唯一值 86~2536 个 |
| 网格槽位指向占位材质 `M_BY_*` | 运行时实测 17 槽全是 `MI_BY_*` |
| 父材质路径写错 | 游戏里真实存在 `/AkashaEffects/MaterialLibrary/Template/Character/MAI_Equipment_Mask.uasset`，与我们 MI 的引用逐字相同 |
| 外观表覆盖了材质 | 官方表里 `OverrideMaterials`、`MI_` 字符串都找不到（-1） |
| 占位母材质被打进包了 | 容器清单 120 条，`Akasha` 命中 0 |
| 虚拟纹理是必须的 | **反了**。官方服装贴图 `T_ZeroHun_Cloth_01_ARM` 的 uasset 只有 1250 字节、名称表里没有 `VirtualTextureStreaming`；作者的贴图是 VT。**两种都能用，不是关键** |
| 缺 `global.utoc` 导致不渲染 | 我们的容器单独挂载也报 `Found IoStore Package but global data is missing`，四个能跑的 mod 一样；且 v23 没发 global 也能显示模型 |
| "把 `~mods` 里的包改个 z 前缀就能抢先" | 反复试过 `zzz0_` / 9 个 z，全部无效。真正的机制是**同包路径只有一份**，且作者的包体量大、表被覆盖 |
| "把作者的容器解开改一改再打回去" | `.uheader` 不是磁盘 uasset，UAT 又必须要 `packagestore.manifest`。**文件层死路** |
| 头往前移能修朝向 | 几何/权重/绑定姿势与作者逐顶点一致，位置本来就对。真因是骨骼顺序 |
| UE4SS 的 `LoadAsset` 能拿资产 | 本机实测：`Asset was found but not loaded, could be a package`，返回 `<bad>`。**这条路在本作不通**（但 `FindAllOf` 拿组件是通的） |

---

## §8 用户明确提出的需求清单（**未完成项，必须继续做**）

### 8.1 白衣无常（主线，未完成）
- [ ] **颜色**：衣服必须显示明末原版材质（裙面花纹、腰带红穗、骨色护肩、皮肤肤色），不能是灰白。
- [ ] **头部朝向**：脸必须朝正前方（现在偏身体右侧，马尾方向是对的参照）。
- [ ] **五官**：不能错乱（已修过一次"睫毛套用眼球贴图"的 bug，但整体仍乱，根因是骨骼顺序）。
- [ ] **前臂**：形状明显不对（同样是骨骼顺序/FBX 链路问题）。
- [x] 删掉腰带正面骷髅（连舌头一起删，52558 → 46002 面）
- [x] 独立新增外观，**不依赖狐雨 / 织绣海寇**
- [x] 槽位落在"第 6/7 个已解锁的 Codex 槽"

### 8.2 鞋（未完成）
- [x] 已累计抬高 13mm（鞋底 Zmin 从 +1.98 调到 −4.36）
- [ ] **再抬约 5mm**（用户最新要求，累计约 18mm）
- 用户倾向"**不动网格**"的抬法（作者《修复方案》也这么建议：改网格容易把脚底踩穿/悬空）→ 可考虑改 Skeleton 的 foot 骨偏移或 PhysicsAsset，而非改顶点。

### 8.3 婉若游龙网鞋覆盖（支线，反复失败）
- [ ] 把作者 `PBZ_WanRuoYouLong_3800` 的下装换成 **"Dragon heels NSFW" 那套龙纹高跟网鞋 + 光腿 + 无内裤**，保留长裙与上装。
- 源：`E:\steam\steamapps\common\Wuchang Fallen Feathers\~mods\婉若游龙 网鞋\Dragon heels NSFW_p.pak`（19.9MB，**只替换 `WuCh_LTZ_Pants.uexp`**，没有独立鞋子资产）
- 已做到：把替换后的下装几何 dump 出来（28212 顶点 / 76695 索引 / 3 段），按骨名映射（`SDtui_*→thigh_l/r`、`Knee_*→calf`、`Ankle_*→foot`、`Toes_*→ball`、中线骨→pelvis），并入婉若游龙身体，做成独立路径 `SK_YLWangxieBody`（REFBONES 1134，骨骼顺序=游戏原序 ✓）。
- **失败点**：覆盖不生效。已排除"包名排序"（改成 `zzz0_` 仍无效）。`【推断】`真因是**同包路径只有一份 + 作者的 GameFeature 会在运行时把网格改回去**（`BPC_CollectionVisual*` 会 `SetSkeletalMeshAsset`）。
- **下一步建议**：不要跟作者的包抢同一路径，而是**做成独立外观**（自己的命名空间 `/Game/Mods/PBZYLShoe/`、自己的一行外观表、自己的表合并），或者直接在运行时用 UE4SS/TS `SetSkeletalMeshAsset` 覆盖（并在每帧重设，因为作者组件会改回去）。

### 8.4 头部改用作者新包里的短发海寇头（未做，**优先**）
- 作者 11-04 整合包里的 `zzzzzzz_PBZ_Corsair_3304_P`（135MB）**自带短发**，骨骼顺序天然正确。
- 用它当 `HeadAsset` 可**一次性解决**三件事：不用剪发、没有朝向错、没有骨骼重排。
- 需要确认：该包的头是"海寇·明末"外观的 HeadAsset，路径形如 `/Game/Mods/PBZxxx/Meshes/SK_...Head`，可在 `DT_PBZAppearanceTable` 里查到（`izprobe ROWJSON`）。

### 8.5 脖子角度 / 领口穿模（已有结论）
- 明末的颈部与胸口皮肤属于**上装**，不属于头。作者的做法是**把领口做进身体网格本身**，与身体共用蒙皮，脖子怎么转都跟着变形 → 结构上不会穿模。
- 结论：**不要**给紧贴骨头的衣服做独立附件/独立网格；**并进身体网格重绑权重**。
- 婉若游龙 mod 里也没有独立颈部网格（`SK_WanRuoYouLongBody` 里就有 `MI_Wuchang_Head` 段）。

### 8.6 其他（用户提过）
- [ ] 马尾 `k=0.34`（织绣黑色马尾截短）—— 现在实装是**棕色**，说明我们的 MI 没生效（头发走 Groom 材质），或用的是原版头发。
- [ ] 手：明末女眷套（裸前臂 + 红绳 + 长指甲）
- [ ] 下装：细带高跟 + 光腿 + 无内裤

---

## §9 待验证假设（按优先级 + 验证方法）

| # | 假设 | 怎么验 | 判据 |
|---|---|---|---|
| 1 | 关闭 `bShareMaterialShaderCode`（False）并**只把材质打进包**，能解决灰 | 改 `DefaultGame.ini` + `DefaultEngine.ini`，重建 27 个 MI，cook+打包，看 `MI_*.uexp` 是否变成几十~几百 KB（自带 shader） | 变红/变色 = 成立 |
| 2 | 我们的 MI 在运行时 `Parent` 解析为 `<null>` | 用 `main.ts` v4 打印每槽 `Parent` | `<null>` = 成立，说明父级没解析 |
| 3 | 贴图在运行时加载失败（`GetSizeX=0`） | 同上，打印 `Albedo` 的 `Blueprint_GetSizeX/Y` | `0x0` = 成立 |
| 4 | 作者的 GameFeature 组件在运行时把网格/材质改回去了 | 打印组件 `SkeletalMesh` 路径 + 槽材质；每帧对比 | 换完又变回 = 成立 → 必须用"独立命名空间 + 自己的表"或每帧重设 |
| 5 | 外观表"混装"是婉若游龙不生效的主因 | 只留作者包 + 我们的包，其余全移走；对比 | 生效 = 成立 |
| 6 | 头部问题纯粹是骨骼顺序 | 用 `Hun_Skin_Skeleton.fbx` 当骨架、按骨名搬权重重建头 | `REFBONES 1134` 且顺序=游戏原序 = 成立 |

**验证 #2/#3 的现成脚本**：`PBZ\ProjectPBZ\PBZModLoader\mods\baiyi-probe\main.ts`（v4，已过 SDK 类型检查，未实跑）。
日志位置：`ProjectPBZ/PBZModLoader/evidence/<时间>/loader.log`，**只捕获 `[PBZMOD]` 前缀**。

---

## §10 关键脚本 / 文件索引

### 10.1 本工程（`E:\steam\steamapps\common\PBZ\workbuddy`）

| 文件 | 作用 |
|---|---|
| `ueproj/ProjectPBZ/ProjectPBZ.uproject` | UE 工程（含自定义 C++ 模块 `ProjectPBZ`，复刻 `PBZAppearanceStruct`） |
| `ueproj/ProjectPBZ/Source/ProjectPBZ/Public/PBZAppearanceStruct.h` | 35 字段结构 + `FlowLocText` + `AppearanceClothData` + `AppearanceGroomData` |
| `ueproj/ProjectPBZ/Config/DefaultGame.ini` | `bShareMaterialShaderCode`、`DirectoriesToAlwaysCook` |
| `ueproj/ProjectPBZ/Config/DefaultEngine.ini` | **另有一份** `bShareMaterialShaderCode`，会覆盖前者 |
| `ueproj/mats_mi.py` | 建 17 + 10 个 `MI_BY_*`，设 Albedo/Normal/Mix + 19 标量 + 5 向量 |
| `ueproj/make_master_mask2.py` | 建占位母材质 `Plugins/AkashaEffects/.../MAI_Equipment_Mask`（**不随包发**） |
| `ueproj/reimport_tex.py` | 强制重导 27 张 TGA（`replace_existing=True`） |
| `ueproj/make_vt3.py` / `make_novt.py` | 开/关虚拟纹理（注意：重导会重置，顺序必须在导入之后） |
| `ueproj/build_dt.py` | 建 69 行 `DT_PBZAppearanceTable` |
| `ueproj/build_dt_wr.py` / `dup_wr_mesh.py` / `assign_wr_mats.py` | 婉若游龙覆盖用：重建 108 行表 / 复制网格到独立路径 / 按槽名指材质 |
| `ueproj/rebuild_v24.sh` | cook + 清引擎内容 + UAT stage + 打包 一键脚本（`RUN=runN` 控制暂存目录） |
| `tools/pack_baiyi17.py` | 把 stage 出的容器封成 `~mods` 三件套 |
| `tools/pack_wr.py` | 婉若游龙覆盖包专用封包 |
| `tools/bl_export_fbx.py` / `bl_export_head.py` | Blender 导出（`arm.name="Armature"`；头要 ×100 并 apply） |
| `tools/bl_fix_armature.py` | 只改骨架对象名为 `Armature` 后重导（head 修复用） |
| `tools/bl_ltz_wangxie.py` | 把 dump 出来的网鞋下装并进 LTZ 身体 |
| `PROGRESS_材质排查.md` / `HANDOFF.md` | 早前的进度文档（材质部分/全量部分） |
| `outgoing/白衣无常-源模型-给作者/` | 交给作者的源模型包（2 FBX + 27 PNG + `NOTES.md` + `修复方案.md`） |

### 10.2 运行时

| 路径 | 说明 |
|---|---|
| `PBZ\ProjectPBZ\PBZModLoader\mods\baiyi-probe\main.ts` | 运行时诊断/修复探针 v4 |
| `PBZ\ProjectPBZ\PBZModLoader\evidence\<时间>\loader.log` | 加载器日志（只看 `[PBZMOD]`） |
| `PBZ\platform\steam\ue4ss\Mods\PBZProbe\` | 旧 UE4SS Lua 探针（**已停用**，`mods.txt` 里 `PBZProbe : 0`） |
| `PBZ\platform\steam\ue4ss\Mods\BaiyiUnlock\` | 旧解锁脚本（已停用，早期崩过两次） |

### 10.3 当前 `~mods` 状态（接手时先看这里）
- 我们的：`zzzzzzzz_PBZ_Baiyi_3002_P.*`（27.4MB ucas，含 `T_Test_Red` 引用但**该贴图未进包**）、`zzz0_PBZ_WanRuoYLshoe_P.*`（1.99MB）
- 作者的：`zzzzzzzz_PBZ_WanRuoYouLong_3800_P`、`Corsair_3304`、`SilkCorsair_2301`、`GoldenTiger_2302`、`FoxRain_2208`、`BaiChiLianPlayer_2034`、`ObsessionDemon_3500`、`NianSuiChang_3301`、`ToadChief_3302`、`Yennefer_3303`、`QueenMarika_3900`、`Tachy_3700`、`Converted_*` 等
- 作者的**辅助包**（关键，见 §4 架构 C）：`OutfitCoexistence_9900`、`CollectionWardrobe_9920`、`CollectionVisuals_9940`、`WardrobeReopen_9941`、`BaiScopedRepair_9942`、`CollectionRelease_9943`、`MuHeadVisibility_9944`、`ClimaxPreviewHair_9945`
- 其他：`zzz_PBZ_WuchangVoice_999_P`（3.4GB）、`zzz_PBZ_WuchangFangYao_1005_P`

---

## §11 版本履历（v1 → v24，只记"改了什么 + 结果"）

| 版本 | 关键改动 | 结果 |
|---|---|---|
| v9 | 外观表、iostore 打包 | 切外观必崩 |
| v10 | 骨架容器改名 `Armature`（1135→1134） | 仍崩 |
| v11 | 放弃自建 base Material，改 MaterialInstance | **不崩了**，白模 |
| v12~v13 | 补 15 个参数；贴图改虚拟纹理 | 仍白 |
| v14~v20 | 补外观表、修路径/尺寸/鞋高 | 能穿上，全灰 |
| v21 | 父材质改成 `MAI_Equipment_Mask` | 仍灰 |
| v22 | `bShareMaterialShaderCode=True`；albedo alpha 全改 255 | 仍灰 |
| v23 | 不发任何 JS；VT 用专用 API 重建 | 仍灰 |
| v24 | ①MI 砍到只设 3 个贴图参数 ②修眉毛/睫毛贴图串位 ③剔除 24 个占位材质 ④强制重导贴图让 alpha 真进包 ⑤参数恢复成作者那套 ⑥ORM 改 MRA ⑦换成原版 D/N/R 三件套 | **仍灰**（期间出现过肤色/变白，但最终一致灰白） |
| **v25** | **给占位母材质补上 Material Usage 标记（`used_with_skeletal_mesh` 等 5 个）**，重建 25 个 MI 后重新 cook | **待验证**。证据：`MI_BY_M_HWC_Qunzi.uexp` 从 **4687 → 8095 字节**（+3408），uheader 2033 → 2310；说明 MIC 里烘进去的 `FMaterialCachedExpressionData` 结构变了 |
| 支线 | 婉若游龙网鞋覆盖（`zzz0_` 包） | 不生效（现已移出 `~mods`，放在 `Paks/_held_wr_side/`） |

---

## §12 硬约束与风险清单（**踩过的坑，别重犯**）

1. **`~mods` 里任何含 JavaScript 的 .pak → UI 文字变 `{ButtonText}`**。别发 JS。
2. **绝不要把 `Engine/` 任何文件打进 mod**（`Engine/Config/*.ini`、`GlobalShaderCache-*.bin`）；也不要在 stage 时带 `ShaderArchive-*`。
3. `UnrealPak` 打 legacy pak 清单必须 **LF**；dest 写 `..\..\..\ProjectPBZ\...`；首行放 `..\..\..\Engine\Pad.txt`。
4. **不要用 `rm -rf` 删 `Cooked/`、`StagedBuilds/`**（会被安全策略拦），一律 `mv` 到 `_held_*`。
5. `unzip "PRBModLoader/*"` **不会解出 `compiler/` 子目录**，必须整体解压。
6. UEModManager 的 `mods.json` 里 `enabled:false` 会**清理文件**，表现为"文件自己消失"。
7. 游戏运行中 `~mods` 里的 `.utoc/.ucas` 被占用，覆盖会失败 → 先确认 `tasklist | grep PBZ.exe`。
8. 游戏日志 `%LOCALAPPDATA%\ProjectPBZ\Saved\Logs\ProjectPBZ.log` 是**加密的**（文件头 `PBZLOGE1`），读不了。可靠日志只有 `ue4ss\UE4SS.log`、`PBZModLoader\evidence\*\loader.log`、`platform\steam\ReShade.log`。
9. 我们的容器**不带 `global.utoc`**；作者的发（4.4MB）。目前看不是必需的，但混装时若出现全局解析异常，可以试补。
10. `izprobe` 读 `~mods` 目录会报 `Found IoStore Package but global data is missing` → **要把目标包复制到临时目录并配一份 `global.utoc/global.ucas`** 才能读（`workbuddy/tmp_silkpk/`）。

---

## §13 一页速查（常用命令）

```bat
:: ===== 读 PBZ 容器内容 =====
UnrealPak.exe "<xxx.utoc>" -List
UnrealPak.exe "<xxx.utoc>" -Extract "E:\out"          :: 注意是空格，不是 -Extract=

:: ===== 读资产（自研工具）=====
izprobe.exe "<Paks目录含global>" 0x4BC8...E01D "<usmap>" MESH  "ProjectPBZ/Content/Mods/xxx/Meshes/SK_XXX"
izprobe.exe ... PARAM   "ProjectPBZ/Content/Mods/xxx/MaterialInstances/MI_XXX"
izprobe.exe ... ROWJSON "rows.json"
izprobe.exe ... EXPORT  "<asset>" "E:\out"            :: 导成 glb，便于数值比对

:: ===== 读明末资产 =====
wcdump.exe "<明末Paks>" "<明末usmap>" MAT  "Assets/Character/player/player_wuchang_rebined/cloth/BWC/Mat/M_HWC_Qunzi"
wcdump.exe ... EXPORT "<asset>" "E:\out.txt"          :: 自定义顶点/索引/骨骼格式

:: ===== cook + 打包 =====
set TMP=D:\UETemp & set TEMP=D:\UETemp & set UE-LocalDataCachePath=D:\UEDDC
UnrealEditor-Cmd.exe "<uproject>" -run=pythonscript -script="<脚本>.py" -unattended -nosplash -nop4 -stdout
UnrealEditor-Cmd.exe "<uproject>" -run=cook -targetplatform=Windows -unattended -nop4 -stdout
RunUAT.bat BuildCookRun -project="<uproject>" -noP4 -platform=Win64 -clientconfig=Development -skipcook -stage -pak -iostore -utf8output -unattended

:: ===== retoc（需自行安装，社区标准流程）=====
retoc.exe -a 0x4BC8...E01D to-legacy -f "<资产. uasset>" --no-shaders --version UE5_7 -v "<游戏Paks>" "<out>"
retoc.exe to-zen --version UE5_7 -v "<out>" "<out>\MyMod_P.utoc"

:: ===== 运行时探针 =====
:: 装 PBZModLoader 后，main.ts 改完自动重编译；进游戏后按 Alt+F5 热重载
:: 日志：ProjectPBZ\PBZModLoader\evidence\<时间>\loader.log（只抓 [PBZMOD] 前缀）
```

---

## §14 建议的接手路线（如果我是下一个模型，我会这么做）

1. **先装 retoc + UAssetGUI**（半小时），做一次"最小可行实验"：
   拿游戏自带的 `MI_ZeroHun_Cloth_01_b` → to-legacy → UAssetGUI 把 Albedo 换成纯红 → to-zen → 丢 `~mods` → 看官方的白衣（`ZeroHun_Cloth_01`）是否变红。
   **这一步能一次验证三件事**：retoc 链路可用 / UAssetGUI 能改 MI / 游戏能加载我们打的容器。
2. 通了之后，把我们的 8 个材质按同法各做一份（改名到自己的命名空间），配我们的 D/N/R。
3. 网格侧：头部改用作者的 `Corsair_3304` 短发头（省事且骨骼天然正确）。
4. 婉若游龙支线**暂缓**——它的失败很可能来自作者的 GameFeature 运行时重设，先确认 §9 假设 #4。
5. 每一步都**只改一个变量**，并把"这一次能判定什么"写清楚再让用户启动。

---

## §15 附：用户提供的《修复方案.md》摘要（作者写的，部分已被后续数据修正）

作者原话要点：
1. `ReferenceSkeleton` 骨骼**数量与名字相同、只有顺序不同**（`[1]` 是 `pelvis` 还是 `ik_weapon_root`）→ 用「网格来自 glTF + 骨架来自 `Hun_Skin_Skeleton.fbx` + 按骨名搬权重」。
2. **MI 父级必须是游戏原件**；自建占位母材质 → **参数静默失效**。
3. 鞋底抬高**不要动网格**。
4. 建议做二分测试：只改一个槽的 Albedo 为纯红，看是否生效，以判定"参数覆盖整条链是否活着"。

> **我们的实测对第 4 条的结论**：那次红图测试**无效**——`T_Test_Red` 因为 cook 未收录而没有进包，`Albedo` 指向了不存在的包，所以"没变红"不能证明参数不通。**这个二分测试必须重做**（用 retoc/UAssetGUI 路线做，或先把贴图确认打进包再做）。

---

*文档结束。有任何一条你认为是错的，请先用工具验一遍再推翻——这个项目已经被"看起来合理的推断"坑过太多次。*
