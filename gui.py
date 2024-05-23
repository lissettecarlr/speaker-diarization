import streamlit as st
import os

from dotenv import load_dotenv
from client import sd_user_client,delete_short_audio_files


# 临时文件存放地址
TEMP = "./temp"

def web_page():
    st.title("角色音提取")
   
    if "temp_input_file" not in st.session_state:
        st.session_state['temp_input_file'] = None

    if "sd_client" not in st.session_state:
        st.session_state['sd_client'] = None
    if st.session_state.sd_client is None:
        st.session_state.sd_client = sd_user_client()

    if "output_audio_folder_path" not in st.session_state:
        st.session_state.output_audio_folder_path = None
    

    st.markdown("------")
    if st.button("清空缓存（该按钮将删除临时文件）"):
        from utils import clear_folder
        clear_folder(TEMP)

    input_file = st.file_uploader("上传媒体：", type=["mp4", "avi", "mkv","wav","mp3"])
    if input_file is not None:
        temp_input_file = os.path.join(
            TEMP,
            input_file.name
        )
        # 将上传的文件保存到临时文件夹中
        if not os.path.exists(temp_input_file):     
            with open(temp_input_file, "wb") as f:
                f.write(input_file.read())
        else:
            print("文件:{} 已存在，无需创建".format(temp_input_file))
        
        st.session_state.temp_input_file = temp_input_file


    if not st.checkbox('禁用时长过滤',True):
        filter = True
        duration_threshold = st.number_input("请输入删除音频文件的时长阈值（单位：秒）", min_value=0.0, value=1.0)
    else:
        filter = False
    
    st.markdown("------------")

    if st.button("开始提取"):
        if input_file is None:
            st.warning("请先上传媒体")
            st.stop()

        st.session_state.output_audio_folder_path = None
        print("开始提取")

        with st.spinner('提取中。。。'):
            output_audio_folder_path = st.session_state.sd_client.run(
                file_path = st.session_state.temp_input_file
            )

        with st.spinner('后续处理。。。'):
            for speaker_folder_name in os.listdir(output_audio_folder_path):
                speaker_folder = os.path.join(output_audio_folder_path,speaker_folder_name)
                if os.path.isdir(speaker_folder):
                    audio_files = [f for f in os.listdir(speaker_folder) if f.endswith(('.mp3', '.wav', '.ogg', '.flac'))]
                    if not audio_files:
                        st.warning("文件夹中没有找到音频文件")
                        return
                    
                    # 找到音频时长最长的，显示播放
                    longest_audio_path = None
                    longest_duration = 0

                    for audio_file in audio_files:
                        audio_path = os.path.join(speaker_folder, audio_file)
                        import torchaudio
                        waveform, sample_rate = torchaudio.load(audio_path)
                        duration = waveform.shape[1] / sample_rate
                        
                        if duration > longest_duration:
                            longest_duration = duration
                            longest_audio_path = audio_path
                        
                    if longest_audio_path:
                        st.write(f"角色: {speaker_folder_name}")
                        st.audio(longest_audio_path, format='audio/wav')

                    # 是否低音频进行过滤
                    if filter:
                        print("开始进行音频过滤: {}".format(output_audio_folder_path))
                        delete_short_audio_files(speaker_folder,duration_threshold)
            # 打包下载 output_audio_folder_path
        st.session_state.output_audio_folder_path = output_audio_folder_path
    
        st.info("提取完成")
     

    if st.session_state.output_audio_folder_path is not  None:
        if st.download_button(
            label="打包下载",
            data=zip_folder(st.session_state.output_audio_folder_path),
            file_name="output.zip",
            mime="application/zip"
        ):
            st.success("打包下载完成")  


import zipfile
import os
from io import BytesIO

def zip_folder(folder_path):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=folder_path)
                zip_file.write(file_path, arcname)
    zip_buffer.seek(0)
    return zip_buffer


if __name__ == "__main__":
    if not os.path.exists(TEMP):
        os.makedirs(TEMP)
    load_dotenv()
    web_page()