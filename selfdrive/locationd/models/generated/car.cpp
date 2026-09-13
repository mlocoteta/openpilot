#include "car.h"

namespace {
#define DIM 9
#define EDIM 9
#define MEDIM 9
typedef void (*Hfun)(double *, double *, double *);

double mass;

void set_mass(double x){ mass = x;}

double rotational_inertia;

void set_rotational_inertia(double x){ rotational_inertia = x;}

double center_to_front;

void set_center_to_front(double x){ center_to_front = x;}

double center_to_rear;

void set_center_to_rear(double x){ center_to_rear = x;}

double stiffness_front;

void set_stiffness_front(double x){ stiffness_front = x;}

double stiffness_rear;

void set_stiffness_rear(double x){ stiffness_rear = x;}
const static double MAHA_THRESH_25 = 3.8414588206941227;
const static double MAHA_THRESH_24 = 5.991464547107981;
const static double MAHA_THRESH_30 = 3.8414588206941227;
const static double MAHA_THRESH_26 = 3.8414588206941227;
const static double MAHA_THRESH_27 = 3.8414588206941227;
const static double MAHA_THRESH_29 = 3.8414588206941227;
const static double MAHA_THRESH_28 = 3.8414588206941227;
const static double MAHA_THRESH_31 = 3.8414588206941227;

/******************************************************************************
 *                      Code generated with SymPy 1.14.0                      *
 *                                                                            *
 *              See http://www.sympy.org/ for more information.               *
 *                                                                            *
 *                         This file is part of 'ekf'                         *
 ******************************************************************************/
void err_fun(double *nom_x, double *delta_x, double *out_8548372190097700555) {
   out_8548372190097700555[0] = delta_x[0] + nom_x[0];
   out_8548372190097700555[1] = delta_x[1] + nom_x[1];
   out_8548372190097700555[2] = delta_x[2] + nom_x[2];
   out_8548372190097700555[3] = delta_x[3] + nom_x[3];
   out_8548372190097700555[4] = delta_x[4] + nom_x[4];
   out_8548372190097700555[5] = delta_x[5] + nom_x[5];
   out_8548372190097700555[6] = delta_x[6] + nom_x[6];
   out_8548372190097700555[7] = delta_x[7] + nom_x[7];
   out_8548372190097700555[8] = delta_x[8] + nom_x[8];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_6257373597812199292) {
   out_6257373597812199292[0] = -nom_x[0] + true_x[0];
   out_6257373597812199292[1] = -nom_x[1] + true_x[1];
   out_6257373597812199292[2] = -nom_x[2] + true_x[2];
   out_6257373597812199292[3] = -nom_x[3] + true_x[3];
   out_6257373597812199292[4] = -nom_x[4] + true_x[4];
   out_6257373597812199292[5] = -nom_x[5] + true_x[5];
   out_6257373597812199292[6] = -nom_x[6] + true_x[6];
   out_6257373597812199292[7] = -nom_x[7] + true_x[7];
   out_6257373597812199292[8] = -nom_x[8] + true_x[8];
}
void H_mod_fun(double *state, double *out_7008429191596952258) {
   out_7008429191596952258[0] = 1.0;
   out_7008429191596952258[1] = 0.0;
   out_7008429191596952258[2] = 0.0;
   out_7008429191596952258[3] = 0.0;
   out_7008429191596952258[4] = 0.0;
   out_7008429191596952258[5] = 0.0;
   out_7008429191596952258[6] = 0.0;
   out_7008429191596952258[7] = 0.0;
   out_7008429191596952258[8] = 0.0;
   out_7008429191596952258[9] = 0.0;
   out_7008429191596952258[10] = 1.0;
   out_7008429191596952258[11] = 0.0;
   out_7008429191596952258[12] = 0.0;
   out_7008429191596952258[13] = 0.0;
   out_7008429191596952258[14] = 0.0;
   out_7008429191596952258[15] = 0.0;
   out_7008429191596952258[16] = 0.0;
   out_7008429191596952258[17] = 0.0;
   out_7008429191596952258[18] = 0.0;
   out_7008429191596952258[19] = 0.0;
   out_7008429191596952258[20] = 1.0;
   out_7008429191596952258[21] = 0.0;
   out_7008429191596952258[22] = 0.0;
   out_7008429191596952258[23] = 0.0;
   out_7008429191596952258[24] = 0.0;
   out_7008429191596952258[25] = 0.0;
   out_7008429191596952258[26] = 0.0;
   out_7008429191596952258[27] = 0.0;
   out_7008429191596952258[28] = 0.0;
   out_7008429191596952258[29] = 0.0;
   out_7008429191596952258[30] = 1.0;
   out_7008429191596952258[31] = 0.0;
   out_7008429191596952258[32] = 0.0;
   out_7008429191596952258[33] = 0.0;
   out_7008429191596952258[34] = 0.0;
   out_7008429191596952258[35] = 0.0;
   out_7008429191596952258[36] = 0.0;
   out_7008429191596952258[37] = 0.0;
   out_7008429191596952258[38] = 0.0;
   out_7008429191596952258[39] = 0.0;
   out_7008429191596952258[40] = 1.0;
   out_7008429191596952258[41] = 0.0;
   out_7008429191596952258[42] = 0.0;
   out_7008429191596952258[43] = 0.0;
   out_7008429191596952258[44] = 0.0;
   out_7008429191596952258[45] = 0.0;
   out_7008429191596952258[46] = 0.0;
   out_7008429191596952258[47] = 0.0;
   out_7008429191596952258[48] = 0.0;
   out_7008429191596952258[49] = 0.0;
   out_7008429191596952258[50] = 1.0;
   out_7008429191596952258[51] = 0.0;
   out_7008429191596952258[52] = 0.0;
   out_7008429191596952258[53] = 0.0;
   out_7008429191596952258[54] = 0.0;
   out_7008429191596952258[55] = 0.0;
   out_7008429191596952258[56] = 0.0;
   out_7008429191596952258[57] = 0.0;
   out_7008429191596952258[58] = 0.0;
   out_7008429191596952258[59] = 0.0;
   out_7008429191596952258[60] = 1.0;
   out_7008429191596952258[61] = 0.0;
   out_7008429191596952258[62] = 0.0;
   out_7008429191596952258[63] = 0.0;
   out_7008429191596952258[64] = 0.0;
   out_7008429191596952258[65] = 0.0;
   out_7008429191596952258[66] = 0.0;
   out_7008429191596952258[67] = 0.0;
   out_7008429191596952258[68] = 0.0;
   out_7008429191596952258[69] = 0.0;
   out_7008429191596952258[70] = 1.0;
   out_7008429191596952258[71] = 0.0;
   out_7008429191596952258[72] = 0.0;
   out_7008429191596952258[73] = 0.0;
   out_7008429191596952258[74] = 0.0;
   out_7008429191596952258[75] = 0.0;
   out_7008429191596952258[76] = 0.0;
   out_7008429191596952258[77] = 0.0;
   out_7008429191596952258[78] = 0.0;
   out_7008429191596952258[79] = 0.0;
   out_7008429191596952258[80] = 1.0;
}
void f_fun(double *state, double dt, double *out_211764458208077354) {
   out_211764458208077354[0] = state[0];
   out_211764458208077354[1] = state[1];
   out_211764458208077354[2] = state[2];
   out_211764458208077354[3] = state[3];
   out_211764458208077354[4] = state[4];
   out_211764458208077354[5] = dt*((-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]))*state[6] - 9.8100000000000005*state[8] + stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*state[1]) + (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*state[4])) + state[5];
   out_211764458208077354[6] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*state[4])) + state[6];
   out_211764458208077354[7] = state[7];
   out_211764458208077354[8] = state[8];
}
void F_fun(double *state, double dt, double *out_6789911951967766610) {
   out_6789911951967766610[0] = 1;
   out_6789911951967766610[1] = 0;
   out_6789911951967766610[2] = 0;
   out_6789911951967766610[3] = 0;
   out_6789911951967766610[4] = 0;
   out_6789911951967766610[5] = 0;
   out_6789911951967766610[6] = 0;
   out_6789911951967766610[7] = 0;
   out_6789911951967766610[8] = 0;
   out_6789911951967766610[9] = 0;
   out_6789911951967766610[10] = 1;
   out_6789911951967766610[11] = 0;
   out_6789911951967766610[12] = 0;
   out_6789911951967766610[13] = 0;
   out_6789911951967766610[14] = 0;
   out_6789911951967766610[15] = 0;
   out_6789911951967766610[16] = 0;
   out_6789911951967766610[17] = 0;
   out_6789911951967766610[18] = 0;
   out_6789911951967766610[19] = 0;
   out_6789911951967766610[20] = 1;
   out_6789911951967766610[21] = 0;
   out_6789911951967766610[22] = 0;
   out_6789911951967766610[23] = 0;
   out_6789911951967766610[24] = 0;
   out_6789911951967766610[25] = 0;
   out_6789911951967766610[26] = 0;
   out_6789911951967766610[27] = 0;
   out_6789911951967766610[28] = 0;
   out_6789911951967766610[29] = 0;
   out_6789911951967766610[30] = 1;
   out_6789911951967766610[31] = 0;
   out_6789911951967766610[32] = 0;
   out_6789911951967766610[33] = 0;
   out_6789911951967766610[34] = 0;
   out_6789911951967766610[35] = 0;
   out_6789911951967766610[36] = 0;
   out_6789911951967766610[37] = 0;
   out_6789911951967766610[38] = 0;
   out_6789911951967766610[39] = 0;
   out_6789911951967766610[40] = 1;
   out_6789911951967766610[41] = 0;
   out_6789911951967766610[42] = 0;
   out_6789911951967766610[43] = 0;
   out_6789911951967766610[44] = 0;
   out_6789911951967766610[45] = dt*(stiffness_front*(-state[2] - state[3] + state[7])/(mass*state[1]) + (-stiffness_front - stiffness_rear)*state[5]/(mass*state[4]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[6]/(mass*state[4]));
   out_6789911951967766610[46] = -dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*pow(state[1], 2));
   out_6789911951967766610[47] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_6789911951967766610[48] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_6789911951967766610[49] = dt*((-1 - (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*pow(state[4], 2)))*state[6] - (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*pow(state[4], 2)));
   out_6789911951967766610[50] = dt*(-stiffness_front*state[0] - stiffness_rear*state[0])/(mass*state[4]) + 1;
   out_6789911951967766610[51] = dt*(-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]));
   out_6789911951967766610[52] = dt*stiffness_front*state[0]/(mass*state[1]);
   out_6789911951967766610[53] = -9.8100000000000005*dt;
   out_6789911951967766610[54] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front - pow(center_to_rear, 2)*stiffness_rear)*state[6]/(rotational_inertia*state[4]));
   out_6789911951967766610[55] = -center_to_front*dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*pow(state[1], 2));
   out_6789911951967766610[56] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_6789911951967766610[57] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_6789911951967766610[58] = dt*(-(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*pow(state[4], 2)) - (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*pow(state[4], 2)));
   out_6789911951967766610[59] = dt*(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(rotational_inertia*state[4]);
   out_6789911951967766610[60] = dt*(-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])/(rotational_inertia*state[4]) + 1;
   out_6789911951967766610[61] = center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_6789911951967766610[62] = 0;
   out_6789911951967766610[63] = 0;
   out_6789911951967766610[64] = 0;
   out_6789911951967766610[65] = 0;
   out_6789911951967766610[66] = 0;
   out_6789911951967766610[67] = 0;
   out_6789911951967766610[68] = 0;
   out_6789911951967766610[69] = 0;
   out_6789911951967766610[70] = 1;
   out_6789911951967766610[71] = 0;
   out_6789911951967766610[72] = 0;
   out_6789911951967766610[73] = 0;
   out_6789911951967766610[74] = 0;
   out_6789911951967766610[75] = 0;
   out_6789911951967766610[76] = 0;
   out_6789911951967766610[77] = 0;
   out_6789911951967766610[78] = 0;
   out_6789911951967766610[79] = 0;
   out_6789911951967766610[80] = 1;
}
void h_25(double *state, double *unused, double *out_7956251239264178232) {
   out_7956251239264178232[0] = state[6];
}
void H_25(double *state, double *unused, double *out_912908841376907547) {
   out_912908841376907547[0] = 0;
   out_912908841376907547[1] = 0;
   out_912908841376907547[2] = 0;
   out_912908841376907547[3] = 0;
   out_912908841376907547[4] = 0;
   out_912908841376907547[5] = 0;
   out_912908841376907547[6] = 1;
   out_912908841376907547[7] = 0;
   out_912908841376907547[8] = 0;
}
void h_24(double *state, double *unused, double *out_7723154835838931558) {
   out_7723154835838931558[0] = state[4];
   out_7723154835838931558[1] = state[5];
}
void H_24(double *state, double *unused, double *out_2501382670766146913) {
   out_2501382670766146913[0] = 0;
   out_2501382670766146913[1] = 0;
   out_2501382670766146913[2] = 0;
   out_2501382670766146913[3] = 0;
   out_2501382670766146913[4] = 1;
   out_2501382670766146913[5] = 0;
   out_2501382670766146913[6] = 0;
   out_2501382670766146913[7] = 0;
   out_2501382670766146913[8] = 0;
   out_2501382670766146913[9] = 0;
   out_2501382670766146913[10] = 0;
   out_2501382670766146913[11] = 0;
   out_2501382670766146913[12] = 0;
   out_2501382670766146913[13] = 0;
   out_2501382670766146913[14] = 1;
   out_2501382670766146913[15] = 0;
   out_2501382670766146913[16] = 0;
   out_2501382670766146913[17] = 0;
}
void h_30(double *state, double *unused, double *out_4094567762835676580) {
   out_4094567762835676580[0] = state[4];
}
void H_30(double *state, double *unused, double *out_3614787488750700651) {
   out_3614787488750700651[0] = 0;
   out_3614787488750700651[1] = 0;
   out_3614787488750700651[2] = 0;
   out_3614787488750700651[3] = 0;
   out_3614787488750700651[4] = 1;
   out_3614787488750700651[5] = 0;
   out_3614787488750700651[6] = 0;
   out_3614787488750700651[7] = 0;
   out_3614787488750700651[8] = 0;
}
void h_26(double *state, double *unused, double *out_4086855108634070771) {
   out_4086855108634070771[0] = state[7];
}
void H_26(double *state, double *unused, double *out_2828594477497148677) {
   out_2828594477497148677[0] = 0;
   out_2828594477497148677[1] = 0;
   out_2828594477497148677[2] = 0;
   out_2828594477497148677[3] = 0;
   out_2828594477497148677[4] = 0;
   out_2828594477497148677[5] = 0;
   out_2828594477497148677[6] = 0;
   out_2828594477497148677[7] = 1;
   out_2828594477497148677[8] = 0;
}
void h_27(double *state, double *unused, double *out_3279583348191151873) {
   out_3279583348191151873[0] = state[3];
}
void H_27(double *state, double *unused, double *out_5789550800551125562) {
   out_5789550800551125562[0] = 0;
   out_5789550800551125562[1] = 0;
   out_5789550800551125562[2] = 0;
   out_5789550800551125562[3] = 1;
   out_5789550800551125562[4] = 0;
   out_5789550800551125562[5] = 0;
   out_5789550800551125562[6] = 0;
   out_5789550800551125562[7] = 0;
   out_5789550800551125562[8] = 0;
}
void h_29(double *state, double *unused, double *out_3491251878159199063) {
   out_3491251878159199063[0] = state[1];
}
void H_29(double *state, double *unused, double *out_3104556144436308467) {
   out_3104556144436308467[0] = 0;
   out_3104556144436308467[1] = 1;
   out_3104556144436308467[2] = 0;
   out_3104556144436308467[3] = 0;
   out_3104556144436308467[4] = 0;
   out_3104556144436308467[5] = 0;
   out_3104556144436308467[6] = 0;
   out_3104556144436308467[7] = 0;
   out_3104556144436308467[8] = 0;
}
void h_28(double *state, double *unused, double *out_2111839547115010136) {
   out_2111839547115010136[0] = state[0];
}
void H_28(double *state, double *unused, double *out_1140925872870982216) {
   out_1140925872870982216[0] = 1;
   out_1140925872870982216[1] = 0;
   out_1140925872870982216[2] = 0;
   out_1140925872870982216[3] = 0;
   out_1140925872870982216[4] = 0;
   out_1140925872870982216[5] = 0;
   out_1140925872870982216[6] = 0;
   out_1140925872870982216[7] = 0;
   out_1140925872870982216[8] = 0;
}
void h_31(double *state, double *unused, double *out_271458526840810605) {
   out_271458526840810605[0] = state[8];
}
void H_31(double *state, double *unused, double *out_3454802579730500153) {
   out_3454802579730500153[0] = 0;
   out_3454802579730500153[1] = 0;
   out_3454802579730500153[2] = 0;
   out_3454802579730500153[3] = 0;
   out_3454802579730500153[4] = 0;
   out_3454802579730500153[5] = 0;
   out_3454802579730500153[6] = 0;
   out_3454802579730500153[7] = 0;
   out_3454802579730500153[8] = 1;
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

void car_update_25(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_25, H_25, NULL, in_z, in_R, in_ea, MAHA_THRESH_25);
}
void car_update_24(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<2, 3, 0>(in_x, in_P, h_24, H_24, NULL, in_z, in_R, in_ea, MAHA_THRESH_24);
}
void car_update_30(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_30, H_30, NULL, in_z, in_R, in_ea, MAHA_THRESH_30);
}
void car_update_26(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_26, H_26, NULL, in_z, in_R, in_ea, MAHA_THRESH_26);
}
void car_update_27(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_27, H_27, NULL, in_z, in_R, in_ea, MAHA_THRESH_27);
}
void car_update_29(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_29, H_29, NULL, in_z, in_R, in_ea, MAHA_THRESH_29);
}
void car_update_28(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_28, H_28, NULL, in_z, in_R, in_ea, MAHA_THRESH_28);
}
void car_update_31(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_31, H_31, NULL, in_z, in_R, in_ea, MAHA_THRESH_31);
}
void car_err_fun(double *nom_x, double *delta_x, double *out_8548372190097700555) {
  err_fun(nom_x, delta_x, out_8548372190097700555);
}
void car_inv_err_fun(double *nom_x, double *true_x, double *out_6257373597812199292) {
  inv_err_fun(nom_x, true_x, out_6257373597812199292);
}
void car_H_mod_fun(double *state, double *out_7008429191596952258) {
  H_mod_fun(state, out_7008429191596952258);
}
void car_f_fun(double *state, double dt, double *out_211764458208077354) {
  f_fun(state,  dt, out_211764458208077354);
}
void car_F_fun(double *state, double dt, double *out_6789911951967766610) {
  F_fun(state,  dt, out_6789911951967766610);
}
void car_h_25(double *state, double *unused, double *out_7956251239264178232) {
  h_25(state, unused, out_7956251239264178232);
}
void car_H_25(double *state, double *unused, double *out_912908841376907547) {
  H_25(state, unused, out_912908841376907547);
}
void car_h_24(double *state, double *unused, double *out_7723154835838931558) {
  h_24(state, unused, out_7723154835838931558);
}
void car_H_24(double *state, double *unused, double *out_2501382670766146913) {
  H_24(state, unused, out_2501382670766146913);
}
void car_h_30(double *state, double *unused, double *out_4094567762835676580) {
  h_30(state, unused, out_4094567762835676580);
}
void car_H_30(double *state, double *unused, double *out_3614787488750700651) {
  H_30(state, unused, out_3614787488750700651);
}
void car_h_26(double *state, double *unused, double *out_4086855108634070771) {
  h_26(state, unused, out_4086855108634070771);
}
void car_H_26(double *state, double *unused, double *out_2828594477497148677) {
  H_26(state, unused, out_2828594477497148677);
}
void car_h_27(double *state, double *unused, double *out_3279583348191151873) {
  h_27(state, unused, out_3279583348191151873);
}
void car_H_27(double *state, double *unused, double *out_5789550800551125562) {
  H_27(state, unused, out_5789550800551125562);
}
void car_h_29(double *state, double *unused, double *out_3491251878159199063) {
  h_29(state, unused, out_3491251878159199063);
}
void car_H_29(double *state, double *unused, double *out_3104556144436308467) {
  H_29(state, unused, out_3104556144436308467);
}
void car_h_28(double *state, double *unused, double *out_2111839547115010136) {
  h_28(state, unused, out_2111839547115010136);
}
void car_H_28(double *state, double *unused, double *out_1140925872870982216) {
  H_28(state, unused, out_1140925872870982216);
}
void car_h_31(double *state, double *unused, double *out_271458526840810605) {
  h_31(state, unused, out_271458526840810605);
}
void car_H_31(double *state, double *unused, double *out_3454802579730500153) {
  H_31(state, unused, out_3454802579730500153);
}
void car_predict(double *in_x, double *in_P, double *in_Q, double dt) {
  predict(in_x, in_P, in_Q, dt);
}
void car_set_mass(double x) {
  set_mass(x);
}
void car_set_rotational_inertia(double x) {
  set_rotational_inertia(x);
}
void car_set_center_to_front(double x) {
  set_center_to_front(x);
}
void car_set_center_to_rear(double x) {
  set_center_to_rear(x);
}
void car_set_stiffness_front(double x) {
  set_stiffness_front(x);
}
void car_set_stiffness_rear(double x) {
  set_stiffness_rear(x);
}
}

