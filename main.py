
from collections import namedtuple
import os.path
import numpy as np
from scipy import ndimage
import matplotlib as mpl
import matplotlib.pyplot as plt
import gspread
import Data_Reduction
import Measurements
import analyses

class interface(object):
    def __init__(self, figure, measurement, actual_data = None):
        font = {'family' : 'sans serif',
            'size'   : 12}
        fontsmall = {'family' : 'sans serif',
            'size'   : 10}
        mpl.rcParams["axes.labelsize"] = 10
        mpl.rcParams["xtick.labelsize"] = 10
        mpl.rcParams["ytick.labelsize"] = 10
        mpl.rcParams["legend.fontsize"] = 10
        mpl.rcParams["legend.labelspacing"] = 0.3         
        mpl.rcParams["legend.borderpad"] = 0.3
        
        if (actual_data is not None):
            self.actual_data = actual_data
        else:
            self.actual_data = measurement.data.data
        
        self.display = figure
        self.current_time = 0#measurement.offsets[2]
        self.measurement = measurement
        self.gs = mpl.gridspec.GridSpec(4,4, width_ratios=[50,1,20,10], height_ratios=[30,20,20,20])
        
        
        self._xRange = (0, 0+self.actual_data.shape[0])
        self._yRange = (0, 0+self.actual_data.shape[1])
        self._timeRange = (0, 0+self.actual_data.shape[2])

        
        self.axes = self.display.add_subplot(self.gs[0:2, 0])
        self.axColour = self.display.add_subplot(self.gs[0:2,1])
        self.axText = self.display.add_subplot(self.gs[0,-1], axisbg='lightgoldenrodyellow')
        self.axRadio = self.display.add_subplot(self.gs[1,-1], axisbg='lightgoldenrodyellow')
        self.axDetail = self.display.add_subplot(self.gs[2, :-1])
        self.axColumn = self.display.add_subplot(self.gs[0:2,2])
        self.axTime = self.display.add_subplot(self.gs[3, :-1])
        self.axSaveButton = self.display.add_subplot(self.gs[3,-1], axisbg='lightgoldenrodyellow')
        #self.gs.tight_layout(self.display)
        self.img = self.axes.imshow(self.actual_data[:,:,self.current_time], interpolation='none', 
                                    extent=(0,self.actual_data.shape[1],
                                            self.actual_data.shape[0], 0
                                            ), aspect = "auto")
        self.point = self.axes.plot(self.measurement.point[0]-self.measurement.offsets[0], self.measurement.point[1]-self.measurement.offsets[1], 'x', color = "white")
        min_temp = np.amin(self.actual_data)
        max_temp = np.amax(self.actual_data)
        self.img.set_clim(min_temp, max_temp)
        #self.maxtime = len(self.actual_data[0,0,:])-1
        self.axes.set_xlim([0,self.actual_data.shape[1]])
        self.axes.set_ylim([0, self.actual_data.shape[0]])
        self.axes.set_autoscalex_on(False)
        self.axes.set_autoscaley_on(False)
        
        ticksize = np.max((1, int(round((int(np.ceil(max_temp))-int(min_temp))/10.0))))
        self.cbar = self.display.colorbar(self.img, self.axColour, ticks=range(int(min_temp), int(np.ceil(max_temp)),ticksize))
        #print(self.cbar.ax.get_xticklabels(minor=True))
        #self.cbar.ax.set_xticklabels(np.round(self.cbar.ax.get_xticklabels()))
        
        self.axDetail.set_title("Row Temperature", **font)
        self.axDetail.set_ylabel("T*")
        self.axDetail.set_xlabel("horizontal position")
        self.axDetail.set_xlim([self._yRange[0], self._yRange[1]-1])
        self.axDetail.set_ylim([min_temp, max_temp])
        self.axDetail.set_autoscalex_on(False)
        self.axDetail.set_autoscaley_on(False)
        self.axTime.set_title("Time profile point", **font)
        self.axTime.set_ylabel("T*")
        self.axTime.set_xlabel("time")
        self.axTime.set_xlim([self._timeRange[0], self._timeRange[1]-1])
        self.axTime.set_ylim([min_temp, max_temp])
        self.axTime.set_autoscalex_on(False)
        self.axTime.set_autoscaley_on(False)
        self.axColumn.set_title("Column Temperature", **font)
        self.axColumn.set_ylabel("T*")
        self.axColumn.set_xlabel("vertical position")
        self.axColumn.set_xlim([self._xRange[0], self._xRange[1]-1])
        self.axColumn.set_ylim([min_temp, max_temp])
        self.axColumn.set_autoscalex_on(False)
        self.axColumn.set_autoscaley_on(False)
        
        self.detail_pos = (np.nan, np.nan)
        self.hor_line = None
        self.ver_line = None
        self.detail_line = None
        self.time_line = None
        self.detail_ver_line = None
        self.column_line = None
        self.column_ver_line = None
        dat_slice = self.actual_data[self._xRange[0]:self._xRange[1], self._yRange[0]:self._yRange[1], self._timeRange[0]:self._timeRange[1]]
        min_temp = np.amin(self.actual_data[self._xRange[0]:self._xRange[1], self._yRange[0]:self._yRange[1], self._timeRange[0]:self._timeRange[1]])
        max_temp = np.amax(self.actual_data[self._xRange[0]:self._xRange[1], self._yRange[0]:self._yRange[1], self._timeRange[0]:self._timeRange[1]])
        self.time_ver_line, = self.axTime.plot([0, 0], [min_temp, max_temp], '-', color='black',linewidth=1)
        ts = self.measurement.data.time_start - self.measurement.offsets[2]
        
        print(self.measurement.data.time_start, ts)
        self.time_start_line, = self.axTime.plot([ts, ts], [min_temp, max_temp], '-', color='0.75',linewidth=1)
        #self.
        
        bmean = np.zeros(self._timeRange[1] - self._timeRange[0])
        
        for t in range(self._timeRange[0], self._timeRange[1]):
            bmean[t-self._timeRange[0]] = np.mean(self.actual_data[self._xRange[0]:self._xRange[1],
                                                                self._yRange[0]:self._yRange[1],
                                                                t])
            
        trange = range(*self._timeRange)
        self.totmean_line, = self.axTime.plot(trange, bmean, color='b', linewidth=1, label="Image mean")

        self.boxmean_line, = self.axTime.plot(trange, bmean, color='r', linewidth=1, label="Box mean")
        self.boxmean_line2, = self.axTime.plot(trange, bmean, color='r', linewidth=1.5)
        self.axTime.legend()
        
        self.mean = np.mean(self.actual_data[:,:,self.current_time])
        self.boxmean = np.mean(self.actual_data[self._xRange[0]:self._xRange[1],self._yRange[0]:self._yRange[1],self.current_time])
        self.rowmean = 0
        self.val = 0
        self.axText.set_autoscalex_on(False)
        self.axText.set_autoscaley_on(False)
        self.axText.set_xlim([0,1])
        self.axText.set_ylim([0,1])
        self.axText.get_xaxis().set_visible(False)
        self.axText.get_yaxis().set_visible(False)
        txt = "(%i, %i, %i) \n" % self.measurement.data.offsets
        txt += "(%.0f, %.0f) \n" % self.detail_pos
        txt += "total mean \n    %.2f \n" % self.mean
        txt += "box mean \n    %.2f \n" % self.boxmean
        txt += "row mean \n    %.2f \n" % self.rowmean
        txt += "Value: %.2f \n" % self.val
        self.Txt = self.axText.text(0.01,1-0.01,txt,verticalalignment='top', **fontsmall)
                
        
        #axcolor = 'lightgoldenrodyellow'
        self.radioLabels = self.measurement.possibleCalculationNames
        self.radioFuncs = self.measurement.possibleCalculations
        self.radio = mpl.widgets.RadioButtons(self.axRadio, self.radioLabels)
        for txt in self.radio.labels:
            txt.set_size(10)
        self.radio.on_clicked(self.ChangeDataSetButton)
        self.saveButton = mpl.widgets.Button(self.axSaveButton, "save\nQ")
        self.saveButton.on_clicked(self._saveQFunc)
        
        self.bid = self.display.canvas.mpl_connect('key_press_event', self.on_press)
        self.cid = self.display.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        
    def ChangeDataSetButton(self, label):
        i = self.radioLabels.index(label)
        self.ChangeDataSet(self.radioFuncs[i]())

    
    def ChangeDataSet(self, newset):
        self.actual_data = newset
        self.rescaleOnSlice(self._xRange, self._yRange, self._timeRange)
        if self.detail_line is not None:
            self._updateDetailLine(self.detail_pos[1], self.current_time)
        
        if self.time_line is not None:
            self._updateTimeLine(self.detail_pos[0],self.detail_pos[1])
        if self.column_line is not None:
            self._updateColumnLine(self.detail_pos[0], self.current_time)
        
        self.img.set_data(self.actual_data[:,:,self.current_time])
        self._updateBoxMeanLine()
        self._updateMeanLine()
        self.display.canvas.draw()
        self._updateLabels()
        
            
        
    def _updateLabels(self):
        self.mean = np.mean(self.actual_data[:,:,self.current_time])
        self.boxmean = np.mean(self.actual_data[self._xRange[0]:self._xRange[1],self._yRange[0]:self._yRange[1],self.current_time])
        if self.detail_line is not None:
            self.rowmean = np.mean(self.actual_data[self.detail_pos[1], : , self.current_time])
            self.val = self.actual_data[self.detail_pos[1], self.detail_pos[0], self.current_time]
        else:
            self.rowmean = 0
            self.val = 0
        txt = "(%.0f, %.0f, %.0f) \n" % self.measurement.offsets
        txt += "pos (%.0f, %.0f) \n" % self.detail_pos
        txt += "time %i \n" % int(self.current_time)
        txt += "total mean \n    %.2f \n" % self.mean
        txt += "box mean \n    %.2f \n" % self.boxmean
        txt += "row mean \n    %.2f \n" % self.rowmean
        txt += "Value: %.4f \n" % self.val
        if self.detail_line is not None:
            txt += "St (%.5f, %.5f) \n" % (self.measurement.st_lam[self.detail_pos[0]], self.measurement.st_turb[self.detail_pos[0]])
            txt += "Re (%.5f) \n" % (self.measurement.reynolds[self.detail_pos[0]])
        self.Txt.set_text(txt);
            
        
    def update(self, time):
        self._updateTime(time)
    
        
    def rescaleOnSlice(self, xRange, yRange, timeRange):
        self._xRange = xRange
        self._yRange = yRange
        self._timeRange = timeRange
        test = np.sort(self.actual_data, axis = None)
        v = 0.00
        min_temp = test[max(0, int(v*len(test)))]
        max_temp = test[min(len(test)-1, int((1-v)*len(test)))]
        #min_temp = np.amin(self.actual_data[xRange[0]:xRange[1], yRange[0]:yRange[1], timeRange[0]:timeRange[1]])
        #max_temp = np.amax(self.actual_data[xRange[0]:xRange[1], yRange[0]:yRange[1], timeRange[0]:timeRange[1]])

        self._reScaleTemperature(min_temp, max_temp)
        self._updateBoxMeanLine()
        self._updateLabels()
        
        
    def _updatePos(self, xnew, ynew):
        
        self._updateTimeLine(xnew, ynew)
        if ynew != self.detail_pos[1]:
            self._updateColumnverLine(ynew)
            self._updateDetailLine(ynew, self.current_time)
        
        if xnew != self.detail_pos[0]:
            self._updateDetailverLine(xnew)
            self._updateColumnLine(xnew, self.current_time)
        
        
        
        
        if xnew != self.detail_pos[0]:
            self._updateVerLine(xnew)
        if ynew != self.detail_pos[1]:
            self._updateHorLine(ynew)

            
        self.detail_pos = (xnew, ynew)
        self._updateLabels()
        self.display.canvas.draw()

    def _updateTime(self, tnew):
        tnew = np.clip(tnew, self._timeRange[0], self._timeRange[1]-1)
        if tnew != self.current_time:
            self.img.set_data(self.actual_data[:,:,tnew])

            self._updateTimeVerLine(tnew)
            if self.detail_line is not None:
                self._updateDetailLine(self.detail_pos[1], tnew)
            if self.column_line is not None:
                self._updateColumnLine(self.detail_pos[0], tnew)
            self.current_time = tnew
            self._updateLabels()
            self.display.canvas.draw()
            
    
    def _updateBoxMeanLine(self):
        bmean = np.zeros(len(self.actual_data[0,0,:]))
        for t in range(len(self.actual_data[0,0,:])):
            bmean[t] = np.mean(self.actual_data[self._xRange[0]:self._xRange[1],
                            self._yRange[0]:self._yRange[1], t])
        self.boxmean_line.set_ydata(bmean)
        self.boxmean_line.set_xdata(range(*self._timeRange))
        self.boxmean_line2.set_ydata(bmean[self._timeRange[0]:self._timeRange[1]])
        self.boxmean_line2.set_xdata(range(*self._timeRange))
    def _updateMeanLine(self):
        tmean = np.zeros(len(self.actual_data[0,0,:]))
        for t in range(len(self.actual_data[0,0,:])):
            tmean[t] = np.mean(self.actual_data[:,:, t])
        self.totmean_line.set_xdata(range(*self._timeRange ))
        self.totmean_line.set_ydata(tmean)
    def _updateTimeVerLine(self, tnew):
        if self.time_ver_line is not None: 
            self.time_ver_line.set_xdata([tnew, tnew])
        else:
            ymin, ymax = self.axTime.get_ylim()
            self.time_ver_line, = self.axTime.plot([tnew, tnew], [ymin, ymax], '-', color='black',linewidth=1)
    def _updateTimeLine(self, xnew, ynew):
        xrange = range(self._timeRange[0], self._timeRange[1])
        if self.time_line is not None:
            self.time_line.set_xdata(xrange)
            self.time_line.set_ydata(self.actual_data[ynew, xnew , :])
        else:
            yrange = self.actual_data[ynew, xnew , :]
            
            self.time_line, = self.axTime.plot(xrange, yrange, color='g', linewidth=1.5, label="Point")
            self.axTime.legend()
            
    def _updateDetailverLine(self, xnew):
        if self.detail_ver_line is not None:
            self.detail_ver_line.set_xdata([xnew, xnew])
        else:
            ymin, ymax = self.axDetail.get_ylim()
            self.detail_ver_line, = self.axDetail.plot([xnew, xnew], [ymin, ymax], '-', color='black',linewidth=1)
    def _updateDetailLine(self, ynew, tnew):
        xrange = range(*self._yRange )
        if self.detail_line is not None:
            self.detail_line.set_xdata(xrange)
            self.detail_line.set_ydata(self.actual_data[ynew, : , tnew])
        else:
            yrange = self.actual_data[ynew, : , tnew]
            self.detail_line, = self.axDetail.plot(xrange, yrange)
            
    def _updateColumnverLine(self, ynew):
        if self.column_ver_line is not None:
            self.column_ver_line.set_xdata([ynew, ynew])
        else:
            ymin, ymax = self.axColumn.get_ylim()
            self.column_ver_line, = self.axColumn.plot([ynew, ynew], [ymin, ymax], '-', color='black',linewidth=1)
    def _updateColumnLine(self, xnew, tnew):
        yrange = range(*self._xRange )
        if self.column_line is not None:
            self.column_line.set_xdata(yrange)
            self.column_line.set_ydata(self.actual_data[:, xnew , tnew])
        else:
            xrange = self.actual_data[:, xnew , tnew]
            self.column_line, = self.axColumn.plot(yrange, xrange)
    def _updateVerLine(self, xnew):
        if self.ver_line is not None:
            self.ver_line.set_xdata([xnew, xnew])
        else:
            ymin, ymax = self.axes.get_ylim()
            self.ver_line, = self.axes.plot([xnew, xnew], [ymin, ymax], '-', color='black',linewidth=1)
    def _updateHorLine(self, ynew):
        if self.hor_line is not None:
            self.hor_line.set_ydata([ynew, ynew])
        else:
            xmin, xmax = self.axes.get_xlim()
            self.hor_line, = self.axes.plot([xmin, xmax], [ynew, ynew], '-', color='black',linewidth=1)
    def _reScaleTemperature(self, min_temp, max_temp):
        self.img.set_clim(min_temp, max_temp)
        self.axDetail.set_ylim([min_temp, max_temp])
        self.axColumn.set_ylim([min_temp, max_temp])
        self.axTime.set_ylim([min_temp, max_temp])
        if self.detail_ver_line is not None:
            self.detail_ver_line.set_ydata([min_temp, max_temp])
        if self.column_ver_line is not None:
            self.column_ver_line.set_ydata([min_temp, max_temp])
        
        self.time_ver_line.set_ydata([min_temp, max_temp])
        ticksize = np.max((1, int(round((int(np.ceil(max_temp))-int(min_temp))/10.0))))
        self.cbar.set_ticks(range(int(min_temp), int(np.ceil(max_temp)),ticksize))
        self._updateLabels()

    def _saveQFunc(self, event):
        self.measurement.saveQ()
        
    
    def on_press(self, event):
        t = None
        if (event.key == "right"):
            t = self.current_time + 1
        if (event.key == "left"):
            t = self.current_time - 1 
        
        if (t != None):
            self.update(t)
    
    def on_mouse_press_main(self, event):
        self._updatePos(round(event.xdata), round(event.ydata))
    
    def on_mouse_press_detail(self, event):
        self._updatePos(round(event.xdata), self.detail_pos[1])

    def on_mouse_press_column(self, event):
        self._updatePos(self.detail_pos[0], round(event.xdata))
        
    def on_mouse_press_time(self, event):
        self._updateTime(round(event.xdata))
        
        
    def createSubFigure(self, axes):
        ftemp = plt.figure()
        ax = ftemp.add_subplot("111")
        if axes == self.axes:
            ax.imshow(self.actual_data[:,:,self.current_time], interpolation='none', aspect = "auto")
        elif axes == self.axDetail and self.detail_line is not None:
            xrange = range(*self._yRange)
            yrange = self.actual_data[self.detail_pos[1], : , self.current_time]
            ax.set_ylabel("Temp")
            ax.set_xlabel("Horizontal position")
            ax.plot(xrange, yrange)
        elif axes == self.axColumn and self.column_line is not None:
            xrange = range(*self._xRange)
            yrange = self.actual_data[:, self.detail_pos[0] , self.current_time]
            ax.set_ylabel("Temp")
            ax.set_xlabel("Vertical position")
            ax.plot(xrange,yrange)
        elif axes == self.axTime:
            trange = range(*self._timeRange)
            if self.time_line is not None:
                yrange = self.actual_data[self.detail_pos[1], self.detail_pos[0] , :]
                ax.plot(trange,yrange, color='g', linewidth=1.5, label="Point")
            bmean = np.zeros(self._timeRange[1] - self._timeRange[0])
            
            for t in range(self._timeRange[0], self._timeRange[1]):
                bmean[t-self._timeRange[0]] = np.mean(self.actual_data[self._xRange[0]:self._xRange[1],
                                                                self._yRange[0]:self._yRange[1],
                                                                t])
            
            tmean = np.zeros(self.actual_data.shape[2])
            for t in range(0, self.actual_data.shape[2]):
                bmean[t] = np.mean(self.actual_data[:,:,t])
            
            #ax.plot(trange, tmean, color='b', linewidth=1, label="Image mean")
    
            ax.plot(trange, bmean, color='r', linewidth=1, label="Box mean")
            ax.plot(trange, bmean, color='r', linewidth=1.5)
            ax.set_ylabel("Temp")
            ax.set_xlabel("Time")
            ax.legend()
        ftemp.axes.append(axes)
        plt.show()
        
    def on_mouse_press(self, event):
        if event.button == 1:
            if event.inaxes == self.axes: self.on_mouse_press_main(event)
            elif event.inaxes == self.axDetail and self.detail_line is not None: self.on_mouse_press_detail(event)
            elif event.inaxes == self.axTime: self.on_mouse_press_time(event)
            elif event.inaxes == self.axColumn and self.column_line is not None: self.on_mouse_press_column(event)
        else:
            if event.inaxes == self.axes or \
                event.inaxes == self.axDetail or \
                event.inaxes == self.axTime or \
                event.inaxes == self.axColumn: 
                self.createSubFigure(event.inaxes)

