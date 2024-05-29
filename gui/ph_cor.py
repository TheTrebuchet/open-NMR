import sys
import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPainter, QDoubleValidator
from PyQt5.QtWidgets import (QStyle, QStyleOptionSlider, QWidget,  
                             QVBoxLayout, QHBoxLayout, QLabel, QLineEdit)
from PyQt5.QtCore import QRect, QPoint, Qt


class phaseCorrectionWindow(QWidget):
    """
    separate window for phase correction gui
    """
    def __init__(self, current_tab=None):
        super().__init__()
        # print("init")
        
        ph0_value = current_tab.experiment.phase_correction.ph0/2*360
        ph1_value = current_tab.experiment.phase_correction.ph1[0].correction/2*360
        pivot_value = current_tab.experiment.phase_correction.ph1[0].pivot*100
        
        self.setGeometry(200, 200, 400, 150)
        phc_0 = pcSlider("PH0", -180, 180, 60, ph0_value, parent=self)
        phc_1 = pcSlider("PH1", -180, 180, 60, ph1_value, parent=self)
        pivot = pcSlider("Pivot \n [%]", 0, 100, 25, pivot_value, parent=self)
        
        layout = QVBoxLayout()
        layout.addWidget(phc_0)
        layout.addWidget(phc_1)
        layout.addWidget(pivot)

        self.setLayout(layout)
        self.slider_changed = {"PH0": self.ph0_changed,
                               "PH1": self.ph1_changed,
                               "Pivot \n [%]": self.pivot_changed,}
        
    def ph0_changed(self):
            print("PH0")
    def ph1_changed(self):
            print("PH1")
    def pivot_changed(self):
            print("Pivot")

class pcSlider(QWidget):
    """
    widget for choosing phase correction, form as below:
        label, slider, text input with position of slider
    """
    def __init__(self, text, minimum, maximum, interval, initial, parent):
        super().__init__(parent=parent)
        self.parent = parent
        self.text_label = QLabel(text, parent=self)
        self.text_label.setMinimumSize(30,40)

        self.slider = LabeledSlider(minimum, maximum, interval, 100)
        self.slider.slider.setValue(int(initial*100))
        self.slider.slider.valueChanged.connect(self.sliderChanged)
        
        
        self.input_field = QLineEdit(parent=self)
        self.input_field.setValidator(QDoubleValidator(minimum, maximum, 2))
        self.input_field.setText(format(initial, "0.2f"))
        self.input_field.editingFinished.connect(self.inputFieldChanged)
        
        layout = QHBoxLayout()
        layout.addWidget(self.text_label)
        layout.addWidget(self.slider)
        layout.addWidget(self.input_field)
        self.setLayout(layout)
        
        self.value = initial

        
    def sliderChanged(self, value):
        # print("S")
        value = value/100
        self.input_field.setText(str(value))
        self.value = value
        # print(self.value)
        
        # signal to phaseCorrectionWindow that value was changed,
        # (inputFieldChanged causes sliderChanged to run anyway)
        self.parent.slider_changed[self.text_label.text()]()
    
    def inputFieldChanged(self):
        # print("F")
        value = self.input_field.text()
        self.value = float(value)
        value = self.value*100
        value = int(value)
  
        self.slider.slider.setValue(value)
        # print(self.value)
        
class LabeledSlider(QtWidgets.QWidget):
    """
    slider with labeled ticks, because it works only on integers to represent 
    float number its ranges are multiplied by scale, which defines also decimal precision
    ie. scale 100 allows to set floats with two decimal places
    """
    def __init__(self, minimum, maximum, interval=1, scale=1, parent=None):
        
        pre_levels=range(minimum, maximum+interval, interval)
        minimum *= scale
        maximum *= scale
        interval *= scale

        
        super(LabeledSlider, self).__init__(parent=parent)

        levels=range(minimum, maximum+interval, interval)

        orientation=Qt.Horizontal
        self.levels=list(zip(levels,map(str,pre_levels)))


        self.layout=QtWidgets.QVBoxLayout(self)
        self.left_margin=10
        self.top_margin=10
        self.right_margin=10
        self.bottom_margin=10

        self.layout.setContentsMargins(self.left_margin,self.top_margin,
                self.right_margin,self.bottom_margin)

        self.slider=QtWidgets.QSlider(orientation, self)
        self.slider.setMinimum(minimum)
        self.slider.setMaximum(maximum)
        self.slider.setValue(minimum)
        if orientation==Qt.Horizontal:
            self.slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
            self.slider.setMinimumWidth(300) 
        else:
            self.slider.setTickPosition(QtWidgets.QSlider.TicksLeft)
            self.slider.setMinimumHeight(300) 
        self.slider.setTickInterval(interval)
        
        # step = (maximum-minimum)/10
        # step = int(step)
        self.slider.setSingleStep(1)

        self.layout.addWidget(self.slider)
        
    def paintEvent(self, e):

        super(LabeledSlider,self).paintEvent(e)

        style=self.slider.style()
        painter=QPainter(self)
        st_slider=QStyleOptionSlider()
        st_slider.initFrom(self.slider)
        st_slider.orientation=self.slider.orientation()

        length=style.pixelMetric(QStyle.PM_SliderLength, st_slider, self.slider)
        available=style.pixelMetric(QStyle.PM_SliderSpaceAvailable, st_slider, self.slider)

        for v, v_str in self.levels:
            rect=painter.drawText(QRect(), Qt.TextDontPrint, v_str)
            x_loc=QStyle.sliderPositionFromValue(self.slider.minimum(),
                    self.slider.maximum(), v, available)+length//2
            left=x_loc-rect.width()//2+self.left_margin
            bottom=self.rect().bottom()
            if v==self.slider.minimum():
                if left<=0:
                    self.left_margin=rect.width()//2-x_loc
                if self.bottom_margin<=rect.height():
                    self.bottom_margin=rect.height()

                self.layout.setContentsMargins(self.left_margin,
                        self.top_margin, self.right_margin,
                        self.bottom_margin)
            if v==self.slider.maximum() and rect.width()//2>=self.right_margin:
                self.right_margin=rect.width()//2
                self.layout.setContentsMargins(self.left_margin,
                        self.top_margin, self.right_margin,
                        self.bottom_margin)
            pos=QPoint(left, bottom)
            painter.drawText(pos, v_str)
        return

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    frame=QtWidgets.QWidget()
    ha=QtWidgets.QHBoxLayout()
    frame.setLayout(ha)

    w = phaseCorrectionWindow()

    ha.addWidget(w)
    frame.show()
    sys.exit(app.exec_())
        
        



