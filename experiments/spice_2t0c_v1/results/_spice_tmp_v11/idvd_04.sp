* dc_idvd_v1.sp
* 2T0C Id-Vd DC sweep at Vg=0.4, 1.2, 2.0V
* Using v1 compact model from igzo_2t0c_v1.lib

.include ../models/igzo_2t0c_v1.lib

* circuit
VD d 0 DC 0
VG g 0 DC 0.4.4
X1 d g 0 IGZO_2T0C_V1

* DC sweep Vd from 0 to 3 V, step 0.05 V
.DC VD 0 3 0.05

.control
set filetype=ascii
run
print V(g) V(d) i(VD)
.endc

.END
