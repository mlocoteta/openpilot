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
void err_fun(double *nom_x, double *delta_x, double *out_5579271098234299589) {
   out_5579271098234299589[0] = delta_x[0] + nom_x[0];
   out_5579271098234299589[1] = delta_x[1] + nom_x[1];
   out_5579271098234299589[2] = delta_x[2] + nom_x[2];
   out_5579271098234299589[3] = delta_x[3] + nom_x[3];
   out_5579271098234299589[4] = delta_x[4] + nom_x[4];
   out_5579271098234299589[5] = delta_x[5] + nom_x[5];
   out_5579271098234299589[6] = delta_x[6] + nom_x[6];
   out_5579271098234299589[7] = delta_x[7] + nom_x[7];
   out_5579271098234299589[8] = delta_x[8] + nom_x[8];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_8879118943542071452) {
   out_8879118943542071452[0] = -nom_x[0] + true_x[0];
   out_8879118943542071452[1] = -nom_x[1] + true_x[1];
   out_8879118943542071452[2] = -nom_x[2] + true_x[2];
   out_8879118943542071452[3] = -nom_x[3] + true_x[3];
   out_8879118943542071452[4] = -nom_x[4] + true_x[4];
   out_8879118943542071452[5] = -nom_x[5] + true_x[5];
   out_8879118943542071452[6] = -nom_x[6] + true_x[6];
   out_8879118943542071452[7] = -nom_x[7] + true_x[7];
   out_8879118943542071452[8] = -nom_x[8] + true_x[8];
}
void H_mod_fun(double *state, double *out_4346759063564356553) {
   out_4346759063564356553[0] = 1.0;
   out_4346759063564356553[1] = 0.0;
   out_4346759063564356553[2] = 0.0;
   out_4346759063564356553[3] = 0.0;
   out_4346759063564356553[4] = 0.0;
   out_4346759063564356553[5] = 0.0;
   out_4346759063564356553[6] = 0.0;
   out_4346759063564356553[7] = 0.0;
   out_4346759063564356553[8] = 0.0;
   out_4346759063564356553[9] = 0.0;
   out_4346759063564356553[10] = 1.0;
   out_4346759063564356553[11] = 0.0;
   out_4346759063564356553[12] = 0.0;
   out_4346759063564356553[13] = 0.0;
   out_4346759063564356553[14] = 0.0;
   out_4346759063564356553[15] = 0.0;
   out_4346759063564356553[16] = 0.0;
   out_4346759063564356553[17] = 0.0;
   out_4346759063564356553[18] = 0.0;
   out_4346759063564356553[19] = 0.0;
   out_4346759063564356553[20] = 1.0;
   out_4346759063564356553[21] = 0.0;
   out_4346759063564356553[22] = 0.0;
   out_4346759063564356553[23] = 0.0;
   out_4346759063564356553[24] = 0.0;
   out_4346759063564356553[25] = 0.0;
   out_4346759063564356553[26] = 0.0;
   out_4346759063564356553[27] = 0.0;
   out_4346759063564356553[28] = 0.0;
   out_4346759063564356553[29] = 0.0;
   out_4346759063564356553[30] = 1.0;
   out_4346759063564356553[31] = 0.0;
   out_4346759063564356553[32] = 0.0;
   out_4346759063564356553[33] = 0.0;
   out_4346759063564356553[34] = 0.0;
   out_4346759063564356553[35] = 0.0;
   out_4346759063564356553[36] = 0.0;
   out_4346759063564356553[37] = 0.0;
   out_4346759063564356553[38] = 0.0;
   out_4346759063564356553[39] = 0.0;
   out_4346759063564356553[40] = 1.0;
   out_4346759063564356553[41] = 0.0;
   out_4346759063564356553[42] = 0.0;
   out_4346759063564356553[43] = 0.0;
   out_4346759063564356553[44] = 0.0;
   out_4346759063564356553[45] = 0.0;
   out_4346759063564356553[46] = 0.0;
   out_4346759063564356553[47] = 0.0;
   out_4346759063564356553[48] = 0.0;
   out_4346759063564356553[49] = 0.0;
   out_4346759063564356553[50] = 1.0;
   out_4346759063564356553[51] = 0.0;
   out_4346759063564356553[52] = 0.0;
   out_4346759063564356553[53] = 0.0;
   out_4346759063564356553[54] = 0.0;
   out_4346759063564356553[55] = 0.0;
   out_4346759063564356553[56] = 0.0;
   out_4346759063564356553[57] = 0.0;
   out_4346759063564356553[58] = 0.0;
   out_4346759063564356553[59] = 0.0;
   out_4346759063564356553[60] = 1.0;
   out_4346759063564356553[61] = 0.0;
   out_4346759063564356553[62] = 0.0;
   out_4346759063564356553[63] = 0.0;
   out_4346759063564356553[64] = 0.0;
   out_4346759063564356553[65] = 0.0;
   out_4346759063564356553[66] = 0.0;
   out_4346759063564356553[67] = 0.0;
   out_4346759063564356553[68] = 0.0;
   out_4346759063564356553[69] = 0.0;
   out_4346759063564356553[70] = 1.0;
   out_4346759063564356553[71] = 0.0;
   out_4346759063564356553[72] = 0.0;
   out_4346759063564356553[73] = 0.0;
   out_4346759063564356553[74] = 0.0;
   out_4346759063564356553[75] = 0.0;
   out_4346759063564356553[76] = 0.0;
   out_4346759063564356553[77] = 0.0;
   out_4346759063564356553[78] = 0.0;
   out_4346759063564356553[79] = 0.0;
   out_4346759063564356553[80] = 1.0;
}
void f_fun(double *state, double dt, double *out_8401415236153157083) {
   out_8401415236153157083[0] = state[0];
   out_8401415236153157083[1] = state[1];
   out_8401415236153157083[2] = state[2];
   out_8401415236153157083[3] = state[3];
   out_8401415236153157083[4] = state[4];
   out_8401415236153157083[5] = dt*((-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]))*state[6] - 9.8100000000000005*state[8] + stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*state[1]) + (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*state[4])) + state[5];
   out_8401415236153157083[6] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*state[4])) + state[6];
   out_8401415236153157083[7] = state[7];
   out_8401415236153157083[8] = state[8];
}
void F_fun(double *state, double dt, double *out_1973239055632703499) {
   out_1973239055632703499[0] = 1;
   out_1973239055632703499[1] = 0;
   out_1973239055632703499[2] = 0;
   out_1973239055632703499[3] = 0;
   out_1973239055632703499[4] = 0;
   out_1973239055632703499[5] = 0;
   out_1973239055632703499[6] = 0;
   out_1973239055632703499[7] = 0;
   out_1973239055632703499[8] = 0;
   out_1973239055632703499[9] = 0;
   out_1973239055632703499[10] = 1;
   out_1973239055632703499[11] = 0;
   out_1973239055632703499[12] = 0;
   out_1973239055632703499[13] = 0;
   out_1973239055632703499[14] = 0;
   out_1973239055632703499[15] = 0;
   out_1973239055632703499[16] = 0;
   out_1973239055632703499[17] = 0;
   out_1973239055632703499[18] = 0;
   out_1973239055632703499[19] = 0;
   out_1973239055632703499[20] = 1;
   out_1973239055632703499[21] = 0;
   out_1973239055632703499[22] = 0;
   out_1973239055632703499[23] = 0;
   out_1973239055632703499[24] = 0;
   out_1973239055632703499[25] = 0;
   out_1973239055632703499[26] = 0;
   out_1973239055632703499[27] = 0;
   out_1973239055632703499[28] = 0;
   out_1973239055632703499[29] = 0;
   out_1973239055632703499[30] = 1;
   out_1973239055632703499[31] = 0;
   out_1973239055632703499[32] = 0;
   out_1973239055632703499[33] = 0;
   out_1973239055632703499[34] = 0;
   out_1973239055632703499[35] = 0;
   out_1973239055632703499[36] = 0;
   out_1973239055632703499[37] = 0;
   out_1973239055632703499[38] = 0;
   out_1973239055632703499[39] = 0;
   out_1973239055632703499[40] = 1;
   out_1973239055632703499[41] = 0;
   out_1973239055632703499[42] = 0;
   out_1973239055632703499[43] = 0;
   out_1973239055632703499[44] = 0;
   out_1973239055632703499[45] = dt*(stiffness_front*(-state[2] - state[3] + state[7])/(mass*state[1]) + (-stiffness_front - stiffness_rear)*state[5]/(mass*state[4]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[6]/(mass*state[4]));
   out_1973239055632703499[46] = -dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*pow(state[1], 2));
   out_1973239055632703499[47] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_1973239055632703499[48] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_1973239055632703499[49] = dt*((-1 - (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*pow(state[4], 2)))*state[6] - (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*pow(state[4], 2)));
   out_1973239055632703499[50] = dt*(-stiffness_front*state[0] - stiffness_rear*state[0])/(mass*state[4]) + 1;
   out_1973239055632703499[51] = dt*(-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]));
   out_1973239055632703499[52] = dt*stiffness_front*state[0]/(mass*state[1]);
   out_1973239055632703499[53] = -9.8100000000000005*dt;
   out_1973239055632703499[54] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front - pow(center_to_rear, 2)*stiffness_rear)*state[6]/(rotational_inertia*state[4]));
   out_1973239055632703499[55] = -center_to_front*dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*pow(state[1], 2));
   out_1973239055632703499[56] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_1973239055632703499[57] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_1973239055632703499[58] = dt*(-(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*pow(state[4], 2)) - (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*pow(state[4], 2)));
   out_1973239055632703499[59] = dt*(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(rotational_inertia*state[4]);
   out_1973239055632703499[60] = dt*(-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])/(rotational_inertia*state[4]) + 1;
   out_1973239055632703499[61] = center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_1973239055632703499[62] = 0;
   out_1973239055632703499[63] = 0;
   out_1973239055632703499[64] = 0;
   out_1973239055632703499[65] = 0;
   out_1973239055632703499[66] = 0;
   out_1973239055632703499[67] = 0;
   out_1973239055632703499[68] = 0;
   out_1973239055632703499[69] = 0;
   out_1973239055632703499[70] = 1;
   out_1973239055632703499[71] = 0;
   out_1973239055632703499[72] = 0;
   out_1973239055632703499[73] = 0;
   out_1973239055632703499[74] = 0;
   out_1973239055632703499[75] = 0;
   out_1973239055632703499[76] = 0;
   out_1973239055632703499[77] = 0;
   out_1973239055632703499[78] = 0;
   out_1973239055632703499[79] = 0;
   out_1973239055632703499[80] = 1;
}
void h_25(double *state, double *unused, double *out_7709444436246576106) {
   out_7709444436246576106[0] = state[6];
}
void H_25(double *state, double *unused, double *out_4906796784232957826) {
   out_4906796784232957826[0] = 0;
   out_4906796784232957826[1] = 0;
   out_4906796784232957826[2] = 0;
   out_4906796784232957826[3] = 0;
   out_4906796784232957826[4] = 0;
   out_4906796784232957826[5] = 0;
   out_4906796784232957826[6] = 1;
   out_4906796784232957826[7] = 0;
   out_4906796784232957826[8] = 0;
}
void h_24(double *state, double *unused, double *out_8161953024412082811) {
   out_8161953024412082811[0] = state[4];
   out_8161953024412082811[1] = state[5];
}
void H_24(double *state, double *unused, double *out_6319825032271366663) {
   out_6319825032271366663[0] = 0;
   out_6319825032271366663[1] = 0;
   out_6319825032271366663[2] = 0;
   out_6319825032271366663[3] = 0;
   out_6319825032271366663[4] = 1;
   out_6319825032271366663[5] = 0;
   out_6319825032271366663[6] = 0;
   out_6319825032271366663[7] = 0;
   out_6319825032271366663[8] = 0;
   out_6319825032271366663[9] = 0;
   out_6319825032271366663[10] = 0;
   out_6319825032271366663[11] = 0;
   out_6319825032271366663[12] = 0;
   out_6319825032271366663[13] = 0;
   out_6319825032271366663[14] = 1;
   out_6319825032271366663[15] = 0;
   out_6319825032271366663[16] = 0;
   out_6319825032271366663[17] = 0;
}
void h_30(double *state, double *unused, double *out_8890419815179839294) {
   out_8890419815179839294[0] = state[4];
}
void H_30(double *state, double *unused, double *out_7425129742740206453) {
   out_7425129742740206453[0] = 0;
   out_7425129742740206453[1] = 0;
   out_7425129742740206453[2] = 0;
   out_7425129742740206453[3] = 0;
   out_7425129742740206453[4] = 1;
   out_7425129742740206453[5] = 0;
   out_7425129742740206453[6] = 0;
   out_7425129742740206453[7] = 0;
   out_7425129742740206453[8] = 0;
}
void h_26(double *state, double *unused, double *out_8798474113368893512) {
   out_8798474113368893512[0] = state[7];
}
void H_26(double *state, double *unused, double *out_1165293465358901602) {
   out_1165293465358901602[0] = 0;
   out_1165293465358901602[1] = 0;
   out_1165293465358901602[2] = 0;
   out_1165293465358901602[3] = 0;
   out_1165293465358901602[4] = 0;
   out_1165293465358901602[5] = 0;
   out_1165293465358901602[6] = 0;
   out_1165293465358901602[7] = 1;
   out_1165293465358901602[8] = 0;
}
void h_27(double *state, double *unused, double *out_4672658384802243421) {
   out_4672658384802243421[0] = state[3];
}
void H_27(double *state, double *unused, double *out_8798020259785401946) {
   out_8798020259785401946[0] = 0;
   out_8798020259785401946[1] = 0;
   out_8798020259785401946[2] = 0;
   out_8798020259785401946[3] = 1;
   out_8798020259785401946[4] = 0;
   out_8798020259785401946[5] = 0;
   out_8798020259785401946[6] = 0;
   out_8798020259785401946[7] = 0;
   out_8798020259785401946[8] = 0;
}
void h_29(double *state, double *unused, double *out_4214457022643681759) {
   out_4214457022643681759[0] = state[1];
}
void H_29(double *state, double *unused, double *out_7935361087054598637) {
   out_7935361087054598637[0] = 0;
   out_7935361087054598637[1] = 1;
   out_7935361087054598637[2] = 0;
   out_7935361087054598637[3] = 0;
   out_7935361087054598637[4] = 0;
   out_7935361087054598637[5] = 0;
   out_7935361087054598637[6] = 0;
   out_7935361087054598637[7] = 0;
   out_7935361087054598637[8] = 0;
}
void h_28(double *state, double *unused, double *out_8772412421246462550) {
   out_8772412421246462550[0] = state[0];
}
void H_28(double *state, double *unused, double *out_2852962069985068063) {
   out_2852962069985068063[0] = 1;
   out_2852962069985068063[1] = 0;
   out_2852962069985068063[2] = 0;
   out_2852962069985068063[3] = 0;
   out_2852962069985068063[4] = 0;
   out_2852962069985068063[5] = 0;
   out_2852962069985068063[6] = 0;
   out_2852962069985068063[7] = 0;
   out_2852962069985068063[8] = 0;
}
void h_31(double *state, double *unused, double *out_7434250373962070217) {
   out_7434250373962070217[0] = state[8];
}
void H_31(double *state, double *unused, double *out_539085363125550126) {
   out_539085363125550126[0] = 0;
   out_539085363125550126[1] = 0;
   out_539085363125550126[2] = 0;
   out_539085363125550126[3] = 0;
   out_539085363125550126[4] = 0;
   out_539085363125550126[5] = 0;
   out_539085363125550126[6] = 0;
   out_539085363125550126[7] = 0;
   out_539085363125550126[8] = 1;
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
void car_err_fun(double *nom_x, double *delta_x, double *out_5579271098234299589) {
  err_fun(nom_x, delta_x, out_5579271098234299589);
}
void car_inv_err_fun(double *nom_x, double *true_x, double *out_8879118943542071452) {
  inv_err_fun(nom_x, true_x, out_8879118943542071452);
}
void car_H_mod_fun(double *state, double *out_4346759063564356553) {
  H_mod_fun(state, out_4346759063564356553);
}
void car_f_fun(double *state, double dt, double *out_8401415236153157083) {
  f_fun(state,  dt, out_8401415236153157083);
}
void car_F_fun(double *state, double dt, double *out_1973239055632703499) {
  F_fun(state,  dt, out_1973239055632703499);
}
void car_h_25(double *state, double *unused, double *out_7709444436246576106) {
  h_25(state, unused, out_7709444436246576106);
}
void car_H_25(double *state, double *unused, double *out_4906796784232957826) {
  H_25(state, unused, out_4906796784232957826);
}
void car_h_24(double *state, double *unused, double *out_8161953024412082811) {
  h_24(state, unused, out_8161953024412082811);
}
void car_H_24(double *state, double *unused, double *out_6319825032271366663) {
  H_24(state, unused, out_6319825032271366663);
}
void car_h_30(double *state, double *unused, double *out_8890419815179839294) {
  h_30(state, unused, out_8890419815179839294);
}
void car_H_30(double *state, double *unused, double *out_7425129742740206453) {
  H_30(state, unused, out_7425129742740206453);
}
void car_h_26(double *state, double *unused, double *out_8798474113368893512) {
  h_26(state, unused, out_8798474113368893512);
}
void car_H_26(double *state, double *unused, double *out_1165293465358901602) {
  H_26(state, unused, out_1165293465358901602);
}
void car_h_27(double *state, double *unused, double *out_4672658384802243421) {
  h_27(state, unused, out_4672658384802243421);
}
void car_H_27(double *state, double *unused, double *out_8798020259785401946) {
  H_27(state, unused, out_8798020259785401946);
}
void car_h_29(double *state, double *unused, double *out_4214457022643681759) {
  h_29(state, unused, out_4214457022643681759);
}
void car_H_29(double *state, double *unused, double *out_7935361087054598637) {
  H_29(state, unused, out_7935361087054598637);
}
void car_h_28(double *state, double *unused, double *out_8772412421246462550) {
  h_28(state, unused, out_8772412421246462550);
}
void car_H_28(double *state, double *unused, double *out_2852962069985068063) {
  H_28(state, unused, out_2852962069985068063);
}
void car_h_31(double *state, double *unused, double *out_7434250373962070217) {
  h_31(state, unused, out_7434250373962070217);
}
void car_H_31(double *state, double *unused, double *out_539085363125550126) {
  H_31(state, unused, out_539085363125550126);
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
