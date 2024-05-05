import typing as t
from PIL import Image
import numpy as np
import os


class OCR:
    def __init__(self):
        self.ocr = None

    def initailize(self):
        print("OCR正在加载中...")
        # 延迟导入paddleocr库
        # 不太懂为什么仅仅只是import paddleocr都会这么慢
        # 飞桨你就不能把耗时操作放在OCR对象初始化时吗？
        from paddleocr import PaddleOCR
        det_model_dir = os.path.join(os.path.dirname(__file__), 'model/det/ch/ch_PP-OCRv4_det_infer')
        rec_model_dir = os.path.join(os.path.dirname(__file__), 'model/rec/ch/ch_PP-OCRv4_rec_infer')
        cls_model_dir = os.path.join(os.path.dirname(__file__), 'model/cls/ch_ppocr_mobile_v2.0_cls_infer')
        self.ocr = PaddleOCR(
            use_angle_cls=True, 
            lang='ch', 
            show_log=False, 
            use_gpu=False,
            det_model_dir=det_model_dir,
            rec_model_dir=rec_model_dir,
            cls_model_dir=cls_model_dir
        )

    def detect(self, image: Image.Image) -> t.List[t.Tuple[int, int, str, float]]:
        image = np.array(image)
        result = []
        # 懒加载，避免一开始就加载模型
        if self.ocr is None:
            self.initailize()
        detect_result = self.ocr.ocr(image, det=True)[0]

        if detect_result is None:
            # 未检测到任何文字，返回空列表
            return result
        
        for positions, name_and_confidence in detect_result:
            left_top, _, right_bottom, _ = positions
            x1, y1 = left_top
            x2, y2 = right_bottom
            # 计算中心坐标
            x: int = int((x1 + x2) / 2)
            y: int = int((y1 + y2) / 2)
            
            name, confidence = name_and_confidence
            result.append((x, y, name, confidence))
        return result


    
    def recognize(self, image: Image.Image) -> t.Tuple[str, float]:
        image = np.array(image)
        # 懒加载，避免一开始就加载模型
        if self.ocr is None:
            self.initailize()
        recognize_result = self.ocr.ocr(image, det=False)[0][0]
        name, confidence = recognize_result
        return name, confidence
    


if __name__ == '__main__':
    ocr = OCR()
    ocr.initailize()