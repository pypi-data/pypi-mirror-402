# pywgb

[![PyPI version](https://img.shields.io/pypi/v/pywgb)](https://pypi.org/project/pywgb/)
[![Python versions](https://img.shields.io/pypi/pyversions/pywgb)](https://pypi.org/project/pywgb/)
[![codecov](https://codecov.io/gh/ChowRex/pywgb/graph/badge.svg?token=1SDIUB46RU)](https://codecov.io/gh/ChowRex/pywgb)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Wecom (WeChat Work) Group Bot Python API - A comprehensive and easy-to-use library for sending messages to Wecom group bots.

## ✨ Features

- 🤖 **Smart Bot** - Automatic message type detection
- 📝 **Multiple Message Types** - Text, Markdown (v1 & v2), Images, Files, Voice, News, Template Cards
- 🎨 **Rich Formatting** - Colored text, tables, lists, code blocks
- 🔒 **Rate Limiting** - Built-in overheat detection (20 msg/min)
- ✅ **Type Hints** - Full type annotation support
- 🧪 **Well Tested** - 100% test coverage
- 📚 **Comprehensive Docs** - Detailed documentation and examples

## 📦 Installation

```bash
# Basic installation (text, markdown, images, news, cards)
pip install pywgb

# Full installation (includes voice message support with pydub)
pip install "pywgb[all]"
```

**Requirements**: Python 3.8+

## 🚀 Quick Start

### 1. Get Your Webhook Key

1. Create a [Wecom Group Bot](https://qinglian.tencent.com/help/docs/2YhR-6/)
2. Copy the webhook URL or just the key (UUID format):
   - Full URL: `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR-UUID-KEY`
   - Or just: `YOUR-UUID-KEY`

### 2. Send Your First Message

```python
from pywgb import SmartBot

# Initialize bot with your key
bot = SmartBot("YOUR-UUID-KEY")

# Send a simple text message
bot.send("Hello, World!")
```

That's it! 🎉

## 📖 Usage Guide

### Text Messages

```python
from pywgb import SmartBot

bot = SmartBot("YOUR-KEY")

# Simple text
bot.send("This is a text message")

# Text with @mentions
bot.send(
    "Important announcement!",
    mentioned_list=["userid1", "@all"],  # @all mentions everyone
    mentioned_mobile_list=["13800138000"]
)
```

### Markdown Messages

#### Markdown v1 (with colored text)

```python
# Colored text (unique feature!)
status = bot.markdown_feature.green("Online")
warning = bot.markdown_feature.orange("High Load")
info = bot.markdown_feature.gray("Last updated: 2026-01-16")

markdown = f"""
# Server Status Report

**Status**: {status}  
**Warning**: {warning}  
**Info**: {info}

> For more details, visit [Dashboard](https://example.com)

Inline `code` example
"""

bot.send(markdown)
```

**Supported syntax**: Titles (H1-H6), **Bold**, [Links](url), `inline code`, > quotes, colored text

#### Markdown v2 (with tables and more)

```python
# Create a table
data = [
    ["Name", "Status", "Score"],
    ["Alice", "Active", "95"],
    ["Bob", "Inactive", "87"],
    ["Charlie", "Active", "92"]
]

markdown_v2 = f"""
# Team Performance

{bot.markdown_feature.list2table(data)}

## Notes
- *Important*: Review pending
- **Deadline**: 2026-01-20

> Main objective
>> Sub-objective

---

```python
def hello():
    print("Hello!")
```


bot.send(markdown_v2)
```

**Additional syntax**: *Italics*, multi-level lists, tables, images, code blocks, horizontal rules

> **Note**: Markdown v2 does NOT support colored text. Choose v1 for colors, v2 for tables.

### Images

```python
# Supported formats: PNG, JPG (max 2MB)
bot.send(file_path="screenshot.png")
```

### Voice Messages

```python
# Requires full installation: pip install "pywgb[all]"
# Format: AMR only (max 2MB, max 60 seconds)
bot.send(file_path="audio.amr")
```

### Files

```python
# Any file format (5B < size < 20MB)
bot.send(file_path="document.pdf")
```

### News Articles

```python
articles = [
    {
        "title": "Breaking News",
        "description": "Important update",
        "url": "https://example.com/article",
        "picurl": "https://example.com/image.jpg"
    },
    # ... up to 8 articles
]

bot.send(articles=articles)
```

### Template Cards

#### Text Card

```python
bot.send(
    main_title={"title": "Deployment Notification", "desc": "Production environment"},
    emphasis_content={"title": "SUCCESS", "desc": "Status"},
    sub_title_text="Deployed by: DevOps Team",
    horizontal_content_list=[
        {"keyname": "Version", "value": "v2.1.0"},
        {"keyname": "Time", "value": "2026-01-16 15:00"}
    ],
    card_action={"type": 1, "url": "https://example.com/details"}
)
```

#### News Card

```python
bot.send(
    main_title={"title": "System Alert", "desc": "Monitoring report"},
    card_image={"url": "https://example.com/chart.png", "aspect_ratio": 2.25},
    image_text_area={
        "type": 1,
        "url": "https://example.com",
        "title": "CPU Usage Alert",
        "desc": "Current usage: 85%",
        "image_url": "https://example.com/icon.png"
    },
    card_action={"type": 1, "url": "https://example.com/dashboard"}
)
```

## 🔧 Advanced Usage

### Upload Temporary Media

```python
# Upload file and get media_id (valid for 3 days)
media_id = bot.upload("document.pdf")
print(f"Media ID: {media_id}")
```

### Use Specific Bot Types

```python
from pywgb.bot import TextBot, MarkdownBot, ImageBot, FileBot

# Use specific bot for better control
text_bot = TextBot("YOUR-KEY")
text_bot.send("Specific text message")

# Send image as file (instead of image message)
file_bot = FileBot("YOUR-KEY")
file_bot.send(file_path="image.png")  # Sent as file, not image
```

## ⚠️ Limitations

| Type | Limit |
|------|-------|
| **Rate Limit** | 20 messages/minute per bot |
| **Text** | Max 2048 bytes (UTF-8) |
| **Markdown** | Max 4096 bytes (UTF-8) |
| **Image** | PNG/JPG, max 2MB |
| **Voice** | AMR only, max 2MB, max 60s |
| **File** | 5B - 20MB |
| **News** | Max 8 articles per message |

> **Rate Limiting**: The library automatically handles rate limits with cooldown detection. When limit is exceeded, it waits and retries automatically.

## 📚 Documentation

- **GitHub**: [ChowRex/pywgb](https://github.com/ChowRex/pywgb)
- **PyPI**: [pywgb](https://pypi.org/project/pywgb/)
- **Official Wecom Docs** (Chinese): [群机器人配置说明](https://developer.work.weixin.qq.com/document/path/99110)
- **API Reference**: See `docs/` directory or build with Sphinx

### Build Documentation

```bash
pip install "pywgb[docs]"
cd docs && make html
open _build/html/index.html
```

## 🧪 Development

### Run Tests

```bash
# Install dev dependencies
pip install -e ".[test]"

# Run tests with coverage
pytest --cov=src/pywgb --cov-report=html -v

# View coverage report
open htmlcov/index.html
```

### Code Quality

- **Test Coverage**: 100%
- **Type Hints**: Full support
- **Code Style**: PEP 8 compliant
- **Documentation**: Sphinx with Google-style docstrings

## 🗺️ Roadmap

- [x] v0.0.1-0.0.5: Initial release with basic message types
- [x] v0.0.6-0.0.9: Add template cards and refactoring
- [x] v0.1.0-0.1.2: Add SmartBot with auto-detection
- [x] v1.0.0-1.0.4: Stable release with full features
- [ ] v1.1.0: Performance optimizations (in progress)
- [ ] v1.2.0: Enhanced documentation and examples
- [ ] v2.0.0: Async support and additional features

See [NEXT_STEPS.md](NEXT_STEPS.md) for detailed improvement plans.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Rex Zhou**
- Email: 879582094@qq.com
- GitHub: [@ChowRex](https://github.com/ChowRex)

## 🙏 Acknowledgments

- Thanks to Tencent for providing the Wecom Group Bot API
- Inspired by the need for a simple, Pythonic interface to Wecom bots

---

**Star ⭐ this repo if you find it helpful!**



