import os
import sys
import numpy as np
import pyqtgraph as pg
from glob import glob
from time import time
from qiplot.reader import get_xye
from qiplot.colors import getcmcolors
from qiplot.arparser import parse_2d_arguments
from matplotlib import cm
import traceback
import logging
from logging.config import fileConfig


try:
    from PyQt6 import QtGui, QtCore, QtWidgets
    PYQT_VERSION = 6
except ImportError:
    from PyQt5 import QtGui, QtCore, QtWidgets
    PYQT_VERSION = 5

pg.setConfigOption('leftButtonPan', False)

class Q2plot:
    def __init__(self, title, size):
        ## initialise qt app
        self.app = pg.mkQApp()
        self.win = pg.GraphicsLayoutWidget(title=title)
        try:
            screensize = self.app.primaryScreen().size()
            (wid, hei) = size
            if size[0]/screensize.width() > 0.95:
                wid = int(np.round(screensize.width()*0.66))
            if size[1]/screensize.height() > 0.95:
                hei = int(np.round(screensize.height()*0.66))
            self.win.resize(int(wid), int(hei))
        except:
            logging.warning(err)
            logging.warning(traceback.format_exc())
            self.win.resize(int(800), int(600))
        self.win.show()

        # create 2d plot box
        self.plo2dw = self.win.addPlot(row=0, col=0, rowspan=1, colspan=1, name='waterfall')
        self.img = pg.ImageItem()
        self.plo2dw.addItem(self.img)
        self.plo2dw.setTitle(text_plot2d())
        # create 1d plot box
        self.label = pg.LabelItem(justify='center')
        self.label.setText(text_plot1d())
        self.win.addItem(self.label, row=1, col=0)
        self.plow = self.win.addPlot(row=2, col=0, rowspan=1, colspan=2, name='1D plot')
        self.plow.showGrid(True, True, 0.5)
        # adjust row heights
        self.win.ci.layout.setRowStretchFactor(0, 64)
        self.win.ci.layout.setRowStretchFactor(1, 1)
        self.win.ci.layout.setRowStretchFactor(2, 48)

    def hover_plot1d(self, evt):
        if self.plow.sceneBoundingRect().contains(evt[0]):
            mousePoint = self.plow.vb.mapSceneToView(evt[0])
            self.label.setText(text_plot1d(mousePoint.x(), mousePoint.y()))


def text_plot2d(x=0, y=0, j=0, i=0, v=0):
    vals = f'x={x:<10.3f}  y={y:<10.3f}  pixel=({j:<5g}, {i:<5g})  value={v:<10g}'
    return "<span style='font-size: 12pt'>"+vals+"</span>"


def text_plot1d(x=0, y=0):
    vals = f'x={x:<10.3f}  y={y:<10.3f}'
    return f"<span style='font-size: 12pt'>"+vals+"</span>"


def main():
#    os.environ["QT_DEBUG_PLUGINS"] = "1"
    try:
        # Start Qt application
        app = QtWidgets.QApplication(sys.argv)

        # Initialize logging
        dname = glob(os.path.dirname(__file__))[0]
        cfgname = dname + '/logconf.py'
        fileConfig(cfgname)
        logging.info('Ready')
        t0 = time()

        ## read input files
        args = parse_2d_arguments()
        fdata, names = get_xye(args.datafiles[::args.every], usecols=[0,1],
                               maxbytes=args.maxbytes*(1<<10), label=args.label)
        t1 = time()
        logging.info(f'Getting data:{np.round(t1-t0, 3)} s')

        # flip images by default
        pg.setConfigOptions(imageAxisOrder='row-major')

        ## start qt application
        qplot = Q2plot(args.title, args.winsize)

        # try to apply colormap directly
        pos = np.array([0., 1., 0.5, 0.25, 0.75])
        color = np.array([[0,255,255,255], [255,255,0,255], [0,0,0,255], (0, 0, 255, 255), (255, 0, 0, 255)], dtype=np.ubyte)
        cmap = pg.ColorMap(pos, color)

        # fill image with data
        data = np.empty((len(fdata), len(fdata[0][0])))
        for ii in range(len(fdata)):
            data[ii,:] = fdata[ii][1]
        if args.diff is not None and isinstance(args.diff, int):
            if args.diff != -99:
                data -= data[args.diff,:]
            elif args.diff == -99:
                data -= np.mean(data, axis=0)

        xdata = fdata[0][0]
        qplot.img.setImage(data, autoLevels=True)

        # scale from npoints to actual x-axis
        xmin, xmax = min(xdata),max(xdata)
        datarange = QtCore.QRectF(xmin, 0, xmax, data.shape[0])
        qplot.img.setRect(datarange)

        # Custom ROI for selecting an image region
        hsize = np.round((xmax-xmin)/5, 1)
        vsize = 1
        roi = pg.RectROI([xdata[np.argmax(np.mean(data, axis=0))] - hsize/2, 0],
                         size=[hsize, vsize], sideScalers=True,
                         maxBounds=datarange, snapSize=np.round(hsize/4, 2), translateSnap=True)
        qplot.plo2dw.addItem(roi)
        roi.setZValue(10)

        # Callbacks for handling user interaction
        def updatePlot():
            selected = roi.getArrayRegion(data, qplot.img)
            x0 = roi.pos()[0]
            x1 = x0 + roi.size()[0]
            newx = np.linspace(x0, x1, selected.shape[1])
            qplot.plow.plot(newx, np.nanmedian(selected, axis=0), clear=True)
            qplot.plow.setXRange(x0, x1)

        roi.sigRegionChanged.connect(updatePlot)
        updatePlot()


        # Contrast/color control
        hist = pg.HistogramLUTItem(image=qplot.img)#, orientation='vertical')
        hist.gradient.setColorMap(cmap)
        qplot.win.addItem(hist, row=0, col=1, rowspan=1, colspan=1)
        hist.setLevels(data.min(), data.max())

        ## add cursor position
        qplot.proxy = pg.SignalProxy(qplot.plow.scene().sigMouseMoved, rateLimit=60, slot=qplot.hover_plot1d)

        def image_hover(event):
            if event.isExit():
                qplot.plo2dw.setTitle(text_plot2d())
                return
            pos = event.pos()
            i, j = pos.y(), pos.x()
            i = int(np.clip(i, 0, data.shape[0] - 1))
            j = int(np.clip(j, 0, data.shape[1] - 1))
            val = data[i, j]
            ppos = qplot.img.mapToParent(pos)
            x, y = ppos.x(), ppos.y()
            qplot.plo2dw.setTitle(text_plot2d(x, y, j, i, val))
        qplot.img.hoverEvent = image_hover

        t2 = time()
        logging.info(f'Plotting:{np.round(t2-t1, 3)} s')


        # Launch Qt application
        if PYQT_VERSION == 5:
            app.exec_()
        else:
            app.exec()

    except Exception as err:
        logging.error(err)
        logging.error(traceback.format_exc())
        sys.exit(1)

    finally:
        if 'app' in locals():
            app.quit()
        sys.exit(0)

if __name__ == '__main__':
    os.system('xhost +localhost')
    main()
