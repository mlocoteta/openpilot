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
void err_fun(double *nom_x, double *delta_x, double *out_3211789106073125283) {
   out_3211789106073125283[0] = delta_x[0] + nom_x[0];
   out_3211789106073125283[1] = delta_x[1] + nom_x[1];
   out_3211789106073125283[2] = delta_x[2] + nom_x[2];
   out_3211789106073125283[3] = delta_x[3] + nom_x[3];
   out_3211789106073125283[4] = delta_x[4] + nom_x[4];
   out_3211789106073125283[5] = delta_x[5] + nom_x[5];
   out_3211789106073125283[6] = delta_x[6] + nom_x[6];
   out_3211789106073125283[7] = delta_x[7] + nom_x[7];
   out_3211789106073125283[8] = delta_x[8] + nom_x[8];
   out_3211789106073125283[9] = delta_x[9] + nom_x[9];
   out_3211789106073125283[10] = delta_x[10] + nom_x[10];
   out_3211789106073125283[11] = delta_x[11] + nom_x[11];
   out_3211789106073125283[12] = delta_x[12] + nom_x[12];
   out_3211789106073125283[13] = delta_x[13] + nom_x[13];
   out_3211789106073125283[14] = delta_x[14] + nom_x[14];
   out_3211789106073125283[15] = delta_x[15] + nom_x[15];
   out_3211789106073125283[16] = delta_x[16] + nom_x[16];
   out_3211789106073125283[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_6226563961506943969) {
   out_6226563961506943969[0] = -nom_x[0] + true_x[0];
   out_6226563961506943969[1] = -nom_x[1] + true_x[1];
   out_6226563961506943969[2] = -nom_x[2] + true_x[2];
   out_6226563961506943969[3] = -nom_x[3] + true_x[3];
   out_6226563961506943969[4] = -nom_x[4] + true_x[4];
   out_6226563961506943969[5] = -nom_x[5] + true_x[5];
   out_6226563961506943969[6] = -nom_x[6] + true_x[6];
   out_6226563961506943969[7] = -nom_x[7] + true_x[7];
   out_6226563961506943969[8] = -nom_x[8] + true_x[8];
   out_6226563961506943969[9] = -nom_x[9] + true_x[9];
   out_6226563961506943969[10] = -nom_x[10] + true_x[10];
   out_6226563961506943969[11] = -nom_x[11] + true_x[11];
   out_6226563961506943969[12] = -nom_x[12] + true_x[12];
   out_6226563961506943969[13] = -nom_x[13] + true_x[13];
   out_6226563961506943969[14] = -nom_x[14] + true_x[14];
   out_6226563961506943969[15] = -nom_x[15] + true_x[15];
   out_6226563961506943969[16] = -nom_x[16] + true_x[16];
   out_6226563961506943969[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_5161461913541420634) {
   out_5161461913541420634[0] = 1.0;
   out_5161461913541420634[1] = 0.0;
   out_5161461913541420634[2] = 0.0;
   out_5161461913541420634[3] = 0.0;
   out_5161461913541420634[4] = 0.0;
   out_5161461913541420634[5] = 0.0;
   out_5161461913541420634[6] = 0.0;
   out_5161461913541420634[7] = 0.0;
   out_5161461913541420634[8] = 0.0;
   out_5161461913541420634[9] = 0.0;
   out_5161461913541420634[10] = 0.0;
   out_5161461913541420634[11] = 0.0;
   out_5161461913541420634[12] = 0.0;
   out_5161461913541420634[13] = 0.0;
   out_5161461913541420634[14] = 0.0;
   out_5161461913541420634[15] = 0.0;
   out_5161461913541420634[16] = 0.0;
   out_5161461913541420634[17] = 0.0;
   out_5161461913541420634[18] = 0.0;
   out_5161461913541420634[19] = 1.0;
   out_5161461913541420634[20] = 0.0;
   out_5161461913541420634[21] = 0.0;
   out_5161461913541420634[22] = 0.0;
   out_5161461913541420634[23] = 0.0;
   out_5161461913541420634[24] = 0.0;
   out_5161461913541420634[25] = 0.0;
   out_5161461913541420634[26] = 0.0;
   out_5161461913541420634[27] = 0.0;
   out_5161461913541420634[28] = 0.0;
   out_5161461913541420634[29] = 0.0;
   out_5161461913541420634[30] = 0.0;
   out_5161461913541420634[31] = 0.0;
   out_5161461913541420634[32] = 0.0;
   out_5161461913541420634[33] = 0.0;
   out_5161461913541420634[34] = 0.0;
   out_5161461913541420634[35] = 0.0;
   out_5161461913541420634[36] = 0.0;
   out_5161461913541420634[37] = 0.0;
   out_5161461913541420634[38] = 1.0;
   out_5161461913541420634[39] = 0.0;
   out_5161461913541420634[40] = 0.0;
   out_5161461913541420634[41] = 0.0;
   out_5161461913541420634[42] = 0.0;
   out_5161461913541420634[43] = 0.0;
   out_5161461913541420634[44] = 0.0;
   out_5161461913541420634[45] = 0.0;
   out_5161461913541420634[46] = 0.0;
   out_5161461913541420634[47] = 0.0;
   out_5161461913541420634[48] = 0.0;
   out_5161461913541420634[49] = 0.0;
   out_5161461913541420634[50] = 0.0;
   out_5161461913541420634[51] = 0.0;
   out_5161461913541420634[52] = 0.0;
   out_5161461913541420634[53] = 0.0;
   out_5161461913541420634[54] = 0.0;
   out_5161461913541420634[55] = 0.0;
   out_5161461913541420634[56] = 0.0;
   out_5161461913541420634[57] = 1.0;
   out_5161461913541420634[58] = 0.0;
   out_5161461913541420634[59] = 0.0;
   out_5161461913541420634[60] = 0.0;
   out_5161461913541420634[61] = 0.0;
   out_5161461913541420634[62] = 0.0;
   out_5161461913541420634[63] = 0.0;
   out_5161461913541420634[64] = 0.0;
   out_5161461913541420634[65] = 0.0;
   out_5161461913541420634[66] = 0.0;
   out_5161461913541420634[67] = 0.0;
   out_5161461913541420634[68] = 0.0;
   out_5161461913541420634[69] = 0.0;
   out_5161461913541420634[70] = 0.0;
   out_5161461913541420634[71] = 0.0;
   out_5161461913541420634[72] = 0.0;
   out_5161461913541420634[73] = 0.0;
   out_5161461913541420634[74] = 0.0;
   out_5161461913541420634[75] = 0.0;
   out_5161461913541420634[76] = 1.0;
   out_5161461913541420634[77] = 0.0;
   out_5161461913541420634[78] = 0.0;
   out_5161461913541420634[79] = 0.0;
   out_5161461913541420634[80] = 0.0;
   out_5161461913541420634[81] = 0.0;
   out_5161461913541420634[82] = 0.0;
   out_5161461913541420634[83] = 0.0;
   out_5161461913541420634[84] = 0.0;
   out_5161461913541420634[85] = 0.0;
   out_5161461913541420634[86] = 0.0;
   out_5161461913541420634[87] = 0.0;
   out_5161461913541420634[88] = 0.0;
   out_5161461913541420634[89] = 0.0;
   out_5161461913541420634[90] = 0.0;
   out_5161461913541420634[91] = 0.0;
   out_5161461913541420634[92] = 0.0;
   out_5161461913541420634[93] = 0.0;
   out_5161461913541420634[94] = 0.0;
   out_5161461913541420634[95] = 1.0;
   out_5161461913541420634[96] = 0.0;
   out_5161461913541420634[97] = 0.0;
   out_5161461913541420634[98] = 0.0;
   out_5161461913541420634[99] = 0.0;
   out_5161461913541420634[100] = 0.0;
   out_5161461913541420634[101] = 0.0;
   out_5161461913541420634[102] = 0.0;
   out_5161461913541420634[103] = 0.0;
   out_5161461913541420634[104] = 0.0;
   out_5161461913541420634[105] = 0.0;
   out_5161461913541420634[106] = 0.0;
   out_5161461913541420634[107] = 0.0;
   out_5161461913541420634[108] = 0.0;
   out_5161461913541420634[109] = 0.0;
   out_5161461913541420634[110] = 0.0;
   out_5161461913541420634[111] = 0.0;
   out_5161461913541420634[112] = 0.0;
   out_5161461913541420634[113] = 0.0;
   out_5161461913541420634[114] = 1.0;
   out_5161461913541420634[115] = 0.0;
   out_5161461913541420634[116] = 0.0;
   out_5161461913541420634[117] = 0.0;
   out_5161461913541420634[118] = 0.0;
   out_5161461913541420634[119] = 0.0;
   out_5161461913541420634[120] = 0.0;
   out_5161461913541420634[121] = 0.0;
   out_5161461913541420634[122] = 0.0;
   out_5161461913541420634[123] = 0.0;
   out_5161461913541420634[124] = 0.0;
   out_5161461913541420634[125] = 0.0;
   out_5161461913541420634[126] = 0.0;
   out_5161461913541420634[127] = 0.0;
   out_5161461913541420634[128] = 0.0;
   out_5161461913541420634[129] = 0.0;
   out_5161461913541420634[130] = 0.0;
   out_5161461913541420634[131] = 0.0;
   out_5161461913541420634[132] = 0.0;
   out_5161461913541420634[133] = 1.0;
   out_5161461913541420634[134] = 0.0;
   out_5161461913541420634[135] = 0.0;
   out_5161461913541420634[136] = 0.0;
   out_5161461913541420634[137] = 0.0;
   out_5161461913541420634[138] = 0.0;
   out_5161461913541420634[139] = 0.0;
   out_5161461913541420634[140] = 0.0;
   out_5161461913541420634[141] = 0.0;
   out_5161461913541420634[142] = 0.0;
   out_5161461913541420634[143] = 0.0;
   out_5161461913541420634[144] = 0.0;
   out_5161461913541420634[145] = 0.0;
   out_5161461913541420634[146] = 0.0;
   out_5161461913541420634[147] = 0.0;
   out_5161461913541420634[148] = 0.0;
   out_5161461913541420634[149] = 0.0;
   out_5161461913541420634[150] = 0.0;
   out_5161461913541420634[151] = 0.0;
   out_5161461913541420634[152] = 1.0;
   out_5161461913541420634[153] = 0.0;
   out_5161461913541420634[154] = 0.0;
   out_5161461913541420634[155] = 0.0;
   out_5161461913541420634[156] = 0.0;
   out_5161461913541420634[157] = 0.0;
   out_5161461913541420634[158] = 0.0;
   out_5161461913541420634[159] = 0.0;
   out_5161461913541420634[160] = 0.0;
   out_5161461913541420634[161] = 0.0;
   out_5161461913541420634[162] = 0.0;
   out_5161461913541420634[163] = 0.0;
   out_5161461913541420634[164] = 0.0;
   out_5161461913541420634[165] = 0.0;
   out_5161461913541420634[166] = 0.0;
   out_5161461913541420634[167] = 0.0;
   out_5161461913541420634[168] = 0.0;
   out_5161461913541420634[169] = 0.0;
   out_5161461913541420634[170] = 0.0;
   out_5161461913541420634[171] = 1.0;
   out_5161461913541420634[172] = 0.0;
   out_5161461913541420634[173] = 0.0;
   out_5161461913541420634[174] = 0.0;
   out_5161461913541420634[175] = 0.0;
   out_5161461913541420634[176] = 0.0;
   out_5161461913541420634[177] = 0.0;
   out_5161461913541420634[178] = 0.0;
   out_5161461913541420634[179] = 0.0;
   out_5161461913541420634[180] = 0.0;
   out_5161461913541420634[181] = 0.0;
   out_5161461913541420634[182] = 0.0;
   out_5161461913541420634[183] = 0.0;
   out_5161461913541420634[184] = 0.0;
   out_5161461913541420634[185] = 0.0;
   out_5161461913541420634[186] = 0.0;
   out_5161461913541420634[187] = 0.0;
   out_5161461913541420634[188] = 0.0;
   out_5161461913541420634[189] = 0.0;
   out_5161461913541420634[190] = 1.0;
   out_5161461913541420634[191] = 0.0;
   out_5161461913541420634[192] = 0.0;
   out_5161461913541420634[193] = 0.0;
   out_5161461913541420634[194] = 0.0;
   out_5161461913541420634[195] = 0.0;
   out_5161461913541420634[196] = 0.0;
   out_5161461913541420634[197] = 0.0;
   out_5161461913541420634[198] = 0.0;
   out_5161461913541420634[199] = 0.0;
   out_5161461913541420634[200] = 0.0;
   out_5161461913541420634[201] = 0.0;
   out_5161461913541420634[202] = 0.0;
   out_5161461913541420634[203] = 0.0;
   out_5161461913541420634[204] = 0.0;
   out_5161461913541420634[205] = 0.0;
   out_5161461913541420634[206] = 0.0;
   out_5161461913541420634[207] = 0.0;
   out_5161461913541420634[208] = 0.0;
   out_5161461913541420634[209] = 1.0;
   out_5161461913541420634[210] = 0.0;
   out_5161461913541420634[211] = 0.0;
   out_5161461913541420634[212] = 0.0;
   out_5161461913541420634[213] = 0.0;
   out_5161461913541420634[214] = 0.0;
   out_5161461913541420634[215] = 0.0;
   out_5161461913541420634[216] = 0.0;
   out_5161461913541420634[217] = 0.0;
   out_5161461913541420634[218] = 0.0;
   out_5161461913541420634[219] = 0.0;
   out_5161461913541420634[220] = 0.0;
   out_5161461913541420634[221] = 0.0;
   out_5161461913541420634[222] = 0.0;
   out_5161461913541420634[223] = 0.0;
   out_5161461913541420634[224] = 0.0;
   out_5161461913541420634[225] = 0.0;
   out_5161461913541420634[226] = 0.0;
   out_5161461913541420634[227] = 0.0;
   out_5161461913541420634[228] = 1.0;
   out_5161461913541420634[229] = 0.0;
   out_5161461913541420634[230] = 0.0;
   out_5161461913541420634[231] = 0.0;
   out_5161461913541420634[232] = 0.0;
   out_5161461913541420634[233] = 0.0;
   out_5161461913541420634[234] = 0.0;
   out_5161461913541420634[235] = 0.0;
   out_5161461913541420634[236] = 0.0;
   out_5161461913541420634[237] = 0.0;
   out_5161461913541420634[238] = 0.0;
   out_5161461913541420634[239] = 0.0;
   out_5161461913541420634[240] = 0.0;
   out_5161461913541420634[241] = 0.0;
   out_5161461913541420634[242] = 0.0;
   out_5161461913541420634[243] = 0.0;
   out_5161461913541420634[244] = 0.0;
   out_5161461913541420634[245] = 0.0;
   out_5161461913541420634[246] = 0.0;
   out_5161461913541420634[247] = 1.0;
   out_5161461913541420634[248] = 0.0;
   out_5161461913541420634[249] = 0.0;
   out_5161461913541420634[250] = 0.0;
   out_5161461913541420634[251] = 0.0;
   out_5161461913541420634[252] = 0.0;
   out_5161461913541420634[253] = 0.0;
   out_5161461913541420634[254] = 0.0;
   out_5161461913541420634[255] = 0.0;
   out_5161461913541420634[256] = 0.0;
   out_5161461913541420634[257] = 0.0;
   out_5161461913541420634[258] = 0.0;
   out_5161461913541420634[259] = 0.0;
   out_5161461913541420634[260] = 0.0;
   out_5161461913541420634[261] = 0.0;
   out_5161461913541420634[262] = 0.0;
   out_5161461913541420634[263] = 0.0;
   out_5161461913541420634[264] = 0.0;
   out_5161461913541420634[265] = 0.0;
   out_5161461913541420634[266] = 1.0;
   out_5161461913541420634[267] = 0.0;
   out_5161461913541420634[268] = 0.0;
   out_5161461913541420634[269] = 0.0;
   out_5161461913541420634[270] = 0.0;
   out_5161461913541420634[271] = 0.0;
   out_5161461913541420634[272] = 0.0;
   out_5161461913541420634[273] = 0.0;
   out_5161461913541420634[274] = 0.0;
   out_5161461913541420634[275] = 0.0;
   out_5161461913541420634[276] = 0.0;
   out_5161461913541420634[277] = 0.0;
   out_5161461913541420634[278] = 0.0;
   out_5161461913541420634[279] = 0.0;
   out_5161461913541420634[280] = 0.0;
   out_5161461913541420634[281] = 0.0;
   out_5161461913541420634[282] = 0.0;
   out_5161461913541420634[283] = 0.0;
   out_5161461913541420634[284] = 0.0;
   out_5161461913541420634[285] = 1.0;
   out_5161461913541420634[286] = 0.0;
   out_5161461913541420634[287] = 0.0;
   out_5161461913541420634[288] = 0.0;
   out_5161461913541420634[289] = 0.0;
   out_5161461913541420634[290] = 0.0;
   out_5161461913541420634[291] = 0.0;
   out_5161461913541420634[292] = 0.0;
   out_5161461913541420634[293] = 0.0;
   out_5161461913541420634[294] = 0.0;
   out_5161461913541420634[295] = 0.0;
   out_5161461913541420634[296] = 0.0;
   out_5161461913541420634[297] = 0.0;
   out_5161461913541420634[298] = 0.0;
   out_5161461913541420634[299] = 0.0;
   out_5161461913541420634[300] = 0.0;
   out_5161461913541420634[301] = 0.0;
   out_5161461913541420634[302] = 0.0;
   out_5161461913541420634[303] = 0.0;
   out_5161461913541420634[304] = 1.0;
   out_5161461913541420634[305] = 0.0;
   out_5161461913541420634[306] = 0.0;
   out_5161461913541420634[307] = 0.0;
   out_5161461913541420634[308] = 0.0;
   out_5161461913541420634[309] = 0.0;
   out_5161461913541420634[310] = 0.0;
   out_5161461913541420634[311] = 0.0;
   out_5161461913541420634[312] = 0.0;
   out_5161461913541420634[313] = 0.0;
   out_5161461913541420634[314] = 0.0;
   out_5161461913541420634[315] = 0.0;
   out_5161461913541420634[316] = 0.0;
   out_5161461913541420634[317] = 0.0;
   out_5161461913541420634[318] = 0.0;
   out_5161461913541420634[319] = 0.0;
   out_5161461913541420634[320] = 0.0;
   out_5161461913541420634[321] = 0.0;
   out_5161461913541420634[322] = 0.0;
   out_5161461913541420634[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_3057528827902898560) {
   out_3057528827902898560[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_3057528827902898560[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_3057528827902898560[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_3057528827902898560[3] = dt*state[12] + state[3];
   out_3057528827902898560[4] = dt*state[13] + state[4];
   out_3057528827902898560[5] = dt*state[14] + state[5];
   out_3057528827902898560[6] = state[6];
   out_3057528827902898560[7] = state[7];
   out_3057528827902898560[8] = state[8];
   out_3057528827902898560[9] = state[9];
   out_3057528827902898560[10] = state[10];
   out_3057528827902898560[11] = state[11];
   out_3057528827902898560[12] = state[12];
   out_3057528827902898560[13] = state[13];
   out_3057528827902898560[14] = state[14];
   out_3057528827902898560[15] = state[15];
   out_3057528827902898560[16] = state[16];
   out_3057528827902898560[17] = state[17];
}
void F_fun(double *state, double dt, double *out_2410705301866754520) {
   out_2410705301866754520[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_2410705301866754520[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_2410705301866754520[2] = 0;
   out_2410705301866754520[3] = 0;
   out_2410705301866754520[4] = 0;
   out_2410705301866754520[5] = 0;
   out_2410705301866754520[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_2410705301866754520[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_2410705301866754520[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_2410705301866754520[9] = 0;
   out_2410705301866754520[10] = 0;
   out_2410705301866754520[11] = 0;
   out_2410705301866754520[12] = 0;
   out_2410705301866754520[13] = 0;
   out_2410705301866754520[14] = 0;
   out_2410705301866754520[15] = 0;
   out_2410705301866754520[16] = 0;
   out_2410705301866754520[17] = 0;
   out_2410705301866754520[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_2410705301866754520[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_2410705301866754520[20] = 0;
   out_2410705301866754520[21] = 0;
   out_2410705301866754520[22] = 0;
   out_2410705301866754520[23] = 0;
   out_2410705301866754520[24] = 0;
   out_2410705301866754520[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_2410705301866754520[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_2410705301866754520[27] = 0;
   out_2410705301866754520[28] = 0;
   out_2410705301866754520[29] = 0;
   out_2410705301866754520[30] = 0;
   out_2410705301866754520[31] = 0;
   out_2410705301866754520[32] = 0;
   out_2410705301866754520[33] = 0;
   out_2410705301866754520[34] = 0;
   out_2410705301866754520[35] = 0;
   out_2410705301866754520[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_2410705301866754520[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_2410705301866754520[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_2410705301866754520[39] = 0;
   out_2410705301866754520[40] = 0;
   out_2410705301866754520[41] = 0;
   out_2410705301866754520[42] = 0;
   out_2410705301866754520[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_2410705301866754520[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_2410705301866754520[45] = 0;
   out_2410705301866754520[46] = 0;
   out_2410705301866754520[47] = 0;
   out_2410705301866754520[48] = 0;
   out_2410705301866754520[49] = 0;
   out_2410705301866754520[50] = 0;
   out_2410705301866754520[51] = 0;
   out_2410705301866754520[52] = 0;
   out_2410705301866754520[53] = 0;
   out_2410705301866754520[54] = 0;
   out_2410705301866754520[55] = 0;
   out_2410705301866754520[56] = 0;
   out_2410705301866754520[57] = 1;
   out_2410705301866754520[58] = 0;
   out_2410705301866754520[59] = 0;
   out_2410705301866754520[60] = 0;
   out_2410705301866754520[61] = 0;
   out_2410705301866754520[62] = 0;
   out_2410705301866754520[63] = 0;
   out_2410705301866754520[64] = 0;
   out_2410705301866754520[65] = 0;
   out_2410705301866754520[66] = dt;
   out_2410705301866754520[67] = 0;
   out_2410705301866754520[68] = 0;
   out_2410705301866754520[69] = 0;
   out_2410705301866754520[70] = 0;
   out_2410705301866754520[71] = 0;
   out_2410705301866754520[72] = 0;
   out_2410705301866754520[73] = 0;
   out_2410705301866754520[74] = 0;
   out_2410705301866754520[75] = 0;
   out_2410705301866754520[76] = 1;
   out_2410705301866754520[77] = 0;
   out_2410705301866754520[78] = 0;
   out_2410705301866754520[79] = 0;
   out_2410705301866754520[80] = 0;
   out_2410705301866754520[81] = 0;
   out_2410705301866754520[82] = 0;
   out_2410705301866754520[83] = 0;
   out_2410705301866754520[84] = 0;
   out_2410705301866754520[85] = dt;
   out_2410705301866754520[86] = 0;
   out_2410705301866754520[87] = 0;
   out_2410705301866754520[88] = 0;
   out_2410705301866754520[89] = 0;
   out_2410705301866754520[90] = 0;
   out_2410705301866754520[91] = 0;
   out_2410705301866754520[92] = 0;
   out_2410705301866754520[93] = 0;
   out_2410705301866754520[94] = 0;
   out_2410705301866754520[95] = 1;
   out_2410705301866754520[96] = 0;
   out_2410705301866754520[97] = 0;
   out_2410705301866754520[98] = 0;
   out_2410705301866754520[99] = 0;
   out_2410705301866754520[100] = 0;
   out_2410705301866754520[101] = 0;
   out_2410705301866754520[102] = 0;
   out_2410705301866754520[103] = 0;
   out_2410705301866754520[104] = dt;
   out_2410705301866754520[105] = 0;
   out_2410705301866754520[106] = 0;
   out_2410705301866754520[107] = 0;
   out_2410705301866754520[108] = 0;
   out_2410705301866754520[109] = 0;
   out_2410705301866754520[110] = 0;
   out_2410705301866754520[111] = 0;
   out_2410705301866754520[112] = 0;
   out_2410705301866754520[113] = 0;
   out_2410705301866754520[114] = 1;
   out_2410705301866754520[115] = 0;
   out_2410705301866754520[116] = 0;
   out_2410705301866754520[117] = 0;
   out_2410705301866754520[118] = 0;
   out_2410705301866754520[119] = 0;
   out_2410705301866754520[120] = 0;
   out_2410705301866754520[121] = 0;
   out_2410705301866754520[122] = 0;
   out_2410705301866754520[123] = 0;
   out_2410705301866754520[124] = 0;
   out_2410705301866754520[125] = 0;
   out_2410705301866754520[126] = 0;
   out_2410705301866754520[127] = 0;
   out_2410705301866754520[128] = 0;
   out_2410705301866754520[129] = 0;
   out_2410705301866754520[130] = 0;
   out_2410705301866754520[131] = 0;
   out_2410705301866754520[132] = 0;
   out_2410705301866754520[133] = 1;
   out_2410705301866754520[134] = 0;
   out_2410705301866754520[135] = 0;
   out_2410705301866754520[136] = 0;
   out_2410705301866754520[137] = 0;
   out_2410705301866754520[138] = 0;
   out_2410705301866754520[139] = 0;
   out_2410705301866754520[140] = 0;
   out_2410705301866754520[141] = 0;
   out_2410705301866754520[142] = 0;
   out_2410705301866754520[143] = 0;
   out_2410705301866754520[144] = 0;
   out_2410705301866754520[145] = 0;
   out_2410705301866754520[146] = 0;
   out_2410705301866754520[147] = 0;
   out_2410705301866754520[148] = 0;
   out_2410705301866754520[149] = 0;
   out_2410705301866754520[150] = 0;
   out_2410705301866754520[151] = 0;
   out_2410705301866754520[152] = 1;
   out_2410705301866754520[153] = 0;
   out_2410705301866754520[154] = 0;
   out_2410705301866754520[155] = 0;
   out_2410705301866754520[156] = 0;
   out_2410705301866754520[157] = 0;
   out_2410705301866754520[158] = 0;
   out_2410705301866754520[159] = 0;
   out_2410705301866754520[160] = 0;
   out_2410705301866754520[161] = 0;
   out_2410705301866754520[162] = 0;
   out_2410705301866754520[163] = 0;
   out_2410705301866754520[164] = 0;
   out_2410705301866754520[165] = 0;
   out_2410705301866754520[166] = 0;
   out_2410705301866754520[167] = 0;
   out_2410705301866754520[168] = 0;
   out_2410705301866754520[169] = 0;
   out_2410705301866754520[170] = 0;
   out_2410705301866754520[171] = 1;
   out_2410705301866754520[172] = 0;
   out_2410705301866754520[173] = 0;
   out_2410705301866754520[174] = 0;
   out_2410705301866754520[175] = 0;
   out_2410705301866754520[176] = 0;
   out_2410705301866754520[177] = 0;
   out_2410705301866754520[178] = 0;
   out_2410705301866754520[179] = 0;
   out_2410705301866754520[180] = 0;
   out_2410705301866754520[181] = 0;
   out_2410705301866754520[182] = 0;
   out_2410705301866754520[183] = 0;
   out_2410705301866754520[184] = 0;
   out_2410705301866754520[185] = 0;
   out_2410705301866754520[186] = 0;
   out_2410705301866754520[187] = 0;
   out_2410705301866754520[188] = 0;
   out_2410705301866754520[189] = 0;
   out_2410705301866754520[190] = 1;
   out_2410705301866754520[191] = 0;
   out_2410705301866754520[192] = 0;
   out_2410705301866754520[193] = 0;
   out_2410705301866754520[194] = 0;
   out_2410705301866754520[195] = 0;
   out_2410705301866754520[196] = 0;
   out_2410705301866754520[197] = 0;
   out_2410705301866754520[198] = 0;
   out_2410705301866754520[199] = 0;
   out_2410705301866754520[200] = 0;
   out_2410705301866754520[201] = 0;
   out_2410705301866754520[202] = 0;
   out_2410705301866754520[203] = 0;
   out_2410705301866754520[204] = 0;
   out_2410705301866754520[205] = 0;
   out_2410705301866754520[206] = 0;
   out_2410705301866754520[207] = 0;
   out_2410705301866754520[208] = 0;
   out_2410705301866754520[209] = 1;
   out_2410705301866754520[210] = 0;
   out_2410705301866754520[211] = 0;
   out_2410705301866754520[212] = 0;
   out_2410705301866754520[213] = 0;
   out_2410705301866754520[214] = 0;
   out_2410705301866754520[215] = 0;
   out_2410705301866754520[216] = 0;
   out_2410705301866754520[217] = 0;
   out_2410705301866754520[218] = 0;
   out_2410705301866754520[219] = 0;
   out_2410705301866754520[220] = 0;
   out_2410705301866754520[221] = 0;
   out_2410705301866754520[222] = 0;
   out_2410705301866754520[223] = 0;
   out_2410705301866754520[224] = 0;
   out_2410705301866754520[225] = 0;
   out_2410705301866754520[226] = 0;
   out_2410705301866754520[227] = 0;
   out_2410705301866754520[228] = 1;
   out_2410705301866754520[229] = 0;
   out_2410705301866754520[230] = 0;
   out_2410705301866754520[231] = 0;
   out_2410705301866754520[232] = 0;
   out_2410705301866754520[233] = 0;
   out_2410705301866754520[234] = 0;
   out_2410705301866754520[235] = 0;
   out_2410705301866754520[236] = 0;
   out_2410705301866754520[237] = 0;
   out_2410705301866754520[238] = 0;
   out_2410705301866754520[239] = 0;
   out_2410705301866754520[240] = 0;
   out_2410705301866754520[241] = 0;
   out_2410705301866754520[242] = 0;
   out_2410705301866754520[243] = 0;
   out_2410705301866754520[244] = 0;
   out_2410705301866754520[245] = 0;
   out_2410705301866754520[246] = 0;
   out_2410705301866754520[247] = 1;
   out_2410705301866754520[248] = 0;
   out_2410705301866754520[249] = 0;
   out_2410705301866754520[250] = 0;
   out_2410705301866754520[251] = 0;
   out_2410705301866754520[252] = 0;
   out_2410705301866754520[253] = 0;
   out_2410705301866754520[254] = 0;
   out_2410705301866754520[255] = 0;
   out_2410705301866754520[256] = 0;
   out_2410705301866754520[257] = 0;
   out_2410705301866754520[258] = 0;
   out_2410705301866754520[259] = 0;
   out_2410705301866754520[260] = 0;
   out_2410705301866754520[261] = 0;
   out_2410705301866754520[262] = 0;
   out_2410705301866754520[263] = 0;
   out_2410705301866754520[264] = 0;
   out_2410705301866754520[265] = 0;
   out_2410705301866754520[266] = 1;
   out_2410705301866754520[267] = 0;
   out_2410705301866754520[268] = 0;
   out_2410705301866754520[269] = 0;
   out_2410705301866754520[270] = 0;
   out_2410705301866754520[271] = 0;
   out_2410705301866754520[272] = 0;
   out_2410705301866754520[273] = 0;
   out_2410705301866754520[274] = 0;
   out_2410705301866754520[275] = 0;
   out_2410705301866754520[276] = 0;
   out_2410705301866754520[277] = 0;
   out_2410705301866754520[278] = 0;
   out_2410705301866754520[279] = 0;
   out_2410705301866754520[280] = 0;
   out_2410705301866754520[281] = 0;
   out_2410705301866754520[282] = 0;
   out_2410705301866754520[283] = 0;
   out_2410705301866754520[284] = 0;
   out_2410705301866754520[285] = 1;
   out_2410705301866754520[286] = 0;
   out_2410705301866754520[287] = 0;
   out_2410705301866754520[288] = 0;
   out_2410705301866754520[289] = 0;
   out_2410705301866754520[290] = 0;
   out_2410705301866754520[291] = 0;
   out_2410705301866754520[292] = 0;
   out_2410705301866754520[293] = 0;
   out_2410705301866754520[294] = 0;
   out_2410705301866754520[295] = 0;
   out_2410705301866754520[296] = 0;
   out_2410705301866754520[297] = 0;
   out_2410705301866754520[298] = 0;
   out_2410705301866754520[299] = 0;
   out_2410705301866754520[300] = 0;
   out_2410705301866754520[301] = 0;
   out_2410705301866754520[302] = 0;
   out_2410705301866754520[303] = 0;
   out_2410705301866754520[304] = 1;
   out_2410705301866754520[305] = 0;
   out_2410705301866754520[306] = 0;
   out_2410705301866754520[307] = 0;
   out_2410705301866754520[308] = 0;
   out_2410705301866754520[309] = 0;
   out_2410705301866754520[310] = 0;
   out_2410705301866754520[311] = 0;
   out_2410705301866754520[312] = 0;
   out_2410705301866754520[313] = 0;
   out_2410705301866754520[314] = 0;
   out_2410705301866754520[315] = 0;
   out_2410705301866754520[316] = 0;
   out_2410705301866754520[317] = 0;
   out_2410705301866754520[318] = 0;
   out_2410705301866754520[319] = 0;
   out_2410705301866754520[320] = 0;
   out_2410705301866754520[321] = 0;
   out_2410705301866754520[322] = 0;
   out_2410705301866754520[323] = 1;
}
void h_4(double *state, double *unused, double *out_9112018432623595899) {
   out_9112018432623595899[0] = state[6] + state[9];
   out_9112018432623595899[1] = state[7] + state[10];
   out_9112018432623595899[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_5072803088510724449) {
   out_5072803088510724449[0] = 0;
   out_5072803088510724449[1] = 0;
   out_5072803088510724449[2] = 0;
   out_5072803088510724449[3] = 0;
   out_5072803088510724449[4] = 0;
   out_5072803088510724449[5] = 0;
   out_5072803088510724449[6] = 1;
   out_5072803088510724449[7] = 0;
   out_5072803088510724449[8] = 0;
   out_5072803088510724449[9] = 1;
   out_5072803088510724449[10] = 0;
   out_5072803088510724449[11] = 0;
   out_5072803088510724449[12] = 0;
   out_5072803088510724449[13] = 0;
   out_5072803088510724449[14] = 0;
   out_5072803088510724449[15] = 0;
   out_5072803088510724449[16] = 0;
   out_5072803088510724449[17] = 0;
   out_5072803088510724449[18] = 0;
   out_5072803088510724449[19] = 0;
   out_5072803088510724449[20] = 0;
   out_5072803088510724449[21] = 0;
   out_5072803088510724449[22] = 0;
   out_5072803088510724449[23] = 0;
   out_5072803088510724449[24] = 0;
   out_5072803088510724449[25] = 1;
   out_5072803088510724449[26] = 0;
   out_5072803088510724449[27] = 0;
   out_5072803088510724449[28] = 1;
   out_5072803088510724449[29] = 0;
   out_5072803088510724449[30] = 0;
   out_5072803088510724449[31] = 0;
   out_5072803088510724449[32] = 0;
   out_5072803088510724449[33] = 0;
   out_5072803088510724449[34] = 0;
   out_5072803088510724449[35] = 0;
   out_5072803088510724449[36] = 0;
   out_5072803088510724449[37] = 0;
   out_5072803088510724449[38] = 0;
   out_5072803088510724449[39] = 0;
   out_5072803088510724449[40] = 0;
   out_5072803088510724449[41] = 0;
   out_5072803088510724449[42] = 0;
   out_5072803088510724449[43] = 0;
   out_5072803088510724449[44] = 1;
   out_5072803088510724449[45] = 0;
   out_5072803088510724449[46] = 0;
   out_5072803088510724449[47] = 1;
   out_5072803088510724449[48] = 0;
   out_5072803088510724449[49] = 0;
   out_5072803088510724449[50] = 0;
   out_5072803088510724449[51] = 0;
   out_5072803088510724449[52] = 0;
   out_5072803088510724449[53] = 0;
}
void h_10(double *state, double *unused, double *out_1222625076235428622) {
   out_1222625076235428622[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_1222625076235428622[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_1222625076235428622[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_6913994360612087924) {
   out_6913994360612087924[0] = 0;
   out_6913994360612087924[1] = 9.8100000000000005*cos(state[1]);
   out_6913994360612087924[2] = 0;
   out_6913994360612087924[3] = 0;
   out_6913994360612087924[4] = -state[8];
   out_6913994360612087924[5] = state[7];
   out_6913994360612087924[6] = 0;
   out_6913994360612087924[7] = state[5];
   out_6913994360612087924[8] = -state[4];
   out_6913994360612087924[9] = 0;
   out_6913994360612087924[10] = 0;
   out_6913994360612087924[11] = 0;
   out_6913994360612087924[12] = 1;
   out_6913994360612087924[13] = 0;
   out_6913994360612087924[14] = 0;
   out_6913994360612087924[15] = 1;
   out_6913994360612087924[16] = 0;
   out_6913994360612087924[17] = 0;
   out_6913994360612087924[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_6913994360612087924[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_6913994360612087924[20] = 0;
   out_6913994360612087924[21] = state[8];
   out_6913994360612087924[22] = 0;
   out_6913994360612087924[23] = -state[6];
   out_6913994360612087924[24] = -state[5];
   out_6913994360612087924[25] = 0;
   out_6913994360612087924[26] = state[3];
   out_6913994360612087924[27] = 0;
   out_6913994360612087924[28] = 0;
   out_6913994360612087924[29] = 0;
   out_6913994360612087924[30] = 0;
   out_6913994360612087924[31] = 1;
   out_6913994360612087924[32] = 0;
   out_6913994360612087924[33] = 0;
   out_6913994360612087924[34] = 1;
   out_6913994360612087924[35] = 0;
   out_6913994360612087924[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_6913994360612087924[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_6913994360612087924[38] = 0;
   out_6913994360612087924[39] = -state[7];
   out_6913994360612087924[40] = state[6];
   out_6913994360612087924[41] = 0;
   out_6913994360612087924[42] = state[4];
   out_6913994360612087924[43] = -state[3];
   out_6913994360612087924[44] = 0;
   out_6913994360612087924[45] = 0;
   out_6913994360612087924[46] = 0;
   out_6913994360612087924[47] = 0;
   out_6913994360612087924[48] = 0;
   out_6913994360612087924[49] = 0;
   out_6913994360612087924[50] = 1;
   out_6913994360612087924[51] = 0;
   out_6913994360612087924[52] = 0;
   out_6913994360612087924[53] = 1;
}
void h_13(double *state, double *unused, double *out_5539054079846767747) {
   out_5539054079846767747[0] = state[3];
   out_5539054079846767747[1] = state[4];
   out_5539054079846767747[2] = state[5];
}
void H_13(double *state, double *unused, double *out_5637405008192568553) {
   out_5637405008192568553[0] = 0;
   out_5637405008192568553[1] = 0;
   out_5637405008192568553[2] = 0;
   out_5637405008192568553[3] = 1;
   out_5637405008192568553[4] = 0;
   out_5637405008192568553[5] = 0;
   out_5637405008192568553[6] = 0;
   out_5637405008192568553[7] = 0;
   out_5637405008192568553[8] = 0;
   out_5637405008192568553[9] = 0;
   out_5637405008192568553[10] = 0;
   out_5637405008192568553[11] = 0;
   out_5637405008192568553[12] = 0;
   out_5637405008192568553[13] = 0;
   out_5637405008192568553[14] = 0;
   out_5637405008192568553[15] = 0;
   out_5637405008192568553[16] = 0;
   out_5637405008192568553[17] = 0;
   out_5637405008192568553[18] = 0;
   out_5637405008192568553[19] = 0;
   out_5637405008192568553[20] = 0;
   out_5637405008192568553[21] = 0;
   out_5637405008192568553[22] = 1;
   out_5637405008192568553[23] = 0;
   out_5637405008192568553[24] = 0;
   out_5637405008192568553[25] = 0;
   out_5637405008192568553[26] = 0;
   out_5637405008192568553[27] = 0;
   out_5637405008192568553[28] = 0;
   out_5637405008192568553[29] = 0;
   out_5637405008192568553[30] = 0;
   out_5637405008192568553[31] = 0;
   out_5637405008192568553[32] = 0;
   out_5637405008192568553[33] = 0;
   out_5637405008192568553[34] = 0;
   out_5637405008192568553[35] = 0;
   out_5637405008192568553[36] = 0;
   out_5637405008192568553[37] = 0;
   out_5637405008192568553[38] = 0;
   out_5637405008192568553[39] = 0;
   out_5637405008192568553[40] = 0;
   out_5637405008192568553[41] = 1;
   out_5637405008192568553[42] = 0;
   out_5637405008192568553[43] = 0;
   out_5637405008192568553[44] = 0;
   out_5637405008192568553[45] = 0;
   out_5637405008192568553[46] = 0;
   out_5637405008192568553[47] = 0;
   out_5637405008192568553[48] = 0;
   out_5637405008192568553[49] = 0;
   out_5637405008192568553[50] = 0;
   out_5637405008192568553[51] = 0;
   out_5637405008192568553[52] = 0;
   out_5637405008192568553[53] = 0;
}
void h_14(double *state, double *unused, double *out_4189770429909065638) {
   out_4189770429909065638[0] = state[6];
   out_4189770429909065638[1] = state[7];
   out_4189770429909065638[2] = state[8];
}
void H_14(double *state, double *unused, double *out_1990014656215352153) {
   out_1990014656215352153[0] = 0;
   out_1990014656215352153[1] = 0;
   out_1990014656215352153[2] = 0;
   out_1990014656215352153[3] = 0;
   out_1990014656215352153[4] = 0;
   out_1990014656215352153[5] = 0;
   out_1990014656215352153[6] = 1;
   out_1990014656215352153[7] = 0;
   out_1990014656215352153[8] = 0;
   out_1990014656215352153[9] = 0;
   out_1990014656215352153[10] = 0;
   out_1990014656215352153[11] = 0;
   out_1990014656215352153[12] = 0;
   out_1990014656215352153[13] = 0;
   out_1990014656215352153[14] = 0;
   out_1990014656215352153[15] = 0;
   out_1990014656215352153[16] = 0;
   out_1990014656215352153[17] = 0;
   out_1990014656215352153[18] = 0;
   out_1990014656215352153[19] = 0;
   out_1990014656215352153[20] = 0;
   out_1990014656215352153[21] = 0;
   out_1990014656215352153[22] = 0;
   out_1990014656215352153[23] = 0;
   out_1990014656215352153[24] = 0;
   out_1990014656215352153[25] = 1;
   out_1990014656215352153[26] = 0;
   out_1990014656215352153[27] = 0;
   out_1990014656215352153[28] = 0;
   out_1990014656215352153[29] = 0;
   out_1990014656215352153[30] = 0;
   out_1990014656215352153[31] = 0;
   out_1990014656215352153[32] = 0;
   out_1990014656215352153[33] = 0;
   out_1990014656215352153[34] = 0;
   out_1990014656215352153[35] = 0;
   out_1990014656215352153[36] = 0;
   out_1990014656215352153[37] = 0;
   out_1990014656215352153[38] = 0;
   out_1990014656215352153[39] = 0;
   out_1990014656215352153[40] = 0;
   out_1990014656215352153[41] = 0;
   out_1990014656215352153[42] = 0;
   out_1990014656215352153[43] = 0;
   out_1990014656215352153[44] = 1;
   out_1990014656215352153[45] = 0;
   out_1990014656215352153[46] = 0;
   out_1990014656215352153[47] = 0;
   out_1990014656215352153[48] = 0;
   out_1990014656215352153[49] = 0;
   out_1990014656215352153[50] = 0;
   out_1990014656215352153[51] = 0;
   out_1990014656215352153[52] = 0;
   out_1990014656215352153[53] = 0;
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
void pose_err_fun(double *nom_x, double *delta_x, double *out_3211789106073125283) {
  err_fun(nom_x, delta_x, out_3211789106073125283);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_6226563961506943969) {
  inv_err_fun(nom_x, true_x, out_6226563961506943969);
}
void pose_H_mod_fun(double *state, double *out_5161461913541420634) {
  H_mod_fun(state, out_5161461913541420634);
}
void pose_f_fun(double *state, double dt, double *out_3057528827902898560) {
  f_fun(state,  dt, out_3057528827902898560);
}
void pose_F_fun(double *state, double dt, double *out_2410705301866754520) {
  F_fun(state,  dt, out_2410705301866754520);
}
void pose_h_4(double *state, double *unused, double *out_9112018432623595899) {
  h_4(state, unused, out_9112018432623595899);
}
void pose_H_4(double *state, double *unused, double *out_5072803088510724449) {
  H_4(state, unused, out_5072803088510724449);
}
void pose_h_10(double *state, double *unused, double *out_1222625076235428622) {
  h_10(state, unused, out_1222625076235428622);
}
void pose_H_10(double *state, double *unused, double *out_6913994360612087924) {
  H_10(state, unused, out_6913994360612087924);
}
void pose_h_13(double *state, double *unused, double *out_5539054079846767747) {
  h_13(state, unused, out_5539054079846767747);
}
void pose_H_13(double *state, double *unused, double *out_5637405008192568553) {
  H_13(state, unused, out_5637405008192568553);
}
void pose_h_14(double *state, double *unused, double *out_4189770429909065638) {
  h_14(state, unused, out_4189770429909065638);
}
void pose_H_14(double *state, double *unused, double *out_1990014656215352153) {
  H_14(state, unused, out_1990014656215352153);
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