class lastFrameInterface(object):
    def __init__(self, figure, measurementlist):
        font = {'family' : 'sans serif',
            'size'   : 12}
        fontsmall = {'family' : 'sans serif',
            'size'   : 10}
        mpl.rcParams["axes.labelsize"] = 10
        mpl.rcParams["xtick.labelsize"] = 10
        mpl.rcParams["ytick.labelsize"] = 10
        mpl.rcParams["legend.fontsize"] = 10
        mpl.rcParams["legend.labelspacing"] = 0.3         
        mpl.rcParams["legend.borderpad"] = 0.3
        
        
        self.current_index = 0
        self.datalist = measurementlist

        self.actual_data = self.datalist[self.current_index].data
        
        
        self.display = figure
        self.current_time = 0
        self.gs = mpl.gridspec.GridSpec(4,4, width_ratios=[50,1,20,10], height_ratios=[30,20,20,5])
        
        self._xRange = (0, 0+self.actual_data.shape[0])
        self._yRange = (0, 0+self.actual_data.shape[1])

        
        self.axes = self.display.add_subplot(self.gs[0:2, 0])
        self.axColour = self.display.add_subplot(self.gs[0:2,1])
        self.axText = self.display.add_subplot(self.gs[0,-1], axisbg='lightgoldenrodyellow')
        self.axDetail = self.display.add_subplot(self.gs[2, :-1])
        self.axColumn = self.display.add_subplot(self.gs[0:2,2])
        self.axTime = self.display.add_subplot(self.gs[3, :-1])
        #self.gs.tight_layout(self.display)
        self.img = self.axes.imshow(self.actual_data[:,:], interpolation='none', 
                                    extent=(0,self.actual_data.shape[1],
                                            self.actual_data.shape[0], 0
                                            ), aspect="auto")
        m = self.datalist[self.current_index]
        self.point, = self.axes.plot(m.point[0]-m.offsets[0], m.point[1]-m.offsets[1], 'x', color = "white")
        self.axes.set_xlim([0,self.actual_data.shape[1]])
        self.axes.set_ylim([0, self.actual_data.shape[0]])
        self.axes.set_autoscalex_on(False)
        self.axes.set_autoscaley_on(False)
        
        
        min_temp = min(np.amin(m.data) for m in self.datalist)
        max_temp = max(np.amax(m.data) for m in self.datalist)
        self.img.set_clim(min_temp, max_temp)
        #self.maxtime = len(self.actual_data[0,0,:])-1
        
        ticksize = np.max((1, int(round((int(np.ceil(max_temp))-int(min_temp))/10.0))))
        self.cbar = self.display.colorbar(self.img, self.axColour, ticks=range(int(min_temp), int(np.ceil(max_temp)),ticksize))
        #print(self.cbar.ax.get_xticklabels(minor=True))
        #self.cbar.ax.set_xticklabels(np.round(self.cbar.ax.get_xticklabels()))
        
        self.axDetail.set_title("Row Temperature", **font)
        self.axDetail.set_ylabel("Q")
        self.axDetail.set_xlabel("horizontal position")
        self.axDetail.set_ylim([min_temp, max_temp])
        self.axDetail.set_autoscaley_on(False)

        self.axColumn.set_title("Column Temperature", **font)
        self.axColumn.set_ylabel("Q")
        self.axColumn.set_xlabel("vertical position")
        self.axColumn.set_ylim([min_temp, max_temp])
        self.axColumn.set_autoscaley_on(False)
        
        self.detail_pos = (np.nan, np.nan)
        self.hor_line = None
        self.ver_line = None
        self.detail_line = None
        self.detail_ver_line = None
        self.column_line = None
        self.column_ver_line = None
        #self.
        
        self.mean = np.mean(self.actual_data[:,:])
        self.rowmean = 0
        self.val = 0
        self.axText.set_autoscalex_on(False)
        self.axText.set_autoscaley_on(False)
        self.axText.set_xlim([0,1])
        self.axText.set_ylim([0,1])
        self.axText.get_xaxis().set_visible(False)
        self.axText.get_yaxis().set_visible(False)
        txt = "(%i, %i) \n" % self.datalist[self.current_index].offsets
        txt += "(%.0f, %.0f) \n" % self.detail_pos
        txt += "total mean \n    %.4f \n" % self.mean
        txt += "row mean \n    %.4f \n" % self.rowmean
        txt += "Value: %.4f \n" % self.val
        self.Txt = self.axText.text(0.01,1-0.01,txt,verticalalignment='top', **fontsmall)
                

        self.bid = self.display.canvas.mpl_connect('key_press_event', self.on_press)
        self.cid = self.display.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        

    def _updateLabels(self):
        self.mean = np.mean(self.actual_data[:,:])
        if self.detail_line is not None:
            self.rowmean = np.mean(self.actual_data[self.detail_pos[1], :])
            self.val = self.actual_data[self.detail_pos[1], self.detail_pos[0]]
        else:
            self.rowmean = 0
            self.val = 0
        txt = "(%.i, %.i) \n" % self.datalist[self.current_index].offsets
        txt += "pos (%.0f, %.0f) \n" % self.detail_pos
        txt += "total mean \n    %.4f \n" % self.mean
        txt += "row mean \n    %.4f \n" % self.rowmean
        txt += "Value: %.4f \n" % self.val
        self.display.suptitle(self.datalist[self.current_index].filepath)
        self.Txt.set_text(txt);
            
    def update(self, newindex):
        self.current_index = min(len(self.datalist)-1, max(0, newindex))
        m = self.datalist[self.current_index]
        self.actual_data = m.data
        self._updateLabels()
        self.img = self.axes.imshow(self.actual_data, interpolation='none', 
                                    extent=(0,self.actual_data.shape[1],
                                            self.actual_data.shape[0], 0
                                            ), aspect="auto")
        self._xRange = (0, 0+self.actual_data.shape[0])
        self._yRange = (0, 0+self.actual_data.shape[1])
        self.point.set_data(m.point[0]-m.offsets[0], m.point[1]-m.offsets[1])
        self.axes.set_xlim([0,self.actual_data.shape[1]])
        self.axes.set_ylim([0, self.actual_data.shape[0]])
        if self.detail_line is not None:
            self._updateDetailLine(self.detail_pos[1])
        if self.column_line is not None:
            self._updateColumnLine(self.detail_pos[0])
        
        self.display.canvas.draw()
       
        
    def _updatePos(self, xnew, ynew):
        if ynew != self.detail_pos[1]:
            self._updateColumnverLine(ynew)
            self._updateDetailLine(ynew)
        
        if xnew != self.detail_pos[0]:
            self._updateDetailverLine(xnew)
            self._updateColumnLine(xnew)
        
        
        
        
        if xnew != self.detail_pos[0]:
            self._updateVerLine(xnew)
        if ynew != self.detail_pos[1]:
            self._updateHorLine(ynew)

            
        self.detail_pos = (xnew, ynew)
        self._updateLabels()
        self.display.canvas.draw()

           

            
    def _updateDetailverLine(self, xnew):
        if self.detail_ver_line is not None:
            self.detail_ver_line.set_xdata([xnew, xnew])
        else:
            ymin, ymax = self.axDetail.get_ylim()
            self.detail_ver_line, = self.axDetail.plot([xnew, xnew], [ymin, ymax], '-', color='black',linewidth=1)
    def _updateDetailLine(self, ynew):
        xrange = range(*self._yRange )
        if self.detail_line is not None:
            self.detail_line.set_xdata(xrange)
            self.detail_line.set_ydata(self.actual_data[ynew, :])
        else:
            yrange = self.actual_data[ynew, :]
            self.detail_line, = self.axDetail.plot(xrange, yrange)
            
    def _updateColumnverLine(self, ynew):
        if self.column_ver_line is not None:
            self.column_ver_line.set_xdata([ynew, ynew])
        else:
            ymin, ymax = self.axColumn.get_ylim()
            self.column_ver_line, = self.axColumn.plot([ynew, ynew], [ymin, ymax], '-', color='black',linewidth=1)
    def _updateColumnLine(self, xnew):
        yrange = range(*self._xRange )
        if self.column_line is not None:
            self.column_line.set_xdata(yrange)
            self.column_line.set_ydata(self.actual_data[:, xnew])
        else:
            xrange = self.actual_data[:, xnew ]
            self.column_line, = self.axColumn.plot(yrange, xrange)
    def _updateVerLine(self, xnew):
        if self.ver_line is not None:
            self.ver_line.set_xdata([xnew, xnew])
        else:
            ymin, ymax = self.axes.get_ylim()
            self.ver_line, = self.axes.plot([xnew, xnew], [ymin, ymax], '-', color='black',linewidth=1)
    def _updateHorLine(self, ynew):
        if self.hor_line is not None:
            self.hor_line.set_ydata([ynew, ynew])
        else:
            xmin, xmax = self.axes.get_xlim()
            self.hor_line, = self.axes.plot([xmin, xmax], [ynew, ynew], '-', color='black',linewidth=1)
    def _reScaleTemperature(self, min_temp, max_temp):
        self.img.set_clim(min_temp, max_temp)
        self.axDetail.set_ylim([min_temp, max_temp])
        self.axColumn.set_ylim([min_temp, max_temp])
        self.axTime.set_ylim([min_temp, max_temp])
        if self.detail_ver_line is not None:
            self.detail_ver_line.set_ydata([min_temp, max_temp])
        if self.column_ver_line is not None:
            self.column_ver_line.set_ydata([min_temp, max_temp])
        
        self.time_ver_line.set_ydata([min_temp, max_temp])
        ticksize = np.max((1, int(round((int(np.ceil(max_temp))-int(min_temp))/10.0))))
        self.cbar.set_ticks(range(int(min_temp), int(np.ceil(max_temp)),ticksize))
        self._updateLabels()

    
    
    def on_press(self, event):
        t = None
        if (event.key == "right"):
            t = self.current_index + 1
        if (event.key == "left"):
            t = self.current_index - 1 
        
        if (t != None):
            self.update(t)
    
    def on_mouse_press_main(self, event):
        self._updatePos(round(event.xdata), round(event.ydata))
    
    def on_mouse_press_detail(self, event):
        self._updatePos(round(event.xdata), self.detail_pos[1])

    def on_mouse_press_column(self, event):
        self._updatePos(self.detail_pos[0], round(event.xdata))
        

        
        
        
    def on_mouse_press(self, event):
        if event.button == 1:
            if event.inaxes == self.axes: self.on_mouse_press_main(event)
            elif event.inaxes == self.axDetail and self.detail_line is not None: self.on_mouse_press_detail(event)
            elif event.inaxes == self.axTime: self.on_mouse_press_time(event)
            elif event.inaxes == self.axColumn and self.column_line is not None: self.on_mouse_press_column(event)
        #else:
        #    if event.inaxes == self.axes or \
        #        event.inaxes == self.axDetail or \
        #        event.inaxes == self.axTime or \
        #        event.inaxes == self.axColumn: 
        #        self.createSubFigure(event.inaxes)


