import os
import random

import numpy as np
import mxupy as mu


def removeGreenBG(file):
    '''
    移除绿幕。
    依赖 scikit-image 包
    '''
    import skimage.exposure
    import moviepy as mpe
    import cv2

    video_clip = mpe.VideoFileClip(file)
    # frame = video_clip.get_frame(0)
    # print(frame.shape)

    processed_frames = []
    for frame in video_clip.iter_frames():

        # convert to LAB
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)

        # extract A channel
        # A-channel: represents the amount of red/green color
        A = lab[:, :, 1]

        # threshold A channel
        thresh = cv2.threshold(
            A, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

        # blur threshold image
        blur = cv2.GaussianBlur(thresh, (0, 0), sigmaX=5,
                                sigmaY=5, borderType=cv2.BORDER_DEFAULT)

        # stretch so that 255 -> 255 and 127.5 -> 0
        mask = skimage.exposure.rescale_intensity(blur, in_range=(
            127.5, 255), out_range=(0, 255)).astype(np.uint8)

        # cv2.imwrite(r"E:\BaiduSyncdisk\AIShellData\retalking\composite\1e0f0ded457842ceb8c14a8c7acfdf5c_nogreen_old.png", frame)

        # add mask to image as alpha channel
        result = frame.copy()
        result = cv2.cvtColor(result, cv2.COLOR_BGR2BGRA)
        result[:, :, 3] = mask
        # result = cv2.cvtColor(result, cv2.COLOR_BGRA2RGBA)

        # cv2.imwrite(r"E:\BaiduSyncdisk\AIShellData\retalking\composite\1e0f0ded457842ceb8c14a8c7acfdf5c_nogreen.png", result)
        # cv2.imwrite(r"E:\BaiduSyncdisk\AIShellData\retalking\composite\1e0f0ded457842ceb8c14a8c7acfdf5c_nogreen_mask.png", mask)

        processed_frames.append(result)

        # break

    processed_video_clip = mpe.ImageSequenceClip(
        processed_frames, fps=video_clip.fps)

    video_clip.close()

    # processed_video_clip.write_videofile(r"E:\BaiduSyncdisk\AIShellData\retalking\composite\1e0f0ded457842ceb8c14a8c7acfdf5c_nogreen.mp4", fps=video_clip.fps)

    return processed_video_clip

def overlayVideoWithRemoveGreenBG(width, height, mainvideo, overlays, output):
    '''
        将mainvideo移除绿幕，与overlays进行叠加在一起。
        视频和叠加物都是一个对象，包含 url/width/height/x/y/z，z越大越在前。
        最终fps与mainvideo一致。
    '''
    from moviepy import VideoFileClip
    import moviepy as mpe
    
    if isinstance(mainvideo,dict):
        mainvideo=mu.dict2Object(mainvideo)

    mainvideo_clip = VideoFileClip(mainvideo.url)
    mainvideo_audio_clip = mainvideo_clip.audio
    print('remove green background...')
    mv = removeGreenBG(mainvideo.url)

    # frame = mv.get_frame(0)
    # print(frame.shape)

    blank = mpe.ColorClip((width, height), color=(
        255, 255, 255, 255)).set_duration(mv.duration)

    clips = [{
        "z": -1,
        "clip": blank
    }]

    clips.append({
        "z": mainvideo.z,
        "clip": mv
    })

    # 遍历背景图或贴纸图的文件名和参数
    for item in overlays:
        if isinstance(item,dict):
            item=mu.dict2Object(item)
        
        # 如果是图片文件，则创建一个ImageClip对象
        # TODO:还需支持gif格式（未来）
        if item.url.endswith(".png") or item.url.endswith(".jpg"):
            clip = mpe.ImageClip(item.url)
        # 如果是视频文件，则创建一个VideoFileClip对象
        elif item.url.endswith(".mp4"):
            clip = mpe.VideoFileClip(item.url)
        # 否则，抛出异常
        else:
            raise ValueError(f"Invalid file format: {item.url}")

        # 将剪辑对象调整到指定的大小和持续时间，并设置到指定的位置和层级
        clip = clip.resize((item.width, item.height)).set_duration(
            mv.duration).set_position((item.x, item.y))

        # frame = clip.get_frame(0)
        # print(frame.shape)

        # 将剪辑对象添加到列表中
        clips.append({
            "z": item.z,
            "clip": clip
        })

    clips.sort(key=lambda x: x["z"])
    clips2 = [item["clip"] for item in clips]
    composite = mpe.CompositeVideoClip(clips2)
    print('overlay videos...')
    composite.set_audio(mainvideo_audio_clip).write_videofile(
        output, fps=mv.fps)
    composite.close()
    mainvideo_clip.close()

def concatVideoWithReverse(input_video_path, output_video_path):
    """ 反向视频拼接
    正向视频和反向视频拼接在一起，形成一个新的视频。
    注意：
        1. 正向视频和反向视频的分辨率必须相同。
        2. 正向视频和反向视频的帧率必须相同。
        3. 正向视频和反向视频的音频必须相同。

    Args:
        input_video_path (str): 输入视频
        output_video_path (str): 输出视频
    """
    from moviepy import VideoFileClip, concatenate_videoclips
    from moviepy import vfx, afx
    # 加载视频
    video_clip = VideoFileClip(input_video_path)

    # 获取视频时长
    # duration = video_clip.duration

    # 正向视频剪辑
    forward_clip = video_clip.copy()

    # 反向视频剪辑
    reversed_clip = video_clip.with_effects([vfx.TimeMirror()])

    # 拼接正向和反向视频
    final_clip = concatenate_videoclips([forward_clip, reversed_clip])
    final_clip = final_clip.without_audio()

    # 设置最终视频的时长为原始视频时长的两倍
    # final_clip = final_clip.with_duration(duration * 2)

    # 导出视频
    final_clip.write_videofile(output_video_path)
    final_clip.close()

def segVideo(video_file, split_seconds, out_dir, keep_dir=False):
    '''
    指定秒数，分割视频为多份文件
    '''
    from moviepy import VideoFileClip
    # 加载视频文件
    video = VideoFileClip(video_file)

    # 获取视频的总时长（秒）
    duration = video.duration

    # 计算需要切分的份数
    parts = int(duration // split_seconds) + 1

    flst = []
    # 循环切分视频和音频
    for i in range(parts):
        # 计算每一份的起始和结束时间（秒）
        start = i * split_seconds
        end = min((i + 1) * split_seconds, duration)

        # 切分视频和音频，并保存为新的文件
        dir = ''
        if keep_dir:
            dir = out_dir.split('\\')[-1]
        fn = f"{out_dir}\\{dir}{i}.mp4"
        flst.append(fn)
        video.subclip(start, end).write_videofile(fn)

    video.close()
    return flst

def cutVideo(src, dest, start, end):
    '''
    裁剪视频
    start：开始秒数
    end：结束秒数
    '''

    import cv2
    vidcap = cv2.VideoCapture(src)
    fps = vidcap.get(cv2.CAP_PROP_FPS)
    start_frame = start * fps  # start from the frame at the time of (4,30)
    end_frame = end * fps  # end at the frame at the time of (5,15)

    # set the starting position
    vidcap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    success, image = vidcap.read()

    fourcc = cv2.VideoWriter_fourcc(*'MP4V')  # define the codec
    # create the output video
    video_out = cv2.VideoWriter(dest, fourcc, fps, image.shape[:2][::-1])

    count = start_frame
    while success and count < end_frame:
        video_out.write(image)  # write the frame
        success, image = vidcap.read()  # read the next frame
        count += 1

    video_out.release()  # release the output video
    vidcap.release()  # release the input video

def resizeVideo(video_file, width, height, out_file):
    import cv2

    # 视频文件路径
    video_path = video_file
    # 输出视频文件路径
    output_path = out_file

    # 打开视频文件
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"Error: Could not open video {video_file}")
        return

    # 定义编解码器和创建VideoWriter对象
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = cap.get(cv2.CAP_PROP_FPS)
    out = cv2.VideoWriter(output_path, fourcc, fps, (int(width), int(height)))

    # 读取并处理视频帧
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 调整帧大小
        resized_frame = cv2.resize(
            frame, (int(width), int(height)), interpolation=cv2.INTER_AREA)

        # 写入新的帧到输出视频
        out.write(resized_frame)

    # 释放资源
    cap.release()
    out.release()

def captureVideoFrame(video_path, output_path, frame_number):
    '''
    截取视频文件某一帧的画面
    frame_number 可以是具体的帧数（注意从0开始到总帧数-1），也可以是：
    -1 最后一帧
    0 第一帧
    0.5 中间帧，在(0.0,1.0)中间都表示为百分比
    '''
    import cv2
    try:
        cap = cv2.VideoCapture(video_path)

        # 获取视频的总帧数
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)

        if frame_number == -1:
            frame_number = frame_count - 1

        elif frame_number < 0:
            frame_number = 0

        elif frame_number >= frame_count:
            frame_number = frame_count - 1

        elif isinstance(frame_number, float) and frame_number > 0.0 and frame_number < 1.0:
            frame_number = int(frame_number * frame_count)

        # 设置读取的帧位置
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

        # 读取指定帧
        ret, frame = cap.read()

        # 保存帧为图像文件
        if ret:
            cv2.imwrite(output_path, frame)
            print(f"Frame {frame_number} saved as {output_path}")
        else:
            print(f"Failed to capture frame {frame_number}")
            return False

        cap.release()
        return True

    except Exception as e:
        print(f"Error capturing frame: {e}")
        return False

