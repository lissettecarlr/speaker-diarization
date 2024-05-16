import os
from dotenv import load_dotenv
import torch
import torchaudio
from utils import add_suffix_to_filename,extract_audio_segment,clear_folder

from logger import setup_logger
log_file = 'diarization.log' 
logger = setup_logger(log_file,"diarization")

TEMP = "./temp"

class Diarization:
    def __init__(self,mode="annote") -> None:
        load_dotenv()
        self.mode = mode
        if mode == "annote": 
            logger.info("Diarization Mode: Annote, init ....")
            from pyannote.audio import Pipeline
            self.pipeline  = Pipeline.from_pretrained(
                            "pyannote/speaker-diarization-3.1",
                            use_auth_token=os.getenv("hf_token"))
            
            # onset=0.6: mark region as active when probability goes above 0.6
            # offset=0.4: switch back to inactive when probability goes below 0.4
            # min_duration_on=0.0: 删除活动区域的时间短于秒数
            # min_duration_off=0.0: 填充非活动区域的时间短于秒数
            
            # https://huggingface.co/pyannote/segmentation#reproducible-research

            
            #self.pipeline.segmentation.onset = 	float(os.getenv("segmentation_onset"))
            #self.pipeline.segmentation.offset = float(os.getenv("segmentation_offset"))
            # 这个参数设置了活动区域的最小持续时间。
            # 增加这个值可以过滤掉那些持续时间非常短的活动片段，从而减少分割片段的数量。
            #self.pipeline.segmentation.min_duration_on = float(os.getenv("segmentation_min_duration_on"))
            # 这个参数设置了非活动区域的最小持续时间。
            # 增加这个值可以填充一些较短的非活动区域，从而合并一些相邻的活动片段，减少分割片段的数量。
            #self.pipeline.segmentation.min_duration_off = float(os.getenv("segmentation_min_duration_off"))

            self.pipeline.to(torch.device("cuda"))

        # elif mode == "ali":
        #     #pip install modelscope
        #     from modelscope.pipelines import pipeline
        #     self.pipeline = pipeline(
        #         task='speaker-diarization',
        #         model='damo/speech_campplus_speaker-diarization_common',
        #         model_revision='v1.0.0'
        #     )

    def infer(self,audio_path,rate_change=True):
        logger.info("start diarization")
        if rate_change :
            audio_path = change_sample_rate(audio_path,output_folder_path=TEMP)
            logger.debug(f"change sample rate output_path:{audio_path}")

        if self.mode == "annote":
            # 加载音频文件的波形和采样率
            waveform, sample_rate = torchaudio.load(audio_path)
            # 推理并监控进度
            from pyannote.audio.pipelines.utils.hook import ProgressHook
            with ProgressHook() as hook:
                # diarization = pipeline("audio.wav", min_speakers=2, max_speakers=5)
                diarization = self.pipeline({"waveform": waveform, "sample_rate": sample_rate})

        elif self.mode == "ali":
            diarization = self.pipeline(audio_path)

        logger.info("Diarization finished")
        return diarization
    
    def audio_slice_save(self,diarization,origin_audio_path,output_folder_path="./temp/output"):
        """
        分割音频，将音频按照说话人进行保存
        diarization : infer分割结果
        origin_audio_path : 原始音频路径
        output_folder_path : 输出文件夹
        """
        # 判断该文件夹是否存在
        if not os.path.exists(output_folder_path):
            os.makedirs(output_folder_path)

        filename_with_extension = os.path.basename(origin_audio_path)
        filename_without_extension = os.path.splitext(filename_with_extension)[0]
        output_folder_path =  os.path.join(output_folder_path, filename_without_extension)

        if not os.path.exists(output_folder_path):
            os.makedirs(output_folder_path)

        clear_folder(output_folder_path)


        for turn, _, speaker in diarization.itertracks(yield_label=True):
            start_time = turn.start
            end_time = turn.end
                    
            speaker_folder = os.path.join(output_folder_path, speaker)
            if not os.path.exists(speaker_folder):
                os.makedirs(speaker_folder)
            
            segment_filename = f"{speaker}_{int(start_time*1000)}_{int(end_time*1000)}.wav"
            segment_path = os.path.join(speaker_folder, segment_filename)
            from utils import extract_audio_segment
            extract_audio_segment(origin_audio_path, start_time, end_time, segment_path)

        result_file = os.path.join(output_folder_path, "result.rttm")
        with open(result_file, "w") as rttm:
            diarization.write_rttm(rttm)    

        return output_folder_path  

def change_sample_rate(audio_path,new_sample_rate=16000,output_folder_path="./temp/output"):
    """
    修改采样率
    audio_path:音频路径
    new_sample_rate:新采样率
    output_folder_path:输出文件夹，新音频命名为 ：原文件名_新波特率.wav
    """
    import torchaudio
    import torchaudio.transforms as T

    waveform, sample_rate = torchaudio.load(audio_path)
    if sample_rate == new_sample_rate:
        return audio_path

    filename_with_extension = os.path.basename(audio_path)
    filename_without_extension = os.path.splitext(filename_with_extension)[0]
    output_audio = os.path.join(output_folder_path,filename_without_extension + "_" + str(new_sample_rate) + ".wav")

    # 创建重采样器
    resampler = T.Resample(orig_freq=sample_rate, new_freq=new_sample_rate)

    # 重采样
    waveform_resampled = resampler(waveform)

    # 保存修改后的音频文件
    torchaudio.save(output_audio, waveform_resampled, new_sample_rate)

    #print(f"Sample rate changed from {sample_rate} Hz to {new_sample_rate} Hz")
    return output_audio

def delete_short_audio_files(directory, duration_threshold=1.0):
    """
    遍历指定文件夹中的所有音频文件，并删除时长小于指定阈值的音频文件。
    参数：
    directory (str): 要遍历的文件夹路径。
    duration_threshold (float): 删除音频文件的时长阈值（单位：秒），默认值为1.0秒。
    """
    # 遍历指定文件夹中的所有文件
    logger.info("开始过滤：{}".format(directory))
    for filename in os.listdir(directory):
        # 构建文件的完整路径
        file_path = os.path.join(directory, filename)
        
        # 检查文件是否为音频文件（这里假设音频文件的扩展名为常见的几种）
        if file_path.endswith(('.mp3', '.wav', '.flac', '.ogg', '.m4a')):
            try:
                # 加载音频文件
                waveform, sample_rate = torchaudio.load(file_path)
                # 计算音频文件的时长（单位为秒）
                duration = waveform.shape[1] / sample_rate
                # 如果音频时长小于指定阈值，则删除该文件
                if duration < duration_threshold:
                    os.remove(file_path)
                    logger.debug(f"Deleted: {file_path} (Duration: {duration:.2f} seconds)")
            except Exception as e:
                logger.warning(f"Error processing {file_path}: {e}")


if __name__ == "__main__":
    
    test = Diarization(mode="annote")
    test_audio = "./temp/2speakers_example_(Vocals)_UVR_MDXNET_Main_(No Echo)_UVR-De-Echo-Aggressive.wav"
    #test_audio = "./temp/2speakers_16K.wav"
    #change_sample_rate(test_audio)

    diarization = test.infer(test_audio)
    # test.audio_slice_save(diarization,test_audio)
    