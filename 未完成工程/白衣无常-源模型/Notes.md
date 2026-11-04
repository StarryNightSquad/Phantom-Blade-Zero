# 白衣无常（明末无常）→ 影之刃零 · 移植工程留档

生成时间：2026-11-05
用途：请人帮忙诊断 / 接手修正用。**不是可直接安装的 mod**，是可以直接导入 UE 的源资产。

---

## 一、这套东西是什么

把《明末：渊虚之羽》主角无常的服装，做成影之刃零的**独立新增外观**（不替换原版）。

| 部位 | 来源 | 备注 |
|---|---|---|
| 上装 | 明末 白衣无常（内部材质名 `M_HWC_*`，HWC = 海寇） | 肩上骷髅已删（含舌头，52558→46002 面） |
| 小臂 / 手 | 明末 女眷套 | 裸前臂 + 腕上红绳 + 长指甲，按游戏骨架重绑，缩放 0.9384 |
| 下装 | 细带高跟 + 光腿 | 无内裤 |
| 鞋 | 白色细带高跟 | 鞋底 Zmin = −4.360（累计抬高 13mm） |
| 头 / 发型 | 织绣海寇的头部 | 马尾沿轴缩短到 k=0.34 |

## 二、文件

```
Baiyi_Final.fbx    身体（17 个材质槽，54927 顶点）
Baiyi_Head.fbx     头部（10 个材质槽，42263 顶点）
tex/*.png          27 张贴图（albedo / 法线 / ORM 等）
```

两个 FBX 都已经：
- 骨架容器节点改名为 **`Armature`**（UE 只跳过叫这个名字的容器节点，否则会多生成一根假根骨，骨骼总数 1135 而不是 1134，切外观必崩）
- 单位 ×100（glTF 米制 → UE 厘米）
- 导出参数：`axis_forward='Y', axis_up='Z'`，`apply_scale_options='FBX_SCALE_ALL'`，`add_leaf_bones=False`

## 三、导入方式（我们用的）

- 骨架：`/HuaShira/Characters/Hero/Hero_Hun/Hun_Skin_Skeleton`（游戏插件根，**不是** `/Game/HuaShira/...`）
  - 必须用 `unreal.load_asset()` 取骨架；`EditorAssetLibrary.load_asset` 对插件内容会返回 None，
    结果 UE 会自动新建一个 `_Skeleton`，白折腾
- 导入后校验：`ReferenceSkeleton` 应为 **1134 根、第 0 根是 `root`**
- 外观：`DT_PBZAppearanceTable` 是**三行一组**（Outfit 行只写 ItemId，Body 行给 `BodyMeshAsset`，Head 行给 `HeadAsset`）
- 材质：每个槽一个 `MaterialInstanceConstant`，父级
  `/AkashaEffects/MaterialLibrary/Template/Character/MAI_Equipment_Mask`

## 四、材质参数（照 PBZ_WanRuoYouLong_3800 的 MI_YL_Shangsheng 填的）

```
Scalar(19): ReplaceAlpha=0  Normal Strength=1  AO Min=0  AO Exponent=1
            Roughness Min=0  Roughness Max=1  Roughness Exponent=1
            Metallic Min=0   Metallic Max=1   Specular=0.5
            Mask Sharpness=0 Mask Bias=0       Mask Final Multiply=1
            Tile=1 Tile_U=1 Tile_V=1 Tile ApplyObjectScale=0
            Use UV2 (For Scene Materials)=0    OpacityThreshold=0.3333
Vector(5):  AO Channel=0000FF  Roughness Channel=00FF00  Metallic Channel=FF0000
            Albedo Controls=FFFFFF  Albedo Overlay=BCBCBC
Texture(3): Albedo / Normal / Mix
```

`T_BY_ORM` 已按 **MRA** 打包（R=Metallic(0)、G=Roughness(179)、B=AO(255)），与上面的通道向量一致。

## 五、目前卡住的问题（重点）

1. **材质不生效**：换成游戏里显示的是整体金属感 / 均匀灰，贴图看不出细节。
   已经排除的：
   - 贴图内容 —— 从成品 pak 里解出来 RGB 与源 PNG 逐像素一致
   - UV —— 网格 TEXCOORD_0 与原始的织绣海寇头一致
   - ORM 通道 —— 已按 MRE/ARM 两种打包都试过，并显式设置了三个通道向量
   - 虚拟纹理开关 —— 开/关都试过
   - 材质挂载 —— 运行时实测 17 槽 / 10 槽全部指向我们的 MI，类型是 `MaterialInstanceConstant`
   - MI 参数 —— 从成品里读出来，与 MI_YL_Shangsheng 逐项一致
   → 怀疑是「MI 是在编辑器里从空 MI 新建、父级指向自建的**占位**母材质」，
     cook 后内嵌的 `FMaterialCachedExpressionData` 与真母材质不一致，导致参数绑不上。
     作者的做法是**拿游戏自带的 `MI_ZeroHun_Cloth_01_b` 复制改名再换贴图**，
     这可能是关键差异。

2. **头部朝向错**：游戏里面朝身体右侧。查到原因是**骨骼顺序被打乱**：
   ```
   我们的头 SK_GoldenTigerHead     0 root 1 ik_weapon_root 2 ik_weapon_r … 16 pelvis
   海寇原头 SK_SilkCorsairHead     0 root 1 pelvis 2 spine_01 …
   我们的身体 SK_GoldenTigerBody   0 root 1 pelvis 2 spine_01 …   ← 身体是对的
   ```
   骨骼总数都是 1134，但头部走的是 glb 自带骨架（Blender 按 DFS 重排），
   身体走的是 `Hun_Skin_Skeleton.fbx` 的原始顺序。**头部需要按原骨架顺序重导。**

3. **前臂错乱**：女眷手是按「肘→腕相似变换」搬的权重，可能少了一节。

4. **鞋底还想再抬约 5mm**。

## 六、求助方向

最想知道两件事：
1. 我们这套 MI 为什么在游戏里不上色？（和作者的 MI 相比，除了父级是自建占位材质，还有别的差异吗）
2. 头部有没有更稳的做法，能保证导入后骨骼顺序和游戏骨架一致、不出现朝向错误。
