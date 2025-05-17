from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, JavascriptException
from urllib.parse import urlparse
import logging

class DOMAutomationChecker:
    def __init__(self, driver):
        self.driver = driver
        self.logger = logging.getLogger(__name__)
        
    def check_all_signals(self):
        """检查所有DOM自动化信号"""
        signals = {
            "js_injection": self._check_js_injection(),
            "canvas_only": self._check_canvas_only(),
            "cross_origin_iframe": self._check_cross_origin_iframe(),
            "shadow_dom": self._check_shadow_dom(),
            "browser_policy": self._check_browser_policy()
        }
        
        return signals
    
    def _check_js_injection(self):
        """信号1：检查DevTools是否无法选中子节点"""
        try:
            result = self.driver.execute_script("""
                return document.querySelector('canvas, embed, object') !== null && 
                       document.querySelector('canvas, embed, object').getBoundingClientRect().width > 0;
            """)
            return {
                "can_automate": not result,
                "message": "页面可能使用canvas/embed/object渲染，无法直接操作DOM元素" if result else "页面可以使用DOM操作"
            }
        except Exception as e:
            return {"can_automate": False, "message": f"JS注入检查失败: {str(e)}"}
    
    def _check_canvas_only(self):
        """信号2：检查是否只有canvas/embed/object元素"""
        try:
            canvas_elements = self.driver.find_elements(By.CSS_SELECTOR, 'canvas, embed, object')
            other_elements = self.driver.find_elements(By.CSS_SELECTOR, 'body *:not(canvas):not(embed):not(object)')
            
            return {
                "can_automate": len(canvas_elements) == 0 or len(other_elements) >= 5,
                "message": "页面主要由canvas/embed/object组成，DOM自动化可能受限" if len(canvas_elements) > 0 and len(other_elements) < 5 
                          else "页面包含足够的可操作DOM元素"
            }
        except Exception as e:
            return {"can_automate": False, "message": f"Canvas检查失败: {str(e)}"}
    
    def _check_cross_origin_iframe(self):
        """信号3：检查是否存在跨域iframe"""
        try:
            frames = self.driver.find_elements(By.TAG_NAME, 'iframe')
            current_domain = urlparse(self.driver.current_url).netloc
            
            for frame in frames:
                src = frame.get_attribute('src')
                if src and urlparse(src).netloc != current_domain:
                    try:
                        self.driver.switch_to.frame(frame)
                        self.driver.execute_script("return document.readyState")
                        self.driver.switch_to.default_content()
                    except (WebDriverException, JavascriptException):
                        return {
                            "can_automate": False,
                            "message": "检测到跨域iframe，可能受同源策略限制"
                        }
            
            return {"can_automate": True, "message": "未检测到跨域iframe限制"}
        except Exception as e:
            return {"can_automate": False, "message": f"iframe检查失败: {str(e)}"}
    
    def _check_shadow_dom(self):
        """信号4：检查是否存在Shadow DOM"""
        try:
            has_shadow_dom = self.driver.execute_script("""
                return document.querySelector('*[shadowroot]') !== null || 
                       document.querySelector('*[shadowrootmode]') !== null;
            """)
            
            return {
                "can_automate": not has_shadow_dom,
                "message": "检测到Shadow DOM，需要特殊处理" if has_shadow_dom else "未检测到Shadow DOM"
            }
        except Exception as e:
            return {"can_automate": False, "message": f"Shadow DOM检查失败: {str(e)}"}
    
    def _check_browser_policy(self):
        """信号5：检查浏览器策略限制"""
        try:
            self.driver.execute_script("alert(1)")
            return {"can_automate": True, "message": "未检测到浏览器策略限制"}
        except Exception as e:
            return {
                "can_automate": False,
                "message": "检测到浏览器策略限制（CSP或其他安全策略）"
            }

def main():
    # 使用示例
    driver = webdriver.Chrome()  # 或其他浏览器驱动
    try:
        checker = DOMAutomationChecker(driver)
        driver.get("https://example.com")  # 替换为要检查的URL
        
        results = checker.check_all_signals()
        for signal_name, result in results.items():
            print(f"\n{signal_name}:")
            print(f"可自动化: {result['can_automate']}")
            print(f"消息: {result['message']}")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    main() 