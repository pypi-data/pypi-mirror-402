import os
import Dans_Diffraction as dif
import numpy as np
import traceback

try:
    os.mkdir('testdata')
except :
    print(traceback.format_exc())

xtl = dif.Crystal()
xtl.Cell.a = 4.7; xtl.Cell.b = 4.7; xtl.Cell.c = 5.7
xtl.Scatter.setup_scatter(wavelength_a=0.3, powder_units='q', min_twotheta=2, max_twotheta=10)
ct = 0
s = 1
for i in range(10):
    ct+=1
    xtl.Cell.a += 0.007
    xtl.Cell.b += 0.004
    xtl.Cell.c -= 0.004
    x,y,r = xtl.Scatter.powder(peak_width=0.01+i*0.002, powder_average=True, background=300)
    np.savetxt(f'testdata/test2d_{ct:02}.xy', np.transpose([x[::s],y[::s]]), fmt='%12.5e', header='17/03/2025 17:54:54')
for i in range(10):
    ct+=1
    xtl.Cell.a -= 0.003
    xtl.Cell.b += 0.003
    x,y,r = xtl.Scatter.powder(peak_width=0.03+i*0.001, powder_average=True, background=300)
    np.savetxt(f'testdata/test2d_{ct:02}.xy', np.transpose([x[::s],y[::s]]), fmt='%12.5e', header='17/03/2025 17:54:54')

print(os.listdir('testdata'))