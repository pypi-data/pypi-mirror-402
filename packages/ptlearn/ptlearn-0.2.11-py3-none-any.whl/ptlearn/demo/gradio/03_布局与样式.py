"""
Gradio 布局与样式
=================
使用 gr.Blocks 可以创建更复杂、更灵活的布局。
相比 gr.Interface，Blocks 提供了更细粒度的控制。

本文件涵盖：
- Blocks 基础
- Row 和 Column 布局
- Tab 标签页
- Accordion 折叠面板
- 主题与样式自定义

适用 Python 版本：3.8+
"""

import gradio as gr

# region 示例1: Blocks 基础结构
if False:  # 改为 False 可跳过此示例
    # gr.Blocks 是一个上下文管理器，所有组件都在其中定义
    with gr.Blocks() as demo:
        # Markdown 组件用于显示标题和说明
        gr.Markdown(
            """
        # 🎨 Blocks 基础示例
        这是一个使用 `gr.Blocks` 创建的界面
        """
        )

        # 定义输入组件
        name_input = gr.Textbox(label="你的名字", placeholder="输入名字...")

        # 定义输出组件
        greeting_output = gr.Textbox(label="问候语")

        # 定义按钮
        greet_button = gr.Button("打招呼", variant="primary")

        # 定义处理函数
        def greet(name: str) -> str:
            return f"你好，{name}！欢迎使用 Gradio Blocks！"

        # 绑定事件：点击按钮时调用函数
        greet_button.click(
            fn=greet,
            inputs=name_input,
            outputs=greeting_output,
        )

    demo.launch()
# endregion

# region 示例2: Row 和 Column 布局
if False:  # 改为 True 可运行此示例
    with gr.Blocks() as demo:
        gr.Markdown("# 📐 Row 和 Column 布局演示")

        # Row: 水平排列组件
        with gr.Row():
            gr.Textbox(label="左侧输入框", scale=1)
            gr.Textbox(label="中间输入框", scale=2)  # scale 控制相对宽度
            gr.Textbox(label="右侧输入框", scale=1)

        gr.Markdown("---")

        # Column: 垂直排列组件
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 左列")
                gr.Textbox(label="输入 1")
                gr.Textbox(label="输入 2")

            with gr.Column(scale=2):
                gr.Markdown("### 右列 (更宽)")
                gr.Textbox(label="输入 3", lines=4)

        gr.Markdown("---")

        # 嵌套布局
        with gr.Row():
            with gr.Column():
                gr.Markdown("#### 嵌套示例")
                with gr.Row():
                    gr.Number(label="数字 1")
                    gr.Number(label="数字 2")
                gr.Button("计算", variant="primary")

            with gr.Column():
                gr.Markdown("#### 结果区域")
                gr.Textbox(label="结果", lines=3)

    demo.launch()
# endregion

# region 示例3: Tab 标签页
if False:  # 改为 True 可运行此示例
    with gr.Blocks() as demo:
        gr.Markdown("# 📑 标签页演示")

        with gr.Tabs():
            # 第一个标签页
            with gr.TabItem("📝 文本处理"):
                text_input = gr.Textbox(label="输入文本", lines=3)
                text_output = gr.Textbox(label="处理结果", lines=3)

                with gr.Row():
                    upper_btn = gr.Button("转大写")
                    lower_btn = gr.Button("转小写")
                    reverse_btn = gr.Button("反转")

                upper_btn.click(lambda x: x.upper(), text_input, text_output)
                lower_btn.click(lambda x: x.lower(), text_input, text_output)
                reverse_btn.click(lambda x: x[::-1], text_input, text_output)

            # 第二个标签页
            with gr.TabItem("🔢 数学计算"):
                with gr.Row():
                    num_a = gr.Number(label="数字 A", value=10)
                    num_b = gr.Number(label="数字 B", value=5)

                calc_result = gr.Number(label="结果")

                with gr.Row():
                    add_btn = gr.Button("➕ 加")
                    sub_btn = gr.Button("➖ 减")
                    mul_btn = gr.Button("✖️ 乘")
                    div_btn = gr.Button("➗ 除")

                add_btn.click(lambda a, b: a + b, [num_a, num_b], calc_result)
                sub_btn.click(lambda a, b: a - b, [num_a, num_b], calc_result)
                mul_btn.click(lambda a, b: a * b, [num_a, num_b], calc_result)
                div_btn.click(
                    lambda a, b: a / b if b != 0 else 0, [num_a, num_b], calc_result
                )

            # 第三个标签页
            with gr.TabItem("ℹ️ 关于"):
                gr.Markdown(
                    """
                ## 关于本示例
                
                这是一个展示 Gradio Tab 组件的示例。
                
                **功能列表：**
                - 文本处理：大小写转换、反转
                - 数学计算：基本四则运算
                """
                )

    demo.launch()