def convNameDataDetail(name):
    tok = name.split("_")
    j = next(j for j,v in enumerate(tok) if v == "r" or v == "l" or v[-3:] == "bar" or v[:3] == "run")
    shape = "_".join(tok[:j])
    i = 1
    l = len(tok)
    DocsData = namedtuple("DocsData", ["shape","height", "size", "pressure"])
    size = 0;
    height = 0;
    pressure = 0;
    while i<l:
        curtok = tok[i]
        if curtok == "h" and i < (l-1):
            height = int(tok[i+1])
            i+=1
        elif (curtok == "r" or curtok == "l") and i < (l-1):
            size = float(tok[i+1])
            while size > 10:
                size /= 10
            i+=1
        elif curtok[-3:] == "bar":
            pressure = int(curtok[:-3])
        i+=1
    if shape == "half_sphere":
        height = size
    dat = DocsData(shape=shape, size=size, height=height, pressure=pressure) 
    return dat


def convNameData(fname, LE):
    k = fname.rfind(".")
    if k > 0:
        name = fname[:k]
    else:
        name = fname
    #unique typos
    s = "half_spherer"
    if name.startswith(s):
        name = "half_sphere_" + name[len(s)-1:]

    if name:
        dat = convNameDataDetail(name)
        return Measurements.measurement(fname, shape = dat.shape, height = dat.height, size = dat.size, pressure = dat.pressure, LE = LE)
    raise ValueError("Badly formatted name %s" % name)

    

