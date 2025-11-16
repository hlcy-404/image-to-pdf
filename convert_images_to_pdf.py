"""
图片转PDF脚本
将image目录下每个子目录的图片转换为单独的PDF文件
每页A4横向纸张，并排放置3张图片
"""

import os
from pathlib import Path
from PIL import Image
from typing import List
import re

# A4纸张尺寸（横向，单位：像素，按照72 DPI计算）
# A4横向：297mm x 210mm = 11.69" x 8.27" = 842 x 595 points (at 72 DPI)
A4_WIDTH = 842  # points
A4_HEIGHT = 595  # points

# 使用更高的DPI以获得更好的质量
DPI = 150
A4_WIDTH_PX = int(11.69 * DPI)  # 约1754 pixels at 150 DPI
A4_HEIGHT_PX = int(8.27 * DPI)   # 约1241 pixels at 150 DPI

IMAGES_PER_PAGE = 3  # 每页放置3张图片


def natural_sort_key(s):
    """自然排序的键函数，正确处理数字"""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', str(s))]


def get_image_files(directory: Path) -> List[Path]:
    """获取目录下所有图片文件，按自然顺序排序"""
    image_extensions = {'.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG'}
    image_files = [f for f in directory.iterdir() 
                   if f.is_file() and f.suffix in image_extensions]
    # 按文件名自然排序
    image_files.sort(key=lambda x: natural_sort_key(x.name))
    return image_files


def create_page_with_three_images(images: List[Image.Image], 
                                  page_width: int, 
                                  page_height: int) -> Image.Image:
    """
    创建一页，包含最多3张图片并排放置
    
    Args:
        images: 图片列表（1-3张）
        page_width: 页面宽度
        page_height: 页面高度
    
    Returns:
        合成后的页面图片
    """
    # 创建白色背景的页面
    page = Image.new('RGB', (page_width, page_height), 'white')
    
    # 计算每张图片的可用宽度（留一些边距）
    margin = int(page_width * 0.01)  # 1%边距
    total_margin = margin * (len(images) + 1)
    available_width_per_image = (page_width - total_margin) // len(images)
    
    # 计算垂直边距
    vertical_margin = int(page_height * 0.02)  # 2%边距
    available_height = page_height - 2 * vertical_margin
    
    x_offset = margin
    
    for img in images:
        # 计算缩放比例，保持宽高比
        width_ratio = available_width_per_image / img.width
        height_ratio = available_height / img.height
        scale_ratio = min(width_ratio, height_ratio)
        
        # 计算新尺寸
        new_width = int(img.width * scale_ratio)
        new_height = int(img.height * scale_ratio)
        
        # 调整图片大小
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 计算垂直居中位置
        y_offset = vertical_margin + (available_height - new_height) // 2
        
        # 粘贴图片到页面
        page.paste(resized_img, (x_offset, y_offset))
        
        # 更新水平位置
        x_offset += available_width_per_image + margin
    
    return page


def convert_folder_to_pdf(input_folder: Path, output_folder: Path):
    """
    将一个文件夹中的所有图片转换为一个PDF文件
    
    Args:
        input_folder: 输入图片文件夹
        output_folder: 输出PDF文件夹
    """
    print(f"\n处理文件夹: {input_folder.name}")
    
    # 获取所有图片文件
    image_files = get_image_files(input_folder)
    
    if not image_files:
        print(f"  警告: 文件夹 {input_folder.name} 中没有找到图片文件")
        return
    
    print(f"  找到 {len(image_files)} 张图片")
    
    # 创建输出文件夹
    output_folder.mkdir(parents=True, exist_ok=True)
    
    # 输出PDF文件名
    output_pdf = output_folder / f"{input_folder.name}.pdf"
    
    # 存储所有页面
    pages = []
    
    # 每3张图片创建一页
    total_pages = (len(image_files) + IMAGES_PER_PAGE - 1) // IMAGES_PER_PAGE
    print(f"  将生成 {total_pages} 页PDF")
    
    for i in range(0, len(image_files), IMAGES_PER_PAGE):
        page_num = i // IMAGES_PER_PAGE + 1
        print(f"  处理第 {page_num}/{total_pages} 页...", end='\r')
        
        # 获取当前页的图片（最多3张）
        current_batch = image_files[i:i + IMAGES_PER_PAGE]
        
        # 打开图片
        images = []
        for img_path in current_batch:
            try:
                img = Image.open(img_path)
                # 转换为RGB模式（确保兼容PDF）
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                images.append(img)
            except Exception as e:
                print(f"\n  警告: 无法打开图片 {img_path.name}: {e}")
                continue
        
        if not images:
            continue
        
        # 创建页面
        page = create_page_with_three_images(images, A4_WIDTH_PX, A4_HEIGHT_PX)
        pages.append(page)
        
        # 关闭打开的图片
        for img in images:
            img.close()
    
    print(f"\n  保存PDF文件: {output_pdf.name}")
    
    # 保存为PDF
    if pages:
        pages[0].save(
            output_pdf,
            save_all=True,
            append_images=pages[1:],
            resolution=DPI,
            quality=95
        )
        print(f"  ✓ 成功生成PDF: {output_pdf}")
        print(f"    - 总页数: {len(pages)}")
        print(f"    - 总图片数: {len(image_files)}")
    else:
        print(f"  错误: 没有有效的页面生成")


def main():
    """主函数"""
    print("=" * 60)
    print("图片转PDF工具")
    print("=" * 60)
    
    # 设置路径
    script_dir = Path(__file__).parent
    image_dir = script_dir / "image"
    output_dir = script_dir / "output"
    
    if not image_dir.exists():
        print(f"错误: 找不到image目录: {image_dir}")
        return
    
    # 获取所有子目录
    subdirs = [d for d in image_dir.iterdir() if d.is_dir()]
    
    if not subdirs:
        print(f"错误: image目录中没有找到子目录")
        return
    
    # 按名称排序子目录
    subdirs.sort(key=lambda x: natural_sort_key(x.name))
    
    print(f"\n找到 {len(subdirs)} 个子目录:")
    for subdir in subdirs:
        print(f"  - {subdir.name}")
    
    print(f"\nPDF配置:")
    print(f"  - 页面尺寸: A4 横向 ({A4_WIDTH_PX} x {A4_HEIGHT_PX} 像素)")
    print(f"  - DPI: {DPI}")
    print(f"  - 每页图片数: {IMAGES_PER_PAGE}")
    print(f"  - 输出目录: {output_dir}")
    
    # 处理每个子目录
    for subdir in subdirs:
        try:
            convert_folder_to_pdf(subdir, output_dir)
        except Exception as e:
            print(f"\n错误: 处理文件夹 {subdir.name} 时出错: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("处理完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

