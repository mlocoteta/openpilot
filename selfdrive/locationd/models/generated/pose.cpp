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
void err_fun(double *nom_x, double *delta_x, double *out_1227579335886564773) {
   out_1227579335886564773[0] = delta_x[0] + nom_x[0];
   out_1227579335886564773[1] = delta_x[1] + nom_x[1];
   out_1227579335886564773[2] = delta_x[2] + nom_x[2];
   out_1227579335886564773[3] = delta_x[3] + nom_x[3];
   out_1227579335886564773[4] = delta_x[4] + nom_x[4];
   out_1227579335886564773[5] = delta_x[5] + nom_x[5];
   out_1227579335886564773[6] = delta_x[6] + nom_x[6];
   out_1227579335886564773[7] = delta_x[7] + nom_x[7];
   out_1227579335886564773[8] = delta_x[8] + nom_x[8];
   out_1227579335886564773[9] = delta_x[9] + nom_x[9];
   out_1227579335886564773[10] = delta_x[10] + nom_x[10];
   out_1227579335886564773[11] = delta_x[11] + nom_x[11];
   out_1227579335886564773[12] = delta_x[12] + nom_x[12];
   out_1227579335886564773[13] = delta_x[13] + nom_x[13];
   out_1227579335886564773[14] = delta_x[14] + nom_x[14];
   out_1227579335886564773[15] = delta_x[15] + nom_x[15];
   out_1227579335886564773[16] = delta_x[16] + nom_x[16];
   out_1227579335886564773[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_7708296302708828001) {
   out_7708296302708828001[0] = -nom_x[0] + true_x[0];
   out_7708296302708828001[1] = -nom_x[1] + true_x[1];
   out_7708296302708828001[2] = -nom_x[2] + true_x[2];
   out_7708296302708828001[3] = -nom_x[3] + true_x[3];
   out_7708296302708828001[4] = -nom_x[4] + true_x[4];
   out_7708296302708828001[5] = -nom_x[5] + true_x[5];
   out_7708296302708828001[6] = -nom_x[6] + true_x[6];
   out_7708296302708828001[7] = -nom_x[7] + true_x[7];
   out_7708296302708828001[8] = -nom_x[8] + true_x[8];
   out_7708296302708828001[9] = -nom_x[9] + true_x[9];
   out_7708296302708828001[10] = -nom_x[10] + true_x[10];
   out_7708296302708828001[11] = -nom_x[11] + true_x[11];
   out_7708296302708828001[12] = -nom_x[12] + true_x[12];
   out_7708296302708828001[13] = -nom_x[13] + true_x[13];
   out_7708296302708828001[14] = -nom_x[14] + true_x[14];
   out_7708296302708828001[15] = -nom_x[15] + true_x[15];
   out_7708296302708828001[16] = -nom_x[16] + true_x[16];
   out_7708296302708828001[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_145151651698479708) {
   out_145151651698479708[0] = 1.0;
   out_145151651698479708[1] = 0.0;
   out_145151651698479708[2] = 0.0;
   out_145151651698479708[3] = 0.0;
   out_145151651698479708[4] = 0.0;
   out_145151651698479708[5] = 0.0;
   out_145151651698479708[6] = 0.0;
   out_145151651698479708[7] = 0.0;
   out_145151651698479708[8] = 0.0;
   out_145151651698479708[9] = 0.0;
   out_145151651698479708[10] = 0.0;
   out_145151651698479708[11] = 0.0;
   out_145151651698479708[12] = 0.0;
   out_145151651698479708[13] = 0.0;
   out_145151651698479708[14] = 0.0;
   out_145151651698479708[15] = 0.0;
   out_145151651698479708[16] = 0.0;
   out_145151651698479708[17] = 0.0;
   out_145151651698479708[18] = 0.0;
   out_145151651698479708[19] = 1.0;
   out_145151651698479708[20] = 0.0;
   out_145151651698479708[21] = 0.0;
   out_145151651698479708[22] = 0.0;
   out_145151651698479708[23] = 0.0;
   out_145151651698479708[24] = 0.0;
   out_145151651698479708[25] = 0.0;
   out_145151651698479708[26] = 0.0;
   out_145151651698479708[27] = 0.0;
   out_145151651698479708[28] = 0.0;
   out_145151651698479708[29] = 0.0;
   out_145151651698479708[30] = 0.0;
   out_145151651698479708[31] = 0.0;
   out_145151651698479708[32] = 0.0;
   out_145151651698479708[33] = 0.0;
   out_145151651698479708[34] = 0.0;
   out_145151651698479708[35] = 0.0;
   out_145151651698479708[36] = 0.0;
   out_145151651698479708[37] = 0.0;
   out_145151651698479708[38] = 1.0;
   out_145151651698479708[39] = 0.0;
   out_145151651698479708[40] = 0.0;
   out_145151651698479708[41] = 0.0;
   out_145151651698479708[42] = 0.0;
   out_145151651698479708[43] = 0.0;
   out_145151651698479708[44] = 0.0;
   out_145151651698479708[45] = 0.0;
   out_145151651698479708[46] = 0.0;
   out_145151651698479708[47] = 0.0;
   out_145151651698479708[48] = 0.0;
   out_145151651698479708[49] = 0.0;
   out_145151651698479708[50] = 0.0;
   out_145151651698479708[51] = 0.0;
   out_145151651698479708[52] = 0.0;
   out_145151651698479708[53] = 0.0;
   out_145151651698479708[54] = 0.0;
   out_145151651698479708[55] = 0.0;
   out_145151651698479708[56] = 0.0;
   out_145151651698479708[57] = 1.0;
   out_145151651698479708[58] = 0.0;
   out_145151651698479708[59] = 0.0;
   out_145151651698479708[60] = 0.0;
   out_145151651698479708[61] = 0.0;
   out_145151651698479708[62] = 0.0;
   out_145151651698479708[63] = 0.0;
   out_145151651698479708[64] = 0.0;
   out_145151651698479708[65] = 0.0;
   out_145151651698479708[66] = 0.0;
   out_145151651698479708[67] = 0.0;
   out_145151651698479708[68] = 0.0;
   out_145151651698479708[69] = 0.0;
   out_145151651698479708[70] = 0.0;
   out_145151651698479708[71] = 0.0;
   out_145151651698479708[72] = 0.0;
   out_145151651698479708[73] = 0.0;
   out_145151651698479708[74] = 0.0;
   out_145151651698479708[75] = 0.0;
   out_145151651698479708[76] = 1.0;
   out_145151651698479708[77] = 0.0;
   out_145151651698479708[78] = 0.0;
   out_145151651698479708[79] = 0.0;
   out_145151651698479708[80] = 0.0;
   out_145151651698479708[81] = 0.0;
   out_145151651698479708[82] = 0.0;
   out_145151651698479708[83] = 0.0;
   out_145151651698479708[84] = 0.0;
   out_145151651698479708[85] = 0.0;
   out_145151651698479708[86] = 0.0;
   out_145151651698479708[87] = 0.0;
   out_145151651698479708[88] = 0.0;
   out_145151651698479708[89] = 0.0;
   out_145151651698479708[90] = 0.0;
   out_145151651698479708[91] = 0.0;
   out_145151651698479708[92] = 0.0;
   out_145151651698479708[93] = 0.0;
   out_145151651698479708[94] = 0.0;
   out_145151651698479708[95] = 1.0;
   out_145151651698479708[96] = 0.0;
   out_145151651698479708[97] = 0.0;
   out_145151651698479708[98] = 0.0;
   out_145151651698479708[99] = 0.0;
   out_145151651698479708[100] = 0.0;
   out_145151651698479708[101] = 0.0;
   out_145151651698479708[102] = 0.0;
   out_145151651698479708[103] = 0.0;
   out_145151651698479708[104] = 0.0;
   out_145151651698479708[105] = 0.0;
   out_145151651698479708[106] = 0.0;
   out_145151651698479708[107] = 0.0;
   out_145151651698479708[108] = 0.0;
   out_145151651698479708[109] = 0.0;
   out_145151651698479708[110] = 0.0;
   out_145151651698479708[111] = 0.0;
   out_145151651698479708[112] = 0.0;
   out_145151651698479708[113] = 0.0;
   out_145151651698479708[114] = 1.0;
   out_145151651698479708[115] = 0.0;
   out_145151651698479708[116] = 0.0;
   out_145151651698479708[117] = 0.0;
   out_145151651698479708[118] = 0.0;
   out_145151651698479708[119] = 0.0;
   out_145151651698479708[120] = 0.0;
   out_145151651698479708[121] = 0.0;
   out_145151651698479708[122] = 0.0;
   out_145151651698479708[123] = 0.0;
   out_145151651698479708[124] = 0.0;
   out_145151651698479708[125] = 0.0;
   out_145151651698479708[126] = 0.0;
   out_145151651698479708[127] = 0.0;
   out_145151651698479708[128] = 0.0;
   out_145151651698479708[129] = 0.0;
   out_145151651698479708[130] = 0.0;
   out_145151651698479708[131] = 0.0;
   out_145151651698479708[132] = 0.0;
   out_145151651698479708[133] = 1.0;
   out_145151651698479708[134] = 0.0;
   out_145151651698479708[135] = 0.0;
   out_145151651698479708[136] = 0.0;
   out_145151651698479708[137] = 0.0;
   out_145151651698479708[138] = 0.0;
   out_145151651698479708[139] = 0.0;
   out_145151651698479708[140] = 0.0;
   out_145151651698479708[141] = 0.0;
   out_145151651698479708[142] = 0.0;
   out_145151651698479708[143] = 0.0;
   out_145151651698479708[144] = 0.0;
   out_145151651698479708[145] = 0.0;
   out_145151651698479708[146] = 0.0;
   out_145151651698479708[147] = 0.0;
   out_145151651698479708[148] = 0.0;
   out_145151651698479708[149] = 0.0;
   out_145151651698479708[150] = 0.0;
   out_145151651698479708[151] = 0.0;
   out_145151651698479708[152] = 1.0;
   out_145151651698479708[153] = 0.0;
   out_145151651698479708[154] = 0.0;
   out_145151651698479708[155] = 0.0;
   out_145151651698479708[156] = 0.0;
   out_145151651698479708[157] = 0.0;
   out_145151651698479708[158] = 0.0;
   out_145151651698479708[159] = 0.0;
   out_145151651698479708[160] = 0.0;
   out_145151651698479708[161] = 0.0;
   out_145151651698479708[162] = 0.0;
   out_145151651698479708[163] = 0.0;
   out_145151651698479708[164] = 0.0;
   out_145151651698479708[165] = 0.0;
   out_145151651698479708[166] = 0.0;
   out_145151651698479708[167] = 0.0;
   out_145151651698479708[168] = 0.0;
   out_145151651698479708[169] = 0.0;
   out_145151651698479708[170] = 0.0;
   out_145151651698479708[171] = 1.0;
   out_145151651698479708[172] = 0.0;
   out_145151651698479708[173] = 0.0;
   out_145151651698479708[174] = 0.0;
   out_145151651698479708[175] = 0.0;
   out_145151651698479708[176] = 0.0;
   out_145151651698479708[177] = 0.0;
   out_145151651698479708[178] = 0.0;
   out_145151651698479708[179] = 0.0;
   out_145151651698479708[180] = 0.0;
   out_145151651698479708[181] = 0.0;
   out_145151651698479708[182] = 0.0;
   out_145151651698479708[183] = 0.0;
   out_145151651698479708[184] = 0.0;
   out_145151651698479708[185] = 0.0;
   out_145151651698479708[186] = 0.0;
   out_145151651698479708[187] = 0.0;
   out_145151651698479708[188] = 0.0;
   out_145151651698479708[189] = 0.0;
   out_145151651698479708[190] = 1.0;
   out_145151651698479708[191] = 0.0;
   out_145151651698479708[192] = 0.0;
   out_145151651698479708[193] = 0.0;
   out_145151651698479708[194] = 0.0;
   out_145151651698479708[195] = 0.0;
   out_145151651698479708[196] = 0.0;
   out_145151651698479708[197] = 0.0;
   out_145151651698479708[198] = 0.0;
   out_145151651698479708[199] = 0.0;
   out_145151651698479708[200] = 0.0;
   out_145151651698479708[201] = 0.0;
   out_145151651698479708[202] = 0.0;
   out_145151651698479708[203] = 0.0;
   out_145151651698479708[204] = 0.0;
   out_145151651698479708[205] = 0.0;
   out_145151651698479708[206] = 0.0;
   out_145151651698479708[207] = 0.0;
   out_145151651698479708[208] = 0.0;
   out_145151651698479708[209] = 1.0;
   out_145151651698479708[210] = 0.0;
   out_145151651698479708[211] = 0.0;
   out_145151651698479708[212] = 0.0;
   out_145151651698479708[213] = 0.0;
   out_145151651698479708[214] = 0.0;
   out_145151651698479708[215] = 0.0;
   out_145151651698479708[216] = 0.0;
   out_145151651698479708[217] = 0.0;
   out_145151651698479708[218] = 0.0;
   out_145151651698479708[219] = 0.0;
   out_145151651698479708[220] = 0.0;
   out_145151651698479708[221] = 0.0;
   out_145151651698479708[222] = 0.0;
   out_145151651698479708[223] = 0.0;
   out_145151651698479708[224] = 0.0;
   out_145151651698479708[225] = 0.0;
   out_145151651698479708[226] = 0.0;
   out_145151651698479708[227] = 0.0;
   out_145151651698479708[228] = 1.0;
   out_145151651698479708[229] = 0.0;
   out_145151651698479708[230] = 0.0;
   out_145151651698479708[231] = 0.0;
   out_145151651698479708[232] = 0.0;
   out_145151651698479708[233] = 0.0;
   out_145151651698479708[234] = 0.0;
   out_145151651698479708[235] = 0.0;
   out_145151651698479708[236] = 0.0;
   out_145151651698479708[237] = 0.0;
   out_145151651698479708[238] = 0.0;
   out_145151651698479708[239] = 0.0;
   out_145151651698479708[240] = 0.0;
   out_145151651698479708[241] = 0.0;
   out_145151651698479708[242] = 0.0;
   out_145151651698479708[243] = 0.0;
   out_145151651698479708[244] = 0.0;
   out_145151651698479708[245] = 0.0;
   out_145151651698479708[246] = 0.0;
   out_145151651698479708[247] = 1.0;
   out_145151651698479708[248] = 0.0;
   out_145151651698479708[249] = 0.0;
   out_145151651698479708[250] = 0.0;
   out_145151651698479708[251] = 0.0;
   out_145151651698479708[252] = 0.0;
   out_145151651698479708[253] = 0.0;
   out_145151651698479708[254] = 0.0;
   out_145151651698479708[255] = 0.0;
   out_145151651698479708[256] = 0.0;
   out_145151651698479708[257] = 0.0;
   out_145151651698479708[258] = 0.0;
   out_145151651698479708[259] = 0.0;
   out_145151651698479708[260] = 0.0;
   out_145151651698479708[261] = 0.0;
   out_145151651698479708[262] = 0.0;
   out_145151651698479708[263] = 0.0;
   out_145151651698479708[264] = 0.0;
   out_145151651698479708[265] = 0.0;
   out_145151651698479708[266] = 1.0;
   out_145151651698479708[267] = 0.0;
   out_145151651698479708[268] = 0.0;
   out_145151651698479708[269] = 0.0;
   out_145151651698479708[270] = 0.0;
   out_145151651698479708[271] = 0.0;
   out_145151651698479708[272] = 0.0;
   out_145151651698479708[273] = 0.0;
   out_145151651698479708[274] = 0.0;
   out_145151651698479708[275] = 0.0;
   out_145151651698479708[276] = 0.0;
   out_145151651698479708[277] = 0.0;
   out_145151651698479708[278] = 0.0;
   out_145151651698479708[279] = 0.0;
   out_145151651698479708[280] = 0.0;
   out_145151651698479708[281] = 0.0;
   out_145151651698479708[282] = 0.0;
   out_145151651698479708[283] = 0.0;
   out_145151651698479708[284] = 0.0;
   out_145151651698479708[285] = 1.0;
   out_145151651698479708[286] = 0.0;
   out_145151651698479708[287] = 0.0;
   out_145151651698479708[288] = 0.0;
   out_145151651698479708[289] = 0.0;
   out_145151651698479708[290] = 0.0;
   out_145151651698479708[291] = 0.0;
   out_145151651698479708[292] = 0.0;
   out_145151651698479708[293] = 0.0;
   out_145151651698479708[294] = 0.0;
   out_145151651698479708[295] = 0.0;
   out_145151651698479708[296] = 0.0;
   out_145151651698479708[297] = 0.0;
   out_145151651698479708[298] = 0.0;
   out_145151651698479708[299] = 0.0;
   out_145151651698479708[300] = 0.0;
   out_145151651698479708[301] = 0.0;
   out_145151651698479708[302] = 0.0;
   out_145151651698479708[303] = 0.0;
   out_145151651698479708[304] = 1.0;
   out_145151651698479708[305] = 0.0;
   out_145151651698479708[306] = 0.0;
   out_145151651698479708[307] = 0.0;
   out_145151651698479708[308] = 0.0;
   out_145151651698479708[309] = 0.0;
   out_145151651698479708[310] = 0.0;
   out_145151651698479708[311] = 0.0;
   out_145151651698479708[312] = 0.0;
   out_145151651698479708[313] = 0.0;
   out_145151651698479708[314] = 0.0;
   out_145151651698479708[315] = 0.0;
   out_145151651698479708[316] = 0.0;
   out_145151651698479708[317] = 0.0;
   out_145151651698479708[318] = 0.0;
   out_145151651698479708[319] = 0.0;
   out_145151651698479708[320] = 0.0;
   out_145151651698479708[321] = 0.0;
   out_145151651698479708[322] = 0.0;
   out_145151651698479708[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_6753877240357292479) {
   out_6753877240357292479[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_6753877240357292479[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_6753877240357292479[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_6753877240357292479[3] = dt*state[12] + state[3];
   out_6753877240357292479[4] = dt*state[13] + state[4];
   out_6753877240357292479[5] = dt*state[14] + state[5];
   out_6753877240357292479[6] = state[6];
   out_6753877240357292479[7] = state[7];
   out_6753877240357292479[8] = state[8];
   out_6753877240357292479[9] = state[9];
   out_6753877240357292479[10] = state[10];
   out_6753877240357292479[11] = state[11];
   out_6753877240357292479[12] = state[12];
   out_6753877240357292479[13] = state[13];
   out_6753877240357292479[14] = state[14];
   out_6753877240357292479[15] = state[15];
   out_6753877240357292479[16] = state[16];
   out_6753877240357292479[17] = state[17];
}
void F_fun(double *state, double dt, double *out_48451545294533288) {
   out_48451545294533288[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_48451545294533288[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_48451545294533288[2] = 0;
   out_48451545294533288[3] = 0;
   out_48451545294533288[4] = 0;
   out_48451545294533288[5] = 0;
   out_48451545294533288[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_48451545294533288[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_48451545294533288[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_48451545294533288[9] = 0;
   out_48451545294533288[10] = 0;
   out_48451545294533288[11] = 0;
   out_48451545294533288[12] = 0;
   out_48451545294533288[13] = 0;
   out_48451545294533288[14] = 0;
   out_48451545294533288[15] = 0;
   out_48451545294533288[16] = 0;
   out_48451545294533288[17] = 0;
   out_48451545294533288[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_48451545294533288[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_48451545294533288[20] = 0;
   out_48451545294533288[21] = 0;
   out_48451545294533288[22] = 0;
   out_48451545294533288[23] = 0;
   out_48451545294533288[24] = 0;
   out_48451545294533288[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_48451545294533288[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_48451545294533288[27] = 0;
   out_48451545294533288[28] = 0;
   out_48451545294533288[29] = 0;
   out_48451545294533288[30] = 0;
   out_48451545294533288[31] = 0;
   out_48451545294533288[32] = 0;
   out_48451545294533288[33] = 0;
   out_48451545294533288[34] = 0;
   out_48451545294533288[35] = 0;
   out_48451545294533288[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_48451545294533288[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_48451545294533288[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_48451545294533288[39] = 0;
   out_48451545294533288[40] = 0;
   out_48451545294533288[41] = 0;
   out_48451545294533288[42] = 0;
   out_48451545294533288[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_48451545294533288[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_48451545294533288[45] = 0;
   out_48451545294533288[46] = 0;
   out_48451545294533288[47] = 0;
   out_48451545294533288[48] = 0;
   out_48451545294533288[49] = 0;
   out_48451545294533288[50] = 0;
   out_48451545294533288[51] = 0;
   out_48451545294533288[52] = 0;
   out_48451545294533288[53] = 0;
   out_48451545294533288[54] = 0;
   out_48451545294533288[55] = 0;
   out_48451545294533288[56] = 0;
   out_48451545294533288[57] = 1;
   out_48451545294533288[58] = 0;
   out_48451545294533288[59] = 0;
   out_48451545294533288[60] = 0;
   out_48451545294533288[61] = 0;
   out_48451545294533288[62] = 0;
   out_48451545294533288[63] = 0;
   out_48451545294533288[64] = 0;
   out_48451545294533288[65] = 0;
   out_48451545294533288[66] = dt;
   out_48451545294533288[67] = 0;
   out_48451545294533288[68] = 0;
   out_48451545294533288[69] = 0;
   out_48451545294533288[70] = 0;
   out_48451545294533288[71] = 0;
   out_48451545294533288[72] = 0;
   out_48451545294533288[73] = 0;
   out_48451545294533288[74] = 0;
   out_48451545294533288[75] = 0;
   out_48451545294533288[76] = 1;
   out_48451545294533288[77] = 0;
   out_48451545294533288[78] = 0;
   out_48451545294533288[79] = 0;
   out_48451545294533288[80] = 0;
   out_48451545294533288[81] = 0;
   out_48451545294533288[82] = 0;
   out_48451545294533288[83] = 0;
   out_48451545294533288[84] = 0;
   out_48451545294533288[85] = dt;
   out_48451545294533288[86] = 0;
   out_48451545294533288[87] = 0;
   out_48451545294533288[88] = 0;
   out_48451545294533288[89] = 0;
   out_48451545294533288[90] = 0;
   out_48451545294533288[91] = 0;
   out_48451545294533288[92] = 0;
   out_48451545294533288[93] = 0;
   out_48451545294533288[94] = 0;
   out_48451545294533288[95] = 1;
   out_48451545294533288[96] = 0;
   out_48451545294533288[97] = 0;
   out_48451545294533288[98] = 0;
   out_48451545294533288[99] = 0;
   out_48451545294533288[100] = 0;
   out_48451545294533288[101] = 0;
   out_48451545294533288[102] = 0;
   out_48451545294533288[103] = 0;
   out_48451545294533288[104] = dt;
   out_48451545294533288[105] = 0;
   out_48451545294533288[106] = 0;
   out_48451545294533288[107] = 0;
   out_48451545294533288[108] = 0;
   out_48451545294533288[109] = 0;
   out_48451545294533288[110] = 0;
   out_48451545294533288[111] = 0;
   out_48451545294533288[112] = 0;
   out_48451545294533288[113] = 0;
   out_48451545294533288[114] = 1;
   out_48451545294533288[115] = 0;
   out_48451545294533288[116] = 0;
   out_48451545294533288[117] = 0;
   out_48451545294533288[118] = 0;
   out_48451545294533288[119] = 0;
   out_48451545294533288[120] = 0;
   out_48451545294533288[121] = 0;
   out_48451545294533288[122] = 0;
   out_48451545294533288[123] = 0;
   out_48451545294533288[124] = 0;
   out_48451545294533288[125] = 0;
   out_48451545294533288[126] = 0;
   out_48451545294533288[127] = 0;
   out_48451545294533288[128] = 0;
   out_48451545294533288[129] = 0;
   out_48451545294533288[130] = 0;
   out_48451545294533288[131] = 0;
   out_48451545294533288[132] = 0;
   out_48451545294533288[133] = 1;
   out_48451545294533288[134] = 0;
   out_48451545294533288[135] = 0;
   out_48451545294533288[136] = 0;
   out_48451545294533288[137] = 0;
   out_48451545294533288[138] = 0;
   out_48451545294533288[139] = 0;
   out_48451545294533288[140] = 0;
   out_48451545294533288[141] = 0;
   out_48451545294533288[142] = 0;
   out_48451545294533288[143] = 0;
   out_48451545294533288[144] = 0;
   out_48451545294533288[145] = 0;
   out_48451545294533288[146] = 0;
   out_48451545294533288[147] = 0;
   out_48451545294533288[148] = 0;
   out_48451545294533288[149] = 0;
   out_48451545294533288[150] = 0;
   out_48451545294533288[151] = 0;
   out_48451545294533288[152] = 1;
   out_48451545294533288[153] = 0;
   out_48451545294533288[154] = 0;
   out_48451545294533288[155] = 0;
   out_48451545294533288[156] = 0;
   out_48451545294533288[157] = 0;
   out_48451545294533288[158] = 0;
   out_48451545294533288[159] = 0;
   out_48451545294533288[160] = 0;
   out_48451545294533288[161] = 0;
   out_48451545294533288[162] = 0;
   out_48451545294533288[163] = 0;
   out_48451545294533288[164] = 0;
   out_48451545294533288[165] = 0;
   out_48451545294533288[166] = 0;
   out_48451545294533288[167] = 0;
   out_48451545294533288[168] = 0;
   out_48451545294533288[169] = 0;
   out_48451545294533288[170] = 0;
   out_48451545294533288[171] = 1;
   out_48451545294533288[172] = 0;
   out_48451545294533288[173] = 0;
   out_48451545294533288[174] = 0;
   out_48451545294533288[175] = 0;
   out_48451545294533288[176] = 0;
   out_48451545294533288[177] = 0;
   out_48451545294533288[178] = 0;
   out_48451545294533288[179] = 0;
   out_48451545294533288[180] = 0;
   out_48451545294533288[181] = 0;
   out_48451545294533288[182] = 0;
   out_48451545294533288[183] = 0;
   out_48451545294533288[184] = 0;
   out_48451545294533288[185] = 0;
   out_48451545294533288[186] = 0;
   out_48451545294533288[187] = 0;
   out_48451545294533288[188] = 0;
   out_48451545294533288[189] = 0;
   out_48451545294533288[190] = 1;
   out_48451545294533288[191] = 0;
   out_48451545294533288[192] = 0;
   out_48451545294533288[193] = 0;
   out_48451545294533288[194] = 0;
   out_48451545294533288[195] = 0;
   out_48451545294533288[196] = 0;
   out_48451545294533288[197] = 0;
   out_48451545294533288[198] = 0;
   out_48451545294533288[199] = 0;
   out_48451545294533288[200] = 0;
   out_48451545294533288[201] = 0;
   out_48451545294533288[202] = 0;
   out_48451545294533288[203] = 0;
   out_48451545294533288[204] = 0;
   out_48451545294533288[205] = 0;
   out_48451545294533288[206] = 0;
   out_48451545294533288[207] = 0;
   out_48451545294533288[208] = 0;
   out_48451545294533288[209] = 1;
   out_48451545294533288[210] = 0;
   out_48451545294533288[211] = 0;
   out_48451545294533288[212] = 0;
   out_48451545294533288[213] = 0;
   out_48451545294533288[214] = 0;
   out_48451545294533288[215] = 0;
   out_48451545294533288[216] = 0;
   out_48451545294533288[217] = 0;
   out_48451545294533288[218] = 0;
   out_48451545294533288[219] = 0;
   out_48451545294533288[220] = 0;
   out_48451545294533288[221] = 0;
   out_48451545294533288[222] = 0;
   out_48451545294533288[223] = 0;
   out_48451545294533288[224] = 0;
   out_48451545294533288[225] = 0;
   out_48451545294533288[226] = 0;
   out_48451545294533288[227] = 0;
   out_48451545294533288[228] = 1;
   out_48451545294533288[229] = 0;
   out_48451545294533288[230] = 0;
   out_48451545294533288[231] = 0;
   out_48451545294533288[232] = 0;
   out_48451545294533288[233] = 0;
   out_48451545294533288[234] = 0;
   out_48451545294533288[235] = 0;
   out_48451545294533288[236] = 0;
   out_48451545294533288[237] = 0;
   out_48451545294533288[238] = 0;
   out_48451545294533288[239] = 0;
   out_48451545294533288[240] = 0;
   out_48451545294533288[241] = 0;
   out_48451545294533288[242] = 0;
   out_48451545294533288[243] = 0;
   out_48451545294533288[244] = 0;
   out_48451545294533288[245] = 0;
   out_48451545294533288[246] = 0;
   out_48451545294533288[247] = 1;
   out_48451545294533288[248] = 0;
   out_48451545294533288[249] = 0;
   out_48451545294533288[250] = 0;
   out_48451545294533288[251] = 0;
   out_48451545294533288[252] = 0;
   out_48451545294533288[253] = 0;
   out_48451545294533288[254] = 0;
   out_48451545294533288[255] = 0;
   out_48451545294533288[256] = 0;
   out_48451545294533288[257] = 0;
   out_48451545294533288[258] = 0;
   out_48451545294533288[259] = 0;
   out_48451545294533288[260] = 0;
   out_48451545294533288[261] = 0;
   out_48451545294533288[262] = 0;
   out_48451545294533288[263] = 0;
   out_48451545294533288[264] = 0;
   out_48451545294533288[265] = 0;
   out_48451545294533288[266] = 1;
   out_48451545294533288[267] = 0;
   out_48451545294533288[268] = 0;
   out_48451545294533288[269] = 0;
   out_48451545294533288[270] = 0;
   out_48451545294533288[271] = 0;
   out_48451545294533288[272] = 0;
   out_48451545294533288[273] = 0;
   out_48451545294533288[274] = 0;
   out_48451545294533288[275] = 0;
   out_48451545294533288[276] = 0;
   out_48451545294533288[277] = 0;
   out_48451545294533288[278] = 0;
   out_48451545294533288[279] = 0;
   out_48451545294533288[280] = 0;
   out_48451545294533288[281] = 0;
   out_48451545294533288[282] = 0;
   out_48451545294533288[283] = 0;
   out_48451545294533288[284] = 0;
   out_48451545294533288[285] = 1;
   out_48451545294533288[286] = 0;
   out_48451545294533288[287] = 0;
   out_48451545294533288[288] = 0;
   out_48451545294533288[289] = 0;
   out_48451545294533288[290] = 0;
   out_48451545294533288[291] = 0;
   out_48451545294533288[292] = 0;
   out_48451545294533288[293] = 0;
   out_48451545294533288[294] = 0;
   out_48451545294533288[295] = 0;
   out_48451545294533288[296] = 0;
   out_48451545294533288[297] = 0;
   out_48451545294533288[298] = 0;
   out_48451545294533288[299] = 0;
   out_48451545294533288[300] = 0;
   out_48451545294533288[301] = 0;
   out_48451545294533288[302] = 0;
   out_48451545294533288[303] = 0;
   out_48451545294533288[304] = 1;
   out_48451545294533288[305] = 0;
   out_48451545294533288[306] = 0;
   out_48451545294533288[307] = 0;
   out_48451545294533288[308] = 0;
   out_48451545294533288[309] = 0;
   out_48451545294533288[310] = 0;
   out_48451545294533288[311] = 0;
   out_48451545294533288[312] = 0;
   out_48451545294533288[313] = 0;
   out_48451545294533288[314] = 0;
   out_48451545294533288[315] = 0;
   out_48451545294533288[316] = 0;
   out_48451545294533288[317] = 0;
   out_48451545294533288[318] = 0;
   out_48451545294533288[319] = 0;
   out_48451545294533288[320] = 0;
   out_48451545294533288[321] = 0;
   out_48451545294533288[322] = 0;
   out_48451545294533288[323] = 1;
}
void h_4(double *state, double *unused, double *out_711207782401779392) {
   out_711207782401779392[0] = state[6] + state[9];
   out_711207782401779392[1] = state[7] + state[10];
   out_711207782401779392[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_6437019938278623926) {
   out_6437019938278623926[0] = 0;
   out_6437019938278623926[1] = 0;
   out_6437019938278623926[2] = 0;
   out_6437019938278623926[3] = 0;
   out_6437019938278623926[4] = 0;
   out_6437019938278623926[5] = 0;
   out_6437019938278623926[6] = 1;
   out_6437019938278623926[7] = 0;
   out_6437019938278623926[8] = 0;
   out_6437019938278623926[9] = 1;
   out_6437019938278623926[10] = 0;
   out_6437019938278623926[11] = 0;
   out_6437019938278623926[12] = 0;
   out_6437019938278623926[13] = 0;
   out_6437019938278623926[14] = 0;
   out_6437019938278623926[15] = 0;
   out_6437019938278623926[16] = 0;
   out_6437019938278623926[17] = 0;
   out_6437019938278623926[18] = 0;
   out_6437019938278623926[19] = 0;
   out_6437019938278623926[20] = 0;
   out_6437019938278623926[21] = 0;
   out_6437019938278623926[22] = 0;
   out_6437019938278623926[23] = 0;
   out_6437019938278623926[24] = 0;
   out_6437019938278623926[25] = 1;
   out_6437019938278623926[26] = 0;
   out_6437019938278623926[27] = 0;
   out_6437019938278623926[28] = 1;
   out_6437019938278623926[29] = 0;
   out_6437019938278623926[30] = 0;
   out_6437019938278623926[31] = 0;
   out_6437019938278623926[32] = 0;
   out_6437019938278623926[33] = 0;
   out_6437019938278623926[34] = 0;
   out_6437019938278623926[35] = 0;
   out_6437019938278623926[36] = 0;
   out_6437019938278623926[37] = 0;
   out_6437019938278623926[38] = 0;
   out_6437019938278623926[39] = 0;
   out_6437019938278623926[40] = 0;
   out_6437019938278623926[41] = 0;
   out_6437019938278623926[42] = 0;
   out_6437019938278623926[43] = 0;
   out_6437019938278623926[44] = 1;
   out_6437019938278623926[45] = 0;
   out_6437019938278623926[46] = 0;
   out_6437019938278623926[47] = 1;
   out_6437019938278623926[48] = 0;
   out_6437019938278623926[49] = 0;
   out_6437019938278623926[50] = 0;
   out_6437019938278623926[51] = 0;
   out_6437019938278623926[52] = 0;
   out_6437019938278623926[53] = 0;
}
void h_10(double *state, double *unused, double *out_2942660564170460979) {
   out_2942660564170460979[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_2942660564170460979[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_2942660564170460979[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_7753365329259358525) {
   out_7753365329259358525[0] = 0;
   out_7753365329259358525[1] = 9.8100000000000005*cos(state[1]);
   out_7753365329259358525[2] = 0;
   out_7753365329259358525[3] = 0;
   out_7753365329259358525[4] = -state[8];
   out_7753365329259358525[5] = state[7];
   out_7753365329259358525[6] = 0;
   out_7753365329259358525[7] = state[5];
   out_7753365329259358525[8] = -state[4];
   out_7753365329259358525[9] = 0;
   out_7753365329259358525[10] = 0;
   out_7753365329259358525[11] = 0;
   out_7753365329259358525[12] = 1;
   out_7753365329259358525[13] = 0;
   out_7753365329259358525[14] = 0;
   out_7753365329259358525[15] = 1;
   out_7753365329259358525[16] = 0;
   out_7753365329259358525[17] = 0;
   out_7753365329259358525[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_7753365329259358525[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_7753365329259358525[20] = 0;
   out_7753365329259358525[21] = state[8];
   out_7753365329259358525[22] = 0;
   out_7753365329259358525[23] = -state[6];
   out_7753365329259358525[24] = -state[5];
   out_7753365329259358525[25] = 0;
   out_7753365329259358525[26] = state[3];
   out_7753365329259358525[27] = 0;
   out_7753365329259358525[28] = 0;
   out_7753365329259358525[29] = 0;
   out_7753365329259358525[30] = 0;
   out_7753365329259358525[31] = 1;
   out_7753365329259358525[32] = 0;
   out_7753365329259358525[33] = 0;
   out_7753365329259358525[34] = 1;
   out_7753365329259358525[35] = 0;
   out_7753365329259358525[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_7753365329259358525[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_7753365329259358525[38] = 0;
   out_7753365329259358525[39] = -state[7];
   out_7753365329259358525[40] = state[6];
   out_7753365329259358525[41] = 0;
   out_7753365329259358525[42] = state[4];
   out_7753365329259358525[43] = -state[3];
   out_7753365329259358525[44] = 0;
   out_7753365329259358525[45] = 0;
   out_7753365329259358525[46] = 0;
   out_7753365329259358525[47] = 0;
   out_7753365329259358525[48] = 0;
   out_7753365329259358525[49] = 0;
   out_7753365329259358525[50] = 1;
   out_7753365329259358525[51] = 0;
   out_7753365329259358525[52] = 0;
   out_7753365329259358525[53] = 1;
}
void h_13(double *state, double *unused, double *out_2914132243760424113) {
   out_2914132243760424113[0] = state[3];
   out_2914132243760424113[1] = state[4];
   out_2914132243760424113[2] = state[5];
}
void H_13(double *state, double *unused, double *out_3224746112946291125) {
   out_3224746112946291125[0] = 0;
   out_3224746112946291125[1] = 0;
   out_3224746112946291125[2] = 0;
   out_3224746112946291125[3] = 1;
   out_3224746112946291125[4] = 0;
   out_3224746112946291125[5] = 0;
   out_3224746112946291125[6] = 0;
   out_3224746112946291125[7] = 0;
   out_3224746112946291125[8] = 0;
   out_3224746112946291125[9] = 0;
   out_3224746112946291125[10] = 0;
   out_3224746112946291125[11] = 0;
   out_3224746112946291125[12] = 0;
   out_3224746112946291125[13] = 0;
   out_3224746112946291125[14] = 0;
   out_3224746112946291125[15] = 0;
   out_3224746112946291125[16] = 0;
   out_3224746112946291125[17] = 0;
   out_3224746112946291125[18] = 0;
   out_3224746112946291125[19] = 0;
   out_3224746112946291125[20] = 0;
   out_3224746112946291125[21] = 0;
   out_3224746112946291125[22] = 1;
   out_3224746112946291125[23] = 0;
   out_3224746112946291125[24] = 0;
   out_3224746112946291125[25] = 0;
   out_3224746112946291125[26] = 0;
   out_3224746112946291125[27] = 0;
   out_3224746112946291125[28] = 0;
   out_3224746112946291125[29] = 0;
   out_3224746112946291125[30] = 0;
   out_3224746112946291125[31] = 0;
   out_3224746112946291125[32] = 0;
   out_3224746112946291125[33] = 0;
   out_3224746112946291125[34] = 0;
   out_3224746112946291125[35] = 0;
   out_3224746112946291125[36] = 0;
   out_3224746112946291125[37] = 0;
   out_3224746112946291125[38] = 0;
   out_3224746112946291125[39] = 0;
   out_3224746112946291125[40] = 0;
   out_3224746112946291125[41] = 1;
   out_3224746112946291125[42] = 0;
   out_3224746112946291125[43] = 0;
   out_3224746112946291125[44] = 0;
   out_3224746112946291125[45] = 0;
   out_3224746112946291125[46] = 0;
   out_3224746112946291125[47] = 0;
   out_3224746112946291125[48] = 0;
   out_3224746112946291125[49] = 0;
   out_3224746112946291125[50] = 0;
   out_3224746112946291125[51] = 0;
   out_3224746112946291125[52] = 0;
   out_3224746112946291125[53] = 0;
}
void h_14(double *state, double *unused, double *out_677306400367602538) {
   out_677306400367602538[0] = state[6];
   out_677306400367602538[1] = state[7];
   out_677306400367602538[2] = state[8];
}
void H_14(double *state, double *unused, double *out_2473779081939139397) {
   out_2473779081939139397[0] = 0;
   out_2473779081939139397[1] = 0;
   out_2473779081939139397[2] = 0;
   out_2473779081939139397[3] = 0;
   out_2473779081939139397[4] = 0;
   out_2473779081939139397[5] = 0;
   out_2473779081939139397[6] = 1;
   out_2473779081939139397[7] = 0;
   out_2473779081939139397[8] = 0;
   out_2473779081939139397[9] = 0;
   out_2473779081939139397[10] = 0;
   out_2473779081939139397[11] = 0;
   out_2473779081939139397[12] = 0;
   out_2473779081939139397[13] = 0;
   out_2473779081939139397[14] = 0;
   out_2473779081939139397[15] = 0;
   out_2473779081939139397[16] = 0;
   out_2473779081939139397[17] = 0;
   out_2473779081939139397[18] = 0;
   out_2473779081939139397[19] = 0;
   out_2473779081939139397[20] = 0;
   out_2473779081939139397[21] = 0;
   out_2473779081939139397[22] = 0;
   out_2473779081939139397[23] = 0;
   out_2473779081939139397[24] = 0;
   out_2473779081939139397[25] = 1;
   out_2473779081939139397[26] = 0;
   out_2473779081939139397[27] = 0;
   out_2473779081939139397[28] = 0;
   out_2473779081939139397[29] = 0;
   out_2473779081939139397[30] = 0;
   out_2473779081939139397[31] = 0;
   out_2473779081939139397[32] = 0;
   out_2473779081939139397[33] = 0;
   out_2473779081939139397[34] = 0;
   out_2473779081939139397[35] = 0;
   out_2473779081939139397[36] = 0;
   out_2473779081939139397[37] = 0;
   out_2473779081939139397[38] = 0;
   out_2473779081939139397[39] = 0;
   out_2473779081939139397[40] = 0;
   out_2473779081939139397[41] = 0;
   out_2473779081939139397[42] = 0;
   out_2473779081939139397[43] = 0;
   out_2473779081939139397[44] = 1;
   out_2473779081939139397[45] = 0;
   out_2473779081939139397[46] = 0;
   out_2473779081939139397[47] = 0;
   out_2473779081939139397[48] = 0;
   out_2473779081939139397[49] = 0;
   out_2473779081939139397[50] = 0;
   out_2473779081939139397[51] = 0;
   out_2473779081939139397[52] = 0;
   out_2473779081939139397[53] = 0;
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
void pose_err_fun(double *nom_x, double *delta_x, double *out_1227579335886564773) {
  err_fun(nom_x, delta_x, out_1227579335886564773);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_7708296302708828001) {
  inv_err_fun(nom_x, true_x, out_7708296302708828001);
}
void pose_H_mod_fun(double *state, double *out_145151651698479708) {
  H_mod_fun(state, out_145151651698479708);
}
void pose_f_fun(double *state, double dt, double *out_6753877240357292479) {
  f_fun(state,  dt, out_6753877240357292479);
}
void pose_F_fun(double *state, double dt, double *out_48451545294533288) {
  F_fun(state,  dt, out_48451545294533288);
}
void pose_h_4(double *state, double *unused, double *out_711207782401779392) {
  h_4(state, unused, out_711207782401779392);
}
void pose_H_4(double *state, double *unused, double *out_6437019938278623926) {
  H_4(state, unused, out_6437019938278623926);
}
void pose_h_10(double *state, double *unused, double *out_2942660564170460979) {
  h_10(state, unused, out_2942660564170460979);
}
void pose_H_10(double *state, double *unused, double *out_7753365329259358525) {
  H_10(state, unused, out_7753365329259358525);
}
void pose_h_13(double *state, double *unused, double *out_2914132243760424113) {
  h_13(state, unused, out_2914132243760424113);
}
void pose_H_13(double *state, double *unused, double *out_3224746112946291125) {
  H_13(state, unused, out_3224746112946291125);
}
void pose_h_14(double *state, double *unused, double *out_677306400367602538) {
  h_14(state, unused, out_677306400367602538);
}
void pose_H_14(double *state, double *unused, double *out_2473779081939139397) {
  H_14(state, unused, out_2473779081939139397);
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
