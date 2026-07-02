# Aesthetic OS · Final Reference v4

最终整合版：

- 大疆 / 金属 / 冷灰 / 干净风格
- 保留每日推荐
- 新增今日产品参考
- 保留 Dr.Coffee 今日案例
- 保留点击图片放大
- 保留历史案例
- 首页只展示最近两天
- 不生成 AI 产品图
- 不需要 OpenAI API
- 不需要充值
- 自动更新内容与产品参考卡片

## 上传

解压后，把所有内容上传到 GitHub 仓库根目录：

```text
index.html
data/
assets/
.github/
scripts/
FINAL_REFERENCE_V4_SETUP.md
```

## 自动更新

GitHub Actions 每天中国时间：

```text
07:30 晨间
18:30 晚间
```

## 产品参考说明

产品参考模块使用“内置精选参考库 + 来源链接”。
为了避免版权问题，页面使用本地生成的占位缩略图，按钮跳转原始来源页面。
