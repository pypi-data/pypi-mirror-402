from __future__ import annotations

import gzip
import os
import shutil
import tarfile
import zipfile
from collections.abc import Callable

# 尝试导入py7zr，如果没有安装则使用try-except
PY7ZR_AVAILABLE = False
try:
    import py7zr
    PY7ZR_AVAILABLE = True
except ImportError:
    pass


class CompressUtils:
    """压缩工具类，提供统一的压缩和解压缩接口"""

    # 支持的压缩格式
    SUPPORTED_FORMATS = ["gzip", "zip", "tar", "tar.gz", "7z"]

    @staticmethod
    def _validate_format(format: str) -> None:
        """验证压缩格式是否支持

        Args:
            format: 压缩格式

        Raises:
            ValueError: 如果格式不支持
        """
        if format not in CompressUtils.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {format}. Supported formats: {', '.join(CompressUtils.SUPPORTED_FORMATS)}")

    @staticmethod
    def _get_files(src_path: str) -> list[str]:
        """获取路径下的所有文件

        Args:
            src_path: 源路径

        Returns:
            文件列表
        """
        files = []
        if os.path.isfile(src_path):
            files.append(src_path)
        elif os.path.isdir(src_path):
            for root, _, filenames in os.walk(src_path):
                for filename in filenames:
                    files.append(os.path.join(root, filename))
        return files

    @staticmethod
    def compress(src_path: str, dst_path: str, format: str, callback: Callable[[int, int], None] = None) -> bool:
        """压缩文件或目录

        Args:
            src_path: 源路径（文件或目录）
            dst_path: 目标压缩文件路径
            format: 压缩格式，支持 gzip, zip, tar, tar.gz, 7z
            callback: 进度回调函数，参数为当前进度和总进度

        Returns:
            是否压缩成功
        """
        CompressUtils._validate_format(format)

        try:
            # 获取所有要压缩的文件
            all_files = CompressUtils._get_files(src_path)
            total_files = len(all_files)
            processed_files = 0

            if format == "gzip":
                # Gzip只支持单个文件
                if len(all_files) != 1:
                    raise ValueError("gzip format only supports single file")

                with open(all_files[0], "rb") as f_in:
                    with gzip.open(dst_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                        processed_files = 1
                        if callback:
                            callback(processed_files, total_files)

            elif format == "zip":
                # Zip支持文件和目录
                with zipfile.ZipFile(dst_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in all_files:
                        # 计算相对路径
                        if os.path.isdir(src_path):
                            arcname = os.path.relpath(file_path, os.path.dirname(src_path))
                        else:
                            arcname = os.path.basename(file_path)

                        zipf.write(file_path, arcname)
                        processed_files += 1
                        if callback:
                            callback(processed_files, total_files)

            elif format in ["tar", "tar.gz"]:
                # Tar和Tar.gz格式
                mode = "w" if format == "tar" else "w:gz"
                with tarfile.open(dst_path, mode) as tarf:
                    tarf.add(src_path, arcname=os.path.basename(src_path))
                    processed_files = total_files
                    if callback:
                        callback(processed_files, total_files)

            elif format == "7z":
                # 7z格式
                if not PY7ZR_AVAILABLE:
                    raise ImportError("py7zr is not installed. Please install it with: pip install py7zr")

                with py7zr.SevenZipFile(dst_path, "w") as z:
                    for file_path in all_files:
                        # 计算相对路径
                        if os.path.isdir(src_path):
                            arcname = os.path.relpath(file_path, os.path.dirname(src_path))
                        else:
                            arcname = os.path.basename(file_path)

                        z.write(file_path, arcname)
                        processed_files += 1
                        if callback:
                            callback(processed_files, total_files)

            return True
        except Exception:
            return False

    @staticmethod
    def decompress(src_path: str, dst_path: str, callback: Callable[[int, int], None] = None) -> bool:
        """解压缩文件

        Args:
            src_path: 源压缩文件路径
            dst_path: 目标目录路径
            callback: 进度回调函数，参数为当前进度和总进度

        Returns:
            是否解压缩成功
        """
        try:
            # 确保目标目录存在
            os.makedirs(dst_path, exist_ok=True)

            # 根据文件扩展名判断格式
            ext = os.path.splitext(src_path)[1].lower()
            processed_files = 0
            total_files = 0

            if ext == ".gz":
                # Gzip格式
                dst_file = os.path.join(dst_path, os.path.basename(src_path).replace(".gz", ""))
                with gzip.open(src_path, "rb") as f_in:
                    with open(dst_file, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                processed_files = 1
                total_files = 1

            elif ext == ".zip":
                # Zip格式
                with zipfile.ZipFile(src_path, "r") as zipf:
                    total_files = len(zipf.infolist())
                    for member in zipf.infolist():
                        zipf.extract(member, dst_path)
                        processed_files += 1
                        if callback:
                            callback(processed_files, total_files)

            elif ext == ".tar":
                # Tar格式
                with tarfile.open(src_path, "r") as tarf:
                    total_files = len(tarf.getmembers())
                    for member in tarf.getmembers():
                        tarf.extract(member, dst_path)
                        processed_files += 1
                        if callback:
                            callback(processed_files, total_files)

            elif ext == ".7z":
                # 7z格式
                if not PY7ZR_AVAILABLE:
                    raise ImportError("py7zr is not installed. Please install it with: pip install py7zr")

                with py7zr.SevenZipFile(src_path, "r") as z:
                    total_files = len(z.files)
                    for i, _ in enumerate(z.files):
                        z.extract(dst_path)
                        processed_files = i + 1
                        if callback:
                            callback(processed_files, total_files)

            elif src_path.endswith(".tar.gz"):
                # Tar.gz格式
                with tarfile.open(src_path, "r:gz") as tarf:
                    total_files = len(tarf.getmembers())
                    for member in tarf.getmembers():
                        tarf.extract(member, dst_path)
                        processed_files += 1
                        if callback:
                            callback(processed_files, total_files)

            else:
                raise ValueError(f"Unsupported file format: {ext}")

            return True
        except Exception:
            return False

    @staticmethod
    def compress_stream(input_stream, output_stream, format: str) -> None:
        """流式压缩

        Args:
            input_stream: 输入流
            output_stream: 输出流
            format: 压缩格式，只支持 gzip
        """
        if format != "gzip":
            raise ValueError("Stream compression only supports gzip format")

        with gzip.GzipFile(fileobj=output_stream, mode="wb") as gz_stream:
            shutil.copyfileobj(input_stream, gz_stream)

    @staticmethod
    def decompress_stream(input_stream, output_stream, format: str) -> None:
        """流式解压缩

        Args:
            input_stream: 输入流
            output_stream: 输出流
            format: 压缩格式，只支持 gzip
        """
        if format != "gzip":
            raise ValueError("Stream decompression only supports gzip format")

        with gzip.GzipFile(fileobj=input_stream, mode="rb") as gz_stream:
            shutil.copyfileobj(gz_stream, output_stream)
