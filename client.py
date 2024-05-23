import os
from pathlib import Path
from dotenv import load_dotenv
import shutil
import requests
from urllib.parse import urlparse
from utils import add_suffix_to_filename,extract_audio_segment,clear_folder

from diarization import Diarization
from audio_separator.separator import Separator

TEMP = "./temp"
INPUT_FILE_TAG = ""

from logger import setup_logger
log_file = 'client.log' 
logger = setup_logger(log_file,"client")


class sd_user_client:
    def __init__(self):
        load_dotenv()

        temp_folder_path = Path(TEMP)
        if not temp_folder_path.exists():
            temp_folder_path.mkdir(parents=True, exist_ok=True)

        # 视频清洁
        self.separator = Separator(model_file_dir = os.getenv("weight_uvr5_root"),
                                   output_dir = TEMP,
                                   output_single_stem = "vocals")
        self.separator.load_model(model_filename = os.getenv("uvr5_model_filename"))

        # 分割
        self.diarization = Diarization()
        

    def get_file(self,file_path:str):
        """
        根据提供的文件路径或URL，获取文件并将其保存到临时目录中。
        
        参数:
        - file_path: 字符串，文件的路径或URL。
        
        返回值:
        - 如果成功复制或下载文件并保存到临时目录，返回新文件的路径；
        - 如果发生异常，抛出相应的异常。
        """
        # 解析输入路径或URL
        parsed_url = urlparse(file_path)
        if parsed_url.scheme in ('http', 'https'):
            logger.info("开始下载: {}".format(file_path))
            response = requests.get(file_path, stream=True)
            if response.status_code == 200:
                # 获取文件名并创建新的文件路径
                filename = os.path.basename(parsed_url.path)
                #filename = INPUT_FILE_TAG  +  "_" + filename
                new_file_path = os.path.join(TEMP, filename)
                new_file_path = add_suffix_to_filename(new_file_path,INPUT_FILE_TAG)
                # 下载并保存文件
                try:
                    with open(new_file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    logger.info(f"下载成功")
                    return new_file_path
                    
                except Exception as e:
                    logger.warning(f"下载失败: {e}")
                    raise Exception(f"下载失败: {e}")
            else:
                error_msg = f"链接请求失败: 状态码 {response.status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)
        else:
            
            # 本地文件情况
            logger.info("获取本地文件：{}".format(file_path))
            file_path = Path(file_path)
            if file_path.exists() and file_path.is_file():
                # 获取文件名并创建新的文件路径
                filename = file_path.name
                new_file_path = os.path.join(TEMP, filename)
                new_file_path = add_suffix_to_filename(new_file_path,INPUT_FILE_TAG)

                if os.path.abspath(file_path) == os.path.abspath(new_file_path):
                    logger.info("文件路径相同，跳过复制")
                    return new_file_path
                try:
                    shutil.copy(file_path, new_file_path)
                    logger.info(f"文件复制成功")
                    return new_file_path
                except Exception as e:
                    logger.warning(f"文件复制失败: {e}")
                    raise Exception(f"文件复制失败: {e}")
            else:
                error_msg = "文件复制失败：文件不存在"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
    def run(self,file_path,output_folder_path="./temp/output",uvr_switch=True):

        # 如果传入的是文件夹
        # if Path(file_path).is_dir():
        #     folder_path = Path(output_folder_path)
        #     if not folder_path.exists():
        #         folder_path.mkdir(parents=True, exist_ok=True)

        temp_file_path = self.get_file(file_path)

        infer_input_audio_path = ""
        # 第一步：得到音频
        if temp_file_path.endswith((".mp4", ".avi",".mkv")):
            logger.info(f"视频文件提取音轨")
            try:
                temp_audio_path = os.path.splitext(temp_file_path)[0] + ".wav"
                from utils import extract_audio
                extract_audio(temp_file_path, temp_audio_path)
            except Exception as e:
                logger.warning(f"提取音轨失败: {e}")
                raise Exception(f"提取音轨失败: {e}")

        elif temp_file_path.endswith((".wav", ".mp3")):
            temp_audio_path = temp_file_path
        else:
            raise ValueError("不支持的文件类型")
        
        infer_input_audio_path = temp_audio_path
        logger.info("开始处理: {}".format(infer_input_audio_path))
        

        # 第二步：音频清洁
        if uvr_switch:
            logger.info("UVR 音频清洁开始")
            try:
                temp_separator_audio_path = self.separator.separate(temp_audio_path)
                logger.info("UVR 音频清洁结束：{}".format(temp_separator_audio_path))
            except Exception as e:
                logger.warning(f"UVR 音频清洁失败: {e}")
                raise Exception(f"UVR 音频清洁失败: {e}")
            
            infer_input_audio_path = os.path.join(TEMP,temp_separator_audio_path[0]) 

 
        # 第三步：分离音频
        logger.info("分离音频中...")
        dia_result= self.diarization.infer(infer_input_audio_path)
        output_audio_folder_path = self.diarization.audio_slice_save(dia_result,
                                          infer_input_audio_path,
                                          output_folder_path=output_folder_path)
        logger.info("分离音频完成:{}".format(output_audio_folder_path))
        return output_audio_folder_path



import argparse
from diarization import delete_short_audio_files

if __name__ == "__main__":

    client = sd_user_client()
    parser = argparse.ArgumentParser(description="角色音提取工具")

    # 添加子命令解析器
    subparsers = parser.add_subparsers(dest='command', help='子命令帮助')

    # 定义第一个子命令: run
    parser_run = subparsers.add_parser('run', help='运行变声工具')
    parser_run.add_argument("--input", "-i", help="输入音频或者视频，可以是url或者本地文件", type=str, required=True)
    parser_run.add_argument("--output", "-o", help="输出文件路径", type=str, required=False, default="./temp/output")

    # 定义第二个子命令: delete
    parser_delete = subparsers.add_parser('filter', help='删除短音频文件')
    parser_delete.add_argument("--directory", "-d", help="音频文件所在目录", type=str, required=True)
    parser_delete.add_argument("--threshold", "-t", help="音频时长阈值(秒)", type=float, required=True,default=1.0)

    args = parser.parse_args()

    if args.command == 'run':
        client.run(file_path=args.input, output_folder_path=args.output)
    elif args.command == 'filter':
        delete_short_audio_files(directory=args.directory, duration_threshold=args.threshold)
    else:
        parser.print_help()