def loadAllMeasurementsGoogleDocs(allmeasurements, login, sheetkey, Verbose = False):
    print(" --- Loading measurement from google docs --- ")
    sh = login.open_by_key(sheetkey)
    worksheets = sh.worksheets()
    for ws in worksheets:
        if Verbose:
            print("Sheet", ws.title)
        try:
            LE = int(ws.title)
        except ValueError as e:
            print("Undefined sheet", ws.title)
        else:
            listoflists = ws.get_all_values()
            for row in listoflists[1:]:
                if row and row[0]:
                    name = row[0]
                    try:
                        m = convNameData(name, LE)
                    except ValueError as e:
                        print ("Badly formatted filename", fname)
                    else:
                        allmeasurements.add_measurement(m)
                        if len(row) >= 7:
                            try:
                                slice = ([int(v) for v in row[1:3]], [int(v) for v in row[3:5]], [int(v) for v in row[5:7]])
                                m.slice = slice
                            except ValueError as E:
                                pass
                        if len(row) >= 9:
                            try:
                                p = tuple(float(v) for v in row[7:9])
                                m.point = p
                            except ValueError as E:
                                pass
                        if len(row) >= 10:
                            try:
                                s = float(row[9])
                                m.scale = s
                            except ValueError as E:
                                pass
                                
                        if Verbose:
                            print("Loading measurement", m)
