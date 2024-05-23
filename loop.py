# 该文件用于视频的批量提取
import os

from dotenv import load_dotenv
from client import sd_user_client,delete_short_audio_files
from utils import clear_folder
# 临时文件存放地址
TEMP = "./temp"

def loop(folder_path):
    sd_client = sd_user_client()
    video_extensions = ('.mp4', '.avi', '.mkv', '.mov', '.flv')
    # 遍历文件夹中的所有文件
    for root, dirs, files in os.walk(folder_path):
        
        for file in files:
            print("开始处理文件：{}".format(file))
            # 检查文件是否是视频文件
            if file.lower().endswith(video_extensions):
                video_path = os.path.join(root, file)
                print(video_path) 
                # 提取
                output_audio_folder_path = sd_client.run(
                    file_path = video_path
                )
                # 后续处理
                for speaker_folder_name in os.listdir(output_audio_folder_path):
                    speaker_folder = os.path.join(output_audio_folder_path,speaker_folder_name)
                    if os.path.isdir(speaker_folder):
                        # 移除时长小于1秒的音频
                        delete_short_audio_files(speaker_folder,1.0)

    print("结束")

if __name__ == "__main__":
    if not os.path.exists(TEMP):
        os.makedirs(TEMP)
    loop("./temp/input")   