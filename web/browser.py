import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, NoSuchWindowException
import typing as t
from time import sleep, time
import traceback
from threading import Event

class Browser:
    def __init__(self, event: Event, callback: t.Optional[t.Callable]) -> None:
        self.url = "https://www.resonance-columba.com/route"
        self.user_data_dir = os.path.join(os.path.dirname(__file__), "user_data")
        if not os.path.exists(self.user_data_dir):
            os.makedirs(self.user_data_dir)
        self._driver: t.Optional[webdriver.Edge] = None
        self.callback = callback
        self.event = event

    @property
    def driver(self) -> webdriver.Edge:
        if self._driver is None:
            self.options = webdriver.EdgeOptions()
            self.options.add_argument(f"user-data-dir={self.user_data_dir}")
            self._driver = webdriver.Edge(options=self.options)
        return self._driver

    def wait_for_info(self, interval_s: int=2) -> None:
        print("正在打开商会网页...")
        try:
            self.driver.get(self.url)
            print("请将<来回>选项开启，并在配置好个人数据")
            print("之后点击想要的路线，打开路线详情，助手会自动检测路线内容")
            while True:
                info = self.get_route_and_goods_list()
                if info is not None:
                    break
                if self.event.is_set():
                    break

                sleep(interval_s)

            # 通过回调函数将信息传递给主线程
            if self.callback is not None and info is not None:
                self.callback(info)
        except NoSuchWindowException:
            print("浏览器窗口已关闭")
        except Exception:
            traceback.print_exc()
        finally:
            if self._driver is not None:
                self._driver.quit()
            self._driver = None

        
        



    def get_route_and_goods_list(self) -> t.Optional[t.Tuple[t.Tuple[str, t.List[str], int], t.Tuple[str, t.List[str], int]]]:
        try:
            ele = self.driver.find_element(by=By.XPATH, value="/html/body/div[2]/div[3]/div")
        except NoSuchElementException:
            return None
        route_ele = ele.find_element(by=By.XPATH, value="./h2")
        src, dst = route_ele.text.split("\n")
        # 七号自由港 -> 7号自由港
        src = src.replace("七号自由港", "7号自由港")
        dst = dst.replace("七号自由港", "7号自由港")
        src_goods_ele = ele.find_element(by=By.XPATH, value="./div[1]/div[1]/p[3]")
        src_goods = [ele.text for ele in src_goods_ele.find_elements(by=By.CLASS_NAME, value="mx-1")]

        dst_goods_ele = ele.find_element(by=By.XPATH, value="./div[1]/div[2]/p[3]")
        dst_goods = [ele.text for ele in dst_goods_ele.find_elements(by=By.CLASS_NAME, value="mx-1")]

        src_extra_goods_num_ele = ele.find_element(by=By.XPATH, value="./div[1]/div[1]/p[2]")
        src_extra_goods_num = int(src_extra_goods_num_ele.text.split("：")[1])

        dst_extra_goods_num_ele = ele.find_element(by=By.XPATH, value="./div[1]/div[2]/p[2]")
        dst_extra_goods_num = int(dst_extra_goods_num_ele.text.split("：")[1])

        return (src, src_goods, src_extra_goods_num), (dst, dst_goods, dst_extra_goods_num)



if __name__ == "__main__":
    browser = Browser(None)
    browser.wait_for_info()