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
void err_fun(double *nom_x, double *delta_x, double *out_7911616955151800495) {
   out_7911616955151800495[0] = delta_x[0] + nom_x[0];
   out_7911616955151800495[1] = delta_x[1] + nom_x[1];
   out_7911616955151800495[2] = delta_x[2] + nom_x[2];
   out_7911616955151800495[3] = delta_x[3] + nom_x[3];
   out_7911616955151800495[4] = delta_x[4] + nom_x[4];
   out_7911616955151800495[5] = delta_x[5] + nom_x[5];
   out_7911616955151800495[6] = delta_x[6] + nom_x[6];
   out_7911616955151800495[7] = delta_x[7] + nom_x[7];
   out_7911616955151800495[8] = delta_x[8] + nom_x[8];
   out_7911616955151800495[9] = delta_x[9] + nom_x[9];
   out_7911616955151800495[10] = delta_x[10] + nom_x[10];
   out_7911616955151800495[11] = delta_x[11] + nom_x[11];
   out_7911616955151800495[12] = delta_x[12] + nom_x[12];
   out_7911616955151800495[13] = delta_x[13] + nom_x[13];
   out_7911616955151800495[14] = delta_x[14] + nom_x[14];
   out_7911616955151800495[15] = delta_x[15] + nom_x[15];
   out_7911616955151800495[16] = delta_x[16] + nom_x[16];
   out_7911616955151800495[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_7584171002491943517) {
   out_7584171002491943517[0] = -nom_x[0] + true_x[0];
   out_7584171002491943517[1] = -nom_x[1] + true_x[1];
   out_7584171002491943517[2] = -nom_x[2] + true_x[2];
   out_7584171002491943517[3] = -nom_x[3] + true_x[3];
   out_7584171002491943517[4] = -nom_x[4] + true_x[4];
   out_7584171002491943517[5] = -nom_x[5] + true_x[5];
   out_7584171002491943517[6] = -nom_x[6] + true_x[6];
   out_7584171002491943517[7] = -nom_x[7] + true_x[7];
   out_7584171002491943517[8] = -nom_x[8] + true_x[8];
   out_7584171002491943517[9] = -nom_x[9] + true_x[9];
   out_7584171002491943517[10] = -nom_x[10] + true_x[10];
   out_7584171002491943517[11] = -nom_x[11] + true_x[11];
   out_7584171002491943517[12] = -nom_x[12] + true_x[12];
   out_7584171002491943517[13] = -nom_x[13] + true_x[13];
   out_7584171002491943517[14] = -nom_x[14] + true_x[14];
   out_7584171002491943517[15] = -nom_x[15] + true_x[15];
   out_7584171002491943517[16] = -nom_x[16] + true_x[16];
   out_7584171002491943517[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_8208145951121679600) {
   out_8208145951121679600[0] = 1.0;
   out_8208145951121679600[1] = 0.0;
   out_8208145951121679600[2] = 0.0;
   out_8208145951121679600[3] = 0.0;
   out_8208145951121679600[4] = 0.0;
   out_8208145951121679600[5] = 0.0;
   out_8208145951121679600[6] = 0.0;
   out_8208145951121679600[7] = 0.0;
   out_8208145951121679600[8] = 0.0;
   out_8208145951121679600[9] = 0.0;
   out_8208145951121679600[10] = 0.0;
   out_8208145951121679600[11] = 0.0;
   out_8208145951121679600[12] = 0.0;
   out_8208145951121679600[13] = 0.0;
   out_8208145951121679600[14] = 0.0;
   out_8208145951121679600[15] = 0.0;
   out_8208145951121679600[16] = 0.0;
   out_8208145951121679600[17] = 0.0;
   out_8208145951121679600[18] = 0.0;
   out_8208145951121679600[19] = 1.0;
   out_8208145951121679600[20] = 0.0;
   out_8208145951121679600[21] = 0.0;
   out_8208145951121679600[22] = 0.0;
   out_8208145951121679600[23] = 0.0;
   out_8208145951121679600[24] = 0.0;
   out_8208145951121679600[25] = 0.0;
   out_8208145951121679600[26] = 0.0;
   out_8208145951121679600[27] = 0.0;
   out_8208145951121679600[28] = 0.0;
   out_8208145951121679600[29] = 0.0;
   out_8208145951121679600[30] = 0.0;
   out_8208145951121679600[31] = 0.0;
   out_8208145951121679600[32] = 0.0;
   out_8208145951121679600[33] = 0.0;
   out_8208145951121679600[34] = 0.0;
   out_8208145951121679600[35] = 0.0;
   out_8208145951121679600[36] = 0.0;
   out_8208145951121679600[37] = 0.0;
   out_8208145951121679600[38] = 1.0;
   out_8208145951121679600[39] = 0.0;
   out_8208145951121679600[40] = 0.0;
   out_8208145951121679600[41] = 0.0;
   out_8208145951121679600[42] = 0.0;
   out_8208145951121679600[43] = 0.0;
   out_8208145951121679600[44] = 0.0;
   out_8208145951121679600[45] = 0.0;
   out_8208145951121679600[46] = 0.0;
   out_8208145951121679600[47] = 0.0;
   out_8208145951121679600[48] = 0.0;
   out_8208145951121679600[49] = 0.0;
   out_8208145951121679600[50] = 0.0;
   out_8208145951121679600[51] = 0.0;
   out_8208145951121679600[52] = 0.0;
   out_8208145951121679600[53] = 0.0;
   out_8208145951121679600[54] = 0.0;
   out_8208145951121679600[55] = 0.0;
   out_8208145951121679600[56] = 0.0;
   out_8208145951121679600[57] = 1.0;
   out_8208145951121679600[58] = 0.0;
   out_8208145951121679600[59] = 0.0;
   out_8208145951121679600[60] = 0.0;
   out_8208145951121679600[61] = 0.0;
   out_8208145951121679600[62] = 0.0;
   out_8208145951121679600[63] = 0.0;
   out_8208145951121679600[64] = 0.0;
   out_8208145951121679600[65] = 0.0;
   out_8208145951121679600[66] = 0.0;
   out_8208145951121679600[67] = 0.0;
   out_8208145951121679600[68] = 0.0;
   out_8208145951121679600[69] = 0.0;
   out_8208145951121679600[70] = 0.0;
   out_8208145951121679600[71] = 0.0;
   out_8208145951121679600[72] = 0.0;
   out_8208145951121679600[73] = 0.0;
   out_8208145951121679600[74] = 0.0;
   out_8208145951121679600[75] = 0.0;
   out_8208145951121679600[76] = 1.0;
   out_8208145951121679600[77] = 0.0;
   out_8208145951121679600[78] = 0.0;
   out_8208145951121679600[79] = 0.0;
   out_8208145951121679600[80] = 0.0;
   out_8208145951121679600[81] = 0.0;
   out_8208145951121679600[82] = 0.0;
   out_8208145951121679600[83] = 0.0;
   out_8208145951121679600[84] = 0.0;
   out_8208145951121679600[85] = 0.0;
   out_8208145951121679600[86] = 0.0;
   out_8208145951121679600[87] = 0.0;
   out_8208145951121679600[88] = 0.0;
   out_8208145951121679600[89] = 0.0;
   out_8208145951121679600[90] = 0.0;
   out_8208145951121679600[91] = 0.0;
   out_8208145951121679600[92] = 0.0;
   out_8208145951121679600[93] = 0.0;
   out_8208145951121679600[94] = 0.0;
   out_8208145951121679600[95] = 1.0;
   out_8208145951121679600[96] = 0.0;
   out_8208145951121679600[97] = 0.0;
   out_8208145951121679600[98] = 0.0;
   out_8208145951121679600[99] = 0.0;
   out_8208145951121679600[100] = 0.0;
   out_8208145951121679600[101] = 0.0;
   out_8208145951121679600[102] = 0.0;
   out_8208145951121679600[103] = 0.0;
   out_8208145951121679600[104] = 0.0;
   out_8208145951121679600[105] = 0.0;
   out_8208145951121679600[106] = 0.0;
   out_8208145951121679600[107] = 0.0;
   out_8208145951121679600[108] = 0.0;
   out_8208145951121679600[109] = 0.0;
   out_8208145951121679600[110] = 0.0;
   out_8208145951121679600[111] = 0.0;
   out_8208145951121679600[112] = 0.0;
   out_8208145951121679600[113] = 0.0;
   out_8208145951121679600[114] = 1.0;
   out_8208145951121679600[115] = 0.0;
   out_8208145951121679600[116] = 0.0;
   out_8208145951121679600[117] = 0.0;
   out_8208145951121679600[118] = 0.0;
   out_8208145951121679600[119] = 0.0;
   out_8208145951121679600[120] = 0.0;
   out_8208145951121679600[121] = 0.0;
   out_8208145951121679600[122] = 0.0;
   out_8208145951121679600[123] = 0.0;
   out_8208145951121679600[124] = 0.0;
   out_8208145951121679600[125] = 0.0;
   out_8208145951121679600[126] = 0.0;
   out_8208145951121679600[127] = 0.0;
   out_8208145951121679600[128] = 0.0;
   out_8208145951121679600[129] = 0.0;
   out_8208145951121679600[130] = 0.0;
   out_8208145951121679600[131] = 0.0;
   out_8208145951121679600[132] = 0.0;
   out_8208145951121679600[133] = 1.0;
   out_8208145951121679600[134] = 0.0;
   out_8208145951121679600[135] = 0.0;
   out_8208145951121679600[136] = 0.0;
   out_8208145951121679600[137] = 0.0;
   out_8208145951121679600[138] = 0.0;
   out_8208145951121679600[139] = 0.0;
   out_8208145951121679600[140] = 0.0;
   out_8208145951121679600[141] = 0.0;
   out_8208145951121679600[142] = 0.0;
   out_8208145951121679600[143] = 0.0;
   out_8208145951121679600[144] = 0.0;
   out_8208145951121679600[145] = 0.0;
   out_8208145951121679600[146] = 0.0;
   out_8208145951121679600[147] = 0.0;
   out_8208145951121679600[148] = 0.0;
   out_8208145951121679600[149] = 0.0;
   out_8208145951121679600[150] = 0.0;
   out_8208145951121679600[151] = 0.0;
   out_8208145951121679600[152] = 1.0;
   out_8208145951121679600[153] = 0.0;
   out_8208145951121679600[154] = 0.0;
   out_8208145951121679600[155] = 0.0;
   out_8208145951121679600[156] = 0.0;
   out_8208145951121679600[157] = 0.0;
   out_8208145951121679600[158] = 0.0;
   out_8208145951121679600[159] = 0.0;
   out_8208145951121679600[160] = 0.0;
   out_8208145951121679600[161] = 0.0;
   out_8208145951121679600[162] = 0.0;
   out_8208145951121679600[163] = 0.0;
   out_8208145951121679600[164] = 0.0;
   out_8208145951121679600[165] = 0.0;
   out_8208145951121679600[166] = 0.0;
   out_8208145951121679600[167] = 0.0;
   out_8208145951121679600[168] = 0.0;
   out_8208145951121679600[169] = 0.0;
   out_8208145951121679600[170] = 0.0;
   out_8208145951121679600[171] = 1.0;
   out_8208145951121679600[172] = 0.0;
   out_8208145951121679600[173] = 0.0;
   out_8208145951121679600[174] = 0.0;
   out_8208145951121679600[175] = 0.0;
   out_8208145951121679600[176] = 0.0;
   out_8208145951121679600[177] = 0.0;
   out_8208145951121679600[178] = 0.0;
   out_8208145951121679600[179] = 0.0;
   out_8208145951121679600[180] = 0.0;
   out_8208145951121679600[181] = 0.0;
   out_8208145951121679600[182] = 0.0;
   out_8208145951121679600[183] = 0.0;
   out_8208145951121679600[184] = 0.0;
   out_8208145951121679600[185] = 0.0;
   out_8208145951121679600[186] = 0.0;
   out_8208145951121679600[187] = 0.0;
   out_8208145951121679600[188] = 0.0;
   out_8208145951121679600[189] = 0.0;
   out_8208145951121679600[190] = 1.0;
   out_8208145951121679600[191] = 0.0;
   out_8208145951121679600[192] = 0.0;
   out_8208145951121679600[193] = 0.0;
   out_8208145951121679600[194] = 0.0;
   out_8208145951121679600[195] = 0.0;
   out_8208145951121679600[196] = 0.0;
   out_8208145951121679600[197] = 0.0;
   out_8208145951121679600[198] = 0.0;
   out_8208145951121679600[199] = 0.0;
   out_8208145951121679600[200] = 0.0;
   out_8208145951121679600[201] = 0.0;
   out_8208145951121679600[202] = 0.0;
   out_8208145951121679600[203] = 0.0;
   out_8208145951121679600[204] = 0.0;
   out_8208145951121679600[205] = 0.0;
   out_8208145951121679600[206] = 0.0;
   out_8208145951121679600[207] = 0.0;
   out_8208145951121679600[208] = 0.0;
   out_8208145951121679600[209] = 1.0;
   out_8208145951121679600[210] = 0.0;
   out_8208145951121679600[211] = 0.0;
   out_8208145951121679600[212] = 0.0;
   out_8208145951121679600[213] = 0.0;
   out_8208145951121679600[214] = 0.0;
   out_8208145951121679600[215] = 0.0;
   out_8208145951121679600[216] = 0.0;
   out_8208145951121679600[217] = 0.0;
   out_8208145951121679600[218] = 0.0;
   out_8208145951121679600[219] = 0.0;
   out_8208145951121679600[220] = 0.0;
   out_8208145951121679600[221] = 0.0;
   out_8208145951121679600[222] = 0.0;
   out_8208145951121679600[223] = 0.0;
   out_8208145951121679600[224] = 0.0;
   out_8208145951121679600[225] = 0.0;
   out_8208145951121679600[226] = 0.0;
   out_8208145951121679600[227] = 0.0;
   out_8208145951121679600[228] = 1.0;
   out_8208145951121679600[229] = 0.0;
   out_8208145951121679600[230] = 0.0;
   out_8208145951121679600[231] = 0.0;
   out_8208145951121679600[232] = 0.0;
   out_8208145951121679600[233] = 0.0;
   out_8208145951121679600[234] = 0.0;
   out_8208145951121679600[235] = 0.0;
   out_8208145951121679600[236] = 0.0;
   out_8208145951121679600[237] = 0.0;
   out_8208145951121679600[238] = 0.0;
   out_8208145951121679600[239] = 0.0;
   out_8208145951121679600[240] = 0.0;
   out_8208145951121679600[241] = 0.0;
   out_8208145951121679600[242] = 0.0;
   out_8208145951121679600[243] = 0.0;
   out_8208145951121679600[244] = 0.0;
   out_8208145951121679600[245] = 0.0;
   out_8208145951121679600[246] = 0.0;
   out_8208145951121679600[247] = 1.0;
   out_8208145951121679600[248] = 0.0;
   out_8208145951121679600[249] = 0.0;
   out_8208145951121679600[250] = 0.0;
   out_8208145951121679600[251] = 0.0;
   out_8208145951121679600[252] = 0.0;
   out_8208145951121679600[253] = 0.0;
   out_8208145951121679600[254] = 0.0;
   out_8208145951121679600[255] = 0.0;
   out_8208145951121679600[256] = 0.0;
   out_8208145951121679600[257] = 0.0;
   out_8208145951121679600[258] = 0.0;
   out_8208145951121679600[259] = 0.0;
   out_8208145951121679600[260] = 0.0;
   out_8208145951121679600[261] = 0.0;
   out_8208145951121679600[262] = 0.0;
   out_8208145951121679600[263] = 0.0;
   out_8208145951121679600[264] = 0.0;
   out_8208145951121679600[265] = 0.0;
   out_8208145951121679600[266] = 1.0;
   out_8208145951121679600[267] = 0.0;
   out_8208145951121679600[268] = 0.0;
   out_8208145951121679600[269] = 0.0;
   out_8208145951121679600[270] = 0.0;
   out_8208145951121679600[271] = 0.0;
   out_8208145951121679600[272] = 0.0;
   out_8208145951121679600[273] = 0.0;
   out_8208145951121679600[274] = 0.0;
   out_8208145951121679600[275] = 0.0;
   out_8208145951121679600[276] = 0.0;
   out_8208145951121679600[277] = 0.0;
   out_8208145951121679600[278] = 0.0;
   out_8208145951121679600[279] = 0.0;
   out_8208145951121679600[280] = 0.0;
   out_8208145951121679600[281] = 0.0;
   out_8208145951121679600[282] = 0.0;
   out_8208145951121679600[283] = 0.0;
   out_8208145951121679600[284] = 0.0;
   out_8208145951121679600[285] = 1.0;
   out_8208145951121679600[286] = 0.0;
   out_8208145951121679600[287] = 0.0;
   out_8208145951121679600[288] = 0.0;
   out_8208145951121679600[289] = 0.0;
   out_8208145951121679600[290] = 0.0;
   out_8208145951121679600[291] = 0.0;
   out_8208145951121679600[292] = 0.0;
   out_8208145951121679600[293] = 0.0;
   out_8208145951121679600[294] = 0.0;
   out_8208145951121679600[295] = 0.0;
   out_8208145951121679600[296] = 0.0;
   out_8208145951121679600[297] = 0.0;
   out_8208145951121679600[298] = 0.0;
   out_8208145951121679600[299] = 0.0;
   out_8208145951121679600[300] = 0.0;
   out_8208145951121679600[301] = 0.0;
   out_8208145951121679600[302] = 0.0;
   out_8208145951121679600[303] = 0.0;
   out_8208145951121679600[304] = 1.0;
   out_8208145951121679600[305] = 0.0;
   out_8208145951121679600[306] = 0.0;
   out_8208145951121679600[307] = 0.0;
   out_8208145951121679600[308] = 0.0;
   out_8208145951121679600[309] = 0.0;
   out_8208145951121679600[310] = 0.0;
   out_8208145951121679600[311] = 0.0;
   out_8208145951121679600[312] = 0.0;
   out_8208145951121679600[313] = 0.0;
   out_8208145951121679600[314] = 0.0;
   out_8208145951121679600[315] = 0.0;
   out_8208145951121679600[316] = 0.0;
   out_8208145951121679600[317] = 0.0;
   out_8208145951121679600[318] = 0.0;
   out_8208145951121679600[319] = 0.0;
   out_8208145951121679600[320] = 0.0;
   out_8208145951121679600[321] = 0.0;
   out_8208145951121679600[322] = 0.0;
   out_8208145951121679600[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_7339808689618378881) {
   out_7339808689618378881[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_7339808689618378881[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_7339808689618378881[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_7339808689618378881[3] = dt*state[12] + state[3];
   out_7339808689618378881[4] = dt*state[13] + state[4];
   out_7339808689618378881[5] = dt*state[14] + state[5];
   out_7339808689618378881[6] = state[6];
   out_7339808689618378881[7] = state[7];
   out_7339808689618378881[8] = state[8];
   out_7339808689618378881[9] = state[9];
   out_7339808689618378881[10] = state[10];
   out_7339808689618378881[11] = state[11];
   out_7339808689618378881[12] = state[12];
   out_7339808689618378881[13] = state[13];
   out_7339808689618378881[14] = state[14];
   out_7339808689618378881[15] = state[15];
   out_7339808689618378881[16] = state[16];
   out_7339808689618378881[17] = state[17];
}
void F_fun(double *state, double dt, double *out_4299830908048765183) {
   out_4299830908048765183[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4299830908048765183[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4299830908048765183[2] = 0;
   out_4299830908048765183[3] = 0;
   out_4299830908048765183[4] = 0;
   out_4299830908048765183[5] = 0;
   out_4299830908048765183[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4299830908048765183[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4299830908048765183[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4299830908048765183[9] = 0;
   out_4299830908048765183[10] = 0;
   out_4299830908048765183[11] = 0;
   out_4299830908048765183[12] = 0;
   out_4299830908048765183[13] = 0;
   out_4299830908048765183[14] = 0;
   out_4299830908048765183[15] = 0;
   out_4299830908048765183[16] = 0;
   out_4299830908048765183[17] = 0;
   out_4299830908048765183[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4299830908048765183[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4299830908048765183[20] = 0;
   out_4299830908048765183[21] = 0;
   out_4299830908048765183[22] = 0;
   out_4299830908048765183[23] = 0;
   out_4299830908048765183[24] = 0;
   out_4299830908048765183[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4299830908048765183[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4299830908048765183[27] = 0;
   out_4299830908048765183[28] = 0;
   out_4299830908048765183[29] = 0;
   out_4299830908048765183[30] = 0;
   out_4299830908048765183[31] = 0;
   out_4299830908048765183[32] = 0;
   out_4299830908048765183[33] = 0;
   out_4299830908048765183[34] = 0;
   out_4299830908048765183[35] = 0;
   out_4299830908048765183[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4299830908048765183[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4299830908048765183[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4299830908048765183[39] = 0;
   out_4299830908048765183[40] = 0;
   out_4299830908048765183[41] = 0;
   out_4299830908048765183[42] = 0;
   out_4299830908048765183[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4299830908048765183[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4299830908048765183[45] = 0;
   out_4299830908048765183[46] = 0;
   out_4299830908048765183[47] = 0;
   out_4299830908048765183[48] = 0;
   out_4299830908048765183[49] = 0;
   out_4299830908048765183[50] = 0;
   out_4299830908048765183[51] = 0;
   out_4299830908048765183[52] = 0;
   out_4299830908048765183[53] = 0;
   out_4299830908048765183[54] = 0;
   out_4299830908048765183[55] = 0;
   out_4299830908048765183[56] = 0;
   out_4299830908048765183[57] = 1;
   out_4299830908048765183[58] = 0;
   out_4299830908048765183[59] = 0;
   out_4299830908048765183[60] = 0;
   out_4299830908048765183[61] = 0;
   out_4299830908048765183[62] = 0;
   out_4299830908048765183[63] = 0;
   out_4299830908048765183[64] = 0;
   out_4299830908048765183[65] = 0;
   out_4299830908048765183[66] = dt;
   out_4299830908048765183[67] = 0;
   out_4299830908048765183[68] = 0;
   out_4299830908048765183[69] = 0;
   out_4299830908048765183[70] = 0;
   out_4299830908048765183[71] = 0;
   out_4299830908048765183[72] = 0;
   out_4299830908048765183[73] = 0;
   out_4299830908048765183[74] = 0;
   out_4299830908048765183[75] = 0;
   out_4299830908048765183[76] = 1;
   out_4299830908048765183[77] = 0;
   out_4299830908048765183[78] = 0;
   out_4299830908048765183[79] = 0;
   out_4299830908048765183[80] = 0;
   out_4299830908048765183[81] = 0;
   out_4299830908048765183[82] = 0;
   out_4299830908048765183[83] = 0;
   out_4299830908048765183[84] = 0;
   out_4299830908048765183[85] = dt;
   out_4299830908048765183[86] = 0;
   out_4299830908048765183[87] = 0;
   out_4299830908048765183[88] = 0;
   out_4299830908048765183[89] = 0;
   out_4299830908048765183[90] = 0;
   out_4299830908048765183[91] = 0;
   out_4299830908048765183[92] = 0;
   out_4299830908048765183[93] = 0;
   out_4299830908048765183[94] = 0;
   out_4299830908048765183[95] = 1;
   out_4299830908048765183[96] = 0;
   out_4299830908048765183[97] = 0;
   out_4299830908048765183[98] = 0;
   out_4299830908048765183[99] = 0;
   out_4299830908048765183[100] = 0;
   out_4299830908048765183[101] = 0;
   out_4299830908048765183[102] = 0;
   out_4299830908048765183[103] = 0;
   out_4299830908048765183[104] = dt;
   out_4299830908048765183[105] = 0;
   out_4299830908048765183[106] = 0;
   out_4299830908048765183[107] = 0;
   out_4299830908048765183[108] = 0;
   out_4299830908048765183[109] = 0;
   out_4299830908048765183[110] = 0;
   out_4299830908048765183[111] = 0;
   out_4299830908048765183[112] = 0;
   out_4299830908048765183[113] = 0;
   out_4299830908048765183[114] = 1;
   out_4299830908048765183[115] = 0;
   out_4299830908048765183[116] = 0;
   out_4299830908048765183[117] = 0;
   out_4299830908048765183[118] = 0;
   out_4299830908048765183[119] = 0;
   out_4299830908048765183[120] = 0;
   out_4299830908048765183[121] = 0;
   out_4299830908048765183[122] = 0;
   out_4299830908048765183[123] = 0;
   out_4299830908048765183[124] = 0;
   out_4299830908048765183[125] = 0;
   out_4299830908048765183[126] = 0;
   out_4299830908048765183[127] = 0;
   out_4299830908048765183[128] = 0;
   out_4299830908048765183[129] = 0;
   out_4299830908048765183[130] = 0;
   out_4299830908048765183[131] = 0;
   out_4299830908048765183[132] = 0;
   out_4299830908048765183[133] = 1;
   out_4299830908048765183[134] = 0;
   out_4299830908048765183[135] = 0;
   out_4299830908048765183[136] = 0;
   out_4299830908048765183[137] = 0;
   out_4299830908048765183[138] = 0;
   out_4299830908048765183[139] = 0;
   out_4299830908048765183[140] = 0;
   out_4299830908048765183[141] = 0;
   out_4299830908048765183[142] = 0;
   out_4299830908048765183[143] = 0;
   out_4299830908048765183[144] = 0;
   out_4299830908048765183[145] = 0;
   out_4299830908048765183[146] = 0;
   out_4299830908048765183[147] = 0;
   out_4299830908048765183[148] = 0;
   out_4299830908048765183[149] = 0;
   out_4299830908048765183[150] = 0;
   out_4299830908048765183[151] = 0;
   out_4299830908048765183[152] = 1;
   out_4299830908048765183[153] = 0;
   out_4299830908048765183[154] = 0;
   out_4299830908048765183[155] = 0;
   out_4299830908048765183[156] = 0;
   out_4299830908048765183[157] = 0;
   out_4299830908048765183[158] = 0;
   out_4299830908048765183[159] = 0;
   out_4299830908048765183[160] = 0;
   out_4299830908048765183[161] = 0;
   out_4299830908048765183[162] = 0;
   out_4299830908048765183[163] = 0;
   out_4299830908048765183[164] = 0;
   out_4299830908048765183[165] = 0;
   out_4299830908048765183[166] = 0;
   out_4299830908048765183[167] = 0;
   out_4299830908048765183[168] = 0;
   out_4299830908048765183[169] = 0;
   out_4299830908048765183[170] = 0;
   out_4299830908048765183[171] = 1;
   out_4299830908048765183[172] = 0;
   out_4299830908048765183[173] = 0;
   out_4299830908048765183[174] = 0;
   out_4299830908048765183[175] = 0;
   out_4299830908048765183[176] = 0;
   out_4299830908048765183[177] = 0;
   out_4299830908048765183[178] = 0;
   out_4299830908048765183[179] = 0;
   out_4299830908048765183[180] = 0;
   out_4299830908048765183[181] = 0;
   out_4299830908048765183[182] = 0;
   out_4299830908048765183[183] = 0;
   out_4299830908048765183[184] = 0;
   out_4299830908048765183[185] = 0;
   out_4299830908048765183[186] = 0;
   out_4299830908048765183[187] = 0;
   out_4299830908048765183[188] = 0;
   out_4299830908048765183[189] = 0;
   out_4299830908048765183[190] = 1;
   out_4299830908048765183[191] = 0;
   out_4299830908048765183[192] = 0;
   out_4299830908048765183[193] = 0;
   out_4299830908048765183[194] = 0;
   out_4299830908048765183[195] = 0;
   out_4299830908048765183[196] = 0;
   out_4299830908048765183[197] = 0;
   out_4299830908048765183[198] = 0;
   out_4299830908048765183[199] = 0;
   out_4299830908048765183[200] = 0;
   out_4299830908048765183[201] = 0;
   out_4299830908048765183[202] = 0;
   out_4299830908048765183[203] = 0;
   out_4299830908048765183[204] = 0;
   out_4299830908048765183[205] = 0;
   out_4299830908048765183[206] = 0;
   out_4299830908048765183[207] = 0;
   out_4299830908048765183[208] = 0;
   out_4299830908048765183[209] = 1;
   out_4299830908048765183[210] = 0;
   out_4299830908048765183[211] = 0;
   out_4299830908048765183[212] = 0;
   out_4299830908048765183[213] = 0;
   out_4299830908048765183[214] = 0;
   out_4299830908048765183[215] = 0;
   out_4299830908048765183[216] = 0;
   out_4299830908048765183[217] = 0;
   out_4299830908048765183[218] = 0;
   out_4299830908048765183[219] = 0;
   out_4299830908048765183[220] = 0;
   out_4299830908048765183[221] = 0;
   out_4299830908048765183[222] = 0;
   out_4299830908048765183[223] = 0;
   out_4299830908048765183[224] = 0;
   out_4299830908048765183[225] = 0;
   out_4299830908048765183[226] = 0;
   out_4299830908048765183[227] = 0;
   out_4299830908048765183[228] = 1;
   out_4299830908048765183[229] = 0;
   out_4299830908048765183[230] = 0;
   out_4299830908048765183[231] = 0;
   out_4299830908048765183[232] = 0;
   out_4299830908048765183[233] = 0;
   out_4299830908048765183[234] = 0;
   out_4299830908048765183[235] = 0;
   out_4299830908048765183[236] = 0;
   out_4299830908048765183[237] = 0;
   out_4299830908048765183[238] = 0;
   out_4299830908048765183[239] = 0;
   out_4299830908048765183[240] = 0;
   out_4299830908048765183[241] = 0;
   out_4299830908048765183[242] = 0;
   out_4299830908048765183[243] = 0;
   out_4299830908048765183[244] = 0;
   out_4299830908048765183[245] = 0;
   out_4299830908048765183[246] = 0;
   out_4299830908048765183[247] = 1;
   out_4299830908048765183[248] = 0;
   out_4299830908048765183[249] = 0;
   out_4299830908048765183[250] = 0;
   out_4299830908048765183[251] = 0;
   out_4299830908048765183[252] = 0;
   out_4299830908048765183[253] = 0;
   out_4299830908048765183[254] = 0;
   out_4299830908048765183[255] = 0;
   out_4299830908048765183[256] = 0;
   out_4299830908048765183[257] = 0;
   out_4299830908048765183[258] = 0;
   out_4299830908048765183[259] = 0;
   out_4299830908048765183[260] = 0;
   out_4299830908048765183[261] = 0;
   out_4299830908048765183[262] = 0;
   out_4299830908048765183[263] = 0;
   out_4299830908048765183[264] = 0;
   out_4299830908048765183[265] = 0;
   out_4299830908048765183[266] = 1;
   out_4299830908048765183[267] = 0;
   out_4299830908048765183[268] = 0;
   out_4299830908048765183[269] = 0;
   out_4299830908048765183[270] = 0;
   out_4299830908048765183[271] = 0;
   out_4299830908048765183[272] = 0;
   out_4299830908048765183[273] = 0;
   out_4299830908048765183[274] = 0;
   out_4299830908048765183[275] = 0;
   out_4299830908048765183[276] = 0;
   out_4299830908048765183[277] = 0;
   out_4299830908048765183[278] = 0;
   out_4299830908048765183[279] = 0;
   out_4299830908048765183[280] = 0;
   out_4299830908048765183[281] = 0;
   out_4299830908048765183[282] = 0;
   out_4299830908048765183[283] = 0;
   out_4299830908048765183[284] = 0;
   out_4299830908048765183[285] = 1;
   out_4299830908048765183[286] = 0;
   out_4299830908048765183[287] = 0;
   out_4299830908048765183[288] = 0;
   out_4299830908048765183[289] = 0;
   out_4299830908048765183[290] = 0;
   out_4299830908048765183[291] = 0;
   out_4299830908048765183[292] = 0;
   out_4299830908048765183[293] = 0;
   out_4299830908048765183[294] = 0;
   out_4299830908048765183[295] = 0;
   out_4299830908048765183[296] = 0;
   out_4299830908048765183[297] = 0;
   out_4299830908048765183[298] = 0;
   out_4299830908048765183[299] = 0;
   out_4299830908048765183[300] = 0;
   out_4299830908048765183[301] = 0;
   out_4299830908048765183[302] = 0;
   out_4299830908048765183[303] = 0;
   out_4299830908048765183[304] = 1;
   out_4299830908048765183[305] = 0;
   out_4299830908048765183[306] = 0;
   out_4299830908048765183[307] = 0;
   out_4299830908048765183[308] = 0;
   out_4299830908048765183[309] = 0;
   out_4299830908048765183[310] = 0;
   out_4299830908048765183[311] = 0;
   out_4299830908048765183[312] = 0;
   out_4299830908048765183[313] = 0;
   out_4299830908048765183[314] = 0;
   out_4299830908048765183[315] = 0;
   out_4299830908048765183[316] = 0;
   out_4299830908048765183[317] = 0;
   out_4299830908048765183[318] = 0;
   out_4299830908048765183[319] = 0;
   out_4299830908048765183[320] = 0;
   out_4299830908048765183[321] = 0;
   out_4299830908048765183[322] = 0;
   out_4299830908048765183[323] = 1;
}
void h_4(double *state, double *unused, double *out_3838924425177329508) {
   out_3838924425177329508[0] = state[6] + state[9];
   out_3838924425177329508[1] = state[7] + state[10];
   out_3838924425177329508[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_6964376043796922763) {
   out_6964376043796922763[0] = 0;
   out_6964376043796922763[1] = 0;
   out_6964376043796922763[2] = 0;
   out_6964376043796922763[3] = 0;
   out_6964376043796922763[4] = 0;
   out_6964376043796922763[5] = 0;
   out_6964376043796922763[6] = 1;
   out_6964376043796922763[7] = 0;
   out_6964376043796922763[8] = 0;
   out_6964376043796922763[9] = 1;
   out_6964376043796922763[10] = 0;
   out_6964376043796922763[11] = 0;
   out_6964376043796922763[12] = 0;
   out_6964376043796922763[13] = 0;
   out_6964376043796922763[14] = 0;
   out_6964376043796922763[15] = 0;
   out_6964376043796922763[16] = 0;
   out_6964376043796922763[17] = 0;
   out_6964376043796922763[18] = 0;
   out_6964376043796922763[19] = 0;
   out_6964376043796922763[20] = 0;
   out_6964376043796922763[21] = 0;
   out_6964376043796922763[22] = 0;
   out_6964376043796922763[23] = 0;
   out_6964376043796922763[24] = 0;
   out_6964376043796922763[25] = 1;
   out_6964376043796922763[26] = 0;
   out_6964376043796922763[27] = 0;
   out_6964376043796922763[28] = 1;
   out_6964376043796922763[29] = 0;
   out_6964376043796922763[30] = 0;
   out_6964376043796922763[31] = 0;
   out_6964376043796922763[32] = 0;
   out_6964376043796922763[33] = 0;
   out_6964376043796922763[34] = 0;
   out_6964376043796922763[35] = 0;
   out_6964376043796922763[36] = 0;
   out_6964376043796922763[37] = 0;
   out_6964376043796922763[38] = 0;
   out_6964376043796922763[39] = 0;
   out_6964376043796922763[40] = 0;
   out_6964376043796922763[41] = 0;
   out_6964376043796922763[42] = 0;
   out_6964376043796922763[43] = 0;
   out_6964376043796922763[44] = 1;
   out_6964376043796922763[45] = 0;
   out_6964376043796922763[46] = 0;
   out_6964376043796922763[47] = 1;
   out_6964376043796922763[48] = 0;
   out_6964376043796922763[49] = 0;
   out_6964376043796922763[50] = 0;
   out_6964376043796922763[51] = 0;
   out_6964376043796922763[52] = 0;
   out_6964376043796922763[53] = 0;
}
void h_10(double *state, double *unused, double *out_4478443536349725461) {
   out_4478443536349725461[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_4478443536349725461[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_4478443536349725461[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_8208658119783990230) {
   out_8208658119783990230[0] = 0;
   out_8208658119783990230[1] = 9.8100000000000005*cos(state[1]);
   out_8208658119783990230[2] = 0;
   out_8208658119783990230[3] = 0;
   out_8208658119783990230[4] = -state[8];
   out_8208658119783990230[5] = state[7];
   out_8208658119783990230[6] = 0;
   out_8208658119783990230[7] = state[5];
   out_8208658119783990230[8] = -state[4];
   out_8208658119783990230[9] = 0;
   out_8208658119783990230[10] = 0;
   out_8208658119783990230[11] = 0;
   out_8208658119783990230[12] = 1;
   out_8208658119783990230[13] = 0;
   out_8208658119783990230[14] = 0;
   out_8208658119783990230[15] = 1;
   out_8208658119783990230[16] = 0;
   out_8208658119783990230[17] = 0;
   out_8208658119783990230[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_8208658119783990230[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_8208658119783990230[20] = 0;
   out_8208658119783990230[21] = state[8];
   out_8208658119783990230[22] = 0;
   out_8208658119783990230[23] = -state[6];
   out_8208658119783990230[24] = -state[5];
   out_8208658119783990230[25] = 0;
   out_8208658119783990230[26] = state[3];
   out_8208658119783990230[27] = 0;
   out_8208658119783990230[28] = 0;
   out_8208658119783990230[29] = 0;
   out_8208658119783990230[30] = 0;
   out_8208658119783990230[31] = 1;
   out_8208658119783990230[32] = 0;
   out_8208658119783990230[33] = 0;
   out_8208658119783990230[34] = 1;
   out_8208658119783990230[35] = 0;
   out_8208658119783990230[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_8208658119783990230[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_8208658119783990230[38] = 0;
   out_8208658119783990230[39] = -state[7];
   out_8208658119783990230[40] = state[6];
   out_8208658119783990230[41] = 0;
   out_8208658119783990230[42] = state[4];
   out_8208658119783990230[43] = -state[3];
   out_8208658119783990230[44] = 0;
   out_8208658119783990230[45] = 0;
   out_8208658119783990230[46] = 0;
   out_8208658119783990230[47] = 0;
   out_8208658119783990230[48] = 0;
   out_8208658119783990230[49] = 0;
   out_8208658119783990230[50] = 1;
   out_8208658119783990230[51] = 0;
   out_8208658119783990230[52] = 0;
   out_8208658119783990230[53] = 1;
}
void h_13(double *state, double *unused, double *out_349204714200215709) {
   out_349204714200215709[0] = state[3];
   out_349204714200215709[1] = state[4];
   out_349204714200215709[2] = state[5];
}
void H_13(double *state, double *unused, double *out_8270094204580296052) {
   out_8270094204580296052[0] = 0;
   out_8270094204580296052[1] = 0;
   out_8270094204580296052[2] = 0;
   out_8270094204580296052[3] = 1;
   out_8270094204580296052[4] = 0;
   out_8270094204580296052[5] = 0;
   out_8270094204580296052[6] = 0;
   out_8270094204580296052[7] = 0;
   out_8270094204580296052[8] = 0;
   out_8270094204580296052[9] = 0;
   out_8270094204580296052[10] = 0;
   out_8270094204580296052[11] = 0;
   out_8270094204580296052[12] = 0;
   out_8270094204580296052[13] = 0;
   out_8270094204580296052[14] = 0;
   out_8270094204580296052[15] = 0;
   out_8270094204580296052[16] = 0;
   out_8270094204580296052[17] = 0;
   out_8270094204580296052[18] = 0;
   out_8270094204580296052[19] = 0;
   out_8270094204580296052[20] = 0;
   out_8270094204580296052[21] = 0;
   out_8270094204580296052[22] = 1;
   out_8270094204580296052[23] = 0;
   out_8270094204580296052[24] = 0;
   out_8270094204580296052[25] = 0;
   out_8270094204580296052[26] = 0;
   out_8270094204580296052[27] = 0;
   out_8270094204580296052[28] = 0;
   out_8270094204580296052[29] = 0;
   out_8270094204580296052[30] = 0;
   out_8270094204580296052[31] = 0;
   out_8270094204580296052[32] = 0;
   out_8270094204580296052[33] = 0;
   out_8270094204580296052[34] = 0;
   out_8270094204580296052[35] = 0;
   out_8270094204580296052[36] = 0;
   out_8270094204580296052[37] = 0;
   out_8270094204580296052[38] = 0;
   out_8270094204580296052[39] = 0;
   out_8270094204580296052[40] = 0;
   out_8270094204580296052[41] = 1;
   out_8270094204580296052[42] = 0;
   out_8270094204580296052[43] = 0;
   out_8270094204580296052[44] = 0;
   out_8270094204580296052[45] = 0;
   out_8270094204580296052[46] = 0;
   out_8270094204580296052[47] = 0;
   out_8270094204580296052[48] = 0;
   out_8270094204580296052[49] = 0;
   out_8270094204580296052[50] = 0;
   out_8270094204580296052[51] = 0;
   out_8270094204580296052[52] = 0;
   out_8270094204580296052[53] = 0;
}
void h_14(double *state, double *unused, double *out_5535558880524166264) {
   out_5535558880524166264[0] = state[6];
   out_5535558880524166264[1] = state[7];
   out_5535558880524166264[2] = state[8];
}
void H_14(double *state, double *unused, double *out_7519127173573144324) {
   out_7519127173573144324[0] = 0;
   out_7519127173573144324[1] = 0;
   out_7519127173573144324[2] = 0;
   out_7519127173573144324[3] = 0;
   out_7519127173573144324[4] = 0;
   out_7519127173573144324[5] = 0;
   out_7519127173573144324[6] = 1;
   out_7519127173573144324[7] = 0;
   out_7519127173573144324[8] = 0;
   out_7519127173573144324[9] = 0;
   out_7519127173573144324[10] = 0;
   out_7519127173573144324[11] = 0;
   out_7519127173573144324[12] = 0;
   out_7519127173573144324[13] = 0;
   out_7519127173573144324[14] = 0;
   out_7519127173573144324[15] = 0;
   out_7519127173573144324[16] = 0;
   out_7519127173573144324[17] = 0;
   out_7519127173573144324[18] = 0;
   out_7519127173573144324[19] = 0;
   out_7519127173573144324[20] = 0;
   out_7519127173573144324[21] = 0;
   out_7519127173573144324[22] = 0;
   out_7519127173573144324[23] = 0;
   out_7519127173573144324[24] = 0;
   out_7519127173573144324[25] = 1;
   out_7519127173573144324[26] = 0;
   out_7519127173573144324[27] = 0;
   out_7519127173573144324[28] = 0;
   out_7519127173573144324[29] = 0;
   out_7519127173573144324[30] = 0;
   out_7519127173573144324[31] = 0;
   out_7519127173573144324[32] = 0;
   out_7519127173573144324[33] = 0;
   out_7519127173573144324[34] = 0;
   out_7519127173573144324[35] = 0;
   out_7519127173573144324[36] = 0;
   out_7519127173573144324[37] = 0;
   out_7519127173573144324[38] = 0;
   out_7519127173573144324[39] = 0;
   out_7519127173573144324[40] = 0;
   out_7519127173573144324[41] = 0;
   out_7519127173573144324[42] = 0;
   out_7519127173573144324[43] = 0;
   out_7519127173573144324[44] = 1;
   out_7519127173573144324[45] = 0;
   out_7519127173573144324[46] = 0;
   out_7519127173573144324[47] = 0;
   out_7519127173573144324[48] = 0;
   out_7519127173573144324[49] = 0;
   out_7519127173573144324[50] = 0;
   out_7519127173573144324[51] = 0;
   out_7519127173573144324[52] = 0;
   out_7519127173573144324[53] = 0;
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
void pose_err_fun(double *nom_x, double *delta_x, double *out_7911616955151800495) {
  err_fun(nom_x, delta_x, out_7911616955151800495);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_7584171002491943517) {
  inv_err_fun(nom_x, true_x, out_7584171002491943517);
}
void pose_H_mod_fun(double *state, double *out_8208145951121679600) {
  H_mod_fun(state, out_8208145951121679600);
}
void pose_f_fun(double *state, double dt, double *out_7339808689618378881) {
  f_fun(state,  dt, out_7339808689618378881);
}
void pose_F_fun(double *state, double dt, double *out_4299830908048765183) {
  F_fun(state,  dt, out_4299830908048765183);
}
void pose_h_4(double *state, double *unused, double *out_3838924425177329508) {
  h_4(state, unused, out_3838924425177329508);
}
void pose_H_4(double *state, double *unused, double *out_6964376043796922763) {
  H_4(state, unused, out_6964376043796922763);
}
void pose_h_10(double *state, double *unused, double *out_4478443536349725461) {
  h_10(state, unused, out_4478443536349725461);
}
void pose_H_10(double *state, double *unused, double *out_8208658119783990230) {
  H_10(state, unused, out_8208658119783990230);
}
void pose_h_13(double *state, double *unused, double *out_349204714200215709) {
  h_13(state, unused, out_349204714200215709);
}
void pose_H_13(double *state, double *unused, double *out_8270094204580296052) {
  H_13(state, unused, out_8270094204580296052);
}
void pose_h_14(double *state, double *unused, double *out_5535558880524166264) {
  h_14(state, unused, out_5535558880524166264);
}
void pose_H_14(double *state, double *unused, double *out_7519127173573144324) {
  H_14(state, unused, out_7519127173573144324);
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
