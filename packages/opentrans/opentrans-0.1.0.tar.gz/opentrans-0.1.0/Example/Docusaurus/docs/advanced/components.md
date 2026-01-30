# Component Gallery

Here is how you define a code block that should remain exactly as is:

```python
def hello_world():
  print("This code should not be translated into Chinese!")
```

:::tip[Pro Tip]
You can use nested structures here. Check the config.yaml for more details. 
:::

Check the [Advanced Setup](./setup.mdx) for more details.

### How to use these for testing:

1. Save these files into the folders indicated.
2. Run your tool:

```bash
OpenTrans ./Example/Docusaurus/docs ./Example/Docusaurus/i18n/zh-Hans/docusaurus-plugin-content-docs/current
```

3.Verify that:

* The Frontmatter (between ---) is unchanged.
* The Code Blocks contain the original Python code.
* The JSX Tags (<MyComponent>) are still valid.
* The LaTeX Math is still in the output.