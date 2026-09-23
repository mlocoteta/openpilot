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
void err_fun(double *nom_x, double *delta_x, double *out_3683974983863530851) {
   out_3683974983863530851[0] = delta_x[0] + nom_x[0];
   out_3683974983863530851[1] = delta_x[1] + nom_x[1];
   out_3683974983863530851[2] = delta_x[2] + nom_x[2];
   out_3683974983863530851[3] = delta_x[3] + nom_x[3];
   out_3683974983863530851[4] = delta_x[4] + nom_x[4];
   out_3683974983863530851[5] = delta_x[5] + nom_x[5];
   out_3683974983863530851[6] = delta_x[6] + nom_x[6];
   out_3683974983863530851[7] = delta_x[7] + nom_x[7];
   out_3683974983863530851[8] = delta_x[8] + nom_x[8];
   out_3683974983863530851[9] = delta_x[9] + nom_x[9];
   out_3683974983863530851[10] = delta_x[10] + nom_x[10];
   out_3683974983863530851[11] = delta_x[11] + nom_x[11];
   out_3683974983863530851[12] = delta_x[12] + nom_x[12];
   out_3683974983863530851[13] = delta_x[13] + nom_x[13];
   out_3683974983863530851[14] = delta_x[14] + nom_x[14];
   out_3683974983863530851[15] = delta_x[15] + nom_x[15];
   out_3683974983863530851[16] = delta_x[16] + nom_x[16];
   out_3683974983863530851[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_7161705307985060718) {
   out_7161705307985060718[0] = -nom_x[0] + true_x[0];
   out_7161705307985060718[1] = -nom_x[1] + true_x[1];
   out_7161705307985060718[2] = -nom_x[2] + true_x[2];
   out_7161705307985060718[3] = -nom_x[3] + true_x[3];
   out_7161705307985060718[4] = -nom_x[4] + true_x[4];
   out_7161705307985060718[5] = -nom_x[5] + true_x[5];
   out_7161705307985060718[6] = -nom_x[6] + true_x[6];
   out_7161705307985060718[7] = -nom_x[7] + true_x[7];
   out_7161705307985060718[8] = -nom_x[8] + true_x[8];
   out_7161705307985060718[9] = -nom_x[9] + true_x[9];
   out_7161705307985060718[10] = -nom_x[10] + true_x[10];
   out_7161705307985060718[11] = -nom_x[11] + true_x[11];
   out_7161705307985060718[12] = -nom_x[12] + true_x[12];
   out_7161705307985060718[13] = -nom_x[13] + true_x[13];
   out_7161705307985060718[14] = -nom_x[14] + true_x[14];
   out_7161705307985060718[15] = -nom_x[15] + true_x[15];
   out_7161705307985060718[16] = -nom_x[16] + true_x[16];
   out_7161705307985060718[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_8701255044286026870) {
   out_8701255044286026870[0] = 1.0;
   out_8701255044286026870[1] = 0.0;
   out_8701255044286026870[2] = 0.0;
   out_8701255044286026870[3] = 0.0;
   out_8701255044286026870[4] = 0.0;
   out_8701255044286026870[5] = 0.0;
   out_8701255044286026870[6] = 0.0;
   out_8701255044286026870[7] = 0.0;
   out_8701255044286026870[8] = 0.0;
   out_8701255044286026870[9] = 0.0;
   out_8701255044286026870[10] = 0.0;
   out_8701255044286026870[11] = 0.0;
   out_8701255044286026870[12] = 0.0;
   out_8701255044286026870[13] = 0.0;
   out_8701255044286026870[14] = 0.0;
   out_8701255044286026870[15] = 0.0;
   out_8701255044286026870[16] = 0.0;
   out_8701255044286026870[17] = 0.0;
   out_8701255044286026870[18] = 0.0;
   out_8701255044286026870[19] = 1.0;
   out_8701255044286026870[20] = 0.0;
   out_8701255044286026870[21] = 0.0;
   out_8701255044286026870[22] = 0.0;
   out_8701255044286026870[23] = 0.0;
   out_8701255044286026870[24] = 0.0;
   out_8701255044286026870[25] = 0.0;
   out_8701255044286026870[26] = 0.0;
   out_8701255044286026870[27] = 0.0;
   out_8701255044286026870[28] = 0.0;
   out_8701255044286026870[29] = 0.0;
   out_8701255044286026870[30] = 0.0;
   out_8701255044286026870[31] = 0.0;
   out_8701255044286026870[32] = 0.0;
   out_8701255044286026870[33] = 0.0;
   out_8701255044286026870[34] = 0.0;
   out_8701255044286026870[35] = 0.0;
   out_8701255044286026870[36] = 0.0;
   out_8701255044286026870[37] = 0.0;
   out_8701255044286026870[38] = 1.0;
   out_8701255044286026870[39] = 0.0;
   out_8701255044286026870[40] = 0.0;
   out_8701255044286026870[41] = 0.0;
   out_8701255044286026870[42] = 0.0;
   out_8701255044286026870[43] = 0.0;
   out_8701255044286026870[44] = 0.0;
   out_8701255044286026870[45] = 0.0;
   out_8701255044286026870[46] = 0.0;
   out_8701255044286026870[47] = 0.0;
   out_8701255044286026870[48] = 0.0;
   out_8701255044286026870[49] = 0.0;
   out_8701255044286026870[50] = 0.0;
   out_8701255044286026870[51] = 0.0;
   out_8701255044286026870[52] = 0.0;
   out_8701255044286026870[53] = 0.0;
   out_8701255044286026870[54] = 0.0;
   out_8701255044286026870[55] = 0.0;
   out_8701255044286026870[56] = 0.0;
   out_8701255044286026870[57] = 1.0;
   out_8701255044286026870[58] = 0.0;
   out_8701255044286026870[59] = 0.0;
   out_8701255044286026870[60] = 0.0;
   out_8701255044286026870[61] = 0.0;
   out_8701255044286026870[62] = 0.0;
   out_8701255044286026870[63] = 0.0;
   out_8701255044286026870[64] = 0.0;
   out_8701255044286026870[65] = 0.0;
   out_8701255044286026870[66] = 0.0;
   out_8701255044286026870[67] = 0.0;
   out_8701255044286026870[68] = 0.0;
   out_8701255044286026870[69] = 0.0;
   out_8701255044286026870[70] = 0.0;
   out_8701255044286026870[71] = 0.0;
   out_8701255044286026870[72] = 0.0;
   out_8701255044286026870[73] = 0.0;
   out_8701255044286026870[74] = 0.0;
   out_8701255044286026870[75] = 0.0;
   out_8701255044286026870[76] = 1.0;
   out_8701255044286026870[77] = 0.0;
   out_8701255044286026870[78] = 0.0;
   out_8701255044286026870[79] = 0.0;
   out_8701255044286026870[80] = 0.0;
   out_8701255044286026870[81] = 0.0;
   out_8701255044286026870[82] = 0.0;
   out_8701255044286026870[83] = 0.0;
   out_8701255044286026870[84] = 0.0;
   out_8701255044286026870[85] = 0.0;
   out_8701255044286026870[86] = 0.0;
   out_8701255044286026870[87] = 0.0;
   out_8701255044286026870[88] = 0.0;
   out_8701255044286026870[89] = 0.0;
   out_8701255044286026870[90] = 0.0;
   out_8701255044286026870[91] = 0.0;
   out_8701255044286026870[92] = 0.0;
   out_8701255044286026870[93] = 0.0;
   out_8701255044286026870[94] = 0.0;
   out_8701255044286026870[95] = 1.0;
   out_8701255044286026870[96] = 0.0;
   out_8701255044286026870[97] = 0.0;
   out_8701255044286026870[98] = 0.0;
   out_8701255044286026870[99] = 0.0;
   out_8701255044286026870[100] = 0.0;
   out_8701255044286026870[101] = 0.0;
   out_8701255044286026870[102] = 0.0;
   out_8701255044286026870[103] = 0.0;
   out_8701255044286026870[104] = 0.0;
   out_8701255044286026870[105] = 0.0;
   out_8701255044286026870[106] = 0.0;
   out_8701255044286026870[107] = 0.0;
   out_8701255044286026870[108] = 0.0;
   out_8701255044286026870[109] = 0.0;
   out_8701255044286026870[110] = 0.0;
   out_8701255044286026870[111] = 0.0;
   out_8701255044286026870[112] = 0.0;
   out_8701255044286026870[113] = 0.0;
   out_8701255044286026870[114] = 1.0;
   out_8701255044286026870[115] = 0.0;
   out_8701255044286026870[116] = 0.0;
   out_8701255044286026870[117] = 0.0;
   out_8701255044286026870[118] = 0.0;
   out_8701255044286026870[119] = 0.0;
   out_8701255044286026870[120] = 0.0;
   out_8701255044286026870[121] = 0.0;
   out_8701255044286026870[122] = 0.0;
   out_8701255044286026870[123] = 0.0;
   out_8701255044286026870[124] = 0.0;
   out_8701255044286026870[125] = 0.0;
   out_8701255044286026870[126] = 0.0;
   out_8701255044286026870[127] = 0.0;
   out_8701255044286026870[128] = 0.0;
   out_8701255044286026870[129] = 0.0;
   out_8701255044286026870[130] = 0.0;
   out_8701255044286026870[131] = 0.0;
   out_8701255044286026870[132] = 0.0;
   out_8701255044286026870[133] = 1.0;
   out_8701255044286026870[134] = 0.0;
   out_8701255044286026870[135] = 0.0;
   out_8701255044286026870[136] = 0.0;
   out_8701255044286026870[137] = 0.0;
   out_8701255044286026870[138] = 0.0;
   out_8701255044286026870[139] = 0.0;
   out_8701255044286026870[140] = 0.0;
   out_8701255044286026870[141] = 0.0;
   out_8701255044286026870[142] = 0.0;
   out_8701255044286026870[143] = 0.0;
   out_8701255044286026870[144] = 0.0;
   out_8701255044286026870[145] = 0.0;
   out_8701255044286026870[146] = 0.0;
   out_8701255044286026870[147] = 0.0;
   out_8701255044286026870[148] = 0.0;
   out_8701255044286026870[149] = 0.0;
   out_8701255044286026870[150] = 0.0;
   out_8701255044286026870[151] = 0.0;
   out_8701255044286026870[152] = 1.0;
   out_8701255044286026870[153] = 0.0;
   out_8701255044286026870[154] = 0.0;
   out_8701255044286026870[155] = 0.0;
   out_8701255044286026870[156] = 0.0;
   out_8701255044286026870[157] = 0.0;
   out_8701255044286026870[158] = 0.0;
   out_8701255044286026870[159] = 0.0;
   out_8701255044286026870[160] = 0.0;
   out_8701255044286026870[161] = 0.0;
   out_8701255044286026870[162] = 0.0;
   out_8701255044286026870[163] = 0.0;
   out_8701255044286026870[164] = 0.0;
   out_8701255044286026870[165] = 0.0;
   out_8701255044286026870[166] = 0.0;
   out_8701255044286026870[167] = 0.0;
   out_8701255044286026870[168] = 0.0;
   out_8701255044286026870[169] = 0.0;
   out_8701255044286026870[170] = 0.0;
   out_8701255044286026870[171] = 1.0;
   out_8701255044286026870[172] = 0.0;
   out_8701255044286026870[173] = 0.0;
   out_8701255044286026870[174] = 0.0;
   out_8701255044286026870[175] = 0.0;
   out_8701255044286026870[176] = 0.0;
   out_8701255044286026870[177] = 0.0;
   out_8701255044286026870[178] = 0.0;
   out_8701255044286026870[179] = 0.0;
   out_8701255044286026870[180] = 0.0;
   out_8701255044286026870[181] = 0.0;
   out_8701255044286026870[182] = 0.0;
   out_8701255044286026870[183] = 0.0;
   out_8701255044286026870[184] = 0.0;
   out_8701255044286026870[185] = 0.0;
   out_8701255044286026870[186] = 0.0;
   out_8701255044286026870[187] = 0.0;
   out_8701255044286026870[188] = 0.0;
   out_8701255044286026870[189] = 0.0;
   out_8701255044286026870[190] = 1.0;
   out_8701255044286026870[191] = 0.0;
   out_8701255044286026870[192] = 0.0;
   out_8701255044286026870[193] = 0.0;
   out_8701255044286026870[194] = 0.0;
   out_8701255044286026870[195] = 0.0;
   out_8701255044286026870[196] = 0.0;
   out_8701255044286026870[197] = 0.0;
   out_8701255044286026870[198] = 0.0;
   out_8701255044286026870[199] = 0.0;
   out_8701255044286026870[200] = 0.0;
   out_8701255044286026870[201] = 0.0;
   out_8701255044286026870[202] = 0.0;
   out_8701255044286026870[203] = 0.0;
   out_8701255044286026870[204] = 0.0;
   out_8701255044286026870[205] = 0.0;
   out_8701255044286026870[206] = 0.0;
   out_8701255044286026870[207] = 0.0;
   out_8701255044286026870[208] = 0.0;
   out_8701255044286026870[209] = 1.0;
   out_8701255044286026870[210] = 0.0;
   out_8701255044286026870[211] = 0.0;
   out_8701255044286026870[212] = 0.0;
   out_8701255044286026870[213] = 0.0;
   out_8701255044286026870[214] = 0.0;
   out_8701255044286026870[215] = 0.0;
   out_8701255044286026870[216] = 0.0;
   out_8701255044286026870[217] = 0.0;
   out_8701255044286026870[218] = 0.0;
   out_8701255044286026870[219] = 0.0;
   out_8701255044286026870[220] = 0.0;
   out_8701255044286026870[221] = 0.0;
   out_8701255044286026870[222] = 0.0;
   out_8701255044286026870[223] = 0.0;
   out_8701255044286026870[224] = 0.0;
   out_8701255044286026870[225] = 0.0;
   out_8701255044286026870[226] = 0.0;
   out_8701255044286026870[227] = 0.0;
   out_8701255044286026870[228] = 1.0;
   out_8701255044286026870[229] = 0.0;
   out_8701255044286026870[230] = 0.0;
   out_8701255044286026870[231] = 0.0;
   out_8701255044286026870[232] = 0.0;
   out_8701255044286026870[233] = 0.0;
   out_8701255044286026870[234] = 0.0;
   out_8701255044286026870[235] = 0.0;
   out_8701255044286026870[236] = 0.0;
   out_8701255044286026870[237] = 0.0;
   out_8701255044286026870[238] = 0.0;
   out_8701255044286026870[239] = 0.0;
   out_8701255044286026870[240] = 0.0;
   out_8701255044286026870[241] = 0.0;
   out_8701255044286026870[242] = 0.0;
   out_8701255044286026870[243] = 0.0;
   out_8701255044286026870[244] = 0.0;
   out_8701255044286026870[245] = 0.0;
   out_8701255044286026870[246] = 0.0;
   out_8701255044286026870[247] = 1.0;
   out_8701255044286026870[248] = 0.0;
   out_8701255044286026870[249] = 0.0;
   out_8701255044286026870[250] = 0.0;
   out_8701255044286026870[251] = 0.0;
   out_8701255044286026870[252] = 0.0;
   out_8701255044286026870[253] = 0.0;
   out_8701255044286026870[254] = 0.0;
   out_8701255044286026870[255] = 0.0;
   out_8701255044286026870[256] = 0.0;
   out_8701255044286026870[257] = 0.0;
   out_8701255044286026870[258] = 0.0;
   out_8701255044286026870[259] = 0.0;
   out_8701255044286026870[260] = 0.0;
   out_8701255044286026870[261] = 0.0;
   out_8701255044286026870[262] = 0.0;
   out_8701255044286026870[263] = 0.0;
   out_8701255044286026870[264] = 0.0;
   out_8701255044286026870[265] = 0.0;
   out_8701255044286026870[266] = 1.0;
   out_8701255044286026870[267] = 0.0;
   out_8701255044286026870[268] = 0.0;
   out_8701255044286026870[269] = 0.0;
   out_8701255044286026870[270] = 0.0;
   out_8701255044286026870[271] = 0.0;
   out_8701255044286026870[272] = 0.0;
   out_8701255044286026870[273] = 0.0;
   out_8701255044286026870[274] = 0.0;
   out_8701255044286026870[275] = 0.0;
   out_8701255044286026870[276] = 0.0;
   out_8701255044286026870[277] = 0.0;
   out_8701255044286026870[278] = 0.0;
   out_8701255044286026870[279] = 0.0;
   out_8701255044286026870[280] = 0.0;
   out_8701255044286026870[281] = 0.0;
   out_8701255044286026870[282] = 0.0;
   out_8701255044286026870[283] = 0.0;
   out_8701255044286026870[284] = 0.0;
   out_8701255044286026870[285] = 1.0;
   out_8701255044286026870[286] = 0.0;
   out_8701255044286026870[287] = 0.0;
   out_8701255044286026870[288] = 0.0;
   out_8701255044286026870[289] = 0.0;
   out_8701255044286026870[290] = 0.0;
   out_8701255044286026870[291] = 0.0;
   out_8701255044286026870[292] = 0.0;
   out_8701255044286026870[293] = 0.0;
   out_8701255044286026870[294] = 0.0;
   out_8701255044286026870[295] = 0.0;
   out_8701255044286026870[296] = 0.0;
   out_8701255044286026870[297] = 0.0;
   out_8701255044286026870[298] = 0.0;
   out_8701255044286026870[299] = 0.0;
   out_8701255044286026870[300] = 0.0;
   out_8701255044286026870[301] = 0.0;
   out_8701255044286026870[302] = 0.0;
   out_8701255044286026870[303] = 0.0;
   out_8701255044286026870[304] = 1.0;
   out_8701255044286026870[305] = 0.0;
   out_8701255044286026870[306] = 0.0;
   out_8701255044286026870[307] = 0.0;
   out_8701255044286026870[308] = 0.0;
   out_8701255044286026870[309] = 0.0;
   out_8701255044286026870[310] = 0.0;
   out_8701255044286026870[311] = 0.0;
   out_8701255044286026870[312] = 0.0;
   out_8701255044286026870[313] = 0.0;
   out_8701255044286026870[314] = 0.0;
   out_8701255044286026870[315] = 0.0;
   out_8701255044286026870[316] = 0.0;
   out_8701255044286026870[317] = 0.0;
   out_8701255044286026870[318] = 0.0;
   out_8701255044286026870[319] = 0.0;
   out_8701255044286026870[320] = 0.0;
   out_8701255044286026870[321] = 0.0;
   out_8701255044286026870[322] = 0.0;
   out_8701255044286026870[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_3554971931229877212) {
   out_3554971931229877212[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_3554971931229877212[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_3554971931229877212[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_3554971931229877212[3] = dt*state[12] + state[3];
   out_3554971931229877212[4] = dt*state[13] + state[4];
   out_3554971931229877212[5] = dt*state[14] + state[5];
   out_3554971931229877212[6] = state[6];
   out_3554971931229877212[7] = state[7];
   out_3554971931229877212[8] = state[8];
   out_3554971931229877212[9] = state[9];
   out_3554971931229877212[10] = state[10];
   out_3554971931229877212[11] = state[11];
   out_3554971931229877212[12] = state[12];
   out_3554971931229877212[13] = state[13];
   out_3554971931229877212[14] = state[14];
   out_3554971931229877212[15] = state[15];
   out_3554971931229877212[16] = state[16];
   out_3554971931229877212[17] = state[17];
}
void F_fun(double *state, double dt, double *out_4213718004866334225) {
   out_4213718004866334225[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4213718004866334225[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4213718004866334225[2] = 0;
   out_4213718004866334225[3] = 0;
   out_4213718004866334225[4] = 0;
   out_4213718004866334225[5] = 0;
   out_4213718004866334225[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4213718004866334225[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4213718004866334225[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4213718004866334225[9] = 0;
   out_4213718004866334225[10] = 0;
   out_4213718004866334225[11] = 0;
   out_4213718004866334225[12] = 0;
   out_4213718004866334225[13] = 0;
   out_4213718004866334225[14] = 0;
   out_4213718004866334225[15] = 0;
   out_4213718004866334225[16] = 0;
   out_4213718004866334225[17] = 0;
   out_4213718004866334225[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4213718004866334225[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4213718004866334225[20] = 0;
   out_4213718004866334225[21] = 0;
   out_4213718004866334225[22] = 0;
   out_4213718004866334225[23] = 0;
   out_4213718004866334225[24] = 0;
   out_4213718004866334225[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4213718004866334225[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4213718004866334225[27] = 0;
   out_4213718004866334225[28] = 0;
   out_4213718004866334225[29] = 0;
   out_4213718004866334225[30] = 0;
   out_4213718004866334225[31] = 0;
   out_4213718004866334225[32] = 0;
   out_4213718004866334225[33] = 0;
   out_4213718004866334225[34] = 0;
   out_4213718004866334225[35] = 0;
   out_4213718004866334225[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4213718004866334225[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4213718004866334225[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4213718004866334225[39] = 0;
   out_4213718004866334225[40] = 0;
   out_4213718004866334225[41] = 0;
   out_4213718004866334225[42] = 0;
   out_4213718004866334225[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4213718004866334225[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4213718004866334225[45] = 0;
   out_4213718004866334225[46] = 0;
   out_4213718004866334225[47] = 0;
   out_4213718004866334225[48] = 0;
   out_4213718004866334225[49] = 0;
   out_4213718004866334225[50] = 0;
   out_4213718004866334225[51] = 0;
   out_4213718004866334225[52] = 0;
   out_4213718004866334225[53] = 0;
   out_4213718004866334225[54] = 0;
   out_4213718004866334225[55] = 0;
   out_4213718004866334225[56] = 0;
   out_4213718004866334225[57] = 1;
   out_4213718004866334225[58] = 0;
   out_4213718004866334225[59] = 0;
   out_4213718004866334225[60] = 0;
   out_4213718004866334225[61] = 0;
   out_4213718004866334225[62] = 0;
   out_4213718004866334225[63] = 0;
   out_4213718004866334225[64] = 0;
   out_4213718004866334225[65] = 0;
   out_4213718004866334225[66] = dt;
   out_4213718004866334225[67] = 0;
   out_4213718004866334225[68] = 0;
   out_4213718004866334225[69] = 0;
   out_4213718004866334225[70] = 0;
   out_4213718004866334225[71] = 0;
   out_4213718004866334225[72] = 0;
   out_4213718004866334225[73] = 0;
   out_4213718004866334225[74] = 0;
   out_4213718004866334225[75] = 0;
   out_4213718004866334225[76] = 1;
   out_4213718004866334225[77] = 0;
   out_4213718004866334225[78] = 0;
   out_4213718004866334225[79] = 0;
   out_4213718004866334225[80] = 0;
   out_4213718004866334225[81] = 0;
   out_4213718004866334225[82] = 0;
   out_4213718004866334225[83] = 0;
   out_4213718004866334225[84] = 0;
   out_4213718004866334225[85] = dt;
   out_4213718004866334225[86] = 0;
   out_4213718004866334225[87] = 0;
   out_4213718004866334225[88] = 0;
   out_4213718004866334225[89] = 0;
   out_4213718004866334225[90] = 0;
   out_4213718004866334225[91] = 0;
   out_4213718004866334225[92] = 0;
   out_4213718004866334225[93] = 0;
   out_4213718004866334225[94] = 0;
   out_4213718004866334225[95] = 1;
   out_4213718004866334225[96] = 0;
   out_4213718004866334225[97] = 0;
   out_4213718004866334225[98] = 0;
   out_4213718004866334225[99] = 0;
   out_4213718004866334225[100] = 0;
   out_4213718004866334225[101] = 0;
   out_4213718004866334225[102] = 0;
   out_4213718004866334225[103] = 0;
   out_4213718004866334225[104] = dt;
   out_4213718004866334225[105] = 0;
   out_4213718004866334225[106] = 0;
   out_4213718004866334225[107] = 0;
   out_4213718004866334225[108] = 0;
   out_4213718004866334225[109] = 0;
   out_4213718004866334225[110] = 0;
   out_4213718004866334225[111] = 0;
   out_4213718004866334225[112] = 0;
   out_4213718004866334225[113] = 0;
   out_4213718004866334225[114] = 1;
   out_4213718004866334225[115] = 0;
   out_4213718004866334225[116] = 0;
   out_4213718004866334225[117] = 0;
   out_4213718004866334225[118] = 0;
   out_4213718004866334225[119] = 0;
   out_4213718004866334225[120] = 0;
   out_4213718004866334225[121] = 0;
   out_4213718004866334225[122] = 0;
   out_4213718004866334225[123] = 0;
   out_4213718004866334225[124] = 0;
   out_4213718004866334225[125] = 0;
   out_4213718004866334225[126] = 0;
   out_4213718004866334225[127] = 0;
   out_4213718004866334225[128] = 0;
   out_4213718004866334225[129] = 0;
   out_4213718004866334225[130] = 0;
   out_4213718004866334225[131] = 0;
   out_4213718004866334225[132] = 0;
   out_4213718004866334225[133] = 1;
   out_4213718004866334225[134] = 0;
   out_4213718004866334225[135] = 0;
   out_4213718004866334225[136] = 0;
   out_4213718004866334225[137] = 0;
   out_4213718004866334225[138] = 0;
   out_4213718004866334225[139] = 0;
   out_4213718004866334225[140] = 0;
   out_4213718004866334225[141] = 0;
   out_4213718004866334225[142] = 0;
   out_4213718004866334225[143] = 0;
   out_4213718004866334225[144] = 0;
   out_4213718004866334225[145] = 0;
   out_4213718004866334225[146] = 0;
   out_4213718004866334225[147] = 0;
   out_4213718004866334225[148] = 0;
   out_4213718004866334225[149] = 0;
   out_4213718004866334225[150] = 0;
   out_4213718004866334225[151] = 0;
   out_4213718004866334225[152] = 1;
   out_4213718004866334225[153] = 0;
   out_4213718004866334225[154] = 0;
   out_4213718004866334225[155] = 0;
   out_4213718004866334225[156] = 0;
   out_4213718004866334225[157] = 0;
   out_4213718004866334225[158] = 0;
   out_4213718004866334225[159] = 0;
   out_4213718004866334225[160] = 0;
   out_4213718004866334225[161] = 0;
   out_4213718004866334225[162] = 0;
   out_4213718004866334225[163] = 0;
   out_4213718004866334225[164] = 0;
   out_4213718004866334225[165] = 0;
   out_4213718004866334225[166] = 0;
   out_4213718004866334225[167] = 0;
   out_4213718004866334225[168] = 0;
   out_4213718004866334225[169] = 0;
   out_4213718004866334225[170] = 0;
   out_4213718004866334225[171] = 1;
   out_4213718004866334225[172] = 0;
   out_4213718004866334225[173] = 0;
   out_4213718004866334225[174] = 0;
   out_4213718004866334225[175] = 0;
   out_4213718004866334225[176] = 0;
   out_4213718004866334225[177] = 0;
   out_4213718004866334225[178] = 0;
   out_4213718004866334225[179] = 0;
   out_4213718004866334225[180] = 0;
   out_4213718004866334225[181] = 0;
   out_4213718004866334225[182] = 0;
   out_4213718004866334225[183] = 0;
   out_4213718004866334225[184] = 0;
   out_4213718004866334225[185] = 0;
   out_4213718004866334225[186] = 0;
   out_4213718004866334225[187] = 0;
   out_4213718004866334225[188] = 0;
   out_4213718004866334225[189] = 0;
   out_4213718004866334225[190] = 1;
   out_4213718004866334225[191] = 0;
   out_4213718004866334225[192] = 0;
   out_4213718004866334225[193] = 0;
   out_4213718004866334225[194] = 0;
   out_4213718004866334225[195] = 0;
   out_4213718004866334225[196] = 0;
   out_4213718004866334225[197] = 0;
   out_4213718004866334225[198] = 0;
   out_4213718004866334225[199] = 0;
   out_4213718004866334225[200] = 0;
   out_4213718004866334225[201] = 0;
   out_4213718004866334225[202] = 0;
   out_4213718004866334225[203] = 0;
   out_4213718004866334225[204] = 0;
   out_4213718004866334225[205] = 0;
   out_4213718004866334225[206] = 0;
   out_4213718004866334225[207] = 0;
   out_4213718004866334225[208] = 0;
   out_4213718004866334225[209] = 1;
   out_4213718004866334225[210] = 0;
   out_4213718004866334225[211] = 0;
   out_4213718004866334225[212] = 0;
   out_4213718004866334225[213] = 0;
   out_4213718004866334225[214] = 0;
   out_4213718004866334225[215] = 0;
   out_4213718004866334225[216] = 0;
   out_4213718004866334225[217] = 0;
   out_4213718004866334225[218] = 0;
   out_4213718004866334225[219] = 0;
   out_4213718004866334225[220] = 0;
   out_4213718004866334225[221] = 0;
   out_4213718004866334225[222] = 0;
   out_4213718004866334225[223] = 0;
   out_4213718004866334225[224] = 0;
   out_4213718004866334225[225] = 0;
   out_4213718004866334225[226] = 0;
   out_4213718004866334225[227] = 0;
   out_4213718004866334225[228] = 1;
   out_4213718004866334225[229] = 0;
   out_4213718004866334225[230] = 0;
   out_4213718004866334225[231] = 0;
   out_4213718004866334225[232] = 0;
   out_4213718004866334225[233] = 0;
   out_4213718004866334225[234] = 0;
   out_4213718004866334225[235] = 0;
   out_4213718004866334225[236] = 0;
   out_4213718004866334225[237] = 0;
   out_4213718004866334225[238] = 0;
   out_4213718004866334225[239] = 0;
   out_4213718004866334225[240] = 0;
   out_4213718004866334225[241] = 0;
   out_4213718004866334225[242] = 0;
   out_4213718004866334225[243] = 0;
   out_4213718004866334225[244] = 0;
   out_4213718004866334225[245] = 0;
   out_4213718004866334225[246] = 0;
   out_4213718004866334225[247] = 1;
   out_4213718004866334225[248] = 0;
   out_4213718004866334225[249] = 0;
   out_4213718004866334225[250] = 0;
   out_4213718004866334225[251] = 0;
   out_4213718004866334225[252] = 0;
   out_4213718004866334225[253] = 0;
   out_4213718004866334225[254] = 0;
   out_4213718004866334225[255] = 0;
   out_4213718004866334225[256] = 0;
   out_4213718004866334225[257] = 0;
   out_4213718004866334225[258] = 0;
   out_4213718004866334225[259] = 0;
   out_4213718004866334225[260] = 0;
   out_4213718004866334225[261] = 0;
   out_4213718004866334225[262] = 0;
   out_4213718004866334225[263] = 0;
   out_4213718004866334225[264] = 0;
   out_4213718004866334225[265] = 0;
   out_4213718004866334225[266] = 1;
   out_4213718004866334225[267] = 0;
   out_4213718004866334225[268] = 0;
   out_4213718004866334225[269] = 0;
   out_4213718004866334225[270] = 0;
   out_4213718004866334225[271] = 0;
   out_4213718004866334225[272] = 0;
   out_4213718004866334225[273] = 0;
   out_4213718004866334225[274] = 0;
   out_4213718004866334225[275] = 0;
   out_4213718004866334225[276] = 0;
   out_4213718004866334225[277] = 0;
   out_4213718004866334225[278] = 0;
   out_4213718004866334225[279] = 0;
   out_4213718004866334225[280] = 0;
   out_4213718004866334225[281] = 0;
   out_4213718004866334225[282] = 0;
   out_4213718004866334225[283] = 0;
   out_4213718004866334225[284] = 0;
   out_4213718004866334225[285] = 1;
   out_4213718004866334225[286] = 0;
   out_4213718004866334225[287] = 0;
   out_4213718004866334225[288] = 0;
   out_4213718004866334225[289] = 0;
   out_4213718004866334225[290] = 0;
   out_4213718004866334225[291] = 0;
   out_4213718004866334225[292] = 0;
   out_4213718004866334225[293] = 0;
   out_4213718004866334225[294] = 0;
   out_4213718004866334225[295] = 0;
   out_4213718004866334225[296] = 0;
   out_4213718004866334225[297] = 0;
   out_4213718004866334225[298] = 0;
   out_4213718004866334225[299] = 0;
   out_4213718004866334225[300] = 0;
   out_4213718004866334225[301] = 0;
   out_4213718004866334225[302] = 0;
   out_4213718004866334225[303] = 0;
   out_4213718004866334225[304] = 1;
   out_4213718004866334225[305] = 0;
   out_4213718004866334225[306] = 0;
   out_4213718004866334225[307] = 0;
   out_4213718004866334225[308] = 0;
   out_4213718004866334225[309] = 0;
   out_4213718004866334225[310] = 0;
   out_4213718004866334225[311] = 0;
   out_4213718004866334225[312] = 0;
   out_4213718004866334225[313] = 0;
   out_4213718004866334225[314] = 0;
   out_4213718004866334225[315] = 0;
   out_4213718004866334225[316] = 0;
   out_4213718004866334225[317] = 0;
   out_4213718004866334225[318] = 0;
   out_4213718004866334225[319] = 0;
   out_4213718004866334225[320] = 0;
   out_4213718004866334225[321] = 0;
   out_4213718004866334225[322] = 0;
   out_4213718004866334225[323] = 1;
}
void h_4(double *state, double *unused, double *out_8042373158170206990) {
   out_8042373158170206990[0] = state[6] + state[9];
   out_8042373158170206990[1] = state[7] + state[10];
   out_8042373158170206990[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_7947094042231314263) {
   out_7947094042231314263[0] = 0;
   out_7947094042231314263[1] = 0;
   out_7947094042231314263[2] = 0;
   out_7947094042231314263[3] = 0;
   out_7947094042231314263[4] = 0;
   out_7947094042231314263[5] = 0;
   out_7947094042231314263[6] = 1;
   out_7947094042231314263[7] = 0;
   out_7947094042231314263[8] = 0;
   out_7947094042231314263[9] = 1;
   out_7947094042231314263[10] = 0;
   out_7947094042231314263[11] = 0;
   out_7947094042231314263[12] = 0;
   out_7947094042231314263[13] = 0;
   out_7947094042231314263[14] = 0;
   out_7947094042231314263[15] = 0;
   out_7947094042231314263[16] = 0;
   out_7947094042231314263[17] = 0;
   out_7947094042231314263[18] = 0;
   out_7947094042231314263[19] = 0;
   out_7947094042231314263[20] = 0;
   out_7947094042231314263[21] = 0;
   out_7947094042231314263[22] = 0;
   out_7947094042231314263[23] = 0;
   out_7947094042231314263[24] = 0;
   out_7947094042231314263[25] = 1;
   out_7947094042231314263[26] = 0;
   out_7947094042231314263[27] = 0;
   out_7947094042231314263[28] = 1;
   out_7947094042231314263[29] = 0;
   out_7947094042231314263[30] = 0;
   out_7947094042231314263[31] = 0;
   out_7947094042231314263[32] = 0;
   out_7947094042231314263[33] = 0;
   out_7947094042231314263[34] = 0;
   out_7947094042231314263[35] = 0;
   out_7947094042231314263[36] = 0;
   out_7947094042231314263[37] = 0;
   out_7947094042231314263[38] = 0;
   out_7947094042231314263[39] = 0;
   out_7947094042231314263[40] = 0;
   out_7947094042231314263[41] = 0;
   out_7947094042231314263[42] = 0;
   out_7947094042231314263[43] = 0;
   out_7947094042231314263[44] = 1;
   out_7947094042231314263[45] = 0;
   out_7947094042231314263[46] = 0;
   out_7947094042231314263[47] = 1;
   out_7947094042231314263[48] = 0;
   out_7947094042231314263[49] = 0;
   out_7947094042231314263[50] = 0;
   out_7947094042231314263[51] = 0;
   out_7947094042231314263[52] = 0;
   out_7947094042231314263[53] = 0;
}
void h_10(double *state, double *unused, double *out_6693017902685099821) {
   out_6693017902685099821[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_6693017902685099821[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_6693017902685099821[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_2240931588784816648) {
   out_2240931588784816648[0] = 0;
   out_2240931588784816648[1] = 9.8100000000000005*cos(state[1]);
   out_2240931588784816648[2] = 0;
   out_2240931588784816648[3] = 0;
   out_2240931588784816648[4] = -state[8];
   out_2240931588784816648[5] = state[7];
   out_2240931588784816648[6] = 0;
   out_2240931588784816648[7] = state[5];
   out_2240931588784816648[8] = -state[4];
   out_2240931588784816648[9] = 0;
   out_2240931588784816648[10] = 0;
   out_2240931588784816648[11] = 0;
   out_2240931588784816648[12] = 1;
   out_2240931588784816648[13] = 0;
   out_2240931588784816648[14] = 0;
   out_2240931588784816648[15] = 1;
   out_2240931588784816648[16] = 0;
   out_2240931588784816648[17] = 0;
   out_2240931588784816648[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_2240931588784816648[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_2240931588784816648[20] = 0;
   out_2240931588784816648[21] = state[8];
   out_2240931588784816648[22] = 0;
   out_2240931588784816648[23] = -state[6];
   out_2240931588784816648[24] = -state[5];
   out_2240931588784816648[25] = 0;
   out_2240931588784816648[26] = state[3];
   out_2240931588784816648[27] = 0;
   out_2240931588784816648[28] = 0;
   out_2240931588784816648[29] = 0;
   out_2240931588784816648[30] = 0;
   out_2240931588784816648[31] = 1;
   out_2240931588784816648[32] = 0;
   out_2240931588784816648[33] = 0;
   out_2240931588784816648[34] = 1;
   out_2240931588784816648[35] = 0;
   out_2240931588784816648[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_2240931588784816648[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_2240931588784816648[38] = 0;
   out_2240931588784816648[39] = -state[7];
   out_2240931588784816648[40] = state[6];
   out_2240931588784816648[41] = 0;
   out_2240931588784816648[42] = state[4];
   out_2240931588784816648[43] = -state[3];
   out_2240931588784816648[44] = 0;
   out_2240931588784816648[45] = 0;
   out_2240931588784816648[46] = 0;
   out_2240931588784816648[47] = 0;
   out_2240931588784816648[48] = 0;
   out_2240931588784816648[49] = 0;
   out_2240931588784816648[50] = 1;
   out_2240931588784816648[51] = 0;
   out_2240931588784816648[52] = 0;
   out_2240931588784816648[53] = 1;
}
void h_13(double *state, double *unused, double *out_4695832005485386494) {
   out_4695832005485386494[0] = state[3];
   out_4695832005485386494[1] = state[4];
   out_4695832005485386494[2] = state[5];
}
void H_13(double *state, double *unused, double *out_4734820216898981462) {
   out_4734820216898981462[0] = 0;
   out_4734820216898981462[1] = 0;
   out_4734820216898981462[2] = 0;
   out_4734820216898981462[3] = 1;
   out_4734820216898981462[4] = 0;
   out_4734820216898981462[5] = 0;
   out_4734820216898981462[6] = 0;
   out_4734820216898981462[7] = 0;
   out_4734820216898981462[8] = 0;
   out_4734820216898981462[9] = 0;
   out_4734820216898981462[10] = 0;
   out_4734820216898981462[11] = 0;
   out_4734820216898981462[12] = 0;
   out_4734820216898981462[13] = 0;
   out_4734820216898981462[14] = 0;
   out_4734820216898981462[15] = 0;
   out_4734820216898981462[16] = 0;
   out_4734820216898981462[17] = 0;
   out_4734820216898981462[18] = 0;
   out_4734820216898981462[19] = 0;
   out_4734820216898981462[20] = 0;
   out_4734820216898981462[21] = 0;
   out_4734820216898981462[22] = 1;
   out_4734820216898981462[23] = 0;
   out_4734820216898981462[24] = 0;
   out_4734820216898981462[25] = 0;
   out_4734820216898981462[26] = 0;
   out_4734820216898981462[27] = 0;
   out_4734820216898981462[28] = 0;
   out_4734820216898981462[29] = 0;
   out_4734820216898981462[30] = 0;
   out_4734820216898981462[31] = 0;
   out_4734820216898981462[32] = 0;
   out_4734820216898981462[33] = 0;
   out_4734820216898981462[34] = 0;
   out_4734820216898981462[35] = 0;
   out_4734820216898981462[36] = 0;
   out_4734820216898981462[37] = 0;
   out_4734820216898981462[38] = 0;
   out_4734820216898981462[39] = 0;
   out_4734820216898981462[40] = 0;
   out_4734820216898981462[41] = 1;
   out_4734820216898981462[42] = 0;
   out_4734820216898981462[43] = 0;
   out_4734820216898981462[44] = 0;
   out_4734820216898981462[45] = 0;
   out_4734820216898981462[46] = 0;
   out_4734820216898981462[47] = 0;
   out_4734820216898981462[48] = 0;
   out_4734820216898981462[49] = 0;
   out_4734820216898981462[50] = 0;
   out_4734820216898981462[51] = 0;
   out_4734820216898981462[52] = 0;
   out_4734820216898981462[53] = 0;
}
void h_14(double *state, double *unused, double *out_5793211794452819883) {
   out_5793211794452819883[0] = state[6];
   out_5793211794452819883[1] = state[7];
   out_5793211794452819883[2] = state[8];
}
void H_14(double *state, double *unused, double *out_3983853185891829734) {
   out_3983853185891829734[0] = 0;
   out_3983853185891829734[1] = 0;
   out_3983853185891829734[2] = 0;
   out_3983853185891829734[3] = 0;
   out_3983853185891829734[4] = 0;
   out_3983853185891829734[5] = 0;
   out_3983853185891829734[6] = 1;
   out_3983853185891829734[7] = 0;
   out_3983853185891829734[8] = 0;
   out_3983853185891829734[9] = 0;
   out_3983853185891829734[10] = 0;
   out_3983853185891829734[11] = 0;
   out_3983853185891829734[12] = 0;
   out_3983853185891829734[13] = 0;
   out_3983853185891829734[14] = 0;
   out_3983853185891829734[15] = 0;
   out_3983853185891829734[16] = 0;
   out_3983853185891829734[17] = 0;
   out_3983853185891829734[18] = 0;
   out_3983853185891829734[19] = 0;
   out_3983853185891829734[20] = 0;
   out_3983853185891829734[21] = 0;
   out_3983853185891829734[22] = 0;
   out_3983853185891829734[23] = 0;
   out_3983853185891829734[24] = 0;
   out_3983853185891829734[25] = 1;
   out_3983853185891829734[26] = 0;
   out_3983853185891829734[27] = 0;
   out_3983853185891829734[28] = 0;
   out_3983853185891829734[29] = 0;
   out_3983853185891829734[30] = 0;
   out_3983853185891829734[31] = 0;
   out_3983853185891829734[32] = 0;
   out_3983853185891829734[33] = 0;
   out_3983853185891829734[34] = 0;
   out_3983853185891829734[35] = 0;
   out_3983853185891829734[36] = 0;
   out_3983853185891829734[37] = 0;
   out_3983853185891829734[38] = 0;
   out_3983853185891829734[39] = 0;
   out_3983853185891829734[40] = 0;
   out_3983853185891829734[41] = 0;
   out_3983853185891829734[42] = 0;
   out_3983853185891829734[43] = 0;
   out_3983853185891829734[44] = 1;
   out_3983853185891829734[45] = 0;
   out_3983853185891829734[46] = 0;
   out_3983853185891829734[47] = 0;
   out_3983853185891829734[48] = 0;
   out_3983853185891829734[49] = 0;
   out_3983853185891829734[50] = 0;
   out_3983853185891829734[51] = 0;
   out_3983853185891829734[52] = 0;
   out_3983853185891829734[53] = 0;
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
void pose_err_fun(double *nom_x, double *delta_x, double *out_3683974983863530851) {
  err_fun(nom_x, delta_x, out_3683974983863530851);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_7161705307985060718) {
  inv_err_fun(nom_x, true_x, out_7161705307985060718);
}
void pose_H_mod_fun(double *state, double *out_8701255044286026870) {
  H_mod_fun(state, out_8701255044286026870);
}
void pose_f_fun(double *state, double dt, double *out_3554971931229877212) {
  f_fun(state,  dt, out_3554971931229877212);
}
void pose_F_fun(double *state, double dt, double *out_4213718004866334225) {
  F_fun(state,  dt, out_4213718004866334225);
}
void pose_h_4(double *state, double *unused, double *out_8042373158170206990) {
  h_4(state, unused, out_8042373158170206990);
}
void pose_H_4(double *state, double *unused, double *out_7947094042231314263) {
  H_4(state, unused, out_7947094042231314263);
}
void pose_h_10(double *state, double *unused, double *out_6693017902685099821) {
  h_10(state, unused, out_6693017902685099821);
}
void pose_H_10(double *state, double *unused, double *out_2240931588784816648) {
  H_10(state, unused, out_2240931588784816648);
}
void pose_h_13(double *state, double *unused, double *out_4695832005485386494) {
  h_13(state, unused, out_4695832005485386494);
}
void pose_H_13(double *state, double *unused, double *out_4734820216898981462) {
  H_13(state, unused, out_4734820216898981462);
}
void pose_h_14(double *state, double *unused, double *out_5793211794452819883) {
  h_14(state, unused, out_5793211794452819883);
}
void pose_H_14(double *state, double *unused, double *out_3983853185891829734) {
  H_14(state, unused, out_3983853185891829734);
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
