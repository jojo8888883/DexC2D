from select_mp4.selector import main as select_mp4_main
from raw2mp4.raw2mp4 import main as raw2mp4_main

# 先运行raw2mp4
raw2mp4_main()

# 再运行select_mp4
select_mp4_main()

