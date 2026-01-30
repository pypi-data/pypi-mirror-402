---
title: Translation Test Document
category: Testing
---

# Project Overview
Welcome to the **OpenTrans** test file. This document is designed to verify that the LLM maintains formatting while translating text.

## Features to Verify
* **Formatting**: This is *italic*, and this is **bold**.
* **Lists**:
    1.  First item with a [Link to Google](https://google.com)
    2.  Second item with a `code_span`
    3.  A nested item:
        * Deeply nested bullet.

> [!TIP]
> This is a callout box. It should be translated while keeping the `[!TIP]` syntax intact for Docusaurus/Obsidian.

### Code Block Test
The code below should **not** be translated:

```python
def hello_world():
    # This comment should stay in English (usually)
    print("Hello, World!")