def loadAllMeasurementsGoogleDocsAdaptiveSlicing(allmeasurements, login, sheetkey, Verbose = False, vertical = 15, trailing = 70, pre = 10, undisturbed = (30,50)):
    print(" --- Loading measurement from google docs --- ")
    sh = login.open_by_key(sheetkey)
    worksheets = sh.worksheets()
    for ws in worksheets:
        if Verbose:
            print("Sheet", ws.title)
        try:
            LE = int(ws.title)
        except ValueError as e:
            print("Undefined sheet", ws.title)
        else:
            listoflists = ws.get_all_values()
            for row in listoflists[1:]:
                if row and row[0]:
                    name = row[0]
                    try:
                        m = convNameData(name, LE)
                    except ValueError as e:
                        print ("Badly formatted filename", fname)
                    else:
                                                        
                        if Verbose:
                            print("Loading measurement", m)
                        allmeasurements.add_measurement(m)
                        if len(row) >= 9:
                            try:
                                p = tuple(float(v) for v in row[7:9])
                                m.point = p
                            except ValueError as E:
                                pass
                        if len(row) >= 10:
                            try:
                                s = float(row[9])
                                m.scale = s
                            except ValueError as E:
                                pass
 
                        slice = ([int(m.point[1] - vertical*m.scale) , int(m.point[1] + vertical*m.scale)], 
                                 [int(m.point[0] - trailing*m.scale), int(m.point[0] + pre*m.scale)], 
                                 [int(v) for v in row[5:7]])
                        _undisturbed = ([int(m.point[1] + undisturbed[0]*m.scale), int(m.point[1] + undisturbed[1]*m.scale)], 
                                       [int(m.point[1] - undisturbed[1]*m.scale), int(m.point[1] - undisturbed[0]*m.scale)])
                        m.slice = slice
                        m.undisturbed = _undisturbed
                        if Verbose:
                            print("Slice", m.slice)
                            print("Undisturbed", m.undisturbed)
