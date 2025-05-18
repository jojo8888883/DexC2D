from select_mp4.selector import main
from raw2mp4.raw2mp4 import main

if __name__ == "__main__":
    # 选择视频
    main(clear_first=True, import_videos=True, video_count=4)

    # 转换视频
    main(clear_first=True, import_videos=True, video_count=4)


