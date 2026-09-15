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
void err_fun(double *nom_x, double *delta_x, double *out_8294180210607547219) {
   out_8294180210607547219[0] = delta_x[0] + nom_x[0];
   out_8294180210607547219[1] = delta_x[1] + nom_x[1];
   out_8294180210607547219[2] = delta_x[2] + nom_x[2];
   out_8294180210607547219[3] = delta_x[3] + nom_x[3];
   out_8294180210607547219[4] = delta_x[4] + nom_x[4];
   out_8294180210607547219[5] = delta_x[5] + nom_x[5];
   out_8294180210607547219[6] = delta_x[6] + nom_x[6];
   out_8294180210607547219[7] = delta_x[7] + nom_x[7];
   out_8294180210607547219[8] = delta_x[8] + nom_x[8];
   out_8294180210607547219[9] = delta_x[9] + nom_x[9];
   out_8294180210607547219[10] = delta_x[10] + nom_x[10];
   out_8294180210607547219[11] = delta_x[11] + nom_x[11];
   out_8294180210607547219[12] = delta_x[12] + nom_x[12];
   out_8294180210607547219[13] = delta_x[13] + nom_x[13];
   out_8294180210607547219[14] = delta_x[14] + nom_x[14];
   out_8294180210607547219[15] = delta_x[15] + nom_x[15];
   out_8294180210607547219[16] = delta_x[16] + nom_x[16];
   out_8294180210607547219[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_8330596021821018044) {
   out_8330596021821018044[0] = -nom_x[0] + true_x[0];
   out_8330596021821018044[1] = -nom_x[1] + true_x[1];
   out_8330596021821018044[2] = -nom_x[2] + true_x[2];
   out_8330596021821018044[3] = -nom_x[3] + true_x[3];
   out_8330596021821018044[4] = -nom_x[4] + true_x[4];
   out_8330596021821018044[5] = -nom_x[5] + true_x[5];
   out_8330596021821018044[6] = -nom_x[6] + true_x[6];
   out_8330596021821018044[7] = -nom_x[7] + true_x[7];
   out_8330596021821018044[8] = -nom_x[8] + true_x[8];
   out_8330596021821018044[9] = -nom_x[9] + true_x[9];
   out_8330596021821018044[10] = -nom_x[10] + true_x[10];
   out_8330596021821018044[11] = -nom_x[11] + true_x[11];
   out_8330596021821018044[12] = -nom_x[12] + true_x[12];
   out_8330596021821018044[13] = -nom_x[13] + true_x[13];
   out_8330596021821018044[14] = -nom_x[14] + true_x[14];
   out_8330596021821018044[15] = -nom_x[15] + true_x[15];
   out_8330596021821018044[16] = -nom_x[16] + true_x[16];
   out_8330596021821018044[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_534058243187542804) {
   out_534058243187542804[0] = 1.0;
   out_534058243187542804[1] = 0.0;
   out_534058243187542804[2] = 0.0;
   out_534058243187542804[3] = 0.0;
   out_534058243187542804[4] = 0.0;
   out_534058243187542804[5] = 0.0;
   out_534058243187542804[6] = 0.0;
   out_534058243187542804[7] = 0.0;
   out_534058243187542804[8] = 0.0;
   out_534058243187542804[9] = 0.0;
   out_534058243187542804[10] = 0.0;
   out_534058243187542804[11] = 0.0;
   out_534058243187542804[12] = 0.0;
   out_534058243187542804[13] = 0.0;
   out_534058243187542804[14] = 0.0;
   out_534058243187542804[15] = 0.0;
   out_534058243187542804[16] = 0.0;
   out_534058243187542804[17] = 0.0;
   out_534058243187542804[18] = 0.0;
   out_534058243187542804[19] = 1.0;
   out_534058243187542804[20] = 0.0;
   out_534058243187542804[21] = 0.0;
   out_534058243187542804[22] = 0.0;
   out_534058243187542804[23] = 0.0;
   out_534058243187542804[24] = 0.0;
   out_534058243187542804[25] = 0.0;
   out_534058243187542804[26] = 0.0;
   out_534058243187542804[27] = 0.0;
   out_534058243187542804[28] = 0.0;
   out_534058243187542804[29] = 0.0;
   out_534058243187542804[30] = 0.0;
   out_534058243187542804[31] = 0.0;
   out_534058243187542804[32] = 0.0;
   out_534058243187542804[33] = 0.0;
   out_534058243187542804[34] = 0.0;
   out_534058243187542804[35] = 0.0;
   out_534058243187542804[36] = 0.0;
   out_534058243187542804[37] = 0.0;
   out_534058243187542804[38] = 1.0;
   out_534058243187542804[39] = 0.0;
   out_534058243187542804[40] = 0.0;
   out_534058243187542804[41] = 0.0;
   out_534058243187542804[42] = 0.0;
   out_534058243187542804[43] = 0.0;
   out_534058243187542804[44] = 0.0;
   out_534058243187542804[45] = 0.0;
   out_534058243187542804[46] = 0.0;
   out_534058243187542804[47] = 0.0;
   out_534058243187542804[48] = 0.0;
   out_534058243187542804[49] = 0.0;
   out_534058243187542804[50] = 0.0;
   out_534058243187542804[51] = 0.0;
   out_534058243187542804[52] = 0.0;
   out_534058243187542804[53] = 0.0;
   out_534058243187542804[54] = 0.0;
   out_534058243187542804[55] = 0.0;
   out_534058243187542804[56] = 0.0;
   out_534058243187542804[57] = 1.0;
   out_534058243187542804[58] = 0.0;
   out_534058243187542804[59] = 0.0;
   out_534058243187542804[60] = 0.0;
   out_534058243187542804[61] = 0.0;
   out_534058243187542804[62] = 0.0;
   out_534058243187542804[63] = 0.0;
   out_534058243187542804[64] = 0.0;
   out_534058243187542804[65] = 0.0;
   out_534058243187542804[66] = 0.0;
   out_534058243187542804[67] = 0.0;
   out_534058243187542804[68] = 0.0;
   out_534058243187542804[69] = 0.0;
   out_534058243187542804[70] = 0.0;
   out_534058243187542804[71] = 0.0;
   out_534058243187542804[72] = 0.0;
   out_534058243187542804[73] = 0.0;
   out_534058243187542804[74] = 0.0;
   out_534058243187542804[75] = 0.0;
   out_534058243187542804[76] = 1.0;
   out_534058243187542804[77] = 0.0;
   out_534058243187542804[78] = 0.0;
   out_534058243187542804[79] = 0.0;
   out_534058243187542804[80] = 0.0;
   out_534058243187542804[81] = 0.0;
   out_534058243187542804[82] = 0.0;
   out_534058243187542804[83] = 0.0;
   out_534058243187542804[84] = 0.0;
   out_534058243187542804[85] = 0.0;
   out_534058243187542804[86] = 0.0;
   out_534058243187542804[87] = 0.0;
   out_534058243187542804[88] = 0.0;
   out_534058243187542804[89] = 0.0;
   out_534058243187542804[90] = 0.0;
   out_534058243187542804[91] = 0.0;
   out_534058243187542804[92] = 0.0;
   out_534058243187542804[93] = 0.0;
   out_534058243187542804[94] = 0.0;
   out_534058243187542804[95] = 1.0;
   out_534058243187542804[96] = 0.0;
   out_534058243187542804[97] = 0.0;
   out_534058243187542804[98] = 0.0;
   out_534058243187542804[99] = 0.0;
   out_534058243187542804[100] = 0.0;
   out_534058243187542804[101] = 0.0;
   out_534058243187542804[102] = 0.0;
   out_534058243187542804[103] = 0.0;
   out_534058243187542804[104] = 0.0;
   out_534058243187542804[105] = 0.0;
   out_534058243187542804[106] = 0.0;
   out_534058243187542804[107] = 0.0;
   out_534058243187542804[108] = 0.0;
   out_534058243187542804[109] = 0.0;
   out_534058243187542804[110] = 0.0;
   out_534058243187542804[111] = 0.0;
   out_534058243187542804[112] = 0.0;
   out_534058243187542804[113] = 0.0;
   out_534058243187542804[114] = 1.0;
   out_534058243187542804[115] = 0.0;
   out_534058243187542804[116] = 0.0;
   out_534058243187542804[117] = 0.0;
   out_534058243187542804[118] = 0.0;
   out_534058243187542804[119] = 0.0;
   out_534058243187542804[120] = 0.0;
   out_534058243187542804[121] = 0.0;
   out_534058243187542804[122] = 0.0;
   out_534058243187542804[123] = 0.0;
   out_534058243187542804[124] = 0.0;
   out_534058243187542804[125] = 0.0;
   out_534058243187542804[126] = 0.0;
   out_534058243187542804[127] = 0.0;
   out_534058243187542804[128] = 0.0;
   out_534058243187542804[129] = 0.0;
   out_534058243187542804[130] = 0.0;
   out_534058243187542804[131] = 0.0;
   out_534058243187542804[132] = 0.0;
   out_534058243187542804[133] = 1.0;
   out_534058243187542804[134] = 0.0;
   out_534058243187542804[135] = 0.0;
   out_534058243187542804[136] = 0.0;
   out_534058243187542804[137] = 0.0;
   out_534058243187542804[138] = 0.0;
   out_534058243187542804[139] = 0.0;
   out_534058243187542804[140] = 0.0;
   out_534058243187542804[141] = 0.0;
   out_534058243187542804[142] = 0.0;
   out_534058243187542804[143] = 0.0;
   out_534058243187542804[144] = 0.0;
   out_534058243187542804[145] = 0.0;
   out_534058243187542804[146] = 0.0;
   out_534058243187542804[147] = 0.0;
   out_534058243187542804[148] = 0.0;
   out_534058243187542804[149] = 0.0;
   out_534058243187542804[150] = 0.0;
   out_534058243187542804[151] = 0.0;
   out_534058243187542804[152] = 1.0;
   out_534058243187542804[153] = 0.0;
   out_534058243187542804[154] = 0.0;
   out_534058243187542804[155] = 0.0;
   out_534058243187542804[156] = 0.0;
   out_534058243187542804[157] = 0.0;
   out_534058243187542804[158] = 0.0;
   out_534058243187542804[159] = 0.0;
   out_534058243187542804[160] = 0.0;
   out_534058243187542804[161] = 0.0;
   out_534058243187542804[162] = 0.0;
   out_534058243187542804[163] = 0.0;
   out_534058243187542804[164] = 0.0;
   out_534058243187542804[165] = 0.0;
   out_534058243187542804[166] = 0.0;
   out_534058243187542804[167] = 0.0;
   out_534058243187542804[168] = 0.0;
   out_534058243187542804[169] = 0.0;
   out_534058243187542804[170] = 0.0;
   out_534058243187542804[171] = 1.0;
   out_534058243187542804[172] = 0.0;
   out_534058243187542804[173] = 0.0;
   out_534058243187542804[174] = 0.0;
   out_534058243187542804[175] = 0.0;
   out_534058243187542804[176] = 0.0;
   out_534058243187542804[177] = 0.0;
   out_534058243187542804[178] = 0.0;
   out_534058243187542804[179] = 0.0;
   out_534058243187542804[180] = 0.0;
   out_534058243187542804[181] = 0.0;
   out_534058243187542804[182] = 0.0;
   out_534058243187542804[183] = 0.0;
   out_534058243187542804[184] = 0.0;
   out_534058243187542804[185] = 0.0;
   out_534058243187542804[186] = 0.0;
   out_534058243187542804[187] = 0.0;
   out_534058243187542804[188] = 0.0;
   out_534058243187542804[189] = 0.0;
   out_534058243187542804[190] = 1.0;
   out_534058243187542804[191] = 0.0;
   out_534058243187542804[192] = 0.0;
   out_534058243187542804[193] = 0.0;
   out_534058243187542804[194] = 0.0;
   out_534058243187542804[195] = 0.0;
   out_534058243187542804[196] = 0.0;
   out_534058243187542804[197] = 0.0;
   out_534058243187542804[198] = 0.0;
   out_534058243187542804[199] = 0.0;
   out_534058243187542804[200] = 0.0;
   out_534058243187542804[201] = 0.0;
   out_534058243187542804[202] = 0.0;
   out_534058243187542804[203] = 0.0;
   out_534058243187542804[204] = 0.0;
   out_534058243187542804[205] = 0.0;
   out_534058243187542804[206] = 0.0;
   out_534058243187542804[207] = 0.0;
   out_534058243187542804[208] = 0.0;
   out_534058243187542804[209] = 1.0;
   out_534058243187542804[210] = 0.0;
   out_534058243187542804[211] = 0.0;
   out_534058243187542804[212] = 0.0;
   out_534058243187542804[213] = 0.0;
   out_534058243187542804[214] = 0.0;
   out_534058243187542804[215] = 0.0;
   out_534058243187542804[216] = 0.0;
   out_534058243187542804[217] = 0.0;
   out_534058243187542804[218] = 0.0;
   out_534058243187542804[219] = 0.0;
   out_534058243187542804[220] = 0.0;
   out_534058243187542804[221] = 0.0;
   out_534058243187542804[222] = 0.0;
   out_534058243187542804[223] = 0.0;
   out_534058243187542804[224] = 0.0;
   out_534058243187542804[225] = 0.0;
   out_534058243187542804[226] = 0.0;
   out_534058243187542804[227] = 0.0;
   out_534058243187542804[228] = 1.0;
   out_534058243187542804[229] = 0.0;
   out_534058243187542804[230] = 0.0;
   out_534058243187542804[231] = 0.0;
   out_534058243187542804[232] = 0.0;
   out_534058243187542804[233] = 0.0;
   out_534058243187542804[234] = 0.0;
   out_534058243187542804[235] = 0.0;
   out_534058243187542804[236] = 0.0;
   out_534058243187542804[237] = 0.0;
   out_534058243187542804[238] = 0.0;
   out_534058243187542804[239] = 0.0;
   out_534058243187542804[240] = 0.0;
   out_534058243187542804[241] = 0.0;
   out_534058243187542804[242] = 0.0;
   out_534058243187542804[243] = 0.0;
   out_534058243187542804[244] = 0.0;
   out_534058243187542804[245] = 0.0;
   out_534058243187542804[246] = 0.0;
   out_534058243187542804[247] = 1.0;
   out_534058243187542804[248] = 0.0;
   out_534058243187542804[249] = 0.0;
   out_534058243187542804[250] = 0.0;
   out_534058243187542804[251] = 0.0;
   out_534058243187542804[252] = 0.0;
   out_534058243187542804[253] = 0.0;
   out_534058243187542804[254] = 0.0;
   out_534058243187542804[255] = 0.0;
   out_534058243187542804[256] = 0.0;
   out_534058243187542804[257] = 0.0;
   out_534058243187542804[258] = 0.0;
   out_534058243187542804[259] = 0.0;
   out_534058243187542804[260] = 0.0;
   out_534058243187542804[261] = 0.0;
   out_534058243187542804[262] = 0.0;
   out_534058243187542804[263] = 0.0;
   out_534058243187542804[264] = 0.0;
   out_534058243187542804[265] = 0.0;
   out_534058243187542804[266] = 1.0;
   out_534058243187542804[267] = 0.0;
   out_534058243187542804[268] = 0.0;
   out_534058243187542804[269] = 0.0;
   out_534058243187542804[270] = 0.0;
   out_534058243187542804[271] = 0.0;
   out_534058243187542804[272] = 0.0;
   out_534058243187542804[273] = 0.0;
   out_534058243187542804[274] = 0.0;
   out_534058243187542804[275] = 0.0;
   out_534058243187542804[276] = 0.0;
   out_534058243187542804[277] = 0.0;
   out_534058243187542804[278] = 0.0;
   out_534058243187542804[279] = 0.0;
   out_534058243187542804[280] = 0.0;
   out_534058243187542804[281] = 0.0;
   out_534058243187542804[282] = 0.0;
   out_534058243187542804[283] = 0.0;
   out_534058243187542804[284] = 0.0;
   out_534058243187542804[285] = 1.0;
   out_534058243187542804[286] = 0.0;
   out_534058243187542804[287] = 0.0;
   out_534058243187542804[288] = 0.0;
   out_534058243187542804[289] = 0.0;
   out_534058243187542804[290] = 0.0;
   out_534058243187542804[291] = 0.0;
   out_534058243187542804[292] = 0.0;
   out_534058243187542804[293] = 0.0;
   out_534058243187542804[294] = 0.0;
   out_534058243187542804[295] = 0.0;
   out_534058243187542804[296] = 0.0;
   out_534058243187542804[297] = 0.0;
   out_534058243187542804[298] = 0.0;
   out_534058243187542804[299] = 0.0;
   out_534058243187542804[300] = 0.0;
   out_534058243187542804[301] = 0.0;
   out_534058243187542804[302] = 0.0;
   out_534058243187542804[303] = 0.0;
   out_534058243187542804[304] = 1.0;
   out_534058243187542804[305] = 0.0;
   out_534058243187542804[306] = 0.0;
   out_534058243187542804[307] = 0.0;
   out_534058243187542804[308] = 0.0;
   out_534058243187542804[309] = 0.0;
   out_534058243187542804[310] = 0.0;
   out_534058243187542804[311] = 0.0;
   out_534058243187542804[312] = 0.0;
   out_534058243187542804[313] = 0.0;
   out_534058243187542804[314] = 0.0;
   out_534058243187542804[315] = 0.0;
   out_534058243187542804[316] = 0.0;
   out_534058243187542804[317] = 0.0;
   out_534058243187542804[318] = 0.0;
   out_534058243187542804[319] = 0.0;
   out_534058243187542804[320] = 0.0;
   out_534058243187542804[321] = 0.0;
   out_534058243187542804[322] = 0.0;
   out_534058243187542804[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_2535209606058579312) {
   out_2535209606058579312[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_2535209606058579312[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_2535209606058579312[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_2535209606058579312[3] = dt*state[12] + state[3];
   out_2535209606058579312[4] = dt*state[13] + state[4];
   out_2535209606058579312[5] = dt*state[14] + state[5];
   out_2535209606058579312[6] = state[6];
   out_2535209606058579312[7] = state[7];
   out_2535209606058579312[8] = state[8];
   out_2535209606058579312[9] = state[9];
   out_2535209606058579312[10] = state[10];
   out_2535209606058579312[11] = state[11];
   out_2535209606058579312[12] = state[12];
   out_2535209606058579312[13] = state[13];
   out_2535209606058579312[14] = state[14];
   out_2535209606058579312[15] = state[15];
   out_2535209606058579312[16] = state[16];
   out_2535209606058579312[17] = state[17];
}
void F_fun(double *state, double dt, double *out_4915847086962688884) {
   out_4915847086962688884[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4915847086962688884[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4915847086962688884[2] = 0;
   out_4915847086962688884[3] = 0;
   out_4915847086962688884[4] = 0;
   out_4915847086962688884[5] = 0;
   out_4915847086962688884[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4915847086962688884[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4915847086962688884[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_4915847086962688884[9] = 0;
   out_4915847086962688884[10] = 0;
   out_4915847086962688884[11] = 0;
   out_4915847086962688884[12] = 0;
   out_4915847086962688884[13] = 0;
   out_4915847086962688884[14] = 0;
   out_4915847086962688884[15] = 0;
   out_4915847086962688884[16] = 0;
   out_4915847086962688884[17] = 0;
   out_4915847086962688884[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4915847086962688884[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4915847086962688884[20] = 0;
   out_4915847086962688884[21] = 0;
   out_4915847086962688884[22] = 0;
   out_4915847086962688884[23] = 0;
   out_4915847086962688884[24] = 0;
   out_4915847086962688884[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4915847086962688884[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_4915847086962688884[27] = 0;
   out_4915847086962688884[28] = 0;
   out_4915847086962688884[29] = 0;
   out_4915847086962688884[30] = 0;
   out_4915847086962688884[31] = 0;
   out_4915847086962688884[32] = 0;
   out_4915847086962688884[33] = 0;
   out_4915847086962688884[34] = 0;
   out_4915847086962688884[35] = 0;
   out_4915847086962688884[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4915847086962688884[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4915847086962688884[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4915847086962688884[39] = 0;
   out_4915847086962688884[40] = 0;
   out_4915847086962688884[41] = 0;
   out_4915847086962688884[42] = 0;
   out_4915847086962688884[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4915847086962688884[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_4915847086962688884[45] = 0;
   out_4915847086962688884[46] = 0;
   out_4915847086962688884[47] = 0;
   out_4915847086962688884[48] = 0;
   out_4915847086962688884[49] = 0;
   out_4915847086962688884[50] = 0;
   out_4915847086962688884[51] = 0;
   out_4915847086962688884[52] = 0;
   out_4915847086962688884[53] = 0;
   out_4915847086962688884[54] = 0;
   out_4915847086962688884[55] = 0;
   out_4915847086962688884[56] = 0;
   out_4915847086962688884[57] = 1;
   out_4915847086962688884[58] = 0;
   out_4915847086962688884[59] = 0;
   out_4915847086962688884[60] = 0;
   out_4915847086962688884[61] = 0;
   out_4915847086962688884[62] = 0;
   out_4915847086962688884[63] = 0;
   out_4915847086962688884[64] = 0;
   out_4915847086962688884[65] = 0;
   out_4915847086962688884[66] = dt;
   out_4915847086962688884[67] = 0;
   out_4915847086962688884[68] = 0;
   out_4915847086962688884[69] = 0;
   out_4915847086962688884[70] = 0;
   out_4915847086962688884[71] = 0;
   out_4915847086962688884[72] = 0;
   out_4915847086962688884[73] = 0;
   out_4915847086962688884[74] = 0;
   out_4915847086962688884[75] = 0;
   out_4915847086962688884[76] = 1;
   out_4915847086962688884[77] = 0;
   out_4915847086962688884[78] = 0;
   out_4915847086962688884[79] = 0;
   out_4915847086962688884[80] = 0;
   out_4915847086962688884[81] = 0;
   out_4915847086962688884[82] = 0;
   out_4915847086962688884[83] = 0;
   out_4915847086962688884[84] = 0;
   out_4915847086962688884[85] = dt;
   out_4915847086962688884[86] = 0;
   out_4915847086962688884[87] = 0;
   out_4915847086962688884[88] = 0;
   out_4915847086962688884[89] = 0;
   out_4915847086962688884[90] = 0;
   out_4915847086962688884[91] = 0;
   out_4915847086962688884[92] = 0;
   out_4915847086962688884[93] = 0;
   out_4915847086962688884[94] = 0;
   out_4915847086962688884[95] = 1;
   out_4915847086962688884[96] = 0;
   out_4915847086962688884[97] = 0;
   out_4915847086962688884[98] = 0;
   out_4915847086962688884[99] = 0;
   out_4915847086962688884[100] = 0;
   out_4915847086962688884[101] = 0;
   out_4915847086962688884[102] = 0;
   out_4915847086962688884[103] = 0;
   out_4915847086962688884[104] = dt;
   out_4915847086962688884[105] = 0;
   out_4915847086962688884[106] = 0;
   out_4915847086962688884[107] = 0;
   out_4915847086962688884[108] = 0;
   out_4915847086962688884[109] = 0;
   out_4915847086962688884[110] = 0;
   out_4915847086962688884[111] = 0;
   out_4915847086962688884[112] = 0;
   out_4915847086962688884[113] = 0;
   out_4915847086962688884[114] = 1;
   out_4915847086962688884[115] = 0;
   out_4915847086962688884[116] = 0;
   out_4915847086962688884[117] = 0;
   out_4915847086962688884[118] = 0;
   out_4915847086962688884[119] = 0;
   out_4915847086962688884[120] = 0;
   out_4915847086962688884[121] = 0;
   out_4915847086962688884[122] = 0;
   out_4915847086962688884[123] = 0;
   out_4915847086962688884[124] = 0;
   out_4915847086962688884[125] = 0;
   out_4915847086962688884[126] = 0;
   out_4915847086962688884[127] = 0;
   out_4915847086962688884[128] = 0;
   out_4915847086962688884[129] = 0;
   out_4915847086962688884[130] = 0;
   out_4915847086962688884[131] = 0;
   out_4915847086962688884[132] = 0;
   out_4915847086962688884[133] = 1;
   out_4915847086962688884[134] = 0;
   out_4915847086962688884[135] = 0;
   out_4915847086962688884[136] = 0;
   out_4915847086962688884[137] = 0;
   out_4915847086962688884[138] = 0;
   out_4915847086962688884[139] = 0;
   out_4915847086962688884[140] = 0;
   out_4915847086962688884[141] = 0;
   out_4915847086962688884[142] = 0;
   out_4915847086962688884[143] = 0;
   out_4915847086962688884[144] = 0;
   out_4915847086962688884[145] = 0;
   out_4915847086962688884[146] = 0;
   out_4915847086962688884[147] = 0;
   out_4915847086962688884[148] = 0;
   out_4915847086962688884[149] = 0;
   out_4915847086962688884[150] = 0;
   out_4915847086962688884[151] = 0;
   out_4915847086962688884[152] = 1;
   out_4915847086962688884[153] = 0;
   out_4915847086962688884[154] = 0;
   out_4915847086962688884[155] = 0;
   out_4915847086962688884[156] = 0;
   out_4915847086962688884[157] = 0;
   out_4915847086962688884[158] = 0;
   out_4915847086962688884[159] = 0;
   out_4915847086962688884[160] = 0;
   out_4915847086962688884[161] = 0;
   out_4915847086962688884[162] = 0;
   out_4915847086962688884[163] = 0;
   out_4915847086962688884[164] = 0;
   out_4915847086962688884[165] = 0;
   out_4915847086962688884[166] = 0;
   out_4915847086962688884[167] = 0;
   out_4915847086962688884[168] = 0;
   out_4915847086962688884[169] = 0;
   out_4915847086962688884[170] = 0;
   out_4915847086962688884[171] = 1;
   out_4915847086962688884[172] = 0;
   out_4915847086962688884[173] = 0;
   out_4915847086962688884[174] = 0;
   out_4915847086962688884[175] = 0;
   out_4915847086962688884[176] = 0;
   out_4915847086962688884[177] = 0;
   out_4915847086962688884[178] = 0;
   out_4915847086962688884[179] = 0;
   out_4915847086962688884[180] = 0;
   out_4915847086962688884[181] = 0;
   out_4915847086962688884[182] = 0;
   out_4915847086962688884[183] = 0;
   out_4915847086962688884[184] = 0;
   out_4915847086962688884[185] = 0;
   out_4915847086962688884[186] = 0;
   out_4915847086962688884[187] = 0;
   out_4915847086962688884[188] = 0;
   out_4915847086962688884[189] = 0;
   out_4915847086962688884[190] = 1;
   out_4915847086962688884[191] = 0;
   out_4915847086962688884[192] = 0;
   out_4915847086962688884[193] = 0;
   out_4915847086962688884[194] = 0;
   out_4915847086962688884[195] = 0;
   out_4915847086962688884[196] = 0;
   out_4915847086962688884[197] = 0;
   out_4915847086962688884[198] = 0;
   out_4915847086962688884[199] = 0;
   out_4915847086962688884[200] = 0;
   out_4915847086962688884[201] = 0;
   out_4915847086962688884[202] = 0;
   out_4915847086962688884[203] = 0;
   out_4915847086962688884[204] = 0;
   out_4915847086962688884[205] = 0;
   out_4915847086962688884[206] = 0;
   out_4915847086962688884[207] = 0;
   out_4915847086962688884[208] = 0;
   out_4915847086962688884[209] = 1;
   out_4915847086962688884[210] = 0;
   out_4915847086962688884[211] = 0;
   out_4915847086962688884[212] = 0;
   out_4915847086962688884[213] = 0;
   out_4915847086962688884[214] = 0;
   out_4915847086962688884[215] = 0;
   out_4915847086962688884[216] = 0;
   out_4915847086962688884[217] = 0;
   out_4915847086962688884[218] = 0;
   out_4915847086962688884[219] = 0;
   out_4915847086962688884[220] = 0;
   out_4915847086962688884[221] = 0;
   out_4915847086962688884[222] = 0;
   out_4915847086962688884[223] = 0;
   out_4915847086962688884[224] = 0;
   out_4915847086962688884[225] = 0;
   out_4915847086962688884[226] = 0;
   out_4915847086962688884[227] = 0;
   out_4915847086962688884[228] = 1;
   out_4915847086962688884[229] = 0;
   out_4915847086962688884[230] = 0;
   out_4915847086962688884[231] = 0;
   out_4915847086962688884[232] = 0;
   out_4915847086962688884[233] = 0;
   out_4915847086962688884[234] = 0;
   out_4915847086962688884[235] = 0;
   out_4915847086962688884[236] = 0;
   out_4915847086962688884[237] = 0;
   out_4915847086962688884[238] = 0;
   out_4915847086962688884[239] = 0;
   out_4915847086962688884[240] = 0;
   out_4915847086962688884[241] = 0;
   out_4915847086962688884[242] = 0;
   out_4915847086962688884[243] = 0;
   out_4915847086962688884[244] = 0;
   out_4915847086962688884[245] = 0;
   out_4915847086962688884[246] = 0;
   out_4915847086962688884[247] = 1;
   out_4915847086962688884[248] = 0;
   out_4915847086962688884[249] = 0;
   out_4915847086962688884[250] = 0;
   out_4915847086962688884[251] = 0;
   out_4915847086962688884[252] = 0;
   out_4915847086962688884[253] = 0;
   out_4915847086962688884[254] = 0;
   out_4915847086962688884[255] = 0;
   out_4915847086962688884[256] = 0;
   out_4915847086962688884[257] = 0;
   out_4915847086962688884[258] = 0;
   out_4915847086962688884[259] = 0;
   out_4915847086962688884[260] = 0;
   out_4915847086962688884[261] = 0;
   out_4915847086962688884[262] = 0;
   out_4915847086962688884[263] = 0;
   out_4915847086962688884[264] = 0;
   out_4915847086962688884[265] = 0;
   out_4915847086962688884[266] = 1;
   out_4915847086962688884[267] = 0;
   out_4915847086962688884[268] = 0;
   out_4915847086962688884[269] = 0;
   out_4915847086962688884[270] = 0;
   out_4915847086962688884[271] = 0;
   out_4915847086962688884[272] = 0;
   out_4915847086962688884[273] = 0;
   out_4915847086962688884[274] = 0;
   out_4915847086962688884[275] = 0;
   out_4915847086962688884[276] = 0;
   out_4915847086962688884[277] = 0;
   out_4915847086962688884[278] = 0;
   out_4915847086962688884[279] = 0;
   out_4915847086962688884[280] = 0;
   out_4915847086962688884[281] = 0;
   out_4915847086962688884[282] = 0;
   out_4915847086962688884[283] = 0;
   out_4915847086962688884[284] = 0;
   out_4915847086962688884[285] = 1;
   out_4915847086962688884[286] = 0;
   out_4915847086962688884[287] = 0;
   out_4915847086962688884[288] = 0;
   out_4915847086962688884[289] = 0;
   out_4915847086962688884[290] = 0;
   out_4915847086962688884[291] = 0;
   out_4915847086962688884[292] = 0;
   out_4915847086962688884[293] = 0;
   out_4915847086962688884[294] = 0;
   out_4915847086962688884[295] = 0;
   out_4915847086962688884[296] = 0;
   out_4915847086962688884[297] = 0;
   out_4915847086962688884[298] = 0;
   out_4915847086962688884[299] = 0;
   out_4915847086962688884[300] = 0;
   out_4915847086962688884[301] = 0;
   out_4915847086962688884[302] = 0;
   out_4915847086962688884[303] = 0;
   out_4915847086962688884[304] = 1;
   out_4915847086962688884[305] = 0;
   out_4915847086962688884[306] = 0;
   out_4915847086962688884[307] = 0;
   out_4915847086962688884[308] = 0;
   out_4915847086962688884[309] = 0;
   out_4915847086962688884[310] = 0;
   out_4915847086962688884[311] = 0;
   out_4915847086962688884[312] = 0;
   out_4915847086962688884[313] = 0;
   out_4915847086962688884[314] = 0;
   out_4915847086962688884[315] = 0;
   out_4915847086962688884[316] = 0;
   out_4915847086962688884[317] = 0;
   out_4915847086962688884[318] = 0;
   out_4915847086962688884[319] = 0;
   out_4915847086962688884[320] = 0;
   out_4915847086962688884[321] = 0;
   out_4915847086962688884[322] = 0;
   out_4915847086962688884[323] = 1;
}
void h_4(double *state, double *unused, double *out_4566450913648834974) {
   out_4566450913648834974[0] = state[6] + state[9];
   out_4566450913648834974[1] = state[7] + state[10];
   out_4566450913648834974[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_8478926176726141688) {
   out_8478926176726141688[0] = 0;
   out_8478926176726141688[1] = 0;
   out_8478926176726141688[2] = 0;
   out_8478926176726141688[3] = 0;
   out_8478926176726141688[4] = 0;
   out_8478926176726141688[5] = 0;
   out_8478926176726141688[6] = 1;
   out_8478926176726141688[7] = 0;
   out_8478926176726141688[8] = 0;
   out_8478926176726141688[9] = 1;
   out_8478926176726141688[10] = 0;
   out_8478926176726141688[11] = 0;
   out_8478926176726141688[12] = 0;
   out_8478926176726141688[13] = 0;
   out_8478926176726141688[14] = 0;
   out_8478926176726141688[15] = 0;
   out_8478926176726141688[16] = 0;
   out_8478926176726141688[17] = 0;
   out_8478926176726141688[18] = 0;
   out_8478926176726141688[19] = 0;
   out_8478926176726141688[20] = 0;
   out_8478926176726141688[21] = 0;
   out_8478926176726141688[22] = 0;
   out_8478926176726141688[23] = 0;
   out_8478926176726141688[24] = 0;
   out_8478926176726141688[25] = 1;
   out_8478926176726141688[26] = 0;
   out_8478926176726141688[27] = 0;
   out_8478926176726141688[28] = 1;
   out_8478926176726141688[29] = 0;
   out_8478926176726141688[30] = 0;
   out_8478926176726141688[31] = 0;
   out_8478926176726141688[32] = 0;
   out_8478926176726141688[33] = 0;
   out_8478926176726141688[34] = 0;
   out_8478926176726141688[35] = 0;
   out_8478926176726141688[36] = 0;
   out_8478926176726141688[37] = 0;
   out_8478926176726141688[38] = 0;
   out_8478926176726141688[39] = 0;
   out_8478926176726141688[40] = 0;
   out_8478926176726141688[41] = 0;
   out_8478926176726141688[42] = 0;
   out_8478926176726141688[43] = 0;
   out_8478926176726141688[44] = 1;
   out_8478926176726141688[45] = 0;
   out_8478926176726141688[46] = 0;
   out_8478926176726141688[47] = 1;
   out_8478926176726141688[48] = 0;
   out_8478926176726141688[49] = 0;
   out_8478926176726141688[50] = 0;
   out_8478926176726141688[51] = 0;
   out_8478926176726141688[52] = 0;
   out_8478926176726141688[53] = 0;
}
void h_10(double *state, double *unused, double *out_7539996529410954195) {
   out_7539996529410954195[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_7539996529410954195[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_7539996529410954195[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_8508433762584458121) {
   out_8508433762584458121[0] = 0;
   out_8508433762584458121[1] = 9.8100000000000005*cos(state[1]);
   out_8508433762584458121[2] = 0;
   out_8508433762584458121[3] = 0;
   out_8508433762584458121[4] = -state[8];
   out_8508433762584458121[5] = state[7];
   out_8508433762584458121[6] = 0;
   out_8508433762584458121[7] = state[5];
   out_8508433762584458121[8] = -state[4];
   out_8508433762584458121[9] = 0;
   out_8508433762584458121[10] = 0;
   out_8508433762584458121[11] = 0;
   out_8508433762584458121[12] = 1;
   out_8508433762584458121[13] = 0;
   out_8508433762584458121[14] = 0;
   out_8508433762584458121[15] = 1;
   out_8508433762584458121[16] = 0;
   out_8508433762584458121[17] = 0;
   out_8508433762584458121[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_8508433762584458121[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_8508433762584458121[20] = 0;
   out_8508433762584458121[21] = state[8];
   out_8508433762584458121[22] = 0;
   out_8508433762584458121[23] = -state[6];
   out_8508433762584458121[24] = -state[5];
   out_8508433762584458121[25] = 0;
   out_8508433762584458121[26] = state[3];
   out_8508433762584458121[27] = 0;
   out_8508433762584458121[28] = 0;
   out_8508433762584458121[29] = 0;
   out_8508433762584458121[30] = 0;
   out_8508433762584458121[31] = 1;
   out_8508433762584458121[32] = 0;
   out_8508433762584458121[33] = 0;
   out_8508433762584458121[34] = 1;
   out_8508433762584458121[35] = 0;
   out_8508433762584458121[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_8508433762584458121[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_8508433762584458121[38] = 0;
   out_8508433762584458121[39] = -state[7];
   out_8508433762584458121[40] = state[6];
   out_8508433762584458121[41] = 0;
   out_8508433762584458121[42] = state[4];
   out_8508433762584458121[43] = -state[3];
   out_8508433762584458121[44] = 0;
   out_8508433762584458121[45] = 0;
   out_8508433762584458121[46] = 0;
   out_8508433762584458121[47] = 0;
   out_8508433762584458121[48] = 0;
   out_8508433762584458121[49] = 0;
   out_8508433762584458121[50] = 1;
   out_8508433762584458121[51] = 0;
   out_8508433762584458121[52] = 0;
   out_8508433762584458121[53] = 1;
}
void h_13(double *state, double *unused, double *out_4338527865886089826) {
   out_4338527865886089826[0] = state[3];
   out_4338527865886089826[1] = state[4];
   out_4338527865886089826[2] = state[5];
}
void H_13(double *state, double *unused, double *out_6755544071651077127) {
   out_6755544071651077127[0] = 0;
   out_6755544071651077127[1] = 0;
   out_6755544071651077127[2] = 0;
   out_6755544071651077127[3] = 1;
   out_6755544071651077127[4] = 0;
   out_6755544071651077127[5] = 0;
   out_6755544071651077127[6] = 0;
   out_6755544071651077127[7] = 0;
   out_6755544071651077127[8] = 0;
   out_6755544071651077127[9] = 0;
   out_6755544071651077127[10] = 0;
   out_6755544071651077127[11] = 0;
   out_6755544071651077127[12] = 0;
   out_6755544071651077127[13] = 0;
   out_6755544071651077127[14] = 0;
   out_6755544071651077127[15] = 0;
   out_6755544071651077127[16] = 0;
   out_6755544071651077127[17] = 0;
   out_6755544071651077127[18] = 0;
   out_6755544071651077127[19] = 0;
   out_6755544071651077127[20] = 0;
   out_6755544071651077127[21] = 0;
   out_6755544071651077127[22] = 1;
   out_6755544071651077127[23] = 0;
   out_6755544071651077127[24] = 0;
   out_6755544071651077127[25] = 0;
   out_6755544071651077127[26] = 0;
   out_6755544071651077127[27] = 0;
   out_6755544071651077127[28] = 0;
   out_6755544071651077127[29] = 0;
   out_6755544071651077127[30] = 0;
   out_6755544071651077127[31] = 0;
   out_6755544071651077127[32] = 0;
   out_6755544071651077127[33] = 0;
   out_6755544071651077127[34] = 0;
   out_6755544071651077127[35] = 0;
   out_6755544071651077127[36] = 0;
   out_6755544071651077127[37] = 0;
   out_6755544071651077127[38] = 0;
   out_6755544071651077127[39] = 0;
   out_6755544071651077127[40] = 0;
   out_6755544071651077127[41] = 1;
   out_6755544071651077127[42] = 0;
   out_6755544071651077127[43] = 0;
   out_6755544071651077127[44] = 0;
   out_6755544071651077127[45] = 0;
   out_6755544071651077127[46] = 0;
   out_6755544071651077127[47] = 0;
   out_6755544071651077127[48] = 0;
   out_6755544071651077127[49] = 0;
   out_6755544071651077127[50] = 0;
   out_6755544071651077127[51] = 0;
   out_6755544071651077127[52] = 0;
   out_6755544071651077127[53] = 0;
}
void h_14(double *state, double *unused, double *out_8691716025455276110) {
   out_8691716025455276110[0] = state[6];
   out_8691716025455276110[1] = state[7];
   out_8691716025455276110[2] = state[8];
}
void H_14(double *state, double *unused, double *out_6004577040643925399) {
   out_6004577040643925399[0] = 0;
   out_6004577040643925399[1] = 0;
   out_6004577040643925399[2] = 0;
   out_6004577040643925399[3] = 0;
   out_6004577040643925399[4] = 0;
   out_6004577040643925399[5] = 0;
   out_6004577040643925399[6] = 1;
   out_6004577040643925399[7] = 0;
   out_6004577040643925399[8] = 0;
   out_6004577040643925399[9] = 0;
   out_6004577040643925399[10] = 0;
   out_6004577040643925399[11] = 0;
   out_6004577040643925399[12] = 0;
   out_6004577040643925399[13] = 0;
   out_6004577040643925399[14] = 0;
   out_6004577040643925399[15] = 0;
   out_6004577040643925399[16] = 0;
   out_6004577040643925399[17] = 0;
   out_6004577040643925399[18] = 0;
   out_6004577040643925399[19] = 0;
   out_6004577040643925399[20] = 0;
   out_6004577040643925399[21] = 0;
   out_6004577040643925399[22] = 0;
   out_6004577040643925399[23] = 0;
   out_6004577040643925399[24] = 0;
   out_6004577040643925399[25] = 1;
   out_6004577040643925399[26] = 0;
   out_6004577040643925399[27] = 0;
   out_6004577040643925399[28] = 0;
   out_6004577040643925399[29] = 0;
   out_6004577040643925399[30] = 0;
   out_6004577040643925399[31] = 0;
   out_6004577040643925399[32] = 0;
   out_6004577040643925399[33] = 0;
   out_6004577040643925399[34] = 0;
   out_6004577040643925399[35] = 0;
   out_6004577040643925399[36] = 0;
   out_6004577040643925399[37] = 0;
   out_6004577040643925399[38] = 0;
   out_6004577040643925399[39] = 0;
   out_6004577040643925399[40] = 0;
   out_6004577040643925399[41] = 0;
   out_6004577040643925399[42] = 0;
   out_6004577040643925399[43] = 0;
   out_6004577040643925399[44] = 1;
   out_6004577040643925399[45] = 0;
   out_6004577040643925399[46] = 0;
   out_6004577040643925399[47] = 0;
   out_6004577040643925399[48] = 0;
   out_6004577040643925399[49] = 0;
   out_6004577040643925399[50] = 0;
   out_6004577040643925399[51] = 0;
   out_6004577040643925399[52] = 0;
   out_6004577040643925399[53] = 0;
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
void pose_err_fun(double *nom_x, double *delta_x, double *out_8294180210607547219) {
  err_fun(nom_x, delta_x, out_8294180210607547219);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_8330596021821018044) {
  inv_err_fun(nom_x, true_x, out_8330596021821018044);
}
void pose_H_mod_fun(double *state, double *out_534058243187542804) {
  H_mod_fun(state, out_534058243187542804);
}
void pose_f_fun(double *state, double dt, double *out_2535209606058579312) {
  f_fun(state,  dt, out_2535209606058579312);
}
void pose_F_fun(double *state, double dt, double *out_4915847086962688884) {
  F_fun(state,  dt, out_4915847086962688884);
}
void pose_h_4(double *state, double *unused, double *out_4566450913648834974) {
  h_4(state, unused, out_4566450913648834974);
}
void pose_H_4(double *state, double *unused, double *out_8478926176726141688) {
  H_4(state, unused, out_8478926176726141688);
}
void pose_h_10(double *state, double *unused, double *out_7539996529410954195) {
  h_10(state, unused, out_7539996529410954195);
}
void pose_H_10(double *state, double *unused, double *out_8508433762584458121) {
  H_10(state, unused, out_8508433762584458121);
}
void pose_h_13(double *state, double *unused, double *out_4338527865886089826) {
  h_13(state, unused, out_4338527865886089826);
}
void pose_H_13(double *state, double *unused, double *out_6755544071651077127) {
  H_13(state, unused, out_6755544071651077127);
}
void pose_h_14(double *state, double *unused, double *out_8691716025455276110) {
  h_14(state, unused, out_8691716025455276110);
}
void pose_H_14(double *state, double *unused, double *out_6004577040643925399) {
  H_14(state, unused, out_6004577040643925399);
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