def loadAllMeasurementsGoogleDocsNoSlicing(allmeasurements, login, sheetkey, Verbose = False):
    print(" --- Loading measurement from google docs --- ")
    sh = login.open_by_key(sheetkey)
    worksheets = sh.worksheets()
    for ws in worksheets:
        if Verbose:
            print("Sheet", ws.title)
        try:
            LE = int(ws.title)
        except ValueError as e:
            print("Undefined sheet", ws.title)
        else:
            listoflists = ws.get_all_values()
            for row in listoflists[1:]:
                if row and row[0]:
                    name = row[0]
                    try:
                        m = convNameData(name, LE)
                    except ValueError as e:
                        print ("Badly formatted filename", fname)
                    else:
                                                        
                        if Verbose:
                            print("Loading measurement", m)
                        allmeasurements.add_measurement(m)
                        if len(row) >= 9:
                            try:
                                p = tuple(float(v) for v in row[7:9])
                                m.point = p
                            except ValueError as E:
                                pass
                        if len(row) >= 10:
                            try:
                                s = float(row[9])
                                m.scale = s
                            except ValueError as E:
                                pass





def findMeasurementDataFromFilename(all_measurements, fname, leading_edge = slice(None, None, None)):
    k = fname.rfind(".")
    if k > 0:
        name = fname[:k]
    else:
        name = fname
    if name:
        try:
            dat = convNameDataDetail(name)
        except ValueError as e:
            return None
        else:
            return all_measurements.get_measurements(shape = dat.shape, size = dat.size, height = dat.height, pressure = dat.pressure, LE = leading_edge, fname = fname)
            
    return None               
                
                
    #Measurements.measurements_list.add(Measurements.measurement())


