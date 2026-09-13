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
void err_fun(double *nom_x, double *delta_x, double *out_7437794640769795433) {
   out_7437794640769795433[0] = delta_x[0] + nom_x[0];
   out_7437794640769795433[1] = delta_x[1] + nom_x[1];
   out_7437794640769795433[2] = delta_x[2] + nom_x[2];
   out_7437794640769795433[3] = delta_x[3] + nom_x[3];
   out_7437794640769795433[4] = delta_x[4] + nom_x[4];
   out_7437794640769795433[5] = delta_x[5] + nom_x[5];
   out_7437794640769795433[6] = delta_x[6] + nom_x[6];
   out_7437794640769795433[7] = delta_x[7] + nom_x[7];
   out_7437794640769795433[8] = delta_x[8] + nom_x[8];
   out_7437794640769795433[9] = delta_x[9] + nom_x[9];
   out_7437794640769795433[10] = delta_x[10] + nom_x[10];
   out_7437794640769795433[11] = delta_x[11] + nom_x[11];
   out_7437794640769795433[12] = delta_x[12] + nom_x[12];
   out_7437794640769795433[13] = delta_x[13] + nom_x[13];
   out_7437794640769795433[14] = delta_x[14] + nom_x[14];
   out_7437794640769795433[15] = delta_x[15] + nom_x[15];
   out_7437794640769795433[16] = delta_x[16] + nom_x[16];
   out_7437794640769795433[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_2037082783356591262) {
   out_2037082783356591262[0] = -nom_x[0] + true_x[0];
   out_2037082783356591262[1] = -nom_x[1] + true_x[1];
   out_2037082783356591262[2] = -nom_x[2] + true_x[2];
   out_2037082783356591262[3] = -nom_x[3] + true_x[3];
   out_2037082783356591262[4] = -nom_x[4] + true_x[4];
   out_2037082783356591262[5] = -nom_x[5] + true_x[5];
   out_2037082783356591262[6] = -nom_x[6] + true_x[6];
   out_2037082783356591262[7] = -nom_x[7] + true_x[7];
   out_2037082783356591262[8] = -nom_x[8] + true_x[8];
   out_2037082783356591262[9] = -nom_x[9] + true_x[9];
   out_2037082783356591262[10] = -nom_x[10] + true_x[10];
   out_2037082783356591262[11] = -nom_x[11] + true_x[11];
   out_2037082783356591262[12] = -nom_x[12] + true_x[12];
   out_2037082783356591262[13] = -nom_x[13] + true_x[13];
   out_2037082783356591262[14] = -nom_x[14] + true_x[14];
   out_2037082783356591262[15] = -nom_x[15] + true_x[15];
   out_2037082783356591262[16] = -nom_x[16] + true_x[16];
   out_2037082783356591262[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_6997830721327979188) {
   out_6997830721327979188[0] = 1.0;
   out_6997830721327979188[1] = 0.0;
   out_6997830721327979188[2] = 0.0;
   out_6997830721327979188[3] = 0.0;
   out_6997830721327979188[4] = 0.0;
   out_6997830721327979188[5] = 0.0;
   out_6997830721327979188[6] = 0.0;
   out_6997830721327979188[7] = 0.0;
   out_6997830721327979188[8] = 0.0;
   out_6997830721327979188[9] = 0.0;
   out_6997830721327979188[10] = 0.0;
   out_6997830721327979188[11] = 0.0;
   out_6997830721327979188[12] = 0.0;
   out_6997830721327979188[13] = 0.0;
   out_6997830721327979188[14] = 0.0;
   out_6997830721327979188[15] = 0.0;
   out_6997830721327979188[16] = 0.0;
   out_6997830721327979188[17] = 0.0;
   out_6997830721327979188[18] = 0.0;
   out_6997830721327979188[19] = 1.0;
   out_6997830721327979188[20] = 0.0;
   out_6997830721327979188[21] = 0.0;
   out_6997830721327979188[22] = 0.0;
   out_6997830721327979188[23] = 0.0;
   out_6997830721327979188[24] = 0.0;
   out_6997830721327979188[25] = 0.0;
   out_6997830721327979188[26] = 0.0;
   out_6997830721327979188[27] = 0.0;
   out_6997830721327979188[28] = 0.0;
   out_6997830721327979188[29] = 0.0;
   out_6997830721327979188[30] = 0.0;
   out_6997830721327979188[31] = 0.0;
   out_6997830721327979188[32] = 0.0;
   out_6997830721327979188[33] = 0.0;
   out_6997830721327979188[34] = 0.0;
   out_6997830721327979188[35] = 0.0;
   out_6997830721327979188[36] = 0.0;
   out_6997830721327979188[37] = 0.0;
   out_6997830721327979188[38] = 1.0;
   out_6997830721327979188[39] = 0.0;
   out_6997830721327979188[40] = 0.0;
   out_6997830721327979188[41] = 0.0;
   out_6997830721327979188[42] = 0.0;
   out_6997830721327979188[43] = 0.0;
   out_6997830721327979188[44] = 0.0;
   out_6997830721327979188[45] = 0.0;
   out_6997830721327979188[46] = 0.0;
   out_6997830721327979188[47] = 0.0;
   out_6997830721327979188[48] = 0.0;
   out_6997830721327979188[49] = 0.0;
   out_6997830721327979188[50] = 0.0;
   out_6997830721327979188[51] = 0.0;
   out_6997830721327979188[52] = 0.0;
   out_6997830721327979188[53] = 0.0;
   out_6997830721327979188[54] = 0.0;
   out_6997830721327979188[55] = 0.0;
   out_6997830721327979188[56] = 0.0;
   out_6997830721327979188[57] = 1.0;
   out_6997830721327979188[58] = 0.0;
   out_6997830721327979188[59] = 0.0;
   out_6997830721327979188[60] = 0.0;
   out_6997830721327979188[61] = 0.0;
   out_6997830721327979188[62] = 0.0;
   out_6997830721327979188[63] = 0.0;
   out_6997830721327979188[64] = 0.0;
   out_6997830721327979188[65] = 0.0;
   out_6997830721327979188[66] = 0.0;
   out_6997830721327979188[67] = 0.0;
   out_6997830721327979188[68] = 0.0;
   out_6997830721327979188[69] = 0.0;
   out_6997830721327979188[70] = 0.0;
   out_6997830721327979188[71] = 0.0;
   out_6997830721327979188[72] = 0.0;
   out_6997830721327979188[73] = 0.0;
   out_6997830721327979188[74] = 0.0;
   out_6997830721327979188[75] = 0.0;
   out_6997830721327979188[76] = 1.0;
   out_6997830721327979188[77] = 0.0;
   out_6997830721327979188[78] = 0.0;
   out_6997830721327979188[79] = 0.0;
   out_6997830721327979188[80] = 0.0;
   out_6997830721327979188[81] = 0.0;
   out_6997830721327979188[82] = 0.0;
   out_6997830721327979188[83] = 0.0;
   out_6997830721327979188[84] = 0.0;
   out_6997830721327979188[85] = 0.0;
   out_6997830721327979188[86] = 0.0;
   out_6997830721327979188[87] = 0.0;
   out_6997830721327979188[88] = 0.0;
   out_6997830721327979188[89] = 0.0;
   out_6997830721327979188[90] = 0.0;
   out_6997830721327979188[91] = 0.0;
   out_6997830721327979188[92] = 0.0;
   out_6997830721327979188[93] = 0.0;
   out_6997830721327979188[94] = 0.0;
   out_6997830721327979188[95] = 1.0;
   out_6997830721327979188[96] = 0.0;
   out_6997830721327979188[97] = 0.0;
   out_6997830721327979188[98] = 0.0;
   out_6997830721327979188[99] = 0.0;
   out_6997830721327979188[100] = 0.0;
   out_6997830721327979188[101] = 0.0;
   out_6997830721327979188[102] = 0.0;
   out_6997830721327979188[103] = 0.0;
   out_6997830721327979188[104] = 0.0;
   out_6997830721327979188[105] = 0.0;
   out_6997830721327979188[106] = 0.0;
   out_6997830721327979188[107] = 0.0;
   out_6997830721327979188[108] = 0.0;
   out_6997830721327979188[109] = 0.0;
   out_6997830721327979188[110] = 0.0;
   out_6997830721327979188[111] = 0.0;
   out_6997830721327979188[112] = 0.0;
   out_6997830721327979188[113] = 0.0;
   out_6997830721327979188[114] = 1.0;
   out_6997830721327979188[115] = 0.0;
   out_6997830721327979188[116] = 0.0;
   out_6997830721327979188[117] = 0.0;
   out_6997830721327979188[118] = 0.0;
   out_6997830721327979188[119] = 0.0;
   out_6997830721327979188[120] = 0.0;
   out_6997830721327979188[121] = 0.0;
   out_6997830721327979188[122] = 0.0;
   out_6997830721327979188[123] = 0.0;
   out_6997830721327979188[124] = 0.0;
   out_6997830721327979188[125] = 0.0;
   out_6997830721327979188[126] = 0.0;
   out_6997830721327979188[127] = 0.0;
   out_6997830721327979188[128] = 0.0;
   out_6997830721327979188[129] = 0.0;
   out_6997830721327979188[130] = 0.0;
   out_6997830721327979188[131] = 0.0;
   out_6997830721327979188[132] = 0.0;
   out_6997830721327979188[133] = 1.0;
   out_6997830721327979188[134] = 0.0;
   out_6997830721327979188[135] = 0.0;
   out_6997830721327979188[136] = 0.0;
   out_6997830721327979188[137] = 0.0;
   out_6997830721327979188[138] = 0.0;
   out_6997830721327979188[139] = 0.0;
   out_6997830721327979188[140] = 0.0;
   out_6997830721327979188[141] = 0.0;
   out_6997830721327979188[142] = 0.0;
   out_6997830721327979188[143] = 0.0;
   out_6997830721327979188[144] = 0.0;
   out_6997830721327979188[145] = 0.0;
   out_6997830721327979188[146] = 0.0;
   out_6997830721327979188[147] = 0.0;
   out_6997830721327979188[148] = 0.0;
   out_6997830721327979188[149] = 0.0;
   out_6997830721327979188[150] = 0.0;
   out_6997830721327979188[151] = 0.0;
   out_6997830721327979188[152] = 1.0;
   out_6997830721327979188[153] = 0.0;
   out_6997830721327979188[154] = 0.0;
   out_6997830721327979188[155] = 0.0;
   out_6997830721327979188[156] = 0.0;
   out_6997830721327979188[157] = 0.0;
   out_6997830721327979188[158] = 0.0;
   out_6997830721327979188[159] = 0.0;
   out_6997830721327979188[160] = 0.0;
   out_6997830721327979188[161] = 0.0;
   out_6997830721327979188[162] = 0.0;
   out_6997830721327979188[163] = 0.0;
   out_6997830721327979188[164] = 0.0;
   out_6997830721327979188[165] = 0.0;
   out_6997830721327979188[166] = 0.0;
   out_6997830721327979188[167] = 0.0;
   out_6997830721327979188[168] = 0.0;
   out_6997830721327979188[169] = 0.0;
   out_6997830721327979188[170] = 0.0;
   out_6997830721327979188[171] = 1.0;
   out_6997830721327979188[172] = 0.0;
   out_6997830721327979188[173] = 0.0;
   out_6997830721327979188[174] = 0.0;
   out_6997830721327979188[175] = 0.0;
   out_6997830721327979188[176] = 0.0;
   out_6997830721327979188[177] = 0.0;
   out_6997830721327979188[178] = 0.0;
   out_6997830721327979188[179] = 0.0;
   out_6997830721327979188[180] = 0.0;
   out_6997830721327979188[181] = 0.0;
   out_6997830721327979188[182] = 0.0;
   out_6997830721327979188[183] = 0.0;
   out_6997830721327979188[184] = 0.0;
   out_6997830721327979188[185] = 0.0;
   out_6997830721327979188[186] = 0.0;
   out_6997830721327979188[187] = 0.0;
   out_6997830721327979188[188] = 0.0;
   out_6997830721327979188[189] = 0.0;
   out_6997830721327979188[190] = 1.0;
   out_6997830721327979188[191] = 0.0;
   out_6997830721327979188[192] = 0.0;
   out_6997830721327979188[193] = 0.0;
   out_6997830721327979188[194] = 0.0;
   out_6997830721327979188[195] = 0.0;
   out_6997830721327979188[196] = 0.0;
   out_6997830721327979188[197] = 0.0;
   out_6997830721327979188[198] = 0.0;
   out_6997830721327979188[199] = 0.0;
   out_6997830721327979188[200] = 0.0;
   out_6997830721327979188[201] = 0.0;
   out_6997830721327979188[202] = 0.0;
   out_6997830721327979188[203] = 0.0;
   out_6997830721327979188[204] = 0.0;
   out_6997830721327979188[205] = 0.0;
   out_6997830721327979188[206] = 0.0;
   out_6997830721327979188[207] = 0.0;
   out_6997830721327979188[208] = 0.0;
   out_6997830721327979188[209] = 1.0;
   out_6997830721327979188[210] = 0.0;
   out_6997830721327979188[211] = 0.0;
   out_6997830721327979188[212] = 0.0;
   out_6997830721327979188[213] = 0.0;
   out_6997830721327979188[214] = 0.0;
   out_6997830721327979188[215] = 0.0;
   out_6997830721327979188[216] = 0.0;
   out_6997830721327979188[217] = 0.0;
   out_6997830721327979188[218] = 0.0;
   out_6997830721327979188[219] = 0.0;
   out_6997830721327979188[220] = 0.0;
   out_6997830721327979188[221] = 0.0;
   out_6997830721327979188[222] = 0.0;
   out_6997830721327979188[223] = 0.0;
   out_6997830721327979188[224] = 0.0;
   out_6997830721327979188[225] = 0.0;
   out_6997830721327979188[226] = 0.0;
   out_6997830721327979188[227] = 0.0;
   out_6997830721327979188[228] = 1.0;
   out_6997830721327979188[229] = 0.0;
   out_6997830721327979188[230] = 0.0;
   out_6997830721327979188[231] = 0.0;
   out_6997830721327979188[232] = 0.0;
   out_6997830721327979188[233] = 0.0;
   out_6997830721327979188[234] = 0.0;
   out_6997830721327979188[235] = 0.0;
   out_6997830721327979188[236] = 0.0;
   out_6997830721327979188[237] = 0.0;
   out_6997830721327979188[238] = 0.0;
   out_6997830721327979188[239] = 0.0;
   out_6997830721327979188[240] = 0.0;
   out_6997830721327979188[241] = 0.0;
   out_6997830721327979188[242] = 0.0;
   out_6997830721327979188[243] = 0.0;
   out_6997830721327979188[244] = 0.0;
   out_6997830721327979188[245] = 0.0;
   out_6997830721327979188[246] = 0.0;
   out_6997830721327979188[247] = 1.0;
   out_6997830721327979188[248] = 0.0;
   out_6997830721327979188[249] = 0.0;
   out_6997830721327979188[250] = 0.0;
   out_6997830721327979188[251] = 0.0;
   out_6997830721327979188[252] = 0.0;
   out_6997830721327979188[253] = 0.0;
   out_6997830721327979188[254] = 0.0;
   out_6997830721327979188[255] = 0.0;
   out_6997830721327979188[256] = 0.0;
   out_6997830721327979188[257] = 0.0;
   out_6997830721327979188[258] = 0.0;
   out_6997830721327979188[259] = 0.0;
   out_6997830721327979188[260] = 0.0;
   out_6997830721327979188[261] = 0.0;
   out_6997830721327979188[262] = 0.0;
   out_6997830721327979188[263] = 0.0;
   out_6997830721327979188[264] = 0.0;
   out_6997830721327979188[265] = 0.0;
   out_6997830721327979188[266] = 1.0;
   out_6997830721327979188[267] = 0.0;
   out_6997830721327979188[268] = 0.0;
   out_6997830721327979188[269] = 0.0;
   out_6997830721327979188[270] = 0.0;
   out_6997830721327979188[271] = 0.0;
   out_6997830721327979188[272] = 0.0;
   out_6997830721327979188[273] = 0.0;
   out_6997830721327979188[274] = 0.0;
   out_6997830721327979188[275] = 0.0;
   out_6997830721327979188[276] = 0.0;
   out_6997830721327979188[277] = 0.0;
   out_6997830721327979188[278] = 0.0;
   out_6997830721327979188[279] = 0.0;
   out_6997830721327979188[280] = 0.0;
   out_6997830721327979188[281] = 0.0;
   out_6997830721327979188[282] = 0.0;
   out_6997830721327979188[283] = 0.0;
   out_6997830721327979188[284] = 0.0;
   out_6997830721327979188[285] = 1.0;
   out_6997830721327979188[286] = 0.0;
   out_6997830721327979188[287] = 0.0;
   out_6997830721327979188[288] = 0.0;
   out_6997830721327979188[289] = 0.0;
   out_6997830721327979188[290] = 0.0;
   out_6997830721327979188[291] = 0.0;
   out_6997830721327979188[292] = 0.0;
   out_6997830721327979188[293] = 0.0;
   out_6997830721327979188[294] = 0.0;
   out_6997830721327979188[295] = 0.0;
   out_6997830721327979188[296] = 0.0;
   out_6997830721327979188[297] = 0.0;
   out_6997830721327979188[298] = 0.0;
   out_6997830721327979188[299] = 0.0;
   out_6997830721327979188[300] = 0.0;
   out_6997830721327979188[301] = 0.0;
   out_6997830721327979188[302] = 0.0;
   out_6997830721327979188[303] = 0.0;
   out_6997830721327979188[304] = 1.0;
   out_6997830721327979188[305] = 0.0;
   out_6997830721327979188[306] = 0.0;
   out_6997830721327979188[307] = 0.0;
   out_6997830721327979188[308] = 0.0;
   out_6997830721327979188[309] = 0.0;
   out_6997830721327979188[310] = 0.0;
   out_6997830721327979188[311] = 0.0;
   out_6997830721327979188[312] = 0.0;
   out_6997830721327979188[313] = 0.0;
   out_6997830721327979188[314] = 0.0;
   out_6997830721327979188[315] = 0.0;
   out_6997830721327979188[316] = 0.0;
   out_6997830721327979188[317] = 0.0;
   out_6997830721327979188[318] = 0.0;
   out_6997830721327979188[319] = 0.0;
   out_6997830721327979188[320] = 0.0;
   out_6997830721327979188[321] = 0.0;
   out_6997830721327979188[322] = 0.0;
   out_6997830721327979188[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_2524658316881090159) {
   out_2524658316881090159[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_2524658316881090159[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_2524658316881090159[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_2524658316881090159[3] = dt*state[12] + state[3];
   out_2524658316881090159[4] = dt*state[13] + state[4];
   out_2524658316881090159[5] = dt*state[14] + state[5];
   out_2524658316881090159[6] = state[6];
   out_2524658316881090159[7] = state[7];
   out_2524658316881090159[8] = state[8];
   out_2524658316881090159[9] = state[9];
   out_2524658316881090159[10] = state[10];
   out_2524658316881090159[11] = state[11];
   out_2524658316881090159[12] = state[12];
   out_2524658316881090159[13] = state[13];
   out_2524658316881090159[14] = state[14];
   out_2524658316881090159[15] = state[15];
   out_2524658316881090159[16] = state[16];
   out_2524658316881090159[17] = state[17];
}
void F_fun(double *state, double dt, double *out_1493803281019954497) {
   out_1493803281019954497[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_1493803281019954497[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_1493803281019954497[2] = 0;
   out_1493803281019954497[3] = 0;
   out_1493803281019954497[4] = 0;
   out_1493803281019954497[5] = 0;
   out_1493803281019954497[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_1493803281019954497[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_1493803281019954497[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_1493803281019954497[9] = 0;
   out_1493803281019954497[10] = 0;
   out_1493803281019954497[11] = 0;
   out_1493803281019954497[12] = 0;
   out_1493803281019954497[13] = 0;
   out_1493803281019954497[14] = 0;
   out_1493803281019954497[15] = 0;
   out_1493803281019954497[16] = 0;
   out_1493803281019954497[17] = 0;
   out_1493803281019954497[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_1493803281019954497[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_1493803281019954497[20] = 0;
   out_1493803281019954497[21] = 0;
   out_1493803281019954497[22] = 0;
   out_1493803281019954497[23] = 0;
   out_1493803281019954497[24] = 0;
   out_1493803281019954497[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_1493803281019954497[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_1493803281019954497[27] = 0;
   out_1493803281019954497[28] = 0;
   out_1493803281019954497[29] = 0;
   out_1493803281019954497[30] = 0;
   out_1493803281019954497[31] = 0;
   out_1493803281019954497[32] = 0;
   out_1493803281019954497[33] = 0;
   out_1493803281019954497[34] = 0;
   out_1493803281019954497[35] = 0;
   out_1493803281019954497[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_1493803281019954497[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_1493803281019954497[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_1493803281019954497[39] = 0;
   out_1493803281019954497[40] = 0;
   out_1493803281019954497[41] = 0;
   out_1493803281019954497[42] = 0;
   out_1493803281019954497[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_1493803281019954497[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_1493803281019954497[45] = 0;
   out_1493803281019954497[46] = 0;
   out_1493803281019954497[47] = 0;
   out_1493803281019954497[48] = 0;
   out_1493803281019954497[49] = 0;
   out_1493803281019954497[50] = 0;
   out_1493803281019954497[51] = 0;
   out_1493803281019954497[52] = 0;
   out_1493803281019954497[53] = 0;
   out_1493803281019954497[54] = 0;
   out_1493803281019954497[55] = 0;
   out_1493803281019954497[56] = 0;
   out_1493803281019954497[57] = 1;
   out_1493803281019954497[58] = 0;
   out_1493803281019954497[59] = 0;
   out_1493803281019954497[60] = 0;
   out_1493803281019954497[61] = 0;
   out_1493803281019954497[62] = 0;
   out_1493803281019954497[63] = 0;
   out_1493803281019954497[64] = 0;
   out_1493803281019954497[65] = 0;
   out_1493803281019954497[66] = dt;
   out_1493803281019954497[67] = 0;
   out_1493803281019954497[68] = 0;
   out_1493803281019954497[69] = 0;
   out_1493803281019954497[70] = 0;
   out_1493803281019954497[71] = 0;
   out_1493803281019954497[72] = 0;
   out_1493803281019954497[73] = 0;
   out_1493803281019954497[74] = 0;
   out_1493803281019954497[75] = 0;
   out_1493803281019954497[76] = 1;
   out_1493803281019954497[77] = 0;
   out_1493803281019954497[78] = 0;
   out_1493803281019954497[79] = 0;
   out_1493803281019954497[80] = 0;
   out_1493803281019954497[81] = 0;
   out_1493803281019954497[82] = 0;
   out_1493803281019954497[83] = 0;
   out_1493803281019954497[84] = 0;
   out_1493803281019954497[85] = dt;
   out_1493803281019954497[86] = 0;
   out_1493803281019954497[87] = 0;
   out_1493803281019954497[88] = 0;
   out_1493803281019954497[89] = 0;
   out_1493803281019954497[90] = 0;
   out_1493803281019954497[91] = 0;
   out_1493803281019954497[92] = 0;
   out_1493803281019954497[93] = 0;
   out_1493803281019954497[94] = 0;
   out_1493803281019954497[95] = 1;
   out_1493803281019954497[96] = 0;
   out_1493803281019954497[97] = 0;
   out_1493803281019954497[98] = 0;
   out_1493803281019954497[99] = 0;
   out_1493803281019954497[100] = 0;
   out_1493803281019954497[101] = 0;
   out_1493803281019954497[102] = 0;
   out_1493803281019954497[103] = 0;
   out_1493803281019954497[104] = dt;
   out_1493803281019954497[105] = 0;
   out_1493803281019954497[106] = 0;
   out_1493803281019954497[107] = 0;
   out_1493803281019954497[108] = 0;
   out_1493803281019954497[109] = 0;
   out_1493803281019954497[110] = 0;
   out_1493803281019954497[111] = 0;
   out_1493803281019954497[112] = 0;
   out_1493803281019954497[113] = 0;
   out_1493803281019954497[114] = 1;
   out_1493803281019954497[115] = 0;
   out_1493803281019954497[116] = 0;
   out_1493803281019954497[117] = 0;
   out_1493803281019954497[118] = 0;
   out_1493803281019954497[119] = 0;
   out_1493803281019954497[120] = 0;
   out_1493803281019954497[121] = 0;
   out_1493803281019954497[122] = 0;
   out_1493803281019954497[123] = 0;
   out_1493803281019954497[124] = 0;
   out_1493803281019954497[125] = 0;
   out_1493803281019954497[126] = 0;
   out_1493803281019954497[127] = 0;
   out_1493803281019954497[128] = 0;
   out_1493803281019954497[129] = 0;
   out_1493803281019954497[130] = 0;
   out_1493803281019954497[131] = 0;
   out_1493803281019954497[132] = 0;
   out_1493803281019954497[133] = 1;
   out_1493803281019954497[134] = 0;
   out_1493803281019954497[135] = 0;
   out_1493803281019954497[136] = 0;
   out_1493803281019954497[137] = 0;
   out_1493803281019954497[138] = 0;
   out_1493803281019954497[139] = 0;
   out_1493803281019954497[140] = 0;
   out_1493803281019954497[141] = 0;
   out_1493803281019954497[142] = 0;
   out_1493803281019954497[143] = 0;
   out_1493803281019954497[144] = 0;
   out_1493803281019954497[145] = 0;
   out_1493803281019954497[146] = 0;
   out_1493803281019954497[147] = 0;
   out_1493803281019954497[148] = 0;
   out_1493803281019954497[149] = 0;
   out_1493803281019954497[150] = 0;
   out_1493803281019954497[151] = 0;
   out_1493803281019954497[152] = 1;
   out_1493803281019954497[153] = 0;
   out_1493803281019954497[154] = 0;
   out_1493803281019954497[155] = 0;
   out_1493803281019954497[156] = 0;
   out_1493803281019954497[157] = 0;
   out_1493803281019954497[158] = 0;
   out_1493803281019954497[159] = 0;
   out_1493803281019954497[160] = 0;
   out_1493803281019954497[161] = 0;
   out_1493803281019954497[162] = 0;
   out_1493803281019954497[163] = 0;
   out_1493803281019954497[164] = 0;
   out_1493803281019954497[165] = 0;
   out_1493803281019954497[166] = 0;
   out_1493803281019954497[167] = 0;
   out_1493803281019954497[168] = 0;
   out_1493803281019954497[169] = 0;
   out_1493803281019954497[170] = 0;
   out_1493803281019954497[171] = 1;
   out_1493803281019954497[172] = 0;
   out_1493803281019954497[173] = 0;
   out_1493803281019954497[174] = 0;
   out_1493803281019954497[175] = 0;
   out_1493803281019954497[176] = 0;
   out_1493803281019954497[177] = 0;
   out_1493803281019954497[178] = 0;
   out_1493803281019954497[179] = 0;
   out_1493803281019954497[180] = 0;
   out_1493803281019954497[181] = 0;
   out_1493803281019954497[182] = 0;
   out_1493803281019954497[183] = 0;
   out_1493803281019954497[184] = 0;
   out_1493803281019954497[185] = 0;
   out_1493803281019954497[186] = 0;
   out_1493803281019954497[187] = 0;
   out_1493803281019954497[188] = 0;
   out_1493803281019954497[189] = 0;
   out_1493803281019954497[190] = 1;
   out_1493803281019954497[191] = 0;
   out_1493803281019954497[192] = 0;
   out_1493803281019954497[193] = 0;
   out_1493803281019954497[194] = 0;
   out_1493803281019954497[195] = 0;
   out_1493803281019954497[196] = 0;
   out_1493803281019954497[197] = 0;
   out_1493803281019954497[198] = 0;
   out_1493803281019954497[199] = 0;
   out_1493803281019954497[200] = 0;
   out_1493803281019954497[201] = 0;
   out_1493803281019954497[202] = 0;
   out_1493803281019954497[203] = 0;
   out_1493803281019954497[204] = 0;
   out_1493803281019954497[205] = 0;
   out_1493803281019954497[206] = 0;
   out_1493803281019954497[207] = 0;
   out_1493803281019954497[208] = 0;
   out_1493803281019954497[209] = 1;
   out_1493803281019954497[210] = 0;
   out_1493803281019954497[211] = 0;
   out_1493803281019954497[212] = 0;
   out_1493803281019954497[213] = 0;
   out_1493803281019954497[214] = 0;
   out_1493803281019954497[215] = 0;
   out_1493803281019954497[216] = 0;
   out_1493803281019954497[217] = 0;
   out_1493803281019954497[218] = 0;
   out_1493803281019954497[219] = 0;
   out_1493803281019954497[220] = 0;
   out_1493803281019954497[221] = 0;
   out_1493803281019954497[222] = 0;
   out_1493803281019954497[223] = 0;
   out_1493803281019954497[224] = 0;
   out_1493803281019954497[225] = 0;
   out_1493803281019954497[226] = 0;
   out_1493803281019954497[227] = 0;
   out_1493803281019954497[228] = 1;
   out_1493803281019954497[229] = 0;
   out_1493803281019954497[230] = 0;
   out_1493803281019954497[231] = 0;
   out_1493803281019954497[232] = 0;
   out_1493803281019954497[233] = 0;
   out_1493803281019954497[234] = 0;
   out_1493803281019954497[235] = 0;
   out_1493803281019954497[236] = 0;
   out_1493803281019954497[237] = 0;
   out_1493803281019954497[238] = 0;
   out_1493803281019954497[239] = 0;
   out_1493803281019954497[240] = 0;
   out_1493803281019954497[241] = 0;
   out_1493803281019954497[242] = 0;
   out_1493803281019954497[243] = 0;
   out_1493803281019954497[244] = 0;
   out_1493803281019954497[245] = 0;
   out_1493803281019954497[246] = 0;
   out_1493803281019954497[247] = 1;
   out_1493803281019954497[248] = 0;
   out_1493803281019954497[249] = 0;
   out_1493803281019954497[250] = 0;
   out_1493803281019954497[251] = 0;
   out_1493803281019954497[252] = 0;
   out_1493803281019954497[253] = 0;
   out_1493803281019954497[254] = 0;
   out_1493803281019954497[255] = 0;
   out_1493803281019954497[256] = 0;
   out_1493803281019954497[257] = 0;
   out_1493803281019954497[258] = 0;
   out_1493803281019954497[259] = 0;
   out_1493803281019954497[260] = 0;
   out_1493803281019954497[261] = 0;
   out_1493803281019954497[262] = 0;
   out_1493803281019954497[263] = 0;
   out_1493803281019954497[264] = 0;
   out_1493803281019954497[265] = 0;
   out_1493803281019954497[266] = 1;
   out_1493803281019954497[267] = 0;
   out_1493803281019954497[268] = 0;
   out_1493803281019954497[269] = 0;
   out_1493803281019954497[270] = 0;
   out_1493803281019954497[271] = 0;
   out_1493803281019954497[272] = 0;
   out_1493803281019954497[273] = 0;
   out_1493803281019954497[274] = 0;
   out_1493803281019954497[275] = 0;
   out_1493803281019954497[276] = 0;
   out_1493803281019954497[277] = 0;
   out_1493803281019954497[278] = 0;
   out_1493803281019954497[279] = 0;
   out_1493803281019954497[280] = 0;
   out_1493803281019954497[281] = 0;
   out_1493803281019954497[282] = 0;
   out_1493803281019954497[283] = 0;
   out_1493803281019954497[284] = 0;
   out_1493803281019954497[285] = 1;
   out_1493803281019954497[286] = 0;
   out_1493803281019954497[287] = 0;
   out_1493803281019954497[288] = 0;
   out_1493803281019954497[289] = 0;
   out_1493803281019954497[290] = 0;
   out_1493803281019954497[291] = 0;
   out_1493803281019954497[292] = 0;
   out_1493803281019954497[293] = 0;
   out_1493803281019954497[294] = 0;
   out_1493803281019954497[295] = 0;
   out_1493803281019954497[296] = 0;
   out_1493803281019954497[297] = 0;
   out_1493803281019954497[298] = 0;
   out_1493803281019954497[299] = 0;
   out_1493803281019954497[300] = 0;
   out_1493803281019954497[301] = 0;
   out_1493803281019954497[302] = 0;
   out_1493803281019954497[303] = 0;
   out_1493803281019954497[304] = 1;
   out_1493803281019954497[305] = 0;
   out_1493803281019954497[306] = 0;
   out_1493803281019954497[307] = 0;
   out_1493803281019954497[308] = 0;
   out_1493803281019954497[309] = 0;
   out_1493803281019954497[310] = 0;
   out_1493803281019954497[311] = 0;
   out_1493803281019954497[312] = 0;
   out_1493803281019954497[313] = 0;
   out_1493803281019954497[314] = 0;
   out_1493803281019954497[315] = 0;
   out_1493803281019954497[316] = 0;
   out_1493803281019954497[317] = 0;
   out_1493803281019954497[318] = 0;
   out_1493803281019954497[319] = 0;
   out_1493803281019954497[320] = 0;
   out_1493803281019954497[321] = 0;
   out_1493803281019954497[322] = 0;
   out_1493803281019954497[323] = 1;
}
void h_4(double *state, double *unused, double *out_9199116239139928597) {
   out_9199116239139928597[0] = state[6] + state[9];
   out_9199116239139928597[1] = state[7] + state[10];
   out_9199116239139928597[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_5055826457360484509) {
   out_5055826457360484509[0] = 0;
   out_5055826457360484509[1] = 0;
   out_5055826457360484509[2] = 0;
   out_5055826457360484509[3] = 0;
   out_5055826457360484509[4] = 0;
   out_5055826457360484509[5] = 0;
   out_5055826457360484509[6] = 1;
   out_5055826457360484509[7] = 0;
   out_5055826457360484509[8] = 0;
   out_5055826457360484509[9] = 1;
   out_5055826457360484509[10] = 0;
   out_5055826457360484509[11] = 0;
   out_5055826457360484509[12] = 0;
   out_5055826457360484509[13] = 0;
   out_5055826457360484509[14] = 0;
   out_5055826457360484509[15] = 0;
   out_5055826457360484509[16] = 0;
   out_5055826457360484509[17] = 0;
   out_5055826457360484509[18] = 0;
   out_5055826457360484509[19] = 0;
   out_5055826457360484509[20] = 0;
   out_5055826457360484509[21] = 0;
   out_5055826457360484509[22] = 0;
   out_5055826457360484509[23] = 0;
   out_5055826457360484509[24] = 0;
   out_5055826457360484509[25] = 1;
   out_5055826457360484509[26] = 0;
   out_5055826457360484509[27] = 0;
   out_5055826457360484509[28] = 1;
   out_5055826457360484509[29] = 0;
   out_5055826457360484509[30] = 0;
   out_5055826457360484509[31] = 0;
   out_5055826457360484509[32] = 0;
   out_5055826457360484509[33] = 0;
   out_5055826457360484509[34] = 0;
   out_5055826457360484509[35] = 0;
   out_5055826457360484509[36] = 0;
   out_5055826457360484509[37] = 0;
   out_5055826457360484509[38] = 0;
   out_5055826457360484509[39] = 0;
   out_5055826457360484509[40] = 0;
   out_5055826457360484509[41] = 0;
   out_5055826457360484509[42] = 0;
   out_5055826457360484509[43] = 0;
   out_5055826457360484509[44] = 1;
   out_5055826457360484509[45] = 0;
   out_5055826457360484509[46] = 0;
   out_5055826457360484509[47] = 1;
   out_5055826457360484509[48] = 0;
   out_5055826457360484509[49] = 0;
   out_5055826457360484509[50] = 0;
   out_5055826457360484509[51] = 0;
   out_5055826457360484509[52] = 0;
   out_5055826457360484509[53] = 0;
}
void h_10(double *state, double *unused, double *out_6229114816113941890) {
   out_6229114816113941890[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_6229114816113941890[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_6229114816113941890[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_4767454895579609867) {
   out_4767454895579609867[0] = 0;
   out_4767454895579609867[1] = 9.8100000000000005*cos(state[1]);
   out_4767454895579609867[2] = 0;
   out_4767454895579609867[3] = 0;
   out_4767454895579609867[4] = -state[8];
   out_4767454895579609867[5] = state[7];
   out_4767454895579609867[6] = 0;
   out_4767454895579609867[7] = state[5];
   out_4767454895579609867[8] = -state[4];
   out_4767454895579609867[9] = 0;
   out_4767454895579609867[10] = 0;
   out_4767454895579609867[11] = 0;
   out_4767454895579609867[12] = 1;
   out_4767454895579609867[13] = 0;
   out_4767454895579609867[14] = 0;
   out_4767454895579609867[15] = 1;
   out_4767454895579609867[16] = 0;
   out_4767454895579609867[17] = 0;
   out_4767454895579609867[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_4767454895579609867[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_4767454895579609867[20] = 0;
   out_4767454895579609867[21] = state[8];
   out_4767454895579609867[22] = 0;
   out_4767454895579609867[23] = -state[6];
   out_4767454895579609867[24] = -state[5];
   out_4767454895579609867[25] = 0;
   out_4767454895579609867[26] = state[3];
   out_4767454895579609867[27] = 0;
   out_4767454895579609867[28] = 0;
   out_4767454895579609867[29] = 0;
   out_4767454895579609867[30] = 0;
   out_4767454895579609867[31] = 1;
   out_4767454895579609867[32] = 0;
   out_4767454895579609867[33] = 0;
   out_4767454895579609867[34] = 1;
   out_4767454895579609867[35] = 0;
   out_4767454895579609867[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_4767454895579609867[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_4767454895579609867[38] = 0;
   out_4767454895579609867[39] = -state[7];
   out_4767454895579609867[40] = state[6];
   out_4767454895579609867[41] = 0;
   out_4767454895579609867[42] = state[4];
   out_4767454895579609867[43] = -state[3];
   out_4767454895579609867[44] = 0;
   out_4767454895579609867[45] = 0;
   out_4767454895579609867[46] = 0;
   out_4767454895579609867[47] = 0;
   out_4767454895579609867[48] = 0;
   out_4767454895579609867[49] = 0;
   out_4767454895579609867[50] = 1;
   out_4767454895579609867[51] = 0;
   out_4767454895579609867[52] = 0;
   out_4767454895579609867[53] = 1;
}
void h_13(double *state, double *unused, double *out_8087901312810249753) {
   out_8087901312810249753[0] = state[3];
   out_8087901312810249753[1] = state[4];
   out_8087901312810249753[2] = state[5];
}
void H_13(double *state, double *unused, double *out_5780286408032366178) {
   out_5780286408032366178[0] = 0;
   out_5780286408032366178[1] = 0;
   out_5780286408032366178[2] = 0;
   out_5780286408032366178[3] = 1;
   out_5780286408032366178[4] = 0;
   out_5780286408032366178[5] = 0;
   out_5780286408032366178[6] = 0;
   out_5780286408032366178[7] = 0;
   out_5780286408032366178[8] = 0;
   out_5780286408032366178[9] = 0;
   out_5780286408032366178[10] = 0;
   out_5780286408032366178[11] = 0;
   out_5780286408032366178[12] = 0;
   out_5780286408032366178[13] = 0;
   out_5780286408032366178[14] = 0;
   out_5780286408032366178[15] = 0;
   out_5780286408032366178[16] = 0;
   out_5780286408032366178[17] = 0;
   out_5780286408032366178[18] = 0;
   out_5780286408032366178[19] = 0;
   out_5780286408032366178[20] = 0;
   out_5780286408032366178[21] = 0;
   out_5780286408032366178[22] = 1;
   out_5780286408032366178[23] = 0;
   out_5780286408032366178[24] = 0;
   out_5780286408032366178[25] = 0;
   out_5780286408032366178[26] = 0;
   out_5780286408032366178[27] = 0;
   out_5780286408032366178[28] = 0;
   out_5780286408032366178[29] = 0;
   out_5780286408032366178[30] = 0;
   out_5780286408032366178[31] = 0;
   out_5780286408032366178[32] = 0;
   out_5780286408032366178[33] = 0;
   out_5780286408032366178[34] = 0;
   out_5780286408032366178[35] = 0;
   out_5780286408032366178[36] = 0;
   out_5780286408032366178[37] = 0;
   out_5780286408032366178[38] = 0;
   out_5780286408032366178[39] = 0;
   out_5780286408032366178[40] = 0;
   out_5780286408032366178[41] = 1;
   out_5780286408032366178[42] = 0;
   out_5780286408032366178[43] = 0;
   out_5780286408032366178[44] = 0;
   out_5780286408032366178[45] = 0;
   out_5780286408032366178[46] = 0;
   out_5780286408032366178[47] = 0;
   out_5780286408032366178[48] = 0;
   out_5780286408032366178[49] = 0;
   out_5780286408032366178[50] = 0;
   out_5780286408032366178[51] = 0;
   out_5780286408032366178[52] = 0;
   out_5780286408032366178[53] = 0;
}
void h_14(double *state, double *unused, double *out_8155013269706044892) {
   out_8155013269706044892[0] = state[6];
   out_8155013269706044892[1] = state[7];
   out_8155013269706044892[2] = state[8];
}
void H_14(double *state, double *unused, double *out_9019067313699969038) {
   out_9019067313699969038[0] = 0;
   out_9019067313699969038[1] = 0;
   out_9019067313699969038[2] = 0;
   out_9019067313699969038[3] = 0;
   out_9019067313699969038[4] = 0;
   out_9019067313699969038[5] = 0;
   out_9019067313699969038[6] = 1;
   out_9019067313699969038[7] = 0;
   out_9019067313699969038[8] = 0;
   out_9019067313699969038[9] = 0;
   out_9019067313699969038[10] = 0;
   out_9019067313699969038[11] = 0;
   out_9019067313699969038[12] = 0;
   out_9019067313699969038[13] = 0;
   out_9019067313699969038[14] = 0;
   out_9019067313699969038[15] = 0;
   out_9019067313699969038[16] = 0;
   out_9019067313699969038[17] = 0;
   out_9019067313699969038[18] = 0;
   out_9019067313699969038[19] = 0;
   out_9019067313699969038[20] = 0;
   out_9019067313699969038[21] = 0;
   out_9019067313699969038[22] = 0;
   out_9019067313699969038[23] = 0;
   out_9019067313699969038[24] = 0;
   out_9019067313699969038[25] = 1;
   out_9019067313699969038[26] = 0;
   out_9019067313699969038[27] = 0;
   out_9019067313699969038[28] = 0;
   out_9019067313699969038[29] = 0;
   out_9019067313699969038[30] = 0;
   out_9019067313699969038[31] = 0;
   out_9019067313699969038[32] = 0;
   out_9019067313699969038[33] = 0;
   out_9019067313699969038[34] = 0;
   out_9019067313699969038[35] = 0;
   out_9019067313699969038[36] = 0;
   out_9019067313699969038[37] = 0;
   out_9019067313699969038[38] = 0;
   out_9019067313699969038[39] = 0;
   out_9019067313699969038[40] = 0;
   out_9019067313699969038[41] = 0;
   out_9019067313699969038[42] = 0;
   out_9019067313699969038[43] = 0;
   out_9019067313699969038[44] = 1;
   out_9019067313699969038[45] = 0;
   out_9019067313699969038[46] = 0;
   out_9019067313699969038[47] = 0;
   out_9019067313699969038[48] = 0;
   out_9019067313699969038[49] = 0;
   out_9019067313699969038[50] = 0;
   out_9019067313699969038[51] = 0;
   out_9019067313699969038[52] = 0;
   out_9019067313699969038[53] = 0;
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
void pose_err_fun(double *nom_x, double *delta_x, double *out_7437794640769795433) {
  err_fun(nom_x, delta_x, out_7437794640769795433);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_2037082783356591262) {
  inv_err_fun(nom_x, true_x, out_2037082783356591262);
}
void pose_H_mod_fun(double *state, double *out_6997830721327979188) {
  H_mod_fun(state, out_6997830721327979188);
}
void pose_f_fun(double *state, double dt, double *out_2524658316881090159) {
  f_fun(state,  dt, out_2524658316881090159);
}
void pose_F_fun(double *state, double dt, double *out_1493803281019954497) {
  F_fun(state,  dt, out_1493803281019954497);
}
void pose_h_4(double *state, double *unused, double *out_9199116239139928597) {
  h_4(state, unused, out_9199116239139928597);
}
void pose_H_4(double *state, double *unused, double *out_5055826457360484509) {
  H_4(state, unused, out_5055826457360484509);
}
void pose_h_10(double *state, double *unused, double *out_6229114816113941890) {
  h_10(state, unused, out_6229114816113941890);
}
void pose_H_10(double *state, double *unused, double *out_4767454895579609867) {
  H_10(state, unused, out_4767454895579609867);
}
void pose_h_13(double *state, double *unused, double *out_8087901312810249753) {
  h_13(state, unused, out_8087901312810249753);
}
void pose_H_13(double *state, double *unused, double *out_5780286408032366178) {
  H_13(state, unused, out_5780286408032366178);
}
void pose_h_14(double *state, double *unused, double *out_8155013269706044892) {
  h_14(state, unused, out_8155013269706044892);
}
void pose_H_14(double *state, double *unused, double *out_9019067313699969038) {
  H_14(state, unused, out_9019067313699969038);
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
