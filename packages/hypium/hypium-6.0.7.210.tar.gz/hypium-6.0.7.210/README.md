## 简介

Hypium是HarmonyOS平台的UI自动化测试框架，支持用户使用Python语言为应用编写UI自动化测试脚本，主要包含以下特性：

1. Hypium提供了控件、图像和比例坐标等**多种控件定位方式**，支持多窗口操作以及触摸屏/鼠标/键盘等**多种模拟输入功能**， 支持*
   *多设备**并行操作， 能够覆盖各类场景和多种形态设备上的自动化用例编写需求，可支持鸿蒙手机、平板、PC等设备。
2. Hypium能够为执行的用例生成详细的**用例执行报告**，并且自动记录设备日志以及执行步骤截图，为用户提供高效和专业的测试用例执行和结果分析体验。

> 可在华为开发者联盟官网下载[DevEco Testing Hypium完整安装包](https://developer.huawei.com/consumer/cn/download/deveco-testing-hypium)
，安装使用其中的**hypium-pycharm-plugin**，支持工程快速创建、用例一键执行、控件查看和投屏操作等多种用例开发辅助功能，提升用例开发体验和效率。

## 快速开始

### 环境准备

请参考[hdc环境准备](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/hdc#%E7%8E%AF%E5%A2%83%E5%87%86%E5%A4%87)
文档配置hdc命令执行环境。

### 安装Hypium

```bash
pip install hypium
```

### 连接设备

通过USB或Wifi无线调试连接设备。连接完成后，执行 `hdc list targets` 命令，控制台中打印已连接设备的序列号表示设备连接成功。

### 编写脚本

Hypium有两种使用模式： Driver模式和测试工程模式。
Driver模式仅提供自动化驱动接口，可以作为SDK集成到其他测试框架或者工具中，驱动设备执行自动化操作。
测试工程模式提供了在支持调用自动化驱动接口的基础上，提供了设备管理、用例开发、调度执行、报告生成等测试工程相关的功能。

**注意：** 两种方式不支持混合使用，即在测试工程模式的用例中不能调用Driver模式提供的driver对象创建和关闭接口。
测试工程模式下，driver对应的设备资源由任务调度框架进行管理。

#### Driver模式

新建test.py文件，保存以下代码示例并执行，即可启动设置应用。

```python
from hypium import UiDriver

driver = UiDriver.connect()  # 创建driver对象，注意该接口不支持在测试工程模式中调用。

driver.start_app("com.huawei.hmos.settings")  # 调用driver接口，实现设备操作。

driver.close()  # 关闭driver，释放资源，注意该接口不支持在测试工程模式中调用。
```

可以在创建driver时指定设备序列号，以及配置日志级别。

```python
from hypium import UiDriver

driver = UiDriver.connect(device_sn="device_sn", log_level="debug")  # 创建driver对象，注意该接口不支持在测试工程模式中调用。

driver.start_app("com.huawei.hmos.settings")  # 调用driver接口，实现设备操作。

driver.close()  # 关闭driver, 释放资源，注意该接口不支持在测试工程模式中调用。
```

#### 测试工程模式

测试工程模式的使用方法请参考[测试脚本快速开发入门](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/hypium-python-guidelines#section589563925210)
文档。

> 更多详细使用指南请参考华为开发者联盟网站[应用UI测试](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/hypium-python-guidelines)。

### API文档

安裝Hypium后，执行 `python -m hypium.docs` 可以查看内置全量API文档路径。

```plaintext
Hypium API references path: /path/to/hypium/docs/hypium_api_20251027220918.md
```

也可以访问[应用UI测试-API使用方法](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/hypium-python-guidelines#section4598236435)
查看常用的API使用说明。

## 隐私声明

Hypium **不会**收集涉及用户的测试用例相关信息，如用例名称、用例数量、执行日志、屏幕截图等。

Hypium **会**收集以下信息用于分析Hypium各功能在不同平台上的使用情况，从而针对性地优化我们的产品：

1. 执行设备的操作系统平台和版本号
2. 被测设备的型号以及鸿蒙系统版本
3. 被测应用的名称或包名
4. Hypium特性功能的触发时间和使用次数

所有Hypium收集的信息均为匿名数据，**不包含**可追踪用户的标识符。

### 关闭用户信息收集

您可以在项目根目录运行 `python -m hypium telemetry disable` 来停止收集Hypium运行相关用户信息。
您可以在项目根目录运行 `python -m hypium telemetry enable` 来开启收集Hypium运行相关用户信息。
您可以在项目根目录运行 `python -m hypium telemetry status` 来查看Hypium运行相关用户信息的收集状态。

> 完整的隐私协议请访问[应用UI测试](https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/hypium-python-guidelines#section112896130577)查看。