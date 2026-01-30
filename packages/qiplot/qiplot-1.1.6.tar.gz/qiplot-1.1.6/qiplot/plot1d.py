#!/usr/bin/env python
import os
import sys
import numpy as np
import pyqtgraph as pg
from glob import glob
from time import time
from qiplot.reader import get_xye
from qiplot.colors import getcmcolors
from qiplot.arparser import parse_1d_arguments
from qiplot.plot2d import text_plot1d
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

class Qiplot:
    def __init__(self, title, size):
        # Initialize Qt app
        self.app = pg.mkQApp()
        self.win = pg.GraphicsLayoutWidget(title=title)
        self.win.closeEvent = self.closeEventHandler
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
        self.label = pg.LabelItem(justify='right')
        self.win.addItem(self.label)
        self.label.setText(text_plot1d())
        self.plow = self.win.addPlot(row=1, col=0, name='p1')
        self.plow.showGrid(True, True, 0.5)
        self.leg = self.plow.addLegend()
        self.leg.autoAnchor((self.plow.width()*0.98, self.plow.height()*0.01))

    def _mouseMoved(self, evt):
        mousePoint = self.plow.vb.mapSceneToView(evt[0])
        self.label.setText(text_plot1d(mousePoint.x(), mousePoint.y()))

    def closeEventHandler(self, event):
        event.accept()
        self.app.quit()
        sys.exit(0)


def main():
#    os.environ["QT_DEBUG_PLUGINS"] = "0"
    try:
        # Start Qt application
        app = QtWidgets.QApplication(sys.argv)

        # Initialize logging
        dname = glob(os.path.dirname(__file__))[0]
        cfgname = dname + '/logconf.py'
        fileConfig(cfgname)
#        logging.info('Ready')

        # Parse input arguments
        args = parse_1d_arguments()
        data, names = get_xye(args.datafiles[::args.every], args.usecols,
                              args.maxbytes * (1 << 10), args.label)

        # Initialize Qiplot
        colors = getcmcolors(len(data), args.cmap)
        qplot = Qiplot(args.title, args.winsize)

        # Add curves to plot
        for ii in range(len(data)):
            x, y, e = data[ii][0], data[ii][1], data[ii][2]
            y += args.offset * ii
            if args.diff is not None and type(args.diff) == int:
                if args.diff != -99:
                    ysubtr, esubtr = data[args.diff][1], data[args.diff][2]
                elif args.diff == -99:
                    ysubtr, esubtr = np.mean(np.array(data)[:, 1], axis=0), np.mean(np.array(data)[:, 2], axis=0)
                y = y - ysubtr
                if sum(e) != 0:
                    e = np.sqrt(e ** 2 + esubtr ** 2)
            cpen = pg.mkPen(colors[ii], width=args.linewidth)
            li = pg.PlotDataItem(x=x, y=y, pen=cpen, name=names[ii])
            qplot.plow.addItem(li)
            if sum(e) != 0:
                e += args.offset * ii
                err = pg.ErrorBarItem(x=x, y=y, top=e / 2, bottom=e / 2, beam=0.5 * np.mean(np.diff(x)), pen=cpen)
                qplot.plow.addItem(err)

        # Add cursor position
        qplot.proxy = pg.SignalProxy(qplot.plow.scene().sigMouseMoved, rateLimit=60, slot=qplot._mouseMoved)

        # Launch Qt application
        if PYQT_VERSION == 5:
            app.exec_()

        else:
            app.exec()

        sys.exit(0)

    except Exception as err:
        logging.error(err)
        logging.error(traceback.format_exc())
        sys.exit(1)

    finally:
        if 'app' in locals():
            app.quit()
        sys.exit(0)

if __name__ == '__main__':
#    os.system('xhost +localhost')    # commented out 2025-oct-28
    sys.exit(main())
