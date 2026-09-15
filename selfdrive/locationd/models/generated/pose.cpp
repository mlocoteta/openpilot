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
void err_fun(double *nom_x, double *delta_x, double *out_5010206230741134473) {
   out_5010206230741134473[0] = delta_x[0] + nom_x[0];
   out_5010206230741134473[1] = delta_x[1] + nom_x[1];
   out_5010206230741134473[2] = delta_x[2] + nom_x[2];
   out_5010206230741134473[3] = delta_x[3] + nom_x[3];
   out_5010206230741134473[4] = delta_x[4] + nom_x[4];
   out_5010206230741134473[5] = delta_x[5] + nom_x[5];
   out_5010206230741134473[6] = delta_x[6] + nom_x[6];
   out_5010206230741134473[7] = delta_x[7] + nom_x[7];
   out_5010206230741134473[8] = delta_x[8] + nom_x[8];
   out_5010206230741134473[9] = delta_x[9] + nom_x[9];
   out_5010206230741134473[10] = delta_x[10] + nom_x[10];
   out_5010206230741134473[11] = delta_x[11] + nom_x[11];
   out_5010206230741134473[12] = delta_x[12] + nom_x[12];
   out_5010206230741134473[13] = delta_x[13] + nom_x[13];
   out_5010206230741134473[14] = delta_x[14] + nom_x[14];
   out_5010206230741134473[15] = delta_x[15] + nom_x[15];
   out_5010206230741134473[16] = delta_x[16] + nom_x[16];
   out_5010206230741134473[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_1188067782326305394) {
   out_1188067782326305394[0] = -nom_x[0] + true_x[0];
   out_1188067782326305394[1] = -nom_x[1] + true_x[1];
   out_1188067782326305394[2] = -nom_x[2] + true_x[2];
   out_1188067782326305394[3] = -nom_x[3] + true_x[3];
   out_1188067782326305394[4] = -nom_x[4] + true_x[4];
   out_1188067782326305394[5] = -nom_x[5] + true_x[5];
   out_1188067782326305394[6] = -nom_x[6] + true_x[6];
   out_1188067782326305394[7] = -nom_x[7] + true_x[7];
   out_1188067782326305394[8] = -nom_x[8] + true_x[8];
   out_1188067782326305394[9] = -nom_x[9] + true_x[9];
   out_1188067782326305394[10] = -nom_x[10] + true_x[10];
   out_1188067782326305394[11] = -nom_x[11] + true_x[11];
   out_1188067782326305394[12] = -nom_x[12] + true_x[12];
   out_1188067782326305394[13] = -nom_x[13] + true_x[13];
   out_1188067782326305394[14] = -nom_x[14] + true_x[14];
   out_1188067782326305394[15] = -nom_x[15] + true_x[15];
   out_1188067782326305394[16] = -nom_x[16] + true_x[16];
   out_1188067782326305394[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_7990211645421290333) {
   out_7990211645421290333[0] = 1.0;
   out_7990211645421290333[1] = 0.0;
   out_7990211645421290333[2] = 0.0;
   out_7990211645421290333[3] = 0.0;
   out_7990211645421290333[4] = 0.0;
   out_7990211645421290333[5] = 0.0;
   out_7990211645421290333[6] = 0.0;
   out_7990211645421290333[7] = 0.0;
   out_7990211645421290333[8] = 0.0;
   out_7990211645421290333[9] = 0.0;
   out_7990211645421290333[10] = 0.0;
   out_7990211645421290333[11] = 0.0;
   out_7990211645421290333[12] = 0.0;
   out_7990211645421290333[13] = 0.0;
   out_7990211645421290333[14] = 0.0;
   out_7990211645421290333[15] = 0.0;
   out_7990211645421290333[16] = 0.0;
   out_7990211645421290333[17] = 0.0;
   out_7990211645421290333[18] = 0.0;
   out_7990211645421290333[19] = 1.0;
   out_7990211645421290333[20] = 0.0;
   out_7990211645421290333[21] = 0.0;
   out_7990211645421290333[22] = 0.0;
   out_7990211645421290333[23] = 0.0;
   out_7990211645421290333[24] = 0.0;
   out_7990211645421290333[25] = 0.0;
   out_7990211645421290333[26] = 0.0;
   out_7990211645421290333[27] = 0.0;
   out_7990211645421290333[28] = 0.0;
   out_7990211645421290333[29] = 0.0;
   out_7990211645421290333[30] = 0.0;
   out_7990211645421290333[31] = 0.0;
   out_7990211645421290333[32] = 0.0;
   out_7990211645421290333[33] = 0.0;
   out_7990211645421290333[34] = 0.0;
   out_7990211645421290333[35] = 0.0;
   out_7990211645421290333[36] = 0.0;
   out_7990211645421290333[37] = 0.0;
   out_7990211645421290333[38] = 1.0;
   out_7990211645421290333[39] = 0.0;
   out_7990211645421290333[40] = 0.0;
   out_7990211645421290333[41] = 0.0;
   out_7990211645421290333[42] = 0.0;
   out_7990211645421290333[43] = 0.0;
   out_7990211645421290333[44] = 0.0;
   out_7990211645421290333[45] = 0.0;
   out_7990211645421290333[46] = 0.0;
   out_7990211645421290333[47] = 0.0;
   out_7990211645421290333[48] = 0.0;
   out_7990211645421290333[49] = 0.0;
   out_7990211645421290333[50] = 0.0;
   out_7990211645421290333[51] = 0.0;
   out_7990211645421290333[52] = 0.0;
   out_7990211645421290333[53] = 0.0;
   out_7990211645421290333[54] = 0.0;
   out_7990211645421290333[55] = 0.0;
   out_7990211645421290333[56] = 0.0;
   out_7990211645421290333[57] = 1.0;
   out_7990211645421290333[58] = 0.0;
   out_7990211645421290333[59] = 0.0;
   out_7990211645421290333[60] = 0.0;
   out_7990211645421290333[61] = 0.0;
   out_7990211645421290333[62] = 0.0;
   out_7990211645421290333[63] = 0.0;
   out_7990211645421290333[64] = 0.0;
   out_7990211645421290333[65] = 0.0;
   out_7990211645421290333[66] = 0.0;
   out_7990211645421290333[67] = 0.0;
   out_7990211645421290333[68] = 0.0;
   out_7990211645421290333[69] = 0.0;
   out_7990211645421290333[70] = 0.0;
   out_7990211645421290333[71] = 0.0;
   out_7990211645421290333[72] = 0.0;
   out_7990211645421290333[73] = 0.0;
   out_7990211645421290333[74] = 0.0;
   out_7990211645421290333[75] = 0.0;
   out_7990211645421290333[76] = 1.0;
   out_7990211645421290333[77] = 0.0;
   out_7990211645421290333[78] = 0.0;
   out_7990211645421290333[79] = 0.0;
   out_7990211645421290333[80] = 0.0;
   out_7990211645421290333[81] = 0.0;
   out_7990211645421290333[82] = 0.0;
   out_7990211645421290333[83] = 0.0;
   out_7990211645421290333[84] = 0.0;
   out_7990211645421290333[85] = 0.0;
   out_7990211645421290333[86] = 0.0;
   out_7990211645421290333[87] = 0.0;
   out_7990211645421290333[88] = 0.0;
   out_7990211645421290333[89] = 0.0;
   out_7990211645421290333[90] = 0.0;
   out_7990211645421290333[91] = 0.0;
   out_7990211645421290333[92] = 0.0;
   out_7990211645421290333[93] = 0.0;
   out_7990211645421290333[94] = 0.0;
   out_7990211645421290333[95] = 1.0;
   out_7990211645421290333[96] = 0.0;
   out_7990211645421290333[97] = 0.0;
   out_7990211645421290333[98] = 0.0;
   out_7990211645421290333[99] = 0.0;
   out_7990211645421290333[100] = 0.0;
   out_7990211645421290333[101] = 0.0;
   out_7990211645421290333[102] = 0.0;
   out_7990211645421290333[103] = 0.0;
   out_7990211645421290333[104] = 0.0;
   out_7990211645421290333[105] = 0.0;
   out_7990211645421290333[106] = 0.0;
   out_7990211645421290333[107] = 0.0;
   out_7990211645421290333[108] = 0.0;
   out_7990211645421290333[109] = 0.0;
   out_7990211645421290333[110] = 0.0;
   out_7990211645421290333[111] = 0.0;
   out_7990211645421290333[112] = 0.0;
   out_7990211645421290333[113] = 0.0;
   out_7990211645421290333[114] = 1.0;
   out_7990211645421290333[115] = 0.0;
   out_7990211645421290333[116] = 0.0;
   out_7990211645421290333[117] = 0.0;
   out_7990211645421290333[118] = 0.0;
   out_7990211645421290333[119] = 0.0;
   out_7990211645421290333[120] = 0.0;
   out_7990211645421290333[121] = 0.0;
   out_7990211645421290333[122] = 0.0;
   out_7990211645421290333[123] = 0.0;
   out_7990211645421290333[124] = 0.0;
   out_7990211645421290333[125] = 0.0;
   out_7990211645421290333[126] = 0.0;
   out_7990211645421290333[127] = 0.0;
   out_7990211645421290333[128] = 0.0;
   out_7990211645421290333[129] = 0.0;
   out_7990211645421290333[130] = 0.0;
   out_7990211645421290333[131] = 0.0;
   out_7990211645421290333[132] = 0.0;
   out_7990211645421290333[133] = 1.0;
   out_7990211645421290333[134] = 0.0;
   out_7990211645421290333[135] = 0.0;
   out_7990211645421290333[136] = 0.0;
   out_7990211645421290333[137] = 0.0;
   out_7990211645421290333[138] = 0.0;
   out_7990211645421290333[139] = 0.0;
   out_7990211645421290333[140] = 0.0;
   out_7990211645421290333[141] = 0.0;
   out_7990211645421290333[142] = 0.0;
   out_7990211645421290333[143] = 0.0;
   out_7990211645421290333[144] = 0.0;
   out_7990211645421290333[145] = 0.0;
   out_7990211645421290333[146] = 0.0;
   out_7990211645421290333[147] = 0.0;
   out_7990211645421290333[148] = 0.0;
   out_7990211645421290333[149] = 0.0;
   out_7990211645421290333[150] = 0.0;
   out_7990211645421290333[151] = 0.0;
   out_7990211645421290333[152] = 1.0;
   out_7990211645421290333[153] = 0.0;
   out_7990211645421290333[154] = 0.0;
   out_7990211645421290333[155] = 0.0;
   out_7990211645421290333[156] = 0.0;
   out_7990211645421290333[157] = 0.0;
   out_7990211645421290333[158] = 0.0;
   out_7990211645421290333[159] = 0.0;
   out_7990211645421290333[160] = 0.0;
   out_7990211645421290333[161] = 0.0;
   out_7990211645421290333[162] = 0.0;
   out_7990211645421290333[163] = 0.0;
   out_7990211645421290333[164] = 0.0;
   out_7990211645421290333[165] = 0.0;
   out_7990211645421290333[166] = 0.0;
   out_7990211645421290333[167] = 0.0;
   out_7990211645421290333[168] = 0.0;
   out_7990211645421290333[169] = 0.0;
   out_7990211645421290333[170] = 0.0;
   out_7990211645421290333[171] = 1.0;
   out_7990211645421290333[172] = 0.0;
   out_7990211645421290333[173] = 0.0;
   out_7990211645421290333[174] = 0.0;
   out_7990211645421290333[175] = 0.0;
   out_7990211645421290333[176] = 0.0;
   out_7990211645421290333[177] = 0.0;
   out_7990211645421290333[178] = 0.0;
   out_7990211645421290333[179] = 0.0;
   out_7990211645421290333[180] = 0.0;
   out_7990211645421290333[181] = 0.0;
   out_7990211645421290333[182] = 0.0;
   out_7990211645421290333[183] = 0.0;
   out_7990211645421290333[184] = 0.0;
   out_7990211645421290333[185] = 0.0;
   out_7990211645421290333[186] = 0.0;
   out_7990211645421290333[187] = 0.0;
   out_7990211645421290333[188] = 0.0;
   out_7990211645421290333[189] = 0.0;
   out_7990211645421290333[190] = 1.0;
   out_7990211645421290333[191] = 0.0;
   out_7990211645421290333[192] = 0.0;
   out_7990211645421290333[193] = 0.0;
   out_7990211645421290333[194] = 0.0;
   out_7990211645421290333[195] = 0.0;
   out_7990211645421290333[196] = 0.0;
   out_7990211645421290333[197] = 0.0;
   out_7990211645421290333[198] = 0.0;
   out_7990211645421290333[199] = 0.0;
   out_7990211645421290333[200] = 0.0;
   out_7990211645421290333[201] = 0.0;
   out_7990211645421290333[202] = 0.0;
   out_7990211645421290333[203] = 0.0;
   out_7990211645421290333[204] = 0.0;
   out_7990211645421290333[205] = 0.0;
   out_7990211645421290333[206] = 0.0;
   out_7990211645421290333[207] = 0.0;
   out_7990211645421290333[208] = 0.0;
   out_7990211645421290333[209] = 1.0;
   out_7990211645421290333[210] = 0.0;
   out_7990211645421290333[211] = 0.0;
   out_7990211645421290333[212] = 0.0;
   out_7990211645421290333[213] = 0.0;
   out_7990211645421290333[214] = 0.0;
   out_7990211645421290333[215] = 0.0;
   out_7990211645421290333[216] = 0.0;
   out_7990211645421290333[217] = 0.0;
   out_7990211645421290333[218] = 0.0;
   out_7990211645421290333[219] = 0.0;
   out_7990211645421290333[220] = 0.0;
   out_7990211645421290333[221] = 0.0;
   out_7990211645421290333[222] = 0.0;
   out_7990211645421290333[223] = 0.0;
   out_7990211645421290333[224] = 0.0;
   out_7990211645421290333[225] = 0.0;
   out_7990211645421290333[226] = 0.0;
   out_7990211645421290333[227] = 0.0;
   out_7990211645421290333[228] = 1.0;
   out_7990211645421290333[229] = 0.0;
   out_7990211645421290333[230] = 0.0;
   out_7990211645421290333[231] = 0.0;
   out_7990211645421290333[232] = 0.0;
   out_7990211645421290333[233] = 0.0;
   out_7990211645421290333[234] = 0.0;
   out_7990211645421290333[235] = 0.0;
   out_7990211645421290333[236] = 0.0;
   out_7990211645421290333[237] = 0.0;
   out_7990211645421290333[238] = 0.0;
   out_7990211645421290333[239] = 0.0;
   out_7990211645421290333[240] = 0.0;
   out_7990211645421290333[241] = 0.0;
   out_7990211645421290333[242] = 0.0;
   out_7990211645421290333[243] = 0.0;
   out_7990211645421290333[244] = 0.0;
   out_7990211645421290333[245] = 0.0;
   out_7990211645421290333[246] = 0.0;
   out_7990211645421290333[247] = 1.0;
   out_7990211645421290333[248] = 0.0;
   out_7990211645421290333[249] = 0.0;
   out_7990211645421290333[250] = 0.0;
   out_7990211645421290333[251] = 0.0;
   out_7990211645421290333[252] = 0.0;
   out_7990211645421290333[253] = 0.0;
   out_7990211645421290333[254] = 0.0;
   out_7990211645421290333[255] = 0.0;
   out_7990211645421290333[256] = 0.0;
   out_7990211645421290333[257] = 0.0;
   out_7990211645421290333[258] = 0.0;
   out_7990211645421290333[259] = 0.0;
   out_7990211645421290333[260] = 0.0;
   out_7990211645421290333[261] = 0.0;
   out_7990211645421290333[262] = 0.0;
   out_7990211645421290333[263] = 0.0;
   out_7990211645421290333[264] = 0.0;
   out_7990211645421290333[265] = 0.0;
   out_7990211645421290333[266] = 1.0;
   out_7990211645421290333[267] = 0.0;
   out_7990211645421290333[268] = 0.0;
   out_7990211645421290333[269] = 0.0;
   out_7990211645421290333[270] = 0.0;
   out_7990211645421290333[271] = 0.0;
   out_7990211645421290333[272] = 0.0;
   out_7990211645421290333[273] = 0.0;
   out_7990211645421290333[274] = 0.0;
   out_7990211645421290333[275] = 0.0;
   out_7990211645421290333[276] = 0.0;
   out_7990211645421290333[277] = 0.0;
   out_7990211645421290333[278] = 0.0;
   out_7990211645421290333[279] = 0.0;
   out_7990211645421290333[280] = 0.0;
   out_7990211645421290333[281] = 0.0;
   out_7990211645421290333[282] = 0.0;
   out_7990211645421290333[283] = 0.0;
   out_7990211645421290333[284] = 0.0;
   out_7990211645421290333[285] = 1.0;
   out_7990211645421290333[286] = 0.0;
   out_7990211645421290333[287] = 0.0;
   out_7990211645421290333[288] = 0.0;
   out_7990211645421290333[289] = 0.0;
   out_7990211645421290333[290] = 0.0;
   out_7990211645421290333[291] = 0.0;
   out_7990211645421290333[292] = 0.0;
   out_7990211645421290333[293] = 0.0;
   out_7990211645421290333[294] = 0.0;
   out_7990211645421290333[295] = 0.0;
   out_7990211645421290333[296] = 0.0;
   out_7990211645421290333[297] = 0.0;
   out_7990211645421290333[298] = 0.0;
   out_7990211645421290333[299] = 0.0;
   out_7990211645421290333[300] = 0.0;
   out_7990211645421290333[301] = 0.0;
   out_7990211645421290333[302] = 0.0;
   out_7990211645421290333[303] = 0.0;
   out_7990211645421290333[304] = 1.0;
   out_7990211645421290333[305] = 0.0;
   out_7990211645421290333[306] = 0.0;
   out_7990211645421290333[307] = 0.0;
   out_7990211645421290333[308] = 0.0;
   out_7990211645421290333[309] = 0.0;
   out_7990211645421290333[310] = 0.0;
   out_7990211645421290333[311] = 0.0;
   out_7990211645421290333[312] = 0.0;
   out_7990211645421290333[313] = 0.0;
   out_7990211645421290333[314] = 0.0;
   out_7990211645421290333[315] = 0.0;
   out_7990211645421290333[316] = 0.0;
   out_7990211645421290333[317] = 0.0;
   out_7990211645421290333[318] = 0.0;
   out_7990211645421290333[319] = 0.0;
   out_7990211645421290333[320] = 0.0;
   out_7990211645421290333[321] = 0.0;
   out_7990211645421290333[322] = 0.0;
   out_7990211645421290333[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_2076252175851799438) {
   out_2076252175851799438[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_2076252175851799438[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_2076252175851799438[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_2076252175851799438[3] = dt*state[12] + state[3];
   out_2076252175851799438[4] = dt*state[13] + state[4];
   out_2076252175851799438[5] = dt*state[14] + state[5];
   out_2076252175851799438[6] = state[6];
   out_2076252175851799438[7] = state[7];
   out_2076252175851799438[8] = state[8];
   out_2076252175851799438[9] = state[9];
   out_2076252175851799438[10] = state[10];
   out_2076252175851799438[11] = state[11];
   out_2076252175851799438[12] = state[12];
   out_2076252175851799438[13] = state[13];
   out_2076252175851799438[14] = state[14];
   out_2076252175851799438[15] = state[15];
   out_2076252175851799438[16] = state[16];
   out_2076252175851799438[17] = state[17];
}
void F_fun(double *state, double dt, double *out_5637265960027517094) {
   out_5637265960027517094[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_5637265960027517094[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_5637265960027517094[2] = 0;
   out_5637265960027517094[3] = 0;
   out_5637265960027517094[4] = 0;
   out_5637265960027517094[5] = 0;
   out_5637265960027517094[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_5637265960027517094[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_5637265960027517094[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_5637265960027517094[9] = 0;
   out_5637265960027517094[10] = 0;
   out_5637265960027517094[11] = 0;
   out_5637265960027517094[12] = 0;
   out_5637265960027517094[13] = 0;
   out_5637265960027517094[14] = 0;
   out_5637265960027517094[15] = 0;
   out_5637265960027517094[16] = 0;
   out_5637265960027517094[17] = 0;
   out_5637265960027517094[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_5637265960027517094[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_5637265960027517094[20] = 0;
   out_5637265960027517094[21] = 0;
   out_5637265960027517094[22] = 0;
   out_5637265960027517094[23] = 0;
   out_5637265960027517094[24] = 0;
   out_5637265960027517094[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_5637265960027517094[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_5637265960027517094[27] = 0;
   out_5637265960027517094[28] = 0;
   out_5637265960027517094[29] = 0;
   out_5637265960027517094[30] = 0;
   out_5637265960027517094[31] = 0;
   out_5637265960027517094[32] = 0;
   out_5637265960027517094[33] = 0;
   out_5637265960027517094[34] = 0;
   out_5637265960027517094[35] = 0;
   out_5637265960027517094[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_5637265960027517094[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_5637265960027517094[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_5637265960027517094[39] = 0;
   out_5637265960027517094[40] = 0;
   out_5637265960027517094[41] = 0;
   out_5637265960027517094[42] = 0;
   out_5637265960027517094[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_5637265960027517094[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_5637265960027517094[45] = 0;
   out_5637265960027517094[46] = 0;
   out_5637265960027517094[47] = 0;
   out_5637265960027517094[48] = 0;
   out_5637265960027517094[49] = 0;
   out_5637265960027517094[50] = 0;
   out_5637265960027517094[51] = 0;
   out_5637265960027517094[52] = 0;
   out_5637265960027517094[53] = 0;
   out_5637265960027517094[54] = 0;
   out_5637265960027517094[55] = 0;
   out_5637265960027517094[56] = 0;
   out_5637265960027517094[57] = 1;
   out_5637265960027517094[58] = 0;
   out_5637265960027517094[59] = 0;
   out_5637265960027517094[60] = 0;
   out_5637265960027517094[61] = 0;
   out_5637265960027517094[62] = 0;
   out_5637265960027517094[63] = 0;
   out_5637265960027517094[64] = 0;
   out_5637265960027517094[65] = 0;
   out_5637265960027517094[66] = dt;
   out_5637265960027517094[67] = 0;
   out_5637265960027517094[68] = 0;
   out_5637265960027517094[69] = 0;
   out_5637265960027517094[70] = 0;
   out_5637265960027517094[71] = 0;
   out_5637265960027517094[72] = 0;
   out_5637265960027517094[73] = 0;
   out_5637265960027517094[74] = 0;
   out_5637265960027517094[75] = 0;
   out_5637265960027517094[76] = 1;
   out_5637265960027517094[77] = 0;
   out_5637265960027517094[78] = 0;
   out_5637265960027517094[79] = 0;
   out_5637265960027517094[80] = 0;
   out_5637265960027517094[81] = 0;
   out_5637265960027517094[82] = 0;
   out_5637265960027517094[83] = 0;
   out_5637265960027517094[84] = 0;
   out_5637265960027517094[85] = dt;
   out_5637265960027517094[86] = 0;
   out_5637265960027517094[87] = 0;
   out_5637265960027517094[88] = 0;
   out_5637265960027517094[89] = 0;
   out_5637265960027517094[90] = 0;
   out_5637265960027517094[91] = 0;
   out_5637265960027517094[92] = 0;
   out_5637265960027517094[93] = 0;
   out_5637265960027517094[94] = 0;
   out_5637265960027517094[95] = 1;
   out_5637265960027517094[96] = 0;
   out_5637265960027517094[97] = 0;
   out_5637265960027517094[98] = 0;
   out_5637265960027517094[99] = 0;
   out_5637265960027517094[100] = 0;
   out_5637265960027517094[101] = 0;
   out_5637265960027517094[102] = 0;
   out_5637265960027517094[103] = 0;
   out_5637265960027517094[104] = dt;
   out_5637265960027517094[105] = 0;
   out_5637265960027517094[106] = 0;
   out_5637265960027517094[107] = 0;
   out_5637265960027517094[108] = 0;
   out_5637265960027517094[109] = 0;
   out_5637265960027517094[110] = 0;
   out_5637265960027517094[111] = 0;
   out_5637265960027517094[112] = 0;
   out_5637265960027517094[113] = 0;
   out_5637265960027517094[114] = 1;
   out_5637265960027517094[115] = 0;
   out_5637265960027517094[116] = 0;
   out_5637265960027517094[117] = 0;
   out_5637265960027517094[118] = 0;
   out_5637265960027517094[119] = 0;
   out_5637265960027517094[120] = 0;
   out_5637265960027517094[121] = 0;
   out_5637265960027517094[122] = 0;
   out_5637265960027517094[123] = 0;
   out_5637265960027517094[124] = 0;
   out_5637265960027517094[125] = 0;
   out_5637265960027517094[126] = 0;
   out_5637265960027517094[127] = 0;
   out_5637265960027517094[128] = 0;
   out_5637265960027517094[129] = 0;
   out_5637265960027517094[130] = 0;
   out_5637265960027517094[131] = 0;
   out_5637265960027517094[132] = 0;
   out_5637265960027517094[133] = 1;
   out_5637265960027517094[134] = 0;
   out_5637265960027517094[135] = 0;
   out_5637265960027517094[136] = 0;
   out_5637265960027517094[137] = 0;
   out_5637265960027517094[138] = 0;
   out_5637265960027517094[139] = 0;
   out_5637265960027517094[140] = 0;
   out_5637265960027517094[141] = 0;
   out_5637265960027517094[142] = 0;
   out_5637265960027517094[143] = 0;
   out_5637265960027517094[144] = 0;
   out_5637265960027517094[145] = 0;
   out_5637265960027517094[146] = 0;
   out_5637265960027517094[147] = 0;
   out_5637265960027517094[148] = 0;
   out_5637265960027517094[149] = 0;
   out_5637265960027517094[150] = 0;
   out_5637265960027517094[151] = 0;
   out_5637265960027517094[152] = 1;
   out_5637265960027517094[153] = 0;
   out_5637265960027517094[154] = 0;
   out_5637265960027517094[155] = 0;
   out_5637265960027517094[156] = 0;
   out_5637265960027517094[157] = 0;
   out_5637265960027517094[158] = 0;
   out_5637265960027517094[159] = 0;
   out_5637265960027517094[160] = 0;
   out_5637265960027517094[161] = 0;
   out_5637265960027517094[162] = 0;
   out_5637265960027517094[163] = 0;
   out_5637265960027517094[164] = 0;
   out_5637265960027517094[165] = 0;
   out_5637265960027517094[166] = 0;
   out_5637265960027517094[167] = 0;
   out_5637265960027517094[168] = 0;
   out_5637265960027517094[169] = 0;
   out_5637265960027517094[170] = 0;
   out_5637265960027517094[171] = 1;
   out_5637265960027517094[172] = 0;
   out_5637265960027517094[173] = 0;
   out_5637265960027517094[174] = 0;
   out_5637265960027517094[175] = 0;
   out_5637265960027517094[176] = 0;
   out_5637265960027517094[177] = 0;
   out_5637265960027517094[178] = 0;
   out_5637265960027517094[179] = 0;
   out_5637265960027517094[180] = 0;
   out_5637265960027517094[181] = 0;
   out_5637265960027517094[182] = 0;
   out_5637265960027517094[183] = 0;
   out_5637265960027517094[184] = 0;
   out_5637265960027517094[185] = 0;
   out_5637265960027517094[186] = 0;
   out_5637265960027517094[187] = 0;
   out_5637265960027517094[188] = 0;
   out_5637265960027517094[189] = 0;
   out_5637265960027517094[190] = 1;
   out_5637265960027517094[191] = 0;
   out_5637265960027517094[192] = 0;
   out_5637265960027517094[193] = 0;
   out_5637265960027517094[194] = 0;
   out_5637265960027517094[195] = 0;
   out_5637265960027517094[196] = 0;
   out_5637265960027517094[197] = 0;
   out_5637265960027517094[198] = 0;
   out_5637265960027517094[199] = 0;
   out_5637265960027517094[200] = 0;
   out_5637265960027517094[201] = 0;
   out_5637265960027517094[202] = 0;
   out_5637265960027517094[203] = 0;
   out_5637265960027517094[204] = 0;
   out_5637265960027517094[205] = 0;
   out_5637265960027517094[206] = 0;
   out_5637265960027517094[207] = 0;
   out_5637265960027517094[208] = 0;
   out_5637265960027517094[209] = 1;
   out_5637265960027517094[210] = 0;
   out_5637265960027517094[211] = 0;
   out_5637265960027517094[212] = 0;
   out_5637265960027517094[213] = 0;
   out_5637265960027517094[214] = 0;
   out_5637265960027517094[215] = 0;
   out_5637265960027517094[216] = 0;
   out_5637265960027517094[217] = 0;
   out_5637265960027517094[218] = 0;
   out_5637265960027517094[219] = 0;
   out_5637265960027517094[220] = 0;
   out_5637265960027517094[221] = 0;
   out_5637265960027517094[222] = 0;
   out_5637265960027517094[223] = 0;
   out_5637265960027517094[224] = 0;
   out_5637265960027517094[225] = 0;
   out_5637265960027517094[226] = 0;
   out_5637265960027517094[227] = 0;
   out_5637265960027517094[228] = 1;
   out_5637265960027517094[229] = 0;
   out_5637265960027517094[230] = 0;
   out_5637265960027517094[231] = 0;
   out_5637265960027517094[232] = 0;
   out_5637265960027517094[233] = 0;
   out_5637265960027517094[234] = 0;
   out_5637265960027517094[235] = 0;
   out_5637265960027517094[236] = 0;
   out_5637265960027517094[237] = 0;
   out_5637265960027517094[238] = 0;
   out_5637265960027517094[239] = 0;
   out_5637265960027517094[240] = 0;
   out_5637265960027517094[241] = 0;
   out_5637265960027517094[242] = 0;
   out_5637265960027517094[243] = 0;
   out_5637265960027517094[244] = 0;
   out_5637265960027517094[245] = 0;
   out_5637265960027517094[246] = 0;
   out_5637265960027517094[247] = 1;
   out_5637265960027517094[248] = 0;
   out_5637265960027517094[249] = 0;
   out_5637265960027517094[250] = 0;
   out_5637265960027517094[251] = 0;
   out_5637265960027517094[252] = 0;
   out_5637265960027517094[253] = 0;
   out_5637265960027517094[254] = 0;
   out_5637265960027517094[255] = 0;
   out_5637265960027517094[256] = 0;
   out_5637265960027517094[257] = 0;
   out_5637265960027517094[258] = 0;
   out_5637265960027517094[259] = 0;
   out_5637265960027517094[260] = 0;
   out_5637265960027517094[261] = 0;
   out_5637265960027517094[262] = 0;
   out_5637265960027517094[263] = 0;
   out_5637265960027517094[264] = 0;
   out_5637265960027517094[265] = 0;
   out_5637265960027517094[266] = 1;
   out_5637265960027517094[267] = 0;
   out_5637265960027517094[268] = 0;
   out_5637265960027517094[269] = 0;
   out_5637265960027517094[270] = 0;
   out_5637265960027517094[271] = 0;
   out_5637265960027517094[272] = 0;
   out_5637265960027517094[273] = 0;
   out_5637265960027517094[274] = 0;
   out_5637265960027517094[275] = 0;
   out_5637265960027517094[276] = 0;
   out_5637265960027517094[277] = 0;
   out_5637265960027517094[278] = 0;
   out_5637265960027517094[279] = 0;
   out_5637265960027517094[280] = 0;
   out_5637265960027517094[281] = 0;
   out_5637265960027517094[282] = 0;
   out_5637265960027517094[283] = 0;
   out_5637265960027517094[284] = 0;
   out_5637265960027517094[285] = 1;
   out_5637265960027517094[286] = 0;
   out_5637265960027517094[287] = 0;
   out_5637265960027517094[288] = 0;
   out_5637265960027517094[289] = 0;
   out_5637265960027517094[290] = 0;
   out_5637265960027517094[291] = 0;
   out_5637265960027517094[292] = 0;
   out_5637265960027517094[293] = 0;
   out_5637265960027517094[294] = 0;
   out_5637265960027517094[295] = 0;
   out_5637265960027517094[296] = 0;
   out_5637265960027517094[297] = 0;
   out_5637265960027517094[298] = 0;
   out_5637265960027517094[299] = 0;
   out_5637265960027517094[300] = 0;
   out_5637265960027517094[301] = 0;
   out_5637265960027517094[302] = 0;
   out_5637265960027517094[303] = 0;
   out_5637265960027517094[304] = 1;
   out_5637265960027517094[305] = 0;
   out_5637265960027517094[306] = 0;
   out_5637265960027517094[307] = 0;
   out_5637265960027517094[308] = 0;
   out_5637265960027517094[309] = 0;
   out_5637265960027517094[310] = 0;
   out_5637265960027517094[311] = 0;
   out_5637265960027517094[312] = 0;
   out_5637265960027517094[313] = 0;
   out_5637265960027517094[314] = 0;
   out_5637265960027517094[315] = 0;
   out_5637265960027517094[316] = 0;
   out_5637265960027517094[317] = 0;
   out_5637265960027517094[318] = 0;
   out_5637265960027517094[319] = 0;
   out_5637265960027517094[320] = 0;
   out_5637265960027517094[321] = 0;
   out_5637265960027517094[322] = 0;
   out_5637265960027517094[323] = 1;
}
void h_4(double *state, double *unused, double *out_4126661282704422428) {
   out_4126661282704422428[0] = state[6] + state[9];
   out_4126661282704422428[1] = state[7] + state[10];
   out_4126661282704422428[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_7236050643366577726) {
   out_7236050643366577726[0] = 0;
   out_7236050643366577726[1] = 0;
   out_7236050643366577726[2] = 0;
   out_7236050643366577726[3] = 0;
   out_7236050643366577726[4] = 0;
   out_7236050643366577726[5] = 0;
   out_7236050643366577726[6] = 1;
   out_7236050643366577726[7] = 0;
   out_7236050643366577726[8] = 0;
   out_7236050643366577726[9] = 1;
   out_7236050643366577726[10] = 0;
   out_7236050643366577726[11] = 0;
   out_7236050643366577726[12] = 0;
   out_7236050643366577726[13] = 0;
   out_7236050643366577726[14] = 0;
   out_7236050643366577726[15] = 0;
   out_7236050643366577726[16] = 0;
   out_7236050643366577726[17] = 0;
   out_7236050643366577726[18] = 0;
   out_7236050643366577726[19] = 0;
   out_7236050643366577726[20] = 0;
   out_7236050643366577726[21] = 0;
   out_7236050643366577726[22] = 0;
   out_7236050643366577726[23] = 0;
   out_7236050643366577726[24] = 0;
   out_7236050643366577726[25] = 1;
   out_7236050643366577726[26] = 0;
   out_7236050643366577726[27] = 0;
   out_7236050643366577726[28] = 1;
   out_7236050643366577726[29] = 0;
   out_7236050643366577726[30] = 0;
   out_7236050643366577726[31] = 0;
   out_7236050643366577726[32] = 0;
   out_7236050643366577726[33] = 0;
   out_7236050643366577726[34] = 0;
   out_7236050643366577726[35] = 0;
   out_7236050643366577726[36] = 0;
   out_7236050643366577726[37] = 0;
   out_7236050643366577726[38] = 0;
   out_7236050643366577726[39] = 0;
   out_7236050643366577726[40] = 0;
   out_7236050643366577726[41] = 0;
   out_7236050643366577726[42] = 0;
   out_7236050643366577726[43] = 0;
   out_7236050643366577726[44] = 1;
   out_7236050643366577726[45] = 0;
   out_7236050643366577726[46] = 0;
   out_7236050643366577726[47] = 1;
   out_7236050643366577726[48] = 0;
   out_7236050643366577726[49] = 0;
   out_7236050643366577726[50] = 0;
   out_7236050643366577726[51] = 0;
   out_7236050643366577726[52] = 0;
   out_7236050643366577726[53] = 0;
}
void h_10(double *state, double *unused, double *out_8418525422339329003) {
   out_8418525422339329003[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_8418525422339329003[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_8418525422339329003[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_7705227448246336422) {
   out_7705227448246336422[0] = 0;
   out_7705227448246336422[1] = 9.8100000000000005*cos(state[1]);
   out_7705227448246336422[2] = 0;
   out_7705227448246336422[3] = 0;
   out_7705227448246336422[4] = -state[8];
   out_7705227448246336422[5] = state[7];
   out_7705227448246336422[6] = 0;
   out_7705227448246336422[7] = state[5];
   out_7705227448246336422[8] = -state[4];
   out_7705227448246336422[9] = 0;
   out_7705227448246336422[10] = 0;
   out_7705227448246336422[11] = 0;
   out_7705227448246336422[12] = 1;
   out_7705227448246336422[13] = 0;
   out_7705227448246336422[14] = 0;
   out_7705227448246336422[15] = 1;
   out_7705227448246336422[16] = 0;
   out_7705227448246336422[17] = 0;
   out_7705227448246336422[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_7705227448246336422[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_7705227448246336422[20] = 0;
   out_7705227448246336422[21] = state[8];
   out_7705227448246336422[22] = 0;
   out_7705227448246336422[23] = -state[6];
   out_7705227448246336422[24] = -state[5];
   out_7705227448246336422[25] = 0;
   out_7705227448246336422[26] = state[3];
   out_7705227448246336422[27] = 0;
   out_7705227448246336422[28] = 0;
   out_7705227448246336422[29] = 0;
   out_7705227448246336422[30] = 0;
   out_7705227448246336422[31] = 1;
   out_7705227448246336422[32] = 0;
   out_7705227448246336422[33] = 0;
   out_7705227448246336422[34] = 1;
   out_7705227448246336422[35] = 0;
   out_7705227448246336422[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_7705227448246336422[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_7705227448246336422[38] = 0;
   out_7705227448246336422[39] = -state[7];
   out_7705227448246336422[40] = state[6];
   out_7705227448246336422[41] = 0;
   out_7705227448246336422[42] = state[4];
   out_7705227448246336422[43] = -state[3];
   out_7705227448246336422[44] = 0;
   out_7705227448246336422[45] = 0;
   out_7705227448246336422[46] = 0;
   out_7705227448246336422[47] = 0;
   out_7705227448246336422[48] = 0;
   out_7705227448246336422[49] = 0;
   out_7705227448246336422[50] = 1;
   out_7705227448246336422[51] = 0;
   out_7705227448246336422[52] = 0;
   out_7705227448246336422[53] = 1;
}
void h_13(double *state, double *unused, double *out_1137889379193769762) {
   out_1137889379193769762[0] = state[3];
   out_1137889379193769762[1] = state[4];
   out_1137889379193769762[2] = state[5];
}
void H_13(double *state, double *unused, double *out_4023776818034244925) {
   out_4023776818034244925[0] = 0;
   out_4023776818034244925[1] = 0;
   out_4023776818034244925[2] = 0;
   out_4023776818034244925[3] = 1;
   out_4023776818034244925[4] = 0;
   out_4023776818034244925[5] = 0;
   out_4023776818034244925[6] = 0;
   out_4023776818034244925[7] = 0;
   out_4023776818034244925[8] = 0;
   out_4023776818034244925[9] = 0;
   out_4023776818034244925[10] = 0;
   out_4023776818034244925[11] = 0;
   out_4023776818034244925[12] = 0;
   out_4023776818034244925[13] = 0;
   out_4023776818034244925[14] = 0;
   out_4023776818034244925[15] = 0;
   out_4023776818034244925[16] = 0;
   out_4023776818034244925[17] = 0;
   out_4023776818034244925[18] = 0;
   out_4023776818034244925[19] = 0;
   out_4023776818034244925[20] = 0;
   out_4023776818034244925[21] = 0;
   out_4023776818034244925[22] = 1;
   out_4023776818034244925[23] = 0;
   out_4023776818034244925[24] = 0;
   out_4023776818034244925[25] = 0;
   out_4023776818034244925[26] = 0;
   out_4023776818034244925[27] = 0;
   out_4023776818034244925[28] = 0;
   out_4023776818034244925[29] = 0;
   out_4023776818034244925[30] = 0;
   out_4023776818034244925[31] = 0;
   out_4023776818034244925[32] = 0;
   out_4023776818034244925[33] = 0;
   out_4023776818034244925[34] = 0;
   out_4023776818034244925[35] = 0;
   out_4023776818034244925[36] = 0;
   out_4023776818034244925[37] = 0;
   out_4023776818034244925[38] = 0;
   out_4023776818034244925[39] = 0;
   out_4023776818034244925[40] = 0;
   out_4023776818034244925[41] = 1;
   out_4023776818034244925[42] = 0;
   out_4023776818034244925[43] = 0;
   out_4023776818034244925[44] = 0;
   out_4023776818034244925[45] = 0;
   out_4023776818034244925[46] = 0;
   out_4023776818034244925[47] = 0;
   out_4023776818034244925[48] = 0;
   out_4023776818034244925[49] = 0;
   out_4023776818034244925[50] = 0;
   out_4023776818034244925[51] = 0;
   out_4023776818034244925[52] = 0;
   out_4023776818034244925[53] = 0;
}
void h_14(double *state, double *unused, double *out_3946282764828343143) {
   out_3946282764828343143[0] = state[6];
   out_3946282764828343143[1] = state[7];
   out_3946282764828343143[2] = state[8];
}
void H_14(double *state, double *unused, double *out_3272809787027093197) {
   out_3272809787027093197[0] = 0;
   out_3272809787027093197[1] = 0;
   out_3272809787027093197[2] = 0;
   out_3272809787027093197[3] = 0;
   out_3272809787027093197[4] = 0;
   out_3272809787027093197[5] = 0;
   out_3272809787027093197[6] = 1;
   out_3272809787027093197[7] = 0;
   out_3272809787027093197[8] = 0;
   out_3272809787027093197[9] = 0;
   out_3272809787027093197[10] = 0;
   out_3272809787027093197[11] = 0;
   out_3272809787027093197[12] = 0;
   out_3272809787027093197[13] = 0;
   out_3272809787027093197[14] = 0;
   out_3272809787027093197[15] = 0;
   out_3272809787027093197[16] = 0;
   out_3272809787027093197[17] = 0;
   out_3272809787027093197[18] = 0;
   out_3272809787027093197[19] = 0;
   out_3272809787027093197[20] = 0;
   out_3272809787027093197[21] = 0;
   out_3272809787027093197[22] = 0;
   out_3272809787027093197[23] = 0;
   out_3272809787027093197[24] = 0;
   out_3272809787027093197[25] = 1;
   out_3272809787027093197[26] = 0;
   out_3272809787027093197[27] = 0;
   out_3272809787027093197[28] = 0;
   out_3272809787027093197[29] = 0;
   out_3272809787027093197[30] = 0;
   out_3272809787027093197[31] = 0;
   out_3272809787027093197[32] = 0;
   out_3272809787027093197[33] = 0;
   out_3272809787027093197[34] = 0;
   out_3272809787027093197[35] = 0;
   out_3272809787027093197[36] = 0;
   out_3272809787027093197[37] = 0;
   out_3272809787027093197[38] = 0;
   out_3272809787027093197[39] = 0;
   out_3272809787027093197[40] = 0;
   out_3272809787027093197[41] = 0;
   out_3272809787027093197[42] = 0;
   out_3272809787027093197[43] = 0;
   out_3272809787027093197[44] = 1;
   out_3272809787027093197[45] = 0;
   out_3272809787027093197[46] = 0;
   out_3272809787027093197[47] = 0;
   out_3272809787027093197[48] = 0;
   out_3272809787027093197[49] = 0;
   out_3272809787027093197[50] = 0;
   out_3272809787027093197[51] = 0;
   out_3272809787027093197[52] = 0;
   out_3272809787027093197[53] = 0;
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
void pose_err_fun(double *nom_x, double *delta_x, double *out_5010206230741134473) {
  err_fun(nom_x, delta_x, out_5010206230741134473);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_1188067782326305394) {
  inv_err_fun(nom_x, true_x, out_1188067782326305394);
}
void pose_H_mod_fun(double *state, double *out_7990211645421290333) {
  H_mod_fun(state, out_7990211645421290333);
}
void pose_f_fun(double *state, double dt, double *out_2076252175851799438) {
  f_fun(state,  dt, out_2076252175851799438);
}
void pose_F_fun(double *state, double dt, double *out_5637265960027517094) {
  F_fun(state,  dt, out_5637265960027517094);
}
void pose_h_4(double *state, double *unused, double *out_4126661282704422428) {
  h_4(state, unused, out_4126661282704422428);
}
void pose_H_4(double *state, double *unused, double *out_7236050643366577726) {
  H_4(state, unused, out_7236050643366577726);
}
void pose_h_10(double *state, double *unused, double *out_8418525422339329003) {
  h_10(state, unused, out_8418525422339329003);
}
void pose_H_10(double *state, double *unused, double *out_7705227448246336422) {
  H_10(state, unused, out_7705227448246336422);
}
void pose_h_13(double *state, double *unused, double *out_1137889379193769762) {
  h_13(state, unused, out_1137889379193769762);
}
void pose_H_13(double *state, double *unused, double *out_4023776818034244925) {
  H_13(state, unused, out_4023776818034244925);
}
void pose_h_14(double *state, double *unused, double *out_3946282764828343143) {
  h_14(state, unused, out_3946282764828343143);
}
void pose_H_14(double *state, double *unused, double *out_3272809787027093197) {
  H_14(state, unused, out_3272809787027093197);
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
