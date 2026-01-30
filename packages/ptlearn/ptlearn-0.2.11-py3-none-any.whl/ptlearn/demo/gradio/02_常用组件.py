"""
Gradio 常用组件
===============
Gradio 提供了 30+ 种内置组件，用于处理各种类型的输入输出。

本文件涵盖：
- 文本类组件: Textbox, Markdown, Code
- 数值类组件: Number, Slider
- 选择类组件: Dropdown, Radio, Checkbox, CheckboxGroup
- 媒体类组件: Image, Audio, Video
- 文件类组件: File, UploadButton

适用 Python 版本：3.8+
"""

import gradio as gr

# region 示例1: 文本类组件
if True:  # 改为 False 可跳过此示例

    def process_text(plain_text: str, code: str) -> tuple[str, str]:
        """处理纯文本和代码"""
        # 统计信息
        stats = f"""
## 📊 文本统计

| 指标 | 值 |
|------|-----|
| 字符数 | {len(plain_text)} |
| 单词数 | {len(plain_text.split())} |
"""
        # 格式化代码
        formatted_code = f"# 你输入的代码:\n{code}"
        return stats, formatted_code

    demo = gr.Interface(
        fn=process_text,
        inputs=[
            gr.Textbox(
                label="纯文本输入",
                placeholder="输入任意文本...",
                lines=3,
                max_lines=10,
            ),
            gr.Code(
                label="代码输入",
                language="python",  # 支持多种语言高亮
                lines=5,
            ),
        ],
        outputs=[
            gr.Markdown(label="统计结果（Markdown 渲染）"),
            gr.Code(label="格式化代码", language="python"),
        ],
        title="📝 文本类组件演示",
    )

    demo.launch()
# endregion

# region 示例2: 数值类组件
if False:  # 改为 True 可运行此示例

    def calculate_bmi(weight: float, height: float) -> tuple[float, str]:
        """计算 BMI 指数"""
        if height <= 0:
            return 0, "身高必须大于 0"

        bmi = weight / (height / 100) ** 2
        bmi = round(bmi, 2)

        if bmi < 18.5:
            category = "偏瘦 🥗"
        elif bmi < 24:
            category = "正常 ✅"
        elif bmi < 28:
            category = "偏胖 ⚠️"
        else:
            category = "肥胖 🚨"

        return bmi, f"BMI: {bmi}，分类: {category}"

    demo = gr.Interface(
        fn=calculate_bmi,
        inputs=[
            gr.Number(
                label="体重 (kg)",
                value=70,  # 默认值
                minimum=20,
                maximum=200,
                step=0.5,
            ),
            gr.Slider(
                label="身高 (cm)",
                minimum=100,
                maximum=220,
                value=170,
                step=1,
                info="拖动滑块选择身高",
            ),
        ],
        outputs=[
            gr.Number(label="BMI 指数", precision=2),
            gr.Textbox(label="健康评估"),
        ],
        title="🏃 BMI 计算器",
        description="输入体重和身高，计算你的 BMI 指数",
    )

    demo.launch()
# endregion

# region 示例3: 选择类组件
if False:  # 改为 True 可运行此示例

    def generate_order_summary(
        drink: str,
        size: str,
        is_ice: bool,
        toppings: list[str],
    ) -> str:
        """生成订单摘要"""
        order = f"""
🧋 订单确认
━━━━━━━━━━━━━━━━━━
饮品: {drink}
规格: {size}
冰块: {"加冰 🧊" if is_ice else "去冰 ☕"}
配料: {", ".join(toppings) if toppings else "无"}
━━━━━━━━━━━━━━━━━━
"""
        return order

    demo = gr.Interface(
        fn=generate_order_summary,
        inputs=[
            gr.Dropdown(
                label="选择饮品",
                choices=["珍珠奶茶", "抹茶拿铁", "芒果冰沙", "柠檬红茶"],
                value="珍珠奶茶",
                allow_custom_value=False,  # 是否允许自定义输入
            ),
            gr.Radio(
                label="选择规格",
                choices=["小杯", "中杯", "大杯"],
                value="中杯",
            ),
            gr.Checkbox(
                label="是否加冰",
                value=True,
            ),
            gr.CheckboxGroup(
                label="选择配料（可多选）",
                choices=["珍珠", "椰果", "布丁", "芋圆", "红豆"],
                value=["珍珠"],
            ),
        ],
        outputs=gr.Textbox(label="订单摘要", lines=8),
        title="🧋 奶茶点单系统",
    )

    demo.launch()
