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
void err_fun(double *nom_x, double *delta_x, double *out_8714848832990626554) {
   out_8714848832990626554[0] = delta_x[0] + nom_x[0];
   out_8714848832990626554[1] = delta_x[1] + nom_x[1];
   out_8714848832990626554[2] = delta_x[2] + nom_x[2];
   out_8714848832990626554[3] = delta_x[3] + nom_x[3];
   out_8714848832990626554[4] = delta_x[4] + nom_x[4];
   out_8714848832990626554[5] = delta_x[5] + nom_x[5];
   out_8714848832990626554[6] = delta_x[6] + nom_x[6];
   out_8714848832990626554[7] = delta_x[7] + nom_x[7];
   out_8714848832990626554[8] = delta_x[8] + nom_x[8];
   out_8714848832990626554[9] = delta_x[9] + nom_x[9];
   out_8714848832990626554[10] = delta_x[10] + nom_x[10];
   out_8714848832990626554[11] = delta_x[11] + nom_x[11];
   out_8714848832990626554[12] = delta_x[12] + nom_x[12];
   out_8714848832990626554[13] = delta_x[13] + nom_x[13];
   out_8714848832990626554[14] = delta_x[14] + nom_x[14];
   out_8714848832990626554[15] = delta_x[15] + nom_x[15];
   out_8714848832990626554[16] = delta_x[16] + nom_x[16];
   out_8714848832990626554[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_5047671582975253903) {
   out_5047671582975253903[0] = -nom_x[0] + true_x[0];
   out_5047671582975253903[1] = -nom_x[1] + true_x[1];
   out_5047671582975253903[2] = -nom_x[2] + true_x[2];
   out_5047671582975253903[3] = -nom_x[3] + true_x[3];
   out_5047671582975253903[4] = -nom_x[4] + true_x[4];
   out_5047671582975253903[5] = -nom_x[5] + true_x[5];
   out_5047671582975253903[6] = -nom_x[6] + true_x[6];
   out_5047671582975253903[7] = -nom_x[7] + true_x[7];
   out_5047671582975253903[8] = -nom_x[8] + true_x[8];
   out_5047671582975253903[9] = -nom_x[9] + true_x[9];
   out_5047671582975253903[10] = -nom_x[10] + true_x[10];
   out_5047671582975253903[11] = -nom_x[11] + true_x[11];
   out_5047671582975253903[12] = -nom_x[12] + true_x[12];
   out_5047671582975253903[13] = -nom_x[13] + true_x[13];
   out_5047671582975253903[14] = -nom_x[14] + true_x[14];
   out_5047671582975253903[15] = -nom_x[15] + true_x[15];
   out_5047671582975253903[16] = -nom_x[16] + true_x[16];
   out_5047671582975253903[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_1709250979764021582) {
   out_1709250979764021582[0] = 1.0;
   out_1709250979764021582[1] = 0.0;
   out_1709250979764021582[2] = 0.0;
   out_1709250979764021582[3] = 0.0;
   out_1709250979764021582[4] = 0.0;
   out_1709250979764021582[5] = 0.0;
   out_1709250979764021582[6] = 0.0;
   out_1709250979764021582[7] = 0.0;
   out_1709250979764021582[8] = 0.0;
   out_1709250979764021582[9] = 0.0;
   out_1709250979764021582[10] = 0.0;
   out_1709250979764021582[11] = 0.0;
   out_1709250979764021582[12] = 0.0;
   out_1709250979764021582[13] = 0.0;
   out_1709250979764021582[14] = 0.0;
   out_1709250979764021582[15] = 0.0;
   out_1709250979764021582[16] = 0.0;
   out_1709250979764021582[17] = 0.0;
   out_1709250979764021582[18] = 0.0;
   out_1709250979764021582[19] = 1.0;
   out_1709250979764021582[20] = 0.0;
   out_1709250979764021582[21] = 0.0;
   out_1709250979764021582[22] = 0.0;
   out_1709250979764021582[23] = 0.0;
   out_1709250979764021582[24] = 0.0;
   out_1709250979764021582[25] = 0.0;
   out_1709250979764021582[26] = 0.0;
   out_1709250979764021582[27] = 0.0;
   out_1709250979764021582[28] = 0.0;
   out_1709250979764021582[29] = 0.0;
   out_1709250979764021582[30] = 0.0;
   out_1709250979764021582[31] = 0.0;
   out_1709250979764021582[32] = 0.0;
   out_1709250979764021582[33] = 0.0;
   out_1709250979764021582[34] = 0.0;
   out_1709250979764021582[35] = 0.0;
   out_1709250979764021582[36] = 0.0;
   out_1709250979764021582[37] = 0.0;
   out_1709250979764021582[38] = 1.0;
   out_1709250979764021582[39] = 0.0;
   out_1709250979764021582[40] = 0.0;
   out_1709250979764021582[41] = 0.0;
   out_1709250979764021582[42] = 0.0;
   out_1709250979764021582[43] = 0.0;
   out_1709250979764021582[44] = 0.0;
   out_1709250979764021582[45] = 0.0;
   out_1709250979764021582[46] = 0.0;
   out_1709250979764021582[47] = 0.0;
   out_1709250979764021582[48] = 0.0;
   out_1709250979764021582[49] = 0.0;
   out_1709250979764021582[50] = 0.0;
   out_1709250979764021582[51] = 0.0;
   out_1709250979764021582[52] = 0.0;
   out_1709250979764021582[53] = 0.0;
   out_1709250979764021582[54] = 0.0;
   out_1709250979764021582[55] = 0.0;
   out_1709250979764021582[56] = 0.0;
   out_1709250979764021582[57] = 1.0;
   out_1709250979764021582[58] = 0.0;
   out_1709250979764021582[59] = 0.0;
   out_1709250979764021582[60] = 0.0;
   out_1709250979764021582[61] = 0.0;
   out_1709250979764021582[62] = 0.0;
   out_1709250979764021582[63] = 0.0;
   out_1709250979764021582[64] = 0.0;
   out_1709250979764021582[65] = 0.0;
   out_1709250979764021582[66] = 0.0;
   out_1709250979764021582[67] = 0.0;
   out_1709250979764021582[68] = 0.0;
   out_1709250979764021582[69] = 0.0;
   out_1709250979764021582[70] = 0.0;
   out_1709250979764021582[71] = 0.0;
   out_1709250979764021582[72] = 0.0;
   out_1709250979764021582[73] = 0.0;
   out_1709250979764021582[74] = 0.0;
   out_1709250979764021582[75] = 0.0;
   out_1709250979764021582[76] = 1.0;
   out_1709250979764021582[77] = 0.0;
   out_1709250979764021582[78] = 0.0;
   out_1709250979764021582[79] = 0.0;
   out_1709250979764021582[80] = 0.0;
   out_1709250979764021582[81] = 0.0;
   out_1709250979764021582[82] = 0.0;
   out_1709250979764021582[83] = 0.0;
   out_1709250979764021582[84] = 0.0;
   out_1709250979764021582[85] = 0.0;
   out_1709250979764021582[86] = 0.0;
   out_1709250979764021582[87] = 0.0;
   out_1709250979764021582[88] = 0.0;
   out_1709250979764021582[89] = 0.0;
   out_1709250979764021582[90] = 0.0;
   out_1709250979764021582[91] = 0.0;
   out_1709250979764021582[92] = 0.0;
   out_1709250979764021582[93] = 0.0;
   out_1709250979764021582[94] = 0.0;
   out_1709250979764021582[95] = 1.0;
   out_1709250979764021582[96] = 0.0;
   out_1709250979764021582[97] = 0.0;
   out_1709250979764021582[98] = 0.0;
   out_1709250979764021582[99] = 0.0;
   out_1709250979764021582[100] = 0.0;
   out_1709250979764021582[101] = 0.0;
   out_1709250979764021582[102] = 0.0;
   out_1709250979764021582[103] = 0.0;
   out_1709250979764021582[104] = 0.0;
   out_1709250979764021582[105] = 0.0;
   out_1709250979764021582[106] = 0.0;
   out_1709250979764021582[107] = 0.0;
   out_1709250979764021582[108] = 0.0;
   out_1709250979764021582[109] = 0.0;
   out_1709250979764021582[110] = 0.0;
   out_1709250979764021582[111] = 0.0;
   out_1709250979764021582[112] = 0.0;
   out_1709250979764021582[113] = 0.0;
   out_1709250979764021582[114] = 1.0;
   out_1709250979764021582[115] = 0.0;
   out_1709250979764021582[116] = 0.0;
   out_1709250979764021582[117] = 0.0;
   out_1709250979764021582[118] = 0.0;
   out_1709250979764021582[119] = 0.0;
   out_1709250979764021582[120] = 0.0;
   out_1709250979764021582[121] = 0.0;
   out_1709250979764021582[122] = 0.0;
   out_1709250979764021582[123] = 0.0;
   out_1709250979764021582[124] = 0.0;
   out_1709250979764021582[125] = 0.0;
   out_1709250979764021582[126] = 0.0;
   out_1709250979764021582[127] = 0.0;
   out_1709250979764021582[128] = 0.0;
   out_1709250979764021582[129] = 0.0;
   out_1709250979764021582[130] = 0.0;
   out_1709250979764021582[131] = 0.0;
   out_1709250979764021582[132] = 0.0;
   out_1709250979764021582[133] = 1.0;
   out_1709250979764021582[134] = 0.0;
   out_1709250979764021582[135] = 0.0;
   out_1709250979764021582[136] = 0.0;
   out_1709250979764021582[137] = 0.0;
   out_1709250979764021582[138] = 0.0;
   out_1709250979764021582[139] = 0.0;
   out_1709250979764021582[140] = 0.0;
   out_1709250979764021582[141] = 0.0;
   out_1709250979764021582[142] = 0.0;
   out_1709250979764021582[143] = 0.0;
   out_1709250979764021582[144] = 0.0;
   out_1709250979764021582[145] = 0.0;
   out_1709250979764021582[146] = 0.0;
   out_1709250979764021582[147] = 0.0;
   out_1709250979764021582[148] = 0.0;
   out_1709250979764021582[149] = 0.0;
   out_1709250979764021582[150] = 0.0;
   out_1709250979764021582[151] = 0.0;
   out_1709250979764021582[152] = 1.0;
   out_1709250979764021582[153] = 0.0;
   out_1709250979764021582[154] = 0.0;
   out_1709250979764021582[155] = 0.0;
   out_1709250979764021582[156] = 0.0;
   out_1709250979764021582[157] = 0.0;
   out_1709250979764021582[158] = 0.0;
   out_1709250979764021582[159] = 0.0;
   out_1709250979764021582[160] = 0.0;
   out_1709250979764021582[161] = 0.0;
   out_1709250979764021582[162] = 0.0;
   out_1709250979764021582[163] = 0.0;
   out_1709250979764021582[164] = 0.0;
   out_1709250979764021582[165] = 0.0;
   out_1709250979764021582[166] = 0.0;
   out_1709250979764021582[167] = 0.0;
   out_1709250979764021582[168] = 0.0;
   out_1709250979764021582[169] = 0.0;
   out_1709250979764021582[170] = 0.0;
   out_1709250979764021582[171] = 1.0;
   out_1709250979764021582[172] = 0.0;
   out_1709250979764021582[173] = 0.0;
   out_1709250979764021582[174] = 0.0;
   out_1709250979764021582[175] = 0.0;
   out_1709250979764021582[176] = 0.0;
   out_1709250979764021582[177] = 0.0;
   out_1709250979764021582[178] = 0.0;
   out_1709250979764021582[179] = 0.0;
   out_1709250979764021582[180] = 0.0;
   out_1709250979764021582[181] = 0.0;
   out_1709250979764021582[182] = 0.0;
   out_1709250979764021582[183] = 0.0;
   out_1709250979764021582[184] = 0.0;
   out_1709250979764021582[185] = 0.0;
   out_1709250979764021582[186] = 0.0;
   out_1709250979764021582[187] = 0.0;
   out_1709250979764021582[188] = 0.0;
   out_1709250979764021582[189] = 0.0;
   out_1709250979764021582[190] = 1.0;
   out_1709250979764021582[191] = 0.0;
   out_1709250979764021582[192] = 0.0;
   out_1709250979764021582[193] = 0.0;
   out_1709250979764021582[194] = 0.0;
   out_1709250979764021582[195] = 0.0;
   out_1709250979764021582[196] = 0.0;
   out_1709250979764021582[197] = 0.0;
   out_1709250979764021582[198] = 0.0;
   out_1709250979764021582[199] = 0.0;
   out_1709250979764021582[200] = 0.0;
   out_1709250979764021582[201] = 0.0;
   out_1709250979764021582[202] = 0.0;
   out_1709250979764021582[203] = 0.0;
   out_1709250979764021582[204] = 0.0;
   out_1709250979764021582[205] = 0.0;
   out_1709250979764021582[206] = 0.0;
   out_1709250979764021582[207] = 0.0;
   out_1709250979764021582[208] = 0.0;
   out_1709250979764021582[209] = 1.0;
   out_1709250979764021582[210] = 0.0;
   out_1709250979764021582[211] = 0.0;
   out_1709250979764021582[212] = 0.0;
   out_1709250979764021582[213] = 0.0;
   out_1709250979764021582[214] = 0.0;
   out_1709250979764021582[215] = 0.0;
   out_1709250979764021582[216] = 0.0;
   out_1709250979764021582[217] = 0.0;
   out_1709250979764021582[218] = 0.0;
   out_1709250979764021582[219] = 0.0;
   out_1709250979764021582[220] = 0.0;
   out_1709250979764021582[221] = 0.0;
   out_1709250979764021582[222] = 0.0;
   out_1709250979764021582[223] = 0.0;
   out_1709250979764021582[224] = 0.0;
   out_1709250979764021582[225] = 0.0;
   out_1709250979764021582[226] = 0.0;
   out_1709250979764021582[227] = 0.0;
   out_1709250979764021582[228] = 1.0;
   out_1709250979764021582[229] = 0.0;
   out_1709250979764021582[230] = 0.0;
   out_1709250979764021582[231] = 0.0;
   out_1709250979764021582[232] = 0.0;
   out_1709250979764021582[233] = 0.0;
   out_1709250979764021582[234] = 0.0;
   out_1709250979764021582[235] = 0.0;
   out_1709250979764021582[236] = 0.0;
   out_1709250979764021582[237] = 0.0;
   out_1709250979764021582[238] = 0.0;
   out_1709250979764021582[239] = 0.0;
   out_1709250979764021582[240] = 0.0;
   out_1709250979764021582[241] = 0.0;
   out_1709250979764021582[242] = 0.0;
   out_1709250979764021582[243] = 0.0;
   out_1709250979764021582[244] = 0.0;
   out_1709250979764021582[245] = 0.0;
   out_1709250979764021582[246] = 0.0;
   out_1709250979764021582[247] = 1.0;
   out_1709250979764021582[248] = 0.0;
   out_1709250979764021582[249] = 0.0;
   out_1709250979764021582[250] = 0.0;
   out_1709250979764021582[251] = 0.0;
   out_1709250979764021582[252] = 0.0;
   out_1709250979764021582[253] = 0.0;
   out_1709250979764021582[254] = 0.0;
   out_1709250979764021582[255] = 0.0;
   out_1709250979764021582[256] = 0.0;
   out_1709250979764021582[257] = 0.0;
   out_1709250979764021582[258] = 0.0;
   out_1709250979764021582[259] = 0.0;
   out_1709250979764021582[260] = 0.0;
   out_1709250979764021582[261] = 0.0;
   out_1709250979764021582[262] = 0.0;
   out_1709250979764021582[263] = 0.0;
   out_1709250979764021582[264] = 0.0;
   out_1709250979764021582[265] = 0.0;
   out_1709250979764021582[266] = 1.0;
   out_1709250979764021582[267] = 0.0;
   out_1709250979764021582[268] = 0.0;
   out_1709250979764021582[269] = 0.0;
   out_1709250979764021582[270] = 0.0;
   out_1709250979764021582[271] = 0.0;
   out_1709250979764021582[272] = 0.0;
   out_1709250979764021582[273] = 0.0;
   out_1709250979764021582[274] = 0.0;
   out_1709250979764021582[275] = 0.0;
   out_1709250979764021582[276] = 0.0;
   out_1709250979764021582[277] = 0.0;
   out_1709250979764021582[278] = 0.0;
   out_1709250979764021582[279] = 0.0;
   out_1709250979764021582[280] = 0.0;
   out_1709250979764021582[281] = 0.0;
   out_1709250979764021582[282] = 0.0;
   out_1709250979764021582[283] = 0.0;
   out_1709250979764021582[284] = 0.0;
   out_1709250979764021582[285] = 1.0;
   out_1709250979764021582[286] = 0.0;
   out_1709250979764021582[287] = 0.0;
   out_1709250979764021582[288] = 0.0;
   out_1709250979764021582[289] = 0.0;
   out_1709250979764021582[290] = 0.0;
   out_1709250979764021582[291] = 0.0;
   out_1709250979764021582[292] = 0.0;
   out_1709250979764021582[293] = 0.0;
   out_1709250979764021582[294] = 0.0;
   out_1709250979764021582[295] = 0.0;
   out_1709250979764021582[296] = 0.0;
   out_1709250979764021582[297] = 0.0;
   out_1709250979764021582[298] = 0.0;
   out_1709250979764021582[299] = 0.0;
   out_1709250979764021582[300] = 0.0;
   out_1709250979764021582[301] = 0.0;
   out_1709250979764021582[302] = 0.0;
   out_1709250979764021582[303] = 0.0;
   out_1709250979764021582[304] = 1.0;
   out_1709250979764021582[305] = 0.0;
   out_1709250979764021582[306] = 0.0;
   out_1709250979764021582[307] = 0.0;
   out_1709250979764021582[308] = 0.0;
   out_1709250979764021582[309] = 0.0;
   out_1709250979764021582[310] = 0.0;
   out_1709250979764021582[311] = 0.0;
   out_1709250979764021582[312] = 0.0;
   out_1709250979764021582[313] = 0.0;
   out_1709250979764021582[314] = 0.0;
   out_1709250979764021582[315] = 0.0;
   out_1709250979764021582[316] = 0.0;
   out_1709250979764021582[317] = 0.0;
   out_1709250979764021582[318] = 0.0;
   out_1709250979764021582[319] = 0.0;
   out_1709250979764021582[320] = 0.0;
   out_1709250979764021582[321] = 0.0;
   out_1709250979764021582[322] = 0.0;
   out_1709250979764021582[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_1316099113648689196) {
   out_1316099113648689196[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_1316099113648689196[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_1316099113648689196[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_1316099113648689196[3] = dt*state[12] + state[3];
   out_1316099113648689196[4] = dt*state[13] + state[4];
   out_1316099113648689196[5] = dt*state[14] + state[5];
   out_1316099113648689196[6] = state[6];
   out_1316099113648689196[7] = state[7];
   out_1316099113648689196[8] = state[8];
   out_1316099113648689196[9] = state[9];
   out_1316099113648689196[10] = state[10];
   out_1316099113648689196[11] = state[11];
   out_1316099113648689196[12] = state[12];
   out_1316099113648689196[13] = state[13];
   out_1316099113648689196[14] = state[14];
   out_1316099113648689196[15] = state[15];
   out_1316099113648689196[16] = state[16];
   out_1316099113648689196[17] = state[17];
}
void F_fun(double *state, double dt, double *out_4732408561172474784) {
   out_4732408561172474784[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4732408561172474784[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4732408561172474784[2] = 0;
   out_4732408561172474784[3] = 0;
   out_4732408561172474784[4] = 0;
   out_4732408561172474784[5] = 0;
   out_4732408561172474784[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4732408561172474784[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4732408561172474784[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4732408561172474784[9] = 0;
   out_4732408561172474784[10] = 0;
   out_4732408561172474784[11] = 0;
   out_4732408561172474784[12] = 0;
   out_4732408561172474784[13] = 0;
   out_4732408561172474784[14] = 0;
   out_4732408561172474784[15] = 0;
   out_4732408561172474784[16] = 0;
   out_4732408561172474784[17] = 0;
   out_4732408561172474784[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4732408561172474784[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4732408561172474784[20] = 0;
   out_4732408561172474784[21] = 0;
   out_4732408561172474784[22] = 0;
   out_4732408561172474784[23] = 0;
   out_4732408561172474784[24] = 0;
   out_4732408561172474784[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4732408561172474784[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4732408561172474784[27] = 0;
   out_4732408561172474784[28] = 0;
   out_4732408561172474784[29] = 0;
   out_4732408561172474784[30] = 0;
   out_4732408561172474784[31] = 0;
   out_4732408561172474784[32] = 0;
   out_4732408561172474784[33] = 0;
   out_4732408561172474784[34] = 0;
   out_4732408561172474784[35] = 0;
   out_4732408561172474784[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4732408561172474784[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4732408561172474784[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4732408561172474784[39] = 0;
   out_4732408561172474784[40] = 0;
   out_4732408561172474784[41] = 0;
   out_4732408561172474784[42] = 0;
   out_4732408561172474784[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4732408561172474784[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4732408561172474784[45] = 0;
   out_4732408561172474784[46] = 0;
   out_4732408561172474784[47] = 0;
   out_4732408561172474784[48] = 0;
   out_4732408561172474784[49] = 0;
   out_4732408561172474784[50] = 0;
   out_4732408561172474784[51] = 0;
   out_4732408561172474784[52] = 0;
   out_4732408561172474784[53] = 0;
   out_4732408561172474784[54] = 0;
   out_4732408561172474784[55] = 0;
   out_4732408561172474784[56] = 0;
   out_4732408561172474784[57] = 1;
   out_4732408561172474784[58] = 0;
   out_4732408561172474784[59] = 0;
   out_4732408561172474784[60] = 0;
   out_4732408561172474784[61] = 0;
   out_4732408561172474784[62] = 0;
   out_4732408561172474784[63] = 0;
   out_4732408561172474784[64] = 0;
   out_4732408561172474784[65] = 0;
   out_4732408561172474784[66] = dt;
   out_4732408561172474784[67] = 0;
   out_4732408561172474784[68] = 0;
   out_4732408561172474784[69] = 0;
   out_4732408561172474784[70] = 0;
   out_4732408561172474784[71] = 0;
   out_4732408561172474784[72] = 0;
   out_4732408561172474784[73] = 0;
   out_4732408561172474784[74] = 0;
   out_4732408561172474784[75] = 0;
   out_4732408561172474784[76] = 1;
   out_4732408561172474784[77] = 0;
   out_4732408561172474784[78] = 0;
   out_4732408561172474784[79] = 0;
   out_4732408561172474784[80] = 0;
   out_4732408561172474784[81] = 0;
   out_4732408561172474784[82] = 0;
   out_4732408561172474784[83] = 0;
   out_4732408561172474784[84] = 0;
   out_4732408561172474784[85] = dt;
   out_4732408561172474784[86] = 0;
   out_4732408561172474784[87] = 0;
   out_4732408561172474784[88] = 0;
   out_4732408561172474784[89] = 0;
   out_4732408561172474784[90] = 0;
   out_4732408561172474784[91] = 0;
   out_4732408561172474784[92] = 0;
   out_4732408561172474784[93] = 0;
   out_4732408561172474784[94] = 0;
   out_4732408561172474784[95] = 1;
   out_4732408561172474784[96] = 0;
   out_4732408561172474784[97] = 0;
   out_4732408561172474784[98] = 0;
   out_4732408561172474784[99] = 0;
   out_4732408561172474784[100] = 0;
   out_4732408561172474784[101] = 0;
   out_4732408561172474784[102] = 0;
   out_4732408561172474784[103] = 0;
   out_4732408561172474784[104] = dt;
   out_4732408561172474784[105] = 0;
   out_4732408561172474784[106] = 0;
   out_4732408561172474784[107] = 0;
   out_4732408561172474784[108] = 0;
   out_4732408561172474784[109] = 0;
   out_4732408561172474784[110] = 0;
   out_4732408561172474784[111] = 0;
   out_4732408561172474784[112] = 0;
   out_4732408561172474784[113] = 0;
   out_4732408561172474784[114] = 1;
   out_4732408561172474784[115] = 0;
   out_4732408561172474784[116] = 0;
   out_4732408561172474784[117] = 0;
   out_4732408561172474784[118] = 0;
   out_4732408561172474784[119] = 0;
   out_4732408561172474784[120] = 0;
   out_4732408561172474784[121] = 0;
   out_4732408561172474784[122] = 0;
   out_4732408561172474784[123] = 0;
   out_4732408561172474784[124] = 0;
   out_4732408561172474784[125] = 0;
   out_4732408561172474784[126] = 0;
   out_4732408561172474784[127] = 0;
   out_4732408561172474784[128] = 0;
   out_4732408561172474784[129] = 0;
   out_4732408561172474784[130] = 0;
   out_4732408561172474784[131] = 0;
   out_4732408561172474784[132] = 0;
   out_4732408561172474784[133] = 1;
   out_4732408561172474784[134] = 0;
   out_4732408561172474784[135] = 0;
   out_4732408561172474784[136] = 0;
   out_4732408561172474784[137] = 0;
   out_4732408561172474784[138] = 0;
   out_4732408561172474784[139] = 0;
   out_4732408561172474784[140] = 0;
   out_4732408561172474784[141] = 0;
   out_4732408561172474784[142] = 0;
   out_4732408561172474784[143] = 0;
   out_4732408561172474784[144] = 0;
   out_4732408561172474784[145] = 0;
   out_4732408561172474784[146] = 0;
   out_4732408561172474784[147] = 0;
   out_4732408561172474784[148] = 0;
   out_4732408561172474784[149] = 0;
   out_4732408561172474784[150] = 0;
   out_4732408561172474784[151] = 0;
   out_4732408561172474784[152] = 1;
   out_4732408561172474784[153] = 0;
   out_4732408561172474784[154] = 0;
   out_4732408561172474784[155] = 0;
   out_4732408561172474784[156] = 0;
   out_4732408561172474784[157] = 0;
   out_4732408561172474784[158] = 0;
   out_4732408561172474784[159] = 0;
   out_4732408561172474784[160] = 0;
   out_4732408561172474784[161] = 0;
   out_4732408561172474784[162] = 0;
   out_4732408561172474784[163] = 0;
   out_4732408561172474784[164] = 0;
   out_4732408561172474784[165] = 0;
   out_4732408561172474784[166] = 0;
   out_4732408561172474784[167] = 0;
   out_4732408561172474784[168] = 0;
   out_4732408561172474784[169] = 0;
   out_4732408561172474784[170] = 0;
   out_4732408561172474784[171] = 1;
   out_4732408561172474784[172] = 0;
   out_4732408561172474784[173] = 0;
   out_4732408561172474784[174] = 0;
   out_4732408561172474784[175] = 0;
   out_4732408561172474784[176] = 0;
   out_4732408561172474784[177] = 0;
   out_4732408561172474784[178] = 0;
   out_4732408561172474784[179] = 0;
   out_4732408561172474784[180] = 0;
   out_4732408561172474784[181] = 0;
   out_4732408561172474784[182] = 0;
   out_4732408561172474784[183] = 0;
   out_4732408561172474784[184] = 0;
   out_4732408561172474784[185] = 0;
   out_4732408561172474784[186] = 0;
   out_4732408561172474784[187] = 0;
   out_4732408561172474784[188] = 0;
   out_4732408561172474784[189] = 0;
   out_4732408561172474784[190] = 1;
   out_4732408561172474784[191] = 0;
   out_4732408561172474784[192] = 0;
   out_4732408561172474784[193] = 0;
   out_4732408561172474784[194] = 0;
   out_4732408561172474784[195] = 0;
   out_4732408561172474784[196] = 0;
   out_4732408561172474784[197] = 0;
   out_4732408561172474784[198] = 0;
   out_4732408561172474784[199] = 0;
   out_4732408561172474784[200] = 0;
   out_4732408561172474784[201] = 0;
   out_4732408561172474784[202] = 0;
   out_4732408561172474784[203] = 0;
   out_4732408561172474784[204] = 0;
   out_4732408561172474784[205] = 0;
   out_4732408561172474784[206] = 0;
   out_4732408561172474784[207] = 0;
   out_4732408561172474784[208] = 0;
   out_4732408561172474784[209] = 1;
   out_4732408561172474784[210] = 0;
   out_4732408561172474784[211] = 0;
   out_4732408561172474784[212] = 0;
   out_4732408561172474784[213] = 0;
   out_4732408561172474784[214] = 0;
   out_4732408561172474784[215] = 0;
   out_4732408561172474784[216] = 0;
   out_4732408561172474784[217] = 0;
   out_4732408561172474784[218] = 0;
   out_4732408561172474784[219] = 0;
   out_4732408561172474784[220] = 0;
   out_4732408561172474784[221] = 0;
   out_4732408561172474784[222] = 0;
   out_4732408561172474784[223] = 0;
   out_4732408561172474784[224] = 0;
   out_4732408561172474784[225] = 0;
   out_4732408561172474784[226] = 0;
   out_4732408561172474784[227] = 0;
   out_4732408561172474784[228] = 1;
   out_4732408561172474784[229] = 0;
   out_4732408561172474784[230] = 0;
   out_4732408561172474784[231] = 0;
   out_4732408561172474784[232] = 0;
   out_4732408561172474784[233] = 0;
   out_4732408561172474784[234] = 0;
   out_4732408561172474784[235] = 0;
   out_4732408561172474784[236] = 0;
   out_4732408561172474784[237] = 0;
   out_4732408561172474784[238] = 0;
   out_4732408561172474784[239] = 0;
   out_4732408561172474784[240] = 0;
   out_4732408561172474784[241] = 0;
   out_4732408561172474784[242] = 0;
   out_4732408561172474784[243] = 0;
   out_4732408561172474784[244] = 0;
   out_4732408561172474784[245] = 0;
   out_4732408561172474784[246] = 0;
   out_4732408561172474784[247] = 1;
   out_4732408561172474784[248] = 0;
   out_4732408561172474784[249] = 0;
   out_4732408561172474784[250] = 0;
   out_4732408561172474784[251] = 0;
   out_4732408561172474784[252] = 0;
   out_4732408561172474784[253] = 0;
   out_4732408561172474784[254] = 0;
   out_4732408561172474784[255] = 0;
   out_4732408561172474784[256] = 0;
   out_4732408561172474784[257] = 0;
   out_4732408561172474784[258] = 0;
   out_4732408561172474784[259] = 0;
   out_4732408561172474784[260] = 0;
   out_4732408561172474784[261] = 0;
   out_4732408561172474784[262] = 0;
   out_4732408561172474784[263] = 0;
   out_4732408561172474784[264] = 0;
   out_4732408561172474784[265] = 0;
   out_4732408561172474784[266] = 1;
   out_4732408561172474784[267] = 0;
   out_4732408561172474784[268] = 0;
   out_4732408561172474784[269] = 0;
   out_4732408561172474784[270] = 0;
   out_4732408561172474784[271] = 0;
   out_4732408561172474784[272] = 0;
   out_4732408561172474784[273] = 0;
   out_4732408561172474784[274] = 0;
   out_4732408561172474784[275] = 0;
   out_4732408561172474784[276] = 0;
   out_4732408561172474784[277] = 0;
   out_4732408561172474784[278] = 0;
   out_4732408561172474784[279] = 0;
   out_4732408561172474784[280] = 0;
   out_4732408561172474784[281] = 0;
   out_4732408561172474784[282] = 0;
   out_4732408561172474784[283] = 0;
   out_4732408561172474784[284] = 0;
   out_4732408561172474784[285] = 1;
   out_4732408561172474784[286] = 0;
   out_4732408561172474784[287] = 0;
   out_4732408561172474784[288] = 0;
   out_4732408561172474784[289] = 0;
   out_4732408561172474784[290] = 0;
   out_4732408561172474784[291] = 0;
   out_4732408561172474784[292] = 0;
   out_4732408561172474784[293] = 0;
   out_4732408561172474784[294] = 0;
   out_4732408561172474784[295] = 0;
   out_4732408561172474784[296] = 0;
   out_4732408561172474784[297] = 0;
   out_4732408561172474784[298] = 0;
   out_4732408561172474784[299] = 0;
   out_4732408561172474784[300] = 0;
   out_4732408561172474784[301] = 0;
   out_4732408561172474784[302] = 0;
   out_4732408561172474784[303] = 0;
   out_4732408561172474784[304] = 1;
   out_4732408561172474784[305] = 0;
   out_4732408561172474784[306] = 0;
   out_4732408561172474784[307] = 0;
   out_4732408561172474784[308] = 0;
   out_4732408561172474784[309] = 0;
   out_4732408561172474784[310] = 0;
   out_4732408561172474784[311] = 0;
   out_4732408561172474784[312] = 0;
   out_4732408561172474784[313] = 0;
   out_4732408561172474784[314] = 0;
   out_4732408561172474784[315] = 0;
   out_4732408561172474784[316] = 0;
   out_4732408561172474784[317] = 0;
   out_4732408561172474784[318] = 0;
   out_4732408561172474784[319] = 0;
   out_4732408561172474784[320] = 0;
   out_4732408561172474784[321] = 0;
   out_4732408561172474784[322] = 0;
   out_4732408561172474784[323] = 1;
}
void h_4(double *state, double *unused, double *out_6918932125970712407) {
   out_6918932125970712407[0] = state[6] + state[9];
   out_6918932125970712407[1] = state[7] + state[10];
   out_6918932125970712407[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_1564971099026927671) {
   out_1564971099026927671[0] = 0;
   out_1564971099026927671[1] = 0;
   out_1564971099026927671[2] = 0;
   out_1564971099026927671[3] = 0;
   out_1564971099026927671[4] = 0;
   out_1564971099026927671[5] = 0;
   out_1564971099026927671[6] = 1;
   out_1564971099026927671[7] = 0;
   out_1564971099026927671[8] = 0;
   out_1564971099026927671[9] = 1;
   out_1564971099026927671[10] = 0;
   out_1564971099026927671[11] = 0;
   out_1564971099026927671[12] = 0;
   out_1564971099026927671[13] = 0;
   out_1564971099026927671[14] = 0;
   out_1564971099026927671[15] = 0;
   out_1564971099026927671[16] = 0;
   out_1564971099026927671[17] = 0;
   out_1564971099026927671[18] = 0;
   out_1564971099026927671[19] = 0;
   out_1564971099026927671[20] = 0;
   out_1564971099026927671[21] = 0;
   out_1564971099026927671[22] = 0;
   out_1564971099026927671[23] = 0;
   out_1564971099026927671[24] = 0;
   out_1564971099026927671[25] = 1;
   out_1564971099026927671[26] = 0;
   out_1564971099026927671[27] = 0;
   out_1564971099026927671[28] = 1;
   out_1564971099026927671[29] = 0;
   out_1564971099026927671[30] = 0;
   out_1564971099026927671[31] = 0;
   out_1564971099026927671[32] = 0;
   out_1564971099026927671[33] = 0;
   out_1564971099026927671[34] = 0;
   out_1564971099026927671[35] = 0;
   out_1564971099026927671[36] = 0;
   out_1564971099026927671[37] = 0;
   out_1564971099026927671[38] = 0;
   out_1564971099026927671[39] = 0;
   out_1564971099026927671[40] = 0;
   out_1564971099026927671[41] = 0;
   out_1564971099026927671[42] = 0;
   out_1564971099026927671[43] = 0;
   out_1564971099026927671[44] = 1;
   out_1564971099026927671[45] = 0;
   out_1564971099026927671[46] = 0;
   out_1564971099026927671[47] = 1;
   out_1564971099026927671[48] = 0;
   out_1564971099026927671[49] = 0;
   out_1564971099026927671[50] = 0;
   out_1564971099026927671[51] = 0;
   out_1564971099026927671[52] = 0;
   out_1564971099026927671[53] = 0;
}
void h_10(double *state, double *unused, double *out_3027582300414544631) {
   out_3027582300414544631[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_3027582300414544631[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_3027582300414544631[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_3487027415066723561) {
   out_3487027415066723561[0] = 0;
   out_3487027415066723561[1] = 9.8100000000000005*cos(state[1]);
   out_3487027415066723561[2] = 0;
   out_3487027415066723561[3] = 0;
   out_3487027415066723561[4] = -state[8];
   out_3487027415066723561[5] = state[7];
   out_3487027415066723561[6] = 0;
   out_3487027415066723561[7] = state[5];
   out_3487027415066723561[8] = -state[4];
   out_3487027415066723561[9] = 0;
   out_3487027415066723561[10] = 0;
   out_3487027415066723561[11] = 0;
   out_3487027415066723561[12] = 1;
   out_3487027415066723561[13] = 0;
   out_3487027415066723561[14] = 0;
   out_3487027415066723561[15] = 1;
   out_3487027415066723561[16] = 0;
   out_3487027415066723561[17] = 0;
   out_3487027415066723561[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_3487027415066723561[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_3487027415066723561[20] = 0;
   out_3487027415066723561[21] = state[8];
   out_3487027415066723561[22] = 0;
   out_3487027415066723561[23] = -state[6];
   out_3487027415066723561[24] = -state[5];
   out_3487027415066723561[25] = 0;
   out_3487027415066723561[26] = state[3];
   out_3487027415066723561[27] = 0;
   out_3487027415066723561[28] = 0;
   out_3487027415066723561[29] = 0;
   out_3487027415066723561[30] = 0;
   out_3487027415066723561[31] = 1;
   out_3487027415066723561[32] = 0;
   out_3487027415066723561[33] = 0;
   out_3487027415066723561[34] = 1;
   out_3487027415066723561[35] = 0;
   out_3487027415066723561[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_3487027415066723561[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_3487027415066723561[38] = 0;
   out_3487027415066723561[39] = -state[7];
   out_3487027415066723561[40] = state[6];
   out_3487027415066723561[41] = 0;
   out_3487027415066723561[42] = state[4];
   out_3487027415066723561[43] = -state[3];
   out_3487027415066723561[44] = 0;
   out_3487027415066723561[45] = 0;
   out_3487027415066723561[46] = 0;
   out_3487027415066723561[47] = 0;
   out_3487027415066723561[48] = 0;
   out_3487027415066723561[49] = 0;
   out_3487027415066723561[50] = 1;
   out_3487027415066723561[51] = 0;
   out_3487027415066723561[52] = 0;
   out_3487027415066723561[53] = 1;
}
void h_13(double *state, double *unused, double *out_4493446518496679699) {
   out_4493446518496679699[0] = state[3];
   out_4493446518496679699[1] = state[4];
   out_4493446518496679699[2] = state[5];
}
void H_13(double *state, double *unused, double *out_1647302726305405130) {
   out_1647302726305405130[0] = 0;
   out_1647302726305405130[1] = 0;
   out_1647302726305405130[2] = 0;
   out_1647302726305405130[3] = 1;
   out_1647302726305405130[4] = 0;
   out_1647302726305405130[5] = 0;
   out_1647302726305405130[6] = 0;
   out_1647302726305405130[7] = 0;
   out_1647302726305405130[8] = 0;
   out_1647302726305405130[9] = 0;
   out_1647302726305405130[10] = 0;
   out_1647302726305405130[11] = 0;
   out_1647302726305405130[12] = 0;
   out_1647302726305405130[13] = 0;
   out_1647302726305405130[14] = 0;
   out_1647302726305405130[15] = 0;
   out_1647302726305405130[16] = 0;
   out_1647302726305405130[17] = 0;
   out_1647302726305405130[18] = 0;
   out_1647302726305405130[19] = 0;
   out_1647302726305405130[20] = 0;
   out_1647302726305405130[21] = 0;
   out_1647302726305405130[22] = 1;
   out_1647302726305405130[23] = 0;
   out_1647302726305405130[24] = 0;
   out_1647302726305405130[25] = 0;
   out_1647302726305405130[26] = 0;
   out_1647302726305405130[27] = 0;
   out_1647302726305405130[28] = 0;
   out_1647302726305405130[29] = 0;
   out_1647302726305405130[30] = 0;
   out_1647302726305405130[31] = 0;
   out_1647302726305405130[32] = 0;
   out_1647302726305405130[33] = 0;
   out_1647302726305405130[34] = 0;
   out_1647302726305405130[35] = 0;
   out_1647302726305405130[36] = 0;
   out_1647302726305405130[37] = 0;
   out_1647302726305405130[38] = 0;
   out_1647302726305405130[39] = 0;
   out_1647302726305405130[40] = 0;
   out_1647302726305405130[41] = 1;
   out_1647302726305405130[42] = 0;
   out_1647302726305405130[43] = 0;
   out_1647302726305405130[44] = 0;
   out_1647302726305405130[45] = 0;
   out_1647302726305405130[46] = 0;
   out_1647302726305405130[47] = 0;
   out_1647302726305405130[48] = 0;
   out_1647302726305405130[49] = 0;
   out_1647302726305405130[50] = 0;
   out_1647302726305405130[51] = 0;
   out_1647302726305405130[52] = 0;
   out_1647302726305405130[53] = 0;
}
void h_14(double *state, double *unused, double *out_507113954569858993) {
   out_507113954569858993[0] = state[6];
   out_507113954569858993[1] = state[7];
   out_507113954569858993[2] = state[8];
}
void H_14(double *state, double *unused, double *out_2398269757312556858) {
   out_2398269757312556858[0] = 0;
   out_2398269757312556858[1] = 0;
   out_2398269757312556858[2] = 0;
   out_2398269757312556858[3] = 0;
   out_2398269757312556858[4] = 0;
   out_2398269757312556858[5] = 0;
   out_2398269757312556858[6] = 1;
   out_2398269757312556858[7] = 0;
   out_2398269757312556858[8] = 0;
   out_2398269757312556858[9] = 0;
   out_2398269757312556858[10] = 0;
   out_2398269757312556858[11] = 0;
   out_2398269757312556858[12] = 0;
   out_2398269757312556858[13] = 0;
   out_2398269757312556858[14] = 0;
   out_2398269757312556858[15] = 0;
   out_2398269757312556858[16] = 0;
   out_2398269757312556858[17] = 0;
   out_2398269757312556858[18] = 0;
   out_2398269757312556858[19] = 0;
   out_2398269757312556858[20] = 0;
   out_2398269757312556858[21] = 0;
   out_2398269757312556858[22] = 0;
   out_2398269757312556858[23] = 0;
   out_2398269757312556858[24] = 0;
   out_2398269757312556858[25] = 1;
   out_2398269757312556858[26] = 0;
   out_2398269757312556858[27] = 0;
   out_2398269757312556858[28] = 0;
   out_2398269757312556858[29] = 0;
   out_2398269757312556858[30] = 0;
   out_2398269757312556858[31] = 0;
   out_2398269757312556858[32] = 0;
   out_2398269757312556858[33] = 0;
   out_2398269757312556858[34] = 0;
   out_2398269757312556858[35] = 0;
   out_2398269757312556858[36] = 0;
   out_2398269757312556858[37] = 0;
   out_2398269757312556858[38] = 0;
   out_2398269757312556858[39] = 0;
   out_2398269757312556858[40] = 0;
   out_2398269757312556858[41] = 0;
   out_2398269757312556858[42] = 0;
   out_2398269757312556858[43] = 0;
   out_2398269757312556858[44] = 1;
   out_2398269757312556858[45] = 0;
   out_2398269757312556858[46] = 0;
   out_2398269757312556858[47] = 0;
   out_2398269757312556858[48] = 0;
   out_2398269757312556858[49] = 0;
   out_2398269757312556858[50] = 0;
   out_2398269757312556858[51] = 0;
   out_2398269757312556858[52] = 0;
   out_2398269757312556858[53] = 0;
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
void pose_err_fun(double *nom_x, double *delta_x, double *out_8714848832990626554) {
  err_fun(nom_x, delta_x, out_8714848832990626554);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_5047671582975253903) {
  inv_err_fun(nom_x, true_x, out_5047671582975253903);
}
void pose_H_mod_fun(double *state, double *out_1709250979764021582) {
  H_mod_fun(state, out_1709250979764021582);
}
void pose_f_fun(double *state, double dt, double *out_1316099113648689196) {
  f_fun(state,  dt, out_1316099113648689196);
}
void pose_F_fun(double *state, double dt, double *out_4732408561172474784) {
  F_fun(state,  dt, out_4732408561172474784);
}
void pose_h_4(double *state, double *unused, double *out_6918932125970712407) {
  h_4(state, unused, out_6918932125970712407);
}
void pose_H_4(double *state, double *unused, double *out_1564971099026927671) {
  H_4(state, unused, out_1564971099026927671);
}
void pose_h_10(double *state, double *unused, double *out_3027582300414544631) {
  h_10(state, unused, out_3027582300414544631);
}
void pose_H_10(double *state, double *unused, double *out_3487027415066723561) {
  H_10(state, unused, out_3487027415066723561);
}
void pose_h_13(double *state, double *unused, double *out_4493446518496679699) {
  h_13(state, unused, out_4493446518496679699);
}
void pose_H_13(double *state, double *unused, double *out_1647302726305405130) {
  H_13(state, unused, out_1647302726305405130);
}
void pose_h_14(double *state, double *unused, double *out_507113954569858993) {
  h_14(state, unused, out_507113954569858993);
}
void pose_H_14(double *state, double *unused, double *out_2398269757312556858) {
  H_14(state, unused, out_2398269757312556858);
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
