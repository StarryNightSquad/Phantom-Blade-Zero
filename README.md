# Phantom Blade Zero · Mod 工程留档

影之刃零（Phantom Blade Zero）的 mod 制作留档。当前重点是**把《明末：渊虚之羽》的服装移植进来**，
做成独立新增外观（不替换原版服装）。

> 这里放的是**可直接导入 UE 5.7 的源模型 + 完整技术记录**，不是可直接安装的 mod。
> 三个套装都已处理到「只差材质着色」这一步。

---

## 目录

```
未完成工程/
├── 白衣无常-源模型/        Baiyi_Body_ShortHair.fbx + HaiKou_ShortHair_Head.fbx + 40 张贴图
│                          明末「无常」白衣无常。上装已删肩上骷髅，女眷手（裸前臂+红绳+长指甲），
│                          细带高跟 + 光腿 + 无内裤。18 槽 / 1134 骨。
│
├── 流云织羽-源模型/        WuchangLiuyun_Body_fix.fbx + HaiKou_ShortHair_Head.fbx
│                          明末「流云织羽」(HD)。13 槽 / 1134 骨。**无贴图**。
│
└── 婉若游龙-源模型/        WuchangLTZ_Wangxie.fbx + HaiKou_ShortHair_Head.fbx
                           明末「婉若游龙」(LTZ)。**下装换成龙纹网鞋 + 光腿 + 无内裤，长裙保留**。
                           15 槽 / 1134 骨 / 137,850 顶点。**无贴图**。

幻鬼mod/                    另一个作者做的幻鬼套，作为参照
```

每个目录里的 `README.md` / `Notes.md` 都写了：骨架校验、**每个材质槽用哪张贴图**、
外观表三行定义、已解决的问题清单、以及卡在哪。

---

## 三套共用的头

`HaiKou_ShortHair_Head.fbx` —— **原生短发**，取自作者「海寇·明末」包的 `SK_CorsairHead`：

```
骨架对象 Armature   1134 根   41,764 顶点   10 个材质槽
```

用它是因为：① 我们需要的短发它自带；② 它本来就是用**游戏骨架**导出的，
骨骼顺序天然正确，不存在「Blender 过 glTF 后被 DFS 重排 → 蒙皮把头顶歪」的问题。

---

## 导入 UE 的三条硬要求

1. **骨架容器对象必须叫 `Armature`**
   UE 只跳过这个名字的容器节点，叫别的（如 `HunSkinSkel`）会让 `ReferenceSkeleton`
   多生成一根假根骨 → **1135 根** → 切换外观时崩 `0xC0000005 @ +0x306E8CD`
2. **缩放 ×100** —— glTF 是米制、UE 是厘米，不放大头只有 1/100 大
3. **骨骼顺序必须是游戏原序** `root, pelvis, spine_01, spine_02, …`
   被重排后 `ik_weapon_root` 会跑到第 1 位、`pelvis` 掉到第 16，蒙皮会把头顶歪
   （表现像「脸朝向错误」，本质是权重挂到了错的骨头）

三个 FBX 都已满足。导入后自检：`bones == 1134` 且第 0 根是 `root`。

---

## 唯一未解决：材质实例不着色

游戏里表现为**均匀金属灰**。已排除贴图内容、alpha、UV、槽位挂载、参数名、表指向。

**根因（实测数据）**：

```
作者可用的 MI   uexp 682 字节
我们 cook 的    uexp 214 字节   ← 没有材质参数，也没有着色器缓存
```

因为父级指向我们自己造的「**同路径但节点是空的**」占位母材质。两条可行路径：

1. **在编辑器里复刻母材质** `MAI_Equipment_Mask` 的节点连线：
   `TextureSample(Albedo) → BaseColor`、`Mix 的 R/G/B → Metallic/Roughness/AO`、
   `Normal → Normal`、`Albedo.a → OpacityMask`
2. **复制游戏原版 MI 改名换贴图**（社区标准做法，需 UAssetGUI 手工操作）

---

## 工具链的硬边界（都是实测，别白试）

| 现象 | 原因 |
|---|---|
| UnrealPak 打 retoc 产出的 uasset 时崩 | `LogUnrealNames: String is too long` + `Assertion failed: Header.Len != 0` (UnrealNames.cpp:2422) —— 两套工具对 UE5.7 FName 编码实现不一致 |
| retoc 读不了 UE cook 产物 | `Extracted 0 (78 failed)`，报缺 `ScriptObjects` chunk，加 `--no-script-objects` 也一样 |
| 游戏启动崩 `Missing global shader FCombineFilteredImageCS` | UAT 打 iostore 时把 `Config/DefaultEngine.ini`、`Content/JavaScript/MainStart.js`、`AssetRegistry.bin`、`Engine/Content/...` 等 **698 个文件 / 2.93 MB** 塞进了 `.pak`，顶掉游戏本体。修法：`.pak` 只留 **456 字节占位**，资产全走 `.utoc/.ucas` |

**结论**：UE 那条链路（`UnrealPak` / UAT）和 retoc 那条链路**不能混用文件**，
必须各自独立打包。多套装共存时，两套素材要分成两个包。

---

## 其他踩过的坑

| 现象 | 原因 / 修法 |
|---|---|
| 摆大字、没动作、没头 | 骨架挂载路径写成 `/Game/HuaShira/…`，应为 `/HuaShira/…`（插件根） |
| 衣柜里看不到新服装 | 缺 `DT_PBZAppearanceTable`。每套 3 行：Outfit（只声明 ItemId）+ Body（BodyMeshAsset）+ Hairstyle（HeadAsset） |
| 界面文字变成 `{ButtonText}` | `~mods` 里**任何**含 JavaScript 的 `.pak` 都会触发。彻底不发 JS |
| 手臂在动作里塌陷 | 完全没有 twist 骨权重（作者占 14,049 顶点，我们 0）。按肘→腕参数 t 拆分给 `lowerarm_twist_01/02`，**每顶点限 4 骨**，否则 UE 直接丢弃 |
| 多个 mod 同存时我们的改动无效 | 30 个包里有 **24 个都提供同一张 `DT_PBZAppearanceTable`**，按文件名排序后加载，我们的被别人的覆盖 |

---

## 外部资料

- [PBZ 解包教程（3DM）](https://bbs.3dmgame.com/thread-6716842-1-1.html) —— 全网唯一的影之刃零专属流程帖，只覆盖到「解包 + 导出模型」
- [retoc](https://github.com/trumank/retoc) —— IoStore 双向转换（`to-legacy` / `to-zen`），已支持 UE5.7
- [UAssetGUI](https://github.com/atenfyr/UAssetGUI) —— 修改 legacy 资产属性
- [phantombladezero_cppbypass](https://github.com/KintaroModding/phantombladezero_cppbypass) —— UE4SS C++ mod，绕过 2026-11-04 更新后的脚本校验器（JS 路线需要它）
- [PBZModLoader](https://www.nexusmods.com/) —— TypeScript mod 加载框架，`mods/<id>/main.ts`，Alt+F5 热重载
