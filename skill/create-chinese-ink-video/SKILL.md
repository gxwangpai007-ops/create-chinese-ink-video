---
name: create-chinese-ink-video
description: 将主题、文稿、参考图片或参考视频转化为中国水墨风格的关键帧、分层 Layer Pack、动态样片和完整视频，并通过方向审批、双参考职责分离、强水墨静态压力测试、晕染形成语法、连续流体墨场显影、纤维状缺口墨团生长、主体出场审计、平滑低清预览、局部重渲染和最终 QA 保持跨镜头一致性。用户要求“中国水墨视频”“国风水墨动画”“水墨晕染视频”“墨在水里散开”“喷气或墨流经过后画面显现”“C 形烟雾或随机墨团逐渐显影”“纤维状墨迹生长”“现代城市水墨”“参考这张图的质感重绘另一个场景”“把画中元素拆层形成”“让人物、汽车、建筑通过墨色渗化和笔触形成”，或需要修改、剪辑、排查卡顿、白洞及重复镜头时使用。
---

# Create Chinese Ink Video

把主题或参考资料转成可验证、可复用、可跨镜头执行的中国水墨视频系统。先锁定水墨方向，再验证静帧与动态，最后扩大到完整视频。让画面通过水痕、渗化、积墨、笔触和轮廓锁定逐步形成；不要用一条长提示词代替 Style Bible，也不要用静态美图代替动态验证。

## 核心原则

- 将中国水墨语言与具体内容、执行器分离。先定义工具无关的 Style Bible，再派生图片或视频模型提示词。
- 将创意自由集中在风格方向，将严格约束集中在阶段产物、验收条件、版本和回退路径。
- 把参考图中的纸张、墨色、笔触、留白、构图和形成方式写成可观察规则；不要只复述“高级、电影感、水墨感”等形容词。
- 区分不变量、可变轴和禁区。跨镜头固定不变量，只按叙事调节可变轴。
- 用代表性静态压力测试验证风格能否覆盖人物、物体、环境和抽象转场。
- 用 3–5 秒低清动态样片验证时间维度。静态 contact sheet 不得替代正常速度播放。
- 使用湿墨负责空间、气氛和形成，使用干笔或线描负责主体结构和稳定。
- 连续流体负责喷气、环境和大范围湿墨；纤维状墨团只负责主体局部显影前缘。两者必须共享到达时机，但不得互相替代。
- 双参考图时，让目标图锁定内容、身份、构图和结构，让风格图只提供纸张、墨色与笔触；明确禁止迁移风格图中的具体对象。
- 分层形成时，先放置连续的无主体环境底板，再叠加批准母版的精确前景像素；不得让人物或物体从剪影形白洞中填出。
- 每个镜头只设置一个主要水墨形成事件。避免摄影机、主体和墨迹同时强运动。
- 每个镜头必须具有独立叙事作用。英雄主体不得无理由重复出现。
- 把正常速度观看作为主要判断，把逐帧指标作为定位卡顿、闪烁和突变的辅助证据。
- 将用户审批绑定到具体 Gate、产物和版本；“确认”不得自动批准未展示的后续产物。
- 版本递增保存。不得覆盖已经展示给用户的方向板、样片或预览。

## 工作模式

根据用户目标选择最小充分模式：

- **Ink style only**：完成 Gate 0–2.5，交付水墨 Style Bible、风格板、提示词和执行建议。
- **Ink style proof**：完成 Gate 0–3，额外交付 3–5 秒水墨动态样片。
- **Full production**：完成 Gate 0–5，交付完整视频和 QA。

不要因为 Skill 支持完整生产而自动生成完整视频。先确认用户需要的模式。

## 配套能力

按阶段读取并遵守实际可用的相关 Skill：

