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
void err_fun(double *nom_x, double *delta_x, double *out_7505672412271645129) {
   out_7505672412271645129[0] = delta_x[0] + nom_x[0];
   out_7505672412271645129[1] = delta_x[1] + nom_x[1];
   out_7505672412271645129[2] = delta_x[2] + nom_x[2];
   out_7505672412271645129[3] = delta_x[3] + nom_x[3];
   out_7505672412271645129[4] = delta_x[4] + nom_x[4];
   out_7505672412271645129[5] = delta_x[5] + nom_x[5];
   out_7505672412271645129[6] = delta_x[6] + nom_x[6];
   out_7505672412271645129[7] = delta_x[7] + nom_x[7];
   out_7505672412271645129[8] = delta_x[8] + nom_x[8];
   out_7505672412271645129[9] = delta_x[9] + nom_x[9];
   out_7505672412271645129[10] = delta_x[10] + nom_x[10];
   out_7505672412271645129[11] = delta_x[11] + nom_x[11];
   out_7505672412271645129[12] = delta_x[12] + nom_x[12];
   out_7505672412271645129[13] = delta_x[13] + nom_x[13];
   out_7505672412271645129[14] = delta_x[14] + nom_x[14];
   out_7505672412271645129[15] = delta_x[15] + nom_x[15];
   out_7505672412271645129[16] = delta_x[16] + nom_x[16];
   out_7505672412271645129[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_850525553930579209) {
   out_850525553930579209[0] = -nom_x[0] + true_x[0];
   out_850525553930579209[1] = -nom_x[1] + true_x[1];
   out_850525553930579209[2] = -nom_x[2] + true_x[2];
   out_850525553930579209[3] = -nom_x[3] + true_x[3];
   out_850525553930579209[4] = -nom_x[4] + true_x[4];
   out_850525553930579209[5] = -nom_x[5] + true_x[5];
   out_850525553930579209[6] = -nom_x[6] + true_x[6];
   out_850525553930579209[7] = -nom_x[7] + true_x[7];
   out_850525553930579209[8] = -nom_x[8] + true_x[8];
   out_850525553930579209[9] = -nom_x[9] + true_x[9];
   out_850525553930579209[10] = -nom_x[10] + true_x[10];
   out_850525553930579209[11] = -nom_x[11] + true_x[11];
   out_850525553930579209[12] = -nom_x[12] + true_x[12];
   out_850525553930579209[13] = -nom_x[13] + true_x[13];
   out_850525553930579209[14] = -nom_x[14] + true_x[14];
   out_850525553930579209[15] = -nom_x[15] + true_x[15];
   out_850525553930579209[16] = -nom_x[16] + true_x[16];
   out_850525553930579209[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_5142011875417202005) {
   out_5142011875417202005[0] = 1.0;
   out_5142011875417202005[1] = 0.0;
   out_5142011875417202005[2] = 0.0;
   out_5142011875417202005[3] = 0.0;
   out_5142011875417202005[4] = 0.0;
   out_5142011875417202005[5] = 0.0;
   out_5142011875417202005[6] = 0.0;
   out_5142011875417202005[7] = 0.0;
   out_5142011875417202005[8] = 0.0;
   out_5142011875417202005[9] = 0.0;
   out_5142011875417202005[10] = 0.0;
   out_5142011875417202005[11] = 0.0;
   out_5142011875417202005[12] = 0.0;
   out_5142011875417202005[13] = 0.0;
   out_5142011875417202005[14] = 0.0;
   out_5142011875417202005[15] = 0.0;
   out_5142011875417202005[16] = 0.0;
   out_5142011875417202005[17] = 0.0;
   out_5142011875417202005[18] = 0.0;
   out_5142011875417202005[19] = 1.0;
   out_5142011875417202005[20] = 0.0;
   out_5142011875417202005[21] = 0.0;
   out_5142011875417202005[22] = 0.0;
   out_5142011875417202005[23] = 0.0;
   out_5142011875417202005[24] = 0.0;
   out_5142011875417202005[25] = 0.0;
   out_5142011875417202005[26] = 0.0;
   out_5142011875417202005[27] = 0.0;
   out_5142011875417202005[28] = 0.0;
   out_5142011875417202005[29] = 0.0;
   out_5142011875417202005[30] = 0.0;
   out_5142011875417202005[31] = 0.0;
   out_5142011875417202005[32] = 0.0;
   out_5142011875417202005[33] = 0.0;
   out_5142011875417202005[34] = 0.0;
   out_5142011875417202005[35] = 0.0;
   out_5142011875417202005[36] = 0.0;
   out_5142011875417202005[37] = 0.0;
   out_5142011875417202005[38] = 1.0;
   out_5142011875417202005[39] = 0.0;
   out_5142011875417202005[40] = 0.0;
   out_5142011875417202005[41] = 0.0;
   out_5142011875417202005[42] = 0.0;
   out_5142011875417202005[43] = 0.0;
   out_5142011875417202005[44] = 0.0;
   out_5142011875417202005[45] = 0.0;
   out_5142011875417202005[46] = 0.0;
   out_5142011875417202005[47] = 0.0;
   out_5142011875417202005[48] = 0.0;
   out_5142011875417202005[49] = 0.0;
   out_5142011875417202005[50] = 0.0;
   out_5142011875417202005[51] = 0.0;
   out_5142011875417202005[52] = 0.0;
   out_5142011875417202005[53] = 0.0;
   out_5142011875417202005[54] = 0.0;
   out_5142011875417202005[55] = 0.0;
   out_5142011875417202005[56] = 0.0;
   out_5142011875417202005[57] = 1.0;
   out_5142011875417202005[58] = 0.0;
   out_5142011875417202005[59] = 0.0;
   out_5142011875417202005[60] = 0.0;
   out_5142011875417202005[61] = 0.0;
   out_5142011875417202005[62] = 0.0;
   out_5142011875417202005[63] = 0.0;
   out_5142011875417202005[64] = 0.0;
   out_5142011875417202005[65] = 0.0;
   out_5142011875417202005[66] = 0.0;
   out_5142011875417202005[67] = 0.0;
   out_5142011875417202005[68] = 0.0;
   out_5142011875417202005[69] = 0.0;
   out_5142011875417202005[70] = 0.0;
   out_5142011875417202005[71] = 0.0;
   out_5142011875417202005[72] = 0.0;
   out_5142011875417202005[73] = 0.0;
   out_5142011875417202005[74] = 0.0;
   out_5142011875417202005[75] = 0.0;
   out_5142011875417202005[76] = 1.0;
   out_5142011875417202005[77] = 0.0;
   out_5142011875417202005[78] = 0.0;
   out_5142011875417202005[79] = 0.0;
   out_5142011875417202005[80] = 0.0;
   out_5142011875417202005[81] = 0.0;
   out_5142011875417202005[82] = 0.0;
   out_5142011875417202005[83] = 0.0;
   out_5142011875417202005[84] = 0.0;
   out_5142011875417202005[85] = 0.0;
   out_5142011875417202005[86] = 0.0;
   out_5142011875417202005[87] = 0.0;
   out_5142011875417202005[88] = 0.0;
   out_5142011875417202005[89] = 0.0;
   out_5142011875417202005[90] = 0.0;
   out_5142011875417202005[91] = 0.0;
   out_5142011875417202005[92] = 0.0;
   out_5142011875417202005[93] = 0.0;
   out_5142011875417202005[94] = 0.0;
   out_5142011875417202005[95] = 1.0;
   out_5142011875417202005[96] = 0.0;
   out_5142011875417202005[97] = 0.0;
   out_5142011875417202005[98] = 0.0;
   out_5142011875417202005[99] = 0.0;
   out_5142011875417202005[100] = 0.0;
   out_5142011875417202005[101] = 0.0;
   out_5142011875417202005[102] = 0.0;
   out_5142011875417202005[103] = 0.0;
   out_5142011875417202005[104] = 0.0;
   out_5142011875417202005[105] = 0.0;
   out_5142011875417202005[106] = 0.0;
   out_5142011875417202005[107] = 0.0;
   out_5142011875417202005[108] = 0.0;
   out_5142011875417202005[109] = 0.0;
   out_5142011875417202005[110] = 0.0;
   out_5142011875417202005[111] = 0.0;
   out_5142011875417202005[112] = 0.0;
   out_5142011875417202005[113] = 0.0;
   out_5142011875417202005[114] = 1.0;
   out_5142011875417202005[115] = 0.0;
   out_5142011875417202005[116] = 0.0;
   out_5142011875417202005[117] = 0.0;
   out_5142011875417202005[118] = 0.0;
   out_5142011875417202005[119] = 0.0;
   out_5142011875417202005[120] = 0.0;
   out_5142011875417202005[121] = 0.0;
   out_5142011875417202005[122] = 0.0;
   out_5142011875417202005[123] = 0.0;
   out_5142011875417202005[124] = 0.0;
   out_5142011875417202005[125] = 0.0;
   out_5142011875417202005[126] = 0.0;
   out_5142011875417202005[127] = 0.0;
   out_5142011875417202005[128] = 0.0;
   out_5142011875417202005[129] = 0.0;
   out_5142011875417202005[130] = 0.0;
   out_5142011875417202005[131] = 0.0;
   out_5142011875417202005[132] = 0.0;
   out_5142011875417202005[133] = 1.0;
   out_5142011875417202005[134] = 0.0;
   out_5142011875417202005[135] = 0.0;
   out_5142011875417202005[136] = 0.0;
   out_5142011875417202005[137] = 0.0;
   out_5142011875417202005[138] = 0.0;
   out_5142011875417202005[139] = 0.0;
   out_5142011875417202005[140] = 0.0;
   out_5142011875417202005[141] = 0.0;
   out_5142011875417202005[142] = 0.0;
   out_5142011875417202005[143] = 0.0;
   out_5142011875417202005[144] = 0.0;
   out_5142011875417202005[145] = 0.0;
   out_5142011875417202005[146] = 0.0;
   out_5142011875417202005[147] = 0.0;
   out_5142011875417202005[148] = 0.0;
   out_5142011875417202005[149] = 0.0;
   out_5142011875417202005[150] = 0.0;
   out_5142011875417202005[151] = 0.0;
   out_5142011875417202005[152] = 1.0;
   out_5142011875417202005[153] = 0.0;
   out_5142011875417202005[154] = 0.0;
   out_5142011875417202005[155] = 0.0;
   out_5142011875417202005[156] = 0.0;
   out_5142011875417202005[157] = 0.0;
   out_5142011875417202005[158] = 0.0;
   out_5142011875417202005[159] = 0.0;
   out_5142011875417202005[160] = 0.0;
   out_5142011875417202005[161] = 0.0;
   out_5142011875417202005[162] = 0.0;
   out_5142011875417202005[163] = 0.0;
   out_5142011875417202005[164] = 0.0;
   out_5142011875417202005[165] = 0.0;
   out_5142011875417202005[166] = 0.0;
   out_5142011875417202005[167] = 0.0;
   out_5142011875417202005[168] = 0.0;
   out_5142011875417202005[169] = 0.0;
   out_5142011875417202005[170] = 0.0;
   out_5142011875417202005[171] = 1.0;
   out_5142011875417202005[172] = 0.0;
   out_5142011875417202005[173] = 0.0;
   out_5142011875417202005[174] = 0.0;
   out_5142011875417202005[175] = 0.0;
   out_5142011875417202005[176] = 0.0;
   out_5142011875417202005[177] = 0.0;
   out_5142011875417202005[178] = 0.0;
   out_5142011875417202005[179] = 0.0;
   out_5142011875417202005[180] = 0.0;
   out_5142011875417202005[181] = 0.0;
   out_5142011875417202005[182] = 0.0;
   out_5142011875417202005[183] = 0.0;
   out_5142011875417202005[184] = 0.0;
   out_5142011875417202005[185] = 0.0;
   out_5142011875417202005[186] = 0.0;
   out_5142011875417202005[187] = 0.0;
   out_5142011875417202005[188] = 0.0;
   out_5142011875417202005[189] = 0.0;
   out_5142011875417202005[190] = 1.0;
   out_5142011875417202005[191] = 0.0;
   out_5142011875417202005[192] = 0.0;
   out_5142011875417202005[193] = 0.0;
   out_5142011875417202005[194] = 0.0;
   out_5142011875417202005[195] = 0.0;
   out_5142011875417202005[196] = 0.0;
   out_5142011875417202005[197] = 0.0;
   out_5142011875417202005[198] = 0.0;
   out_5142011875417202005[199] = 0.0;
   out_5142011875417202005[200] = 0.0;
   out_5142011875417202005[201] = 0.0;
   out_5142011875417202005[202] = 0.0;
   out_5142011875417202005[203] = 0.0;
   out_5142011875417202005[204] = 0.0;
   out_5142011875417202005[205] = 0.0;
   out_5142011875417202005[206] = 0.0;
   out_5142011875417202005[207] = 0.0;
   out_5142011875417202005[208] = 0.0;
   out_5142011875417202005[209] = 1.0;
   out_5142011875417202005[210] = 0.0;
   out_5142011875417202005[211] = 0.0;
   out_5142011875417202005[212] = 0.0;
   out_5142011875417202005[213] = 0.0;
   out_5142011875417202005[214] = 0.0;
   out_5142011875417202005[215] = 0.0;
   out_5142011875417202005[216] = 0.0;
   out_5142011875417202005[217] = 0.0;
   out_5142011875417202005[218] = 0.0;
   out_5142011875417202005[219] = 0.0;
   out_5142011875417202005[220] = 0.0;
   out_5142011875417202005[221] = 0.0;
   out_5142011875417202005[222] = 0.0;
   out_5142011875417202005[223] = 0.0;
   out_5142011875417202005[224] = 0.0;
   out_5142011875417202005[225] = 0.0;
   out_5142011875417202005[226] = 0.0;
   out_5142011875417202005[227] = 0.0;
   out_5142011875417202005[228] = 1.0;
   out_5142011875417202005[229] = 0.0;
   out_5142011875417202005[230] = 0.0;
   out_5142011875417202005[231] = 0.0;
   out_5142011875417202005[232] = 0.0;
   out_5142011875417202005[233] = 0.0;
   out_5142011875417202005[234] = 0.0;
   out_5142011875417202005[235] = 0.0;
   out_5142011875417202005[236] = 0.0;
   out_5142011875417202005[237] = 0.0;
   out_5142011875417202005[238] = 0.0;
   out_5142011875417202005[239] = 0.0;
   out_5142011875417202005[240] = 0.0;
   out_5142011875417202005[241] = 0.0;
   out_5142011875417202005[242] = 0.0;
   out_5142011875417202005[243] = 0.0;
   out_5142011875417202005[244] = 0.0;
   out_5142011875417202005[245] = 0.0;
   out_5142011875417202005[246] = 0.0;
   out_5142011875417202005[247] = 1.0;
   out_5142011875417202005[248] = 0.0;
   out_5142011875417202005[249] = 0.0;
   out_5142011875417202005[250] = 0.0;
   out_5142011875417202005[251] = 0.0;
   out_5142011875417202005[252] = 0.0;
   out_5142011875417202005[253] = 0.0;
   out_5142011875417202005[254] = 0.0;
   out_5142011875417202005[255] = 0.0;
   out_5142011875417202005[256] = 0.0;
   out_5142011875417202005[257] = 0.0;
   out_5142011875417202005[258] = 0.0;
   out_5142011875417202005[259] = 0.0;
   out_5142011875417202005[260] = 0.0;
   out_5142011875417202005[261] = 0.0;
   out_5142011875417202005[262] = 0.0;
   out_5142011875417202005[263] = 0.0;
   out_5142011875417202005[264] = 0.0;
   out_5142011875417202005[265] = 0.0;
   out_5142011875417202005[266] = 1.0;
   out_5142011875417202005[267] = 0.0;
   out_5142011875417202005[268] = 0.0;
   out_5142011875417202005[269] = 0.0;
   out_5142011875417202005[270] = 0.0;
   out_5142011875417202005[271] = 0.0;
   out_5142011875417202005[272] = 0.0;
   out_5142011875417202005[273] = 0.0;
   out_5142011875417202005[274] = 0.0;
   out_5142011875417202005[275] = 0.0;
   out_5142011875417202005[276] = 0.0;
   out_5142011875417202005[277] = 0.0;
   out_5142011875417202005[278] = 0.0;
   out_5142011875417202005[279] = 0.0;
   out_5142011875417202005[280] = 0.0;
   out_5142011875417202005[281] = 0.0;
   out_5142011875417202005[282] = 0.0;
   out_5142011875417202005[283] = 0.0;
   out_5142011875417202005[284] = 0.0;
   out_5142011875417202005[285] = 1.0;
   out_5142011875417202005[286] = 0.0;
   out_5142011875417202005[287] = 0.0;
   out_5142011875417202005[288] = 0.0;
   out_5142011875417202005[289] = 0.0;
   out_5142011875417202005[290] = 0.0;
   out_5142011875417202005[291] = 0.0;
   out_5142011875417202005[292] = 0.0;
   out_5142011875417202005[293] = 0.0;
   out_5142011875417202005[294] = 0.0;
   out_5142011875417202005[295] = 0.0;
   out_5142011875417202005[296] = 0.0;
   out_5142011875417202005[297] = 0.0;
   out_5142011875417202005[298] = 0.0;
   out_5142011875417202005[299] = 0.0;
   out_5142011875417202005[300] = 0.0;
   out_5142011875417202005[301] = 0.0;
   out_5142011875417202005[302] = 0.0;
   out_5142011875417202005[303] = 0.0;
   out_5142011875417202005[304] = 1.0;
   out_5142011875417202005[305] = 0.0;
   out_5142011875417202005[306] = 0.0;
   out_5142011875417202005[307] = 0.0;
   out_5142011875417202005[308] = 0.0;
   out_5142011875417202005[309] = 0.0;
   out_5142011875417202005[310] = 0.0;
   out_5142011875417202005[311] = 0.0;
   out_5142011875417202005[312] = 0.0;
   out_5142011875417202005[313] = 0.0;
   out_5142011875417202005[314] = 0.0;
   out_5142011875417202005[315] = 0.0;
   out_5142011875417202005[316] = 0.0;
   out_5142011875417202005[317] = 0.0;
   out_5142011875417202005[318] = 0.0;
   out_5142011875417202005[319] = 0.0;
   out_5142011875417202005[320] = 0.0;
   out_5142011875417202005[321] = 0.0;
   out_5142011875417202005[322] = 0.0;
   out_5142011875417202005[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_203013903358445647) {
   out_203013903358445647[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_203013903358445647[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_203013903358445647[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_203013903358445647[3] = dt*state[12] + state[3];
   out_203013903358445647[4] = dt*state[13] + state[4];
   out_203013903358445647[5] = dt*state[14] + state[5];
   out_203013903358445647[6] = state[6];
   out_203013903358445647[7] = state[7];
   out_203013903358445647[8] = state[8];
   out_203013903358445647[9] = state[9];
   out_203013903358445647[10] = state[10];
   out_203013903358445647[11] = state[11];
   out_203013903358445647[12] = state[12];
   out_203013903358445647[13] = state[13];
   out_203013903358445647[14] = state[14];
   out_203013903358445647[15] = state[15];
   out_203013903358445647[16] = state[16];
   out_203013903358445647[17] = state[17];
}
void F_fun(double *state, double dt, double *out_7326468457789213143) {
   out_7326468457789213143[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_7326468457789213143[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_7326468457789213143[2] = 0;
   out_7326468457789213143[3] = 0;
   out_7326468457789213143[4] = 0;
   out_7326468457789213143[5] = 0;
   out_7326468457789213143[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_7326468457789213143[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_7326468457789213143[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_7326468457789213143[9] = 0;
   out_7326468457789213143[10] = 0;
   out_7326468457789213143[11] = 0;
   out_7326468457789213143[12] = 0;
   out_7326468457789213143[13] = 0;
   out_7326468457789213143[14] = 0;
   out_7326468457789213143[15] = 0;
   out_7326468457789213143[16] = 0;
   out_7326468457789213143[17] = 0;
   out_7326468457789213143[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_7326468457789213143[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_7326468457789213143[20] = 0;
   out_7326468457789213143[21] = 0;
   out_7326468457789213143[22] = 0;
   out_7326468457789213143[23] = 0;
   out_7326468457789213143[24] = 0;
   out_7326468457789213143[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_7326468457789213143[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_7326468457789213143[27] = 0;
   out_7326468457789213143[28] = 0;
   out_7326468457789213143[29] = 0;
   out_7326468457789213143[30] = 0;
   out_7326468457789213143[31] = 0;
   out_7326468457789213143[32] = 0;
   out_7326468457789213143[33] = 0;
   out_7326468457789213143[34] = 0;
   out_7326468457789213143[35] = 0;
   out_7326468457789213143[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_7326468457789213143[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_7326468457789213143[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_7326468457789213143[39] = 0;
   out_7326468457789213143[40] = 0;
   out_7326468457789213143[41] = 0;
   out_7326468457789213143[42] = 0;
   out_7326468457789213143[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_7326468457789213143[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_7326468457789213143[45] = 0;
   out_7326468457789213143[46] = 0;
   out_7326468457789213143[47] = 0;
   out_7326468457789213143[48] = 0;
   out_7326468457789213143[49] = 0;
   out_7326468457789213143[50] = 0;
   out_7326468457789213143[51] = 0;
   out_7326468457789213143[52] = 0;
   out_7326468457789213143[53] = 0;
   out_7326468457789213143[54] = 0;
   out_7326468457789213143[55] = 0;
   out_7326468457789213143[56] = 0;
   out_7326468457789213143[57] = 1;
   out_7326468457789213143[58] = 0;
   out_7326468457789213143[59] = 0;
   out_7326468457789213143[60] = 0;
   out_7326468457789213143[61] = 0;
   out_7326468457789213143[62] = 0;
   out_7326468457789213143[63] = 0;
   out_7326468457789213143[64] = 0;
   out_7326468457789213143[65] = 0;
   out_7326468457789213143[66] = dt;
   out_7326468457789213143[67] = 0;
   out_7326468457789213143[68] = 0;
   out_7326468457789213143[69] = 0;
   out_7326468457789213143[70] = 0;
   out_7326468457789213143[71] = 0;
   out_7326468457789213143[72] = 0;
   out_7326468457789213143[73] = 0;
   out_7326468457789213143[74] = 0;
   out_7326468457789213143[75] = 0;
   out_7326468457789213143[76] = 1;
   out_7326468457789213143[77] = 0;
   out_7326468457789213143[78] = 0;
   out_7326468457789213143[79] = 0;
   out_7326468457789213143[80] = 0;
   out_7326468457789213143[81] = 0;
   out_7326468457789213143[82] = 0;
   out_7326468457789213143[83] = 0;
   out_7326468457789213143[84] = 0;
   out_7326468457789213143[85] = dt;
   out_7326468457789213143[86] = 0;
   out_7326468457789213143[87] = 0;
   out_7326468457789213143[88] = 0;
   out_7326468457789213143[89] = 0;
   out_7326468457789213143[90] = 0;
   out_7326468457789213143[91] = 0;
   out_7326468457789213143[92] = 0;
   out_7326468457789213143[93] = 0;
   out_7326468457789213143[94] = 0;
   out_7326468457789213143[95] = 1;
   out_7326468457789213143[96] = 0;
   out_7326468457789213143[97] = 0;
   out_7326468457789213143[98] = 0;
   out_7326468457789213143[99] = 0;
   out_7326468457789213143[100] = 0;
   out_7326468457789213143[101] = 0;
   out_7326468457789213143[102] = 0;
   out_7326468457789213143[103] = 0;
   out_7326468457789213143[104] = dt;
   out_7326468457789213143[105] = 0;
   out_7326468457789213143[106] = 0;
   out_7326468457789213143[107] = 0;
   out_7326468457789213143[108] = 0;
   out_7326468457789213143[109] = 0;
   out_7326468457789213143[110] = 0;
   out_7326468457789213143[111] = 0;
   out_7326468457789213143[112] = 0;
   out_7326468457789213143[113] = 0;
   out_7326468457789213143[114] = 1;
   out_7326468457789213143[115] = 0;
   out_7326468457789213143[116] = 0;
   out_7326468457789213143[117] = 0;
   out_7326468457789213143[118] = 0;
   out_7326468457789213143[119] = 0;
   out_7326468457789213143[120] = 0;
   out_7326468457789213143[121] = 0;
   out_7326468457789213143[122] = 0;
   out_7326468457789213143[123] = 0;
   out_7326468457789213143[124] = 0;
   out_7326468457789213143[125] = 0;
   out_7326468457789213143[126] = 0;
   out_7326468457789213143[127] = 0;
   out_7326468457789213143[128] = 0;
   out_7326468457789213143[129] = 0;
   out_7326468457789213143[130] = 0;
   out_7326468457789213143[131] = 0;
   out_7326468457789213143[132] = 0;
   out_7326468457789213143[133] = 1;
   out_7326468457789213143[134] = 0;
   out_7326468457789213143[135] = 0;
   out_7326468457789213143[136] = 0;
   out_7326468457789213143[137] = 0;
   out_7326468457789213143[138] = 0;
   out_7326468457789213143[139] = 0;
   out_7326468457789213143[140] = 0;
   out_7326468457789213143[141] = 0;
   out_7326468457789213143[142] = 0;
   out_7326468457789213143[143] = 0;
   out_7326468457789213143[144] = 0;
   out_7326468457789213143[145] = 0;
   out_7326468457789213143[146] = 0;
   out_7326468457789213143[147] = 0;
   out_7326468457789213143[148] = 0;
   out_7326468457789213143[149] = 0;
   out_7326468457789213143[150] = 0;
   out_7326468457789213143[151] = 0;
   out_7326468457789213143[152] = 1;
   out_7326468457789213143[153] = 0;
   out_7326468457789213143[154] = 0;
   out_7326468457789213143[155] = 0;
   out_7326468457789213143[156] = 0;
   out_7326468457789213143[157] = 0;
   out_7326468457789213143[158] = 0;
   out_7326468457789213143[159] = 0;
   out_7326468457789213143[160] = 0;
   out_7326468457789213143[161] = 0;
   out_7326468457789213143[162] = 0;
   out_7326468457789213143[163] = 0;
   out_7326468457789213143[164] = 0;
   out_7326468457789213143[165] = 0;
   out_7326468457789213143[166] = 0;
   out_7326468457789213143[167] = 0;
   out_7326468457789213143[168] = 0;
   out_7326468457789213143[169] = 0;
   out_7326468457789213143[170] = 0;
   out_7326468457789213143[171] = 1;
   out_7326468457789213143[172] = 0;
   out_7326468457789213143[173] = 0;
   out_7326468457789213143[174] = 0;
   out_7326468457789213143[175] = 0;
   out_7326468457789213143[176] = 0;
   out_7326468457789213143[177] = 0;
   out_7326468457789213143[178] = 0;
   out_7326468457789213143[179] = 0;
   out_7326468457789213143[180] = 0;
   out_7326468457789213143[181] = 0;
   out_7326468457789213143[182] = 0;
   out_7326468457789213143[183] = 0;
   out_7326468457789213143[184] = 0;
   out_7326468457789213143[185] = 0;
   out_7326468457789213143[186] = 0;
   out_7326468457789213143[187] = 0;
   out_7326468457789213143[188] = 0;
   out_7326468457789213143[189] = 0;
   out_7326468457789213143[190] = 1;
   out_7326468457789213143[191] = 0;
   out_7326468457789213143[192] = 0;
   out_7326468457789213143[193] = 0;
   out_7326468457789213143[194] = 0;
   out_7326468457789213143[195] = 0;
   out_7326468457789213143[196] = 0;
   out_7326468457789213143[197] = 0;
   out_7326468457789213143[198] = 0;
   out_7326468457789213143[199] = 0;
   out_7326468457789213143[200] = 0;
   out_7326468457789213143[201] = 0;
   out_7326468457789213143[202] = 0;
   out_7326468457789213143[203] = 0;
   out_7326468457789213143[204] = 0;
   out_7326468457789213143[205] = 0;
   out_7326468457789213143[206] = 0;
   out_7326468457789213143[207] = 0;
   out_7326468457789213143[208] = 0;
   out_7326468457789213143[209] = 1;
   out_7326468457789213143[210] = 0;
   out_7326468457789213143[211] = 0;
   out_7326468457789213143[212] = 0;
   out_7326468457789213143[213] = 0;
   out_7326468457789213143[214] = 0;
   out_7326468457789213143[215] = 0;
   out_7326468457789213143[216] = 0;
   out_7326468457789213143[217] = 0;
   out_7326468457789213143[218] = 0;
   out_7326468457789213143[219] = 0;
   out_7326468457789213143[220] = 0;
   out_7326468457789213143[221] = 0;
   out_7326468457789213143[222] = 0;
   out_7326468457789213143[223] = 0;
   out_7326468457789213143[224] = 0;
   out_7326468457789213143[225] = 0;
   out_7326468457789213143[226] = 0;
   out_7326468457789213143[227] = 0;
   out_7326468457789213143[228] = 1;
   out_7326468457789213143[229] = 0;
   out_7326468457789213143[230] = 0;
   out_7326468457789213143[231] = 0;
   out_7326468457789213143[232] = 0;
   out_7326468457789213143[233] = 0;
   out_7326468457789213143[234] = 0;
   out_7326468457789213143[235] = 0;
   out_7326468457789213143[236] = 0;
   out_7326468457789213143[237] = 0;
   out_7326468457789213143[238] = 0;
   out_7326468457789213143[239] = 0;
   out_7326468457789213143[240] = 0;
   out_7326468457789213143[241] = 0;
   out_7326468457789213143[242] = 0;
   out_7326468457789213143[243] = 0;
   out_7326468457789213143[244] = 0;
   out_7326468457789213143[245] = 0;
   out_7326468457789213143[246] = 0;
   out_7326468457789213143[247] = 1;
   out_7326468457789213143[248] = 0;
   out_7326468457789213143[249] = 0;
   out_7326468457789213143[250] = 0;
   out_7326468457789213143[251] = 0;
   out_7326468457789213143[252] = 0;
   out_7326468457789213143[253] = 0;
   out_7326468457789213143[254] = 0;
   out_7326468457789213143[255] = 0;
   out_7326468457789213143[256] = 0;
   out_7326468457789213143[257] = 0;
   out_7326468457789213143[258] = 0;
   out_7326468457789213143[259] = 0;
   out_7326468457789213143[260] = 0;
   out_7326468457789213143[261] = 0;
   out_7326468457789213143[262] = 0;
   out_7326468457789213143[263] = 0;
   out_7326468457789213143[264] = 0;
   out_7326468457789213143[265] = 0;
   out_7326468457789213143[266] = 1;
   out_7326468457789213143[267] = 0;
   out_7326468457789213143[268] = 0;
   out_7326468457789213143[269] = 0;
   out_7326468457789213143[270] = 0;
   out_7326468457789213143[271] = 0;
   out_7326468457789213143[272] = 0;
   out_7326468457789213143[273] = 0;
   out_7326468457789213143[274] = 0;
   out_7326468457789213143[275] = 0;
   out_7326468457789213143[276] = 0;
   out_7326468457789213143[277] = 0;
   out_7326468457789213143[278] = 0;
   out_7326468457789213143[279] = 0;
   out_7326468457789213143[280] = 0;
   out_7326468457789213143[281] = 0;
   out_7326468457789213143[282] = 0;
   out_7326468457789213143[283] = 0;
   out_7326468457789213143[284] = 0;
   out_7326468457789213143[285] = 1;
   out_7326468457789213143[286] = 0;
   out_7326468457789213143[287] = 0;
   out_7326468457789213143[288] = 0;
   out_7326468457789213143[289] = 0;
   out_7326468457789213143[290] = 0;
   out_7326468457789213143[291] = 0;
   out_7326468457789213143[292] = 0;
   out_7326468457789213143[293] = 0;
   out_7326468457789213143[294] = 0;
   out_7326468457789213143[295] = 0;
   out_7326468457789213143[296] = 0;
   out_7326468457789213143[297] = 0;
   out_7326468457789213143[298] = 0;
   out_7326468457789213143[299] = 0;
   out_7326468457789213143[300] = 0;
   out_7326468457789213143[301] = 0;
   out_7326468457789213143[302] = 0;
   out_7326468457789213143[303] = 0;
   out_7326468457789213143[304] = 1;
   out_7326468457789213143[305] = 0;
   out_7326468457789213143[306] = 0;
   out_7326468457789213143[307] = 0;
   out_7326468457789213143[308] = 0;
   out_7326468457789213143[309] = 0;
   out_7326468457789213143[310] = 0;
   out_7326468457789213143[311] = 0;
   out_7326468457789213143[312] = 0;
   out_7326468457789213143[313] = 0;
   out_7326468457789213143[314] = 0;
   out_7326468457789213143[315] = 0;
   out_7326468457789213143[316] = 0;
   out_7326468457789213143[317] = 0;
   out_7326468457789213143[318] = 0;
   out_7326468457789213143[319] = 0;
   out_7326468457789213143[320] = 0;
   out_7326468457789213143[321] = 0;
   out_7326468457789213143[322] = 0;
   out_7326468457789213143[323] = 1;
}
void h_4(double *state, double *unused, double *out_8153824291242181436) {
   out_8153824291242181436[0] = state[6] + state[9];
   out_8153824291242181436[1] = state[7] + state[10];
   out_8153824291242181436[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_3058293008556022762) {
   out_3058293008556022762[0] = 0;
   out_3058293008556022762[1] = 0;
   out_3058293008556022762[2] = 0;
   out_3058293008556022762[3] = 0;
   out_3058293008556022762[4] = 0;
   out_3058293008556022762[5] = 0;
   out_3058293008556022762[6] = 1;
   out_3058293008556022762[7] = 0;
   out_3058293008556022762[8] = 0;
   out_3058293008556022762[9] = 1;
   out_3058293008556022762[10] = 0;
   out_3058293008556022762[11] = 0;
   out_3058293008556022762[12] = 0;
   out_3058293008556022762[13] = 0;
   out_3058293008556022762[14] = 0;
   out_3058293008556022762[15] = 0;
   out_3058293008556022762[16] = 0;
   out_3058293008556022762[17] = 0;
   out_3058293008556022762[18] = 0;
   out_3058293008556022762[19] = 0;
   out_3058293008556022762[20] = 0;
   out_3058293008556022762[21] = 0;
   out_3058293008556022762[22] = 0;
   out_3058293008556022762[23] = 0;
   out_3058293008556022762[24] = 0;
   out_3058293008556022762[25] = 1;
   out_3058293008556022762[26] = 0;
   out_3058293008556022762[27] = 0;
   out_3058293008556022762[28] = 1;
   out_3058293008556022762[29] = 0;
   out_3058293008556022762[30] = 0;
   out_3058293008556022762[31] = 0;
   out_3058293008556022762[32] = 0;
   out_3058293008556022762[33] = 0;
   out_3058293008556022762[34] = 0;
   out_3058293008556022762[35] = 0;
   out_3058293008556022762[36] = 0;
   out_3058293008556022762[37] = 0;
   out_3058293008556022762[38] = 0;
   out_3058293008556022762[39] = 0;
   out_3058293008556022762[40] = 0;
   out_3058293008556022762[41] = 0;
   out_3058293008556022762[42] = 0;
   out_3058293008556022762[43] = 0;
   out_3058293008556022762[44] = 1;
   out_3058293008556022762[45] = 0;
   out_3058293008556022762[46] = 0;
   out_3058293008556022762[47] = 1;
   out_3058293008556022762[48] = 0;
   out_3058293008556022762[49] = 0;
   out_3058293008556022762[50] = 0;
   out_3058293008556022762[51] = 0;
   out_3058293008556022762[52] = 0;
   out_3058293008556022762[53] = 0;
}
void h_10(double *state, double *unused, double *out_3951144425666594182) {
   out_3951144425666594182[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_3951144425666594182[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_3951144425666594182[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_3697294613085597244) {
   out_3697294613085597244[0] = 0;
   out_3697294613085597244[1] = 9.8100000000000005*cos(state[1]);
   out_3697294613085597244[2] = 0;
   out_3697294613085597244[3] = 0;
   out_3697294613085597244[4] = -state[8];
   out_3697294613085597244[5] = state[7];
   out_3697294613085597244[6] = 0;
   out_3697294613085597244[7] = state[5];
   out_3697294613085597244[8] = -state[4];
   out_3697294613085597244[9] = 0;
   out_3697294613085597244[10] = 0;
   out_3697294613085597244[11] = 0;
   out_3697294613085597244[12] = 1;
   out_3697294613085597244[13] = 0;
   out_3697294613085597244[14] = 0;
   out_3697294613085597244[15] = 1;
   out_3697294613085597244[16] = 0;
   out_3697294613085597244[17] = 0;
   out_3697294613085597244[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_3697294613085597244[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_3697294613085597244[20] = 0;
   out_3697294613085597244[21] = state[8];
   out_3697294613085597244[22] = 0;
   out_3697294613085597244[23] = -state[6];
   out_3697294613085597244[24] = -state[5];
   out_3697294613085597244[25] = 0;
   out_3697294613085597244[26] = state[3];
   out_3697294613085597244[27] = 0;
   out_3697294613085597244[28] = 0;
   out_3697294613085597244[29] = 0;
   out_3697294613085597244[30] = 0;
   out_3697294613085597244[31] = 1;
   out_3697294613085597244[32] = 0;
   out_3697294613085597244[33] = 0;
   out_3697294613085597244[34] = 1;
   out_3697294613085597244[35] = 0;
   out_3697294613085597244[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_3697294613085597244[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_3697294613085597244[38] = 0;
   out_3697294613085597244[39] = -state[7];
   out_3697294613085597244[40] = state[6];
   out_3697294613085597244[41] = 0;
   out_3697294613085597244[42] = state[4];
   out_3697294613085597244[43] = -state[3];
   out_3697294613085597244[44] = 0;
   out_3697294613085597244[45] = 0;
   out_3697294613085597244[46] = 0;
   out_3697294613085597244[47] = 0;
   out_3697294613085597244[48] = 0;
   out_3697294613085597244[49] = 0;
   out_3697294613085597244[50] = 1;
   out_3697294613085597244[51] = 0;
   out_3697294613085597244[52] = 0;
   out_3697294613085597244[53] = 1;
}
void h_13(double *state, double *unused, double *out_6907487104961603826) {
   out_6907487104961603826[0] = state[3];
   out_6907487104961603826[1] = state[4];
   out_6907487104961603826[2] = state[5];
}
void H_13(double *state, double *unused, double *out_7777819856836827925) {
   out_7777819856836827925[0] = 0;
   out_7777819856836827925[1] = 0;
   out_7777819856836827925[2] = 0;
   out_7777819856836827925[3] = 1;
   out_7777819856836827925[4] = 0;
   out_7777819856836827925[5] = 0;
   out_7777819856836827925[6] = 0;
   out_7777819856836827925[7] = 0;
   out_7777819856836827925[8] = 0;
   out_7777819856836827925[9] = 0;
   out_7777819856836827925[10] = 0;
   out_7777819856836827925[11] = 0;
   out_7777819856836827925[12] = 0;
   out_7777819856836827925[13] = 0;
   out_7777819856836827925[14] = 0;
   out_7777819856836827925[15] = 0;
   out_7777819856836827925[16] = 0;
   out_7777819856836827925[17] = 0;
   out_7777819856836827925[18] = 0;
   out_7777819856836827925[19] = 0;
   out_7777819856836827925[20] = 0;
   out_7777819856836827925[21] = 0;
   out_7777819856836827925[22] = 1;
   out_7777819856836827925[23] = 0;
   out_7777819856836827925[24] = 0;
   out_7777819856836827925[25] = 0;
   out_7777819856836827925[26] = 0;
   out_7777819856836827925[27] = 0;
   out_7777819856836827925[28] = 0;
   out_7777819856836827925[29] = 0;
   out_7777819856836827925[30] = 0;
   out_7777819856836827925[31] = 0;
   out_7777819856836827925[32] = 0;
   out_7777819856836827925[33] = 0;
   out_7777819856836827925[34] = 0;
   out_7777819856836827925[35] = 0;
   out_7777819856836827925[36] = 0;
   out_7777819856836827925[37] = 0;
   out_7777819856836827925[38] = 0;
   out_7777819856836827925[39] = 0;
   out_7777819856836827925[40] = 0;
   out_7777819856836827925[41] = 1;
   out_7777819856836827925[42] = 0;
   out_7777819856836827925[43] = 0;
   out_7777819856836827925[44] = 0;
   out_7777819856836827925[45] = 0;
   out_7777819856836827925[46] = 0;
   out_7777819856836827925[47] = 0;
   out_7777819856836827925[48] = 0;
   out_7777819856836827925[49] = 0;
   out_7777819856836827925[50] = 0;
   out_7777819856836827925[51] = 0;
   out_7777819856836827925[52] = 0;
   out_7777819856836827925[53] = 0;
}
void h_14(double *state, double *unused, double *out_2370415612838457693) {
   out_2370415612838457693[0] = state[6];
   out_2370415612838457693[1] = state[7];
   out_2370415612838457693[2] = state[8];
}
void H_14(double *state, double *unused, double *out_7021533864895507291) {
   out_7021533864895507291[0] = 0;
   out_7021533864895507291[1] = 0;
   out_7021533864895507291[2] = 0;
   out_7021533864895507291[3] = 0;
   out_7021533864895507291[4] = 0;
   out_7021533864895507291[5] = 0;
   out_7021533864895507291[6] = 1;
   out_7021533864895507291[7] = 0;
   out_7021533864895507291[8] = 0;
   out_7021533864895507291[9] = 0;
   out_7021533864895507291[10] = 0;
   out_7021533864895507291[11] = 0;
   out_7021533864895507291[12] = 0;
   out_7021533864895507291[13] = 0;
   out_7021533864895507291[14] = 0;
   out_7021533864895507291[15] = 0;
   out_7021533864895507291[16] = 0;
   out_7021533864895507291[17] = 0;
   out_7021533864895507291[18] = 0;
   out_7021533864895507291[19] = 0;
   out_7021533864895507291[20] = 0;
   out_7021533864895507291[21] = 0;
   out_7021533864895507291[22] = 0;
   out_7021533864895507291[23] = 0;
   out_7021533864895507291[24] = 0;
   out_7021533864895507291[25] = 1;
   out_7021533864895507291[26] = 0;
   out_7021533864895507291[27] = 0;
   out_7021533864895507291[28] = 0;
   out_7021533864895507291[29] = 0;
   out_7021533864895507291[30] = 0;
   out_7021533864895507291[31] = 0;
   out_7021533864895507291[32] = 0;
   out_7021533864895507291[33] = 0;
   out_7021533864895507291[34] = 0;
   out_7021533864895507291[35] = 0;
   out_7021533864895507291[36] = 0;
   out_7021533864895507291[37] = 0;
   out_7021533864895507291[38] = 0;
   out_7021533864895507291[39] = 0;
   out_7021533864895507291[40] = 0;
   out_7021533864895507291[41] = 0;
   out_7021533864895507291[42] = 0;
   out_7021533864895507291[43] = 0;
   out_7021533864895507291[44] = 1;
   out_7021533864895507291[45] = 0;
   out_7021533864895507291[46] = 0;
   out_7021533864895507291[47] = 0;
   out_7021533864895507291[48] = 0;
   out_7021533864895507291[49] = 0;
   out_7021533864895507291[50] = 0;
   out_7021533864895507291[51] = 0;
   out_7021533864895507291[52] = 0;
   out_7021533864895507291[53] = 0;
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
void pose_err_fun(double *nom_x, double *delta_x, double *out_7505672412271645129) {
  err_fun(nom_x, delta_x, out_7505672412271645129);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_850525553930579209) {
  inv_err_fun(nom_x, true_x, out_850525553930579209);
}
void pose_H_mod_fun(double *state, double *out_5142011875417202005) {
  H_mod_fun(state, out_5142011875417202005);
}
void pose_f_fun(double *state, double dt, double *out_203013903358445647) {
  f_fun(state,  dt, out_203013903358445647);
}
void pose_F_fun(double *state, double dt, double *out_7326468457789213143) {
  F_fun(state,  dt, out_7326468457789213143);
}
void pose_h_4(double *state, double *unused, double *out_8153824291242181436) {
  h_4(state, unused, out_8153824291242181436);
}
void pose_H_4(double *state, double *unused, double *out_3058293008556022762) {
  H_4(state, unused, out_3058293008556022762);
}
void pose_h_10(double *state, double *unused, double *out_3951144425666594182) {
  h_10(state, unused, out_3951144425666594182);
}
void pose_H_10(double *state, double *unused, double *out_3697294613085597244) {
  H_10(state, unused, out_3697294613085597244);
}
void pose_h_13(double *state, double *unused, double *out_6907487104961603826) {
  h_13(state, unused, out_6907487104961603826);
}
void pose_H_13(double *state, double *unused, double *out_7777819856836827925) {
  H_13(state, unused, out_7777819856836827925);
}
void pose_h_14(double *state, double *unused, double *out_2370415612838457693) {
  h_14(state, unused, out_2370415612838457693);
}
void pose_H_14(double *state, double *unused, double *out_7021533864895507291) {
  H_14(state, unused, out_7021533864895507291);
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
