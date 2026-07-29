# 多区域水墨联合显影

当一个画面包含多个品牌、人物、产品、建筑或叙事区域，并需要它们被同一条墨脉连接、依次形成时，使用本路线。不要让每个区域各自播放独立淡入。

## 职责结构

```text
批准母版
+ 无主体环境底板
+ 宣纸底图
+ JSON 区域配置
→ 共享环境到达场
→ 多区域纤维墨团
→ 环境与主体联合形成
→ 精确母版像素锁形
```

共享墨脉负责画面的空间连续性；区域墨团负责局部形成节奏；后段锁形负责 Logo、面部、产品边缘等不可变结构。

## 适用条件

- 同一画面包含两个以上需要分时形成的区域。
- 需要用河流、山脉、烟气、墨迹或光路连接多个主体。
- Logo、人物或产品不能在形成过程中变形。
- 画面需要保留中央或指定区域的宣纸留白。
- 需要把一次成功的专用测试转成配置化、可重复渲染。

单主体局部形成继续使用 `render_fibrous_ink_bloom.py`。真实喷气或水中连续流体继续使用 `render_fluid_ink_matte.py`。多区域编排不要冒充完整二维流体模拟。

## 输入职责

- `master`：已经批准的完整终态，锁定最终构图和主体结构。
- `clean`：构图兼容、没有精确主体的环境底板。
- `paper`：宣纸底图，不包含主体或环境结构。
- `config`：环境路径、区域、墨团、锁形和留白参数。

`master`、`clean` 与 `paper` 必须同构图。不得用不兼容的环境图填补人物或产品背后区域。

## 配置

从模板开始：

```text
<skill-dir>/assets/multi-region-ink-template.json
```

关键字段：

- `environment_paths[].points`：`[x, y, time]` 归一化路径点。
- `environment_paths[].spread`：墨脉对周围环境的横纵到达范围。
- `regions[].zone`：局部形成区域的椭圆范围。
- `regions[].blooms`：错时、异向、异尺寸纤维墨团。
- `regions[].lock`：精确母版差异或外部遮罩的后段锁形。
- `negative_space`：需要抑制环境形成的椭圆或遮罩区域。
- `settle`：结尾只减弱浮墨前缘，不移除已形成内容。

同一主体跨越多个区域时，使用一个较大的区域和多个墨团；不要把它切成互相争抢像素的小区域。

## 运行

先校验配置：

```bash
python <skill-dir>/scripts/render_multi_region_ink.py \
  --master <project>/approved-master.png \
  --clean <project>/clean-plate.png \
  --paper <project>/paper-plate.png \
  --config <project>/multi-region-ink.json \
  --validate-only
```

再渲染：

```bash
python <skill-dir>/scripts/render_multi_region_ink.py \
  --master <project>/approved-master.png \
  --clean <project>/clean-plate.png \
  --paper <project>/paper-plate.png \
  --config <project>/multi-region-ink.json \
  --output <project>/preview/multi-region-proof.mp4
```

脚本使用 48 fps 内部帧和两帧时域混合输出 24 fps，并生成同名渲染清单。测试时可用 `--width`、`--height` 和 `--duration` 覆盖配置。

## 编排规则

1. 先让共享墨脉进入第一个叙事区域。
2. 环境结构随墨脉到达逐步出现，不要等待 Logo 或人物开始后才整块跳出。
3. 每个区域使用 3–7 个纤维墨团，错开 0.25–0.60 秒。
4. 下一区域在上一区域进入稳定形成后启动，避免全画面同时沸腾。
5. 锁形只覆盖母版与环境底板之间的必要差异；不要重新淡入整张母版。
6. 最后 15–20% 减弱湿墨前缘并保持终态。

如果中央留白被吃掉，提高 `negative_space[].strength` 或扩大其半径。如果区域像独立贴纸，增加通往该区域的环境分支，并让其起始时间略早于局部墨团。

## QA

- 正常速度下能否看出一条连续因果链，而非多个独立淡入。
- 每个主体是否与周围环境共同形成。
- 多区域启动是否有先后层次，没有同时抢夺注意力。
- Logo、面部和产品轮廓是否在后段准确锁定。
- 指定留白是否从头到尾保持呼吸空间。
- 是否出现矩形显影、规则圆章、永久白洞或结尾硬补齐。
- 逐帧变化扫描是否存在整块区域突然出现的异常峰值。
