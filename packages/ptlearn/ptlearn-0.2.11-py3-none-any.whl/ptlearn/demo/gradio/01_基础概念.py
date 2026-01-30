"""
Gradio 基础概念
===============
Gradio 是一个用于快速构建机器学习演示界面的 Python 库。
它可以让你用几行代码就把 Python 函数变成交互式 Web 应用。

本文件涵盖：
- 安装与导入
- gr.Interface 基础
- 简单的输入输出示例
- 启动与分享

适用 Python 版本：3.8+
需要安装：pip install gradio
"""

import gradio as gr

# region 示例1: 最简单的 Hello World
if True:  # 改为 False 可跳过此示例
    # 定义一个简单的函数
    def greet(name: str) -> str:
        """接收名字，返回问候语"""
        return f"你好, {name}！欢迎学习 Gradio！"

    # 使用 gr.Interface 创建界面
    # fn: 要封装的函数
    # inputs: 输入组件类型
    # outputs: 输出组件类型
    demo = gr.Interface(
        fn=greet,
        inputs="text",  # 简写形式，等价于 gr.Textbox()
        outputs="text",
        title="Hello World 示例",
        description="输入你的名字，获取问候语",
    )

    # 启动应用
    # share=True 可以生成公网链接（需要网络）
    demo.launch()
# endregion

# region 示例2: 多输入多输出
if False:  # 改为 True 可运行此示例

    def calculate(a: float, b: float, operation: str) -> tuple[float, str]:
        """简单计算器：根据选择的运算符计算结果"""
        if operation == "加法":
            result = a + b
        elif operation == "减法":
            result = a - b
        elif operation == "乘法":
            result = a * b
        elif operation == "除法":
            result = a / b if b != 0 else float("inf")
        else:
            result = 0

        explanation = f"计算过程: {a} {operation} {b} = {result}"
        return result, explanation

    demo = gr.Interface(
        fn=calculate,
        inputs=[
            gr.Number(label="第一个数字"),
            gr.Number(label="第二个数字"),
            gr.Dropdown(
                choices=["加法", "减法", "乘法", "除法"],
                label="运算类型",
                value="加法",  # 默认值
            ),
        ],
        outputs=[
            gr.Number(label="计算结果"),
            gr.Textbox(label="计算说明"),
        ],
        title="简单计算器",
        description="选择两个数字和运算类型，查看计算结果",
    )

    demo.launch()
# endregion

# region 示例3: 使用 examples 提供示例数据
if False:  # 改为 True 可运行此示例

    def echo_with_length(text: str) -> tuple[str, int]:
        """返回输入的文本及其长度"""
        return text.upper(), len(text)

    demo = gr.Interface(
        fn=echo_with_length,
        inputs=gr.Textbox(label="输入文本", placeholder="在这里输入..."),
        outputs=[
            gr.Textbox(label="大写文本"),
            gr.Number(label="文本长度"),
        ],
        # examples 提供预设的示例输入，用户点击即可填充
        examples=[
            ["Hello Gradio"],
            ["Python 是最好的语言"],
            ["机器学习很有趣"],
        ],
        title="文本处理器",
        description="输入文本，查看大写版本和长度",
    )

    demo.launch()
# endregion

# region 示例4: 自定义界面外观
if False:  # 改为 True 可运行此示例

    def reverse_text(text: str) -> str:
        """反转文本"""
        return text[::-1]

    # Interface 支持多种自定义选项
    demo = gr.Interface(
        fn=reverse_text,
        inputs=gr.Textbox(
            label="原始文本",
            placeholder="输入要反转的文本",
            lines=3,  # 文本框行数
        ),
        outputs=gr.Textbox(label="反转后的文本", lines=3),
        title="🔄 文本反转器",
        description="输入任意文本，查看反转结果",
        article="这是一个简单的文本反转工具，适用于各种语言。",  # 底部说明
        theme="soft",  # 主题: default, soft, glass, monochrome 等
        allow_flagging="never",  # 禁用标记功能
    )

    demo.launch(
        server_port=7861,  # 自定义端口
        # share=True,  # 生成公网链接
        # inbrowser=True,  # 自动打开浏览器
    )
# endregion

# region 示例5: 使用 live 模式实现实时更新
if False:  # 改为 True 可运行此示例

    def count_words(text: str) -> dict:
        """统计文本中的单词数量"""
        if not text.strip():
            return {"字符数": 0, "单词数": 0, "行数": 0}

        return {
            "字符数": len(text),
            "单词数": len(text.split()),
            "行数": len(text.splitlines()),
        }

    # live=True 表示输入改变时自动触发函数
    demo = gr.Interface(
        fn=count_words,
        inputs=gr.Textbox(label="输入文本", lines=5, placeholder="在这里输入文本..."),
        outputs=gr.JSON(label="统计结果"),
        title="📊 实时文本统计",
        description="输入文本时自动统计字符数、单词数和行数",
        live=True,  # 实时模式：输入改变时自动更新输出
    )

    demo.launch()
# endregion
