import os
from PIL import Image, ImageDraw, ImageFont # 增加了 ImageFont
import math

# --- 用户配置：字体文件 ---
# 必须将 simhei.ttf 文件放在和此脚本相同的目录下
FONT_FILENAME = "SimHei.ttf"

def crop_to_circle(img):
    """
    [第一步] 将一张图片对象裁剪成圆形，背景填充为白色。
    """
    img = img.convert("RGBA")
    width, height = img.size
    diameter = min(width, height)
    background = Image.new("RGB", (width, height), (255, 255, 255))
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    left = (width - diameter) // 2
    top = (height - diameter) // 2
    right = left + diameter
    bottom = top + diameter
    draw.ellipse((left, top, right, bottom), fill=255)
    background.paste(img, (0, 0), mask)
    return background

def resize_and_place_on_square(img):
    """
    [第二步] 将图片缩小，放置，添加禁止标志，并添加文字。
    """
    original_width, original_height = img.size

    # --- 1. 将图片大小缩小至80% ---
    new_width = int(original_width * 0.8)
    new_height = int(original_height * 0.8)
    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # --- 2. 创建白色正方形背景 ---
    canvas_size = max(original_width, original_height)
    canvas = Image.new("RGB", (canvas_size, canvas_size), (255, 255, 255))

    # --- 3. 计算粘贴位置 ---
    paste_x = (canvas_size - new_width) // 2
    top_margin_percentage = 0.02
    paste_y = int(canvas_size * top_margin_percentage)

    # --- 4. 将缩小后的图片粘贴到背景上 ---
    canvas.paste(resized_img, (paste_x, paste_y))

    # --- 5. 绘制红色圆圈和斜杠 ---
    draw = ImageDraw.Draw(canvas)
    circle_center_x = paste_x + new_width // 2
    circle_center_y = paste_y + new_height // 2
    red_circle_diameter = min(new_width, new_height) + int(canvas_size * 0.02)
    red_circle_radius = red_circle_diameter // 2
    red_circle_bottom = circle_center_y + red_circle_radius # 获取圆圈底部的位置

    line_width = int(canvas_size * 0.06)
    if line_width < 2: line_width = 2
    
    draw.ellipse(
        (circle_center_x - red_circle_radius, circle_center_y - red_circle_radius,
         circle_center_x + red_circle_radius, circle_center_y + red_circle_radius),
        outline=(255, 0, 0), width=line_width
    )
    
    angle = math.pi / 4
    effective_radius = red_circle_radius - (line_width / 2.0)
    dx = effective_radius * math.cos(angle)
    dy = effective_radius * math.sin(angle)
    draw.line(
        (circle_center_x - dx, circle_center_y - dy, circle_center_x + dx, circle_center_y + dy),
        fill=(255, 0, 0), width=line_width
    )

    # --- 6. 在图片下方添加文字 ---
    try:
        text_to_add = "我方禁用英雄"
        font_size = int(canvas_size * 0.10)
        font = ImageFont.truetype(FONT_FILENAME, font_size)
        text_bbox = draw.textbbox((0, 0), text_to_add, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = (canvas_size - text_width) / 2
        space_top = red_circle_bottom
        space_bottom = canvas_size
        space_height = space_bottom - space_top
        text_y = space_top + (space_height - text_height) / 2
        draw.text((text_x, text_y), text_to_add, fill=(0, 0, 0), font=font)

    except FileNotFoundError:
        print(f"错误：找不到字体文件 '{FONT_FILENAME}'。请下载并将其放在脚本旁边。")
    except Exception as e:
        print(f"添加文字时出错: {e}")
    
    return canvas

def batch_process_pipeline(input_folder, output_folder):
    """
    执行完整的批量处理流程。
    读取 -> 处理 -> 保存最终结果
    *** 不会生成任何中间文件或文件夹 ***
    """
    if not os.path.exists(FONT_FILENAME):
        print(f"错误：字体文件 '{FONT_FILENAME}' 未找到！")
        print("请下载 'simhei.ttf' 并将其与Python脚本放在同一个文件夹中，然后重新运行。")
        return

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"已创建输出文件夹: {output_folder}")

    for filename in os.listdir(input_folder):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)
            
            try:
                with Image.open(input_path) as img:
                    # 流程1：裁剪为圆形
                    circled_image = crop_to_circle(img)
                    
                    # 流程2：添加禁止标志和文字
                    final_image = resize_and_place_on_square(circled_image)
                    
                    # 直接保存最终结果
                    final_image.save(output_path, "JPEG")
                    print(f"成功处理: {filename}")
            except Exception as e:
                print(f"处理失败: {filename} - 错误: {e}")

    print("\n所有图片处理完成！")

if __name__ == "__main__":
    # 配置输入和输出目录
    source_directory = "input_images"
    final_directory = "final_images"
    
    if not os.path.isdir(source_directory):
        print(f"错误：输入文件夹 '{source_directory}' 不存在。")
        print(f"请创建一个名为 '{source_directory}' 的文件夹，并将你的图片放入其中。")
    else:
        batch_process_pipeline(source_directory, final_directory)
