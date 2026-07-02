# Aesthetic OS 自动更新包

这个包用于让你的 GitHub Pages 网站每天自动更新。

## 文件包含

```text
.github/workflows/daily-update.yml
scripts/generate_daily.py
requirements.txt
```

## 上传位置

把这三个内容上传到仓库根目录：

```text
Fengzi01/aesthetic-daily/
```

上传后仓库应该变成：

```text
aesthetic-daily
├── index.html
├── data
│   └── content.json
├── assets
├── scripts
│   └── generate_daily.py
├── requirements.txt
└── .github
    └── workflows
        └── daily-update.yml
```

## 必须设置 OPENAI_API_KEY

进入 GitHub 仓库：

```text
Settings
→ Secrets and variables
→ Actions
→ New repository secret
```

新增：

```text
Name: OPENAI_API_KEY
Value: 你的 OpenAI API Key
```

## 可选设置模型

进入：

```text
Settings
→ Secrets and variables
→ Actions
→ Variables
```

可选新增：

```text
OPENAI_TEXT_MODEL = gpt-4.1-mini
OPENAI_IMAGE_MODEL = gpt-image-2
```

## 自动更新时间

默认按中国时间：

```text
07:30  自动更新晨间
18:30  自动更新晚间
```

## 手动测试

进入 GitHub 仓库：

```text
Actions
→ Daily Aesthetic OS Update
→ Run workflow
```

选择：

```text
am / pm / auto
```

然后运行。

## 重要说明

1. 如果没有配置 OPENAI_API_KEY，脚本仍会更新网站，但只生成 SVG 占位图，不会生成真实 AI 产品图。
2. 如果 OpenAI 图像生成失败，脚本不会中断，会自动用 SVG 占位图替代。
3. 生成图可能出现机器细节不稳定。更稳定的商业方案是后续上传真实 F15 透明底 PNG，让程序合成到 AI 场景里。
