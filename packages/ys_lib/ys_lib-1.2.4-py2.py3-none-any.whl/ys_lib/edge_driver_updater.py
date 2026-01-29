# -*- coding: utf-8 -*-
import io
import lxml.etree
import os
import requests
import shutil
import win32api
import zipfile
from loguru import logger


class EdgeDriverUpdater:
    url: str = "https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/"

    def __init__(self, dst_path: str = None):
        self.dst_path: str = dst_path or os.path.join(
            os.getenv("windir"), "msedgedriver.exe"
        )

    @property
    def dst_path_tmp(self) -> str:
        return self.dst_path + ".tmp"

    @classmethod
    def get_file_version(cls, file_path: str):
        """读取 指定文件 的产品版本"""
        try:
            # 获取文件的版本信息字典
            version_info = win32api.GetFileVersionInfo(file_path, "\\")

            # 提取版本号的两个关键整数（存储版本号的四个部分）
            version_ms = version_info.get("FileVersionMS", 0)
            version_ls = version_info.get("FileVersionLS", 0)

            # 分解为 [主版本, 次版本, 构建号, 修订号]
            major = win32api.HIWORD(version_ms)  # 高16位（主版本）
            minor = win32api.LOWORD(version_ms)  # 低16位（次版本）
            build = win32api.HIWORD(version_ls)  # 高16位（构建号）
            revision = win32api.LOWORD(version_ls)  # 低16位（修订号）

            return f"{major}.{minor}.{build}.{revision}"

        except Exception as e:
            logger.error(f"读取版本信息失败: {e}")
            return ""

    @property
    def current_version(self) -> str:
        """获取当前EdgeDriver的版本"""
        if os.path.exists(self.dst_path):
            current_version: str = self.get_file_version(self.dst_path)
            logger.debug(f"[msedgedriver]current_version: {current_version}")
            return current_version
        else:
            return ""

    def update(self) -> bool:
        """将本地EdgeDriver更新至最新稳定版"""
        try:
            r = requests.get(self.url)
            r.raise_for_status()
            e = lxml.etree.HTML(r.text)
            latest_version: str = "".join(
                e.xpath(
                    '//*[text()="Stable Channel"]/../../../..//strong[text()="Version"]/../text()'
                )
            ).strip()
            logger.debug(f"[msedgedriver]latest_version: {latest_version}")

            current_version: str = self.current_version
            if latest_version != current_version:
                hrefs = e.xpath('//*[text()="Stable Channel"]/../../../..//a/@href')
                for href in hrefs:
                    if href.endswith("_win64.zip"):
                        # href = 'https://msedgedriver.microsoft.com/143.0.3650.139/edgedriver_win64.zip'
                        r = requests.get(href)
                        r.raise_for_status()
                        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
                            with (
                                zf.open(os.path.basename(self.dst_path)) as z,
                                open(self.dst_path_tmp, "wb") as f,
                            ):
                                while b := z.read(8192):
                                    f.write(b)
                        version_tmp: str = self.get_file_version(self.dst_path_tmp)
                        assert version_tmp == latest_version
                        shutil.move(self.dst_path_tmp, self.dst_path)
                        logger.warning(
                            f"[msedgedriver]update_version: {current_version} -> {latest_version}"
                        )
                        break
        except Exception as e:
            logger.exception(e)
            return False
        return True


if __name__ == "__main__":
    EdgeDriverUpdater().update()