- 分析本地参考图前，先实际查看图片；不要只根据文件名推断。
- Gate 2 生成风格板或关键帧时，使用 `imagegen` 或用户指定的图像生成能力。
- Gate 3–5 创建、动画或渲染视频时，先读取 `hyperframes`；再按实现需要读取 `hyperframes-core`、`hyperframes-animation`、`hyperframes-keyframes`、`hyperframes-cli`、`motion-graphics` 和 `media-use`。
- 用户明确要求 ChatCut、HeyGen 或某个生成式视频工具时，读取对应 Skill，并保留本工作流的审批和 QA。

## Gate 0：任务与参考预检

收集或合理推断：

- 主题、文稿、受众和叙事目标
- 交付模式、时长、画幅、平台和分辨率
- 参考图片、参考视频、品牌素材和必须保持的对象
- 用户明确喜欢、不喜欢或希望保留的特征
- 人物、产品、Logo、字幕、证件模板、事实声明和版权约束
- `text_policy`：`none`、`graphics_only`、`captions` 或 `designed_text`
- `brand_policy`：允许使用的品牌、使用位置、是否只能使用用户提供素材
- `document_policy`：真实文件、示意模板、禁止仿制的安全边界
- `revision_duration_policy`：删镜头后选择缩短、重分配时长或生成替代镜头
- 可用执行器、预算、速度和可控性偏好

把推断与用户明确要求分开记录。产出：

```text
brief.md
reference-analysis.md
approval-log.json
```

参考分析至少覆盖：宣纸或底材、墨色层次、干湿笔触、留白、主体处理、构图、空间、摄影、晕染潜力、可迁移特征、不可照搬内容和失败风险。

## Gate 1：风格方向审批

没有明确方向时，在中国水墨体系内提出 2–3 个差异真实的方向，例如文人留白、表现主义都市水墨、工笔建筑、雾化写实、书法构成或水墨加金。用户已选定参考方向时，不重复无效探索；改为提出克制、平衡、强化等墨量和写实度变体。

每个方向必须包含：

- 一句话视觉命题
- 3–5 个核心不变量
- 可变轴与建议默认值
- 色彩、材质、构图和主体处理
- 镜头、运动和转场语言
- 适用内容、主要风险和降级方案

产出 `style-directions.md`；需要图片时同时产出带编号的 `style-directions-contact-sheet.png`。等待用户选定方向后进入 Gate 2。

## Gate 2：静态风格压力测试

不要只生成一个容易成功的英雄画面。默认测试：

1. 人物近景
2. 产品、车辆或关键物体
3. 建筑、城市或环境大景
4. 抽象情绪或转场画面

对每张图保持相同不变量，同时有意改变主体、景别和画面密度。生成带编号的 contact sheet，执行静态 QA，保存提示词与生成参数。产出：

```text
style-board-vNN.png
style-board-qa-vNN.md
generation-prompts-vNN.md
```

需要统一联系表时运行：

```bash
python <skill-dir>/scripts/build_contact_sheet.py <images...> -o <project>/style-board-vNN.png
```

检查四张图是否像同一部片、主体是否可辨认、风格是否能脱离原参考内容成立，以及是否出现假字、假 Logo、水印、人物或结构畸变。等待用户确认风格板后进入 Gate 2.5。

## Gate 2.5：固化 Style Pack

完整读取 [style-bible-schema.md](references/style-bible-schema.md) 并生成 `style-bible.json`。使用：

```bash
python <skill-dir>/scripts/validate_style_bible.py <project>/style-bible.json
```

同时产出：

```text
prompt-kit.md
negative-constraints.md
motion-grammar.md
test-shot-blueprint.md
```

完整读取 [expressive-urban-ink.md](references/expressive-urban-ink.md)，以 B 版表现主义都市水墨作为默认基准，并按用户内容选择同一水墨家族中的克制、工笔、雾化、书法构成或水墨加金变体。构建提示词时读取 [prompt-construction.md](references/prompt-construction.md)；不要把所有规则重复写入主 Skill。

