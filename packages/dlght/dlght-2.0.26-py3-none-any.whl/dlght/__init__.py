
import fire
from .dgx import DGX
from .preset import PRESET  

class ENTRY(object):
    def x(self, url: str, output: str = None, resume: bool = True, unzip: bool = False, proxy: bool = False):
        """下载GitHub文件（支持断点续传和自动解压）
        
        Args:
            url: GitHub文件的URL地址
            output: 输出文件路径，默认为None时使用原文件名
            resume: 是否启用断点续传功能，默认为True
            unzip: 是否自动解压下载的文件，默认为False
            proxy: 是否使用代理进行下载，默认为False
        
        通过DGX下载器从GitHub下载文件，支持断点续传避免重复下载，
        可选择自动解压压缩文件，并支持代理访问。
        """
        DGX(url, output, resume, unzip, proxy)


    def preset(self):
        """下载预设的软件
        
        预设了一些软件可以进行非常方便的选择和下载
        """
        PRESET() 

    def from_file(self):
        """从文件批量导入下载任务
        
        从指定的配置文件中读取并执行批量下载任务。
        """
        print("不确定要不要开发这个功能 暂时用不上")
        pass


def main() -> None:
    try:
        fire.Fire(ENTRY)
    except KeyboardInterrupt:
        print("\n操作已取消")
        exit(0)
