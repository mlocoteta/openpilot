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
void err_fun(double *nom_x, double *delta_x, double *out_8999648935700225800) {
   out_8999648935700225800[0] = delta_x[0] + nom_x[0];
   out_8999648935700225800[1] = delta_x[1] + nom_x[1];
   out_8999648935700225800[2] = delta_x[2] + nom_x[2];
   out_8999648935700225800[3] = delta_x[3] + nom_x[3];
   out_8999648935700225800[4] = delta_x[4] + nom_x[4];
   out_8999648935700225800[5] = delta_x[5] + nom_x[5];
   out_8999648935700225800[6] = delta_x[6] + nom_x[6];
   out_8999648935700225800[7] = delta_x[7] + nom_x[7];
   out_8999648935700225800[8] = delta_x[8] + nom_x[8];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_1037891798927481552) {
   out_1037891798927481552[0] = -nom_x[0] + true_x[0];
   out_1037891798927481552[1] = -nom_x[1] + true_x[1];
   out_1037891798927481552[2] = -nom_x[2] + true_x[2];
   out_1037891798927481552[3] = -nom_x[3] + true_x[3];
   out_1037891798927481552[4] = -nom_x[4] + true_x[4];
   out_1037891798927481552[5] = -nom_x[5] + true_x[5];
   out_1037891798927481552[6] = -nom_x[6] + true_x[6];
   out_1037891798927481552[7] = -nom_x[7] + true_x[7];
   out_1037891798927481552[8] = -nom_x[8] + true_x[8];
}
void H_mod_fun(double *state, double *out_2102418200973278943) {
   out_2102418200973278943[0] = 1.0;
   out_2102418200973278943[1] = 0.0;
   out_2102418200973278943[2] = 0.0;
   out_2102418200973278943[3] = 0.0;
   out_2102418200973278943[4] = 0.0;
   out_2102418200973278943[5] = 0.0;
   out_2102418200973278943[6] = 0.0;
   out_2102418200973278943[7] = 0.0;
   out_2102418200973278943[8] = 0.0;
   out_2102418200973278943[9] = 0.0;
   out_2102418200973278943[10] = 1.0;
   out_2102418200973278943[11] = 0.0;
   out_2102418200973278943[12] = 0.0;
   out_2102418200973278943[13] = 0.0;
   out_2102418200973278943[14] = 0.0;
   out_2102418200973278943[15] = 0.0;
   out_2102418200973278943[16] = 0.0;
   out_2102418200973278943[17] = 0.0;
   out_2102418200973278943[18] = 0.0;
   out_2102418200973278943[19] = 0.0;
   out_2102418200973278943[20] = 1.0;
   out_2102418200973278943[21] = 0.0;
   out_2102418200973278943[22] = 0.0;
   out_2102418200973278943[23] = 0.0;
   out_2102418200973278943[24] = 0.0;
   out_2102418200973278943[25] = 0.0;
   out_2102418200973278943[26] = 0.0;
   out_2102418200973278943[27] = 0.0;
   out_2102418200973278943[28] = 0.0;
   out_2102418200973278943[29] = 0.0;
   out_2102418200973278943[30] = 1.0;
   out_2102418200973278943[31] = 0.0;
   out_2102418200973278943[32] = 0.0;
   out_2102418200973278943[33] = 0.0;
   out_2102418200973278943[34] = 0.0;
   out_2102418200973278943[35] = 0.0;
   out_2102418200973278943[36] = 0.0;
   out_2102418200973278943[37] = 0.0;
   out_2102418200973278943[38] = 0.0;
   out_2102418200973278943[39] = 0.0;
   out_2102418200973278943[40] = 1.0;
   out_2102418200973278943[41] = 0.0;
   out_2102418200973278943[42] = 0.0;
   out_2102418200973278943[43] = 0.0;
   out_2102418200973278943[44] = 0.0;
   out_2102418200973278943[45] = 0.0;
   out_2102418200973278943[46] = 0.0;
   out_2102418200973278943[47] = 0.0;
   out_2102418200973278943[48] = 0.0;
   out_2102418200973278943[49] = 0.0;
   out_2102418200973278943[50] = 1.0;
   out_2102418200973278943[51] = 0.0;
   out_2102418200973278943[52] = 0.0;
   out_2102418200973278943[53] = 0.0;
   out_2102418200973278943[54] = 0.0;
   out_2102418200973278943[55] = 0.0;
   out_2102418200973278943[56] = 0.0;
   out_2102418200973278943[57] = 0.0;
   out_2102418200973278943[58] = 0.0;
   out_2102418200973278943[59] = 0.0;
   out_2102418200973278943[60] = 1.0;
   out_2102418200973278943[61] = 0.0;
   out_2102418200973278943[62] = 0.0;
   out_2102418200973278943[63] = 0.0;
   out_2102418200973278943[64] = 0.0;
   out_2102418200973278943[65] = 0.0;
   out_2102418200973278943[66] = 0.0;
   out_2102418200973278943[67] = 0.0;
   out_2102418200973278943[68] = 0.0;
   out_2102418200973278943[69] = 0.0;
   out_2102418200973278943[70] = 1.0;
   out_2102418200973278943[71] = 0.0;
   out_2102418200973278943[72] = 0.0;
   out_2102418200973278943[73] = 0.0;
   out_2102418200973278943[74] = 0.0;
   out_2102418200973278943[75] = 0.0;
   out_2102418200973278943[76] = 0.0;
   out_2102418200973278943[77] = 0.0;
   out_2102418200973278943[78] = 0.0;
   out_2102418200973278943[79] = 0.0;
   out_2102418200973278943[80] = 1.0;
}
void f_fun(double *state, double dt, double *out_7837527456128700272) {
   out_7837527456128700272[0] = state[0];
   out_7837527456128700272[1] = state[1];
   out_7837527456128700272[2] = state[2];
   out_7837527456128700272[3] = state[3];
   out_7837527456128700272[4] = state[4];
   out_7837527456128700272[5] = dt*((-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]))*state[6] - 9.8100000000000005*state[8] + stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*state[1]) + (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*state[4])) + state[5];
   out_7837527456128700272[6] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*state[4])) + state[6];
   out_7837527456128700272[7] = state[7];
   out_7837527456128700272[8] = state[8];
}
void F_fun(double *state, double dt, double *out_727133835749799749) {
   out_727133835749799749[0] = 1;
   out_727133835749799749[1] = 0;
   out_727133835749799749[2] = 0;
   out_727133835749799749[3] = 0;
   out_727133835749799749[4] = 0;
   out_727133835749799749[5] = 0;
   out_727133835749799749[6] = 0;
   out_727133835749799749[7] = 0;
   out_727133835749799749[8] = 0;
   out_727133835749799749[9] = 0;
   out_727133835749799749[10] = 1;
   out_727133835749799749[11] = 0;
   out_727133835749799749[12] = 0;
   out_727133835749799749[13] = 0;
   out_727133835749799749[14] = 0;
   out_727133835749799749[15] = 0;
   out_727133835749799749[16] = 0;
   out_727133835749799749[17] = 0;
   out_727133835749799749[18] = 0;
   out_727133835749799749[19] = 0;
   out_727133835749799749[20] = 1;
   out_727133835749799749[21] = 0;
   out_727133835749799749[22] = 0;
   out_727133835749799749[23] = 0;
   out_727133835749799749[24] = 0;
   out_727133835749799749[25] = 0;
   out_727133835749799749[26] = 0;
   out_727133835749799749[27] = 0;
   out_727133835749799749[28] = 0;
   out_727133835749799749[29] = 0;
   out_727133835749799749[30] = 1;
   out_727133835749799749[31] = 0;
   out_727133835749799749[32] = 0;
   out_727133835749799749[33] = 0;
   out_727133835749799749[34] = 0;
   out_727133835749799749[35] = 0;
   out_727133835749799749[36] = 0;
   out_727133835749799749[37] = 0;
   out_727133835749799749[38] = 0;
   out_727133835749799749[39] = 0;
   out_727133835749799749[40] = 1;
   out_727133835749799749[41] = 0;
   out_727133835749799749[42] = 0;
   out_727133835749799749[43] = 0;
   out_727133835749799749[44] = 0;
   out_727133835749799749[45] = dt*(stiffness_front*(-state[2] - state[3] + state[7])/(mass*state[1]) + (-stiffness_front - stiffness_rear)*state[5]/(mass*state[4]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[6]/(mass*state[4]));
   out_727133835749799749[46] = -dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*pow(state[1], 2));
   out_727133835749799749[47] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_727133835749799749[48] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_727133835749799749[49] = dt*((-1 - (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*pow(state[4], 2)))*state[6] - (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*pow(state[4], 2)));
   out_727133835749799749[50] = dt*(-stiffness_front*state[0] - stiffness_rear*state[0])/(mass*state[4]) + 1;
   out_727133835749799749[51] = dt*(-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]));
   out_727133835749799749[52] = dt*stiffness_front*state[0]/(mass*state[1]);
   out_727133835749799749[53] = -9.8100000000000005*dt;
   out_727133835749799749[54] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front - pow(center_to_rear, 2)*stiffness_rear)*state[6]/(rotational_inertia*state[4]));
   out_727133835749799749[55] = -center_to_front*dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*pow(state[1], 2));
   out_727133835749799749[56] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_727133835749799749[57] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_727133835749799749[58] = dt*(-(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*pow(state[4], 2)) - (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*pow(state[4], 2)));
   out_727133835749799749[59] = dt*(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(rotational_inertia*state[4]);
   out_727133835749799749[60] = dt*(-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])/(rotational_inertia*state[4]) + 1;
   out_727133835749799749[61] = center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_727133835749799749[62] = 0;
   out_727133835749799749[63] = 0;
   out_727133835749799749[64] = 0;
   out_727133835749799749[65] = 0;
   out_727133835749799749[66] = 0;
   out_727133835749799749[67] = 0;
   out_727133835749799749[68] = 0;
   out_727133835749799749[69] = 0;
   out_727133835749799749[70] = 1;
   out_727133835749799749[71] = 0;
   out_727133835749799749[72] = 0;
   out_727133835749799749[73] = 0;
   out_727133835749799749[74] = 0;
   out_727133835749799749[75] = 0;
   out_727133835749799749[76] = 0;
   out_727133835749799749[77] = 0;
   out_727133835749799749[78] = 0;
   out_727133835749799749[79] = 0;
   out_727133835749799749[80] = 1;
}
void h_25(double *state, double *unused, double *out_577890879895288968) {
   out_577890879895288968[0] = state[6];
}
void H_25(double *state, double *unused, double *out_6386951471255294300) {
   out_6386951471255294300[0] = 0;
   out_6386951471255294300[1] = 0;
   out_6386951471255294300[2] = 0;
   out_6386951471255294300[3] = 0;
   out_6386951471255294300[4] = 0;
   out_6386951471255294300[5] = 0;
   out_6386951471255294300[6] = 1;
   out_6386951471255294300[7] = 0;
   out_6386951471255294300[8] = 0;
}
void h_24(double *state, double *unused, double *out_7629006599360388474) {
   out_7629006599360388474[0] = state[4];
   out_7629006599360388474[1] = state[5];
}
void H_24(double *state, double *unused, double *out_7231948080038989699) {
   out_7231948080038989699[0] = 0;
   out_7231948080038989699[1] = 0;
   out_7231948080038989699[2] = 0;
   out_7231948080038989699[3] = 0;
   out_7231948080038989699[4] = 1;
   out_7231948080038989699[5] = 0;
   out_7231948080038989699[6] = 0;
   out_7231948080038989699[7] = 0;
   out_7231948080038989699[8] = 0;
   out_7231948080038989699[9] = 0;
   out_7231948080038989699[10] = 0;
   out_7231948080038989699[11] = 0;
   out_7231948080038989699[12] = 0;
   out_7231948080038989699[13] = 0;
   out_7231948080038989699[14] = 1;
   out_7231948080038989699[15] = 0;
   out_7231948080038989699[16] = 0;
   out_7231948080038989699[17] = 0;
}
void h_30(double *state, double *unused, double *out_1619678494567612724) {
   out_1619678494567612724[0] = state[4];
}
void H_30(double *state, double *unused, double *out_8905284429762542927) {
   out_8905284429762542927[0] = 0;
   out_8905284429762542927[1] = 0;
   out_8905284429762542927[2] = 0;
   out_8905284429762542927[3] = 0;
   out_8905284429762542927[4] = 1;
   out_8905284429762542927[5] = 0;
   out_8905284429762542927[6] = 0;
   out_8905284429762542927[7] = 0;
   out_8905284429762542927[8] = 0;
}
void h_26(double *state, double *unused, double *out_2710552281154473983) {
   out_2710552281154473983[0] = state[7];
}
void H_26(double *state, double *unused, double *out_2645448152381238076) {
   out_2645448152381238076[0] = 0;
   out_2645448152381238076[1] = 0;
   out_2645448152381238076[2] = 0;
   out_2645448152381238076[3] = 0;
   out_2645448152381238076[4] = 0;
   out_2645448152381238076[5] = 0;
   out_2645448152381238076[6] = 0;
   out_2645448152381238076[7] = 1;
   out_2645448152381238076[8] = 0;
}
void h_27(double *state, double *unused, double *out_1112556954840391992) {
   out_1112556954840391992[0] = state[3];
}
void H_27(double *state, double *unused, double *out_7317865572763065472) {
   out_7317865572763065472[0] = 0;
   out_7317865572763065472[1] = 0;
   out_7317865572763065472[2] = 0;
   out_7317865572763065472[3] = 1;
   out_7317865572763065472[4] = 0;
   out_7317865572763065472[5] = 0;
   out_7317865572763065472[6] = 0;
   out_7317865572763065472[7] = 0;
   out_7317865572763065472[8] = 0;
}
void h_29(double *state, double *unused, double *out_1269743623191521137) {
   out_1269743623191521137[0] = state[1];
}
void H_29(double *state, double *unused, double *out_9031228299632616505) {
   out_9031228299632616505[0] = 0;
   out_9031228299632616505[1] = 1;
   out_9031228299632616505[2] = 0;
   out_9031228299632616505[3] = 0;
   out_9031228299632616505[4] = 0;
   out_9031228299632616505[5] = 0;
   out_9031228299632616505[6] = 0;
   out_9031228299632616505[7] = 0;
   out_9031228299632616505[8] = 0;
}
void h_28(double *state, double *unused, double *out_4149343006284724677) {
   out_4149343006284724677[0] = state[0];
}
void H_28(double *state, double *unused, double *out_4333116757007404537) {
   out_4333116757007404537[0] = 1;
   out_4333116757007404537[1] = 0;
   out_4333116757007404537[2] = 0;
   out_4333116757007404537[3] = 0;
   out_4333116757007404537[4] = 0;
   out_4333116757007404537[5] = 0;
   out_4333116757007404537[6] = 0;
   out_4333116757007404537[7] = 0;
   out_4333116757007404537[8] = 0;
}
void h_31(double *state, double *unused, double *out_656605003849113299) {
   out_656605003849113299[0] = state[8];
}
void H_31(double *state, double *unused, double *out_2019240050147886600) {
   out_2019240050147886600[0] = 0;
   out_2019240050147886600[1] = 0;
   out_2019240050147886600[2] = 0;
   out_2019240050147886600[3] = 0;
   out_2019240050147886600[4] = 0;
   out_2019240050147886600[5] = 0;
   out_2019240050147886600[6] = 0;
   out_2019240050147886600[7] = 0;
   out_2019240050147886600[8] = 1;
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
void car_err_fun(double *nom_x, double *delta_x, double *out_8999648935700225800) {
  err_fun(nom_x, delta_x, out_8999648935700225800);
}
void car_inv_err_fun(double *nom_x, double *true_x, double *out_1037891798927481552) {
  inv_err_fun(nom_x, true_x, out_1037891798927481552);
}
void car_H_mod_fun(double *state, double *out_2102418200973278943) {
  H_mod_fun(state, out_2102418200973278943);
}
void car_f_fun(double *state, double dt, double *out_7837527456128700272) {
  f_fun(state,  dt, out_7837527456128700272);
}
void car_F_fun(double *state, double dt, double *out_727133835749799749) {
  F_fun(state,  dt, out_727133835749799749);
}
void car_h_25(double *state, double *unused, double *out_577890879895288968) {
  h_25(state, unused, out_577890879895288968);
}
void car_H_25(double *state, double *unused, double *out_6386951471255294300) {
  H_25(state, unused, out_6386951471255294300);
}
void car_h_24(double *state, double *unused, double *out_7629006599360388474) {
  h_24(state, unused, out_7629006599360388474);
}
void car_H_24(double *state, double *unused, double *out_7231948080038989699) {
  H_24(state, unused, out_7231948080038989699);
}
void car_h_30(double *state, double *unused, double *out_1619678494567612724) {
  h_30(state, unused, out_1619678494567612724);
}
void car_H_30(double *state, double *unused, double *out_8905284429762542927) {
  H_30(state, unused, out_8905284429762542927);
}
void car_h_26(double *state, double *unused, double *out_2710552281154473983) {
  h_26(state, unused, out_2710552281154473983);
}
void car_H_26(double *state, double *unused, double *out_2645448152381238076) {
  H_26(state, unused, out_2645448152381238076);
}
void car_h_27(double *state, double *unused, double *out_1112556954840391992) {
  h_27(state, unused, out_1112556954840391992);
}
void car_H_27(double *state, double *unused, double *out_7317865572763065472) {
  H_27(state, unused, out_7317865572763065472);
}
void car_h_29(double *state, double *unused, double *out_1269743623191521137) {
  h_29(state, unused, out_1269743623191521137);
}
void car_H_29(double *state, double *unused, double *out_9031228299632616505) {
  H_29(state, unused, out_9031228299632616505);
}
void car_h_28(double *state, double *unused, double *out_4149343006284724677) {
  h_28(state, unused, out_4149343006284724677);
}
void car_H_28(double *state, double *unused, double *out_4333116757007404537) {
  H_28(state, unused, out_4333116757007404537);
}
void car_h_31(double *state, double *unused, double *out_656605003849113299) {
  h_31(state, unused, out_656605003849113299);
}
void car_H_31(double *state, double *unused, double *out_2019240050147886600) {
  H_31(state, unused, out_2019240050147886600);
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