# endregion

# region 示例4: Accordion 折叠面板
if False:  # 改为 True 可运行此示例
    with gr.Blocks() as demo:
        gr.Markdown("# 📦 折叠面板演示")

        input_text = gr.Textbox(label="输入文本", value="Hello Gradio")

        # Accordion 默认折叠，点击展开
        with gr.Accordion("⚙️ 高级设置", open=False):
            with gr.Row():
                repeat_count = gr.Slider(
                    label="重复次数", minimum=1, maximum=10, value=3, step=1
                )
                separator = gr.Textbox(label="分隔符", value=" | ")

        with gr.Accordion("📊 统计信息", open=True):
            char_count = gr.Number(label="字符数")
            word_count = gr.Number(label="单词数")

        output_text = gr.Textbox(label="输出结果", lines=3)
        process_btn = gr.Button("处理", variant="primary")

        def process(text: str, repeat: int, sep: str) -> tuple[str, int, int]:
            result = sep.join([text] * int(repeat))
            return result, len(text), len(text.split())

        process_btn.click(
            fn=process,
            inputs=[input_text, repeat_count, separator],
            outputs=[output_text, char_count, word_count],
        )

    demo.launch()
# endregion

# region 示例5: 主题定制
if False:  # 改为 True 可运行此示例
    # 使用预设主题
    # 可选主题: gr.themes.Default(), Soft(), Monochrome(), Glass(), Base()

    # 自定义主题
    custom_theme = gr.themes.Soft(
        primary_hue="emerald",  # 主色调
        secondary_hue="blue",  # 次要色调
        neutral_hue="slate",  # 中性色调
        font=gr.themes.GoogleFont("Noto Sans SC"),  # 自定义字体
    ).set(
        # 进一步自定义
        body_background_fill="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        body_background_fill_dark="linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
        button_primary_background_fill="*primary_500",
        button_primary_background_fill_hover="*primary_600",
        block_title_text_weight="600",
        block_border_width="2px",
    )

    with gr.Blocks(theme=custom_theme) as demo:
        gr.Markdown(
            """
        # 🎨 自定义主题示例
        
        这个界面使用了自定义的 Gradio 主题
        """
        )

        with gr.Row():
            with gr.Column():
                gr.Textbox(label="输入", placeholder="输入一些文本...")
                gr.Slider(label="滑块", minimum=0, maximum=100, value=50)
                gr.Checkbox(label="选项", value=True)

            with gr.Column():
                gr.Textbox(label="输出", lines=3)
                with gr.Row():
                    gr.Button("主要按钮", variant="primary")
                    gr.Button("次要按钮", variant="secondary")
                    gr.Button("停止按钮", variant="stop")

    demo.launch()
# endregion

# region 示例6: CSS 自定义样式
if True:  # 改为 True 可运行此示例
    # 使用自定义 CSS
    custom_css = """
    .gradio-container {
        max-width: 800px !important;
    }
    
    .custom-title {
        text-align: center;
        background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5em !important;
        font-weight: bold;
    }
    
    .highlight-box {
        border: 2px solid #4ecdc4;
        border-radius: 10px;
        padding: 10px;
        background-color: rgba(78, 205, 196, 0.1);
    }
    """

    with gr.Blocks() as demo:
        # elem_classes 用于添加自定义 CSS 类
        gr.Markdown("# Gradio 样式定制", elem_classes=["custom-title"])

        with gr.Row():
            with gr.Column(elem_classes=["highlight-box"]):
                gr.Markdown("### 🎯 输入区域")
                user_input = gr.Textbox(label="输入", placeholder="在这里输入...")
                submit_btn = gr.Button("提交", variant="primary")

            with gr.Column(elem_classes=["highlight-box"]):
                gr.Markdown("### 📤 输出区域")
                output = gr.Textbox(label="输出", lines=3)

        submit_btn.click(lambda x: f"你输入了: {x}", user_input, output)

    demo.launch(css=custom_css)
# endregion
