# pptsmith

从 Markdown 生成 PowerPoint 演示文稿的工具。

## 安装

```bash
pip install -e .
# or
uv tool install -e .
```

## 使用方法

```bash
pptsmith <markdown_file> [OPTIONS]
```

### 参数

- `MARKDOWN_FILE`: Markdown 文件路径（必需）

### 选项

| 选项 | 说明 |
|------|------|
| `-t, --template PATH` | PowerPoint 模板文件（默认: template.pptx） |
| `-o, --output PATH` | 输出文件路径（默认: 与输入文件同名的 .pptx） |
| `-v, --verbose` | 打印每页渲染的内容 |

### 示例

```bash
uv sync
# 指定模板 并显示详细渲染信息
uv run pptsmith example/main.md -t template.pptx -v
```

## Markdown 格式

使用 `---` 分隔页面，每页支持：

- `# 标题` - 一级标题作为幻灯片标题
- 正文内容 - 自动填充到文本框
- `![alt](image.png)` - 图片（相对于 Markdown 文件路径）

### 示例

```markdown
# 第一页标题

这是第一页的正文内容。
支持多行文本。

![](image1.png)

---

# 第二页标题

第二页的内容。
```

## 模板要求

模板 PPT 的第一页作为所有页面的模板，需包含以下元素：

| 元素类型 | 命名规则 |
|---------|---------|
| 标题 | placeholder idx=0 |
| 文本框 | 名称包含「文本框」「Content」或「Text」 |
| 图片 | 名称包含「图片」「Picture」或「Image」 |

填充时会保留文本框的原有样式（字体、大小、颜色等）。

## 依赖

- python-pptx >= 0.6.21
- click >= 8.0.0
