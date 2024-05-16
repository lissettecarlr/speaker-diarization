import ffmpeg
import os

def concat_video_audio(video_path,audio_path,output_video_path="./final_video.mp4"):
    """
    通过ffmpeg合并视频和音频
    """
    try:
        if not os.path.exists(video_path):
            raise "{} not find".format(video_path)
        if not os.path.exists(audio_path):
            raise "{} not find".format(audio_path)
        if  os.path.exists(output_video_path):
            os.remove(output_video_path)
        video_stream = ffmpeg.input(video_path)
        audio_stream = ffmpeg.input(audio_path)
        (
            ffmpeg
            #.output(video_stream, audio_stream, output_video_path, codec="copy", **{'c:a': 'aac'})
            .output(video_stream.video, audio_stream.audio, output_video_path, vcodec='copy', acodec='aac')
            .run()
        )
    except Exception as e:
        raise e
    
def separate_audio(video_path,output_audio_path="./output_separate_audio.wav",ac=2,ar="44000"):
    """
    从视频中分离音频
    """
    if not os.path.exists(video_path):
        raise "{} not find".format(video_path)
    if  os.path.exists(output_audio_path):
        os.remove(output_audio_path)

    audio_stream = ffmpeg.input(video_path)
    (
        ffmpeg
        .output(audio_stream,output_audio_path,acodec="pcm_s16le", ac=ac, ar=ar)
    )


def extract_audio(video_path, output_audio_path):
    """
    从视频文件中提取音频并保存为wav。
    参数:
    video_path (str): 视频文件的路径。
    output_audio_path (str): 输出音频文件的路径。
    """
    if not os.path.exists(video_path):
        raise "{} not find".format(video_path)
    if  os.path.exists(output_audio_path):
        os.remove(output_audio_path)
    try:
        (
            ffmpeg
            .input(video_path)
            .output(output_audio_path, acodec='mp3', audio_bitrate='320k')
            .run(overwrite_output=True)
        )
    except ffmpeg.Error as e:
        raise e

def extract_audio_from_folder(folder_path):
    """
    提取指定文件夹内所有视频文件的音频，并保存在同一文件夹中。
    参数:
    folder_path (str): 包含视频文件的文件夹路径。
    """
    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        video_path = os.path.join(folder_path, filename)
        # 检查文件是否是视频文件，这里假设视频文件有以下扩展名
        if video_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            # 构造输出音频文件的路径
            output_audio_path = os.path.splitext(video_path)[0] + '.mp3'
            try:
                # 调用之前定义的函数来提取音频
                extract_audio(video_path, output_audio_path)
                print(f"Extracted audio from {video_path} to {output_audio_path}")
            except Exception as e:
                print(f"Failed to extract audio from {video_path}: {e}")

def concat_videos(video_list_file_path,output_video_path):
    """
    视频合并
    """
    if not os.path.exists(video_list_file_path):
        raise "{} not find".format(video_list_file_path)
    if  os.path.exists(output_video_path):
        os.remove(output_video_path)    
    (
        ffmpeg
        .input(video_list_file_path,format='concat', safe=0)
        .output(output_video_path, c='copy')
        .run(overwrite_output=True)
    )


def clear_folder(folder_path):
    # 获取绝对路径
    abs_folder_path = os.path.abspath(folder_path)

    # 检查是否是根目录或其他关键系统目录
    forbidden_paths = [
        os.path.abspath('/'),         # 根目录
        os.path.abspath('/home'),     # 用户主目录（根据需要添加更多路径）
        os.path.abspath('/usr'),
        os.path.abspath('/bin'),
        os.path.abspath('/sbin'),
        os.path.abspath('/etc'),
        os.path.abspath('/var'),
        os.path.abspath('/lib'),
        os.path.abspath('/lib64'),
        os.path.abspath('/opt'),
        os.path.abspath('/root'),
        os.path.abspath('/tmp'),
        os.path.abspath('/boot'),
        os.path.abspath('/mnt'),
        os.path.abspath('/media'),
        os.path.abspath('/srv')
    ]

    if abs_folder_path in forbidden_paths:
        print("警告：禁止操作关键系统目录：{}".format(abs_folder_path))
        return

    # 确保路径存在且是一个目录
    if not os.path.exists(abs_folder_path) or not os.path.isdir(abs_folder_path):
        print("错误：路径不存在或不是一个目录：{}".format(abs_folder_path))
        return

    for filename in os.listdir(abs_folder_path):
        file_path = os.path.join(abs_folder_path, filename)
        if os.path.isdir(file_path):
            clear_folder(file_path)  # 递归删除子文件夹内容
            os.rmdir(file_path)      # 删除空文件夹
        else:
            os.remove(file_path)     # 删除文件

    print("清空文件夹：{}".format(abs_folder_path))



def image_to_video(image_path,duration,output_video_path):
    """
    通过图片生成视频
    """
    if not os.path.exists(image_path):
        raise "{} not find".format(image_path)    
    if  os.path.exists(output_video_path):
        os.remove(output_video_path)
    (
        ffmpeg
        .input(image_path, loop=1, t=duration, framerate=25) 
        .output(output_video_path, vcodec='libx264', pix_fmt='yuv420p')
        .run()
    )


def truncated_mean(data, trim_ratio):
    """
    计算截断平均值。
    :param data: 包含数据点的列表或数组。
    :param trim_ratio: 要从每端去除的数据的比例，例如0.1表示去除最高和最低的10%数据。
    :return: 截断平均值。
    """
    if trim_ratio < 0 or trim_ratio >= 0.5:
        raise ValueError("trim_ratio 必须在0到0.5之间（不包括0.5）")
    
    # 对数据进行排序
    sorted_data = sorted(data)
    # 计算要去除的数据点数量
    n = len(data)
    trim_count = int(n * trim_ratio)
    
    # 去除最高和最低的数据点
    trimmed_data = sorted_data[trim_count:n-trim_count]
    
    # 计算并返回截断平均值
    return sum(trimmed_data) / len(trimmed_data)


def add_suffix_to_filename(filepath, suffix):
    """
    给定一个文件路径和一个后缀，返回添加了后缀的新文件路径。
    
    参数:
    filepath (str): 原始文件路径。
    suffix (str): 要添加的后缀。
    
    返回:
    str: 添加了后缀的文件路径。
    """
    if suffix == "":
        return filepath
    # 分离文件的目录部分和文件名部分
    directory, filename = os.path.split(filepath)
    
    # 分离文件名和扩展名
    file_base, file_extension = os.path.splitext(filename)
    
    # 构造新的文件名
    new_filename = f"{file_base}_{suffix}{file_extension}"
    
    # 构造新的完整文件路径
    new_filepath = os.path.join(directory, new_filename)
    
    return new_filepath


def extract_audio_segment(input_audio_path, start_time, end_time, output_audio_path):
    """
    使用ffmpeg从源音频中提取特定时间段的音频。

    参数:
        input_audio_path (str): 源音频文件路径
        start_time (float): 开始时间（以秒为单位）
        end_time (float): 结束时间（以秒为单位）
        output_audio_path (str): 输出音频文件路径
    """
    (
        ffmpeg
        .input(input_audio_path, ss=start_time, to=end_time)
        .output(output_audio_path)
        .global_args('-loglevel', 'quiet')
        .run(overwrite_output=True)
    )

if __name__ == "__main__":
    #concat_videos("./temp/filelist.txt","./temp/1111.mp4")
    extract_audio_from_folder(r"C:\Users\lisse\Desktop\11")