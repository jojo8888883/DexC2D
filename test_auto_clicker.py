import pyautogui
import time

def test_mouse_position():
    print("请在 5 秒内将鼠标移动到想要点击的位置...")
    time.sleep(5)
    x, y = pyautogui.position()
    print(f"当前鼠标位置：({x}, {y})")
    return x, y

def test_click():
    print("测试点击功能...")
    x, y = test_mouse_position()
    pyautogui.click(x, y)
    print(f"已点击位置：({x}, {y})")

def test_type():
    print("测试输入功能...")
    time.sleep(2)
    pyautogui.write("Hello, this is a test!")
    print("已输入测试文本")

if __name__ == "__main__":
    print("开始测试 PyAutoGUI 功能...")
    print("提示：将鼠标移动到屏幕左上角可以中断程序")
    
    # 测试鼠标位置获取
    test_mouse_position()
    
    # 测试点击功能
    test_click()
    
    # 测试输入功能
    test_type()
    
    print("测试完成！") 