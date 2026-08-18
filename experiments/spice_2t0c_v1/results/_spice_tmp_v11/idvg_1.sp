* dc_idvg_v1.sp
* 2T0C Id-Vg DC sweep at Vd=0.1V and Vd=1V
* Using v1 compact model from igzo_2t0c_v1.lib

.include ../models/igzo_2t0c_v1.lib

* circuit
VD d 0 DC 1.0.1
VG g 0 DC 0
X1 d g 0 IGZO_2T0C_V1

* DC sweep Vg from -1 to 2 V, step 0.05 V
.DC VG -1 2 0.05

.control
set filetype=ascii
run
print V(g) V(d) i(VD)
.endc

.END
