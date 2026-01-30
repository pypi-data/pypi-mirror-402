"""
Gradio 高级应用
===============
本文件展示 Gradio 的高级功能和实际应用场景。

本文件涵盖：
- 聊天界面 (ChatInterface)
- 多页面应用
- 与 API 集成
- 认证与访问控制
- 队列与并发处理

适用 Python 版本：3.8+
"""

import random
import time

import gradio as gr

# region 示例1: 聊天界面 (ChatInterface)
if False:  # 改为 False 可跳过此示例

    def echo_bot(message: str, history: list) -> str:
        """简单的回声机器人"""
        # history 是一个列表，每个元素是 [用户消息, 机器人回复]
        responses = [
            f"你说的是：{message}",
            f"我收到了你的消息：'{message}'",
            f"有趣！你说了 '{message}'",
            f"让我想想...你是说 '{message}' 对吧？",
        ]
        return random.choice(responses)

    # ChatInterface 是专门为聊天应用设计的高级接口
    demo = gr.ChatInterface(
        fn=echo_bot,
        title="🤖 Echo Bot",
        description="一个简单的回声机器人，会重复你说的话",
        examples=["你好！", "今天天气怎么样？", "给我讲个笑话"],
    )

    demo.launch()
# endregion

# region 示例2: 流式聊天（模拟 LLM）
if False:  # 改为 True 可运行此示例

    def fake_llm_stream(message: str, history: list):
        """模拟大语言模型的流式回复"""
        responses = {
            "你好": "你好！很高兴见到你。有什么我可以帮助你的吗？",
            "讲个笑话": "好的，来一个：为什么程序员总是分不清万圣节和圣诞节？因为 Oct 31 = Dec 25！（八进制的31等于十进制的25）😄",
            "default": f"我理解你说的是「{message}」。作为一个演示机器人，我的回复能力有限。但我可以展示流式输出的效果！这段文字会逐字显示出来...",
        }

        response = responses.get(message, responses["default"])

        # 流式输出：逐字返回
        partial = ""
        for char in response:
            partial += char
            time.sleep(0.03)
            yield partial

    demo = gr.ChatInterface(
        fn=fake_llm_stream,
        title="🧠 模拟 LLM 聊天",
        description="模拟大语言模型的流式回复效果",
        examples=["你好", "讲个笑话", "介绍一下 Python"],
    )

    demo.launch()
# endregion

# region 示例3: 自定义聊天界面
if False:  # 改为 True 可运行此示例
    with gr.Blocks() as demo:
        gr.Markdown("# 💬 自定义聊天界面")

        # 使用 Chatbot 组件
        chatbot = gr.Chatbot(
            label="对话",
            height=400,
            buttons=["copy"],  # Gradio 6.x 使用 buttons 参数代替 show_copy_button
        )

        with gr.Row():
            msg = gr.Textbox(
                label="输入消息",
                placeholder="输入你的消息...",
                scale=4,
            )
            send = gr.Button("发送", variant="primary", scale=1)

        clear = gr.Button("清空对话")

        # 系统设置
        with gr.Accordion("⚙️ 设置", open=False):
            temperature = gr.Slider(
                label="温度",
                minimum=0,
                maximum=1,
                value=0.7,
                step=0.1,
                info="较高的值会使输出更随机",
            )
            max_tokens = gr.Slider(
                label="最大长度",
                minimum=50,
                maximum=500,
                value=200,
                step=50,
            )

        def respond(message: str, chat_history: list, temp: float, max_len: int):
            """处理用户消息并生成回复"""
            if not message.strip():
                return "", chat_history

            # 模拟根据温度生成不同风格的回复
            if temp < 0.3:
                style = "正式"
            elif temp < 0.7:
                style = "友好"
            else:
                style = "创意"

            bot_response = f"[{style}风格，最大{int(max_len)}字] 你说的是：{message}"

            # 更新聊天历史
            chat_history.append({"role": "user", "content": message})
            chat_history.append({"role": "assistant", "content": bot_response})
            return "", chat_history

        # 绑定发送事件
        msg.submit(respond, [msg, chatbot, temperature, max_tokens], [msg, chatbot])
        send.click(respond, [msg, chatbot, temperature, max_tokens], [msg, chatbot])
        clear.click(lambda: [], outputs=[chatbot])

    demo.launch()
