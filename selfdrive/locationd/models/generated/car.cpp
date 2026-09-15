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
void err_fun(double *nom_x, double *delta_x, double *out_5552049021186220575) {
   out_5552049021186220575[0] = delta_x[0] + nom_x[0];
   out_5552049021186220575[1] = delta_x[1] + nom_x[1];
   out_5552049021186220575[2] = delta_x[2] + nom_x[2];
   out_5552049021186220575[3] = delta_x[3] + nom_x[3];
   out_5552049021186220575[4] = delta_x[4] + nom_x[4];
   out_5552049021186220575[5] = delta_x[5] + nom_x[5];
   out_5552049021186220575[6] = delta_x[6] + nom_x[6];
   out_5552049021186220575[7] = delta_x[7] + nom_x[7];
   out_5552049021186220575[8] = delta_x[8] + nom_x[8];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_590150806491182217) {
   out_590150806491182217[0] = -nom_x[0] + true_x[0];
   out_590150806491182217[1] = -nom_x[1] + true_x[1];
   out_590150806491182217[2] = -nom_x[2] + true_x[2];
   out_590150806491182217[3] = -nom_x[3] + true_x[3];
   out_590150806491182217[4] = -nom_x[4] + true_x[4];
   out_590150806491182217[5] = -nom_x[5] + true_x[5];
   out_590150806491182217[6] = -nom_x[6] + true_x[6];
   out_590150806491182217[7] = -nom_x[7] + true_x[7];
   out_590150806491182217[8] = -nom_x[8] + true_x[8];
}
void H_mod_fun(double *state, double *out_462982770310503507) {
   out_462982770310503507[0] = 1.0;
   out_462982770310503507[1] = 0.0;
   out_462982770310503507[2] = 0.0;
   out_462982770310503507[3] = 0.0;
   out_462982770310503507[4] = 0.0;
   out_462982770310503507[5] = 0.0;
   out_462982770310503507[6] = 0.0;
   out_462982770310503507[7] = 0.0;
   out_462982770310503507[8] = 0.0;
   out_462982770310503507[9] = 0.0;
   out_462982770310503507[10] = 1.0;
   out_462982770310503507[11] = 0.0;
   out_462982770310503507[12] = 0.0;
   out_462982770310503507[13] = 0.0;
   out_462982770310503507[14] = 0.0;
   out_462982770310503507[15] = 0.0;
   out_462982770310503507[16] = 0.0;
   out_462982770310503507[17] = 0.0;
   out_462982770310503507[18] = 0.0;
   out_462982770310503507[19] = 0.0;
   out_462982770310503507[20] = 1.0;
   out_462982770310503507[21] = 0.0;
   out_462982770310503507[22] = 0.0;
   out_462982770310503507[23] = 0.0;
   out_462982770310503507[24] = 0.0;
   out_462982770310503507[25] = 0.0;
   out_462982770310503507[26] = 0.0;
   out_462982770310503507[27] = 0.0;
   out_462982770310503507[28] = 0.0;
   out_462982770310503507[29] = 0.0;
   out_462982770310503507[30] = 1.0;
   out_462982770310503507[31] = 0.0;
   out_462982770310503507[32] = 0.0;
   out_462982770310503507[33] = 0.0;
   out_462982770310503507[34] = 0.0;
   out_462982770310503507[35] = 0.0;
   out_462982770310503507[36] = 0.0;
   out_462982770310503507[37] = 0.0;
   out_462982770310503507[38] = 0.0;
   out_462982770310503507[39] = 0.0;
   out_462982770310503507[40] = 1.0;
   out_462982770310503507[41] = 0.0;
   out_462982770310503507[42] = 0.0;
   out_462982770310503507[43] = 0.0;
   out_462982770310503507[44] = 0.0;
   out_462982770310503507[45] = 0.0;
   out_462982770310503507[46] = 0.0;
   out_462982770310503507[47] = 0.0;
   out_462982770310503507[48] = 0.0;
   out_462982770310503507[49] = 0.0;
   out_462982770310503507[50] = 1.0;
   out_462982770310503507[51] = 0.0;
   out_462982770310503507[52] = 0.0;
   out_462982770310503507[53] = 0.0;
   out_462982770310503507[54] = 0.0;
   out_462982770310503507[55] = 0.0;
   out_462982770310503507[56] = 0.0;
   out_462982770310503507[57] = 0.0;
   out_462982770310503507[58] = 0.0;
   out_462982770310503507[59] = 0.0;
   out_462982770310503507[60] = 1.0;
   out_462982770310503507[61] = 0.0;
   out_462982770310503507[62] = 0.0;
   out_462982770310503507[63] = 0.0;
   out_462982770310503507[64] = 0.0;
   out_462982770310503507[65] = 0.0;
   out_462982770310503507[66] = 0.0;
   out_462982770310503507[67] = 0.0;
   out_462982770310503507[68] = 0.0;
   out_462982770310503507[69] = 0.0;
   out_462982770310503507[70] = 1.0;
   out_462982770310503507[71] = 0.0;
   out_462982770310503507[72] = 0.0;
   out_462982770310503507[73] = 0.0;
   out_462982770310503507[74] = 0.0;
   out_462982770310503507[75] = 0.0;
   out_462982770310503507[76] = 0.0;
   out_462982770310503507[77] = 0.0;
   out_462982770310503507[78] = 0.0;
   out_462982770310503507[79] = 0.0;
   out_462982770310503507[80] = 1.0;
}
void f_fun(double *state, double dt, double *out_169833714219358489) {
   out_169833714219358489[0] = state[0];
   out_169833714219358489[1] = state[1];
   out_169833714219358489[2] = state[2];
   out_169833714219358489[3] = state[3];
   out_169833714219358489[4] = state[4];
   out_169833714219358489[5] = dt*((-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]))*state[6] - 9.8100000000000005*state[8] + stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*state[1]) + (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*state[4])) + state[5];
   out_169833714219358489[6] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*state[4])) + state[6];
   out_169833714219358489[7] = state[7];
   out_169833714219358489[8] = state[8];
}
void F_fun(double *state, double dt, double *out_3869384383894482819) {
   out_3869384383894482819[0] = 1;
   out_3869384383894482819[1] = 0;
   out_3869384383894482819[2] = 0;
   out_3869384383894482819[3] = 0;
   out_3869384383894482819[4] = 0;
   out_3869384383894482819[5] = 0;
   out_3869384383894482819[6] = 0;
   out_3869384383894482819[7] = 0;
   out_3869384383894482819[8] = 0;
   out_3869384383894482819[9] = 0;
   out_3869384383894482819[10] = 1;
   out_3869384383894482819[11] = 0;
   out_3869384383894482819[12] = 0;
   out_3869384383894482819[13] = 0;
   out_3869384383894482819[14] = 0;
   out_3869384383894482819[15] = 0;
   out_3869384383894482819[16] = 0;
   out_3869384383894482819[17] = 0;
   out_3869384383894482819[18] = 0;
   out_3869384383894482819[19] = 0;
   out_3869384383894482819[20] = 1;
   out_3869384383894482819[21] = 0;
   out_3869384383894482819[22] = 0;
   out_3869384383894482819[23] = 0;
   out_3869384383894482819[24] = 0;
   out_3869384383894482819[25] = 0;
   out_3869384383894482819[26] = 0;
   out_3869384383894482819[27] = 0;
   out_3869384383894482819[28] = 0;
   out_3869384383894482819[29] = 0;
   out_3869384383894482819[30] = 1;
   out_3869384383894482819[31] = 0;
   out_3869384383894482819[32] = 0;
   out_3869384383894482819[33] = 0;
   out_3869384383894482819[34] = 0;
   out_3869384383894482819[35] = 0;
   out_3869384383894482819[36] = 0;
   out_3869384383894482819[37] = 0;
   out_3869384383894482819[38] = 0;
   out_3869384383894482819[39] = 0;
   out_3869384383894482819[40] = 1;
   out_3869384383894482819[41] = 0;
   out_3869384383894482819[42] = 0;
   out_3869384383894482819[43] = 0;
   out_3869384383894482819[44] = 0;
   out_3869384383894482819[45] = dt*(stiffness_front*(-state[2] - state[3] + state[7])/(mass*state[1]) + (-stiffness_front - stiffness_rear)*state[5]/(mass*state[4]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[6]/(mass*state[4]));
   out_3869384383894482819[46] = -dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*pow(state[1], 2));
   out_3869384383894482819[47] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_3869384383894482819[48] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_3869384383894482819[49] = dt*((-1 - (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*pow(state[4], 2)))*state[6] - (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*pow(state[4], 2)));
   out_3869384383894482819[50] = dt*(-stiffness_front*state[0] - stiffness_rear*state[0])/(mass*state[4]) + 1;
   out_3869384383894482819[51] = dt*(-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]));
   out_3869384383894482819[52] = dt*stiffness_front*state[0]/(mass*state[1]);
   out_3869384383894482819[53] = -9.8100000000000005*dt;
   out_3869384383894482819[54] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front - pow(center_to_rear, 2)*stiffness_rear)*state[6]/(rotational_inertia*state[4]));
   out_3869384383894482819[55] = -center_to_front*dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*pow(state[1], 2));
   out_3869384383894482819[56] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_3869384383894482819[57] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_3869384383894482819[58] = dt*(-(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*pow(state[4], 2)) - (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*pow(state[4], 2)));
   out_3869384383894482819[59] = dt*(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(rotational_inertia*state[4]);
   out_3869384383894482819[60] = dt*(-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])/(rotational_inertia*state[4]) + 1;
   out_3869384383894482819[61] = center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_3869384383894482819[62] = 0;
   out_3869384383894482819[63] = 0;
   out_3869384383894482819[64] = 0;
   out_3869384383894482819[65] = 0;
   out_3869384383894482819[66] = 0;
   out_3869384383894482819[67] = 0;
   out_3869384383894482819[68] = 0;
   out_3869384383894482819[69] = 0;
   out_3869384383894482819[70] = 1;
   out_3869384383894482819[71] = 0;
   out_3869384383894482819[72] = 0;
   out_3869384383894482819[73] = 0;
   out_3869384383894482819[74] = 0;
   out_3869384383894482819[75] = 0;
   out_3869384383894482819[76] = 0;
   out_3869384383894482819[77] = 0;
   out_3869384383894482819[78] = 0;
   out_3869384383894482819[79] = 0;
   out_3869384383894482819[80] = 1;
}
void h_25(double *state, double *unused, double *out_3087348870251025033) {
   out_3087348870251025033[0] = state[6];
}
void H_25(double *state, double *unused, double *out_8790573077486810872) {
   out_8790573077486810872[0] = 0;
   out_8790573077486810872[1] = 0;
   out_8790573077486810872[2] = 0;
   out_8790573077486810872[3] = 0;
   out_8790573077486810872[4] = 0;
   out_8790573077486810872[5] = 0;
   out_8790573077486810872[6] = 1;
   out_8790573077486810872[7] = 0;
   out_8790573077486810872[8] = 0;
}
void h_24(double *state, double *unused, double *out_6915008056190712895) {
   out_6915008056190712895[0] = state[4];
   out_6915008056190712895[1] = state[5];
}
void H_24(double *state, double *unused, double *out_6617923478481311306) {
   out_6617923478481311306[0] = 0;
   out_6617923478481311306[1] = 0;
   out_6617923478481311306[2] = 0;
   out_6617923478481311306[3] = 0;
   out_6617923478481311306[4] = 1;
   out_6617923478481311306[5] = 0;
   out_6617923478481311306[6] = 0;
   out_6617923478481311306[7] = 0;
   out_6617923478481311306[8] = 0;
   out_6617923478481311306[9] = 0;
   out_6617923478481311306[10] = 0;
   out_6617923478481311306[11] = 0;
   out_6617923478481311306[12] = 0;
   out_6617923478481311306[13] = 0;
   out_6617923478481311306[14] = 1;
   out_6617923478481311306[15] = 0;
   out_6617923478481311306[16] = 0;
   out_6617923478481311306[17] = 0;
}
void h_30(double *state, double *unused, double *out_3500479056225270130) {
   out_3500479056225270130[0] = state[4];
}
void H_30(double *state, double *unused, double *out_2739480654731123989) {
   out_2739480654731123989[0] = 0;
   out_2739480654731123989[1] = 0;
   out_2739480654731123989[2] = 0;
   out_2739480654731123989[3] = 0;
   out_2739480654731123989[4] = 1;
   out_2739480654731123989[5] = 0;
   out_2739480654731123989[6] = 0;
   out_2739480654731123989[7] = 0;
   out_2739480654731123989[8] = 0;
}
void h_26(double *state, double *unused, double *out_2897163171548792613) {
   out_2897163171548792613[0] = state[7];
}
void H_26(double *state, double *unused, double *out_5049069758612754648) {
   out_5049069758612754648[0] = 0;
   out_5049069758612754648[1] = 0;
   out_5049069758612754648[2] = 0;
   out_5049069758612754648[3] = 0;
   out_5049069758612754648[4] = 0;
   out_5049069758612754648[5] = 0;
   out_5049069758612754648[6] = 0;
   out_5049069758612754648[7] = 1;
   out_5049069758612754648[8] = 0;
}
void h_27(double *state, double *unused, double *out_5691754191059722684) {
   out_5691754191059722684[0] = state[3];
}
void H_27(double *state, double *unused, double *out_4914243966531548900) {
   out_4914243966531548900[0] = 0;
   out_4914243966531548900[1] = 0;
   out_4914243966531548900[2] = 0;
   out_4914243966531548900[3] = 1;
   out_4914243966531548900[4] = 0;
   out_4914243966531548900[5] = 0;
   out_4914243966531548900[6] = 0;
   out_4914243966531548900[7] = 0;
   out_4914243966531548900[8] = 0;
}
void h_29(double *state, double *unused, double *out_8502152323886115775) {
   out_8502152323886115775[0] = state[1];
}
void H_29(double *state, double *unused, double *out_6627606693401099933) {
   out_6627606693401099933[0] = 0;
   out_6627606693401099933[1] = 1;
   out_6627606693401099933[2] = 0;
   out_6627606693401099933[3] = 0;
   out_6627606693401099933[4] = 0;
   out_6627606693401099933[5] = 0;
   out_6627606693401099933[6] = 0;
   out_6627606693401099933[7] = 0;
   out_6627606693401099933[8] = 0;
}
void h_28(double *state, double *unused, double *out_7413122646763798369) {
   out_7413122646763798369[0] = state[0];
}
void H_28(double *state, double *unused, double *out_6736738363238921109) {
   out_6736738363238921109[0] = 1;
   out_6736738363238921109[1] = 0;
   out_6736738363238921109[2] = 0;
   out_6736738363238921109[3] = 0;
   out_6736738363238921109[4] = 0;
   out_6736738363238921109[5] = 0;
   out_6736738363238921109[6] = 0;
   out_6736738363238921109[7] = 0;
   out_6736738363238921109[8] = 0;
}
void h_31(double *state, double *unused, double *out_2930162201899895888) {
   out_2930162201899895888[0] = state[8];
}
void H_31(double *state, double *unused, double *out_8821219039363771300) {
   out_8821219039363771300[0] = 0;
   out_8821219039363771300[1] = 0;
   out_8821219039363771300[2] = 0;
   out_8821219039363771300[3] = 0;
   out_8821219039363771300[4] = 0;
   out_8821219039363771300[5] = 0;
   out_8821219039363771300[6] = 0;
   out_8821219039363771300[7] = 0;
   out_8821219039363771300[8] = 1;
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
void car_err_fun(double *nom_x, double *delta_x, double *out_5552049021186220575) {
  err_fun(nom_x, delta_x, out_5552049021186220575);
}
void car_inv_err_fun(double *nom_x, double *true_x, double *out_590150806491182217) {
  inv_err_fun(nom_x, true_x, out_590150806491182217);
}
void car_H_mod_fun(double *state, double *out_462982770310503507) {
  H_mod_fun(state, out_462982770310503507);
}
void car_f_fun(double *state, double dt, double *out_169833714219358489) {
  f_fun(state,  dt, out_169833714219358489);
}
void car_F_fun(double *state, double dt, double *out_3869384383894482819) {
  F_fun(state,  dt, out_3869384383894482819);
}
void car_h_25(double *state, double *unused, double *out_3087348870251025033) {
  h_25(state, unused, out_3087348870251025033);
}
void car_H_25(double *state, double *unused, double *out_8790573077486810872) {
  H_25(state, unused, out_8790573077486810872);
}
void car_h_24(double *state, double *unused, double *out_6915008056190712895) {
  h_24(state, unused, out_6915008056190712895);
}
void car_H_24(double *state, double *unused, double *out_6617923478481311306) {
  H_24(state, unused, out_6617923478481311306);
}
void car_h_30(double *state, double *unused, double *out_3500479056225270130) {
  h_30(state, unused, out_3500479056225270130);
}
void car_H_30(double *state, double *unused, double *out_2739480654731123989) {
  H_30(state, unused, out_2739480654731123989);
}
void car_h_26(double *state, double *unused, double *out_2897163171548792613) {
  h_26(state, unused, out_2897163171548792613);
}
void car_H_26(double *state, double *unused, double *out_5049069758612754648) {
  H_26(state, unused, out_5049069758612754648);
}
void car_h_27(double *state, double *unused, double *out_5691754191059722684) {
  h_27(state, unused, out_5691754191059722684);
}
void car_H_27(double *state, double *unused, double *out_4914243966531548900) {
  H_27(state, unused, out_4914243966531548900);
}
void car_h_29(double *state, double *unused, double *out_8502152323886115775) {
  h_29(state, unused, out_8502152323886115775);
}
void car_H_29(double *state, double *unused, double *out_6627606693401099933) {
  H_29(state, unused, out_6627606693401099933);
}
void car_h_28(double *state, double *unused, double *out_7413122646763798369) {
  h_28(state, unused, out_7413122646763798369);
}
void car_H_28(double *state, double *unused, double *out_6736738363238921109) {
  H_28(state, unused, out_6736738363238921109);
}
void car_h_31(double *state, double *unused, double *out_2930162201899895888) {
  h_31(state, unused, out_2930162201899895888);
}
void car_H_31(double *state, double *unused, double *out_8821219039363771300) {
  H_31(state, unused, out_8821219039363771300);
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