def main_loadgoogle(allMeasurements):
    
    
    t = 0.00039999998989515007 
    rho = 0.0004495114372566317 
    c = 1005 
    k = 1.4 
    dt1 = np.array([ 0., 0.00307481, -0.005996,    0.00522731, -0.00061496,  0.43048938, \
                   0.40421411,  0.15344358,  0.18690944,  0.2201325,   0.20294551,  0.19625714, \
                   0.20864527,  0.22018654,  0.24443638,  0.228085,    0.23038194,  0.26600715, \
                   0.25055069,  0.24066542,  0.27106,     0.25178359])
    
    
    gc = gspread.login("D07TAS", "hypersonicroughness")
        
    
    

    loadAllMeasurementsGoogleDocsAdaptiveSlicing(allMeasurements, gc, "1Xw_EXTmFHbKhSj4OGKRff0ClR-_QSO_V_YLUTaOD_GM")
    #loadAllMeasurementsGoogleDocsNoSlicing(allMeasurements, gc, "1Xw_EXTmFHbKhSj4OGKRff0ClR-_QSO_V_YLUTaOD_GM")
    print("---------------------")

def main_load_data(test_measurements):
    for m in test_measurements:
        m.load()
        m.readSlice()
def main_show_measurements(test_measurements):
    datalist = []
    displist = []
    for m in test_measurements:
        fmain = plt.figure()
        fmain.suptitle(m.filepath)
        disp = interface(fmain, m, m.data.data)
        displist.append(disp)
    plt.show()
    return (datalist, displist)
def main_show_reduced_measurements(reduced_measurements):
    fmain = plt.figure()
    disp = lastFrameInterface(fmain, reduced_measurements)
    plt.show()
    return disp