# endregion

# region 示例4: API 集成与 HTTP 请求
if False:  # 改为 True 可运行此示例
    import urllib.request
    import json

    def fetch_random_joke() -> str:
        """从公共 API 获取随机笑话"""
        try:
            # 使用一个简单的公共 API
            url = "https://official-joke-api.appspot.com/random_joke"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode())
                return f"**{data['setup']}**\n\n{data['punchline']}"
        except Exception as e:
            return f"获取失败: {e}"

    def fetch_random_activity() -> str:
        """从 Bored API 获取随机活动建议"""
        try:
            url = "https://www.boredapi.com/api/activity"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode())
                return f"""
**活动建议**: {data["activity"]}

- 类型: {data["type"]}
- 参与人数: {data["participants"]}
- 难度: {data.get("accessibility", "N/A")}
"""
        except Exception as e:
            return f"获取失败: {e}"

    with gr.Blocks() as demo:
        gr.Markdown("# 🌐 API 集成演示")

        with gr.Row():
            with gr.Column():
                gr.Markdown("### 😂 随机笑话")
                joke_output = gr.Markdown("点击按钮获取笑话")
                joke_btn = gr.Button("获取笑话", variant="primary")
                joke_btn.click(fetch_random_joke, outputs=joke_output)

            with gr.Column():
                gr.Markdown("### 🎲 无聊了做什么")
                activity_output = gr.Markdown("点击按钮获取建议")
                activity_btn = gr.Button("获取建议", variant="primary")
                activity_btn.click(fetch_random_activity, outputs=activity_output)

    demo.launch()
# endregion

# region 示例5: 队列与并发控制
if False:  # 改为 True 可运行此示例

    def slow_task(name: str, duration: int, progress=gr.Progress()) -> str:
        """模拟一个耗时任务"""
        for i in progress.tqdm(range(int(duration)), desc=f"处理 {name}"):
            time.sleep(1)
        return f"✅ 任务 '{name}' 完成！耗时 {duration} 秒"

    # 启用队列可以更好地处理并发请求
    with gr.Blocks() as demo:
        gr.Markdown("# ⏱️ 队列演示")
        gr.Markdown(
            """
        队列系统可以确保长时间运行的任务不会阻塞其他用户。
        尝试在多个标签页中同时运行任务！
        """
        )

        with gr.Row():
            task_name = gr.Textbox(label="任务名称", value="我的任务")
            task_duration = gr.Slider(
                label="任务时长（秒）", minimum=1, maximum=10, value=5, step=1
            )

        run_btn = gr.Button("运行任务", variant="primary")
        result = gr.Textbox(label="结果")

        run_btn.click(fn=slow_task, inputs=[task_name, task_duration], outputs=result)

    # queue() 启用队列系统
    demo.queue(
        max_size=10,  # 最大队列长度
    ).launch()
# endregion

# region 示例6: 认证与访问控制
if True:  # 改为 True 可运行此示例

    def secret_function(password: str) -> str:
        """一个需要验证的功能"""
        return f"🎉 欢迎！你已经通过了认证。密码是: {password}"

    with gr.Blocks() as demo:
        gr.Markdown("# 🔐 认证演示")
        gr.Markdown("这个应用需要登录才能访问")

        with gr.Row():
            input_text = gr.Textbox(label="输入一些内容")
            output_text = gr.Textbox(label="输出")

        submit_btn = gr.Button("提交", variant="primary")
        submit_btn.click(lambda x: f"你输入了: {x}", input_text, output_text)

    # 使用 auth 参数启用基本认证
    # 用户名: admin, 密码: password
    demo.launch(
        auth=("admin", "password"),  # 单用户认证
        # auth=[("user1", "pass1"), ("user2", "pass2")],  # 多用户认证
        # auth=lambda u, p: u == "admin" and p == "secret",  # 自定义认证函数
        auth_message="请输入用户名和密码（admin/password）",
    )
# endregion
