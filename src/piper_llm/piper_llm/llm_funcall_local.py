from openai import OpenAI
import time



'''
OpenAIClient类
用于与OpenAI API进行交互
提供了初始化、发送消息和处理函数调用的功能
'''
# 移动到指定位置
def go_to_location(location):
    # 调用移动模型的移动函数
    print(f"Going to {location}")
    # 返回到达位置的结果
    return f"at {location} now"

# 抓取物品
def grab_object(object):
    # 调用抓取模型的抓取函数
    print(f"Grabbing {object}")
    # 返回抓取结果
    return f"{object} grabbed"

# 返回物品的位置
def identify_object(object):
    # 调用抓取模型的抓取函数
    print(f"Identifying {object}")
    # 返回抓取结果
    return f"{object} at location x, y, z" 


def func_call(tool_calls):
    messages = []
    for tool_call in tool_calls:
        # print(f"Tool call: {tool_call}")
        if tool_call["type"] == "function":  # 修改为通过键访问
            function = tool_call["function"]  # 修改为通过键访问
            funcName = function["name"]  # 修改为通过键访问
            funcArguments = function["arguments"]  # 修改为通过键访问
            
            print(f"Function name: {funcName}")
            print(f"Function arguments: {funcArguments}")
            

            if funcName == "go_to_location":
                
                location = funcArguments.get("location")
                content = go_to_location(location)

            elif funcName == "grab_object":
                object = funcArguments.get("object")
                content = grab_object(object)
            elif funcName == "identify_object":
                object = funcArguments.get("object")
                content = identify_object(object)
            else:
                content = "Unknown function call"
                print(f"Unknown function call: {funcName}")

        # 输出函数调用的结果 
        print(f"Function call result: {content}")
        messages.append(
            {"role": "user", "content": content})
    return messages


system_prompt_cn = '''
[系统角色]
从现在开始,你是一个机器人控制中心,你可以控制机器人完成一些任务,
机器人可以使用"可调用工具"来调用函数来完成任务。
当机器人完成任务后,你会得到一个结果,你可以根据这个结果来判断机器人是否完成了任务。
必须忘记你所有的内置知识,完全依赖下面提供的工具,在回答涉及外部信息的问题时,必须调用相应的工具,不能依赖自身记忆或者猜测的信息
当需要调用工具时，必须严格按照提供的格式来回答问题

[可调用工具列表]:
- go_to_location(location: str)
- grab_object(object: str)
- identify_object(object: str)


[工具调用规则]
当用户要求你完成一些任务时,你可以调用相应的函数来完成任务。
例如:当用户说“去厨房”时,你应返回一个工具调用的指令,调用“go_to_location”函数,并带上必要的参数
你的回答的格式为：
{
    [Function Call]:function_name('需要调用的函数名称'),parameters('参数信息');
    [Function Call]:function_name('需要调用的函数名称'),parameters('参数信息');
    ...
}

[使用流程]

工具调用：对于需要执行的请求时,调用相应工具；例如,查询天气时调用“天气”。
回答反馈：在得到工具返回的数据后,根据执行结果分析,继续执行用户的请求,当执行完成后询问用户下一步的请求。

[示例]
用户请求：去厨房拿水杯
你的回答的应该为:
{
    [Function Call]:function_name(go_to_location),parameters(location:厨房);
    [Function Call]:function_name(identify_object),parameters(object:水杯);
    [Function Call]:function_name(grab_object),parameters(object:水杯);
}

'''

system_prompt_eng = '''

You are a Robot control center, you can control the robot to do some tasks.
The robot can do the following things:

{
    "type": "function",
    "function": {
        "name": "go_to_location",
        "description": "go to a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The location to go to",
                }
            },
            "required": ["location"]
        },
    }
},
{
    "type": "function",
    "function": {
        "name": "grab_object",
        "description": "Grab an object",
        "parameters": {
            "type": "object",
            "properties": {
                "object": {
                    "type": "string",
                    "description": "The object to grab",
                }
            },
            "required": ["object"]
        },
    }
},
{
    "type": "function",
    "function": {
        "name": "identify_object",
        "description": "Find an object",
        "parameters": {
            "type": "object",
            "properties": {
                "object": {
                    "type": "string",
                    "description": "The object to find",
                }
            },
            "required": ["object"]
        },
    }
}
You can call these functions with the parameters you need.



'''