# endregion

# region 示例4: 图片组件
if False:  # 改为 True 可运行此示例
    from PIL import Image, ImageFilter

    def process_image(
        image: Image.Image,
        effect: str,
        intensity: float,
    ) -> Image.Image:
        """对图片应用滤镜效果"""
        if image is None:
            return None

        if effect == "模糊":
            return image.filter(ImageFilter.GaussianBlur(radius=intensity * 10))
        elif effect == "锐化":
            return image.filter(ImageFilter.SHARPEN)
        elif effect == "边缘检测":
            return image.filter(ImageFilter.FIND_EDGES)
        elif effect == "浮雕":
            return image.filter(ImageFilter.EMBOSS)
        elif effect == "灰度":
            return image.convert("L")
        else:
            return image

    demo = gr.Interface(
        fn=process_image,
        inputs=[
            gr.Image(
                label="上传图片",
                type="pil",  # 返回 PIL.Image 对象
                # type="numpy",  # 返回 numpy 数组
                # type="filepath",  # 返回文件路径
            ),
            gr.Dropdown(
                label="选择效果",
                choices=["模糊", "锐化", "边缘检测", "浮雕", "灰度"],
                value="模糊",
            ),
            gr.Slider(
                label="效果强度",
                minimum=0.1,
                maximum=1.0,
                value=0.5,
                step=0.1,
            ),
        ],
        outputs=gr.Image(label="处理后的图片"),
        title="🖼️ 图片滤镜",
        description="上传图片并应用各种滤镜效果",
    )

    demo.launch()
# endregion

# region 示例5: 文件上传与下载
if False:  # 改为 True 可运行此示例
    import os

    def analyze_file(file) -> tuple[str, str]:
        """分析上传的文件"""
        if file is None:
            return "请先上传文件", ""

        # file 是一个临时文件路径
        file_path = file.name if hasattr(file, "name") else str(file)
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        # 尝试读取文件内容（仅文本文件）
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                preview = content[:500] + "..." if len(content) > 500 else content
        except (OSError, UnicodeDecodeError):
            preview = "（二进制文件，无法预览）"

        info = f"""
📁 文件信息
━━━━━━━━━━━━━━━━
文件名: {file_name}
大小: {file_size:,} 字节
路径: {file_path}
━━━━━━━━━━━━━━━━
"""
        return info, preview

    demo = gr.Interface(
        fn=analyze_file,
        inputs=gr.File(
            label="上传文件",
            file_types=[".txt", ".py", ".json", ".md"],  # 限制文件类型
        ),
        outputs=[
            gr.Textbox(label="文件信息", lines=7),
            gr.Textbox(label="内容预览", lines=10),
        ],
        title="📁 文件分析器",
        description="上传文本文件，查看文件信息和内容预览",
    )

    demo.launch()
# endregion

# region 示例6: 按钮组件
if False:  # 改为 True 可运行此示例
    # 使用 Blocks API 创建带按钮的界面
    with gr.Blocks() as demo:
        gr.Markdown("# 🎲 随机数生成器")

        with gr.Row():
            min_val = gr.Number(label="最小值", value=1)
            max_val = gr.Number(label="最大值", value=100)

        result = gr.Number(label="生成的随机数")

        # 创建按钮
        generate_btn = gr.Button("🎲 生成随机数", variant="primary")
        clear_btn = gr.Button("🗑️ 清除", variant="secondary")

        # 定义按钮点击事件
        import random

        def generate_random(min_v: float, max_v: float) -> float:
            return random.randint(int(min_v), int(max_v))

        def clear_result() -> float:
            return 0

        generate_btn.click(
            fn=generate_random,
            inputs=[min_val, max_val],
            outputs=result,
        )

        clear_btn.click(
            fn=clear_result,
            inputs=None,
            outputs=result,
        )

    demo.launch()
# endregion