用户要求“参照另一张图的质感”“更浓、更像表现主义水墨”或“拆分画中元素形成”时，完整读取 [strong-ink-layered-workflow.md](references/strong-ink-layered-workflow.md)。先生成约 70% 的 B1 与约 85% 的 B2 两档；静帧批准后再制作 Layer Pack，不要把静帧批准扩大为动态批准。

## Gate 3：低清动态风格样片

完整读取 [motion-grammar.md](references/motion-grammar.md)、[renderer-routing.md](references/renderer-routing.md) 和 [qa-and-fallbacks.md](references/qa-and-fallbacks.md)。

用户要求墨水在水中连续扩散、喷气带动画面显影、自然卷曲回流，或反馈烟雾像圆团、软管、速度忽快忽慢时，完整读取 [fluid-ink-formation.md](references/fluid-ink-formation.md)。优先让同一流体密度场同时生成可见墨层和累积显影母版；不得用彼此独立的烟雾动画与透明度遮罩伪造因果关系。

用户要求人物、车辆或产品通过纤维边缘、C 形／缺口墨团、多个随机墨云逐步显影时，完整读取 [fibrous-ink-bloom.md](references/fibrous-ink-bloom.md)。保留已经批准的环境流体或喷气，让墨团仅承担主体局部形成；使用多个错时、异向、异尺寸墨团并在后段干笔锁形，不得生成规则字母 C、同心圆或永久白洞。

先制作 3–5 秒 Style Proof，不要直接生产长片。样片至少包含：

- 一个代表主体
- 一个明确摄影机行为
- 一个主体动作或状态变化
- 一个主要水墨形成或转场事件
- 一个由当前状态自然保持的完成态

只设计一个主要水墨事件。摄影机、主体和墨迹不得同时做强运动。先渲染低清 MP4，实际播放并执行动态 QA；再生成 proof-frame contact sheet。产出：

```text
preview/style-proof-low-vNN.mp4
preview/style-proof-contact-sheet-vNN.jpg
gate3-motion-qa-vNN.md
```

按动作关键点抽帧，再用联系表脚本排版：

```bash
python <skill-dir>/scripts/extract_proof_frames.py <video> --times <seconds> -o <frames-dir>
```

运行逐帧变化扫描，定位异常峰值；不要把统一阈值当成审美结论：

```bash
python <skill-dir>/scripts/analyze_frame_delta.py <video> -o <report.json>
```

默认以 48 fps 捕获完整确定性帧序列，再用两帧时域混合输出 24 fps 低清样片：

```bash
python <skill-dir>/scripts/encode_smooth_preview.py \
  <frames-48-dir> -o <preview/style-proof-low-vNN.mp4>
```

显影墨点随机分布后，按空间顺序排序并把到达时间均匀重分配，避免局部墨点扎堆造成突然成片出现。结束阶段连续渗透收口，不得在最后一帧硬补齐整层。

向用户说明这是动态风格审批稿。用户确认后才扩大到完整视频。

## Gate 4：分镜与镜头生产

根据文稿生成 `storyboard.md` 与 `shot-manifest.json`。每镜记录：

- 叙事功能、时间范围和声音锚点
- 主体、景别、构图和摄影机行为
- 水墨不变量与本镜墨量、写实度、密度、气氛和点色取值
- 形成方式、主体动作、转场承接
- 关键帧提示词、负面约束和生成器适配
- 可控路线、生成式路线和降级路线
- `primary_entity`、`narrative_role`、`appearance_index`
- `repeat_allowed` 与非空 `repeat_reason`

只拆分具有独立运动、遮挡、形成或跨镜头延续价值的层。不要强制所有镜头使用相同图层数量。分批生成关键帧并制作全片 contact sheet；先解决风格漂移，再制作昂贵视频。

人物与工具交互镜头优先使用：宣纸、淡墨空环境、批准背景结构、主要物体、人物身体、手与工具、点色。已有遮罩时运行：

```bash
python <skill-dir>/scripts/build_hybrid_layer_pack.py \
  --master <approved-master.png> \
  --paper <paper.png> \
  --clean-plate <empty-environment.png> \
  --subject-mask <subject-mask.png> \
  --object-mask <object-mask.png> \
  --detail-mask <hands-tool-mask.png> \
  --output-dir <project>/assets/layers-vNN
```