def getVideoSize(video_path):
    '''
    获取视频文件宽高
    '''
    import cv2
    try:
        cap = cv2.VideoCapture(video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        return width, height
    except Exception as e:
        print(f"Error opening video: {e}")
        return 0, 0

def getVideoDuration(video_path):
    from moviepy import VideoFileClip
    clip = VideoFileClip(video_path)
    len1 = clip.duration
    clip.close()
    return len1

def extractAudio(video_file, output_audio_file):
    '''
    从视频中取出音频部分
    '''
    # 加载视频文件
    from moviepy import VideoFileClip
    video_clip = VideoFileClip(video_file)

    # 提取音频
    audio_clip = video_clip.audio

    # 保存音频为MP3文件
    audio_clip.write_audiofile(output_audio_file)

    # 关闭视频和音频剪辑
    video_clip.close()
    audio_clip.close()

def clipVideo(src, dest, x, y, width, height):
    from moviepy import VideoFileClip
    # 加载视频
    clip = VideoFileClip(src)

    # 裁剪视频
    cropped_clip = clip.crop(x1=x, y1=y, width=width, height=height)

    # 写入裁剪后的视频
    cropped_clip.write_videofile(dest, codec='libx264')

    # 释放资源
    clip.close()
    cropped_clip.close()

def overlayVideo(src, paste, dest, x, y):
    '''
    在原视频上叠加一个视频。
    原视频的声音会去掉，采用叠加的视频声音。
    原视频的fps会设置与叠加一致。
    原视频的时长不足时，会循环反向补齐，保障与粘贴的视频长度一致。
    '''
    from moviepy import VideoFileClip, CompositeVideoClip, concatenate_videoclips
    import moviepy.video.fx.all as vfx

    # 要修改 moviepy 源码，将 ffmpeg_reader.py 195/196 两行注释掉

    # 加载源视频，不需要声音
    src_clip = VideoFileClip(src, audio=False)

    # 加载要贴上的视频
    paste_clip = VideoFileClip(paste)

    src_clip = src_clip.set_fps(paste_clip.fps)

    extended_clips = [src_clip]
    while src_clip.duration < paste_clip.duration:
        # 反向剪辑
        reversed_clip = src_clip.fx(vfx.time_mirror)
        # 将原始剪辑和反向剪辑拼接
        extended_clips.append(reversed_clip)
        # 更新剪辑
        src_clip = concatenate_videoclips(extended_clips, method="compose")

    # 将要贴上的视频放置在源视频的指定位置
    composite_clip = src_clip.set_position(
        (0, 0)).set_duration(paste_clip.duration)
    paste_clip = paste_clip.set_position(
        (x, y)).set_duration(paste_clip.duration)
    final_clip = CompositeVideoClip([composite_clip, paste_clip])

    # 保存合成后的视频
    final_clip.write_videofile(dest, codec='libx264')

    # 释放资源
    src_clip.close()
    paste_clip.close()
    final_clip.close()

def matchVideoLength(original_video_path, reference_video_path, output_video_path):
    from moviepy import VideoFileClip, concatenate_videoclips
    # 加载原始视频和参考视频
    original_clip = VideoFileClip(original_video_path)
    reference_clip = VideoFileClip(reference_video_path)

    # 获取视频的持续时间
    original_duration = original_clip.duration
    reference_duration = reference_clip.duration

    # 如果原始视频比参考视频短，进行扩展操作
    if original_duration < reference_duration:
        # 计算需要循环的次数，包括正向和反向播放
        loop_count = int(reference_duration / original_duration) + 1

        # 创建一个列表，存储所有循环的视频片段
        clips = [original_clip]
        for _ in range(loop_count - 1):
            # 复制当前片段，然后进行反转
            reversed_clip = clips[-1].reverse()
            clips.append(reversed_clip)

        # 合并所有片段，创建一个新剪辑
        extended_clip = VideoFileClip.concatenate(clips, method="compose")
    else:
        # 如果原始视频已经比参考视频长，直接裁剪到参考视频的长度
        extended_clip = original_clip.subclip(0, reference_duration)

    # 写入视频文件
    extended_clip.write_videofile(
        output_video_path, codec='libx264', audio_codec='copy')

    # 释放资源
    original_clip.close()
    reference_clip.close()
    extended_clip.close()

def setVideoFPS(src, dest, fps):
    """
    修改视频文件的帧率。

    参数:
    src (str): 源视频文件的路径。
    dest (str): 目标视频文件的路径，即修改帧率后的视频保存路径。
    fps (int): 目标帧率。
    """
    from moviepy import VideoFileClip
    # 载入视频文件
    clip = VideoFileClip(src)

    # 设置新的帧率
    clip = clip.with_fps(fps)

    # 输出修改后的视频
    clip.write_videofile(dest, codec="libx264")

    # 关闭clip，释放资源
    clip.close()

def embedAudioInVideo(video_path, audio_path, output_path):
    """
    将音频嵌入到视频中，并确保合成后的视频长度与视频本身的长度一致。

    参数:
    video_path (str): 视频文件的路径。
    audio_path (str): 音频文件的路径。
    output_path (str): 合成后的视频文件的保存路径。
    """
    from moviepy import VideoFileClip, AudioFileClip
    # 载入视频文件
    video_clip = VideoFileClip(video_path)

    # 载入音频文件
    audio_clip = AudioFileClip(audio_path)

    # 将音频剪辑到与视频相同的长度
    audio_clip = audio_clip.set_duration(video_clip.duration)

    # 将音频嵌入到视频中
    video_clip = video_clip.set_audio(audio_clip)

    # 输出合成后的视频
    video_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

    # 关闭clip，释放资源
    video_clip.close()
    audio_clip.close()

def buildVideo(images_path, audio_path, dest, fps):
    from moviepy import VideoFileClip, ImageClip, AudioFileClip, concatenate_videoclips

    images = mu.getFiles(images_path)
    audio_clip = AudioFileClip(audio_path)
    
    # 获取音频时长
    audio_duration = audio_clip.duration

    video_clips = [ImageClip(img,duration=1/fps) for img in images]

    # 合并所有剪辑为一个视频剪辑
    new_clip = concatenate_videoclips(video_clips)

    # 将原始音频添加到新的视频剪辑中
    new_clip = new_clip.with_audio(audio_clip).with_duration(audio_duration)

    # 导出视频
    new_clip.write_videofile(dest, fps=fps)

    # 清理，释放资源
    new_clip.close()

def mergeVideo(video_path, dest):
    from moviepy import VideoFileClip, ImageClip, AudioFileClip, concatenate_videoclips

    vids = mu.getFiles(video_path)
    video_clips = [VideoFileClip(v) for v in vids]
    new_clip = concatenate_videoclips(video_clips)
    new_clip.write_videofile(dest)
    new_clip.close()

# 读取指定文件夹里的 mp4 文件 批量生成 m3u8 和 ts 文件 存到指定目录下
def convertMp4sToM3u8s(mp4_files, m3u8_path):
    for root, dirs, files in os.walk(mp4_files):
        for file in files:
            if file.endswith(".mp4"):
                convertMp4ToM3u8(root+"\\"+file,m3u8_path)

def convertMp4ToM3u8(mp4_file, m3u8_path):
    import ffmpeg
    import subprocess
    try:
        # 使用 mu.fileParts 分解文件路径
        filepath, shotname, extension = mu.fileParts(mp4_file)
        
        # 组装 FFmpeg 命令行指令
        command = [
            'ffmpeg',
            '-i', mp4_file,
            '-force_key_frames', 'expr:gte(t,n_forced*2)',
            '-strict', '-2',
            '-c:a', 'aac',
            '-c:v', 'libx264',
            '-hls_time', '2',
            '-f', 'hls',
            '-hls_list_size', '0',
            '-hls_segment_filename', f'{m3u8_path}/{shotname}-%03d.ts',
            f'{m3u8_path}/{shotname}.m3u8'
        ]
        
        # 执行 FFmpeg 命令
        subprocess.run(command, check=True)
        print(f"成功将 {mp4_file} 转换为 m3u8 格式和对应的.ts 文件。")
        
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg 命令执行失败：{e}")
    except Exception as e:
        print(f"转换过程中出现错误：{e}")


# 单个 mp4 文件路径 生成 m3u8 和 ts 文件 存到指定目录下
def convertMp4ToM3u81(mp4_file, m3u8_path):
    import ffmpeg
    import subprocess
    try:
        filepath, shotname, extension = mu.fileParts(mp4_file)
        # ffmpeg.input(mp4_file).output(m3u8_path + '/'+shotname+'_%03d.ts', format='segment', segment_list=m3u8_path + '/'+ shotname +'.m3u8').run()
        command = f'ffmpeg -i {mp4_file} -force_key_frames "expr:gte(t,n_forced*2)" -strict -2 -c:a aac -c:v libx264 -hls_time 2 -f hls -hls_list_size 0 -hls_segment_filename '+ m3u8_path + '/'+ shotname +'-%03d.ts ' + m3u8_path + '/'+ shotname +'.m3u8'
        # command = f'ffmpeg -i {mp4_file} -c:v libx264 -profile:v baseline -level 3.0 -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 96k -ac 2 -ar 44100 -strict experimental ' + m3u8_path + '/'+ shotname +'-.m3u8'
        subprocess.run(command, check=True, shell=True)
        print(f"成功将 {mp4_file} 转换为 m3u8 格式和对应的.ts 文件。")
    except ffmpeg.Error as e:
        print(f"转换过程中出现错误：{e}")

# 读取指定的 m3u8 文件 修改里面的 ts路径 适配 bigO 的 文件下载 api
def convertTSUrlOfM3u8(m3u8_path, pattern):
    import re

    filepath, shotname, extension = mu.fileParts(m3u8_path)

    # 获取文本数据
    fileData = mu.readAllText(m3u8_path)

    # 使用findall方法来查找所有匹配的数据
    items = re.findall(shotname + r'-.*?.ts', fileData)
    
    items = list(set(items))
    
    for i1 in items:
        # "?filename="+i1+f"&userId={userId}&type=user&download=true"
        i2 = pattern.replace("{tsUrl}", i1)
        fileData = fileData.replace(i1, i2)

    mu.writeAllText(m3u8_path, fileData, 'w')
                
# 读取文件夹里的 m3u8 文件 批量修改里面的 ts路径 适配 bigO 的 文件下载 api
def convertTSUrlOfM3u8Batch(m3u8_path, pattern):
    # ?filename=0-000.ts&userId=0&type=user&download=true
    for root, dirs, files in os.walk(m3u8_path):
        for file in files:
            if file.endswith(".m3u8"):
                rootFile = root.replace('\\', '/') + '/' + file

                convertTSUrlOfM3u8(rootFile,pattern)
                
def genMatchVideo(static_file, action_files, audio_file, out_file):
    """
        生成与音频长度匹配的视频。
        从动态视频中随机选择，剩下的时间由静态视频补充，最终生成的视频长度与音频一致。

    Args:
        static_file (str): 静态视频文件路径。
        action_files (list[str]): 动态视频文件路径列表。
        audio_file (str): 音频文件路径。
        out_file (str): 输出视频文件路径。

    Returns:
        str: 输出视频文件路径。
    """
    import moviepy as mpy
    
    # 加载音频文件
    audio = mpy.AudioFileClip(audio_file)

    # 获取音频的时长
    audio_duration = audio.duration

    # 记录每个视频地址、clip及其时长
    static_clip = mpy.VideoFileClip(static_file)
    static_duration = static_clip.duration

    actions = []
    result = []

    for action_file in action_files:

        action1_clip = mpy.VideoFileClip(action_file)
        action1_duration = action1_clip.duration
        actions.append({
            "file": action_file,
            "clip": action1_clip,
            "duration": action1_duration
        })

    # 创建一个计数器
    count = 0
    
    # 初始权重列表，假设每个选项初始权重相同
    weights = [1] * len(action_files)

    # 最多搞20次就差不多了，剩下的就直接用静态视频补齐
    while audio_duration > 0 and count < 20:
        # 根据权重计算累计权重
        total_weight = sum(weights)
        # 如果总权重为 0，重新初始化权重
        if total_weight == 0:
            weights = [1] * len(action_files)
            total_weight = sum(weights)
        # 生成一个随机数，用于选择
        rand = random.uniform(0, total_weight)
        # 遍历选项，找到对应的选择
        cumulative_weight = 0
        choice = -1
        for i in range(len(weights)):
            cumulative_weight += weights[i]
            if rand <= cumulative_weight:
                choice = i
                break
        # 降低已选中项的权重
        weights[choice] *= 0.05  # 例如，将权重减半
        
        # 每次循环增加计数器的值
        count += 1

        # choice = random.choice(range(len(action_files)))
        act = actions[choice]
        
        # 如果小时间块能够完整地放入audio_duration中，就将它添加到结果列表中，并从 audio_duration 中减去相应的秒数
        if act["duration"] <= audio_duration:
            result.append(act)
            audio_duration -= act["duration"]
            # print(act)
        # 如果小时间块不能完整地放入audio_duration中，就跳过它，继续下一次循环
        else:
            continue

    # # 最多搞20次就差不多了，剩下的就直接用静态视频补齐
    # while audio_duration > 0 and count < 20:
    #     # 每次循环增加计数器的值
    #     count += 1

    #     choice = random.choice(range(len(action_files)))
    #     act = actions[choice]
        
    #     # 如果小时间块能够完整地放入audio_duration中，就将它添加到结果列表中，并从 audio_duration 中减去相应的秒数
    #     if act["duration"] <= audio_duration:
    #         result.append(act)
    #         audio_duration -= act["duration"]
    #         # print(act)
    #     # 如果小时间块不能完整地放入audio_duration中，就跳过它，继续下一次循环
    #     else:
    #         continue

    # 当循环结束时，检查audio_duration是否还有剩余的秒数，如果有，就用静态视频来填充
    if audio_duration > 0:
        # 将静态视频裁剪为剩余时间
        if static_duration > audio_duration:
            # static_clip = static_clip.subclip(0, audio_duration)
            static_clip = static_clip.with_end(audio_duration)
        # 将静态视频扩展到剩余时间
        else:
            static_clip = static_clip.with_duration(duration=audio_duration)
            # static_clip = static_clip.loop(duration=audio_duration)
        result.append({
            "file": static_file,
            "clip": static_clip,
            "duration": audio_duration
        })
        
    print(audio_duration)

    video_clips = [x['clip'] for x in result]
    # 合并所有的视频片段，形成一个完整的视频
    v = mpy.concatenate_videoclips(video_clips)

    # 将音频和视频合成为一个文件，并保存为out_file
    # try:
    # v.set_audio(audio).write_videofile(out_file)
    # 不需要声音
    v.write_videofile(out_file, audio=False)
    v.close()
    # except Exception as e:
    # 处理其他异常
    # print("concatenate_videoclips->write_videofile 发生了未知错误：", mu.getErrorStackTrace())
    # v.write_videofile(out_file)

    # 释放文件句柄
    audio.close()
    static_clip.close()
    for act in actions:
        act["clip"].close()

    print(result)

def genFixedMatchVideo(static_file, action_files, audio_file, out_file):
    """
        生成与音频长度匹配的视频。
        使用动态视频中传进来的固定项，剩下的时间由静态视频补充，最终生成的视频长度与音频一致。

    Args:
        static_file (str): 静态视频文件路径。
        action_files (list[str]): 动态视频文件路径列表。
        audio_file (str): 音频文件路径。
        out_file (str): 输出视频文件路径。

    Returns:
        str: 输出视频文件路径。
    """
    import moviepy as mpy
    
    # 加载音频文件
    audio = mpy.AudioFileClip(audio_file)

    # 获取音频的时长
    audio_duration = audio.duration

    # 记录每个视频地址、clip及其时长
    static_clip = mpy.VideoFileClip(static_file)
    static_duration = static_clip.duration

    # 修改actions为字典结构，以action_file为key
    actions = {}
    result = []

    # 使用传入的固定项，而不是随机选择
    for action_file in action_files:
        # 如果action_file已存在于actions字典中，则直接使用
        if action_file in actions:
            action_item = actions[action_file]
        else:
            # 如果不存在，则创建新的条目
            action1_clip = mpy.VideoFileClip(action_file)
            action1_duration = action1_clip.duration
            action_item = {
                "file": action_file,
                "clip": action1_clip,
                "duration": action1_duration
            }
            # 将新条目添加到actions字典中
            actions[action_file] = action_item
            
        # 添加到结果列表中
        result.append(action_item)
        # 从总时长中减去已使用的时长
        audio_duration -= action_item["duration"]

    # 当循环结束时，检查audio_duration是否还有剩余的秒数，如果有，就用静态视频来填充
    if audio_duration > 0:
        # 将静态视频裁剪为剩余时间
        if static_duration > audio_duration:
            static_clip = static_clip.with_end(audio_duration)
        # 将静态视频扩展到剩余时间
        else:
            static_clip = static_clip.with_duration(duration=audio_duration)
        result.append({
            "file": static_file,
            "clip": static_clip,
            "duration": audio_duration
        })
        
    print(audio_duration)

    video_clips = [x['clip'] for x in result]
    # 合并所有的视频片段，形成一个完整的视频
    v = mpy.concatenate_videoclips(video_clips)

    # 将音频和视频合成为一个文件，并保存为out_file
    # 不需要声音
    v.write_videofile(out_file, audio=False)
    v.close()

    # 释放文件句柄
    audio.close()
    static_clip.close()
    
    # 循环actions字典去释放资源
    for action_item in actions.values():
        if hasattr(action_item["clip"], 'close'):
            action_item["clip"].close()

    print(result)
