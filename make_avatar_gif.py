import os
import subprocess
import tempfile
from PIL import Image, ImageDraw

# ---------------------------------------------
#             配置路径
# ---------------------------------------------
INPUT_JPG_FOLDER = "input_images"        # 原始 JPG 输入文件夹
FINAL_GIF_FOLDER = "final_gifs"          # 最终透明 GIF 输出文件夹
FFMPEG_PATH = "ffmpeg"
FPS = 25
DURATION = 1
ROTATE_SPEED = "t*2*PI"
# ---------------------------------------------


def ensure_folders():
    os.makedirs(FINAL_GIF_FOLDER, exist_ok=True)


# ---------------------------------------------
# 裁剪成圆形 PNG（保持在内存，不保存）
# ---------------------------------------------
def crop_jpg_to_circle_image(path):
    img = Image.open(path).convert("RGBA")

    w, h = img.size
    d = min(w, h)
    left = (w - d) // 2
    top = (h - d) // 2
    img = img.crop((left, top, left + d, top + d))

    mask = Image.new("L", (d, d), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, d, d), fill=255)

    result = Image.new("RGBA", (d, d))
    result.paste(img, (0, 0), mask)

    return result  # 内存中的 PNG


# ---------------------------------------------
# 使用 ffmpeg 旋转（输入 PNG 二进制 → 输出 GIF 二进制）
# ---------------------------------------------
def rotate_png_to_gif_bytes(png_image):
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_png:
        png_path = tmp_png.name
        png_image.save(png_path)

    with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as tmp_gif:
        gif_path = tmp_gif.name

    cmd = [
        FFMPEG_PATH,
        "-loop", "1",
        "-i", png_path,
        "-vf", f"rotate={ROTATE_SPEED}:fillcolor=none",
        "-t", str(DURATION),
        "-r", str(FPS),
        "-y",
        gif_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 读取 GIF 进内存
    with open(gif_path, "rb") as f:
        gif_bytes = f.read()

    # 清理临时文件
    os.remove(png_path)
    os.remove(gif_path)

    return gif_bytes


# ---------------------------------------------
# 去除黑背景（保持帧率）
# ---------------------------------------------
def remove_black_background_from_gif_bytes(gif_bytes, output_path):
    # 临时写入 GIF
    with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as tmp:
        in_path = tmp.name
        tmp.write(gif_bytes)

    # 打开 GIF
    img = Image.open(in_path)
    w, h = img.size

    # 创建圆形蒙版
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, w, h), fill=255)

    frames = []
    durations = []
    disposals = []

    for frame in range(img.n_frames):
        img.seek(frame)
        durations.append(img.info.get("duration", 50))
        disposals.append(getattr(img, "disposal_method", 2))

        rgba = img.convert("RGBA")
        new_frame = Image.new("RGBA", (w, h))
        new_frame.paste(rgba, (0, 0), mask)
        frames.append(new_frame)

    # 完成后关闭文件句柄
    img.close()

    # 保存新 GIF
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        loop=0,
        duration=durations,
        disposal=disposals,
        optimize=False,
    )

    # 必须在 img.close() 之后才能删除
    os.remove(in_path)



# ---------------------------------------------
# 主流程（无任何中间文件）
# ---------------------------------------------
if __name__ == "__main__":
    ensure_folders()

    for filename in os.listdir(INPUT_JPG_FOLDER):
        if filename.lower().endswith(".jpg"):
            print("处理中：", filename)

            # Step 1 内存裁圆
            circle_img = crop_jpg_to_circle_image(
                os.path.join(INPUT_JPG_FOLDER, filename)
            )

            # Step 2 内存调用 ffmpeg 旋转生成 GIF
            gif_bytes = rotate_png_to_gif_bytes(circle_img)

            # Step 3 去背景并保存最终 GIF
            out_gif_path = os.path.join(
                FINAL_GIF_FOLDER,
                filename.replace(".jpg", ".gif")
            )
            remove_black_background_from_gif_bytes(gif_bytes, out_gif_path)

            print("✅ 完成：", out_gif_path)

    print("\n🎉 全部完成！最终文件在：", FINAL_GIF_FOLDER)