大面积人物遮挡不要默认使用自动修复补洞；优先生成或复用构图兼容的无人物环境底板，并向宣纸混合为淡墨层。

运行主体与叙事重复审计：

```bash
python <skill-dir>/scripts/audit_shot_manifest.py <project>/shot-manifest.json
```

## Gate 4.5：组装前剪辑审计

完整读取 [assembly-and-revision.md](references/assembly-and-revision.md)。在完整动画前：

- 生成每镜一帧的 shot contact sheet，不得只抽漂亮画面
- 检查同一主体、叙事功能、景别和构图是否无理由重复
- 检查每个转场是否有视觉承接物、宣纸留白或墨迹种子
- 检查无文字模式下，画面是否仍能传递必要信息
- 为每个可删除镜头记录删镜后的时长策略

产出 `assembly-audit-vNN.md`。存在未解释的英雄主体重复时，不得进入 Gate 5。

## Gate 5：完整预览、最终渲染与 QA

先交付低清整片预览，确认节奏、叙事和风格连续性。任何镜头、资产或动画修改后，重新生成受影响的预览和 QA，不得沿用旧审批。

同时生成两种检查物：

- 每镜一帧 contact sheet：检查风格、主体和叙事重复
- 每个转场的连续帧条：检查白闪、硬切、顿挫和承接

```bash
python <skill-dir>/scripts/build_transition_strips.py <video> \
  --transitions <seconds> -o <transition-sheet.jpg>
```

只有低清整片获批后才执行高质量渲染。最终检查：

- 编码、分辨率、帧率、时长、音轨和画幅
- 跨镜头色彩、材质、主体和风格事件的一致性
- 人物、产品、建筑和 Logo 的结构连续
- 无假字、水印、闪烁、重影、重复对象或突变
- 转场属于既定运动语法
- `text_policy`、`brand_policy` 与 `document_policy` 均已满足
- 最终文件与批准预览一致

使用 `python <skill-dir>/scripts/probe_video.py <video>` 核对机器可读的视频参数。

HyperFrames 原生渲染失败或只修改局部时间段时，按
[assembly-and-revision.md](references/assembly-and-revision.md) 使用分批快照回退；先运行
`snapshot_frame_ranges.py --dry-run` 核对范围，再执行并只替换受影响帧。

交付最终 MP4、抽帧 contact sheet、`final-qa.md` 和实际使用的 Style Bible。

## 一票否决

以下任一情况不得称为完成：

- 只给一条长提示词，没有结构化水墨系统
- 只在同一类主体上测试风格，却宣称适用于完整视频
- 用普通透明度、平滑圆形遮罩或整图缩放冒充水痕、晕染、积墨和笔触形成
- 前景显影前出现人物形、物体形或规则多边形白洞
- 大面积自动补洞产生放射状拉伸、糊块或人工填充痕迹
- 只看静态图，没有播放低清动态样片
- 技术参数通过，但正常速度下看不出宣纸、墨色渗化与笔触锁形
- 用户已批准的关键不变量在后续镜头中漂移
- 英雄主体或叙事功能无理由重复
- 无文字模式仍出现新增标题、字幕、说明文字或假文字
- 转场存在未解释的白闪、硬切、明显停顿或峰值突变
- 生成器失败后无限重试，没有使用预设降级路线
- 高质量渲染与批准预览不一致

## 项目产物

按所选工作模式保留适用产物：

```text
brief.md
reference-analysis.md
approval-log.json
style-directions.md
style-board-vNN.png
style-board-qa-vNN.md
style-bible.json
prompt-kit.md
negative-constraints.md
motion-grammar.md
test-shot-blueprint.md
layer-pack.json
preview/
storyboard.md
shot-manifest.json
assembly-audit-vNN.md
renders/
final-qa.md
```
