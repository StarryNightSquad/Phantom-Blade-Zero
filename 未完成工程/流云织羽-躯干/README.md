# 流云织羽（HD）· 躯干

《明末：渊虚之羽》的「流云织羽」套装躯干，移植到影之刃零用的源资产。

## 文件

```
WuchangLiuyun_Body_fix.fbx    躯干（含腿）
```

## 已经做过的处理

- 骨架容器节点改名 **`Armature`**
  这是必须的：UE 只会跳过叫这个名字的容器节点，否则会多生成一根假根骨，
  骨骼总数变成 1135 而不是 1134，**切换外观时必定崩溃（0xC0000005）**。
- 校验结果：`ReferenceSkeleton` = **1134 根**，第 0 根是 `root`，
  骨骼顺序与游戏骨架一致（`root, pelvis, spine_01, spine_02, spine_03, …`），不是 Blender 的 DFS 顺序。
- 单位 ×100（glTF 米制 → UE 厘米）
- 导出参数：`axis_forward='Y'`, `axis_up='Z'`, `apply_scale_options='FBX_SCALE_ALL'`, `add_leaf_bones=False`

原始（未修骨架）的 `WuchangLiuyun_Body.fbx` 里骨架对象叫 `HunSkinSkel`，直接导入会多一根假根骨，不要用那个。

## 材质槽（原版对应）

明末原版的材质名前缀是 `M_HD_*`：

```
M_HD_QZ     裙子
M_HD_SB     手臂
M_HD_XZ     鞋子
M_HD_HW     护腕 / 花纹
M_HD_yumao  羽毛
```

注意别和「婉若游龙」搞混 —— 婉若游龙是 `M_WuCh_LTZ_*`（LTZ），这一套是 `M_HD_*`。

## 用途 / 状态

原本是给「婉若游龙换成网鞋」那版做过一次身体基础（后来改用 LTZ 本体，见
`未完成工程/婉若游龙-身体/`），同时也验证了"我们自己的重绑脚本 + `Hun_Skin_Skeleton.fbx`
原始骨架"这条链路是能产出合规资产的 —— 目前**唯一同时通过「1134 根」和「骨骼顺序=游戏原序」两项检查**的样本之一。

它本身没有单独的成品 mod，作为参考资产留档。
