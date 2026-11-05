# 流云织羽 · 源模型（短发版）

《明末：渊虚之羽》的「流云织羽」（内部代号 `HD`）套装 → 影之刃零移植用的**源模型**。
已过 Blender 处理，可直接导入 UE 5.7。**只差材质着色**（与白衣无常同一问题，见文末）。

最后更新：2026-11-05 12:00

---

## 文件

| 文件 | 大小 | 内容 |
|---|---|---|
| `WuchangLiuyun_Body_fix.fbx` | 11.9 MB | 身体，3 mesh / 13 材质槽 / **1134 骨** |
| `HaiKou_ShortHair_Head.fbx` | 11.7 MB | 头部，取自作者「海寇·明末」包（**原生短发**）/ 10 槽 |

> **本目录没有贴图**。流云织羽的贴图在整个工程里从未导出过
> （我们只做到躯干几何）。要做完整需从明末原包导出 HD 套的 `_D / _N / _R`：
> ```bat
> wcdump <明末Paks> <usmap> LS "cloth/HD/"
> wcdump <明末Paks> <usmap> MAT "Assets/Character/player/player_wuchang_rebined/cloth/HD/Mat/<材质名>"
> ```
> 明末 AES key：`0xC46B1A3D21AC9F6DF57A45A24CC479B413E3F326F93AB46DCFE0E0120DCFFBC8`

---

## 骨架

```
骨架对象名 = Armature          1134 根          顺序 = 游戏原序
```

三条硬要求（与白衣无常相同）：

1. 骨架容器对象必须叫 `Armature` —— 否则 `ReferenceSkeleton` 多一根假根骨（1135）→ 切外观崩 `0xC0000005`
2. 缩放 ×100 —— glTF 米制 → UE 厘米
3. 骨骼顺序必须是 `root, pelvis, spine_01, spine_02, …` —— 被 DFS 重排会导致蒙皮把头顶歪

> 原始未修版叫 `WuchangLiuyun_Body.fbx`，骨架对象名是 `HunSkinSkel`。
> **别直接用它**，一定用本目录这个 `_fix` 版。

---

## 材质槽（3 mesh / 13 槽）

### `WUCH_HD_Jacket` — 14,821 顶点 / 8 槽

| 槽 | 名称 | 含义 |
|---|---|---|
| 0 | `MI_Head` | 头部（由 HeadAsset 提供，此槽可忽略） |
| 1 | `M_HD_HW` | 护腕 |
| 2 | `M_HD_yumao` | 羽毛装饰 |
| 3 | `MI_Body` | 身体皮肤 |
| 4 | `yumao` | 羽毛（另一段） |
| 5 | `M_HD_QZ` | 裙子主体 |
| 6 | `M_HD_SB` | 手臂 |
| 7 | `invisible` | 隐藏段 |

### `WUCH_HD_Pants` — 7,614 顶点 / 3 槽

| 槽 | 名称 | 含义 |
|---|---|---|
| 0 | `MI_Body.001` | 腿的皮肤 |
| 1 | `M_HD_XZ` | 靴子 |
| 2 | `M_HD_HW.001` | 护腕（下段） |

### `WUCH_HD_Hands` — 5,191 顶点 / 2 槽

| 槽 | 名称 | 含义 |
|---|---|---|
| 0 | `M_HD_SB.001` | 手臂皮肤 |
| 1 | `MI_Body.002` | 手部皮肤 |

> 材质前缀是 `M_HD_*`。**不要和婉若游龙的 `M_WuCh_LTZ_*` 混**，两套是不同服装。

---

## 外观表

与白衣无常完全相同的结构，每套 3 行：

```
Hun_OutFit_CodexXXX          AppearanceType = Outfit
CodexXXX_Body                AppearanceType = Body        BodyMeshAsset = SK_LiuyunBody
CodexXXX_Head                AppearanceType = Hairstyle   HeadAsset     = SK_CorsairHead
```

官方预留 5 个 Codex 槽位：
`CodexFY / CodexFoxRain / CodexSilkCorsair / CodexGoldenTiger / CodexMuXiaoKui`

---

## 头部材质槽（`HaiKou_ShortHair_Head.fbx`）

原生短发，游戏骨架导出，1134 骨，41,764 顶点，原版 13 槽去重后 10 槽：

| 槽 | 名称 | 含义 |
|---|---|---|
| 0 | `MI_FO_bfa4d791a5f2` | 头发（占原版 5 槽） |
| 1 | `MI_FO_934b31c540d2` | 发饰 |
| 2 | `MI_Wuchang_Brows_67630add` | 眉毛 |
| 3 | `MI_Wuchang_Eye_7f573563` | 眼球 |
| 4 | `MI_Wuchang_Eyelash_5157e96a` | 睫毛 |
| 5 | `MI_Wuchang_Head_eedd7a66` | 脸部皮肤 |
| 6 | `MI_Wuchang_Tear_7427bc8b` | 泪痕 |
| 7 | `MI_teeth_low_2e7ba38b` | 下牙 |
| 8 | `MI_teeth_up_9d491ce7` | 上牙 |
| 9 | `MI_tongue_8777624a` | 舌头 |

---

## 已知问题

**材质不着色 —— 与本仓库 `白衣无常-源模型/Notes.md` 里写的是同一个根因**：

```
作者可用的 MI   uexp 682 字节
我们 cook 的    uexp 214 字节   ← 没有材质参数，也没有着色器缓存
```

父级指向自造的「同路径但节点是空的」占位母材质。解法两条：
1. 编辑器里复刻 `MAI_Equipment_Mask` 的节点连线
2. 复制游戏原版 MI 改名换贴图（UAssetGUI 手工）

另外两项：
- 本目录**没有贴图**（见上文）
- 流云织羽的「长靴」是原版 `M_HD_XZ` 那一段，是否要换成高跟/网鞋由你决定

---

## 工具链硬边界（实测）

- UE 的 UnrealPak **读不了** retoc 产出的 uasset（`String is too long` / `Header.Len != 0`）
- retoc **读不了** UE cook 产物（`Extracted 0 (78 failed)`，缺 `ScriptObjects`）
- → 两条链路不能混，必须各自独立打包
- UAT 打 iostore 会往 `.pak` 里塞 `Config/DefaultEngine.ini`、`MainStart.js` 等 698 个文件，
  顶掉游戏本体 → 启动崩 `Missing global shader`。**`.pak` 必须只留 456 字节占位**。
