# sphinx_tabs_selector

This plugin is created based on the `sphinx_tabs` plugin and supports all formats supported by `sphinx_tabs` v3.4.7.

## Features

1. Supports all formats supported by `sphinx_tabs` with v3.4.7.
2. Supports showing tabs in switching mode or flat mode.
3. Supports Unix glob pattern for `tabs_include` and `tabs_exclude` configuration. You can use Unix glob pattern to
   select multiple tabs. For example:
    - `tabs_include = ["tab1_*", "tab2_*", "tab3_*"]` will select all tabs that start with `tab1_`, `tab2_`, `tab3_`.
    - `tabs_exclude = ["tab4_*", "tab5_*", "tab6_*"]` to exclude all tabs that start with `tab4_`, `tab5_`, `tab6_`.
4. When `tabs_flat` is set to `True`, and builder is `latex`, the tabs will be displayed in flat mode, and pdf will show
   the tab with blue,bold tab name and the tab contents will be surrounded by a box. The non-nested tabs are displayed
   very well. But the nested tabs are displayed not very well.
5. Supports replace `strings` in tab contents by set `tabs_replace_dict`. This only effect on flat mode.


## Installation

```bash
pip install sphinx-tabs-selector
```

## Usage

Add the following configuration to `conf.py`:

```python
extensions = [
    ...
    'sphinx_tabs_selector.selector',
    ...
]

# tabs_include is used to configure the tabs to be selected. Support Unix glob pattern.
# The configuration item is a list. Each element in the list is a string, which is the name of the tab to be selected. 
# If the tab is nested, you need to write down all the names of the tabs in the nesting path.
tabs_include = ["tab1_name", "tab2_name", "tab3_*"]

# tabs_exclude is used to configure the tabs to be skipped. Support Unix glob pattern.
# The configuration item is a list. Each element in the list is a string, which is the name of the tab to be skipped.
tabs_exclude = ["tab4_name", "tab5_name", "tab6_*"]

# default is False. If True, the tabs will be displayed in flat mode. Otherwise, the tabs will be displayed in switching mode.
tabs_flat = True

tabs_replace_dict = {
    "tab1":{
        "key1":"value1"
    }
}
```

For the way of writing tabs in RST files, you can refer to the documentation of
the [sphinx_tabs](https://sphinx-tabs.readthedocs.io/en/latest/) plugin. Thanks for the author of the sphinx_tabs
plugin.

## Notes

1. If you want to use this plugin. You must add the `tabs_include` or `tabs_exclude` configuration to `conf.py`;
   Otherwise, the plugin will not take effect. Therefore, you can use the `tabs_include` or `tabs_exclude`configuration
   to control the activation of the plugin.
    - If any of the `tabs_include` or `tabs_exclude` configuration is added, the plugin will be activated.
    - If either of the `tabs_include` or `tabs_exclude` configuration is not added, the plugin will not be activated.
    - If only `tabs_include` is added, the plugin will only select the tabs in the `tabs_include` configuration.
    - If only `tabs_exclude` is added, the plugin will select all tabs except the tabs in the `tabs_exclude`
      configuration.
    - If both `tabs_include` and `tabs_exclude` are added, the plugin will select the tabs in the `tabs_include`
      configuration, and exclude the tabs in the `tabs_exclude` configuration. **But excluding takes precedence over
      selecting**.
2. You need add the `tabs_flat` configuration to `conf.py` to control the display mode of the tabs.
    - If the `tabs_flat` configuration is not added, the tabs will be displayed in switching mode.
    - If the `tabs_flat` configuration is added and set to `True`, the tabs will be displayed in flat mode.
    - If the `tabs_flat` configuration is added and set to `False`, the tabs will be displayed in switching mode.
3. If both the `sphinx_tabs` plugin and the `sphinx_tabs_selector` plugin are added to the `extensions` in `conf.py`,
   for the `sphinx_tabs_selector` plugin to work, it must be added after `sphinx_tabs`.
4. The `sphinx_tabs_selector` plugin can be used independently even if the `sphinx_tabs` plugin is not added to
   `conf.py`.
6. If only set the `sphinx_tabs_selector` plugin in `conf.py` and not set the `sphinx_tabs` plugin, and `tabs_flat` is
   set to `False` or not set, and not set the `tabs_include` or `tabs_exclude` configuration, the plugin will work as
   the `sphinx_tabs` plugin with v3.4.7.
7. If one `tabs` has no content, it will not be displayed. (updated in v1.0.12)
