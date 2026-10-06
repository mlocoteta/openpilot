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
void err_fun(double *nom_x, double *delta_x, double *out_2251541010105652257) {
   out_2251541010105652257[0] = delta_x[0] + nom_x[0];
   out_2251541010105652257[1] = delta_x[1] + nom_x[1];
   out_2251541010105652257[2] = delta_x[2] + nom_x[2];
   out_2251541010105652257[3] = delta_x[3] + nom_x[3];
   out_2251541010105652257[4] = delta_x[4] + nom_x[4];
   out_2251541010105652257[5] = delta_x[5] + nom_x[5];
   out_2251541010105652257[6] = delta_x[6] + nom_x[6];
   out_2251541010105652257[7] = delta_x[7] + nom_x[7];
   out_2251541010105652257[8] = delta_x[8] + nom_x[8];
   out_2251541010105652257[9] = delta_x[9] + nom_x[9];
   out_2251541010105652257[10] = delta_x[10] + nom_x[10];
   out_2251541010105652257[11] = delta_x[11] + nom_x[11];
   out_2251541010105652257[12] = delta_x[12] + nom_x[12];
   out_2251541010105652257[13] = delta_x[13] + nom_x[13];
   out_2251541010105652257[14] = delta_x[14] + nom_x[14];
   out_2251541010105652257[15] = delta_x[15] + nom_x[15];
   out_2251541010105652257[16] = delta_x[16] + nom_x[16];
   out_2251541010105652257[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_3400329631105902853) {
   out_3400329631105902853[0] = -nom_x[0] + true_x[0];
   out_3400329631105902853[1] = -nom_x[1] + true_x[1];
   out_3400329631105902853[2] = -nom_x[2] + true_x[2];
   out_3400329631105902853[3] = -nom_x[3] + true_x[3];
   out_3400329631105902853[4] = -nom_x[4] + true_x[4];
   out_3400329631105902853[5] = -nom_x[5] + true_x[5];
   out_3400329631105902853[6] = -nom_x[6] + true_x[6];
   out_3400329631105902853[7] = -nom_x[7] + true_x[7];
   out_3400329631105902853[8] = -nom_x[8] + true_x[8];
   out_3400329631105902853[9] = -nom_x[9] + true_x[9];
   out_3400329631105902853[10] = -nom_x[10] + true_x[10];
   out_3400329631105902853[11] = -nom_x[11] + true_x[11];
   out_3400329631105902853[12] = -nom_x[12] + true_x[12];
   out_3400329631105902853[13] = -nom_x[13] + true_x[13];
   out_3400329631105902853[14] = -nom_x[14] + true_x[14];
   out_3400329631105902853[15] = -nom_x[15] + true_x[15];
   out_3400329631105902853[16] = -nom_x[16] + true_x[16];
   out_3400329631105902853[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_7864672362290258107) {
   out_7864672362290258107[0] = 1.0;
   out_7864672362290258107[1] = 0.0;
   out_7864672362290258107[2] = 0.0;
   out_7864672362290258107[3] = 0.0;
   out_7864672362290258107[4] = 0.0;
   out_7864672362290258107[5] = 0.0;
   out_7864672362290258107[6] = 0.0;
   out_7864672362290258107[7] = 0.0;
   out_7864672362290258107[8] = 0.0;
   out_7864672362290258107[9] = 0.0;
   out_7864672362290258107[10] = 0.0;
   out_7864672362290258107[11] = 0.0;
   out_7864672362290258107[12] = 0.0;
   out_7864672362290258107[13] = 0.0;
   out_7864672362290258107[14] = 0.0;
   out_7864672362290258107[15] = 0.0;
   out_7864672362290258107[16] = 0.0;
   out_7864672362290258107[17] = 0.0;
   out_7864672362290258107[18] = 0.0;
   out_7864672362290258107[19] = 1.0;
   out_7864672362290258107[20] = 0.0;
   out_7864672362290258107[21] = 0.0;
   out_7864672362290258107[22] = 0.0;
   out_7864672362290258107[23] = 0.0;
   out_7864672362290258107[24] = 0.0;
   out_7864672362290258107[25] = 0.0;
   out_7864672362290258107[26] = 0.0;
   out_7864672362290258107[27] = 0.0;
   out_7864672362290258107[28] = 0.0;
   out_7864672362290258107[29] = 0.0;
   out_7864672362290258107[30] = 0.0;
   out_7864672362290258107[31] = 0.0;
   out_7864672362290258107[32] = 0.0;
   out_7864672362290258107[33] = 0.0;
   out_7864672362290258107[34] = 0.0;
   out_7864672362290258107[35] = 0.0;
   out_7864672362290258107[36] = 0.0;
   out_7864672362290258107[37] = 0.0;
   out_7864672362290258107[38] = 1.0;
   out_7864672362290258107[39] = 0.0;
   out_7864672362290258107[40] = 0.0;
   out_7864672362290258107[41] = 0.0;
   out_7864672362290258107[42] = 0.0;
   out_7864672362290258107[43] = 0.0;
   out_7864672362290258107[44] = 0.0;
   out_7864672362290258107[45] = 0.0;
   out_7864672362290258107[46] = 0.0;
   out_7864672362290258107[47] = 0.0;
   out_7864672362290258107[48] = 0.0;
   out_7864672362290258107[49] = 0.0;
   out_7864672362290258107[50] = 0.0;
   out_7864672362290258107[51] = 0.0;
   out_7864672362290258107[52] = 0.0;
   out_7864672362290258107[53] = 0.0;
   out_7864672362290258107[54] = 0.0;
   out_7864672362290258107[55] = 0.0;
   out_7864672362290258107[56] = 0.0;
   out_7864672362290258107[57] = 1.0;
   out_7864672362290258107[58] = 0.0;
   out_7864672362290258107[59] = 0.0;
   out_7864672362290258107[60] = 0.0;
   out_7864672362290258107[61] = 0.0;
   out_7864672362290258107[62] = 0.0;
   out_7864672362290258107[63] = 0.0;
   out_7864672362290258107[64] = 0.0;
   out_7864672362290258107[65] = 0.0;
   out_7864672362290258107[66] = 0.0;
   out_7864672362290258107[67] = 0.0;
   out_7864672362290258107[68] = 0.0;
   out_7864672362290258107[69] = 0.0;
   out_7864672362290258107[70] = 0.0;
   out_7864672362290258107[71] = 0.0;
   out_7864672362290258107[72] = 0.0;
   out_7864672362290258107[73] = 0.0;
   out_7864672362290258107[74] = 0.0;
   out_7864672362290258107[75] = 0.0;
   out_7864672362290258107[76] = 1.0;
   out_7864672362290258107[77] = 0.0;
   out_7864672362290258107[78] = 0.0;
   out_7864672362290258107[79] = 0.0;
   out_7864672362290258107[80] = 0.0;
   out_7864672362290258107[81] = 0.0;
   out_7864672362290258107[82] = 0.0;
   out_7864672362290258107[83] = 0.0;
   out_7864672362290258107[84] = 0.0;
   out_7864672362290258107[85] = 0.0;
   out_7864672362290258107[86] = 0.0;
   out_7864672362290258107[87] = 0.0;
   out_7864672362290258107[88] = 0.0;
   out_7864672362290258107[89] = 0.0;
   out_7864672362290258107[90] = 0.0;
   out_7864672362290258107[91] = 0.0;
   out_7864672362290258107[92] = 0.0;
   out_7864672362290258107[93] = 0.0;
   out_7864672362290258107[94] = 0.0;
   out_7864672362290258107[95] = 1.0;
   out_7864672362290258107[96] = 0.0;
   out_7864672362290258107[97] = 0.0;
   out_7864672362290258107[98] = 0.0;
   out_7864672362290258107[99] = 0.0;
   out_7864672362290258107[100] = 0.0;
   out_7864672362290258107[101] = 0.0;
   out_7864672362290258107[102] = 0.0;
   out_7864672362290258107[103] = 0.0;
   out_7864672362290258107[104] = 0.0;
   out_7864672362290258107[105] = 0.0;
   out_7864672362290258107[106] = 0.0;
   out_7864672362290258107[107] = 0.0;
   out_7864672362290258107[108] = 0.0;
   out_7864672362290258107[109] = 0.0;
   out_7864672362290258107[110] = 0.0;
   out_7864672362290258107[111] = 0.0;
   out_7864672362290258107[112] = 0.0;
   out_7864672362290258107[113] = 0.0;
   out_7864672362290258107[114] = 1.0;
   out_7864672362290258107[115] = 0.0;
   out_7864672362290258107[116] = 0.0;
   out_7864672362290258107[117] = 0.0;
   out_7864672362290258107[118] = 0.0;
   out_7864672362290258107[119] = 0.0;
   out_7864672362290258107[120] = 0.0;
   out_7864672362290258107[121] = 0.0;
   out_7864672362290258107[122] = 0.0;
   out_7864672362290258107[123] = 0.0;
   out_7864672362290258107[124] = 0.0;
   out_7864672362290258107[125] = 0.0;
   out_7864672362290258107[126] = 0.0;
   out_7864672362290258107[127] = 0.0;
   out_7864672362290258107[128] = 0.0;
   out_7864672362290258107[129] = 0.0;
   out_7864672362290258107[130] = 0.0;
   out_7864672362290258107[131] = 0.0;
   out_7864672362290258107[132] = 0.0;
   out_7864672362290258107[133] = 1.0;
   out_7864672362290258107[134] = 0.0;
   out_7864672362290258107[135] = 0.0;
   out_7864672362290258107[136] = 0.0;
   out_7864672362290258107[137] = 0.0;
   out_7864672362290258107[138] = 0.0;
   out_7864672362290258107[139] = 0.0;
   out_7864672362290258107[140] = 0.0;
   out_7864672362290258107[141] = 0.0;
   out_7864672362290258107[142] = 0.0;
   out_7864672362290258107[143] = 0.0;
   out_7864672362290258107[144] = 0.0;
   out_7864672362290258107[145] = 0.0;
   out_7864672362290258107[146] = 0.0;
   out_7864672362290258107[147] = 0.0;
   out_7864672362290258107[148] = 0.0;
   out_7864672362290258107[149] = 0.0;
   out_7864672362290258107[150] = 0.0;
   out_7864672362290258107[151] = 0.0;
   out_7864672362290258107[152] = 1.0;
   out_7864672362290258107[153] = 0.0;
   out_7864672362290258107[154] = 0.0;
   out_7864672362290258107[155] = 0.0;
   out_7864672362290258107[156] = 0.0;
   out_7864672362290258107[157] = 0.0;
   out_7864672362290258107[158] = 0.0;
   out_7864672362290258107[159] = 0.0;
   out_7864672362290258107[160] = 0.0;
   out_7864672362290258107[161] = 0.0;
   out_7864672362290258107[162] = 0.0;
   out_7864672362290258107[163] = 0.0;
   out_7864672362290258107[164] = 0.0;
   out_7864672362290258107[165] = 0.0;
   out_7864672362290258107[166] = 0.0;
   out_7864672362290258107[167] = 0.0;
   out_7864672362290258107[168] = 0.0;
   out_7864672362290258107[169] = 0.0;
   out_7864672362290258107[170] = 0.0;
   out_7864672362290258107[171] = 1.0;
   out_7864672362290258107[172] = 0.0;
   out_7864672362290258107[173] = 0.0;
   out_7864672362290258107[174] = 0.0;
   out_7864672362290258107[175] = 0.0;
   out_7864672362290258107[176] = 0.0;
   out_7864672362290258107[177] = 0.0;
   out_7864672362290258107[178] = 0.0;
   out_7864672362290258107[179] = 0.0;
   out_7864672362290258107[180] = 0.0;
   out_7864672362290258107[181] = 0.0;
   out_7864672362290258107[182] = 0.0;
   out_7864672362290258107[183] = 0.0;
   out_7864672362290258107[184] = 0.0;
   out_7864672362290258107[185] = 0.0;
   out_7864672362290258107[186] = 0.0;
   out_7864672362290258107[187] = 0.0;
   out_7864672362290258107[188] = 0.0;
   out_7864672362290258107[189] = 0.0;
   out_7864672362290258107[190] = 1.0;
   out_7864672362290258107[191] = 0.0;
   out_7864672362290258107[192] = 0.0;
   out_7864672362290258107[193] = 0.0;
   out_7864672362290258107[194] = 0.0;
   out_7864672362290258107[195] = 0.0;
   out_7864672362290258107[196] = 0.0;
   out_7864672362290258107[197] = 0.0;
   out_7864672362290258107[198] = 0.0;
   out_7864672362290258107[199] = 0.0;
   out_7864672362290258107[200] = 0.0;
   out_7864672362290258107[201] = 0.0;
   out_7864672362290258107[202] = 0.0;
   out_7864672362290258107[203] = 0.0;
   out_7864672362290258107[204] = 0.0;
   out_7864672362290258107[205] = 0.0;
   out_7864672362290258107[206] = 0.0;
   out_7864672362290258107[207] = 0.0;
   out_7864672362290258107[208] = 0.0;
   out_7864672362290258107[209] = 1.0;
   out_7864672362290258107[210] = 0.0;
   out_7864672362290258107[211] = 0.0;
   out_7864672362290258107[212] = 0.0;
   out_7864672362290258107[213] = 0.0;
   out_7864672362290258107[214] = 0.0;
   out_7864672362290258107[215] = 0.0;
   out_7864672362290258107[216] = 0.0;
   out_7864672362290258107[217] = 0.0;
   out_7864672362290258107[218] = 0.0;
   out_7864672362290258107[219] = 0.0;
   out_7864672362290258107[220] = 0.0;
   out_7864672362290258107[221] = 0.0;
   out_7864672362290258107[222] = 0.0;
   out_7864672362290258107[223] = 0.0;
   out_7864672362290258107[224] = 0.0;
   out_7864672362290258107[225] = 0.0;
   out_7864672362290258107[226] = 0.0;
   out_7864672362290258107[227] = 0.0;
   out_7864672362290258107[228] = 1.0;
   out_7864672362290258107[229] = 0.0;
   out_7864672362290258107[230] = 0.0;
   out_7864672362290258107[231] = 0.0;
   out_7864672362290258107[232] = 0.0;
   out_7864672362290258107[233] = 0.0;
   out_7864672362290258107[234] = 0.0;
   out_7864672362290258107[235] = 0.0;
   out_7864672362290258107[236] = 0.0;
   out_7864672362290258107[237] = 0.0;
   out_7864672362290258107[238] = 0.0;
   out_7864672362290258107[239] = 0.0;
   out_7864672362290258107[240] = 0.0;
   out_7864672362290258107[241] = 0.0;
   out_7864672362290258107[242] = 0.0;
   out_7864672362290258107[243] = 0.0;
   out_7864672362290258107[244] = 0.0;
   out_7864672362290258107[245] = 0.0;
   out_7864672362290258107[246] = 0.0;
   out_7864672362290258107[247] = 1.0;
   out_7864672362290258107[248] = 0.0;
   out_7864672362290258107[249] = 0.0;
   out_7864672362290258107[250] = 0.0;
   out_7864672362290258107[251] = 0.0;
   out_7864672362290258107[252] = 0.0;
   out_7864672362290258107[253] = 0.0;
   out_7864672362290258107[254] = 0.0;
   out_7864672362290258107[255] = 0.0;
   out_7864672362290258107[256] = 0.0;
   out_7864672362290258107[257] = 0.0;
   out_7864672362290258107[258] = 0.0;
   out_7864672362290258107[259] = 0.0;
   out_7864672362290258107[260] = 0.0;
   out_7864672362290258107[261] = 0.0;
   out_7864672362290258107[262] = 0.0;
   out_7864672362290258107[263] = 0.0;
   out_7864672362290258107[264] = 0.0;
   out_7864672362290258107[265] = 0.0;
   out_7864672362290258107[266] = 1.0;
   out_7864672362290258107[267] = 0.0;
   out_7864672362290258107[268] = 0.0;
   out_7864672362290258107[269] = 0.0;
   out_7864672362290258107[270] = 0.0;
   out_7864672362290258107[271] = 0.0;
   out_7864672362290258107[272] = 0.0;
   out_7864672362290258107[273] = 0.0;
   out_7864672362290258107[274] = 0.0;
   out_7864672362290258107[275] = 0.0;
   out_7864672362290258107[276] = 0.0;
   out_7864672362290258107[277] = 0.0;
   out_7864672362290258107[278] = 0.0;
   out_7864672362290258107[279] = 0.0;
   out_7864672362290258107[280] = 0.0;
   out_7864672362290258107[281] = 0.0;
   out_7864672362290258107[282] = 0.0;
   out_7864672362290258107[283] = 0.0;
   out_7864672362290258107[284] = 0.0;
   out_7864672362290258107[285] = 1.0;
   out_7864672362290258107[286] = 0.0;
   out_7864672362290258107[287] = 0.0;
   out_7864672362290258107[288] = 0.0;
   out_7864672362290258107[289] = 0.0;
   out_7864672362290258107[290] = 0.0;
   out_7864672362290258107[291] = 0.0;
   out_7864672362290258107[292] = 0.0;
   out_7864672362290258107[293] = 0.0;
   out_7864672362290258107[294] = 0.0;
   out_7864672362290258107[295] = 0.0;
   out_7864672362290258107[296] = 0.0;
   out_7864672362290258107[297] = 0.0;
   out_7864672362290258107[298] = 0.0;
   out_7864672362290258107[299] = 0.0;
   out_7864672362290258107[300] = 0.0;
   out_7864672362290258107[301] = 0.0;
   out_7864672362290258107[302] = 0.0;
   out_7864672362290258107[303] = 0.0;
   out_7864672362290258107[304] = 1.0;
   out_7864672362290258107[305] = 0.0;
   out_7864672362290258107[306] = 0.0;
   out_7864672362290258107[307] = 0.0;
   out_7864672362290258107[308] = 0.0;
   out_7864672362290258107[309] = 0.0;
   out_7864672362290258107[310] = 0.0;
   out_7864672362290258107[311] = 0.0;
   out_7864672362290258107[312] = 0.0;
   out_7864672362290258107[313] = 0.0;
   out_7864672362290258107[314] = 0.0;
   out_7864672362290258107[315] = 0.0;
   out_7864672362290258107[316] = 0.0;
   out_7864672362290258107[317] = 0.0;
   out_7864672362290258107[318] = 0.0;
   out_7864672362290258107[319] = 0.0;
   out_7864672362290258107[320] = 0.0;
   out_7864672362290258107[321] = 0.0;
   out_7864672362290258107[322] = 0.0;
   out_7864672362290258107[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_1708698118726409450) {
   out_1708698118726409450[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_1708698118726409450[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_1708698118726409450[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_1708698118726409450[3] = dt*state[12] + state[3];
   out_1708698118726409450[4] = dt*state[13] + state[4];
   out_1708698118726409450[5] = dt*state[14] + state[5];
   out_1708698118726409450[6] = state[6];
   out_1708698118726409450[7] = state[7];
   out_1708698118726409450[8] = state[8];
   out_1708698118726409450[9] = state[9];
   out_1708698118726409450[10] = state[10];
   out_1708698118726409450[11] = state[11];
   out_1708698118726409450[12] = state[12];
   out_1708698118726409450[13] = state[13];
   out_1708698118726409450[14] = state[14];
   out_1708698118726409450[15] = state[15];
   out_1708698118726409450[16] = state[16];
   out_1708698118726409450[17] = state[17];
}
void F_fun(double *state, double dt, double *out_269214026509656143) {
   out_269214026509656143[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_269214026509656143[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_269214026509656143[2] = 0;
   out_269214026509656143[3] = 0;
   out_269214026509656143[4] = 0;
   out_269214026509656143[5] = 0;
   out_269214026509656143[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_269214026509656143[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_269214026509656143[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_269214026509656143[9] = 0;
   out_269214026509656143[10] = 0;
   out_269214026509656143[11] = 0;
   out_269214026509656143[12] = 0;
   out_269214026509656143[13] = 0;
   out_269214026509656143[14] = 0;
   out_269214026509656143[15] = 0;
   out_269214026509656143[16] = 0;
   out_269214026509656143[17] = 0;
   out_269214026509656143[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_269214026509656143[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_269214026509656143[20] = 0;
   out_269214026509656143[21] = 0;
   out_269214026509656143[22] = 0;
   out_269214026509656143[23] = 0;
   out_269214026509656143[24] = 0;
   out_269214026509656143[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_269214026509656143[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_269214026509656143[27] = 0;
   out_269214026509656143[28] = 0;
   out_269214026509656143[29] = 0;
   out_269214026509656143[30] = 0;
   out_269214026509656143[31] = 0;
   out_269214026509656143[32] = 0;
   out_269214026509656143[33] = 0;
   out_269214026509656143[34] = 0;
   out_269214026509656143[35] = 0;
   out_269214026509656143[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_269214026509656143[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_269214026509656143[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_269214026509656143[39] = 0;
   out_269214026509656143[40] = 0;
   out_269214026509656143[41] = 0;
   out_269214026509656143[42] = 0;
   out_269214026509656143[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_269214026509656143[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_269214026509656143[45] = 0;
   out_269214026509656143[46] = 0;
   out_269214026509656143[47] = 0;
   out_269214026509656143[48] = 0;
   out_269214026509656143[49] = 0;
   out_269214026509656143[50] = 0;
   out_269214026509656143[51] = 0;
   out_269214026509656143[52] = 0;
   out_269214026509656143[53] = 0;
   out_269214026509656143[54] = 0;
   out_269214026509656143[55] = 0;
   out_269214026509656143[56] = 0;
   out_269214026509656143[57] = 1;
   out_269214026509656143[58] = 0;
   out_269214026509656143[59] = 0;
   out_269214026509656143[60] = 0;
   out_269214026509656143[61] = 0;
   out_269214026509656143[62] = 0;
   out_269214026509656143[63] = 0;
   out_269214026509656143[64] = 0;
   out_269214026509656143[65] = 0;
   out_269214026509656143[66] = dt;
   out_269214026509656143[67] = 0;
   out_269214026509656143[68] = 0;
   out_269214026509656143[69] = 0;
   out_269214026509656143[70] = 0;
   out_269214026509656143[71] = 0;
   out_269214026509656143[72] = 0;
   out_269214026509656143[73] = 0;
   out_269214026509656143[74] = 0;
   out_269214026509656143[75] = 0;
   out_269214026509656143[76] = 1;
   out_269214026509656143[77] = 0;
   out_269214026509656143[78] = 0;
   out_269214026509656143[79] = 0;
   out_269214026509656143[80] = 0;
   out_269214026509656143[81] = 0;
   out_269214026509656143[82] = 0;
   out_269214026509656143[83] = 0;
   out_269214026509656143[84] = 0;
   out_269214026509656143[85] = dt;
   out_269214026509656143[86] = 0;
   out_269214026509656143[87] = 0;
   out_269214026509656143[88] = 0;
   out_269214026509656143[89] = 0;
   out_269214026509656143[90] = 0;
   out_269214026509656143[91] = 0;
   out_269214026509656143[92] = 0;
   out_269214026509656143[93] = 0;
   out_269214026509656143[94] = 0;
   out_269214026509656143[95] = 1;
   out_269214026509656143[96] = 0;
   out_269214026509656143[97] = 0;
   out_269214026509656143[98] = 0;
   out_269214026509656143[99] = 0;
   out_269214026509656143[100] = 0;
   out_269214026509656143[101] = 0;
   out_269214026509656143[102] = 0;
   out_269214026509656143[103] = 0;
   out_269214026509656143[104] = dt;
   out_269214026509656143[105] = 0;
   out_269214026509656143[106] = 0;
   out_269214026509656143[107] = 0;
   out_269214026509656143[108] = 0;
   out_269214026509656143[109] = 0;
   out_269214026509656143[110] = 0;
   out_269214026509656143[111] = 0;
   out_269214026509656143[112] = 0;
   out_269214026509656143[113] = 0;
   out_269214026509656143[114] = 1;
   out_269214026509656143[115] = 0;
   out_269214026509656143[116] = 0;
   out_269214026509656143[117] = 0;
   out_269214026509656143[118] = 0;
   out_269214026509656143[119] = 0;
   out_269214026509656143[120] = 0;
   out_269214026509656143[121] = 0;
   out_269214026509656143[122] = 0;
   out_269214026509656143[123] = 0;
   out_269214026509656143[124] = 0;
   out_269214026509656143[125] = 0;
   out_269214026509656143[126] = 0;
   out_269214026509656143[127] = 0;
   out_269214026509656143[128] = 0;
   out_269214026509656143[129] = 0;
   out_269214026509656143[130] = 0;
   out_269214026509656143[131] = 0;
   out_269214026509656143[132] = 0;
   out_269214026509656143[133] = 1;
   out_269214026509656143[134] = 0;
   out_269214026509656143[135] = 0;
   out_269214026509656143[136] = 0;
   out_269214026509656143[137] = 0;
   out_269214026509656143[138] = 0;
   out_269214026509656143[139] = 0;
   out_269214026509656143[140] = 0;
   out_269214026509656143[141] = 0;
   out_269214026509656143[142] = 0;
   out_269214026509656143[143] = 0;
   out_269214026509656143[144] = 0;
   out_269214026509656143[145] = 0;
   out_269214026509656143[146] = 0;
   out_269214026509656143[147] = 0;
   out_269214026509656143[148] = 0;
   out_269214026509656143[149] = 0;
   out_269214026509656143[150] = 0;
   out_269214026509656143[151] = 0;
   out_269214026509656143[152] = 1;
   out_269214026509656143[153] = 0;
   out_269214026509656143[154] = 0;
   out_269214026509656143[155] = 0;
   out_269214026509656143[156] = 0;
   out_269214026509656143[157] = 0;
   out_269214026509656143[158] = 0;
   out_269214026509656143[159] = 0;
   out_269214026509656143[160] = 0;
   out_269214026509656143[161] = 0;
   out_269214026509656143[162] = 0;
   out_269214026509656143[163] = 0;
   out_269214026509656143[164] = 0;
   out_269214026509656143[165] = 0;
   out_269214026509656143[166] = 0;
   out_269214026509656143[167] = 0;
   out_269214026509656143[168] = 0;
   out_269214026509656143[169] = 0;
   out_269214026509656143[170] = 0;
   out_269214026509656143[171] = 1;
   out_269214026509656143[172] = 0;
   out_269214026509656143[173] = 0;
   out_269214026509656143[174] = 0;
   out_269214026509656143[175] = 0;
   out_269214026509656143[176] = 0;
   out_269214026509656143[177] = 0;
   out_269214026509656143[178] = 0;
   out_269214026509656143[179] = 0;
   out_269214026509656143[180] = 0;
   out_269214026509656143[181] = 0;
   out_269214026509656143[182] = 0;
   out_269214026509656143[183] = 0;
   out_269214026509656143[184] = 0;
   out_269214026509656143[185] = 0;
   out_269214026509656143[186] = 0;
   out_269214026509656143[187] = 0;
   out_269214026509656143[188] = 0;
   out_269214026509656143[189] = 0;
   out_269214026509656143[190] = 1;
   out_269214026509656143[191] = 0;
   out_269214026509656143[192] = 0;
   out_269214026509656143[193] = 0;
   out_269214026509656143[194] = 0;
   out_269214026509656143[195] = 0;
   out_269214026509656143[196] = 0;
   out_269214026509656143[197] = 0;
   out_269214026509656143[198] = 0;
   out_269214026509656143[199] = 0;
   out_269214026509656143[200] = 0;
   out_269214026509656143[201] = 0;
   out_269214026509656143[202] = 0;
   out_269214026509656143[203] = 0;
   out_269214026509656143[204] = 0;
   out_269214026509656143[205] = 0;
   out_269214026509656143[206] = 0;
   out_269214026509656143[207] = 0;
   out_269214026509656143[208] = 0;
   out_269214026509656143[209] = 1;
   out_269214026509656143[210] = 0;
   out_269214026509656143[211] = 0;
   out_269214026509656143[212] = 0;
   out_269214026509656143[213] = 0;
   out_269214026509656143[214] = 0;
   out_269214026509656143[215] = 0;
   out_269214026509656143[216] = 0;
   out_269214026509656143[217] = 0;
   out_269214026509656143[218] = 0;
   out_269214026509656143[219] = 0;
   out_269214026509656143[220] = 0;
   out_269214026509656143[221] = 0;
   out_269214026509656143[222] = 0;
   out_269214026509656143[223] = 0;
   out_269214026509656143[224] = 0;
   out_269214026509656143[225] = 0;
   out_269214026509656143[226] = 0;
   out_269214026509656143[227] = 0;
   out_269214026509656143[228] = 1;
   out_269214026509656143[229] = 0;
   out_269214026509656143[230] = 0;
   out_269214026509656143[231] = 0;
   out_269214026509656143[232] = 0;
   out_269214026509656143[233] = 0;
   out_269214026509656143[234] = 0;
   out_269214026509656143[235] = 0;
   out_269214026509656143[236] = 0;
   out_269214026509656143[237] = 0;
   out_269214026509656143[238] = 0;
   out_269214026509656143[239] = 0;
   out_269214026509656143[240] = 0;
   out_269214026509656143[241] = 0;
   out_269214026509656143[242] = 0;
   out_269214026509656143[243] = 0;
   out_269214026509656143[244] = 0;
   out_269214026509656143[245] = 0;
   out_269214026509656143[246] = 0;
   out_269214026509656143[247] = 1;
   out_269214026509656143[248] = 0;
   out_269214026509656143[249] = 0;
   out_269214026509656143[250] = 0;
   out_269214026509656143[251] = 0;
   out_269214026509656143[252] = 0;
   out_269214026509656143[253] = 0;
   out_269214026509656143[254] = 0;
   out_269214026509656143[255] = 0;
   out_269214026509656143[256] = 0;
   out_269214026509656143[257] = 0;
   out_269214026509656143[258] = 0;
   out_269214026509656143[259] = 0;
   out_269214026509656143[260] = 0;
   out_269214026509656143[261] = 0;
   out_269214026509656143[262] = 0;
   out_269214026509656143[263] = 0;
   out_269214026509656143[264] = 0;
   out_269214026509656143[265] = 0;
   out_269214026509656143[266] = 1;
   out_269214026509656143[267] = 0;
   out_269214026509656143[268] = 0;
   out_269214026509656143[269] = 0;
   out_269214026509656143[270] = 0;
   out_269214026509656143[271] = 0;
   out_269214026509656143[272] = 0;
   out_269214026509656143[273] = 0;
   out_269214026509656143[274] = 0;
   out_269214026509656143[275] = 0;
   out_269214026509656143[276] = 0;
   out_269214026509656143[277] = 0;
   out_269214026509656143[278] = 0;
   out_269214026509656143[279] = 0;
   out_269214026509656143[280] = 0;
   out_269214026509656143[281] = 0;
   out_269214026509656143[282] = 0;
   out_269214026509656143[283] = 0;
   out_269214026509656143[284] = 0;
   out_269214026509656143[285] = 1;
   out_269214026509656143[286] = 0;
   out_269214026509656143[287] = 0;
   out_269214026509656143[288] = 0;
   out_269214026509656143[289] = 0;
   out_269214026509656143[290] = 0;
   out_269214026509656143[291] = 0;
   out_269214026509656143[292] = 0;
   out_269214026509656143[293] = 0;
   out_269214026509656143[294] = 0;
   out_269214026509656143[295] = 0;
   out_269214026509656143[296] = 0;
   out_269214026509656143[297] = 0;
   out_269214026509656143[298] = 0;
   out_269214026509656143[299] = 0;
   out_269214026509656143[300] = 0;
   out_269214026509656143[301] = 0;
   out_269214026509656143[302] = 0;
   out_269214026509656143[303] = 0;
   out_269214026509656143[304] = 1;
   out_269214026509656143[305] = 0;
   out_269214026509656143[306] = 0;
   out_269214026509656143[307] = 0;
   out_269214026509656143[308] = 0;
   out_269214026509656143[309] = 0;
   out_269214026509656143[310] = 0;
   out_269214026509656143[311] = 0;
   out_269214026509656143[312] = 0;
   out_269214026509656143[313] = 0;
   out_269214026509656143[314] = 0;
   out_269214026509656143[315] = 0;
   out_269214026509656143[316] = 0;
   out_269214026509656143[317] = 0;
   out_269214026509656143[318] = 0;
   out_269214026509656143[319] = 0;
   out_269214026509656143[320] = 0;
   out_269214026509656143[321] = 0;
   out_269214026509656143[322] = 0;
   out_269214026509656143[323] = 1;
}
void h_4(double *state, double *unused, double *out_6722098375813311917) {
   out_6722098375813311917[0] = state[6] + state[9];
   out_6722098375813311917[1] = state[7] + state[10];
   out_6722098375813311917[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_4092865152446350535) {
   out_4092865152446350535[0] = 0;
   out_4092865152446350535[1] = 0;
   out_4092865152446350535[2] = 0;
   out_4092865152446350535[3] = 0;
   out_4092865152446350535[4] = 0;
   out_4092865152446350535[5] = 0;
   out_4092865152446350535[6] = 1;
   out_4092865152446350535[7] = 0;
   out_4092865152446350535[8] = 0;
   out_4092865152446350535[9] = 1;
   out_4092865152446350535[10] = 0;
   out_4092865152446350535[11] = 0;
   out_4092865152446350535[12] = 0;
   out_4092865152446350535[13] = 0;
   out_4092865152446350535[14] = 0;
   out_4092865152446350535[15] = 0;
   out_4092865152446350535[16] = 0;
   out_4092865152446350535[17] = 0;
   out_4092865152446350535[18] = 0;
   out_4092865152446350535[19] = 0;
   out_4092865152446350535[20] = 0;
   out_4092865152446350535[21] = 0;
   out_4092865152446350535[22] = 0;
   out_4092865152446350535[23] = 0;
   out_4092865152446350535[24] = 0;
   out_4092865152446350535[25] = 1;
   out_4092865152446350535[26] = 0;
   out_4092865152446350535[27] = 0;
   out_4092865152446350535[28] = 1;
   out_4092865152446350535[29] = 0;
   out_4092865152446350535[30] = 0;
   out_4092865152446350535[31] = 0;
   out_4092865152446350535[32] = 0;
   out_4092865152446350535[33] = 0;
   out_4092865152446350535[34] = 0;
   out_4092865152446350535[35] = 0;
   out_4092865152446350535[36] = 0;
   out_4092865152446350535[37] = 0;
   out_4092865152446350535[38] = 0;
   out_4092865152446350535[39] = 0;
   out_4092865152446350535[40] = 0;
   out_4092865152446350535[41] = 0;
   out_4092865152446350535[42] = 0;
   out_4092865152446350535[43] = 0;
   out_4092865152446350535[44] = 1;
   out_4092865152446350535[45] = 0;
   out_4092865152446350535[46] = 0;
   out_4092865152446350535[47] = 1;
   out_4092865152446350535[48] = 0;
   out_4092865152446350535[49] = 0;
   out_4092865152446350535[50] = 0;
   out_4092865152446350535[51] = 0;
   out_4092865152446350535[52] = 0;
   out_4092865152446350535[53] = 0;
}
void h_10(double *state, double *unused, double *out_5359691896685221629) {
   out_5359691896685221629[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_5359691896685221629[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_5359691896685221629[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_5571839411167880879) {
   out_5571839411167880879[0] = 0;
   out_5571839411167880879[1] = 9.8100000000000005*cos(state[1]);
   out_5571839411167880879[2] = 0;
   out_5571839411167880879[3] = 0;
   out_5571839411167880879[4] = -state[8];
   out_5571839411167880879[5] = state[7];
   out_5571839411167880879[6] = 0;
   out_5571839411167880879[7] = state[5];
   out_5571839411167880879[8] = -state[4];
   out_5571839411167880879[9] = 0;
   out_5571839411167880879[10] = 0;
   out_5571839411167880879[11] = 0;
   out_5571839411167880879[12] = 1;
   out_5571839411167880879[13] = 0;
   out_5571839411167880879[14] = 0;
   out_5571839411167880879[15] = 1;
   out_5571839411167880879[16] = 0;
   out_5571839411167880879[17] = 0;
   out_5571839411167880879[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_5571839411167880879[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_5571839411167880879[20] = 0;
   out_5571839411167880879[21] = state[8];
   out_5571839411167880879[22] = 0;
   out_5571839411167880879[23] = -state[6];
   out_5571839411167880879[24] = -state[5];
   out_5571839411167880879[25] = 0;
   out_5571839411167880879[26] = state[3];
   out_5571839411167880879[27] = 0;
   out_5571839411167880879[28] = 0;
   out_5571839411167880879[29] = 0;
   out_5571839411167880879[30] = 0;
   out_5571839411167880879[31] = 1;
   out_5571839411167880879[32] = 0;
   out_5571839411167880879[33] = 0;
   out_5571839411167880879[34] = 1;
   out_5571839411167880879[35] = 0;
   out_5571839411167880879[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_5571839411167880879[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_5571839411167880879[38] = 0;
   out_5571839411167880879[39] = -state[7];
   out_5571839411167880879[40] = state[6];
   out_5571839411167880879[41] = 0;
   out_5571839411167880879[42] = state[4];
   out_5571839411167880879[43] = -state[3];
   out_5571839411167880879[44] = 0;
   out_5571839411167880879[45] = 0;
   out_5571839411167880879[46] = 0;
   out_5571839411167880879[47] = 0;
   out_5571839411167880879[48] = 0;
   out_5571839411167880879[49] = 0;
   out_5571839411167880879[50] = 1;
   out_5571839411167880879[51] = 0;
   out_5571839411167880879[52] = 0;
   out_5571839411167880879[53] = 1;
}
void h_13(double *state, double *unused, double *out_1702932630428691594) {
   out_1702932630428691594[0] = state[3];
   out_1702932630428691594[1] = state[4];
   out_1702932630428691594[2] = state[5];
}
void H_13(double *state, double *unused, double *out_3517766055870350394) {
   out_3517766055870350394[0] = 0;
   out_3517766055870350394[1] = 0;
   out_3517766055870350394[2] = 0;
   out_3517766055870350394[3] = 1;
   out_3517766055870350394[4] = 0;
   out_3517766055870350394[5] = 0;
   out_3517766055870350394[6] = 0;
   out_3517766055870350394[7] = 0;
   out_3517766055870350394[8] = 0;
   out_3517766055870350394[9] = 0;
   out_3517766055870350394[10] = 0;
   out_3517766055870350394[11] = 0;
   out_3517766055870350394[12] = 0;
   out_3517766055870350394[13] = 0;
   out_3517766055870350394[14] = 0;
   out_3517766055870350394[15] = 0;
   out_3517766055870350394[16] = 0;
   out_3517766055870350394[17] = 0;
   out_3517766055870350394[18] = 0;
   out_3517766055870350394[19] = 0;
   out_3517766055870350394[20] = 0;
   out_3517766055870350394[21] = 0;
   out_3517766055870350394[22] = 1;
   out_3517766055870350394[23] = 0;
   out_3517766055870350394[24] = 0;
   out_3517766055870350394[25] = 0;
   out_3517766055870350394[26] = 0;
   out_3517766055870350394[27] = 0;
   out_3517766055870350394[28] = 0;
   out_3517766055870350394[29] = 0;
   out_3517766055870350394[30] = 0;
   out_3517766055870350394[31] = 0;
   out_3517766055870350394[32] = 0;
   out_3517766055870350394[33] = 0;
   out_3517766055870350394[34] = 0;
   out_3517766055870350394[35] = 0;
   out_3517766055870350394[36] = 0;
   out_3517766055870350394[37] = 0;
   out_3517766055870350394[38] = 0;
   out_3517766055870350394[39] = 0;
   out_3517766055870350394[40] = 0;
   out_3517766055870350394[41] = 1;
   out_3517766055870350394[42] = 0;
   out_3517766055870350394[43] = 0;
   out_3517766055870350394[44] = 0;
   out_3517766055870350394[45] = 0;
   out_3517766055870350394[46] = 0;
   out_3517766055870350394[47] = 0;
   out_3517766055870350394[48] = 0;
   out_3517766055870350394[49] = 0;
   out_3517766055870350394[50] = 0;
   out_3517766055870350394[51] = 0;
   out_3517766055870350394[52] = 0;
   out_3517766055870350394[53] = 0;
}
void h_14(double *state, double *unused, double *out_4050504407425724528) {
   out_4050504407425724528[0] = state[6];
   out_4050504407425724528[1] = state[7];
   out_4050504407425724528[2] = state[8];
}
void H_14(double *state, double *unused, double *out_129624296106866006) {
   out_129624296106866006[0] = 0;
   out_129624296106866006[1] = 0;
   out_129624296106866006[2] = 0;
   out_129624296106866006[3] = 0;
   out_129624296106866006[4] = 0;
   out_129624296106866006[5] = 0;
   out_129624296106866006[6] = 1;
   out_129624296106866006[7] = 0;
   out_129624296106866006[8] = 0;
   out_129624296106866006[9] = 0;
   out_129624296106866006[10] = 0;
   out_129624296106866006[11] = 0;
   out_129624296106866006[12] = 0;
   out_129624296106866006[13] = 0;
   out_129624296106866006[14] = 0;
   out_129624296106866006[15] = 0;
   out_129624296106866006[16] = 0;
   out_129624296106866006[17] = 0;
   out_129624296106866006[18] = 0;
   out_129624296106866006[19] = 0;
   out_129624296106866006[20] = 0;
   out_129624296106866006[21] = 0;
   out_129624296106866006[22] = 0;
   out_129624296106866006[23] = 0;
   out_129624296106866006[24] = 0;
   out_129624296106866006[25] = 1;
   out_129624296106866006[26] = 0;
   out_129624296106866006[27] = 0;
   out_129624296106866006[28] = 0;
   out_129624296106866006[29] = 0;
   out_129624296106866006[30] = 0;
   out_129624296106866006[31] = 0;
   out_129624296106866006[32] = 0;
   out_129624296106866006[33] = 0;
   out_129624296106866006[34] = 0;
   out_129624296106866006[35] = 0;
   out_129624296106866006[36] = 0;
   out_129624296106866006[37] = 0;
   out_129624296106866006[38] = 0;
   out_129624296106866006[39] = 0;
   out_129624296106866006[40] = 0;
   out_129624296106866006[41] = 0;
   out_129624296106866006[42] = 0;
   out_129624296106866006[43] = 0;
   out_129624296106866006[44] = 1;
   out_129624296106866006[45] = 0;
   out_129624296106866006[46] = 0;
   out_129624296106866006[47] = 0;
   out_129624296106866006[48] = 0;
   out_129624296106866006[49] = 0;
   out_129624296106866006[50] = 0;
   out_129624296106866006[51] = 0;
   out_129624296106866006[52] = 0;
   out_129624296106866006[53] = 0;
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
void pose_err_fun(double *nom_x, double *delta_x, double *out_2251541010105652257) {
  err_fun(nom_x, delta_x, out_2251541010105652257);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_3400329631105902853) {
  inv_err_fun(nom_x, true_x, out_3400329631105902853);
}
void pose_H_mod_fun(double *state, double *out_7864672362290258107) {
  H_mod_fun(state, out_7864672362290258107);
}
void pose_f_fun(double *state, double dt, double *out_1708698118726409450) {
  f_fun(state,  dt, out_1708698118726409450);
}
void pose_F_fun(double *state, double dt, double *out_269214026509656143) {
  F_fun(state,  dt, out_269214026509656143);
}
void pose_h_4(double *state, double *unused, double *out_6722098375813311917) {
  h_4(state, unused, out_6722098375813311917);
}
void pose_H_4(double *state, double *unused, double *out_4092865152446350535) {
  H_4(state, unused, out_4092865152446350535);
}
void pose_h_10(double *state, double *unused, double *out_5359691896685221629) {
  h_10(state, unused, out_5359691896685221629);
}
void pose_H_10(double *state, double *unused, double *out_5571839411167880879) {
  H_10(state, unused, out_5571839411167880879);
}
void pose_h_13(double *state, double *unused, double *out_1702932630428691594) {
  h_13(state, unused, out_1702932630428691594);
}
void pose_H_13(double *state, double *unused, double *out_3517766055870350394) {
  H_13(state, unused, out_3517766055870350394);
}
void pose_h_14(double *state, double *unused, double *out_4050504407425724528) {
  h_14(state, unused, out_4050504407425724528);
}
void pose_H_14(double *state, double *unused, double *out_129624296106866006) {
  H_14(state, unused, out_129624296106866006);
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
