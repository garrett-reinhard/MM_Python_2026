# -*- coding: utf-8 -*-

# For testing/debugging QM Control components with iPython:
# launch windows powershell
# cd "C:\Users\John Price\Q Mag Code\qmcontrol" or equivalent
# launch ipython
#    In[1]: run ipy
#    In[2]: tc.get_TA1(si)  # etc...
#    In[3]: si.SendExt485(b'testing')
#    In[4]: fred = si.ReceiveExt485()
#    etc.

import numpy as np
import qmcontrol.host_interface as hi
import qmcontrol.shim_system as ss
import qmcontrol.temp_ctrl as tc
import qmcontrol.ext485 as ex4

si=hi.SpectrometerInterface(configure=True, verbose=True)
