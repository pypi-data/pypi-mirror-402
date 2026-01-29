import os


def segAudio(audio_file, split_seconds, out_dir, keep_dir=False):
    '''
    指定秒数，分割音频为多份文件
    '''
    # 加载音频文件
    from pydub import AudioSegment
    audio = AudioSegment.from_mp3(audio_file)

    # 获取音频的总时长（毫秒）
    duration = len(audio)

    # 计算需要切分的份数
    parts = int(duration // (split_seconds * 1000)) + 1

    flst = []

    # 循环切分音频，并保存为新的文件
    for i in range(parts):
        # 计算每一份的起始和结束时间（毫秒）
        start = i * split_seconds * 1000
        end = min((i + 1) * split_seconds * 1000, duration)

        # 切分音频，并保存为新的文件
        dir = ''
        if keep_dir:
            dir = out_dir.split('\\')[-1]
        fn = f"{out_dir}\\{dir}{i}.mp3"
        flst.append(fn)
        audio[start:end].export(fn, format="mp3")

    return flst


def cutAudio(src, dest, start, end):
    '''
    截取音频的一部分并根据目标文件的扩展名导出为相应格式
    '''
    from pydub import AudioSegment
    # 从源文件读取音频
    sound = AudioSegment.from_file(src)

    # 将开始和结束时间转换为毫秒
    start_time = int(start * 1000)  # 开始时间转换为毫秒
    end_time = int(end * 1000)  # 结束时间转换为毫秒

    # 截取音频片段
    new_file = sound[start_time:end_time]

    # 根据目标文件的扩展名确定格式
    _, ext = os.path.splitext(dest)
    format = ext[1:].lower()
    # 导出到目标文件，使用确定的格式
    new_file.export(dest, format=format)


def convertAudio(in_file, out_file):
    # 确认ffmpeg或libav已安装
    from pydub import AudioSegment
    # 读取输入文件
    sound = AudioSegment.from_file(in_file)

    # 根据输出文件的扩展名确定格式
    _, ext = os.path.splitext(out_file)
    format = ext[1:].lower()  # 移除点并转换为小写

    # 导出到指定格式的输出文件
    sound.export(out_file, format=format)


def speedAudio(src, dest, factor=1):
    import moviepy as mpy
    # 加载音频文件
    audio_clip = mpy.AudioFileClip(src)

    # 根据提供的因子调整音频速率
    modified_audio = audio_clip.fl_time(
        lambda t: factor * t, apply_to=['mask', 'audio'])

    modified_audio = modified_audio.set_duration(
        audio_clip.duration / factor)
    # 保存修改后的音频文件
    modified_audio.write_audiofile(dest, codec='libmp3lame')

    # 释放资源
    audio_clip.close()
    modified_audio.close()


def pitchAudio(src, dest, semitones=-5):
    import librosa
    import soundfile as sf

    # 加载源音频文件
    data, samplerate = librosa.load(src, sr=None)

    # 调整音调
    data_pitched = librosa.effects.pitch_shift(
        data, samplerate, n_steps=semitones)

    # 保存目标音频文件
    sf.write(dest, data_pitched, samplerate)


def denoiseAudio(src, dest):
    import noisereduce as nr
    import librosa
    import soundfile as sf
    # 加载音频文件
    y, sr = librosa.load(src, sr=None)

    # 进行去噪处理
    y_denoised = nr.reduce_noise(y=y, sr=sr, verbose=False)

    # 保存去噪后的音频文件
    sf.write(file=dest, data=y_denoised, samplerate=sr)


def getAudioDuration(audio_path):
    import moviepy as mpy
    clip = mpy.AudioFileClip(audio_path)
    len1 = clip.duration
    clip.close()
    return len1