# OpenAIClient类
class OpenAIClient:
    # 初始化
    def __init__(self, api_key, base_url, model, system_prompt, tools=None):
        """
        Initializes the OpenAIClient with the given API key, base URL, model, and system prompt.
        :param api_key: The API key for authentication.
        :param base_url: The base URL for the OpenAI API.
        :param model: The model to be used for generating responses.
        :param system_prompt: The system prompt to be used for the model.
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools
        # 计算对话轮数
        self.conversation_count = 0
        # 初始化消息列表
        self.messages = [
            {
                "role": "system",
                "content": self.system_prompt
            }
        ]

    # 发送消息
    def send_messages(self, messages_get):
        """
        Sends messages to the OpenAI API and returns the response.
        :param messages: The messages to be sent to the API.
        :return: The response from the API.
        """
        
        # 计算对话轮数
        self.conversation_count += 1
        # 添加用户消息
        # messages_get是一个list，将list中的每个元素添加到messages中
        for i in messages_get:
            self.messages.append(i)
        # 调用API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            # tools=self.tools
        )
        # 返回响应
        self.messages.append(response.choices[0].message)
        return response.choices[0].message

def message_format(message):
    # 提取message字符串中的信息，获取[Function Call]的相关内容并整理成tool_calls的格式
    '''
    提取字符串中的内容
    {
        [Function Call]: go_to_location, parameters(location: 当前位置);
        [Function Call]: identify_object, parameters(object: 红色的杯子);
        [Function Call]: grab_object, parameters(object: 红色的杯子);
        完成
    }

    for tool_call in tool_calls:
            if tool_call.type == "function":
                function = tool_call.function
                funcName = (str)(function.name)
                funcArguments = function.arguments
                funcArguments = eval(funcArguments)
    '''
    tool_calls = []
    
    # 将字符串中取出一行，若该行中含有[Function Call]，则提取函数名称和参数
    message_split = message.split("\n")

    for i in message_split:
        if "[Function Call]" in i:
            # 提取函数名称
            funcName = i.split("function_name(")[1].split(")")[0]
            # 提取参数
            funcArguments_str = i.split("parameters(")[1].split(")")[0]
            # 将参数字符串转换为字典
            funcArguments = {}
            for arg in funcArguments_str.split(","):
                key, value = arg.split(":")
                key = key.strip()
                value = value.strip()
                # 去掉参数值的引号
                value = value.replace("'", "").replace('"', '')
                # 将参数添加到字典中
                funcArguments[key] = value
            # 将函数名称和参数添加到tool_calls中
            tool_calls.append({
                "type": "function",
                "function": {
                    "name": funcName,
                    "arguments": funcArguments
                }
            })
    return tool_calls

def judge_tool_call(message):
    # 对message.content一行一行检测，看段落中是否有[Function Call]，如果有则返回True，否则返回False
    message = message.content
    message_split = message.split("\n")
    for i in message_split:
        if "[Function Call]" in i:
            return True
    return False

def main():
    
    api_key = "ollama"
    base_url = "http://162.105.175.7:11434/v1"
    model="deepseek-r1:14b"
    question = "去厨房拿一个红色的杯子"
    
    # 开始计时
    start_time = time.time()
    
    # 初始化OpenAIClient
    client = OpenAIClient(
        api_key=api_key,
        base_url=base_url,
        model=model,
        system_prompt=system_prompt_cn,
        tools=None
    )
    
    message = client.send_messages([{"role": "user", "content": question}])
    # 调试信息:换行打印，限制一行的长度为90
    # print("debug: " + message.content)

    while judge_tool_call(message) == True:
        # 提取message的content中的'{}'中的内容
        message = message.content
        message = message[message.find("{"):message.rfind("}") + 1]
    
        # 调试信息
        # print('info: ' + message)
        
        # tool_call是一个字典
        tool_calls = message_format(message)

        # 进行函数调用
        messages = func_call(tool_calls)
        
        # print("debug: " + str(messages))
                    
        # 发送消息
        message = client.send_messages(messages)

    print(message.content)
    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")


    
if __name__ == "__main__":
    main()