"""
Gradio 事件与交互
=================
Gradio 提供了丰富的事件处理机制，用于创建交互式应用。

本文件涵盖：
- 事件绑定：click, change, submit 等
- 事件链接与依赖
- 状态管理 (gr.State)
- 进度条与流式输出
- 组件可见性控制

适用 Python 版本：3.8+
"""

import time

import gradio as gr

# region 示例1: 常见事件类型
if True:  # 改为 False 可跳过此示例
    with gr.Blocks() as demo:
        gr.Markdown("# 🎯 事件类型演示")

        with gr.Row():
            with gr.Column():
                # Textbox 的 change 事件：内容改变时触发
                text_input = gr.Textbox(label="输入文本（change 事件）")
                char_count = gr.Number(label="字符数（实时更新）")

                # Number 的 change 事件
                number_input = gr.Number(label="输入数字", value=0)
                squared = gr.Number(label="平方值")

            with gr.Column():
                # Textbox 的 submit 事件：按 Enter 时触发
                submit_input = gr.Textbox(label="按 Enter 提交")
                submit_output = gr.Textbox(label="提交结果")

                # Button 的 click 事件
                click_btn = gr.Button("点击我", variant="primary")
                click_output = gr.Textbox(label="点击结果")

        # 绑定 change 事件
        text_input.change(
            fn=lambda x: len(x) if x else 0, inputs=text_input, outputs=char_count
        )

        number_input.change(
            fn=lambda x: x**2 if x is not None else 0,
            inputs=number_input,
            outputs=squared,
        )

        # 绑定 submit 事件
        submit_input.submit(
            fn=lambda x: f"你提交了: {x}", inputs=submit_input, outputs=submit_output
        )

        # 绑定 click 事件
        click_count = gr.State(0)  # 使用 State 保存状态

        def on_click(count: int) -> tuple[str, int]:
            count += 1
            return f"按钮被点击了 {count} 次", count

        click_btn.click(
            fn=on_click, inputs=click_count, outputs=[click_output, click_count]
        )

    demo.launch()
# endregion

# region 示例2: 事件链接（多个事件串联）
if False:  # 改为 True 可运行此示例
    with gr.Blocks() as demo:
        gr.Markdown("# 🔗 事件链接演示")
        gr.Markdown("点击按钮后，多个步骤会依次执行")

        input_text = gr.Textbox(label="输入", value="Hello")

        step1_output = gr.Textbox(label="步骤 1: 转大写")
        step2_output = gr.Textbox(label="步骤 2: 添加装饰")
        step3_output = gr.Textbox(label="步骤 3: 最终结果")

        process_btn = gr.Button("开始处理", variant="primary")

        def step1(text: str) -> str:
            time.sleep(0.5)  # 模拟耗时操作
            return text.upper()

        def step2(text: str) -> str:
            time.sleep(0.5)
            return f"✨ {text} ✨"

        def step3(text: str) -> str:
            time.sleep(0.5)
            return f"【{text}】处理完成！"

        # 使用 .then() 链接多个事件
        process_btn.click(fn=step1, inputs=input_text, outputs=step1_output).then(
            fn=step2, inputs=step1_output, outputs=step2_output
        ).then(fn=step3, inputs=step2_output, outputs=step3_output)

    demo.launch()
# endregion

# region 示例3: 状态管理 (gr.State)
if False:  # 改为 True 可运行此示例
    with gr.Blocks() as demo:
        gr.Markdown("# 📦 状态管理演示")
        gr.Markdown("使用 `gr.State` 在多次交互之间保持状态")

        # State 用于保存用户会话中的数据
        history = gr.State([])  # 初始值为空列表

        with gr.Row():
            with gr.Column(scale=2):
                item_input = gr.Textbox(label="添加项目", placeholder="输入内容...")
                with gr.Row():
                    add_btn = gr.Button("➕ 添加", variant="primary")
                    clear_btn = gr.Button("🗑️ 清空", variant="stop")

            with gr.Column(scale=3):
                history_display = gr.Textbox(
                    label="历史记录",
                    lines=10,
                    interactive=False,
                )
                count_display = gr.Number(label="项目数量")

        def add_item(item: str, hist: list) -> tuple[list, str, int, str]:
            if item.strip():
                hist = [*hist, item]  # 创建新列表避免修改原列表
            display = "\n".join(f"{i + 1}. {h}" for i, h in enumerate(hist))
            return hist, display, len(hist), ""

        def clear_history() -> tuple[list, str, int]:
            return [], "", 0

        add_btn.click(
            fn=add_item,
            inputs=[item_input, history],
            outputs=[history, history_display, count_display, item_input],
        )

        clear_btn.click(
            fn=clear_history, outputs=[history, history_display, count_display]
        )

    demo.launch()
