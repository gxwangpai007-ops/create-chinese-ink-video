# Create Chinese Ink Video

把主题、文稿或参考画面转化为具有中国水墨语言的关键帧、分层 Layer Pack、动态样片和完整视频。

This Codex skill turns a brief, script, or visual reference into a controlled Chinese-ink video workflow—from style approval and layered scene formation to smooth previews and final QA.

![分层水墨动态样片](examples/worker-factory/demo.gif)

> 示例：现代拖车制造厂中的亚裔工人。画面采用表现主义都市水墨质感，并通过环境底板、人物、器械、墨迹与纸纹等层级逐步显影。

## 它解决什么问题

很多“水墨视频”只是让一张水墨图淡入或缩放，人物、建筑和车辆并没有真正形成。这套 Skill 把水墨风格拆成可执行的制作流程：

- 先确认风格方向，再进入正式制作
- 将内容参考与风格参考分开，避免把参考图中的对象错误迁移到新场景
- 用人物、物体、环境和抽象转场进行静态压力测试
- 从母版关键帧生成混合七层 Layer Pack，减少抠像白洞
- 让湿墨负责空间与气氛，干笔和线描负责主体结构
- 以水痕、积墨、笔触和轮廓锁定完成“形成”，而不是整图简单淡入
- 使用 48fps 中间渲染与 24fps 输出，降低低清预览的卡顿感
- 通过逐镜审计、局部重渲染和最终 QA 保持跨镜头一致性

## 默认工作流

1. **Gate 0 — 任务与参考预检**  
   明确主题、时长、画幅、文字政策、品牌与文件边界。
2. **Gate 1 — 风格方向审批**  
   在中国水墨体系内给出有真实差异的方向或墨量变体。
3. **Gate 2 — 静态风格压力测试**  
   同时验证人物、物体、环境与抽象画面的统一性。
4. **Gate 2.5 — 固化 Style Pack**  
   生成 Style Bible、提示词套件、负面约束与运动语法。
5. **Gate 3 — 低清动态样片**  
   用 3–5 秒样片验证晕染节奏、主体形成和镜头运动。
6. **Gate 4 — 完整分镜与资产计划**  
   拆分镜头职责、Layer Pack、版本和回退路径。
7. **Gate 5 — 渲染、审计与交付**  
   正常速度观看、逐帧指标辅助定位，并仅重渲染失败区间。

## 核心特色

### 强水墨 B2 基准

默认基准强调深墨、飞白、干湿笔触冲突、宣纸吸附和受控朱红点缀。它可以用于现代城市、车辆、工厂、建筑和人物，而不把画面退化为灰度照片滤镜。

### 混合七层 Layer Pack

```text
paper
environment wash
far structure
mid structure
hero subject
foreground structure
ink / atmosphere effects
```

连续环境底板先建立完整空间，精确母版像素再叠加到主体层。这样既能获得视差与形成层次，也能避免人物周围出现剪影状白洞。

### 可重复的本地工具

仓库内置 Python 脚本，用于：

- 构建 contact sheet 和转场检查条
- 校验 Style Bible 与镜头清单
- 从母版图生成混合 Layer Pack
- 抽取 QA 帧并分析相邻帧变化
- 编码平滑低清预览并探测视频参数

## 安装

把 Skill 目录复制到 Codex 的 skills 目录。

Windows PowerShell：

```powershell
Copy-Item -Recurse -Force `
  .\skill\create-chinese-ink-video `
  "$env:USERPROFILE\.codex\skills\create-chinese-ink-video"
```

macOS / Linux：

```bash
cp -R skill/create-chinese-ink-video \
  ~/.codex/skills/create-chinese-ink-video
```

重新打开 Codex 会话后，可以直接提出“中国水墨视频”“水墨晕染形成”“把画中元素拆层形成”等请求。

## 依赖

- Codex 或其他支持 `SKILL.md` 的代理环境
- Python 3.10+
- Pillow
- NumPy
- FFmpeg 与 ffprobe
- Node.js / npx
- HyperFrames（进行确定性动画、预览与渲染时）
- 可用的图像生成能力（生成风格板和关键帧时）

安装 Python 依赖：

```bash
python -m pip install -r requirements.txt
```

## 使用示例

```text
使用 create-chinese-ink-video，把下面的 20 秒口播拆成竖屏水墨视频。
不要字幕，先给我 3 个风格方向，确认后再生成关键帧。
```

```text
参考这张照片的构图，参考另一张图的深墨和飞白质感。
先做 B1 / B2 两档静态压力测试，不要迁移风格图里的具体对象。
```

```text
把已批准的工厂关键帧拆成 Layer Pack，做 5 秒低清动态样片。
要求人物、工具和厂房通过不同墨层形成，不要整张图一起淡入。
```

## 示例文件

- [批准的 B2 关键帧](examples/worker-factory/keyframe-b2.png)
- [5 秒低清 MP4 样片](examples/worker-factory/layered-ink-proof.mp4)

## 仓库结构

```text
.
├── README.md
├── requirements.txt
├── examples/
│   └── worker-factory/
└── skill/
    └── create-chinese-ink-video/
        ├── SKILL.md
        ├── agents/
        ├── assets/
        ├── references/
        └── scripts/
```

## 使用边界

- 生成的视频不构成法律、移民、就业或财务建议。
- 涉及品牌、人物、音乐和参考素材时，使用者应确认相应权利。
- 对证件、印章、Logo 和事实性声明，应在制作前明确真实素材、示意模板与禁止仿制的边界。
- 生成模型可能产生伪文字、伪标志或结构错误；正式交付前必须执行人工 QA。

## 项目状态

当前版本已经过竖屏现代工厂场景测试，覆盖强水墨静态迁移、混合七层拆分、均匀晕染形成和平滑低清预览。欢迎提交 Issue，分享新的题材压力测试、渲染器适配和失败案例。
