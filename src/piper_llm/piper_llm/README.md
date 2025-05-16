# README

## 简介
`llm_funcal.py` 和 `llm_funcall_local.py`，它们实现了通过调用函数来控制机器人完成任务的功能。两个模块的核心逻辑是通过与LLM交互，解析用户输入的任务指令，并调用相应的函数来完成任务。

---

## 模块解析

### 1. llm_funcal.py
#### 功能
- 通过OpenAI API与DeepSeek模型交互，解析用户输入的任务指令。
- 提供三个主要的机器人控制功能：
  - **go_to_location(location: str)**：移动到指定位置。
  - **grab_object(object: str)**：抓取指定物体。
  - **identify_object(object: str)**：识别指定物体的位置。
  - ...(其他的指令待设计)
- 支持循环调用工具函数，直到任务完成。

#### 核心逻辑
1. **初始化客户端**：
   使用`initialize_client`函数初始化OpenAI客户端，传入API密钥和基础URL。
2. **发送消息**：
   使用`send_messages`函数与模型交互，传递用户输入和工具列表。
3. **函数调用**：
   - 根据模型返回的`tool_calls`，调用对应的函数（如`go_to_location`、`grab_object`等）。
   - 将函数调用结果追加到消息列表中，继续与模型交互。
4. **任务完成**：
   循环调用工具函数，直到模型返回完整的任务结果。

#### 使用方法
1. 设置API密钥和基础URL：
   ```python
   api_key = "your_api_key"
   base_url = "https://api.deepseek.com"
   ```
2. 修改用户问题：
   ```python
   question = "find and grab the red ball on the table then hold the ball go to the kitchen"
   ```
3. 运行脚本：
   ```bash
   python llm_funcal.py
   ```

---

### 2. llm_funcall_local.py
#### 功能
- 本地化实现了与OpenAI API的交互逻辑，支持中文和英文的系统提示。
- 提供与`llm_funcal.py`类似的功能，但更注重本地化和灵活性。
- 通过`OpenAIClient`类封装了API交互逻辑，支持多轮对话。

#### 核心逻辑
1. **OpenAIClient类**：
   - 封装了API初始化、消息发送等功能。
   - 支持多轮对话，自动管理消息历史。
2. **函数调用**：
   - 提供与`llm_funcal.py`相同的功能函数（如`go_to_location`、`grab_object`等）。
   - 使用`func_call`函数解析工具调用并执行相应的操作。
3. **消息格式化**：
   - 使用`message_format`函数解析模型返回的工具调用信息。
   - 支持从模型返回的字符串中提取函数名称和参数。
4. **任务完成**：
   循环调用工具函数，直到任务完成。

#### 使用方法
1. 设置本地模型URL：
   ```python
   base_url = "http://162.105.175.7:11434/v1"
   ```
2. 修改用户问题：
   ```python
   question = "去厨房拿一个红色的杯子"
   ```
3. 运行脚本：
   ```bash
   python llm_funcall_local.py
   ```

---

## 模块对比
| 功能                | llm_funcal.py                     | llm_funcall_local.py               |
|---------------------|-------------------------------------|-------------------------------------|
| API交互            | 使用DeepSeek模型                   | 使用本地部署的模型(没有function call 功能)                      |
| 函数调用方式        | 直接解析`tool_calls`               | 通过`message_format`解析工具调用   |

---

## 注意事项
1. 确保已安装`openai`库：
   ```bash
   pip install openai
   ```
2. 确保API密钥或URL正确配置。
3. 根据需求选择合适的模块运行。