# endregion

# region 示例4: 进度条
if False:  # 改为 True 可运行此示例
    with gr.Blocks() as demo:
        gr.Markdown("# ⏳ 进度条演示")

        task_count = gr.Slider(
            label="任务数量", minimum=1, maximum=20, value=10, step=1
        )
        start_btn = gr.Button("开始处理", variant="primary")
        result = gr.Textbox(label="处理结果", lines=5)

        def process_tasks(count: int, progress=gr.Progress()) -> str:
            """使用 gr.Progress() 显示进度"""
            results = []

            # 使用 progress.tqdm 包装迭代器
            for i in progress.tqdm(range(int(count)), desc="处理中"):
                time.sleep(0.3)  # 模拟耗时任务
                results.append(f"任务 {i + 1} 完成")

            return "\n".join(results)

        start_btn.click(fn=process_tasks, inputs=task_count, outputs=result)

    demo.launch()
# endregion

# region 示例5: 流式输出（打字机效果）
if False:  # 改为 True 可运行此示例
    with gr.Blocks() as demo:
        gr.Markdown("# ⌨️ 流式输出演示")
        gr.Markdown("模拟 ChatGPT 的打字机效果")

        prompt = gr.Textbox(label="输入提示", value="请给我讲一个故事")
        generate_btn = gr.Button("生成", variant="primary")
        output = gr.Textbox(label="生成结果", lines=10)

        def generate_stream(text: str):
            """使用 yield 实现流式输出"""
            response = f"好的，根据你的提示「{text}」，我来生成一个故事：\n\n"
            story = """从前有一座山，山里有一座庙。庙里有一个老和尚在给小和尚讲故事。讲的什么呢？

"从前有一座山，山里有一座庙……"

小和尚听着听着就睡着了。月光洒在窗台上，微风轻轻吹过。老和尚看着熟睡的小和尚，微微一笑，轻声说道：

"做个好梦吧。"

故事就这样结束了。"""

            # 逐字输出
            for char in story:
                response += char
                yield response  # 使用 yield 返回中间结果
                time.sleep(0.05)  # 控制输出速度

        generate_btn.click(fn=generate_stream, inputs=prompt, outputs=output)

    demo.launch()
# endregion

# region 示例6: 组件可见性控制
if False:  # 改为 True 可运行此示例
    with gr.Blocks() as demo:
        gr.Markdown("# 👁️ 组件可见性控制")

        mode = gr.Radio(
            label="选择模式",
            choices=["简单模式", "高级模式"],
            value="简单模式",
        )

        # 简单模式组件
        with gr.Group(visible=True) as simple_group:
            gr.Markdown("### 简单模式")
            simple_input = gr.Textbox(label="简单输入")

        # 高级模式组件
        with gr.Group(visible=False) as advanced_group:
            gr.Markdown("### 高级模式")
            with gr.Row():
                adv_input1 = gr.Textbox(label="输入 1")
                adv_input2 = gr.Textbox(label="输入 2")
            with gr.Row():
                adv_slider = gr.Slider(label="参数", minimum=0, maximum=100, value=50)
                adv_checkbox = gr.Checkbox(label="启用额外功能")

        output = gr.Textbox(label="输出")
        submit = gr.Button("提交", variant="primary")

        def toggle_mode(selected_mode: str) -> tuple:
            """切换模式时更新组件可见性"""
            if selected_mode == "简单模式":
                return gr.update(visible=True), gr.update(visible=False)
            else:
                return gr.update(visible=False), gr.update(visible=True)

        mode.change(
            fn=toggle_mode,
            inputs=mode,
            outputs=[simple_group, advanced_group],
        )

        def process(mode_val, simple, adv1, adv2, slider, checkbox):
            if mode_val == "简单模式":
                return f"简单模式处理: {simple}"
            else:
                return f"高级模式处理: {adv1}, {adv2}, 参数={slider}, 额外功能={'启用' if checkbox else '禁用'}"

        submit.click(
            fn=process,
            inputs=[
                mode,
                simple_input,
                adv_input1,
                adv_input2,
                adv_slider,
                adv_checkbox,
            ],
            outputs=output,
        )

    demo.launch()
# endregion
