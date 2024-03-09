import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton
from PyQt6.QtGui import QPainter, QPolygonF
from PyQt6.QtCore import QPointF
import numpy as np
from spectrum import Spectrum_1D
import math

def data_prep(data, width, height, rang):
    data = data[round(len(data)*rang[0]):round(len(data)*rang[1])]
    data = np.column_stack((np.linspace(0,1,len(data)), data))
    #normalize
    ymax = max(data[:,1])
    ymin = min(data[:,1])
    data[:,1] = -(data[:,1]-ymin)/(ymax-ymin)+1
    #downsampling, bad method, we need one for nmr spectra specifically
    pointperpixel = 100
    sample = max(len(data)//(pointperpixel*width),1)
    
    #scaling to image size
    resampled = data[::sample]
    resampled = resampled*(width, height)
    return resampled

class spectrum_painter(QWidget):
    def __init__(self, data, info):
        super().__init__()
        #geometry
        self.data = data
        self.resampled = []
        self.info = info
        self.axpars = {'dlen': 5, 'pixperinc': 50, 'incperppm': 2, 'ax_padding': 30, 'spect_padding': 50}
        self.rang = (0,1)
        #deln is a length of delimiter in pixels
        #incperppm: multiples - 2 => 0.5 is the minimum increment
        print(info)

    def paintEvent(self, event):
        # settings
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # updating window size
        rect = self.rect()
        self.p_size = {
            'w' : rect.topRight().x()-rect.topLeft().x(),
            'h' : rect.bottomLeft().y()-rect.topRight().y()
            }
        #drawing plot
        fragm = (0,1)
        self.resampled = data_prep(self.data.copy(), self.p_size['w'], self.p_size['h']-self.axpars['spect_padding'], self.rang)
        self.resampled = [QPointF(i[0], i[1]) for i in self.resampled]
        painter.drawPolyline(QPolygonF(self.resampled))
        
        # drawing axis delimiters, adjusts automatically
        # parameters
        ax_pos = self.p_size['h']-self.axpars['ax_padding']
        width = self.info['plot_end_ppm']-self.info['plot_begin_ppm']
        incr = math.ceil(self.axpars['incperppm']*width/(self.p_size['w']//self.axpars['pixperinc']))/self.axpars['incperppm']
        # axis line
        painter.drawLine(QPointF(0.0,ax_pos), QPointF(self.p_size['w'], ax_pos))
        # increments lists
        del_pos_list = [(i*incr+width%incr)/width for i in range(int(width//incr))]
        del_text_list = [str(round((self.info['plot_end_ppm']-i*width)*self.axpars['incperppm'])/self.axpars['incperppm']) for i in del_pos_list]
        # if last delimiter is too close to edge
        if (1-del_pos_list[-1])*self.p_size['w']<10: 
            del_pos_list.pop(-1)
            del_text_list.pop(-1)
        # draw delimiters
        for i in range(len(del_pos_list)):
            del_pos = del_pos_list[i]
            del_text = del_text_list[i]
            top_del = QPointF(del_pos*self.p_size['w'],ax_pos+self.axpars['dlen'])
            bot_del = QPointF(del_pos*self.p_size['w'],ax_pos-self.axpars['dlen'])
            painter.drawLine(top_del, bot_del)
            num_pos = QPointF(del_pos*self.p_size['w'],ax_pos+4*self.axpars['dlen'])
            painter.drawText(num_pos, del_text)
        
        painter.end()

class window(QMainWindow):
    def __init__(self, experiments):
        super().__init__()
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        self.button = QPushButton("Open File")
        layout.addWidget(self.button)
        self.button = QPushButton("Find Peaks")
        layout.addWidget(self.button)

        # widnow size, position, margins, etc
        size = {'w':800,'h':400}
        self.setGeometry(200, 200, size['w'], size['h']) 
        
        # opening spectrum, in the future on event
        experiments = []
        title = "Open NMR"
        if 'event':
            nmr_file_path = "./example_fids/agilent_example1H.fid"
            experiments.append(Spectrum_1D.create_from_file(nmr_file_path))
            title+= ' - ' + nmr_file_path
        
        # modifying in relation to spectrum
        self.setWindowTitle(title)
        spec = experiments[0]
        self.painter_widget = spectrum_painter(spec.spectrum, spec.info)
        layout.addWidget(self.painter_widget)

        self.setCentralWidget(central_widget)

if __name__ == "__main__":
    #main app
    experiments = []
    app = QApplication(sys.argv)
    window = window(experiments)
    window.show()
    sys.exit(app.exec())

