#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit test

- Author: Rex Zhou <879582094@qq.com>
- Created Time: 2025/6/3 14:42
- Copyright: Copyright © 2025 Rex Zhou. All rights reserved.
"""
from logging import basicConfig, DEBUG
from os import getenv
from pathlib import Path

from dotenv import load_dotenv

# pylint: disable=import-error
from src.pywgb import SmartBot

basicConfig(level=DEBUG, format="%(levelname)s %(name)s %(lineno)d %(message)s")
env_file = Path(__file__).parent.with_name(".env")
errors_file = Path(__file__).with_name("card_errors.yml")
load_dotenv(env_file, override=True)
VALID_KEY = getenv("VALID_KEY")
bot = SmartBot(VALID_KEY)
_COL = [
    bot.markdown_feature.green,
    bot.markdown_feature.gray,
    bot.markdown_feature.orange,
]
_COL = "".join(_COL[idx % 3](ltr) for idx, ltr in enumerate("colorful"))
TEST_VALID_MARKDOWN = f"""
# TESTING

> Author: **Rex**

This is a {_COL} Markdown message
"""
_TABLE = [
    ["Name", "Gender", "Title"],
    ["Julia", "Female", "Accounting"],
    ["Jess", "Female", "Reception"],
    ["Tom", "Male", "Manager"],
    ["Grance", "Male", "Testing"],
    ["Rex", "Male", "DevOps"],
]
TEST_VALID_MARKDOWN_V2 = f"""
# TESTING v2

*Italics*

> Author: **Rex**
>> Version: v2
>>> Peace and love

---

- Unordered List 1
- Unordered List 2
  - Unordered List 2.1
  - Unordered List 2.2
1. Ordered List 1
2. Ordered List 2

![Picture](https://res.mail.qq.com/node/ww/wwopenmng/images/independent/doc/test_pic_msg1.png)

```
There is a test code block.
```

Here is a empty string when the table is less than 2 rows.

{bot.markdown_feature.list2table(_TABLE[:1])}

Here is a test table.

{bot.markdown_feature.list2table(_TABLE)}

"""

TEST_VALID_ARTICLES = [
    {
        "title": "中秋节礼品领取",
        "description": "今年中秋节公司有豪礼相送",
        "url": "www.qq.com",
        # pylint: disable=line-too-long
        "picurl": "http://res.mail.qq.com/node/ww/wwopenmng/images/independent/doc/test_pic_msg1.png",
    }
]
TEST_VALID_TEXT_CARD = {
    "main_title": {"title": "欢迎使用企业微信", "desc": "您的好友正在邀请您加入企业微信"},
    "emphasis_content": {"title": "100", "desc": "数据含义"},
    "quote_area": {
        "type": 1,
        "url": "https://work.weixin.qq.com/?from=openApi",
        "title": "引用文本标题",
        "quote_text": "Jack：企业微信真的很好用~\nBalian：超级好的一款软件！",
    },
    "sub_title_text": "下载企业微信还能抢红包！",
    "horizontal_content_list": [
        {"keyname": "邀请人", "value": "张三"},
        {
            "keyname": "企微官网",
            "value": "点击访问",
            "type": 1,
            "url": "https://work.weixin.qq.com/?from=openApi",
        },
    ],
    "jump_list": [
        {
            "type": 1,
            "url": "https://work.weixin.qq.com/?from=openApi",
            "title": "企业微信官网",
        }
    ],
    "card_action": {
        "type": 1,
        "url": "https://work.weixin.qq.com/?from=openApi",
    },
}
TEST_VALID_NEWS_CARD = {
    "source": {
        "icon_url": "https://wework.qpic.cn/wwpic/252813_jOfDHtcISzuodLa_1629280209/0",
        "desc": "企业微信",
        "desc_color": 0,
    },
    "main_title": {"title": "欢迎使用企业微信", "desc": "您的好友正在邀请您加入企业微信"},
    "card_image": {
        "url": "https://wework.qpic.cn/wwpic/354393_4zpkKXd7SrGMvfg_1629280616/0",
        "aspect_ratio": 2.25,
    },
    "image_text_area": {
        "type": 1,
        "url": "https://work.weixin.qq.com",
        "title": "欢迎使用企业微信",
        "desc": "您的好友正在邀请您加入企业微信",
        "image_url": "https://wework.qpic.cn/wwpic/354393_4zpkKXd7SrGMvfg_1629280616/0",
    },
    "quote_area": {
        "type": 1,
        "url": "https://work.weixin.qq.com/?from=openApi",
        "appid": "APPID",
        "pagepath": "PAGEPATH",
        "title": "引用文本标题",
        "quote_text": "Jack：企业微信真的很好用~\nBalian：超级好的一款软件！",
    },
    "vertical_content_list": [{"title": "惊喜红包等你来拿", "desc": "下载企业微信还能抢红包！"}],
    "horizontal_content_list": [
        {"keyname": "邀请人", "value": "张三"},
        {
            "keyname": "企微官网",
            "value": "点击访问",
            "type": 1,
            "url": "https://work.weixin.qq.com/?from=openApi",
        },
    ],
    "jump_list": [
        {
            "type": 1,
            "url": "https://work.weixin.qq.com/?from=openApi",
            "title": "企业微信官网",
        }
    ],
    "card_action": {"type": 1, "url": "https://work.weixin.qq.com/?from=openApi"},
}


# pylint: disable=protected-access
def main():  # pragma: no cover
    """
    For unit testing
    :return:
    """
    result = bot.send(TEST_VALID_MARKDOWN)
    print(result)


if __name__ == "__main__":  # pragma: no cover
    main()
