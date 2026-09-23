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
void err_fun(double *nom_x, double *delta_x, double *out_7750065176779719590) {
   out_7750065176779719590[0] = delta_x[0] + nom_x[0];
   out_7750065176779719590[1] = delta_x[1] + nom_x[1];
   out_7750065176779719590[2] = delta_x[2] + nom_x[2];
   out_7750065176779719590[3] = delta_x[3] + nom_x[3];
   out_7750065176779719590[4] = delta_x[4] + nom_x[4];
   out_7750065176779719590[5] = delta_x[5] + nom_x[5];
   out_7750065176779719590[6] = delta_x[6] + nom_x[6];
   out_7750065176779719590[7] = delta_x[7] + nom_x[7];
   out_7750065176779719590[8] = delta_x[8] + nom_x[8];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_8753902870006442752) {
   out_8753902870006442752[0] = -nom_x[0] + true_x[0];
   out_8753902870006442752[1] = -nom_x[1] + true_x[1];
   out_8753902870006442752[2] = -nom_x[2] + true_x[2];
   out_8753902870006442752[3] = -nom_x[3] + true_x[3];
   out_8753902870006442752[4] = -nom_x[4] + true_x[4];
   out_8753902870006442752[5] = -nom_x[5] + true_x[5];
   out_8753902870006442752[6] = -nom_x[6] + true_x[6];
   out_8753902870006442752[7] = -nom_x[7] + true_x[7];
   out_8753902870006442752[8] = -nom_x[8] + true_x[8];
}
void H_mod_fun(double *state, double *out_7635199098624435267) {
   out_7635199098624435267[0] = 1.0;
   out_7635199098624435267[1] = 0.0;
   out_7635199098624435267[2] = 0.0;
   out_7635199098624435267[3] = 0.0;
   out_7635199098624435267[4] = 0.0;
   out_7635199098624435267[5] = 0.0;
   out_7635199098624435267[6] = 0.0;
   out_7635199098624435267[7] = 0.0;
   out_7635199098624435267[8] = 0.0;
   out_7635199098624435267[9] = 0.0;
   out_7635199098624435267[10] = 1.0;
   out_7635199098624435267[11] = 0.0;
   out_7635199098624435267[12] = 0.0;
   out_7635199098624435267[13] = 0.0;
   out_7635199098624435267[14] = 0.0;
   out_7635199098624435267[15] = 0.0;
   out_7635199098624435267[16] = 0.0;
   out_7635199098624435267[17] = 0.0;
   out_7635199098624435267[18] = 0.0;
   out_7635199098624435267[19] = 0.0;
   out_7635199098624435267[20] = 1.0;
   out_7635199098624435267[21] = 0.0;
   out_7635199098624435267[22] = 0.0;
   out_7635199098624435267[23] = 0.0;
   out_7635199098624435267[24] = 0.0;
   out_7635199098624435267[25] = 0.0;
   out_7635199098624435267[26] = 0.0;
   out_7635199098624435267[27] = 0.0;
   out_7635199098624435267[28] = 0.0;
   out_7635199098624435267[29] = 0.0;
   out_7635199098624435267[30] = 1.0;
   out_7635199098624435267[31] = 0.0;
   out_7635199098624435267[32] = 0.0;
   out_7635199098624435267[33] = 0.0;
   out_7635199098624435267[34] = 0.0;
   out_7635199098624435267[35] = 0.0;
   out_7635199098624435267[36] = 0.0;
   out_7635199098624435267[37] = 0.0;
   out_7635199098624435267[38] = 0.0;
   out_7635199098624435267[39] = 0.0;
   out_7635199098624435267[40] = 1.0;
   out_7635199098624435267[41] = 0.0;
   out_7635199098624435267[42] = 0.0;
   out_7635199098624435267[43] = 0.0;
   out_7635199098624435267[44] = 0.0;
   out_7635199098624435267[45] = 0.0;
   out_7635199098624435267[46] = 0.0;
   out_7635199098624435267[47] = 0.0;
   out_7635199098624435267[48] = 0.0;
   out_7635199098624435267[49] = 0.0;
   out_7635199098624435267[50] = 1.0;
   out_7635199098624435267[51] = 0.0;
   out_7635199098624435267[52] = 0.0;
   out_7635199098624435267[53] = 0.0;
   out_7635199098624435267[54] = 0.0;
   out_7635199098624435267[55] = 0.0;
   out_7635199098624435267[56] = 0.0;
   out_7635199098624435267[57] = 0.0;
   out_7635199098624435267[58] = 0.0;
   out_7635199098624435267[59] = 0.0;
   out_7635199098624435267[60] = 1.0;
   out_7635199098624435267[61] = 0.0;
   out_7635199098624435267[62] = 0.0;
   out_7635199098624435267[63] = 0.0;
   out_7635199098624435267[64] = 0.0;
   out_7635199098624435267[65] = 0.0;
   out_7635199098624435267[66] = 0.0;
   out_7635199098624435267[67] = 0.0;
   out_7635199098624435267[68] = 0.0;
   out_7635199098624435267[69] = 0.0;
   out_7635199098624435267[70] = 1.0;
   out_7635199098624435267[71] = 0.0;
   out_7635199098624435267[72] = 0.0;
   out_7635199098624435267[73] = 0.0;
   out_7635199098624435267[74] = 0.0;
   out_7635199098624435267[75] = 0.0;
   out_7635199098624435267[76] = 0.0;
   out_7635199098624435267[77] = 0.0;
   out_7635199098624435267[78] = 0.0;
   out_7635199098624435267[79] = 0.0;
   out_7635199098624435267[80] = 1.0;
}
void f_fun(double *state, double dt, double *out_2250998510373555857) {
   out_2250998510373555857[0] = state[0];
   out_2250998510373555857[1] = state[1];
   out_2250998510373555857[2] = state[2];
   out_2250998510373555857[3] = state[3];
   out_2250998510373555857[4] = state[4];
   out_2250998510373555857[5] = dt*((-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]))*state[6] - 9.8100000000000005*state[8] + stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*state[1]) + (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*state[4])) + state[5];
   out_2250998510373555857[6] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*state[4])) + state[6];
   out_2250998510373555857[7] = state[7];
   out_2250998510373555857[8] = state[8];
}
void F_fun(double *state, double dt, double *out_2659791887869057736) {
   out_2659791887869057736[0] = 1;
   out_2659791887869057736[1] = 0;
   out_2659791887869057736[2] = 0;
   out_2659791887869057736[3] = 0;
   out_2659791887869057736[4] = 0;
   out_2659791887869057736[5] = 0;
   out_2659791887869057736[6] = 0;
   out_2659791887869057736[7] = 0;
   out_2659791887869057736[8] = 0;
   out_2659791887869057736[9] = 0;
   out_2659791887869057736[10] = 1;
   out_2659791887869057736[11] = 0;
   out_2659791887869057736[12] = 0;
   out_2659791887869057736[13] = 0;
   out_2659791887869057736[14] = 0;
   out_2659791887869057736[15] = 0;
   out_2659791887869057736[16] = 0;
   out_2659791887869057736[17] = 0;
   out_2659791887869057736[18] = 0;
   out_2659791887869057736[19] = 0;
   out_2659791887869057736[20] = 1;
   out_2659791887869057736[21] = 0;
   out_2659791887869057736[22] = 0;
   out_2659791887869057736[23] = 0;
   out_2659791887869057736[24] = 0;
   out_2659791887869057736[25] = 0;
   out_2659791887869057736[26] = 0;
   out_2659791887869057736[27] = 0;
   out_2659791887869057736[28] = 0;
   out_2659791887869057736[29] = 0;
   out_2659791887869057736[30] = 1;
   out_2659791887869057736[31] = 0;
   out_2659791887869057736[32] = 0;
   out_2659791887869057736[33] = 0;
   out_2659791887869057736[34] = 0;
   out_2659791887869057736[35] = 0;
   out_2659791887869057736[36] = 0;
   out_2659791887869057736[37] = 0;
   out_2659791887869057736[38] = 0;
   out_2659791887869057736[39] = 0;
   out_2659791887869057736[40] = 1;
   out_2659791887869057736[41] = 0;
   out_2659791887869057736[42] = 0;
   out_2659791887869057736[43] = 0;
   out_2659791887869057736[44] = 0;
   out_2659791887869057736[45] = dt*(stiffness_front*(-state[2] - state[3] + state[7])/(mass*state[1]) + (-stiffness_front - stiffness_rear)*state[5]/(mass*state[4]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[6]/(mass*state[4]));
   out_2659791887869057736[46] = -dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*pow(state[1], 2));
   out_2659791887869057736[47] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_2659791887869057736[48] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_2659791887869057736[49] = dt*((-1 - (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*pow(state[4], 2)))*state[6] - (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*pow(state[4], 2)));
   out_2659791887869057736[50] = dt*(-stiffness_front*state[0] - stiffness_rear*state[0])/(mass*state[4]) + 1;
   out_2659791887869057736[51] = dt*(-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]));
   out_2659791887869057736[52] = dt*stiffness_front*state[0]/(mass*state[1]);
   out_2659791887869057736[53] = -9.8100000000000005*dt;
   out_2659791887869057736[54] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front - pow(center_to_rear, 2)*stiffness_rear)*state[6]/(rotational_inertia*state[4]));
   out_2659791887869057736[55] = -center_to_front*dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*pow(state[1], 2));
   out_2659791887869057736[56] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_2659791887869057736[57] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_2659791887869057736[58] = dt*(-(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*pow(state[4], 2)) - (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*pow(state[4], 2)));
   out_2659791887869057736[59] = dt*(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(rotational_inertia*state[4]);
   out_2659791887869057736[60] = dt*(-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])/(rotational_inertia*state[4]) + 1;
   out_2659791887869057736[61] = center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_2659791887869057736[62] = 0;
   out_2659791887869057736[63] = 0;
   out_2659791887869057736[64] = 0;
   out_2659791887869057736[65] = 0;
   out_2659791887869057736[66] = 0;
   out_2659791887869057736[67] = 0;
   out_2659791887869057736[68] = 0;
   out_2659791887869057736[69] = 0;
   out_2659791887869057736[70] = 1;
   out_2659791887869057736[71] = 0;
   out_2659791887869057736[72] = 0;
   out_2659791887869057736[73] = 0;
   out_2659791887869057736[74] = 0;
   out_2659791887869057736[75] = 0;
   out_2659791887869057736[76] = 0;
   out_2659791887869057736[77] = 0;
   out_2659791887869057736[78] = 0;
   out_2659791887869057736[79] = 0;
   out_2659791887869057736[80] = 1;
}
void h_25(double *state, double *unused, double *out_4981676432707949210) {
   out_4981676432707949210[0] = state[6];
}
void H_25(double *state, double *unused, double *out_1538290732018060651) {
   out_1538290732018060651[0] = 0;
   out_1538290732018060651[1] = 0;
   out_1538290732018060651[2] = 0;
   out_1538290732018060651[3] = 0;
   out_1538290732018060651[4] = 0;
   out_1538290732018060651[5] = 0;
   out_1538290732018060651[6] = 1;
   out_1538290732018060651[7] = 0;
   out_1538290732018060651[8] = 0;
}
void h_24(double *state, double *unused, double *out_7244510398663534980) {
   out_7244510398663534980[0] = state[4];
   out_7244510398663534980[1] = state[5];
}
void H_24(double *state, double *unused, double *out_634358866987438915) {
   out_634358866987438915[0] = 0;
   out_634358866987438915[1] = 0;
   out_634358866987438915[2] = 0;
   out_634358866987438915[3] = 0;
   out_634358866987438915[4] = 1;
   out_634358866987438915[5] = 0;
   out_634358866987438915[6] = 0;
   out_634358866987438915[7] = 0;
   out_634358866987438915[8] = 0;
   out_634358866987438915[9] = 0;
   out_634358866987438915[10] = 0;
   out_634358866987438915[11] = 0;
   out_634358866987438915[12] = 0;
   out_634358866987438915[13] = 0;
   out_634358866987438915[14] = 1;
   out_634358866987438915[15] = 0;
   out_634358866987438915[16] = 0;
   out_634358866987438915[17] = 0;
}
void h_30(double *state, double *unused, double *out_4825190164283060522) {
   out_4825190164283060522[0] = state[4];
}
void H_30(double *state, double *unused, double *out_4056623690525309278) {
   out_4056623690525309278[0] = 0;
   out_4056623690525309278[1] = 0;
   out_4056623690525309278[2] = 0;
   out_4056623690525309278[3] = 0;
   out_4056623690525309278[4] = 1;
   out_4056623690525309278[5] = 0;
   out_4056623690525309278[6] = 0;
   out_4056623690525309278[7] = 0;
   out_4056623690525309278[8] = 0;
}
void h_26(double *state, double *unused, double *out_7861976215727393207) {
   out_7861976215727393207[0] = state[7];
}
void H_26(double *state, double *unused, double *out_4842816701778861252) {
   out_4842816701778861252[0] = 0;
   out_4842816701778861252[1] = 0;
   out_4842816701778861252[2] = 0;
   out_4842816701778861252[3] = 0;
   out_4842816701778861252[4] = 0;
   out_4842816701778861252[5] = 0;
   out_4842816701778861252[6] = 0;
   out_4842816701778861252[7] = 1;
   out_4842816701778861252[8] = 0;
}
void h_27(double *state, double *unused, double *out_7794228535977802593) {
   out_7794228535977802593[0] = state[3];
}
void H_27(double *state, double *unused, double *out_6280217761709252495) {
   out_6280217761709252495[0] = 0;
   out_6280217761709252495[1] = 0;
   out_6280217761709252495[2] = 0;
   out_6280217761709252495[3] = 1;
   out_6280217761709252495[4] = 0;
   out_6280217761709252495[5] = 0;
   out_6280217761709252495[6] = 0;
   out_6280217761709252495[7] = 0;
   out_6280217761709252495[8] = 0;
}
void h_29(double *state, double *unused, double *out_3881680311381398087) {
   out_3881680311381398087[0] = state[1];
}
void H_29(double *state, double *unused, double *out_4566855034839701462) {
   out_4566855034839701462[0] = 0;
   out_4566855034839701462[1] = 1;
   out_4566855034839701462[2] = 0;
   out_4566855034839701462[3] = 0;
   out_4566855034839701462[4] = 0;
   out_4566855034839701462[5] = 0;
   out_4566855034839701462[6] = 0;
   out_4566855034839701462[7] = 0;
   out_4566855034839701462[8] = 0;
}
void h_28(double *state, double *unused, double *out_2792555268316956948) {
   out_2792555268316956948[0] = state[0];
}
void H_28(double *state, double *unused, double *out_515543982229829112) {
   out_515543982229829112[0] = 1;
   out_515543982229829112[1] = 0;
   out_515543982229829112[2] = 0;
   out_515543982229829112[3] = 0;
   out_515543982229829112[4] = 0;
   out_515543982229829112[5] = 0;
   out_515543982229829112[6] = 0;
   out_515543982229829112[7] = 0;
   out_515543982229829112[8] = 0;
}
void h_31(double *state, double *unused, double *out_2703116279715418417) {
   out_2703116279715418417[0] = state[8];
}
void H_31(double *state, double *unused, double *out_4216608599545509776) {
   out_4216608599545509776[0] = 0;
   out_4216608599545509776[1] = 0;
   out_4216608599545509776[2] = 0;
   out_4216608599545509776[3] = 0;
   out_4216608599545509776[4] = 0;
   out_4216608599545509776[5] = 0;
   out_4216608599545509776[6] = 0;
   out_4216608599545509776[7] = 0;
   out_4216608599545509776[8] = 1;
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
void car_err_fun(double *nom_x, double *delta_x, double *out_7750065176779719590) {
  err_fun(nom_x, delta_x, out_7750065176779719590);
}
void car_inv_err_fun(double *nom_x, double *true_x, double *out_8753902870006442752) {
  inv_err_fun(nom_x, true_x, out_8753902870006442752);
}
void car_H_mod_fun(double *state, double *out_7635199098624435267) {
  H_mod_fun(state, out_7635199098624435267);
}
void car_f_fun(double *state, double dt, double *out_2250998510373555857) {
  f_fun(state,  dt, out_2250998510373555857);
}
void car_F_fun(double *state, double dt, double *out_2659791887869057736) {
  F_fun(state,  dt, out_2659791887869057736);
}
void car_h_25(double *state, double *unused, double *out_4981676432707949210) {
  h_25(state, unused, out_4981676432707949210);
}
void car_H_25(double *state, double *unused, double *out_1538290732018060651) {
  H_25(state, unused, out_1538290732018060651);
}
void car_h_24(double *state, double *unused, double *out_7244510398663534980) {
  h_24(state, unused, out_7244510398663534980);
}
void car_H_24(double *state, double *unused, double *out_634358866987438915) {
  H_24(state, unused, out_634358866987438915);
}
void car_h_30(double *state, double *unused, double *out_4825190164283060522) {
  h_30(state, unused, out_4825190164283060522);
}
void car_H_30(double *state, double *unused, double *out_4056623690525309278) {
  H_30(state, unused, out_4056623690525309278);
}
void car_h_26(double *state, double *unused, double *out_7861976215727393207) {
  h_26(state, unused, out_7861976215727393207);
}
void car_H_26(double *state, double *unused, double *out_4842816701778861252) {
  H_26(state, unused, out_4842816701778861252);
}
void car_h_27(double *state, double *unused, double *out_7794228535977802593) {
  h_27(state, unused, out_7794228535977802593);
}
void car_H_27(double *state, double *unused, double *out_6280217761709252495) {
  H_27(state, unused, out_6280217761709252495);
}
void car_h_29(double *state, double *unused, double *out_3881680311381398087) {
  h_29(state, unused, out_3881680311381398087);
}
void car_H_29(double *state, double *unused, double *out_4566855034839701462) {
  H_29(state, unused, out_4566855034839701462);
}
void car_h_28(double *state, double *unused, double *out_2792555268316956948) {
  h_28(state, unused, out_2792555268316956948);
}
void car_H_28(double *state, double *unused, double *out_515543982229829112) {
  H_28(state, unused, out_515543982229829112);
}
void car_h_31(double *state, double *unused, double *out_2703116279715418417) {
  h_31(state, unused, out_2703116279715418417);
}
void car_H_31(double *state, double *unused, double *out_4216608599545509776) {
  H_31(state, unused, out_4216608599545509776);
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
