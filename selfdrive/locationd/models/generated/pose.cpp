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
void err_fun(double *nom_x, double *delta_x, double *out_7165967535860238129) {
   out_7165967535860238129[0] = delta_x[0] + nom_x[0];
   out_7165967535860238129[1] = delta_x[1] + nom_x[1];
   out_7165967535860238129[2] = delta_x[2] + nom_x[2];
   out_7165967535860238129[3] = delta_x[3] + nom_x[3];
   out_7165967535860238129[4] = delta_x[4] + nom_x[4];
   out_7165967535860238129[5] = delta_x[5] + nom_x[5];
   out_7165967535860238129[6] = delta_x[6] + nom_x[6];
   out_7165967535860238129[7] = delta_x[7] + nom_x[7];
   out_7165967535860238129[8] = delta_x[8] + nom_x[8];
   out_7165967535860238129[9] = delta_x[9] + nom_x[9];
   out_7165967535860238129[10] = delta_x[10] + nom_x[10];
   out_7165967535860238129[11] = delta_x[11] + nom_x[11];
   out_7165967535860238129[12] = delta_x[12] + nom_x[12];
   out_7165967535860238129[13] = delta_x[13] + nom_x[13];
   out_7165967535860238129[14] = delta_x[14] + nom_x[14];
   out_7165967535860238129[15] = delta_x[15] + nom_x[15];
   out_7165967535860238129[16] = delta_x[16] + nom_x[16];
   out_7165967535860238129[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_9032729807193459598) {
   out_9032729807193459598[0] = -nom_x[0] + true_x[0];
   out_9032729807193459598[1] = -nom_x[1] + true_x[1];
   out_9032729807193459598[2] = -nom_x[2] + true_x[2];
   out_9032729807193459598[3] = -nom_x[3] + true_x[3];
   out_9032729807193459598[4] = -nom_x[4] + true_x[4];
   out_9032729807193459598[5] = -nom_x[5] + true_x[5];
   out_9032729807193459598[6] = -nom_x[6] + true_x[6];
   out_9032729807193459598[7] = -nom_x[7] + true_x[7];
   out_9032729807193459598[8] = -nom_x[8] + true_x[8];
   out_9032729807193459598[9] = -nom_x[9] + true_x[9];
   out_9032729807193459598[10] = -nom_x[10] + true_x[10];
   out_9032729807193459598[11] = -nom_x[11] + true_x[11];
   out_9032729807193459598[12] = -nom_x[12] + true_x[12];
   out_9032729807193459598[13] = -nom_x[13] + true_x[13];
   out_9032729807193459598[14] = -nom_x[14] + true_x[14];
   out_9032729807193459598[15] = -nom_x[15] + true_x[15];
   out_9032729807193459598[16] = -nom_x[16] + true_x[16];
   out_9032729807193459598[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_5054599202167139908) {
   out_5054599202167139908[0] = 1.0;
   out_5054599202167139908[1] = 0.0;
   out_5054599202167139908[2] = 0.0;
   out_5054599202167139908[3] = 0.0;
   out_5054599202167139908[4] = 0.0;
   out_5054599202167139908[5] = 0.0;
   out_5054599202167139908[6] = 0.0;
   out_5054599202167139908[7] = 0.0;
   out_5054599202167139908[8] = 0.0;
   out_5054599202167139908[9] = 0.0;
   out_5054599202167139908[10] = 0.0;
   out_5054599202167139908[11] = 0.0;
   out_5054599202167139908[12] = 0.0;
   out_5054599202167139908[13] = 0.0;
   out_5054599202167139908[14] = 0.0;
   out_5054599202167139908[15] = 0.0;
   out_5054599202167139908[16] = 0.0;
   out_5054599202167139908[17] = 0.0;
   out_5054599202167139908[18] = 0.0;
   out_5054599202167139908[19] = 1.0;
   out_5054599202167139908[20] = 0.0;
   out_5054599202167139908[21] = 0.0;
   out_5054599202167139908[22] = 0.0;
   out_5054599202167139908[23] = 0.0;
   out_5054599202167139908[24] = 0.0;
   out_5054599202167139908[25] = 0.0;
   out_5054599202167139908[26] = 0.0;
   out_5054599202167139908[27] = 0.0;
   out_5054599202167139908[28] = 0.0;
   out_5054599202167139908[29] = 0.0;
   out_5054599202167139908[30] = 0.0;
   out_5054599202167139908[31] = 0.0;
   out_5054599202167139908[32] = 0.0;
   out_5054599202167139908[33] = 0.0;
   out_5054599202167139908[34] = 0.0;
   out_5054599202167139908[35] = 0.0;
   out_5054599202167139908[36] = 0.0;
   out_5054599202167139908[37] = 0.0;
   out_5054599202167139908[38] = 1.0;
   out_5054599202167139908[39] = 0.0;
   out_5054599202167139908[40] = 0.0;
   out_5054599202167139908[41] = 0.0;
   out_5054599202167139908[42] = 0.0;
   out_5054599202167139908[43] = 0.0;
   out_5054599202167139908[44] = 0.0;
   out_5054599202167139908[45] = 0.0;
   out_5054599202167139908[46] = 0.0;
   out_5054599202167139908[47] = 0.0;
   out_5054599202167139908[48] = 0.0;
   out_5054599202167139908[49] = 0.0;
   out_5054599202167139908[50] = 0.0;
   out_5054599202167139908[51] = 0.0;
   out_5054599202167139908[52] = 0.0;
   out_5054599202167139908[53] = 0.0;
   out_5054599202167139908[54] = 0.0;
   out_5054599202167139908[55] = 0.0;
   out_5054599202167139908[56] = 0.0;
   out_5054599202167139908[57] = 1.0;
   out_5054599202167139908[58] = 0.0;
   out_5054599202167139908[59] = 0.0;
   out_5054599202167139908[60] = 0.0;
   out_5054599202167139908[61] = 0.0;
   out_5054599202167139908[62] = 0.0;
   out_5054599202167139908[63] = 0.0;
   out_5054599202167139908[64] = 0.0;
   out_5054599202167139908[65] = 0.0;
   out_5054599202167139908[66] = 0.0;
   out_5054599202167139908[67] = 0.0;
   out_5054599202167139908[68] = 0.0;
   out_5054599202167139908[69] = 0.0;
   out_5054599202167139908[70] = 0.0;
   out_5054599202167139908[71] = 0.0;
   out_5054599202167139908[72] = 0.0;
   out_5054599202167139908[73] = 0.0;
   out_5054599202167139908[74] = 0.0;
   out_5054599202167139908[75] = 0.0;
   out_5054599202167139908[76] = 1.0;
   out_5054599202167139908[77] = 0.0;
   out_5054599202167139908[78] = 0.0;
   out_5054599202167139908[79] = 0.0;
   out_5054599202167139908[80] = 0.0;
   out_5054599202167139908[81] = 0.0;
   out_5054599202167139908[82] = 0.0;
   out_5054599202167139908[83] = 0.0;
   out_5054599202167139908[84] = 0.0;
   out_5054599202167139908[85] = 0.0;
   out_5054599202167139908[86] = 0.0;
   out_5054599202167139908[87] = 0.0;
   out_5054599202167139908[88] = 0.0;
   out_5054599202167139908[89] = 0.0;
   out_5054599202167139908[90] = 0.0;
   out_5054599202167139908[91] = 0.0;
   out_5054599202167139908[92] = 0.0;
   out_5054599202167139908[93] = 0.0;
   out_5054599202167139908[94] = 0.0;
   out_5054599202167139908[95] = 1.0;
   out_5054599202167139908[96] = 0.0;
   out_5054599202167139908[97] = 0.0;
   out_5054599202167139908[98] = 0.0;
   out_5054599202167139908[99] = 0.0;
   out_5054599202167139908[100] = 0.0;
   out_5054599202167139908[101] = 0.0;
   out_5054599202167139908[102] = 0.0;
   out_5054599202167139908[103] = 0.0;
   out_5054599202167139908[104] = 0.0;
   out_5054599202167139908[105] = 0.0;
   out_5054599202167139908[106] = 0.0;
   out_5054599202167139908[107] = 0.0;
   out_5054599202167139908[108] = 0.0;
   out_5054599202167139908[109] = 0.0;
   out_5054599202167139908[110] = 0.0;
   out_5054599202167139908[111] = 0.0;
   out_5054599202167139908[112] = 0.0;
   out_5054599202167139908[113] = 0.0;
   out_5054599202167139908[114] = 1.0;
   out_5054599202167139908[115] = 0.0;
   out_5054599202167139908[116] = 0.0;
   out_5054599202167139908[117] = 0.0;
   out_5054599202167139908[118] = 0.0;
   out_5054599202167139908[119] = 0.0;
   out_5054599202167139908[120] = 0.0;
   out_5054599202167139908[121] = 0.0;
   out_5054599202167139908[122] = 0.0;
   out_5054599202167139908[123] = 0.0;
   out_5054599202167139908[124] = 0.0;
   out_5054599202167139908[125] = 0.0;
   out_5054599202167139908[126] = 0.0;
   out_5054599202167139908[127] = 0.0;
   out_5054599202167139908[128] = 0.0;
   out_5054599202167139908[129] = 0.0;
   out_5054599202167139908[130] = 0.0;
   out_5054599202167139908[131] = 0.0;
   out_5054599202167139908[132] = 0.0;
   out_5054599202167139908[133] = 1.0;
   out_5054599202167139908[134] = 0.0;
   out_5054599202167139908[135] = 0.0;
   out_5054599202167139908[136] = 0.0;
   out_5054599202167139908[137] = 0.0;
   out_5054599202167139908[138] = 0.0;
   out_5054599202167139908[139] = 0.0;
   out_5054599202167139908[140] = 0.0;
   out_5054599202167139908[141] = 0.0;
   out_5054599202167139908[142] = 0.0;
   out_5054599202167139908[143] = 0.0;
   out_5054599202167139908[144] = 0.0;
   out_5054599202167139908[145] = 0.0;
   out_5054599202167139908[146] = 0.0;
   out_5054599202167139908[147] = 0.0;
   out_5054599202167139908[148] = 0.0;
   out_5054599202167139908[149] = 0.0;
   out_5054599202167139908[150] = 0.0;
   out_5054599202167139908[151] = 0.0;
   out_5054599202167139908[152] = 1.0;
   out_5054599202167139908[153] = 0.0;
   out_5054599202167139908[154] = 0.0;
   out_5054599202167139908[155] = 0.0;
   out_5054599202167139908[156] = 0.0;
   out_5054599202167139908[157] = 0.0;
   out_5054599202167139908[158] = 0.0;
   out_5054599202167139908[159] = 0.0;
   out_5054599202167139908[160] = 0.0;
   out_5054599202167139908[161] = 0.0;
   out_5054599202167139908[162] = 0.0;
   out_5054599202167139908[163] = 0.0;
   out_5054599202167139908[164] = 0.0;
   out_5054599202167139908[165] = 0.0;
   out_5054599202167139908[166] = 0.0;
   out_5054599202167139908[167] = 0.0;
   out_5054599202167139908[168] = 0.0;
   out_5054599202167139908[169] = 0.0;
   out_5054599202167139908[170] = 0.0;
   out_5054599202167139908[171] = 1.0;
   out_5054599202167139908[172] = 0.0;
   out_5054599202167139908[173] = 0.0;
   out_5054599202167139908[174] = 0.0;
   out_5054599202167139908[175] = 0.0;
   out_5054599202167139908[176] = 0.0;
   out_5054599202167139908[177] = 0.0;
   out_5054599202167139908[178] = 0.0;
   out_5054599202167139908[179] = 0.0;
   out_5054599202167139908[180] = 0.0;
   out_5054599202167139908[181] = 0.0;
   out_5054599202167139908[182] = 0.0;
   out_5054599202167139908[183] = 0.0;
   out_5054599202167139908[184] = 0.0;
   out_5054599202167139908[185] = 0.0;
   out_5054599202167139908[186] = 0.0;
   out_5054599202167139908[187] = 0.0;
   out_5054599202167139908[188] = 0.0;
   out_5054599202167139908[189] = 0.0;
   out_5054599202167139908[190] = 1.0;
   out_5054599202167139908[191] = 0.0;
   out_5054599202167139908[192] = 0.0;
   out_5054599202167139908[193] = 0.0;
   out_5054599202167139908[194] = 0.0;
   out_5054599202167139908[195] = 0.0;
   out_5054599202167139908[196] = 0.0;
   out_5054599202167139908[197] = 0.0;
   out_5054599202167139908[198] = 0.0;
   out_5054599202167139908[199] = 0.0;
   out_5054599202167139908[200] = 0.0;
   out_5054599202167139908[201] = 0.0;
   out_5054599202167139908[202] = 0.0;
   out_5054599202167139908[203] = 0.0;
   out_5054599202167139908[204] = 0.0;
   out_5054599202167139908[205] = 0.0;
   out_5054599202167139908[206] = 0.0;
   out_5054599202167139908[207] = 0.0;
   out_5054599202167139908[208] = 0.0;
   out_5054599202167139908[209] = 1.0;
   out_5054599202167139908[210] = 0.0;
   out_5054599202167139908[211] = 0.0;
   out_5054599202167139908[212] = 0.0;
   out_5054599202167139908[213] = 0.0;
   out_5054599202167139908[214] = 0.0;
   out_5054599202167139908[215] = 0.0;
   out_5054599202167139908[216] = 0.0;
   out_5054599202167139908[217] = 0.0;
   out_5054599202167139908[218] = 0.0;
   out_5054599202167139908[219] = 0.0;
   out_5054599202167139908[220] = 0.0;
   out_5054599202167139908[221] = 0.0;
   out_5054599202167139908[222] = 0.0;
   out_5054599202167139908[223] = 0.0;
   out_5054599202167139908[224] = 0.0;
   out_5054599202167139908[225] = 0.0;
   out_5054599202167139908[226] = 0.0;
   out_5054599202167139908[227] = 0.0;
   out_5054599202167139908[228] = 1.0;
   out_5054599202167139908[229] = 0.0;
   out_5054599202167139908[230] = 0.0;
   out_5054599202167139908[231] = 0.0;
   out_5054599202167139908[232] = 0.0;
   out_5054599202167139908[233] = 0.0;
   out_5054599202167139908[234] = 0.0;
   out_5054599202167139908[235] = 0.0;
   out_5054599202167139908[236] = 0.0;
   out_5054599202167139908[237] = 0.0;
   out_5054599202167139908[238] = 0.0;
   out_5054599202167139908[239] = 0.0;
   out_5054599202167139908[240] = 0.0;
   out_5054599202167139908[241] = 0.0;
   out_5054599202167139908[242] = 0.0;
   out_5054599202167139908[243] = 0.0;
   out_5054599202167139908[244] = 0.0;
   out_5054599202167139908[245] = 0.0;
   out_5054599202167139908[246] = 0.0;
   out_5054599202167139908[247] = 1.0;
   out_5054599202167139908[248] = 0.0;
   out_5054599202167139908[249] = 0.0;
   out_5054599202167139908[250] = 0.0;
   out_5054599202167139908[251] = 0.0;
   out_5054599202167139908[252] = 0.0;
   out_5054599202167139908[253] = 0.0;
   out_5054599202167139908[254] = 0.0;
   out_5054599202167139908[255] = 0.0;
   out_5054599202167139908[256] = 0.0;
   out_5054599202167139908[257] = 0.0;
   out_5054599202167139908[258] = 0.0;
   out_5054599202167139908[259] = 0.0;
   out_5054599202167139908[260] = 0.0;
   out_5054599202167139908[261] = 0.0;
   out_5054599202167139908[262] = 0.0;
   out_5054599202167139908[263] = 0.0;
   out_5054599202167139908[264] = 0.0;
   out_5054599202167139908[265] = 0.0;
   out_5054599202167139908[266] = 1.0;
   out_5054599202167139908[267] = 0.0;
   out_5054599202167139908[268] = 0.0;
   out_5054599202167139908[269] = 0.0;
   out_5054599202167139908[270] = 0.0;
   out_5054599202167139908[271] = 0.0;
   out_5054599202167139908[272] = 0.0;
   out_5054599202167139908[273] = 0.0;
   out_5054599202167139908[274] = 0.0;
   out_5054599202167139908[275] = 0.0;
   out_5054599202167139908[276] = 0.0;
   out_5054599202167139908[277] = 0.0;
   out_5054599202167139908[278] = 0.0;
   out_5054599202167139908[279] = 0.0;
   out_5054599202167139908[280] = 0.0;
   out_5054599202167139908[281] = 0.0;
   out_5054599202167139908[282] = 0.0;
   out_5054599202167139908[283] = 0.0;
   out_5054599202167139908[284] = 0.0;
   out_5054599202167139908[285] = 1.0;
   out_5054599202167139908[286] = 0.0;
   out_5054599202167139908[287] = 0.0;
   out_5054599202167139908[288] = 0.0;
   out_5054599202167139908[289] = 0.0;
   out_5054599202167139908[290] = 0.0;
   out_5054599202167139908[291] = 0.0;
   out_5054599202167139908[292] = 0.0;
   out_5054599202167139908[293] = 0.0;
   out_5054599202167139908[294] = 0.0;
   out_5054599202167139908[295] = 0.0;
   out_5054599202167139908[296] = 0.0;
   out_5054599202167139908[297] = 0.0;
   out_5054599202167139908[298] = 0.0;
   out_5054599202167139908[299] = 0.0;
   out_5054599202167139908[300] = 0.0;
   out_5054599202167139908[301] = 0.0;
   out_5054599202167139908[302] = 0.0;
   out_5054599202167139908[303] = 0.0;
   out_5054599202167139908[304] = 1.0;
   out_5054599202167139908[305] = 0.0;
   out_5054599202167139908[306] = 0.0;
   out_5054599202167139908[307] = 0.0;
   out_5054599202167139908[308] = 0.0;
   out_5054599202167139908[309] = 0.0;
   out_5054599202167139908[310] = 0.0;
   out_5054599202167139908[311] = 0.0;
   out_5054599202167139908[312] = 0.0;
   out_5054599202167139908[313] = 0.0;
   out_5054599202167139908[314] = 0.0;
   out_5054599202167139908[315] = 0.0;
   out_5054599202167139908[316] = 0.0;
   out_5054599202167139908[317] = 0.0;
   out_5054599202167139908[318] = 0.0;
   out_5054599202167139908[319] = 0.0;
   out_5054599202167139908[320] = 0.0;
   out_5054599202167139908[321] = 0.0;
   out_5054599202167139908[322] = 0.0;
   out_5054599202167139908[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_5000035888964044284) {
   out_5000035888964044284[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_5000035888964044284[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_5000035888964044284[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_5000035888964044284[3] = dt*state[12] + state[3];
   out_5000035888964044284[4] = dt*state[13] + state[4];
   out_5000035888964044284[5] = dt*state[14] + state[5];
   out_5000035888964044284[6] = state[6];
   out_5000035888964044284[7] = state[7];
   out_5000035888964044284[8] = state[8];
   out_5000035888964044284[9] = state[9];
   out_5000035888964044284[10] = state[10];
   out_5000035888964044284[11] = state[11];
   out_5000035888964044284[12] = state[12];
   out_5000035888964044284[13] = state[13];
   out_5000035888964044284[14] = state[14];
   out_5000035888964044284[15] = state[15];
   out_5000035888964044284[16] = state[16];
   out_5000035888964044284[17] = state[17];
}
void F_fun(double *state, double dt, double *out_9018422947626896264) {
   out_9018422947626896264[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_9018422947626896264[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_9018422947626896264[2] = 0;
   out_9018422947626896264[3] = 0;
   out_9018422947626896264[4] = 0;
   out_9018422947626896264[5] = 0;
   out_9018422947626896264[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_9018422947626896264[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_9018422947626896264[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_9018422947626896264[9] = 0;
   out_9018422947626896264[10] = 0;
   out_9018422947626896264[11] = 0;
   out_9018422947626896264[12] = 0;
   out_9018422947626896264[13] = 0;
   out_9018422947626896264[14] = 0;
   out_9018422947626896264[15] = 0;
   out_9018422947626896264[16] = 0;
   out_9018422947626896264[17] = 0;
   out_9018422947626896264[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_9018422947626896264[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_9018422947626896264[20] = 0;
   out_9018422947626896264[21] = 0;
   out_9018422947626896264[22] = 0;
   out_9018422947626896264[23] = 0;
   out_9018422947626896264[24] = 0;
   out_9018422947626896264[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_9018422947626896264[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_9018422947626896264[27] = 0;
   out_9018422947626896264[28] = 0;
   out_9018422947626896264[29] = 0;
   out_9018422947626896264[30] = 0;
   out_9018422947626896264[31] = 0;
   out_9018422947626896264[32] = 0;
   out_9018422947626896264[33] = 0;
   out_9018422947626896264[34] = 0;
   out_9018422947626896264[35] = 0;
   out_9018422947626896264[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_9018422947626896264[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_9018422947626896264[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_9018422947626896264[39] = 0;
   out_9018422947626896264[40] = 0;
   out_9018422947626896264[41] = 0;
   out_9018422947626896264[42] = 0;
   out_9018422947626896264[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_9018422947626896264[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_9018422947626896264[45] = 0;
   out_9018422947626896264[46] = 0;
   out_9018422947626896264[47] = 0;
   out_9018422947626896264[48] = 0;
   out_9018422947626896264[49] = 0;
   out_9018422947626896264[50] = 0;
   out_9018422947626896264[51] = 0;
   out_9018422947626896264[52] = 0;
   out_9018422947626896264[53] = 0;
   out_9018422947626896264[54] = 0;
   out_9018422947626896264[55] = 0;
   out_9018422947626896264[56] = 0;
   out_9018422947626896264[57] = 1;
   out_9018422947626896264[58] = 0;
   out_9018422947626896264[59] = 0;
   out_9018422947626896264[60] = 0;
   out_9018422947626896264[61] = 0;
   out_9018422947626896264[62] = 0;
   out_9018422947626896264[63] = 0;
   out_9018422947626896264[64] = 0;
   out_9018422947626896264[65] = 0;
   out_9018422947626896264[66] = dt;
   out_9018422947626896264[67] = 0;
   out_9018422947626896264[68] = 0;
   out_9018422947626896264[69] = 0;
   out_9018422947626896264[70] = 0;
   out_9018422947626896264[71] = 0;
   out_9018422947626896264[72] = 0;
   out_9018422947626896264[73] = 0;
   out_9018422947626896264[74] = 0;
   out_9018422947626896264[75] = 0;
   out_9018422947626896264[76] = 1;
   out_9018422947626896264[77] = 0;
   out_9018422947626896264[78] = 0;
   out_9018422947626896264[79] = 0;
   out_9018422947626896264[80] = 0;
   out_9018422947626896264[81] = 0;
   out_9018422947626896264[82] = 0;
   out_9018422947626896264[83] = 0;
   out_9018422947626896264[84] = 0;
   out_9018422947626896264[85] = dt;
   out_9018422947626896264[86] = 0;
   out_9018422947626896264[87] = 0;
   out_9018422947626896264[88] = 0;
   out_9018422947626896264[89] = 0;
   out_9018422947626896264[90] = 0;
   out_9018422947626896264[91] = 0;
   out_9018422947626896264[92] = 0;
   out_9018422947626896264[93] = 0;
   out_9018422947626896264[94] = 0;
   out_9018422947626896264[95] = 1;
   out_9018422947626896264[96] = 0;
   out_9018422947626896264[97] = 0;
   out_9018422947626896264[98] = 0;
   out_9018422947626896264[99] = 0;
   out_9018422947626896264[100] = 0;
   out_9018422947626896264[101] = 0;
   out_9018422947626896264[102] = 0;
   out_9018422947626896264[103] = 0;
   out_9018422947626896264[104] = dt;
   out_9018422947626896264[105] = 0;
   out_9018422947626896264[106] = 0;
   out_9018422947626896264[107] = 0;
   out_9018422947626896264[108] = 0;
   out_9018422947626896264[109] = 0;
   out_9018422947626896264[110] = 0;
   out_9018422947626896264[111] = 0;
   out_9018422947626896264[112] = 0;
   out_9018422947626896264[113] = 0;
   out_9018422947626896264[114] = 1;
   out_9018422947626896264[115] = 0;
   out_9018422947626896264[116] = 0;
   out_9018422947626896264[117] = 0;
   out_9018422947626896264[118] = 0;
   out_9018422947626896264[119] = 0;
   out_9018422947626896264[120] = 0;
   out_9018422947626896264[121] = 0;
   out_9018422947626896264[122] = 0;
   out_9018422947626896264[123] = 0;
   out_9018422947626896264[124] = 0;
   out_9018422947626896264[125] = 0;
   out_9018422947626896264[126] = 0;
   out_9018422947626896264[127] = 0;
   out_9018422947626896264[128] = 0;
   out_9018422947626896264[129] = 0;
   out_9018422947626896264[130] = 0;
   out_9018422947626896264[131] = 0;
   out_9018422947626896264[132] = 0;
   out_9018422947626896264[133] = 1;
   out_9018422947626896264[134] = 0;
   out_9018422947626896264[135] = 0;
   out_9018422947626896264[136] = 0;
   out_9018422947626896264[137] = 0;
   out_9018422947626896264[138] = 0;
   out_9018422947626896264[139] = 0;
   out_9018422947626896264[140] = 0;
   out_9018422947626896264[141] = 0;
   out_9018422947626896264[142] = 0;
   out_9018422947626896264[143] = 0;
   out_9018422947626896264[144] = 0;
   out_9018422947626896264[145] = 0;
   out_9018422947626896264[146] = 0;
   out_9018422947626896264[147] = 0;
   out_9018422947626896264[148] = 0;
   out_9018422947626896264[149] = 0;
   out_9018422947626896264[150] = 0;
   out_9018422947626896264[151] = 0;
   out_9018422947626896264[152] = 1;
   out_9018422947626896264[153] = 0;
   out_9018422947626896264[154] = 0;
   out_9018422947626896264[155] = 0;
   out_9018422947626896264[156] = 0;
   out_9018422947626896264[157] = 0;
   out_9018422947626896264[158] = 0;
   out_9018422947626896264[159] = 0;
   out_9018422947626896264[160] = 0;
   out_9018422947626896264[161] = 0;
   out_9018422947626896264[162] = 0;
   out_9018422947626896264[163] = 0;
   out_9018422947626896264[164] = 0;
   out_9018422947626896264[165] = 0;
   out_9018422947626896264[166] = 0;
   out_9018422947626896264[167] = 0;
   out_9018422947626896264[168] = 0;
   out_9018422947626896264[169] = 0;
   out_9018422947626896264[170] = 0;
   out_9018422947626896264[171] = 1;
   out_9018422947626896264[172] = 0;
   out_9018422947626896264[173] = 0;
   out_9018422947626896264[174] = 0;
   out_9018422947626896264[175] = 0;
   out_9018422947626896264[176] = 0;
   out_9018422947626896264[177] = 0;
   out_9018422947626896264[178] = 0;
   out_9018422947626896264[179] = 0;
   out_9018422947626896264[180] = 0;
   out_9018422947626896264[181] = 0;
   out_9018422947626896264[182] = 0;
   out_9018422947626896264[183] = 0;
   out_9018422947626896264[184] = 0;
   out_9018422947626896264[185] = 0;
   out_9018422947626896264[186] = 0;
   out_9018422947626896264[187] = 0;
   out_9018422947626896264[188] = 0;
   out_9018422947626896264[189] = 0;
   out_9018422947626896264[190] = 1;
   out_9018422947626896264[191] = 0;
   out_9018422947626896264[192] = 0;
   out_9018422947626896264[193] = 0;
   out_9018422947626896264[194] = 0;
   out_9018422947626896264[195] = 0;
   out_9018422947626896264[196] = 0;
   out_9018422947626896264[197] = 0;
   out_9018422947626896264[198] = 0;
   out_9018422947626896264[199] = 0;
   out_9018422947626896264[200] = 0;
   out_9018422947626896264[201] = 0;
   out_9018422947626896264[202] = 0;
   out_9018422947626896264[203] = 0;
   out_9018422947626896264[204] = 0;
   out_9018422947626896264[205] = 0;
   out_9018422947626896264[206] = 0;
   out_9018422947626896264[207] = 0;
   out_9018422947626896264[208] = 0;
   out_9018422947626896264[209] = 1;
   out_9018422947626896264[210] = 0;
   out_9018422947626896264[211] = 0;
   out_9018422947626896264[212] = 0;
   out_9018422947626896264[213] = 0;
   out_9018422947626896264[214] = 0;
   out_9018422947626896264[215] = 0;
   out_9018422947626896264[216] = 0;
   out_9018422947626896264[217] = 0;
   out_9018422947626896264[218] = 0;
   out_9018422947626896264[219] = 0;
   out_9018422947626896264[220] = 0;
   out_9018422947626896264[221] = 0;
   out_9018422947626896264[222] = 0;
   out_9018422947626896264[223] = 0;
   out_9018422947626896264[224] = 0;
   out_9018422947626896264[225] = 0;
   out_9018422947626896264[226] = 0;
   out_9018422947626896264[227] = 0;
   out_9018422947626896264[228] = 1;
   out_9018422947626896264[229] = 0;
   out_9018422947626896264[230] = 0;
   out_9018422947626896264[231] = 0;
   out_9018422947626896264[232] = 0;
   out_9018422947626896264[233] = 0;
   out_9018422947626896264[234] = 0;
   out_9018422947626896264[235] = 0;
   out_9018422947626896264[236] = 0;
   out_9018422947626896264[237] = 0;
   out_9018422947626896264[238] = 0;
   out_9018422947626896264[239] = 0;
   out_9018422947626896264[240] = 0;
   out_9018422947626896264[241] = 0;
   out_9018422947626896264[242] = 0;
   out_9018422947626896264[243] = 0;
   out_9018422947626896264[244] = 0;
   out_9018422947626896264[245] = 0;
   out_9018422947626896264[246] = 0;
   out_9018422947626896264[247] = 1;
   out_9018422947626896264[248] = 0;
   out_9018422947626896264[249] = 0;
   out_9018422947626896264[250] = 0;
   out_9018422947626896264[251] = 0;
   out_9018422947626896264[252] = 0;
   out_9018422947626896264[253] = 0;
   out_9018422947626896264[254] = 0;
   out_9018422947626896264[255] = 0;
   out_9018422947626896264[256] = 0;
   out_9018422947626896264[257] = 0;
   out_9018422947626896264[258] = 0;
   out_9018422947626896264[259] = 0;
   out_9018422947626896264[260] = 0;
   out_9018422947626896264[261] = 0;
   out_9018422947626896264[262] = 0;
   out_9018422947626896264[263] = 0;
   out_9018422947626896264[264] = 0;
   out_9018422947626896264[265] = 0;
   out_9018422947626896264[266] = 1;
   out_9018422947626896264[267] = 0;
   out_9018422947626896264[268] = 0;
   out_9018422947626896264[269] = 0;
   out_9018422947626896264[270] = 0;
   out_9018422947626896264[271] = 0;
   out_9018422947626896264[272] = 0;
   out_9018422947626896264[273] = 0;
   out_9018422947626896264[274] = 0;
   out_9018422947626896264[275] = 0;
   out_9018422947626896264[276] = 0;
   out_9018422947626896264[277] = 0;
   out_9018422947626896264[278] = 0;
   out_9018422947626896264[279] = 0;
   out_9018422947626896264[280] = 0;
   out_9018422947626896264[281] = 0;
   out_9018422947626896264[282] = 0;
   out_9018422947626896264[283] = 0;
   out_9018422947626896264[284] = 0;
   out_9018422947626896264[285] = 1;
   out_9018422947626896264[286] = 0;
   out_9018422947626896264[287] = 0;
   out_9018422947626896264[288] = 0;
   out_9018422947626896264[289] = 0;
   out_9018422947626896264[290] = 0;
   out_9018422947626896264[291] = 0;
   out_9018422947626896264[292] = 0;
   out_9018422947626896264[293] = 0;
   out_9018422947626896264[294] = 0;
   out_9018422947626896264[295] = 0;
   out_9018422947626896264[296] = 0;
   out_9018422947626896264[297] = 0;
   out_9018422947626896264[298] = 0;
   out_9018422947626896264[299] = 0;
   out_9018422947626896264[300] = 0;
   out_9018422947626896264[301] = 0;
   out_9018422947626896264[302] = 0;
   out_9018422947626896264[303] = 0;
   out_9018422947626896264[304] = 1;
   out_9018422947626896264[305] = 0;
   out_9018422947626896264[306] = 0;
   out_9018422947626896264[307] = 0;
   out_9018422947626896264[308] = 0;
   out_9018422947626896264[309] = 0;
   out_9018422947626896264[310] = 0;
   out_9018422947626896264[311] = 0;
   out_9018422947626896264[312] = 0;
   out_9018422947626896264[313] = 0;
   out_9018422947626896264[314] = 0;
   out_9018422947626896264[315] = 0;
   out_9018422947626896264[316] = 0;
   out_9018422947626896264[317] = 0;
   out_9018422947626896264[318] = 0;
   out_9018422947626896264[319] = 0;
   out_9018422947626896264[320] = 0;
   out_9018422947626896264[321] = 0;
   out_9018422947626896264[322] = 0;
   out_9018422947626896264[323] = 1;
}
void h_4(double *state, double *unused, double *out_6773718258743003346) {
   out_6773718258743003346[0] = state[6] + state[9];
   out_6773718258743003346[1] = state[7] + state[10];
   out_6773718258743003346[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_793482604584818813) {
   out_793482604584818813[0] = 0;
   out_793482604584818813[1] = 0;
   out_793482604584818813[2] = 0;
   out_793482604584818813[3] = 0;
   out_793482604584818813[4] = 0;
   out_793482604584818813[5] = 0;
   out_793482604584818813[6] = 1;
   out_793482604584818813[7] = 0;
   out_793482604584818813[8] = 0;
   out_793482604584818813[9] = 1;
   out_793482604584818813[10] = 0;
   out_793482604584818813[11] = 0;
   out_793482604584818813[12] = 0;
   out_793482604584818813[13] = 0;
   out_793482604584818813[14] = 0;
   out_793482604584818813[15] = 0;
   out_793482604584818813[16] = 0;
   out_793482604584818813[17] = 0;
   out_793482604584818813[18] = 0;
   out_793482604584818813[19] = 0;
   out_793482604584818813[20] = 0;
   out_793482604584818813[21] = 0;
   out_793482604584818813[22] = 0;
   out_793482604584818813[23] = 0;
   out_793482604584818813[24] = 0;
   out_793482604584818813[25] = 1;
   out_793482604584818813[26] = 0;
   out_793482604584818813[27] = 0;
   out_793482604584818813[28] = 1;
   out_793482604584818813[29] = 0;
   out_793482604584818813[30] = 0;
   out_793482604584818813[31] = 0;
   out_793482604584818813[32] = 0;
   out_793482604584818813[33] = 0;
   out_793482604584818813[34] = 0;
   out_793482604584818813[35] = 0;
   out_793482604584818813[36] = 0;
   out_793482604584818813[37] = 0;
   out_793482604584818813[38] = 0;
   out_793482604584818813[39] = 0;
   out_793482604584818813[40] = 0;
   out_793482604584818813[41] = 0;
   out_793482604584818813[42] = 0;
   out_793482604584818813[43] = 0;
   out_793482604584818813[44] = 1;
   out_793482604584818813[45] = 0;
   out_793482604584818813[46] = 0;
   out_793482604584818813[47] = 1;
   out_793482604584818813[48] = 0;
   out_793482604584818813[49] = 0;
   out_793482604584818813[50] = 0;
   out_793482604584818813[51] = 0;
   out_793482604584818813[52] = 0;
   out_793482604584818813[53] = 0;
}
void h_10(double *state, double *unused, double *out_3870110240018051215) {
   out_3870110240018051215[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_3870110240018051215[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_3870110240018051215[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_3089556940454179292) {
   out_3089556940454179292[0] = 0;
   out_3089556940454179292[1] = 9.8100000000000005*cos(state[1]);
   out_3089556940454179292[2] = 0;
   out_3089556940454179292[3] = 0;
   out_3089556940454179292[4] = -state[8];
   out_3089556940454179292[5] = state[7];
   out_3089556940454179292[6] = 0;
   out_3089556940454179292[7] = state[5];
   out_3089556940454179292[8] = -state[4];
   out_3089556940454179292[9] = 0;
   out_3089556940454179292[10] = 0;
   out_3089556940454179292[11] = 0;
   out_3089556940454179292[12] = 1;
   out_3089556940454179292[13] = 0;
   out_3089556940454179292[14] = 0;
   out_3089556940454179292[15] = 1;
   out_3089556940454179292[16] = 0;
   out_3089556940454179292[17] = 0;
   out_3089556940454179292[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_3089556940454179292[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_3089556940454179292[20] = 0;
   out_3089556940454179292[21] = state[8];
   out_3089556940454179292[22] = 0;
   out_3089556940454179292[23] = -state[6];
   out_3089556940454179292[24] = -state[5];
   out_3089556940454179292[25] = 0;
   out_3089556940454179292[26] = state[3];
   out_3089556940454179292[27] = 0;
   out_3089556940454179292[28] = 0;
   out_3089556940454179292[29] = 0;
   out_3089556940454179292[30] = 0;
   out_3089556940454179292[31] = 1;
   out_3089556940454179292[32] = 0;
   out_3089556940454179292[33] = 0;
   out_3089556940454179292[34] = 1;
   out_3089556940454179292[35] = 0;
   out_3089556940454179292[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_3089556940454179292[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_3089556940454179292[38] = 0;
   out_3089556940454179292[39] = -state[7];
   out_3089556940454179292[40] = state[6];
   out_3089556940454179292[41] = 0;
   out_3089556940454179292[42] = state[4];
   out_3089556940454179292[43] = -state[3];
   out_3089556940454179292[44] = 0;
   out_3089556940454179292[45] = 0;
   out_3089556940454179292[46] = 0;
   out_3089556940454179292[47] = 0;
   out_3089556940454179292[48] = 0;
   out_3089556940454179292[49] = 0;
   out_3089556940454179292[50] = 1;
   out_3089556940454179292[51] = 0;
   out_3089556940454179292[52] = 0;
   out_3089556940454179292[53] = 1;
}
void h_13(double *state, double *unused, double *out_7087737251706748874) {
   out_7087737251706748874[0] = state[3];
   out_7087737251706748874[1] = state[4];
   out_7087737251706748874[2] = state[5];
}
void H_13(double *state, double *unused, double *out_2418791220747513988) {
   out_2418791220747513988[0] = 0;
   out_2418791220747513988[1] = 0;
   out_2418791220747513988[2] = 0;
   out_2418791220747513988[3] = 1;
   out_2418791220747513988[4] = 0;
   out_2418791220747513988[5] = 0;
   out_2418791220747513988[6] = 0;
   out_2418791220747513988[7] = 0;
   out_2418791220747513988[8] = 0;
   out_2418791220747513988[9] = 0;
   out_2418791220747513988[10] = 0;
   out_2418791220747513988[11] = 0;
   out_2418791220747513988[12] = 0;
   out_2418791220747513988[13] = 0;
   out_2418791220747513988[14] = 0;
   out_2418791220747513988[15] = 0;
   out_2418791220747513988[16] = 0;
   out_2418791220747513988[17] = 0;
   out_2418791220747513988[18] = 0;
   out_2418791220747513988[19] = 0;
   out_2418791220747513988[20] = 0;
   out_2418791220747513988[21] = 0;
   out_2418791220747513988[22] = 1;
   out_2418791220747513988[23] = 0;
   out_2418791220747513988[24] = 0;
   out_2418791220747513988[25] = 0;
   out_2418791220747513988[26] = 0;
   out_2418791220747513988[27] = 0;
   out_2418791220747513988[28] = 0;
   out_2418791220747513988[29] = 0;
   out_2418791220747513988[30] = 0;
   out_2418791220747513988[31] = 0;
   out_2418791220747513988[32] = 0;
   out_2418791220747513988[33] = 0;
   out_2418791220747513988[34] = 0;
   out_2418791220747513988[35] = 0;
   out_2418791220747513988[36] = 0;
   out_2418791220747513988[37] = 0;
   out_2418791220747513988[38] = 0;
   out_2418791220747513988[39] = 0;
   out_2418791220747513988[40] = 0;
   out_2418791220747513988[41] = 1;
   out_2418791220747513988[42] = 0;
   out_2418791220747513988[43] = 0;
   out_2418791220747513988[44] = 0;
   out_2418791220747513988[45] = 0;
   out_2418791220747513988[46] = 0;
   out_2418791220747513988[47] = 0;
   out_2418791220747513988[48] = 0;
   out_2418791220747513988[49] = 0;
   out_2418791220747513988[50] = 0;
   out_2418791220747513988[51] = 0;
   out_2418791220747513988[52] = 0;
   out_2418791220747513988[53] = 0;
}
void h_14(double *state, double *unused, double *out_8542055892000654086) {
   out_8542055892000654086[0] = state[6];
   out_8542055892000654086[1] = state[7];
   out_8542055892000654086[2] = state[8];
}
void H_14(double *state, double *unused, double *out_3169758251754665716) {
   out_3169758251754665716[0] = 0;
   out_3169758251754665716[1] = 0;
   out_3169758251754665716[2] = 0;
   out_3169758251754665716[3] = 0;
   out_3169758251754665716[4] = 0;
   out_3169758251754665716[5] = 0;
   out_3169758251754665716[6] = 1;
   out_3169758251754665716[7] = 0;
   out_3169758251754665716[8] = 0;
   out_3169758251754665716[9] = 0;
   out_3169758251754665716[10] = 0;
   out_3169758251754665716[11] = 0;
   out_3169758251754665716[12] = 0;
   out_3169758251754665716[13] = 0;
   out_3169758251754665716[14] = 0;
   out_3169758251754665716[15] = 0;
   out_3169758251754665716[16] = 0;
   out_3169758251754665716[17] = 0;
   out_3169758251754665716[18] = 0;
   out_3169758251754665716[19] = 0;
   out_3169758251754665716[20] = 0;
   out_3169758251754665716[21] = 0;
   out_3169758251754665716[22] = 0;
   out_3169758251754665716[23] = 0;
   out_3169758251754665716[24] = 0;
   out_3169758251754665716[25] = 1;
   out_3169758251754665716[26] = 0;
   out_3169758251754665716[27] = 0;
   out_3169758251754665716[28] = 0;
   out_3169758251754665716[29] = 0;
   out_3169758251754665716[30] = 0;
   out_3169758251754665716[31] = 0;
   out_3169758251754665716[32] = 0;
   out_3169758251754665716[33] = 0;
   out_3169758251754665716[34] = 0;
   out_3169758251754665716[35] = 0;
   out_3169758251754665716[36] = 0;
   out_3169758251754665716[37] = 0;
   out_3169758251754665716[38] = 0;
   out_3169758251754665716[39] = 0;
   out_3169758251754665716[40] = 0;
   out_3169758251754665716[41] = 0;
   out_3169758251754665716[42] = 0;
   out_3169758251754665716[43] = 0;
   out_3169758251754665716[44] = 1;
   out_3169758251754665716[45] = 0;
   out_3169758251754665716[46] = 0;
   out_3169758251754665716[47] = 0;
   out_3169758251754665716[48] = 0;
   out_3169758251754665716[49] = 0;
   out_3169758251754665716[50] = 0;
   out_3169758251754665716[51] = 0;
   out_3169758251754665716[52] = 0;
   out_3169758251754665716[53] = 0;
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
void pose_err_fun(double *nom_x, double *delta_x, double *out_7165967535860238129) {
  err_fun(nom_x, delta_x, out_7165967535860238129);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_9032729807193459598) {
  inv_err_fun(nom_x, true_x, out_9032729807193459598);
}
void pose_H_mod_fun(double *state, double *out_5054599202167139908) {
  H_mod_fun(state, out_5054599202167139908);
}
void pose_f_fun(double *state, double dt, double *out_5000035888964044284) {
  f_fun(state,  dt, out_5000035888964044284);
}
void pose_F_fun(double *state, double dt, double *out_9018422947626896264) {
  F_fun(state,  dt, out_9018422947626896264);
}
void pose_h_4(double *state, double *unused, double *out_6773718258743003346) {
  h_4(state, unused, out_6773718258743003346);
}
void pose_H_4(double *state, double *unused, double *out_793482604584818813) {
  H_4(state, unused, out_793482604584818813);
}
void pose_h_10(double *state, double *unused, double *out_3870110240018051215) {
  h_10(state, unused, out_3870110240018051215);
}
void pose_H_10(double *state, double *unused, double *out_3089556940454179292) {
  H_10(state, unused, out_3089556940454179292);
}
void pose_h_13(double *state, double *unused, double *out_7087737251706748874) {
  h_13(state, unused, out_7087737251706748874);
}
void pose_H_13(double *state, double *unused, double *out_2418791220747513988) {
  H_13(state, unused, out_2418791220747513988);
}
void pose_h_14(double *state, double *unused, double *out_8542055892000654086) {
  h_14(state, unused, out_8542055892000654086);
}
void pose_H_14(double *state, double *unused, double *out_3169758251754665716) {
  H_14(state, unused, out_3169758251754665716);
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
