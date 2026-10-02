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
void err_fun(double *nom_x, double *delta_x, double *out_2493721592867885738) {
   out_2493721592867885738[0] = delta_x[0] + nom_x[0];
   out_2493721592867885738[1] = delta_x[1] + nom_x[1];
   out_2493721592867885738[2] = delta_x[2] + nom_x[2];
   out_2493721592867885738[3] = delta_x[3] + nom_x[3];
   out_2493721592867885738[4] = delta_x[4] + nom_x[4];
   out_2493721592867885738[5] = delta_x[5] + nom_x[5];
   out_2493721592867885738[6] = delta_x[6] + nom_x[6];
   out_2493721592867885738[7] = delta_x[7] + nom_x[7];
   out_2493721592867885738[8] = delta_x[8] + nom_x[8];
   out_2493721592867885738[9] = delta_x[9] + nom_x[9];
   out_2493721592867885738[10] = delta_x[10] + nom_x[10];
   out_2493721592867885738[11] = delta_x[11] + nom_x[11];
   out_2493721592867885738[12] = delta_x[12] + nom_x[12];
   out_2493721592867885738[13] = delta_x[13] + nom_x[13];
   out_2493721592867885738[14] = delta_x[14] + nom_x[14];
   out_2493721592867885738[15] = delta_x[15] + nom_x[15];
   out_2493721592867885738[16] = delta_x[16] + nom_x[16];
   out_2493721592867885738[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_7705211639884929019) {
   out_7705211639884929019[0] = -nom_x[0] + true_x[0];
   out_7705211639884929019[1] = -nom_x[1] + true_x[1];
   out_7705211639884929019[2] = -nom_x[2] + true_x[2];
   out_7705211639884929019[3] = -nom_x[3] + true_x[3];
   out_7705211639884929019[4] = -nom_x[4] + true_x[4];
   out_7705211639884929019[5] = -nom_x[5] + true_x[5];
   out_7705211639884929019[6] = -nom_x[6] + true_x[6];
   out_7705211639884929019[7] = -nom_x[7] + true_x[7];
   out_7705211639884929019[8] = -nom_x[8] + true_x[8];
   out_7705211639884929019[9] = -nom_x[9] + true_x[9];
   out_7705211639884929019[10] = -nom_x[10] + true_x[10];
   out_7705211639884929019[11] = -nom_x[11] + true_x[11];
   out_7705211639884929019[12] = -nom_x[12] + true_x[12];
   out_7705211639884929019[13] = -nom_x[13] + true_x[13];
   out_7705211639884929019[14] = -nom_x[14] + true_x[14];
   out_7705211639884929019[15] = -nom_x[15] + true_x[15];
   out_7705211639884929019[16] = -nom_x[16] + true_x[16];
   out_7705211639884929019[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_5366119461374868342) {
   out_5366119461374868342[0] = 1.0;
   out_5366119461374868342[1] = 0.0;
   out_5366119461374868342[2] = 0.0;
   out_5366119461374868342[3] = 0.0;
   out_5366119461374868342[4] = 0.0;
   out_5366119461374868342[5] = 0.0;
   out_5366119461374868342[6] = 0.0;
   out_5366119461374868342[7] = 0.0;
   out_5366119461374868342[8] = 0.0;
   out_5366119461374868342[9] = 0.0;
   out_5366119461374868342[10] = 0.0;
   out_5366119461374868342[11] = 0.0;
   out_5366119461374868342[12] = 0.0;
   out_5366119461374868342[13] = 0.0;
   out_5366119461374868342[14] = 0.0;
   out_5366119461374868342[15] = 0.0;
   out_5366119461374868342[16] = 0.0;
   out_5366119461374868342[17] = 0.0;
   out_5366119461374868342[18] = 0.0;
   out_5366119461374868342[19] = 1.0;
   out_5366119461374868342[20] = 0.0;
   out_5366119461374868342[21] = 0.0;
   out_5366119461374868342[22] = 0.0;
   out_5366119461374868342[23] = 0.0;
   out_5366119461374868342[24] = 0.0;
   out_5366119461374868342[25] = 0.0;
   out_5366119461374868342[26] = 0.0;
   out_5366119461374868342[27] = 0.0;
   out_5366119461374868342[28] = 0.0;
   out_5366119461374868342[29] = 0.0;
   out_5366119461374868342[30] = 0.0;
   out_5366119461374868342[31] = 0.0;
   out_5366119461374868342[32] = 0.0;
   out_5366119461374868342[33] = 0.0;
   out_5366119461374868342[34] = 0.0;
   out_5366119461374868342[35] = 0.0;
   out_5366119461374868342[36] = 0.0;
   out_5366119461374868342[37] = 0.0;
   out_5366119461374868342[38] = 1.0;
   out_5366119461374868342[39] = 0.0;
   out_5366119461374868342[40] = 0.0;
   out_5366119461374868342[41] = 0.0;
   out_5366119461374868342[42] = 0.0;
   out_5366119461374868342[43] = 0.0;
   out_5366119461374868342[44] = 0.0;
   out_5366119461374868342[45] = 0.0;
   out_5366119461374868342[46] = 0.0;
   out_5366119461374868342[47] = 0.0;
   out_5366119461374868342[48] = 0.0;
   out_5366119461374868342[49] = 0.0;
   out_5366119461374868342[50] = 0.0;
   out_5366119461374868342[51] = 0.0;
   out_5366119461374868342[52] = 0.0;
   out_5366119461374868342[53] = 0.0;
   out_5366119461374868342[54] = 0.0;
   out_5366119461374868342[55] = 0.0;
   out_5366119461374868342[56] = 0.0;
   out_5366119461374868342[57] = 1.0;
   out_5366119461374868342[58] = 0.0;
   out_5366119461374868342[59] = 0.0;
   out_5366119461374868342[60] = 0.0;
   out_5366119461374868342[61] = 0.0;
   out_5366119461374868342[62] = 0.0;
   out_5366119461374868342[63] = 0.0;
   out_5366119461374868342[64] = 0.0;
   out_5366119461374868342[65] = 0.0;
   out_5366119461374868342[66] = 0.0;
   out_5366119461374868342[67] = 0.0;
   out_5366119461374868342[68] = 0.0;
   out_5366119461374868342[69] = 0.0;
   out_5366119461374868342[70] = 0.0;
   out_5366119461374868342[71] = 0.0;
   out_5366119461374868342[72] = 0.0;
   out_5366119461374868342[73] = 0.0;
   out_5366119461374868342[74] = 0.0;
   out_5366119461374868342[75] = 0.0;
   out_5366119461374868342[76] = 1.0;
   out_5366119461374868342[77] = 0.0;
   out_5366119461374868342[78] = 0.0;
   out_5366119461374868342[79] = 0.0;
   out_5366119461374868342[80] = 0.0;
   out_5366119461374868342[81] = 0.0;
   out_5366119461374868342[82] = 0.0;
   out_5366119461374868342[83] = 0.0;
   out_5366119461374868342[84] = 0.0;
   out_5366119461374868342[85] = 0.0;
   out_5366119461374868342[86] = 0.0;
   out_5366119461374868342[87] = 0.0;
   out_5366119461374868342[88] = 0.0;
   out_5366119461374868342[89] = 0.0;
   out_5366119461374868342[90] = 0.0;
   out_5366119461374868342[91] = 0.0;
   out_5366119461374868342[92] = 0.0;
   out_5366119461374868342[93] = 0.0;
   out_5366119461374868342[94] = 0.0;
   out_5366119461374868342[95] = 1.0;
   out_5366119461374868342[96] = 0.0;
   out_5366119461374868342[97] = 0.0;
   out_5366119461374868342[98] = 0.0;
   out_5366119461374868342[99] = 0.0;
   out_5366119461374868342[100] = 0.0;
   out_5366119461374868342[101] = 0.0;
   out_5366119461374868342[102] = 0.0;
   out_5366119461374868342[103] = 0.0;
   out_5366119461374868342[104] = 0.0;
   out_5366119461374868342[105] = 0.0;
   out_5366119461374868342[106] = 0.0;
   out_5366119461374868342[107] = 0.0;
   out_5366119461374868342[108] = 0.0;
   out_5366119461374868342[109] = 0.0;
   out_5366119461374868342[110] = 0.0;
   out_5366119461374868342[111] = 0.0;
   out_5366119461374868342[112] = 0.0;
   out_5366119461374868342[113] = 0.0;
   out_5366119461374868342[114] = 1.0;
   out_5366119461374868342[115] = 0.0;
   out_5366119461374868342[116] = 0.0;
   out_5366119461374868342[117] = 0.0;
   out_5366119461374868342[118] = 0.0;
   out_5366119461374868342[119] = 0.0;
   out_5366119461374868342[120] = 0.0;
   out_5366119461374868342[121] = 0.0;
   out_5366119461374868342[122] = 0.0;
   out_5366119461374868342[123] = 0.0;
   out_5366119461374868342[124] = 0.0;
   out_5366119461374868342[125] = 0.0;
   out_5366119461374868342[126] = 0.0;
   out_5366119461374868342[127] = 0.0;
   out_5366119461374868342[128] = 0.0;
   out_5366119461374868342[129] = 0.0;
   out_5366119461374868342[130] = 0.0;
   out_5366119461374868342[131] = 0.0;
   out_5366119461374868342[132] = 0.0;
   out_5366119461374868342[133] = 1.0;
   out_5366119461374868342[134] = 0.0;
   out_5366119461374868342[135] = 0.0;
   out_5366119461374868342[136] = 0.0;
   out_5366119461374868342[137] = 0.0;
   out_5366119461374868342[138] = 0.0;
   out_5366119461374868342[139] = 0.0;
   out_5366119461374868342[140] = 0.0;
   out_5366119461374868342[141] = 0.0;
   out_5366119461374868342[142] = 0.0;
   out_5366119461374868342[143] = 0.0;
   out_5366119461374868342[144] = 0.0;
   out_5366119461374868342[145] = 0.0;
   out_5366119461374868342[146] = 0.0;
   out_5366119461374868342[147] = 0.0;
   out_5366119461374868342[148] = 0.0;
   out_5366119461374868342[149] = 0.0;
   out_5366119461374868342[150] = 0.0;
   out_5366119461374868342[151] = 0.0;
   out_5366119461374868342[152] = 1.0;
   out_5366119461374868342[153] = 0.0;
   out_5366119461374868342[154] = 0.0;
   out_5366119461374868342[155] = 0.0;
   out_5366119461374868342[156] = 0.0;
   out_5366119461374868342[157] = 0.0;
   out_5366119461374868342[158] = 0.0;
   out_5366119461374868342[159] = 0.0;
   out_5366119461374868342[160] = 0.0;
   out_5366119461374868342[161] = 0.0;
   out_5366119461374868342[162] = 0.0;
   out_5366119461374868342[163] = 0.0;
   out_5366119461374868342[164] = 0.0;
   out_5366119461374868342[165] = 0.0;
   out_5366119461374868342[166] = 0.0;
   out_5366119461374868342[167] = 0.0;
   out_5366119461374868342[168] = 0.0;
   out_5366119461374868342[169] = 0.0;
   out_5366119461374868342[170] = 0.0;
   out_5366119461374868342[171] = 1.0;
   out_5366119461374868342[172] = 0.0;
   out_5366119461374868342[173] = 0.0;
   out_5366119461374868342[174] = 0.0;
   out_5366119461374868342[175] = 0.0;
   out_5366119461374868342[176] = 0.0;
   out_5366119461374868342[177] = 0.0;
   out_5366119461374868342[178] = 0.0;
   out_5366119461374868342[179] = 0.0;
   out_5366119461374868342[180] = 0.0;
   out_5366119461374868342[181] = 0.0;
   out_5366119461374868342[182] = 0.0;
   out_5366119461374868342[183] = 0.0;
   out_5366119461374868342[184] = 0.0;
   out_5366119461374868342[185] = 0.0;
   out_5366119461374868342[186] = 0.0;
   out_5366119461374868342[187] = 0.0;
   out_5366119461374868342[188] = 0.0;
   out_5366119461374868342[189] = 0.0;
   out_5366119461374868342[190] = 1.0;
   out_5366119461374868342[191] = 0.0;
   out_5366119461374868342[192] = 0.0;
   out_5366119461374868342[193] = 0.0;
   out_5366119461374868342[194] = 0.0;
   out_5366119461374868342[195] = 0.0;
   out_5366119461374868342[196] = 0.0;
   out_5366119461374868342[197] = 0.0;
   out_5366119461374868342[198] = 0.0;
   out_5366119461374868342[199] = 0.0;
   out_5366119461374868342[200] = 0.0;
   out_5366119461374868342[201] = 0.0;
   out_5366119461374868342[202] = 0.0;
   out_5366119461374868342[203] = 0.0;
   out_5366119461374868342[204] = 0.0;
   out_5366119461374868342[205] = 0.0;
   out_5366119461374868342[206] = 0.0;
   out_5366119461374868342[207] = 0.0;
   out_5366119461374868342[208] = 0.0;
   out_5366119461374868342[209] = 1.0;
   out_5366119461374868342[210] = 0.0;
   out_5366119461374868342[211] = 0.0;
   out_5366119461374868342[212] = 0.0;
   out_5366119461374868342[213] = 0.0;
   out_5366119461374868342[214] = 0.0;
   out_5366119461374868342[215] = 0.0;
   out_5366119461374868342[216] = 0.0;
   out_5366119461374868342[217] = 0.0;
   out_5366119461374868342[218] = 0.0;
   out_5366119461374868342[219] = 0.0;
   out_5366119461374868342[220] = 0.0;
   out_5366119461374868342[221] = 0.0;
   out_5366119461374868342[222] = 0.0;
   out_5366119461374868342[223] = 0.0;
   out_5366119461374868342[224] = 0.0;
   out_5366119461374868342[225] = 0.0;
   out_5366119461374868342[226] = 0.0;
   out_5366119461374868342[227] = 0.0;
   out_5366119461374868342[228] = 1.0;
   out_5366119461374868342[229] = 0.0;
   out_5366119461374868342[230] = 0.0;
   out_5366119461374868342[231] = 0.0;
   out_5366119461374868342[232] = 0.0;
   out_5366119461374868342[233] = 0.0;
   out_5366119461374868342[234] = 0.0;
   out_5366119461374868342[235] = 0.0;
   out_5366119461374868342[236] = 0.0;
   out_5366119461374868342[237] = 0.0;
   out_5366119461374868342[238] = 0.0;
   out_5366119461374868342[239] = 0.0;
   out_5366119461374868342[240] = 0.0;
   out_5366119461374868342[241] = 0.0;
   out_5366119461374868342[242] = 0.0;
   out_5366119461374868342[243] = 0.0;
   out_5366119461374868342[244] = 0.0;
   out_5366119461374868342[245] = 0.0;
   out_5366119461374868342[246] = 0.0;
   out_5366119461374868342[247] = 1.0;
   out_5366119461374868342[248] = 0.0;
   out_5366119461374868342[249] = 0.0;
   out_5366119461374868342[250] = 0.0;
   out_5366119461374868342[251] = 0.0;
   out_5366119461374868342[252] = 0.0;
   out_5366119461374868342[253] = 0.0;
   out_5366119461374868342[254] = 0.0;
   out_5366119461374868342[255] = 0.0;
   out_5366119461374868342[256] = 0.0;
   out_5366119461374868342[257] = 0.0;
   out_5366119461374868342[258] = 0.0;
   out_5366119461374868342[259] = 0.0;
   out_5366119461374868342[260] = 0.0;
   out_5366119461374868342[261] = 0.0;
   out_5366119461374868342[262] = 0.0;
   out_5366119461374868342[263] = 0.0;
   out_5366119461374868342[264] = 0.0;
   out_5366119461374868342[265] = 0.0;
   out_5366119461374868342[266] = 1.0;
   out_5366119461374868342[267] = 0.0;
   out_5366119461374868342[268] = 0.0;
   out_5366119461374868342[269] = 0.0;
   out_5366119461374868342[270] = 0.0;
   out_5366119461374868342[271] = 0.0;
   out_5366119461374868342[272] = 0.0;
   out_5366119461374868342[273] = 0.0;
   out_5366119461374868342[274] = 0.0;
   out_5366119461374868342[275] = 0.0;
   out_5366119461374868342[276] = 0.0;
   out_5366119461374868342[277] = 0.0;
   out_5366119461374868342[278] = 0.0;
   out_5366119461374868342[279] = 0.0;
   out_5366119461374868342[280] = 0.0;
   out_5366119461374868342[281] = 0.0;
   out_5366119461374868342[282] = 0.0;
   out_5366119461374868342[283] = 0.0;
   out_5366119461374868342[284] = 0.0;
   out_5366119461374868342[285] = 1.0;
   out_5366119461374868342[286] = 0.0;
   out_5366119461374868342[287] = 0.0;
   out_5366119461374868342[288] = 0.0;
   out_5366119461374868342[289] = 0.0;
   out_5366119461374868342[290] = 0.0;
   out_5366119461374868342[291] = 0.0;
   out_5366119461374868342[292] = 0.0;
   out_5366119461374868342[293] = 0.0;
   out_5366119461374868342[294] = 0.0;
   out_5366119461374868342[295] = 0.0;
   out_5366119461374868342[296] = 0.0;
   out_5366119461374868342[297] = 0.0;
   out_5366119461374868342[298] = 0.0;
   out_5366119461374868342[299] = 0.0;
   out_5366119461374868342[300] = 0.0;
   out_5366119461374868342[301] = 0.0;
   out_5366119461374868342[302] = 0.0;
   out_5366119461374868342[303] = 0.0;
   out_5366119461374868342[304] = 1.0;
   out_5366119461374868342[305] = 0.0;
   out_5366119461374868342[306] = 0.0;
   out_5366119461374868342[307] = 0.0;
   out_5366119461374868342[308] = 0.0;
   out_5366119461374868342[309] = 0.0;
   out_5366119461374868342[310] = 0.0;
   out_5366119461374868342[311] = 0.0;
   out_5366119461374868342[312] = 0.0;
   out_5366119461374868342[313] = 0.0;
   out_5366119461374868342[314] = 0.0;
   out_5366119461374868342[315] = 0.0;
   out_5366119461374868342[316] = 0.0;
   out_5366119461374868342[317] = 0.0;
   out_5366119461374868342[318] = 0.0;
   out_5366119461374868342[319] = 0.0;
   out_5366119461374868342[320] = 0.0;
   out_5366119461374868342[321] = 0.0;
   out_5366119461374868342[322] = 0.0;
   out_5366119461374868342[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_6027033949105645460) {
   out_6027033949105645460[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_6027033949105645460[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_6027033949105645460[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_6027033949105645460[3] = dt*state[12] + state[3];
   out_6027033949105645460[4] = dt*state[13] + state[4];
   out_6027033949105645460[5] = dt*state[14] + state[5];
   out_6027033949105645460[6] = state[6];
   out_6027033949105645460[7] = state[7];
   out_6027033949105645460[8] = state[8];
   out_6027033949105645460[9] = state[9];
   out_6027033949105645460[10] = state[10];
   out_6027033949105645460[11] = state[11];
   out_6027033949105645460[12] = state[12];
   out_6027033949105645460[13] = state[13];
   out_6027033949105645460[14] = state[14];
   out_6027033949105645460[15] = state[15];
   out_6027033949105645460[16] = state[16];
   out_6027033949105645460[17] = state[17];
}
void F_fun(double *state, double dt, double *out_3018765872118070900) {
   out_3018765872118070900[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_3018765872118070900[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_3018765872118070900[2] = 0;
   out_3018765872118070900[3] = 0;
   out_3018765872118070900[4] = 0;
   out_3018765872118070900[5] = 0;
   out_3018765872118070900[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_3018765872118070900[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_3018765872118070900[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_3018765872118070900[9] = 0;
   out_3018765872118070900[10] = 0;
   out_3018765872118070900[11] = 0;
   out_3018765872118070900[12] = 0;
   out_3018765872118070900[13] = 0;
   out_3018765872118070900[14] = 0;
   out_3018765872118070900[15] = 0;
   out_3018765872118070900[16] = 0;
   out_3018765872118070900[17] = 0;
   out_3018765872118070900[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_3018765872118070900[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_3018765872118070900[20] = 0;
   out_3018765872118070900[21] = 0;
   out_3018765872118070900[22] = 0;
   out_3018765872118070900[23] = 0;
   out_3018765872118070900[24] = 0;
   out_3018765872118070900[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_3018765872118070900[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_3018765872118070900[27] = 0;
   out_3018765872118070900[28] = 0;
   out_3018765872118070900[29] = 0;
   out_3018765872118070900[30] = 0;
   out_3018765872118070900[31] = 0;
   out_3018765872118070900[32] = 0;
   out_3018765872118070900[33] = 0;
   out_3018765872118070900[34] = 0;
   out_3018765872118070900[35] = 0;
   out_3018765872118070900[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_3018765872118070900[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_3018765872118070900[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_3018765872118070900[39] = 0;
   out_3018765872118070900[40] = 0;
   out_3018765872118070900[41] = 0;
   out_3018765872118070900[42] = 0;
   out_3018765872118070900[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_3018765872118070900[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_3018765872118070900[45] = 0;
   out_3018765872118070900[46] = 0;
   out_3018765872118070900[47] = 0;
   out_3018765872118070900[48] = 0;
   out_3018765872118070900[49] = 0;
   out_3018765872118070900[50] = 0;
   out_3018765872118070900[51] = 0;
   out_3018765872118070900[52] = 0;
   out_3018765872118070900[53] = 0;
   out_3018765872118070900[54] = 0;
   out_3018765872118070900[55] = 0;
   out_3018765872118070900[56] = 0;
   out_3018765872118070900[57] = 1;
   out_3018765872118070900[58] = 0;
   out_3018765872118070900[59] = 0;
   out_3018765872118070900[60] = 0;
   out_3018765872118070900[61] = 0;
   out_3018765872118070900[62] = 0;
   out_3018765872118070900[63] = 0;
   out_3018765872118070900[64] = 0;
   out_3018765872118070900[65] = 0;
   out_3018765872118070900[66] = dt;
   out_3018765872118070900[67] = 0;
   out_3018765872118070900[68] = 0;
   out_3018765872118070900[69] = 0;
   out_3018765872118070900[70] = 0;
   out_3018765872118070900[71] = 0;
   out_3018765872118070900[72] = 0;
   out_3018765872118070900[73] = 0;
   out_3018765872118070900[74] = 0;
   out_3018765872118070900[75] = 0;
   out_3018765872118070900[76] = 1;
   out_3018765872118070900[77] = 0;
   out_3018765872118070900[78] = 0;
   out_3018765872118070900[79] = 0;
   out_3018765872118070900[80] = 0;
   out_3018765872118070900[81] = 0;
   out_3018765872118070900[82] = 0;
   out_3018765872118070900[83] = 0;
   out_3018765872118070900[84] = 0;
   out_3018765872118070900[85] = dt;
   out_3018765872118070900[86] = 0;
   out_3018765872118070900[87] = 0;
   out_3018765872118070900[88] = 0;
   out_3018765872118070900[89] = 0;
   out_3018765872118070900[90] = 0;
   out_3018765872118070900[91] = 0;
   out_3018765872118070900[92] = 0;
   out_3018765872118070900[93] = 0;
   out_3018765872118070900[94] = 0;
   out_3018765872118070900[95] = 1;
   out_3018765872118070900[96] = 0;
   out_3018765872118070900[97] = 0;
   out_3018765872118070900[98] = 0;
   out_3018765872118070900[99] = 0;
   out_3018765872118070900[100] = 0;
   out_3018765872118070900[101] = 0;
   out_3018765872118070900[102] = 0;
   out_3018765872118070900[103] = 0;
   out_3018765872118070900[104] = dt;
   out_3018765872118070900[105] = 0;
   out_3018765872118070900[106] = 0;
   out_3018765872118070900[107] = 0;
   out_3018765872118070900[108] = 0;
   out_3018765872118070900[109] = 0;
   out_3018765872118070900[110] = 0;
   out_3018765872118070900[111] = 0;
   out_3018765872118070900[112] = 0;
   out_3018765872118070900[113] = 0;
   out_3018765872118070900[114] = 1;
   out_3018765872118070900[115] = 0;
   out_3018765872118070900[116] = 0;
   out_3018765872118070900[117] = 0;
   out_3018765872118070900[118] = 0;
   out_3018765872118070900[119] = 0;
   out_3018765872118070900[120] = 0;
   out_3018765872118070900[121] = 0;
   out_3018765872118070900[122] = 0;
   out_3018765872118070900[123] = 0;
   out_3018765872118070900[124] = 0;
   out_3018765872118070900[125] = 0;
   out_3018765872118070900[126] = 0;
   out_3018765872118070900[127] = 0;
   out_3018765872118070900[128] = 0;
   out_3018765872118070900[129] = 0;
   out_3018765872118070900[130] = 0;
   out_3018765872118070900[131] = 0;
   out_3018765872118070900[132] = 0;
   out_3018765872118070900[133] = 1;
   out_3018765872118070900[134] = 0;
   out_3018765872118070900[135] = 0;
   out_3018765872118070900[136] = 0;
   out_3018765872118070900[137] = 0;
   out_3018765872118070900[138] = 0;
   out_3018765872118070900[139] = 0;
   out_3018765872118070900[140] = 0;
   out_3018765872118070900[141] = 0;
   out_3018765872118070900[142] = 0;
   out_3018765872118070900[143] = 0;
   out_3018765872118070900[144] = 0;
   out_3018765872118070900[145] = 0;
   out_3018765872118070900[146] = 0;
   out_3018765872118070900[147] = 0;
   out_3018765872118070900[148] = 0;
   out_3018765872118070900[149] = 0;
   out_3018765872118070900[150] = 0;
   out_3018765872118070900[151] = 0;
   out_3018765872118070900[152] = 1;
   out_3018765872118070900[153] = 0;
   out_3018765872118070900[154] = 0;
   out_3018765872118070900[155] = 0;
   out_3018765872118070900[156] = 0;
   out_3018765872118070900[157] = 0;
   out_3018765872118070900[158] = 0;
   out_3018765872118070900[159] = 0;
   out_3018765872118070900[160] = 0;
   out_3018765872118070900[161] = 0;
   out_3018765872118070900[162] = 0;
   out_3018765872118070900[163] = 0;
   out_3018765872118070900[164] = 0;
   out_3018765872118070900[165] = 0;
   out_3018765872118070900[166] = 0;
   out_3018765872118070900[167] = 0;
   out_3018765872118070900[168] = 0;
   out_3018765872118070900[169] = 0;
   out_3018765872118070900[170] = 0;
   out_3018765872118070900[171] = 1;
   out_3018765872118070900[172] = 0;
   out_3018765872118070900[173] = 0;
   out_3018765872118070900[174] = 0;
   out_3018765872118070900[175] = 0;
   out_3018765872118070900[176] = 0;
   out_3018765872118070900[177] = 0;
   out_3018765872118070900[178] = 0;
   out_3018765872118070900[179] = 0;
   out_3018765872118070900[180] = 0;
   out_3018765872118070900[181] = 0;
   out_3018765872118070900[182] = 0;
   out_3018765872118070900[183] = 0;
   out_3018765872118070900[184] = 0;
   out_3018765872118070900[185] = 0;
   out_3018765872118070900[186] = 0;
   out_3018765872118070900[187] = 0;
   out_3018765872118070900[188] = 0;
   out_3018765872118070900[189] = 0;
   out_3018765872118070900[190] = 1;
   out_3018765872118070900[191] = 0;
   out_3018765872118070900[192] = 0;
   out_3018765872118070900[193] = 0;
   out_3018765872118070900[194] = 0;
   out_3018765872118070900[195] = 0;
   out_3018765872118070900[196] = 0;
   out_3018765872118070900[197] = 0;
   out_3018765872118070900[198] = 0;
   out_3018765872118070900[199] = 0;
   out_3018765872118070900[200] = 0;
   out_3018765872118070900[201] = 0;
   out_3018765872118070900[202] = 0;
   out_3018765872118070900[203] = 0;
   out_3018765872118070900[204] = 0;
   out_3018765872118070900[205] = 0;
   out_3018765872118070900[206] = 0;
   out_3018765872118070900[207] = 0;
   out_3018765872118070900[208] = 0;
   out_3018765872118070900[209] = 1;
   out_3018765872118070900[210] = 0;
   out_3018765872118070900[211] = 0;
   out_3018765872118070900[212] = 0;
   out_3018765872118070900[213] = 0;
   out_3018765872118070900[214] = 0;
   out_3018765872118070900[215] = 0;
   out_3018765872118070900[216] = 0;
   out_3018765872118070900[217] = 0;
   out_3018765872118070900[218] = 0;
   out_3018765872118070900[219] = 0;
   out_3018765872118070900[220] = 0;
   out_3018765872118070900[221] = 0;
   out_3018765872118070900[222] = 0;
   out_3018765872118070900[223] = 0;
   out_3018765872118070900[224] = 0;
   out_3018765872118070900[225] = 0;
   out_3018765872118070900[226] = 0;
   out_3018765872118070900[227] = 0;
   out_3018765872118070900[228] = 1;
   out_3018765872118070900[229] = 0;
   out_3018765872118070900[230] = 0;
   out_3018765872118070900[231] = 0;
   out_3018765872118070900[232] = 0;
   out_3018765872118070900[233] = 0;
   out_3018765872118070900[234] = 0;
   out_3018765872118070900[235] = 0;
   out_3018765872118070900[236] = 0;
   out_3018765872118070900[237] = 0;
   out_3018765872118070900[238] = 0;
   out_3018765872118070900[239] = 0;
   out_3018765872118070900[240] = 0;
   out_3018765872118070900[241] = 0;
   out_3018765872118070900[242] = 0;
   out_3018765872118070900[243] = 0;
   out_3018765872118070900[244] = 0;
   out_3018765872118070900[245] = 0;
   out_3018765872118070900[246] = 0;
   out_3018765872118070900[247] = 1;
   out_3018765872118070900[248] = 0;
   out_3018765872118070900[249] = 0;
   out_3018765872118070900[250] = 0;
   out_3018765872118070900[251] = 0;
   out_3018765872118070900[252] = 0;
   out_3018765872118070900[253] = 0;
   out_3018765872118070900[254] = 0;
   out_3018765872118070900[255] = 0;
   out_3018765872118070900[256] = 0;
   out_3018765872118070900[257] = 0;
   out_3018765872118070900[258] = 0;
   out_3018765872118070900[259] = 0;
   out_3018765872118070900[260] = 0;
   out_3018765872118070900[261] = 0;
   out_3018765872118070900[262] = 0;
   out_3018765872118070900[263] = 0;
   out_3018765872118070900[264] = 0;
   out_3018765872118070900[265] = 0;
   out_3018765872118070900[266] = 1;
   out_3018765872118070900[267] = 0;
   out_3018765872118070900[268] = 0;
   out_3018765872118070900[269] = 0;
   out_3018765872118070900[270] = 0;
   out_3018765872118070900[271] = 0;
   out_3018765872118070900[272] = 0;
   out_3018765872118070900[273] = 0;
   out_3018765872118070900[274] = 0;
   out_3018765872118070900[275] = 0;
   out_3018765872118070900[276] = 0;
   out_3018765872118070900[277] = 0;
   out_3018765872118070900[278] = 0;
   out_3018765872118070900[279] = 0;
   out_3018765872118070900[280] = 0;
   out_3018765872118070900[281] = 0;
   out_3018765872118070900[282] = 0;
   out_3018765872118070900[283] = 0;
   out_3018765872118070900[284] = 0;
   out_3018765872118070900[285] = 1;
   out_3018765872118070900[286] = 0;
   out_3018765872118070900[287] = 0;
   out_3018765872118070900[288] = 0;
   out_3018765872118070900[289] = 0;
   out_3018765872118070900[290] = 0;
   out_3018765872118070900[291] = 0;
   out_3018765872118070900[292] = 0;
   out_3018765872118070900[293] = 0;
   out_3018765872118070900[294] = 0;
   out_3018765872118070900[295] = 0;
   out_3018765872118070900[296] = 0;
   out_3018765872118070900[297] = 0;
   out_3018765872118070900[298] = 0;
   out_3018765872118070900[299] = 0;
   out_3018765872118070900[300] = 0;
   out_3018765872118070900[301] = 0;
   out_3018765872118070900[302] = 0;
   out_3018765872118070900[303] = 0;
   out_3018765872118070900[304] = 1;
   out_3018765872118070900[305] = 0;
   out_3018765872118070900[306] = 0;
   out_3018765872118070900[307] = 0;
   out_3018765872118070900[308] = 0;
   out_3018765872118070900[309] = 0;
   out_3018765872118070900[310] = 0;
   out_3018765872118070900[311] = 0;
   out_3018765872118070900[312] = 0;
   out_3018765872118070900[313] = 0;
   out_3018765872118070900[314] = 0;
   out_3018765872118070900[315] = 0;
   out_3018765872118070900[316] = 0;
   out_3018765872118070900[317] = 0;
   out_3018765872118070900[318] = 0;
   out_3018765872118070900[319] = 0;
   out_3018765872118070900[320] = 0;
   out_3018765872118070900[321] = 0;
   out_3018765872118070900[322] = 0;
   out_3018765872118070900[323] = 1;
}
void h_4(double *state, double *unused, double *out_8360223364191194135) {
   out_8360223364191194135[0] = state[6] + state[9];
   out_8360223364191194135[1] = state[7] + state[10];
   out_8360223364191194135[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_2834185422598356425) {
   out_2834185422598356425[0] = 0;
   out_2834185422598356425[1] = 0;
   out_2834185422598356425[2] = 0;
   out_2834185422598356425[3] = 0;
   out_2834185422598356425[4] = 0;
   out_2834185422598356425[5] = 0;
   out_2834185422598356425[6] = 1;
   out_2834185422598356425[7] = 0;
   out_2834185422598356425[8] = 0;
   out_2834185422598356425[9] = 1;
   out_2834185422598356425[10] = 0;
   out_2834185422598356425[11] = 0;
   out_2834185422598356425[12] = 0;
   out_2834185422598356425[13] = 0;
   out_2834185422598356425[14] = 0;
   out_2834185422598356425[15] = 0;
   out_2834185422598356425[16] = 0;
   out_2834185422598356425[17] = 0;
   out_2834185422598356425[18] = 0;
   out_2834185422598356425[19] = 0;
   out_2834185422598356425[20] = 0;
   out_2834185422598356425[21] = 0;
   out_2834185422598356425[22] = 0;
   out_2834185422598356425[23] = 0;
   out_2834185422598356425[24] = 0;
   out_2834185422598356425[25] = 1;
   out_2834185422598356425[26] = 0;
   out_2834185422598356425[27] = 0;
   out_2834185422598356425[28] = 1;
   out_2834185422598356425[29] = 0;
   out_2834185422598356425[30] = 0;
   out_2834185422598356425[31] = 0;
   out_2834185422598356425[32] = 0;
   out_2834185422598356425[33] = 0;
   out_2834185422598356425[34] = 0;
   out_2834185422598356425[35] = 0;
   out_2834185422598356425[36] = 0;
   out_2834185422598356425[37] = 0;
   out_2834185422598356425[38] = 0;
   out_2834185422598356425[39] = 0;
   out_2834185422598356425[40] = 0;
   out_2834185422598356425[41] = 0;
   out_2834185422598356425[42] = 0;
   out_2834185422598356425[43] = 0;
   out_2834185422598356425[44] = 1;
   out_2834185422598356425[45] = 0;
   out_2834185422598356425[46] = 0;
   out_2834185422598356425[47] = 1;
   out_2834185422598356425[48] = 0;
   out_2834185422598356425[49] = 0;
   out_2834185422598356425[50] = 0;
   out_2834185422598356425[51] = 0;
   out_2834185422598356425[52] = 0;
   out_2834185422598356425[53] = 0;
}
void h_10(double *state, double *unused, double *out_8320173138289403317) {
   out_8320173138289403317[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_8320173138289403317[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_8320173138289403317[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_3734892584971238307) {
   out_3734892584971238307[0] = 0;
   out_3734892584971238307[1] = 9.8100000000000005*cos(state[1]);
   out_3734892584971238307[2] = 0;
   out_3734892584971238307[3] = 0;
   out_3734892584971238307[4] = -state[8];
   out_3734892584971238307[5] = state[7];
   out_3734892584971238307[6] = 0;
   out_3734892584971238307[7] = state[5];
   out_3734892584971238307[8] = -state[4];
   out_3734892584971238307[9] = 0;
   out_3734892584971238307[10] = 0;
   out_3734892584971238307[11] = 0;
   out_3734892584971238307[12] = 1;
   out_3734892584971238307[13] = 0;
   out_3734892584971238307[14] = 0;
   out_3734892584971238307[15] = 1;
   out_3734892584971238307[16] = 0;
   out_3734892584971238307[17] = 0;
   out_3734892584971238307[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_3734892584971238307[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_3734892584971238307[20] = 0;
   out_3734892584971238307[21] = state[8];
   out_3734892584971238307[22] = 0;
   out_3734892584971238307[23] = -state[6];
   out_3734892584971238307[24] = -state[5];
   out_3734892584971238307[25] = 0;
   out_3734892584971238307[26] = state[3];
   out_3734892584971238307[27] = 0;
   out_3734892584971238307[28] = 0;
   out_3734892584971238307[29] = 0;
   out_3734892584971238307[30] = 0;
   out_3734892584971238307[31] = 1;
   out_3734892584971238307[32] = 0;
   out_3734892584971238307[33] = 0;
   out_3734892584971238307[34] = 1;
   out_3734892584971238307[35] = 0;
   out_3734892584971238307[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_3734892584971238307[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_3734892584971238307[38] = 0;
   out_3734892584971238307[39] = -state[7];
   out_3734892584971238307[40] = state[6];
   out_3734892584971238307[41] = 0;
   out_3734892584971238307[42] = state[4];
   out_3734892584971238307[43] = -state[3];
   out_3734892584971238307[44] = 0;
   out_3734892584971238307[45] = 0;
   out_3734892584971238307[46] = 0;
   out_3734892584971238307[47] = 0;
   out_3734892584971238307[48] = 0;
   out_3734892584971238307[49] = 0;
   out_3734892584971238307[50] = 1;
   out_3734892584971238307[51] = 0;
   out_3734892584971238307[52] = 0;
   out_3734892584971238307[53] = 1;
}
void h_13(double *state, double *unused, double *out_2356519242840275727) {
   out_2356519242840275727[0] = state[3];
   out_2356519242840275727[1] = state[4];
   out_2356519242840275727[2] = state[5];
}
void H_13(double *state, double *unused, double *out_8001927442794494262) {
   out_8001927442794494262[0] = 0;
   out_8001927442794494262[1] = 0;
   out_8001927442794494262[2] = 0;
   out_8001927442794494262[3] = 1;
   out_8001927442794494262[4] = 0;
   out_8001927442794494262[5] = 0;
   out_8001927442794494262[6] = 0;
   out_8001927442794494262[7] = 0;
   out_8001927442794494262[8] = 0;
   out_8001927442794494262[9] = 0;
   out_8001927442794494262[10] = 0;
   out_8001927442794494262[11] = 0;
   out_8001927442794494262[12] = 0;
   out_8001927442794494262[13] = 0;
   out_8001927442794494262[14] = 0;
   out_8001927442794494262[15] = 0;
   out_8001927442794494262[16] = 0;
   out_8001927442794494262[17] = 0;
   out_8001927442794494262[18] = 0;
   out_8001927442794494262[19] = 0;
   out_8001927442794494262[20] = 0;
   out_8001927442794494262[21] = 0;
   out_8001927442794494262[22] = 1;
   out_8001927442794494262[23] = 0;
   out_8001927442794494262[24] = 0;
   out_8001927442794494262[25] = 0;
   out_8001927442794494262[26] = 0;
   out_8001927442794494262[27] = 0;
   out_8001927442794494262[28] = 0;
   out_8001927442794494262[29] = 0;
   out_8001927442794494262[30] = 0;
   out_8001927442794494262[31] = 0;
   out_8001927442794494262[32] = 0;
   out_8001927442794494262[33] = 0;
   out_8001927442794494262[34] = 0;
   out_8001927442794494262[35] = 0;
   out_8001927442794494262[36] = 0;
   out_8001927442794494262[37] = 0;
   out_8001927442794494262[38] = 0;
   out_8001927442794494262[39] = 0;
   out_8001927442794494262[40] = 0;
   out_8001927442794494262[41] = 1;
   out_8001927442794494262[42] = 0;
   out_8001927442794494262[43] = 0;
   out_8001927442794494262[44] = 0;
   out_8001927442794494262[45] = 0;
   out_8001927442794494262[46] = 0;
   out_8001927442794494262[47] = 0;
   out_8001927442794494262[48] = 0;
   out_8001927442794494262[49] = 0;
   out_8001927442794494262[50] = 0;
   out_8001927442794494262[51] = 0;
   out_8001927442794494262[52] = 0;
   out_8001927442794494262[53] = 0;
}
void h_14(double *state, double *unused, double *out_3701937905252005950) {
   out_3701937905252005950[0] = state[6];
   out_3701937905252005950[1] = state[7];
   out_3701937905252005950[2] = state[8];
}
void H_14(double *state, double *unused, double *out_6797426278937840954) {
   out_6797426278937840954[0] = 0;
   out_6797426278937840954[1] = 0;
   out_6797426278937840954[2] = 0;
   out_6797426278937840954[3] = 0;
   out_6797426278937840954[4] = 0;
   out_6797426278937840954[5] = 0;
   out_6797426278937840954[6] = 1;
   out_6797426278937840954[7] = 0;
   out_6797426278937840954[8] = 0;
   out_6797426278937840954[9] = 0;
   out_6797426278937840954[10] = 0;
   out_6797426278937840954[11] = 0;
   out_6797426278937840954[12] = 0;
   out_6797426278937840954[13] = 0;
   out_6797426278937840954[14] = 0;
   out_6797426278937840954[15] = 0;
   out_6797426278937840954[16] = 0;
   out_6797426278937840954[17] = 0;
   out_6797426278937840954[18] = 0;
   out_6797426278937840954[19] = 0;
   out_6797426278937840954[20] = 0;
   out_6797426278937840954[21] = 0;
   out_6797426278937840954[22] = 0;
   out_6797426278937840954[23] = 0;
   out_6797426278937840954[24] = 0;
   out_6797426278937840954[25] = 1;
   out_6797426278937840954[26] = 0;
   out_6797426278937840954[27] = 0;
   out_6797426278937840954[28] = 0;
   out_6797426278937840954[29] = 0;
   out_6797426278937840954[30] = 0;
   out_6797426278937840954[31] = 0;
   out_6797426278937840954[32] = 0;
   out_6797426278937840954[33] = 0;
   out_6797426278937840954[34] = 0;
   out_6797426278937840954[35] = 0;
   out_6797426278937840954[36] = 0;
   out_6797426278937840954[37] = 0;
   out_6797426278937840954[38] = 0;
   out_6797426278937840954[39] = 0;
   out_6797426278937840954[40] = 0;
   out_6797426278937840954[41] = 0;
   out_6797426278937840954[42] = 0;
   out_6797426278937840954[43] = 0;
   out_6797426278937840954[44] = 1;
   out_6797426278937840954[45] = 0;
   out_6797426278937840954[46] = 0;
   out_6797426278937840954[47] = 0;
   out_6797426278937840954[48] = 0;
   out_6797426278937840954[49] = 0;
   out_6797426278937840954[50] = 0;
   out_6797426278937840954[51] = 0;
   out_6797426278937840954[52] = 0;
   out_6797426278937840954[53] = 0;
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
void pose_err_fun(double *nom_x, double *delta_x, double *out_2493721592867885738) {
  err_fun(nom_x, delta_x, out_2493721592867885738);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_7705211639884929019) {
  inv_err_fun(nom_x, true_x, out_7705211639884929019);
}
void pose_H_mod_fun(double *state, double *out_5366119461374868342) {
  H_mod_fun(state, out_5366119461374868342);
}
void pose_f_fun(double *state, double dt, double *out_6027033949105645460) {
  f_fun(state,  dt, out_6027033949105645460);
}
void pose_F_fun(double *state, double dt, double *out_3018765872118070900) {
  F_fun(state,  dt, out_3018765872118070900);
}
void pose_h_4(double *state, double *unused, double *out_8360223364191194135) {
  h_4(state, unused, out_8360223364191194135);
}
void pose_H_4(double *state, double *unused, double *out_2834185422598356425) {
  H_4(state, unused, out_2834185422598356425);
}
void pose_h_10(double *state, double *unused, double *out_8320173138289403317) {
  h_10(state, unused, out_8320173138289403317);
}
void pose_H_10(double *state, double *unused, double *out_3734892584971238307) {
  H_10(state, unused, out_3734892584971238307);
}
void pose_h_13(double *state, double *unused, double *out_2356519242840275727) {
  h_13(state, unused, out_2356519242840275727);
}
void pose_H_13(double *state, double *unused, double *out_8001927442794494262) {
  H_13(state, unused, out_8001927442794494262);
}
void pose_h_14(double *state, double *unused, double *out_3701937905252005950) {
  h_14(state, unused, out_3701937905252005950);
}
void pose_H_14(double *state, double *unused, double *out_6797426278937840954) {
  H_14(state, unused, out_6797426278937840954);
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
