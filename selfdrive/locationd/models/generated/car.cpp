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
void err_fun(double *nom_x, double *delta_x, double *out_1981160884949189432) {
   out_1981160884949189432[0] = delta_x[0] + nom_x[0];
   out_1981160884949189432[1] = delta_x[1] + nom_x[1];
   out_1981160884949189432[2] = delta_x[2] + nom_x[2];
   out_1981160884949189432[3] = delta_x[3] + nom_x[3];
   out_1981160884949189432[4] = delta_x[4] + nom_x[4];
   out_1981160884949189432[5] = delta_x[5] + nom_x[5];
   out_1981160884949189432[6] = delta_x[6] + nom_x[6];
   out_1981160884949189432[7] = delta_x[7] + nom_x[7];
   out_1981160884949189432[8] = delta_x[8] + nom_x[8];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_8847679371512298388) {
   out_8847679371512298388[0] = -nom_x[0] + true_x[0];
   out_8847679371512298388[1] = -nom_x[1] + true_x[1];
   out_8847679371512298388[2] = -nom_x[2] + true_x[2];
   out_8847679371512298388[3] = -nom_x[3] + true_x[3];
   out_8847679371512298388[4] = -nom_x[4] + true_x[4];
   out_8847679371512298388[5] = -nom_x[5] + true_x[5];
   out_8847679371512298388[6] = -nom_x[6] + true_x[6];
   out_8847679371512298388[7] = -nom_x[7] + true_x[7];
   out_8847679371512298388[8] = -nom_x[8] + true_x[8];
}
void H_mod_fun(double *state, double *out_5601961838873094342) {
   out_5601961838873094342[0] = 1.0;
   out_5601961838873094342[1] = 0.0;
   out_5601961838873094342[2] = 0.0;
   out_5601961838873094342[3] = 0.0;
   out_5601961838873094342[4] = 0.0;
   out_5601961838873094342[5] = 0.0;
   out_5601961838873094342[6] = 0.0;
   out_5601961838873094342[7] = 0.0;
   out_5601961838873094342[8] = 0.0;
   out_5601961838873094342[9] = 0.0;
   out_5601961838873094342[10] = 1.0;
   out_5601961838873094342[11] = 0.0;
   out_5601961838873094342[12] = 0.0;
   out_5601961838873094342[13] = 0.0;
   out_5601961838873094342[14] = 0.0;
   out_5601961838873094342[15] = 0.0;
   out_5601961838873094342[16] = 0.0;
   out_5601961838873094342[17] = 0.0;
   out_5601961838873094342[18] = 0.0;
   out_5601961838873094342[19] = 0.0;
   out_5601961838873094342[20] = 1.0;
   out_5601961838873094342[21] = 0.0;
   out_5601961838873094342[22] = 0.0;
   out_5601961838873094342[23] = 0.0;
   out_5601961838873094342[24] = 0.0;
   out_5601961838873094342[25] = 0.0;
   out_5601961838873094342[26] = 0.0;
   out_5601961838873094342[27] = 0.0;
   out_5601961838873094342[28] = 0.0;
   out_5601961838873094342[29] = 0.0;
   out_5601961838873094342[30] = 1.0;
   out_5601961838873094342[31] = 0.0;
   out_5601961838873094342[32] = 0.0;
   out_5601961838873094342[33] = 0.0;
   out_5601961838873094342[34] = 0.0;
   out_5601961838873094342[35] = 0.0;
   out_5601961838873094342[36] = 0.0;
   out_5601961838873094342[37] = 0.0;
   out_5601961838873094342[38] = 0.0;
   out_5601961838873094342[39] = 0.0;
   out_5601961838873094342[40] = 1.0;
   out_5601961838873094342[41] = 0.0;
   out_5601961838873094342[42] = 0.0;
   out_5601961838873094342[43] = 0.0;
   out_5601961838873094342[44] = 0.0;
   out_5601961838873094342[45] = 0.0;
   out_5601961838873094342[46] = 0.0;
   out_5601961838873094342[47] = 0.0;
   out_5601961838873094342[48] = 0.0;
   out_5601961838873094342[49] = 0.0;
   out_5601961838873094342[50] = 1.0;
   out_5601961838873094342[51] = 0.0;
   out_5601961838873094342[52] = 0.0;
   out_5601961838873094342[53] = 0.0;
   out_5601961838873094342[54] = 0.0;
   out_5601961838873094342[55] = 0.0;
   out_5601961838873094342[56] = 0.0;
   out_5601961838873094342[57] = 0.0;
   out_5601961838873094342[58] = 0.0;
   out_5601961838873094342[59] = 0.0;
   out_5601961838873094342[60] = 1.0;
   out_5601961838873094342[61] = 0.0;
   out_5601961838873094342[62] = 0.0;
   out_5601961838873094342[63] = 0.0;
   out_5601961838873094342[64] = 0.0;
   out_5601961838873094342[65] = 0.0;
   out_5601961838873094342[66] = 0.0;
   out_5601961838873094342[67] = 0.0;
   out_5601961838873094342[68] = 0.0;
   out_5601961838873094342[69] = 0.0;
   out_5601961838873094342[70] = 1.0;
   out_5601961838873094342[71] = 0.0;
   out_5601961838873094342[72] = 0.0;
   out_5601961838873094342[73] = 0.0;
   out_5601961838873094342[74] = 0.0;
   out_5601961838873094342[75] = 0.0;
   out_5601961838873094342[76] = 0.0;
   out_5601961838873094342[77] = 0.0;
   out_5601961838873094342[78] = 0.0;
   out_5601961838873094342[79] = 0.0;
   out_5601961838873094342[80] = 1.0;
}
void f_fun(double *state, double dt, double *out_5149707672518823132) {
   out_5149707672518823132[0] = state[0];
   out_5149707672518823132[1] = state[1];
   out_5149707672518823132[2] = state[2];
   out_5149707672518823132[3] = state[3];
   out_5149707672518823132[4] = state[4];
   out_5149707672518823132[5] = dt*((-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]))*state[6] - 9.8100000000000005*state[8] + stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*state[1]) + (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*state[4])) + state[5];
   out_5149707672518823132[6] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*state[4])) + state[6];
   out_5149707672518823132[7] = state[7];
   out_5149707672518823132[8] = state[8];
}
void F_fun(double *state, double dt, double *out_6841526781584604245) {
   out_6841526781584604245[0] = 1;
   out_6841526781584604245[1] = 0;
   out_6841526781584604245[2] = 0;
   out_6841526781584604245[3] = 0;
   out_6841526781584604245[4] = 0;
   out_6841526781584604245[5] = 0;
   out_6841526781584604245[6] = 0;
   out_6841526781584604245[7] = 0;
   out_6841526781584604245[8] = 0;
   out_6841526781584604245[9] = 0;
   out_6841526781584604245[10] = 1;
   out_6841526781584604245[11] = 0;
   out_6841526781584604245[12] = 0;
   out_6841526781584604245[13] = 0;
   out_6841526781584604245[14] = 0;
   out_6841526781584604245[15] = 0;
   out_6841526781584604245[16] = 0;
   out_6841526781584604245[17] = 0;
   out_6841526781584604245[18] = 0;
   out_6841526781584604245[19] = 0;
   out_6841526781584604245[20] = 1;
   out_6841526781584604245[21] = 0;
   out_6841526781584604245[22] = 0;
   out_6841526781584604245[23] = 0;
   out_6841526781584604245[24] = 0;
   out_6841526781584604245[25] = 0;
   out_6841526781584604245[26] = 0;
   out_6841526781584604245[27] = 0;
   out_6841526781584604245[28] = 0;
   out_6841526781584604245[29] = 0;
   out_6841526781584604245[30] = 1;
   out_6841526781584604245[31] = 0;
   out_6841526781584604245[32] = 0;
   out_6841526781584604245[33] = 0;
   out_6841526781584604245[34] = 0;
   out_6841526781584604245[35] = 0;
   out_6841526781584604245[36] = 0;
   out_6841526781584604245[37] = 0;
   out_6841526781584604245[38] = 0;
   out_6841526781584604245[39] = 0;
   out_6841526781584604245[40] = 1;
   out_6841526781584604245[41] = 0;
   out_6841526781584604245[42] = 0;
   out_6841526781584604245[43] = 0;
   out_6841526781584604245[44] = 0;
   out_6841526781584604245[45] = dt*(stiffness_front*(-state[2] - state[3] + state[7])/(mass*state[1]) + (-stiffness_front - stiffness_rear)*state[5]/(mass*state[4]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[6]/(mass*state[4]));
   out_6841526781584604245[46] = -dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*pow(state[1], 2));
   out_6841526781584604245[47] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_6841526781584604245[48] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_6841526781584604245[49] = dt*((-1 - (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*pow(state[4], 2)))*state[6] - (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*pow(state[4], 2)));
   out_6841526781584604245[50] = dt*(-stiffness_front*state[0] - stiffness_rear*state[0])/(mass*state[4]) + 1;
   out_6841526781584604245[51] = dt*(-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]));
   out_6841526781584604245[52] = dt*stiffness_front*state[0]/(mass*state[1]);
   out_6841526781584604245[53] = -9.8100000000000005*dt;
   out_6841526781584604245[54] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front - pow(center_to_rear, 2)*stiffness_rear)*state[6]/(rotational_inertia*state[4]));
   out_6841526781584604245[55] = -center_to_front*dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*pow(state[1], 2));
   out_6841526781584604245[56] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_6841526781584604245[57] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_6841526781584604245[58] = dt*(-(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*pow(state[4], 2)) - (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*pow(state[4], 2)));
   out_6841526781584604245[59] = dt*(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(rotational_inertia*state[4]);
   out_6841526781584604245[60] = dt*(-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])/(rotational_inertia*state[4]) + 1;
   out_6841526781584604245[61] = center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_6841526781584604245[62] = 0;
   out_6841526781584604245[63] = 0;
   out_6841526781584604245[64] = 0;
   out_6841526781584604245[65] = 0;
   out_6841526781584604245[66] = 0;
   out_6841526781584604245[67] = 0;
   out_6841526781584604245[68] = 0;
   out_6841526781584604245[69] = 0;
   out_6841526781584604245[70] = 1;
   out_6841526781584604245[71] = 0;
   out_6841526781584604245[72] = 0;
   out_6841526781584604245[73] = 0;
   out_6841526781584604245[74] = 0;
   out_6841526781584604245[75] = 0;
   out_6841526781584604245[76] = 0;
   out_6841526781584604245[77] = 0;
   out_6841526781584604245[78] = 0;
   out_6841526781584604245[79] = 0;
   out_6841526781584604245[80] = 1;
}
void h_25(double *state, double *unused, double *out_7458155415496567305) {
   out_7458155415496567305[0] = state[6];
}
void H_25(double *state, double *unused, double *out_698270013688429502) {
   out_698270013688429502[0] = 0;
   out_698270013688429502[1] = 0;
   out_698270013688429502[2] = 0;
   out_698270013688429502[3] = 0;
   out_698270013688429502[4] = 0;
   out_698270013688429502[5] = 0;
   out_698270013688429502[6] = 1;
   out_698270013688429502[7] = 0;
   out_698270013688429502[8] = 0;
}
void h_24(double *state, double *unused, double *out_8762756803592850260) {
   out_8762756803592850260[0] = state[4];
   out_8762756803592850260[1] = state[5];
}
void H_24(double *state, double *unused, double *out_2427133132865743571) {
   out_2427133132865743571[0] = 0;
   out_2427133132865743571[1] = 0;
   out_2427133132865743571[2] = 0;
   out_2427133132865743571[3] = 0;
   out_2427133132865743571[4] = 1;
   out_2427133132865743571[5] = 0;
   out_2427133132865743571[6] = 0;
   out_2427133132865743571[7] = 0;
   out_2427133132865743571[8] = 0;
   out_2427133132865743571[9] = 0;
   out_2427133132865743571[10] = 0;
   out_2427133132865743571[11] = 0;
   out_2427133132865743571[12] = 0;
   out_2427133132865743571[13] = 0;
   out_2427133132865743571[14] = 1;
   out_2427133132865743571[15] = 0;
   out_2427133132865743571[16] = 0;
   out_2427133132865743571[17] = 0;
}
void h_30(double *state, double *unused, double *out_434784079387956054) {
   out_434784079387956054[0] = state[4];
}
void H_30(double *state, double *unused, double *out_6218420327803187253) {
   out_6218420327803187253[0] = 0;
   out_6218420327803187253[1] = 0;
   out_6218420327803187253[2] = 0;
   out_6218420327803187253[3] = 0;
   out_6218420327803187253[4] = 1;
   out_6218420327803187253[5] = 0;
   out_6218420327803187253[6] = 0;
   out_6218420327803187253[7] = 0;
   out_6218420327803187253[8] = 0;
}
void h_26(double *state, double *unused, double *out_8798712813018318160) {
   out_8798712813018318160[0] = state[7];
}
void H_26(double *state, double *unused, double *out_4439773332562485726) {
   out_4439773332562485726[0] = 0;
   out_4439773332562485726[1] = 0;
   out_4439773332562485726[2] = 0;
   out_4439773332562485726[3] = 0;
   out_4439773332562485726[4] = 0;
   out_4439773332562485726[5] = 0;
   out_4439773332562485726[6] = 0;
   out_4439773332562485726[7] = 1;
   out_4439773332562485726[8] = 0;
}
void h_27(double *state, double *unused, double *out_723267455973180046) {
   out_723267455973180046[0] = state[3];
}
void H_27(double *state, double *unused, double *out_4043657016002762342) {
   out_4043657016002762342[0] = 0;
   out_4043657016002762342[1] = 0;
   out_4043657016002762342[2] = 0;
   out_4043657016002762342[3] = 1;
   out_4043657016002762342[4] = 0;
   out_4043657016002762342[5] = 0;
   out_4043657016002762342[6] = 0;
   out_4043657016002762342[7] = 0;
   out_4043657016002762342[8] = 0;
}
void h_29(double *state, double *unused, double *out_4920797374511219811) {
   out_4920797374511219811[0] = state[1];
}
void H_29(double *state, double *unused, double *out_2330294289133211309) {
   out_2330294289133211309[0] = 0;
   out_2330294289133211309[1] = 1;
   out_2330294289133211309[2] = 0;
   out_2330294289133211309[3] = 0;
   out_2330294289133211309[4] = 0;
   out_2330294289133211309[5] = 0;
   out_2330294289133211309[6] = 0;
   out_2330294289133211309[7] = 0;
   out_2330294289133211309[8] = 0;
}
void h_28(double *state, double *unused, double *out_3477859511150572185) {
   out_3477859511150572185[0] = state[0];
}
void H_28(double *state, double *unused, double *out_2752104727936319265) {
   out_2752104727936319265[0] = 1;
   out_2752104727936319265[1] = 0;
   out_2752104727936319265[2] = 0;
   out_2752104727936319265[3] = 0;
   out_2752104727936319265[4] = 0;
   out_2752104727936319265[5] = 0;
   out_2752104727936319265[6] = 0;
   out_2752104727936319265[7] = 0;
   out_2752104727936319265[8] = 0;
}
void h_31(double *state, double *unused, double *out_4217753431862633375) {
   out_4217753431862633375[0] = state[8];
}
void H_31(double *state, double *unused, double *out_667624051811469074) {
   out_667624051811469074[0] = 0;
   out_667624051811469074[1] = 0;
   out_667624051811469074[2] = 0;
   out_667624051811469074[3] = 0;
   out_667624051811469074[4] = 0;
   out_667624051811469074[5] = 0;
   out_667624051811469074[6] = 0;
   out_667624051811469074[7] = 0;
   out_667624051811469074[8] = 1;
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
void car_err_fun(double *nom_x, double *delta_x, double *out_1981160884949189432) {
  err_fun(nom_x, delta_x, out_1981160884949189432);
}
void car_inv_err_fun(double *nom_x, double *true_x, double *out_8847679371512298388) {
  inv_err_fun(nom_x, true_x, out_8847679371512298388);
}
void car_H_mod_fun(double *state, double *out_5601961838873094342) {
  H_mod_fun(state, out_5601961838873094342);
}
void car_f_fun(double *state, double dt, double *out_5149707672518823132) {
  f_fun(state,  dt, out_5149707672518823132);
}
void car_F_fun(double *state, double dt, double *out_6841526781584604245) {
  F_fun(state,  dt, out_6841526781584604245);
}
void car_h_25(double *state, double *unused, double *out_7458155415496567305) {
  h_25(state, unused, out_7458155415496567305);
}
void car_H_25(double *state, double *unused, double *out_698270013688429502) {
  H_25(state, unused, out_698270013688429502);
}
void car_h_24(double *state, double *unused, double *out_8762756803592850260) {
  h_24(state, unused, out_8762756803592850260);
}
void car_H_24(double *state, double *unused, double *out_2427133132865743571) {
  H_24(state, unused, out_2427133132865743571);
}
void car_h_30(double *state, double *unused, double *out_434784079387956054) {
  h_30(state, unused, out_434784079387956054);
}
void car_H_30(double *state, double *unused, double *out_6218420327803187253) {
  H_30(state, unused, out_6218420327803187253);
}
void car_h_26(double *state, double *unused, double *out_8798712813018318160) {
  h_26(state, unused, out_8798712813018318160);
}
void car_H_26(double *state, double *unused, double *out_4439773332562485726) {
  H_26(state, unused, out_4439773332562485726);
}
void car_h_27(double *state, double *unused, double *out_723267455973180046) {
  h_27(state, unused, out_723267455973180046);
}
void car_H_27(double *state, double *unused, double *out_4043657016002762342) {
  H_27(state, unused, out_4043657016002762342);
}
void car_h_29(double *state, double *unused, double *out_4920797374511219811) {
  h_29(state, unused, out_4920797374511219811);
}
void car_H_29(double *state, double *unused, double *out_2330294289133211309) {
  H_29(state, unused, out_2330294289133211309);
}
void car_h_28(double *state, double *unused, double *out_3477859511150572185) {
  h_28(state, unused, out_3477859511150572185);
}
void car_H_28(double *state, double *unused, double *out_2752104727936319265) {
  H_28(state, unused, out_2752104727936319265);
}
void car_h_31(double *state, double *unused, double *out_4217753431862633375) {
  h_31(state, unused, out_4217753431862633375);
}
void car_H_31(double *state, double *unused, double *out_667624051811469074) {
  H_31(state, unused, out_667624051811469074);
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