def main_calculate_and_save_q(test_measurements):
    for m in test_measurements:
        print("-----",m,"-----")
        m.saveQ()
def main_calculate_and_save_q_all_memory_efficient(test_measurements):
    t = len(test_measurements)
    i = 0
    for m in test_measurements:
        i+=1
        print("-----",m,i,t,"-----")
        m.load()
        if m.data is not None:
            m.readSlice()
            m.data.ml_q
            m.saveQ()
        m.unload()
        

def maxAverage(data):
    t = np.mean(data, 0)
    t = np.mean(t,0)
    print(t.shape)
    print(t, np.argmax(t))
    return np.argmax(t)

def main_keep_only_last_q(test_measurements):
    simple_measurements = []
    for m in test_measurements:
        print("-----",m,"-----")
        l = False
        if not m.isLoaded():
            l = True
            m.load()
            m.readSlice()
        m.data.ml_q[:,:,-1] = analyses.addGaussianBlurAdv(m.data.ml_q[:,:,-1], m.scale*0.25,2)            
        tdat = m.data.ml_binK
        sm = Measurements.simple_measurement(m, tdat)
        simple_measurements.append(sm)
        
        if l:
            m.unload()
    return simple_measurements
    
        

        
def addGaussianBlur(data):
    gauss = 1/16*np.array([[1,2,1],[2,4,2],[1,2,1]])
    return ndimage.convolve(data, gauss, mode = "nearest")


    

def addGaussianBlurAdv(data, sigma, maxradius):
    #r = np.array([[2,1,2],[1,0,1],[2,1,2]])
    r = np.zeros((maxradius*2+1,maxradius*2+1))
    
    for ind, _ in np.ndenumerate(r):
        r[ind] = sum((i - maxradius)**2 for i in ind)
    gauss = gaussian2d(r, sigma)
    print(gauss)
    gauss = 1/np.sum(gauss) * gauss
    
    return ndimage.convolve(data, gauss, mode = "nearest")

def syncFilter(data, cutoff, maxradius):
    r = np.zeros((maxradius*2+1,maxradius*2+1))
    for ind, _ in np.ndenumerate(r):
        r[ind] = cutoff*np.sqrt(sum((i - maxradius)**2 for i in ind))
    sincfilter = np.sinc(r)
    sincfilter= 1/np.sum(sincfilter) * sincfilter
    return ndimage.convolve(data, sincfilter, mode = "nearest")

def addBoxBlur(data):
    blur = 1/9*np.array([[1,1,1],[1,1,1],[1,1,1]])
    return ndimage.convolve(data, blur, mode = "nearest")



def onGoingAnalysis(test_measurements):
    simple_measurements = main_keep_only_last_q(test_measurements)
    for m in simple_measurements:
        line = analyses.getColumnLine(m.data)
        rel_point = m.to_relative_pos(m.point)
        print(m)
        
        #upstream only
        tmp = m.data[:,rel_point[0]:]
        tmpline = line[rel_point[0]:]
        pos = m.to_absolute_pos(np.unravel_index(tmp.T.argmax(), tmp.T.shape))
        pos = m.to_point_pos(pos)
        print("   maximum (upstream)", np.amax(tmp), pos)
        pos = line.argmax() + m.offsets[0] - m.point[0]
        print("   maximum column (upstream)", np.amax(line),line.argmax(), pos)
        
        
        
        #trailing point only        
        tmp = m.data[:,:rel_point[0]]
        tmpline = line[:rel_point[0]]
        pos = m.to_absolute_pos(np.unravel_index(tmp.T.argmax(), tmp.T.shape))
        pos = m.to_point_pos(pos)
        print("   maximum (trail)", np.amax(tmp), pos)
        pos = line.argmax() + m.offsets[0] - m.point[0]
        print("   maximum column (trail)", np.amax(line),line.argmax(), pos)
        
        
    main_show_reduced_measurements(simple_measurements)


        
def main():


    
    filename = "half_sphere_r_2_100bar_run2.ptw"
    filename2 = "cylinder_r_2_h_2_100bar_run2.ptw"
    allMeasurements = Measurements.all_measurements(("H:/AE2223-II/3cm_LE/","H:/AE2223-II/6cm_LE/"))
    main_loadgoogle(allMeasurements)
    
    print(len(allMeasurements))
    print("loaded google docs")
    #test_measurements = allMeasurements.get_measurements(LE=60)
    #test_measurements = allMeasurements.get_measurements(fname = filename,LE=30)
    #test_measurements = allMeasurements.get_measurements(fname = filename,LE=60)
    #test_measurements = allMeasurements.get_measurements("cylinder",2.85,LE=30)
    test_measurements = allMeasurements.get_measurements(size=2, height=6, pressure=100)
    """
        Item access
        @param shape: shape slice
        @param size: size slice
        @param height: height slice
        @param pressure: pressure slice
        @param LE: leading edge slice
        @param fname: filepath. If fname is given, loads the specific filenames and ignores other params  
        @return: List of measurements fitting criteria
    """
    
    print(len(test_measurements))
    
   
    
    
    reduced_measurements = main_keep_only_last_q(test_measurements)
    main_show_reduced_measurements(reduced_measurements)
    #test_measurements.extend(allMeasurements.get_measurements( size=2, height=2, pressure=100, LE=60)  )
    """
        Item access
        @param shape: shape slice
        @param size: size slice
        @param height: height slice
        @param pressure: pressure slice
        @param LE: leading edge slice
        @param fname: filepath. If fname is given, loads the specific filenames and ignores other params  
        @return: List of measurements fitting criteria
    """
    
    

        
    
    

    print("end")


if (__name__ == "__main__"):
    main()
