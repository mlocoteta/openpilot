#include "pose.h"

namespace {
#define DIM 18
#define EDIM 18
#define MEDIM 18
typedef void (*Hfun)(double *, double *, double *);
const static double MAHA_THRESH_4 = 7.814727903251177;
const static double MAHA_THRESH_10 = 7.814727903251177;
const static double MAHA_THRESH_13 = 7.814727903251177;
const static double MAHA_THRESH_14 = 7.814727903251177;

/******************************************************************************
 *                      Code generated with SymPy 1.14.0                      *
 *                                                                            *
 *              See http://www.sympy.org/ for more information.               *
 *                                                                            *
 *                         This file is part of 'ekf'                         *
 ******************************************************************************/
void err_fun(double *nom_x, double *delta_x, double *out_5807655181837607214) {
   out_5807655181837607214[0] = delta_x[0] + nom_x[0];
   out_5807655181837607214[1] = delta_x[1] + nom_x[1];
   out_5807655181837607214[2] = delta_x[2] + nom_x[2];
   out_5807655181837607214[3] = delta_x[3] + nom_x[3];
   out_5807655181837607214[4] = delta_x[4] + nom_x[4];
   out_5807655181837607214[5] = delta_x[5] + nom_x[5];
   out_5807655181837607214[6] = delta_x[6] + nom_x[6];
   out_5807655181837607214[7] = delta_x[7] + nom_x[7];
   out_5807655181837607214[8] = delta_x[8] + nom_x[8];
   out_5807655181837607214[9] = delta_x[9] + nom_x[9];
   out_5807655181837607214[10] = delta_x[10] + nom_x[10];
   out_5807655181837607214[11] = delta_x[11] + nom_x[11];
   out_5807655181837607214[12] = delta_x[12] + nom_x[12];
   out_5807655181837607214[13] = delta_x[13] + nom_x[13];
   out_5807655181837607214[14] = delta_x[14] + nom_x[14];
   out_5807655181837607214[15] = delta_x[15] + nom_x[15];
   out_5807655181837607214[16] = delta_x[16] + nom_x[16];
   out_5807655181837607214[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_8974761284027602384) {
   out_8974761284027602384[0] = -nom_x[0] + true_x[0];
   out_8974761284027602384[1] = -nom_x[1] + true_x[1];
   out_8974761284027602384[2] = -nom_x[2] + true_x[2];
   out_8974761284027602384[3] = -nom_x[3] + true_x[3];
   out_8974761284027602384[4] = -nom_x[4] + true_x[4];
   out_8974761284027602384[5] = -nom_x[5] + true_x[5];
   out_8974761284027602384[6] = -nom_x[6] + true_x[6];
   out_8974761284027602384[7] = -nom_x[7] + true_x[7];
   out_8974761284027602384[8] = -nom_x[8] + true_x[8];
   out_8974761284027602384[9] = -nom_x[9] + true_x[9];
   out_8974761284027602384[10] = -nom_x[10] + true_x[10];
   out_8974761284027602384[11] = -nom_x[11] + true_x[11];
   out_8974761284027602384[12] = -nom_x[12] + true_x[12];
   out_8974761284027602384[13] = -nom_x[13] + true_x[13];
   out_8974761284027602384[14] = -nom_x[14] + true_x[14];
   out_8974761284027602384[15] = -nom_x[15] + true_x[15];
   out_8974761284027602384[16] = -nom_x[16] + true_x[16];
   out_8974761284027602384[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_7615318893377638193) {
   out_7615318893377638193[0] = 1.0;
   out_7615318893377638193[1] = 0.0;
   out_7615318893377638193[2] = 0.0;
   out_7615318893377638193[3] = 0.0;
   out_7615318893377638193[4] = 0.0;
   out_7615318893377638193[5] = 0.0;
   out_7615318893377638193[6] = 0.0;
   out_7615318893377638193[7] = 0.0;
   out_7615318893377638193[8] = 0.0;
   out_7615318893377638193[9] = 0.0;
   out_7615318893377638193[10] = 0.0;
   out_7615318893377638193[11] = 0.0;
   out_7615318893377638193[12] = 0.0;
   out_7615318893377638193[13] = 0.0;
   out_7615318893377638193[14] = 0.0;
   out_7615318893377638193[15] = 0.0;
   out_7615318893377638193[16] = 0.0;
   out_7615318893377638193[17] = 0.0;
   out_7615318893377638193[18] = 0.0;
   out_7615318893377638193[19] = 1.0;
   out_7615318893377638193[20] = 0.0;
   out_7615318893377638193[21] = 0.0;
   out_7615318893377638193[22] = 0.0;
   out_7615318893377638193[23] = 0.0;
   out_7615318893377638193[24] = 0.0;
   out_7615318893377638193[25] = 0.0;
   out_7615318893377638193[26] = 0.0;
   out_7615318893377638193[27] = 0.0;
   out_7615318893377638193[28] = 0.0;
   out_7615318893377638193[29] = 0.0;
   out_7615318893377638193[30] = 0.0;
   out_7615318893377638193[31] = 0.0;
   out_7615318893377638193[32] = 0.0;
   out_7615318893377638193[33] = 0.0;
   out_7615318893377638193[34] = 0.0;
   out_7615318893377638193[35] = 0.0;
   out_7615318893377638193[36] = 0.0;
   out_7615318893377638193[37] = 0.0;
   out_7615318893377638193[38] = 1.0;
   out_7615318893377638193[39] = 0.0;
   out_7615318893377638193[40] = 0.0;
   out_7615318893377638193[41] = 0.0;
   out_7615318893377638193[42] = 0.0;
   out_7615318893377638193[43] = 0.0;
   out_7615318893377638193[44] = 0.0;
   out_7615318893377638193[45] = 0.0;
   out_7615318893377638193[46] = 0.0;
   out_7615318893377638193[47] = 0.0;
   out_7615318893377638193[48] = 0.0;
   out_7615318893377638193[49] = 0.0;
   out_7615318893377638193[50] = 0.0;
   out_7615318893377638193[51] = 0.0;
   out_7615318893377638193[52] = 0.0;
   out_7615318893377638193[53] = 0.0;
   out_7615318893377638193[54] = 0.0;
   out_7615318893377638193[55] = 0.0;
   out_7615318893377638193[56] = 0.0;
   out_7615318893377638193[57] = 1.0;
   out_7615318893377638193[58] = 0.0;
   out_7615318893377638193[59] = 0.0;
   out_7615318893377638193[60] = 0.0;
   out_7615318893377638193[61] = 0.0;
   out_7615318893377638193[62] = 0.0;
   out_7615318893377638193[63] = 0.0;
   out_7615318893377638193[64] = 0.0;
   out_7615318893377638193[65] = 0.0;
   out_7615318893377638193[66] = 0.0;
   out_7615318893377638193[67] = 0.0;
   out_7615318893377638193[68] = 0.0;
   out_7615318893377638193[69] = 0.0;
   out_7615318893377638193[70] = 0.0;
   out_7615318893377638193[71] = 0.0;
   out_7615318893377638193[72] = 0.0;
   out_7615318893377638193[73] = 0.0;
   out_7615318893377638193[74] = 0.0;
   out_7615318893377638193[75] = 0.0;
   out_7615318893377638193[76] = 1.0;
   out_7615318893377638193[77] = 0.0;
   out_7615318893377638193[78] = 0.0;
   out_7615318893377638193[79] = 0.0;
   out_7615318893377638193[80] = 0.0;
   out_7615318893377638193[81] = 0.0;
   out_7615318893377638193[82] = 0.0;
   out_7615318893377638193[83] = 0.0;
   out_7615318893377638193[84] = 0.0;
   out_7615318893377638193[85] = 0.0;
   out_7615318893377638193[86] = 0.0;
   out_7615318893377638193[87] = 0.0;
   out_7615318893377638193[88] = 0.0;
   out_7615318893377638193[89] = 0.0;
   out_7615318893377638193[90] = 0.0;
   out_7615318893377638193[91] = 0.0;
   out_7615318893377638193[92] = 0.0;
   out_7615318893377638193[93] = 0.0;
   out_7615318893377638193[94] = 0.0;
   out_7615318893377638193[95] = 1.0;
   out_7615318893377638193[96] = 0.0;
   out_7615318893377638193[97] = 0.0;
   out_7615318893377638193[98] = 0.0;
   out_7615318893377638193[99] = 0.0;
   out_7615318893377638193[100] = 0.0;
   out_7615318893377638193[101] = 0.0;
   out_7615318893377638193[102] = 0.0;
   out_7615318893377638193[103] = 0.0;
   out_7615318893377638193[104] = 0.0;
   out_7615318893377638193[105] = 0.0;
   out_7615318893377638193[106] = 0.0;
   out_7615318893377638193[107] = 0.0;
   out_7615318893377638193[108] = 0.0;
   out_7615318893377638193[109] = 0.0;
   out_7615318893377638193[110] = 0.0;
   out_7615318893377638193[111] = 0.0;
   out_7615318893377638193[112] = 0.0;
   out_7615318893377638193[113] = 0.0;
   out_7615318893377638193[114] = 1.0;
   out_7615318893377638193[115] = 0.0;
   out_7615318893377638193[116] = 0.0;
   out_7615318893377638193[117] = 0.0;
   out_7615318893377638193[118] = 0.0;
   out_7615318893377638193[119] = 0.0;
   out_7615318893377638193[120] = 0.0;
   out_7615318893377638193[121] = 0.0;
   out_7615318893377638193[122] = 0.0;
   out_7615318893377638193[123] = 0.0;
   out_7615318893377638193[124] = 0.0;
   out_7615318893377638193[125] = 0.0;
   out_7615318893377638193[126] = 0.0;
   out_7615318893377638193[127] = 0.0;
   out_7615318893377638193[128] = 0.0;
   out_7615318893377638193[129] = 0.0;
   out_7615318893377638193[130] = 0.0;
   out_7615318893377638193[131] = 0.0;
   out_7615318893377638193[132] = 0.0;
   out_7615318893377638193[133] = 1.0;
   out_7615318893377638193[134] = 0.0;
   out_7615318893377638193[135] = 0.0;
   out_7615318893377638193[136] = 0.0;
   out_7615318893377638193[137] = 0.0;
   out_7615318893377638193[138] = 0.0;
   out_7615318893377638193[139] = 0.0;
   out_7615318893377638193[140] = 0.0;
   out_7615318893377638193[141] = 0.0;
   out_7615318893377638193[142] = 0.0;
   out_7615318893377638193[143] = 0.0;
   out_7615318893377638193[144] = 0.0;
   out_7615318893377638193[145] = 0.0;
   out_7615318893377638193[146] = 0.0;
   out_7615318893377638193[147] = 0.0;
   out_7615318893377638193[148] = 0.0;
   out_7615318893377638193[149] = 0.0;
   out_7615318893377638193[150] = 0.0;
   out_7615318893377638193[151] = 0.0;
   out_7615318893377638193[152] = 1.0;
   out_7615318893377638193[153] = 0.0;
   out_7615318893377638193[154] = 0.0;
   out_7615318893377638193[155] = 0.0;
   out_7615318893377638193[156] = 0.0;
   out_7615318893377638193[157] = 0.0;
   out_7615318893377638193[158] = 0.0;
   out_7615318893377638193[159] = 0.0;
   out_7615318893377638193[160] = 0.0;
   out_7615318893377638193[161] = 0.0;
   out_7615318893377638193[162] = 0.0;
   out_7615318893377638193[163] = 0.0;
   out_7615318893377638193[164] = 0.0;
   out_7615318893377638193[165] = 0.0;
   out_7615318893377638193[166] = 0.0;
   out_7615318893377638193[167] = 0.0;
   out_7615318893377638193[168] = 0.0;
   out_7615318893377638193[169] = 0.0;
   out_7615318893377638193[170] = 0.0;
   out_7615318893377638193[171] = 1.0;
   out_7615318893377638193[172] = 0.0;
   out_7615318893377638193[173] = 0.0;
   out_7615318893377638193[174] = 0.0;
   out_7615318893377638193[175] = 0.0;
   out_7615318893377638193[176] = 0.0;
   out_7615318893377638193[177] = 0.0;
   out_7615318893377638193[178] = 0.0;
   out_7615318893377638193[179] = 0.0;
   out_7615318893377638193[180] = 0.0;
   out_7615318893377638193[181] = 0.0;
   out_7615318893377638193[182] = 0.0;
   out_7615318893377638193[183] = 0.0;
   out_7615318893377638193[184] = 0.0;
   out_7615318893377638193[185] = 0.0;
   out_7615318893377638193[186] = 0.0;
   out_7615318893377638193[187] = 0.0;
   out_7615318893377638193[188] = 0.0;
   out_7615318893377638193[189] = 0.0;
   out_7615318893377638193[190] = 1.0;
   out_7615318893377638193[191] = 0.0;
   out_7615318893377638193[192] = 0.0;
   out_7615318893377638193[193] = 0.0;
   out_7615318893377638193[194] = 0.0;
   out_7615318893377638193[195] = 0.0;
   out_7615318893377638193[196] = 0.0;
   out_7615318893377638193[197] = 0.0;
   out_7615318893377638193[198] = 0.0;
   out_7615318893377638193[199] = 0.0;
   out_7615318893377638193[200] = 0.0;
   out_7615318893377638193[201] = 0.0;
   out_7615318893377638193[202] = 0.0;
   out_7615318893377638193[203] = 0.0;
   out_7615318893377638193[204] = 0.0;
   out_7615318893377638193[205] = 0.0;
   out_7615318893377638193[206] = 0.0;
   out_7615318893377638193[207] = 0.0;
   out_7615318893377638193[208] = 0.0;
   out_7615318893377638193[209] = 1.0;
   out_7615318893377638193[210] = 0.0;
   out_7615318893377638193[211] = 0.0;
   out_7615318893377638193[212] = 0.0;
   out_7615318893377638193[213] = 0.0;
   out_7615318893377638193[214] = 0.0;
   out_7615318893377638193[215] = 0.0;
   out_7615318893377638193[216] = 0.0;
   out_7615318893377638193[217] = 0.0;
   out_7615318893377638193[218] = 0.0;
   out_7615318893377638193[219] = 0.0;
   out_7615318893377638193[220] = 0.0;
   out_7615318893377638193[221] = 0.0;
   out_7615318893377638193[222] = 0.0;
   out_7615318893377638193[223] = 0.0;
   out_7615318893377638193[224] = 0.0;
   out_7615318893377638193[225] = 0.0;
   out_7615318893377638193[226] = 0.0;
   out_7615318893377638193[227] = 0.0;
   out_7615318893377638193[228] = 1.0;
   out_7615318893377638193[229] = 0.0;
   out_7615318893377638193[230] = 0.0;
   out_7615318893377638193[231] = 0.0;
   out_7615318893377638193[232] = 0.0;
   out_7615318893377638193[233] = 0.0;
   out_7615318893377638193[234] = 0.0;
   out_7615318893377638193[235] = 0.0;
   out_7615318893377638193[236] = 0.0;
   out_7615318893377638193[237] = 0.0;
   out_7615318893377638193[238] = 0.0;
   out_7615318893377638193[239] = 0.0;
   out_7615318893377638193[240] = 0.0;
   out_7615318893377638193[241] = 0.0;
   out_7615318893377638193[242] = 0.0;
   out_7615318893377638193[243] = 0.0;
   out_7615318893377638193[244] = 0.0;
   out_7615318893377638193[245] = 0.0;
   out_7615318893377638193[246] = 0.0;
   out_7615318893377638193[247] = 1.0;
   out_7615318893377638193[248] = 0.0;
   out_7615318893377638193[249] = 0.0;
   out_7615318893377638193[250] = 0.0;
   out_7615318893377638193[251] = 0.0;
   out_7615318893377638193[252] = 0.0;
   out_7615318893377638193[253] = 0.0;
   out_7615318893377638193[254] = 0.0;
   out_7615318893377638193[255] = 0.0;
   out_7615318893377638193[256] = 0.0;
   out_7615318893377638193[257] = 0.0;
   out_7615318893377638193[258] = 0.0;
   out_7615318893377638193[259] = 0.0;
   out_7615318893377638193[260] = 0.0;
   out_7615318893377638193[261] = 0.0;
   out_7615318893377638193[262] = 0.0;
   out_7615318893377638193[263] = 0.0;
   out_7615318893377638193[264] = 0.0;
   out_7615318893377638193[265] = 0.0;
   out_7615318893377638193[266] = 1.0;
   out_7615318893377638193[267] = 0.0;
   out_7615318893377638193[268] = 0.0;
   out_7615318893377638193[269] = 0.0;
   out_7615318893377638193[270] = 0.0;
   out_7615318893377638193[271] = 0.0;
   out_7615318893377638193[272] = 0.0;
   out_7615318893377638193[273] = 0.0;
   out_7615318893377638193[274] = 0.0;
   out_7615318893377638193[275] = 0.0;
   out_7615318893377638193[276] = 0.0;
   out_7615318893377638193[277] = 0.0;
   out_7615318893377638193[278] = 0.0;
   out_7615318893377638193[279] = 0.0;
   out_7615318893377638193[280] = 0.0;
   out_7615318893377638193[281] = 0.0;
   out_7615318893377638193[282] = 0.0;
   out_7615318893377638193[283] = 0.0;
   out_7615318893377638193[284] = 0.0;
   out_7615318893377638193[285] = 1.0;
   out_7615318893377638193[286] = 0.0;
   out_7615318893377638193[287] = 0.0;
   out_7615318893377638193[288] = 0.0;
   out_7615318893377638193[289] = 0.0;
   out_7615318893377638193[290] = 0.0;
   out_7615318893377638193[291] = 0.0;
   out_7615318893377638193[292] = 0.0;
   out_7615318893377638193[293] = 0.0;
   out_7615318893377638193[294] = 0.0;
   out_7615318893377638193[295] = 0.0;
   out_7615318893377638193[296] = 0.0;
   out_7615318893377638193[297] = 0.0;
   out_7615318893377638193[298] = 0.0;
   out_7615318893377638193[299] = 0.0;
   out_7615318893377638193[300] = 0.0;
   out_7615318893377638193[301] = 0.0;
   out_7615318893377638193[302] = 0.0;
   out_7615318893377638193[303] = 0.0;
   out_7615318893377638193[304] = 1.0;
   out_7615318893377638193[305] = 0.0;
   out_7615318893377638193[306] = 0.0;
   out_7615318893377638193[307] = 0.0;
   out_7615318893377638193[308] = 0.0;
   out_7615318893377638193[309] = 0.0;
   out_7615318893377638193[310] = 0.0;
   out_7615318893377638193[311] = 0.0;
   out_7615318893377638193[312] = 0.0;
   out_7615318893377638193[313] = 0.0;
   out_7615318893377638193[314] = 0.0;
   out_7615318893377638193[315] = 0.0;
   out_7615318893377638193[316] = 0.0;
   out_7615318893377638193[317] = 0.0;
   out_7615318893377638193[318] = 0.0;
   out_7615318893377638193[319] = 0.0;
   out_7615318893377638193[320] = 0.0;
   out_7615318893377638193[321] = 0.0;
   out_7615318893377638193[322] = 0.0;
   out_7615318893377638193[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_4539696263163526019) {
   out_4539696263163526019[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_4539696263163526019[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_4539696263163526019[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_4539696263163526019[3] = dt*state[12] + state[3];
   out_4539696263163526019[4] = dt*state[13] + state[4];
   out_4539696263163526019[5] = dt*state[14] + state[5];
   out_4539696263163526019[6] = state[6];
   out_4539696263163526019[7] = state[7];
   out_4539696263163526019[8] = state[8];
   out_4539696263163526019[9] = state[9];
   out_4539696263163526019[10] = state[10];
   out_4539696263163526019[11] = state[11];
   out_4539696263163526019[12] = state[12];
   out_4539696263163526019[13] = state[13];
   out_4539696263163526019[14] = state[14];
   out_4539696263163526019[15] = state[15];
   out_4539696263163526019[16] = state[16];
   out_4539696263163526019[17] = state[17];
}
void F_fun(double *state, double dt, double *out_2543913590993509263) {
   out_2543913590993509263[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_2543913590993509263[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_2543913590993509263[2] = 0;
   out_2543913590993509263[3] = 0;
   out_2543913590993509263[4] = 0;
   out_2543913590993509263[5] = 0;
   out_2543913590993509263[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_2543913590993509263[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_2543913590993509263[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_2543913590993509263[9] = 0;
   out_2543913590993509263[10] = 0;
   out_2543913590993509263[11] = 0;
   out_2543913590993509263[12] = 0;
   out_2543913590993509263[13] = 0;
   out_2543913590993509263[14] = 0;
   out_2543913590993509263[15] = 0;
   out_2543913590993509263[16] = 0;
   out_2543913590993509263[17] = 0;
   out_2543913590993509263[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_2543913590993509263[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_2543913590993509263[20] = 0;
   out_2543913590993509263[21] = 0;
   out_2543913590993509263[22] = 0;
   out_2543913590993509263[23] = 0;
   out_2543913590993509263[24] = 0;
   out_2543913590993509263[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_2543913590993509263[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_2543913590993509263[27] = 0;
   out_2543913590993509263[28] = 0;
   out_2543913590993509263[29] = 0;
   out_2543913590993509263[30] = 0;
   out_2543913590993509263[31] = 0;
   out_2543913590993509263[32] = 0;
   out_2543913590993509263[33] = 0;
   out_2543913590993509263[34] = 0;
   out_2543913590993509263[35] = 0;
   out_2543913590993509263[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_2543913590993509263[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_2543913590993509263[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_2543913590993509263[39] = 0;
   out_2543913590993509263[40] = 0;
   out_2543913590993509263[41] = 0;
   out_2543913590993509263[42] = 0;
   out_2543913590993509263[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_2543913590993509263[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_2543913590993509263[45] = 0;
   out_2543913590993509263[46] = 0;
   out_2543913590993509263[47] = 0;
   out_2543913590993509263[48] = 0;
   out_2543913590993509263[49] = 0;
   out_2543913590993509263[50] = 0;
   out_2543913590993509263[51] = 0;
   out_2543913590993509263[52] = 0;
   out_2543913590993509263[53] = 0;
   out_2543913590993509263[54] = 0;
   out_2543913590993509263[55] = 0;
   out_2543913590993509263[56] = 0;
   out_2543913590993509263[57] = 1;
   out_2543913590993509263[58] = 0;
   out_2543913590993509263[59] = 0;
   out_2543913590993509263[60] = 0;
   out_2543913590993509263[61] = 0;
   out_2543913590993509263[62] = 0;
   out_2543913590993509263[63] = 0;
   out_2543913590993509263[64] = 0;
   out_2543913590993509263[65] = 0;
   out_2543913590993509263[66] = dt;
   out_2543913590993509263[67] = 0;
   out_2543913590993509263[68] = 0;
   out_2543913590993509263[69] = 0;
   out_2543913590993509263[70] = 0;
   out_2543913590993509263[71] = 0;
   out_2543913590993509263[72] = 0;
   out_2543913590993509263[73] = 0;
   out_2543913590993509263[74] = 0;
   out_2543913590993509263[75] = 0;
   out_2543913590993509263[76] = 1;
   out_2543913590993509263[77] = 0;
   out_2543913590993509263[78] = 0;
   out_2543913590993509263[79] = 0;
   out_2543913590993509263[80] = 0;
   out_2543913590993509263[81] = 0;
   out_2543913590993509263[82] = 0;
   out_2543913590993509263[83] = 0;
   out_2543913590993509263[84] = 0;
   out_2543913590993509263[85] = dt;
   out_2543913590993509263[86] = 0;
   out_2543913590993509263[87] = 0;
   out_2543913590993509263[88] = 0;
   out_2543913590993509263[89] = 0;
   out_2543913590993509263[90] = 0;
   out_2543913590993509263[91] = 0;
   out_2543913590993509263[92] = 0;
   out_2543913590993509263[93] = 0;
   out_2543913590993509263[94] = 0;
   out_2543913590993509263[95] = 1;
   out_2543913590993509263[96] = 0;
   out_2543913590993509263[97] = 0;
   out_2543913590993509263[98] = 0;
   out_2543913590993509263[99] = 0;
   out_2543913590993509263[100] = 0;
   out_2543913590993509263[101] = 0;
   out_2543913590993509263[102] = 0;
   out_2543913590993509263[103] = 0;
   out_2543913590993509263[104] = dt;
   out_2543913590993509263[105] = 0;
   out_2543913590993509263[106] = 0;
   out_2543913590993509263[107] = 0;
   out_2543913590993509263[108] = 0;
   out_2543913590993509263[109] = 0;
   out_2543913590993509263[110] = 0;
   out_2543913590993509263[111] = 0;
   out_2543913590993509263[112] = 0;
   out_2543913590993509263[113] = 0;
   out_2543913590993509263[114] = 1;
   out_2543913590993509263[115] = 0;
   out_2543913590993509263[116] = 0;
   out_2543913590993509263[117] = 0;
   out_2543913590993509263[118] = 0;
   out_2543913590993509263[119] = 0;
   out_2543913590993509263[120] = 0;
   out_2543913590993509263[121] = 0;
   out_2543913590993509263[122] = 0;
   out_2543913590993509263[123] = 0;
   out_2543913590993509263[124] = 0;
   out_2543913590993509263[125] = 0;
   out_2543913590993509263[126] = 0;
   out_2543913590993509263[127] = 0;
   out_2543913590993509263[128] = 0;
   out_2543913590993509263[129] = 0;
   out_2543913590993509263[130] = 0;
   out_2543913590993509263[131] = 0;
   out_2543913590993509263[132] = 0;
   out_2543913590993509263[133] = 1;
   out_2543913590993509263[134] = 0;
   out_2543913590993509263[135] = 0;
   out_2543913590993509263[136] = 0;
   out_2543913590993509263[137] = 0;
   out_2543913590993509263[138] = 0;
   out_2543913590993509263[139] = 0;
   out_2543913590993509263[140] = 0;
   out_2543913590993509263[141] = 0;
   out_2543913590993509263[142] = 0;
   out_2543913590993509263[143] = 0;
   out_2543913590993509263[144] = 0;
   out_2543913590993509263[145] = 0;
   out_2543913590993509263[146] = 0;
   out_2543913590993509263[147] = 0;
   out_2543913590993509263[148] = 0;
   out_2543913590993509263[149] = 0;
   out_2543913590993509263[150] = 0;
   out_2543913590993509263[151] = 0;
   out_2543913590993509263[152] = 1;
   out_2543913590993509263[153] = 0;
   out_2543913590993509263[154] = 0;
   out_2543913590993509263[155] = 0;
   out_2543913590993509263[156] = 0;
   out_2543913590993509263[157] = 0;
   out_2543913590993509263[158] = 0;
   out_2543913590993509263[159] = 0;
   out_2543913590993509263[160] = 0;
   out_2543913590993509263[161] = 0;
   out_2543913590993509263[162] = 0;
   out_2543913590993509263[163] = 0;
   out_2543913590993509263[164] = 0;
   out_2543913590993509263[165] = 0;
   out_2543913590993509263[166] = 0;
   out_2543913590993509263[167] = 0;
   out_2543913590993509263[168] = 0;
   out_2543913590993509263[169] = 0;
   out_2543913590993509263[170] = 0;
   out_2543913590993509263[171] = 1;
   out_2543913590993509263[172] = 0;
   out_2543913590993509263[173] = 0;
   out_2543913590993509263[174] = 0;
   out_2543913590993509263[175] = 0;
   out_2543913590993509263[176] = 0;
   out_2543913590993509263[177] = 0;
   out_2543913590993509263[178] = 0;
   out_2543913590993509263[179] = 0;
   out_2543913590993509263[180] = 0;
   out_2543913590993509263[181] = 0;
   out_2543913590993509263[182] = 0;
   out_2543913590993509263[183] = 0;
   out_2543913590993509263[184] = 0;
   out_2543913590993509263[185] = 0;
   out_2543913590993509263[186] = 0;
   out_2543913590993509263[187] = 0;
   out_2543913590993509263[188] = 0;
   out_2543913590993509263[189] = 0;
   out_2543913590993509263[190] = 1;
   out_2543913590993509263[191] = 0;
   out_2543913590993509263[192] = 0;
   out_2543913590993509263[193] = 0;
   out_2543913590993509263[194] = 0;
   out_2543913590993509263[195] = 0;
   out_2543913590993509263[196] = 0;
   out_2543913590993509263[197] = 0;
   out_2543913590993509263[198] = 0;
   out_2543913590993509263[199] = 0;
   out_2543913590993509263[200] = 0;
   out_2543913590993509263[201] = 0;
   out_2543913590993509263[202] = 0;
   out_2543913590993509263[203] = 0;
   out_2543913590993509263[204] = 0;
   out_2543913590993509263[205] = 0;
   out_2543913590993509263[206] = 0;
   out_2543913590993509263[207] = 0;
   out_2543913590993509263[208] = 0;
   out_2543913590993509263[209] = 1;
   out_2543913590993509263[210] = 0;
   out_2543913590993509263[211] = 0;
   out_2543913590993509263[212] = 0;
   out_2543913590993509263[213] = 0;
   out_2543913590993509263[214] = 0;
   out_2543913590993509263[215] = 0;
   out_2543913590993509263[216] = 0;
   out_2543913590993509263[217] = 0;
   out_2543913590993509263[218] = 0;
   out_2543913590993509263[219] = 0;
   out_2543913590993509263[220] = 0;
   out_2543913590993509263[221] = 0;
   out_2543913590993509263[222] = 0;
   out_2543913590993509263[223] = 0;
   out_2543913590993509263[224] = 0;
   out_2543913590993509263[225] = 0;
   out_2543913590993509263[226] = 0;
   out_2543913590993509263[227] = 0;
   out_2543913590993509263[228] = 1;
   out_2543913590993509263[229] = 0;
   out_2543913590993509263[230] = 0;
   out_2543913590993509263[231] = 0;
   out_2543913590993509263[232] = 0;
   out_2543913590993509263[233] = 0;
   out_2543913590993509263[234] = 0;
   out_2543913590993509263[235] = 0;
   out_2543913590993509263[236] = 0;
   out_2543913590993509263[237] = 0;
   out_2543913590993509263[238] = 0;
   out_2543913590993509263[239] = 0;
   out_2543913590993509263[240] = 0;
   out_2543913590993509263[241] = 0;
   out_2543913590993509263[242] = 0;
   out_2543913590993509263[243] = 0;
   out_2543913590993509263[244] = 0;
   out_2543913590993509263[245] = 0;
   out_2543913590993509263[246] = 0;
   out_2543913590993509263[247] = 1;
   out_2543913590993509263[248] = 0;
   out_2543913590993509263[249] = 0;
   out_2543913590993509263[250] = 0;
   out_2543913590993509263[251] = 0;
   out_2543913590993509263[252] = 0;
   out_2543913590993509263[253] = 0;
   out_2543913590993509263[254] = 0;
   out_2543913590993509263[255] = 0;
   out_2543913590993509263[256] = 0;
   out_2543913590993509263[257] = 0;
   out_2543913590993509263[258] = 0;
   out_2543913590993509263[259] = 0;
   out_2543913590993509263[260] = 0;
   out_2543913590993509263[261] = 0;
   out_2543913590993509263[262] = 0;
   out_2543913590993509263[263] = 0;
   out_2543913590993509263[264] = 0;
   out_2543913590993509263[265] = 0;
   out_2543913590993509263[266] = 1;
   out_2543913590993509263[267] = 0;
   out_2543913590993509263[268] = 0;
   out_2543913590993509263[269] = 0;
   out_2543913590993509263[270] = 0;
   out_2543913590993509263[271] = 0;
   out_2543913590993509263[272] = 0;
   out_2543913590993509263[273] = 0;
   out_2543913590993509263[274] = 0;
   out_2543913590993509263[275] = 0;
   out_2543913590993509263[276] = 0;
   out_2543913590993509263[277] = 0;
   out_2543913590993509263[278] = 0;
   out_2543913590993509263[279] = 0;
   out_2543913590993509263[280] = 0;
   out_2543913590993509263[281] = 0;
   out_2543913590993509263[282] = 0;
   out_2543913590993509263[283] = 0;
   out_2543913590993509263[284] = 0;
   out_2543913590993509263[285] = 1;
   out_2543913590993509263[286] = 0;
   out_2543913590993509263[287] = 0;
   out_2543913590993509263[288] = 0;
   out_2543913590993509263[289] = 0;
   out_2543913590993509263[290] = 0;
   out_2543913590993509263[291] = 0;
   out_2543913590993509263[292] = 0;
   out_2543913590993509263[293] = 0;
   out_2543913590993509263[294] = 0;
   out_2543913590993509263[295] = 0;
   out_2543913590993509263[296] = 0;
   out_2543913590993509263[297] = 0;
   out_2543913590993509263[298] = 0;
   out_2543913590993509263[299] = 0;
   out_2543913590993509263[300] = 0;
   out_2543913590993509263[301] = 0;
   out_2543913590993509263[302] = 0;
   out_2543913590993509263[303] = 0;
   out_2543913590993509263[304] = 1;
   out_2543913590993509263[305] = 0;
   out_2543913590993509263[306] = 0;
   out_2543913590993509263[307] = 0;
   out_2543913590993509263[308] = 0;
   out_2543913590993509263[309] = 0;
   out_2543913590993509263[310] = 0;
   out_2543913590993509263[311] = 0;
   out_2543913590993509263[312] = 0;
   out_2543913590993509263[313] = 0;
   out_2543913590993509263[314] = 0;
   out_2543913590993509263[315] = 0;
   out_2543913590993509263[316] = 0;
   out_2543913590993509263[317] = 0;
   out_2543913590993509263[318] = 0;
   out_2543913590993509263[319] = 0;
   out_2543913590993509263[320] = 0;
   out_2543913590993509263[321] = 0;
   out_2543913590993509263[322] = 0;
   out_2543913590993509263[323] = 1;
}
void h_4(double *state, double *unused, double *out_8982992753369428231) {
   out_8982992753369428231[0] = state[6] + state[9];
   out_8982992753369428231[1] = state[7] + state[10];
   out_8982992753369428231[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_1965697165790759737) {
   out_1965697165790759737[0] = 0;
   out_1965697165790759737[1] = 0;
   out_1965697165790759737[2] = 0;
   out_1965697165790759737[3] = 0;
   out_1965697165790759737[4] = 0;
   out_1965697165790759737[5] = 0;
   out_1965697165790759737[6] = 1;
   out_1965697165790759737[7] = 0;
   out_1965697165790759737[8] = 0;
   out_1965697165790759737[9] = 1;
   out_1965697165790759737[10] = 0;
   out_1965697165790759737[11] = 0;
   out_1965697165790759737[12] = 0;
   out_1965697165790759737[13] = 0;
   out_1965697165790759737[14] = 0;
   out_1965697165790759737[15] = 0;
   out_1965697165790759737[16] = 0;
   out_1965697165790759737[17] = 0;
   out_1965697165790759737[18] = 0;
   out_1965697165790759737[19] = 0;
   out_1965697165790759737[20] = 0;
   out_1965697165790759737[21] = 0;
   out_1965697165790759737[22] = 0;
   out_1965697165790759737[23] = 0;
   out_1965697165790759737[24] = 0;
   out_1965697165790759737[25] = 1;
   out_1965697165790759737[26] = 0;
   out_1965697165790759737[27] = 0;
   out_1965697165790759737[28] = 1;
   out_1965697165790759737[29] = 0;
   out_1965697165790759737[30] = 0;
   out_1965697165790759737[31] = 0;
   out_1965697165790759737[32] = 0;
   out_1965697165790759737[33] = 0;
   out_1965697165790759737[34] = 0;
   out_1965697165790759737[35] = 0;
   out_1965697165790759737[36] = 0;
   out_1965697165790759737[37] = 0;
   out_1965697165790759737[38] = 0;
   out_1965697165790759737[39] = 0;
   out_1965697165790759737[40] = 0;
   out_1965697165790759737[41] = 0;
   out_1965697165790759737[42] = 0;
   out_1965697165790759737[43] = 0;
   out_1965697165790759737[44] = 1;
   out_1965697165790759737[45] = 0;
   out_1965697165790759737[46] = 0;
   out_1965697165790759737[47] = 1;
   out_1965697165790759737[48] = 0;
   out_1965697165790759737[49] = 0;
   out_1965697165790759737[50] = 0;
   out_1965697165790759737[51] = 0;
   out_1965697165790759737[52] = 0;
   out_1965697165790759737[53] = 0;
}
void h_10(double *state, double *unused, double *out_8485879645605284392) {
   out_8485879645605284392[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_8485879645605284392[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_8485879645605284392[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_7331944868831731257) {
   out_7331944868831731257[0] = 0;
   out_7331944868831731257[1] = 9.8100000000000005*cos(state[1]);
   out_7331944868831731257[2] = 0;
   out_7331944868831731257[3] = 0;
   out_7331944868831731257[4] = -state[8];
   out_7331944868831731257[5] = state[7];
   out_7331944868831731257[6] = 0;
   out_7331944868831731257[7] = state[5];
   out_7331944868831731257[8] = -state[4];
   out_7331944868831731257[9] = 0;
   out_7331944868831731257[10] = 0;
   out_7331944868831731257[11] = 0;
   out_7331944868831731257[12] = 1;
   out_7331944868831731257[13] = 0;
   out_7331944868831731257[14] = 0;
   out_7331944868831731257[15] = 1;
   out_7331944868831731257[16] = 0;
   out_7331944868831731257[17] = 0;
   out_7331944868831731257[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_7331944868831731257[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_7331944868831731257[20] = 0;
   out_7331944868831731257[21] = state[8];
   out_7331944868831731257[22] = 0;
   out_7331944868831731257[23] = -state[6];
   out_7331944868831731257[24] = -state[5];
   out_7331944868831731257[25] = 0;
   out_7331944868831731257[26] = state[3];
   out_7331944868831731257[27] = 0;
   out_7331944868831731257[28] = 0;
   out_7331944868831731257[29] = 0;
   out_7331944868831731257[30] = 0;
   out_7331944868831731257[31] = 1;
   out_7331944868831731257[32] = 0;
   out_7331944868831731257[33] = 0;
   out_7331944868831731257[34] = 1;
   out_7331944868831731257[35] = 0;
   out_7331944868831731257[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_7331944868831731257[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_7331944868831731257[38] = 0;
   out_7331944868831731257[39] = -state[7];
   out_7331944868831731257[40] = state[6];
   out_7331944868831731257[41] = 0;
   out_7331944868831731257[42] = state[4];
   out_7331944868831731257[43] = -state[3];
   out_7331944868831731257[44] = 0;
   out_7331944868831731257[45] = 0;
   out_7331944868831731257[46] = 0;
   out_7331944868831731257[47] = 0;
   out_7331944868831731257[48] = 0;
   out_7331944868831731257[49] = 0;
   out_7331944868831731257[50] = 1;
   out_7331944868831731257[51] = 0;
   out_7331944868831731257[52] = 0;
   out_7331944868831731257[53] = 1;
}
void h_13(double *state, double *unused, double *out_2838239477305121349) {
   out_2838239477305121349[0] = state[3];
   out_2838239477305121349[1] = state[4];
   out_2838239477305121349[2] = state[5];
}
void H_13(double *state, double *unused, double *out_5177970991123092538) {
   out_5177970991123092538[0] = 0;
   out_5177970991123092538[1] = 0;
   out_5177970991123092538[2] = 0;
   out_5177970991123092538[3] = 1;
   out_5177970991123092538[4] = 0;
   out_5177970991123092538[5] = 0;
   out_5177970991123092538[6] = 0;
   out_5177970991123092538[7] = 0;
   out_5177970991123092538[8] = 0;
   out_5177970991123092538[9] = 0;
   out_5177970991123092538[10] = 0;
   out_5177970991123092538[11] = 0;
   out_5177970991123092538[12] = 0;
   out_5177970991123092538[13] = 0;
   out_5177970991123092538[14] = 0;
   out_5177970991123092538[15] = 0;
   out_5177970991123092538[16] = 0;
   out_5177970991123092538[17] = 0;
   out_5177970991123092538[18] = 0;
   out_5177970991123092538[19] = 0;
   out_5177970991123092538[20] = 0;
   out_5177970991123092538[21] = 0;
   out_5177970991123092538[22] = 1;
   out_5177970991123092538[23] = 0;
   out_5177970991123092538[24] = 0;
   out_5177970991123092538[25] = 0;
   out_5177970991123092538[26] = 0;
   out_5177970991123092538[27] = 0;
   out_5177970991123092538[28] = 0;
   out_5177970991123092538[29] = 0;
   out_5177970991123092538[30] = 0;
   out_5177970991123092538[31] = 0;
   out_5177970991123092538[32] = 0;
   out_5177970991123092538[33] = 0;
   out_5177970991123092538[34] = 0;
   out_5177970991123092538[35] = 0;
   out_5177970991123092538[36] = 0;
   out_5177970991123092538[37] = 0;
   out_5177970991123092538[38] = 0;
   out_5177970991123092538[39] = 0;
   out_5177970991123092538[40] = 0;
   out_5177970991123092538[41] = 1;
   out_5177970991123092538[42] = 0;
   out_5177970991123092538[43] = 0;
   out_5177970991123092538[44] = 0;
   out_5177970991123092538[45] = 0;
   out_5177970991123092538[46] = 0;
   out_5177970991123092538[47] = 0;
   out_5177970991123092538[48] = 0;
   out_5177970991123092538[49] = 0;
   out_5177970991123092538[50] = 0;
   out_5177970991123092538[51] = 0;
   out_5177970991123092538[52] = 0;
   out_5177970991123092538[53] = 0;
}
void h_14(double *state, double *unused, double *out_3664563598411967491) {
   out_3664563598411967491[0] = state[6];
   out_3664563598411967491[1] = state[7];
   out_3664563598411967491[2] = state[8];
}
void H_14(double *state, double *unused, double *out_5928938022130244266) {
   out_5928938022130244266[0] = 0;
   out_5928938022130244266[1] = 0;
   out_5928938022130244266[2] = 0;
   out_5928938022130244266[3] = 0;
   out_5928938022130244266[4] = 0;
   out_5928938022130244266[5] = 0;
   out_5928938022130244266[6] = 1;
   out_5928938022130244266[7] = 0;
   out_5928938022130244266[8] = 0;
   out_5928938022130244266[9] = 0;
   out_5928938022130244266[10] = 0;
   out_5928938022130244266[11] = 0;
   out_5928938022130244266[12] = 0;
   out_5928938022130244266[13] = 0;
   out_5928938022130244266[14] = 0;
   out_5928938022130244266[15] = 0;
   out_5928938022130244266[16] = 0;
   out_5928938022130244266[17] = 0;
   out_5928938022130244266[18] = 0;
   out_5928938022130244266[19] = 0;
   out_5928938022130244266[20] = 0;
   out_5928938022130244266[21] = 0;
   out_5928938022130244266[22] = 0;
   out_5928938022130244266[23] = 0;
   out_5928938022130244266[24] = 0;
   out_5928938022130244266[25] = 1;
   out_5928938022130244266[26] = 0;
   out_5928938022130244266[27] = 0;
   out_5928938022130244266[28] = 0;
   out_5928938022130244266[29] = 0;
   out_5928938022130244266[30] = 0;
   out_5928938022130244266[31] = 0;
   out_5928938022130244266[32] = 0;
   out_5928938022130244266[33] = 0;
   out_5928938022130244266[34] = 0;
   out_5928938022130244266[35] = 0;
   out_5928938022130244266[36] = 0;
   out_5928938022130244266[37] = 0;
   out_5928938022130244266[38] = 0;
   out_5928938022130244266[39] = 0;
   out_5928938022130244266[40] = 0;
   out_5928938022130244266[41] = 0;
   out_5928938022130244266[42] = 0;
   out_5928938022130244266[43] = 0;
   out_5928938022130244266[44] = 1;
   out_5928938022130244266[45] = 0;
   out_5928938022130244266[46] = 0;
   out_5928938022130244266[47] = 0;
   out_5928938022130244266[48] = 0;
   out_5928938022130244266[49] = 0;
   out_5928938022130244266[50] = 0;
   out_5928938022130244266[51] = 0;
   out_5928938022130244266[52] = 0;
   out_5928938022130244266[53] = 0;
}
#include <eigen3/Eigen/Dense>
#include <iostream>

typedef Eigen::Matrix<double, DIM, DIM, Eigen::RowMajor> DDM;
typedef Eigen::Matrix<double, EDIM, EDIM, Eigen::RowMajor> EEM;
typedef Eigen::Matrix<double, DIM, EDIM, Eigen::RowMajor> DEM;

void predict(double *in_x, double *in_P, double *in_Q, double dt) {
  typedef Eigen::Matrix<double, MEDIM, MEDIM, Eigen::RowMajor> RRM;

  double nx[DIM] = {0};
  double in_F[EDIM*EDIM] = {0};

  // functions from sympy
  f_fun(in_x, dt, nx);
  F_fun(in_x, dt, in_F);


  EEM F(in_F);
  EEM P(in_P);
  EEM Q(in_Q);

  RRM F_main = F.topLeftCorner(MEDIM, MEDIM);
  P.topLeftCorner(MEDIM, MEDIM) = (F_main * P.topLeftCorner(MEDIM, MEDIM)) * F_main.transpose();
  P.topRightCorner(MEDIM, EDIM - MEDIM) = F_main * P.topRightCorner(MEDIM, EDIM - MEDIM);
  P.bottomLeftCorner(EDIM - MEDIM, MEDIM) = P.bottomLeftCorner(EDIM - MEDIM, MEDIM) * F_main.transpose();

  P = P + dt*Q;

  // copy out state
  memcpy(in_x, nx, DIM * sizeof(double));
  memcpy(in_P, P.data(), EDIM * EDIM * sizeof(double));
}

// note: extra_args dim only correct when null space projecting
// otherwise 1
template <int ZDIM, int EADIM, bool MAHA_TEST>
void update(double *in_x, double *in_P, Hfun h_fun, Hfun H_fun, Hfun Hea_fun, double *in_z, double *in_R, double *in_ea, double MAHA_THRESHOLD) {
  typedef Eigen::Matrix<double, ZDIM, ZDIM, Eigen::RowMajor> ZZM;
  typedef Eigen::Matrix<double, ZDIM, DIM, Eigen::RowMajor> ZDM;
  typedef Eigen::Matrix<double, Eigen::Dynamic, EDIM, Eigen::RowMajor> XEM;
  //typedef Eigen::Matrix<double, EDIM, ZDIM, Eigen::RowMajor> EZM;
  typedef Eigen::Matrix<double, Eigen::Dynamic, 1> X1M;
  typedef Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> XXM;

  double in_hx[ZDIM] = {0};
  double in_H[ZDIM * DIM] = {0};
  double in_H_mod[EDIM * DIM] = {0};
  double delta_x[EDIM] = {0};
  double x_new[DIM] = {0};


  // state x, P
  Eigen::Matrix<double, ZDIM, 1> z(in_z);
  EEM P(in_P);
  ZZM pre_R(in_R);

  // functions from sympy
  h_fun(in_x, in_ea, in_hx);
  H_fun(in_x, in_ea, in_H);
  ZDM pre_H(in_H);

  // get y (y = z - hx)
  Eigen::Matrix<double, ZDIM, 1> pre_y(in_hx); pre_y = z - pre_y;
  X1M y; XXM H; XXM R;
  if (Hea_fun){
    typedef Eigen::Matrix<double, ZDIM, EADIM, Eigen::RowMajor> ZAM;
    double in_Hea[ZDIM * EADIM] = {0};
    Hea_fun(in_x, in_ea, in_Hea);
    ZAM Hea(in_Hea);
    XXM A = Hea.transpose().fullPivLu().kernel();


    y = A.transpose() * pre_y;
    H = A.transpose() * pre_H;
    R = A.transpose() * pre_R * A;
  } else {
    y = pre_y;
    H = pre_H;
    R = pre_R;
  }
  // get modified H
  H_mod_fun(in_x, in_H_mod);
  DEM H_mod(in_H_mod);
  XEM H_err = H * H_mod;

  // Do mahalobis distance test
  if (MAHA_TEST){
    XXM a = (H_err * P * H_err.transpose() + R).inverse();
    double maha_dist = y.transpose() * a * y;
    if (maha_dist > MAHA_THRESHOLD){
      R = 1.0e16 * R;
    }
  }

  // Outlier resilient weighting
  double weight = 1;//(1.5)/(1 + y.squaredNorm()/R.sum());

  // kalman gains and I_KH
  XXM S = ((H_err * P) * H_err.transpose()) + R/weight;
  XEM KT = S.fullPivLu().solve(H_err * P.transpose());
  //EZM K = KT.transpose(); TODO: WHY DOES THIS NOT COMPILE?
  //EZM K = S.fullPivLu().solve(H_err * P.transpose()).transpose();
  //std::cout << "Here is the matrix rot:\n" << K << std::endl;
  EEM I_KH = Eigen::Matrix<double, EDIM, EDIM>::Identity() - (KT.transpose() * H_err);

  // update state by injecting dx
  Eigen::Matrix<double, EDIM, 1> dx(delta_x);
  dx  = (KT.transpose() * y);
  memcpy(delta_x, dx.data(), EDIM * sizeof(double));
  err_fun(in_x, delta_x, x_new);
  Eigen::Matrix<double, DIM, 1> x(x_new);

  // update cov
  P = ((I_KH * P) * I_KH.transpose()) + ((KT.transpose() * R) * KT);

  // copy out state
  memcpy(in_x, x.data(), DIM * sizeof(double));
  memcpy(in_P, P.data(), EDIM * EDIM * sizeof(double));
  memcpy(in_z, y.data(), y.rows() * sizeof(double));
}




}
extern "C" {

void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_4, H_4, NULL, in_z, in_R, in_ea, MAHA_THRESH_4);
}
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_10, H_10, NULL, in_z, in_R, in_ea, MAHA_THRESH_10);
}
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_13, H_13, NULL, in_z, in_R, in_ea, MAHA_THRESH_13);
}
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_14, H_14, NULL, in_z, in_R, in_ea, MAHA_THRESH_14);
}
void pose_err_fun(double *nom_x, double *delta_x, double *out_5807655181837607214) {
  err_fun(nom_x, delta_x, out_5807655181837607214);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_8974761284027602384) {
  inv_err_fun(nom_x, true_x, out_8974761284027602384);
}
void pose_H_mod_fun(double *state, double *out_7615318893377638193) {
  H_mod_fun(state, out_7615318893377638193);
}
void pose_f_fun(double *state, double dt, double *out_4539696263163526019) {
  f_fun(state,  dt, out_4539696263163526019);
}
void pose_F_fun(double *state, double dt, double *out_2543913590993509263) {
  F_fun(state,  dt, out_2543913590993509263);
}
void pose_h_4(double *state, double *unused, double *out_8982992753369428231) {
  h_4(state, unused, out_8982992753369428231);
}
void pose_H_4(double *state, double *unused, double *out_1965697165790759737) {
  H_4(state, unused, out_1965697165790759737);
}
void pose_h_10(double *state, double *unused, double *out_8485879645605284392) {
  h_10(state, unused, out_8485879645605284392);
}
void pose_H_10(double *state, double *unused, double *out_7331944868831731257) {
  H_10(state, unused, out_7331944868831731257);
}
void pose_h_13(double *state, double *unused, double *out_2838239477305121349) {
  h_13(state, unused, out_2838239477305121349);
}
void pose_H_13(double *state, double *unused, double *out_5177970991123092538) {
  H_13(state, unused, out_5177970991123092538);
}
void pose_h_14(double *state, double *unused, double *out_3664563598411967491) {
  h_14(state, unused, out_3664563598411967491);
}
void pose_H_14(double *state, double *unused, double *out_5928938022130244266) {
  H_14(state, unused, out_5928938022130244266);
}
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt) {
  predict(in_x, in_P, in_Q, dt);
}
}

const EKF pose = {
  .name = "pose",
  .kinds = { 4, 10, 13, 14 },
  .feature_kinds = {  },
  .f_fun = pose_f_fun,
  .F_fun = pose_F_fun,
  .err_fun = pose_err_fun,
  .inv_err_fun = pose_inv_err_fun,
  .H_mod_fun = pose_H_mod_fun,
  .predict = pose_predict,
  .hs = {
    { 4, pose_h_4 },
    { 10, pose_h_10 },
    { 13, pose_h_13 },
    { 14, pose_h_14 },
  },
  .Hs = {
    { 4, pose_H_4 },
    { 10, pose_H_10 },
    { 13, pose_H_13 },
    { 14, pose_H_14 },
  },
  .updates = {
    { 4, pose_update_4 },
    { 10, pose_update_10 },
    { 13, pose_update_13 },
    { 14, pose_update_14 },
  },
  .Hes = {
  },
  .sets = {
  },
  .extra_routines = {
  },
};

ekf_lib_init(pose)