const EKF car = {
  .name = "car",
  .kinds = { 25, 24, 30, 26, 27, 29, 28, 31 },
  .feature_kinds = {  },
  .f_fun = car_f_fun,
  .F_fun = car_F_fun,
  .err_fun = car_err_fun,
  .inv_err_fun = car_inv_err_fun,
  .H_mod_fun = car_H_mod_fun,
  .predict = car_predict,
  .hs = {
    { 25, car_h_25 },
    { 24, car_h_24 },
    { 30, car_h_30 },
    { 26, car_h_26 },
    { 27, car_h_27 },
    { 29, car_h_29 },
    { 28, car_h_28 },
    { 31, car_h_31 },
  },
  .Hs = {
    { 25, car_H_25 },
    { 24, car_H_24 },
    { 30, car_H_30 },
    { 26, car_H_26 },
    { 27, car_H_27 },
    { 29, car_H_29 },
    { 28, car_H_28 },
    { 31, car_H_31 },
  },
  .updates = {
    { 25, car_update_25 },
    { 24, car_update_24 },
    { 30, car_update_30 },
    { 26, car_update_26 },
    { 27, car_update_27 },
    { 29, car_update_29 },
    { 28, car_update_28 },
    { 31, car_update_31 },
  },
  .Hes = {
  },
  .sets = {
    { "mass", car_set_mass },
    { "rotational_inertia", car_set_rotational_inertia },
    { "center_to_front", car_set_center_to_front },
    { "center_to_rear", car_set_center_to_rear },
    { "stiffness_front", car_set_stiffness_front },
    { "stiffness_rear", car_set_stiffness_rear },
  },
  .extra_routines = {
  },
};

ekf_lib_init(car)
