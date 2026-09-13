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
void err_fun(double *nom_x, double *delta_x, double *out_6455770263676897448) {
   out_6455770263676897448[0] = delta_x[0] + nom_x[0];
   out_6455770263676897448[1] = delta_x[1] + nom_x[1];
   out_6455770263676897448[2] = delta_x[2] + nom_x[2];
   out_6455770263676897448[3] = delta_x[3] + nom_x[3];
   out_6455770263676897448[4] = delta_x[4] + nom_x[4];
   out_6455770263676897448[5] = delta_x[5] + nom_x[5];
   out_6455770263676897448[6] = delta_x[6] + nom_x[6];
   out_6455770263676897448[7] = delta_x[7] + nom_x[7];
   out_6455770263676897448[8] = delta_x[8] + nom_x[8];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_3264339508163218326) {
   out_3264339508163218326[0] = -nom_x[0] + true_x[0];
   out_3264339508163218326[1] = -nom_x[1] + true_x[1];
   out_3264339508163218326[2] = -nom_x[2] + true_x[2];
   out_3264339508163218326[3] = -nom_x[3] + true_x[3];
   out_3264339508163218326[4] = -nom_x[4] + true_x[4];
   out_3264339508163218326[5] = -nom_x[5] + true_x[5];
   out_3264339508163218326[6] = -nom_x[6] + true_x[6];
   out_3264339508163218326[7] = -nom_x[7] + true_x[7];
   out_3264339508163218326[8] = -nom_x[8] + true_x[8];
}
void H_mod_fun(double *state, double *out_2314116705851516155) {
   out_2314116705851516155[0] = 1.0;
   out_2314116705851516155[1] = 0.0;
   out_2314116705851516155[2] = 0.0;
   out_2314116705851516155[3] = 0.0;
   out_2314116705851516155[4] = 0.0;
   out_2314116705851516155[5] = 0.0;
   out_2314116705851516155[6] = 0.0;
   out_2314116705851516155[7] = 0.0;
   out_2314116705851516155[8] = 0.0;
   out_2314116705851516155[9] = 0.0;
   out_2314116705851516155[10] = 1.0;
   out_2314116705851516155[11] = 0.0;
   out_2314116705851516155[12] = 0.0;
   out_2314116705851516155[13] = 0.0;
   out_2314116705851516155[14] = 0.0;
   out_2314116705851516155[15] = 0.0;
   out_2314116705851516155[16] = 0.0;
   out_2314116705851516155[17] = 0.0;
   out_2314116705851516155[18] = 0.0;
   out_2314116705851516155[19] = 0.0;
   out_2314116705851516155[20] = 1.0;
   out_2314116705851516155[21] = 0.0;
   out_2314116705851516155[22] = 0.0;
   out_2314116705851516155[23] = 0.0;
   out_2314116705851516155[24] = 0.0;
   out_2314116705851516155[25] = 0.0;
   out_2314116705851516155[26] = 0.0;
   out_2314116705851516155[27] = 0.0;
   out_2314116705851516155[28] = 0.0;
   out_2314116705851516155[29] = 0.0;
   out_2314116705851516155[30] = 1.0;
   out_2314116705851516155[31] = 0.0;
   out_2314116705851516155[32] = 0.0;
   out_2314116705851516155[33] = 0.0;
   out_2314116705851516155[34] = 0.0;
   out_2314116705851516155[35] = 0.0;
   out_2314116705851516155[36] = 0.0;
   out_2314116705851516155[37] = 0.0;
   out_2314116705851516155[38] = 0.0;
   out_2314116705851516155[39] = 0.0;
   out_2314116705851516155[40] = 1.0;
   out_2314116705851516155[41] = 0.0;
   out_2314116705851516155[42] = 0.0;
   out_2314116705851516155[43] = 0.0;
   out_2314116705851516155[44] = 0.0;
   out_2314116705851516155[45] = 0.0;
   out_2314116705851516155[46] = 0.0;
   out_2314116705851516155[47] = 0.0;
   out_2314116705851516155[48] = 0.0;
   out_2314116705851516155[49] = 0.0;
   out_2314116705851516155[50] = 1.0;
   out_2314116705851516155[51] = 0.0;
   out_2314116705851516155[52] = 0.0;
   out_2314116705851516155[53] = 0.0;
   out_2314116705851516155[54] = 0.0;
   out_2314116705851516155[55] = 0.0;
   out_2314116705851516155[56] = 0.0;
   out_2314116705851516155[57] = 0.0;
   out_2314116705851516155[58] = 0.0;
   out_2314116705851516155[59] = 0.0;
   out_2314116705851516155[60] = 1.0;
   out_2314116705851516155[61] = 0.0;
   out_2314116705851516155[62] = 0.0;
   out_2314116705851516155[63] = 0.0;
   out_2314116705851516155[64] = 0.0;
   out_2314116705851516155[65] = 0.0;
   out_2314116705851516155[66] = 0.0;
   out_2314116705851516155[67] = 0.0;
   out_2314116705851516155[68] = 0.0;
   out_2314116705851516155[69] = 0.0;
   out_2314116705851516155[70] = 1.0;
   out_2314116705851516155[71] = 0.0;
   out_2314116705851516155[72] = 0.0;
   out_2314116705851516155[73] = 0.0;
   out_2314116705851516155[74] = 0.0;
   out_2314116705851516155[75] = 0.0;
   out_2314116705851516155[76] = 0.0;
   out_2314116705851516155[77] = 0.0;
   out_2314116705851516155[78] = 0.0;
   out_2314116705851516155[79] = 0.0;
   out_2314116705851516155[80] = 1.0;
}
void f_fun(double *state, double dt, double *out_3179221506286947540) {
   out_3179221506286947540[0] = state[0];
   out_3179221506286947540[1] = state[1];
   out_3179221506286947540[2] = state[2];
   out_3179221506286947540[3] = state[3];
   out_3179221506286947540[4] = state[4];
   out_3179221506286947540[5] = dt*((-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]))*state[6] - 9.8100000000000005*state[8] + stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*state[1]) + (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*state[4])) + state[5];
   out_3179221506286947540[6] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*state[4])) + state[6];
   out_3179221506286947540[7] = state[7];
   out_3179221506286947540[8] = state[8];
}
void F_fun(double *state, double dt, double *out_2603402554270443885) {
   out_2603402554270443885[0] = 1;
   out_2603402554270443885[1] = 0;
   out_2603402554270443885[2] = 0;
   out_2603402554270443885[3] = 0;
   out_2603402554270443885[4] = 0;
   out_2603402554270443885[5] = 0;
   out_2603402554270443885[6] = 0;
   out_2603402554270443885[7] = 0;
   out_2603402554270443885[8] = 0;
   out_2603402554270443885[9] = 0;
   out_2603402554270443885[10] = 1;
   out_2603402554270443885[11] = 0;
   out_2603402554270443885[12] = 0;
   out_2603402554270443885[13] = 0;
   out_2603402554270443885[14] = 0;
   out_2603402554270443885[15] = 0;
   out_2603402554270443885[16] = 0;
   out_2603402554270443885[17] = 0;
   out_2603402554270443885[18] = 0;
   out_2603402554270443885[19] = 0;
   out_2603402554270443885[20] = 1;
   out_2603402554270443885[21] = 0;
   out_2603402554270443885[22] = 0;
   out_2603402554270443885[23] = 0;
   out_2603402554270443885[24] = 0;
   out_2603402554270443885[25] = 0;
   out_2603402554270443885[26] = 0;
   out_2603402554270443885[27] = 0;
   out_2603402554270443885[28] = 0;
   out_2603402554270443885[29] = 0;
   out_2603402554270443885[30] = 1;
   out_2603402554270443885[31] = 0;
   out_2603402554270443885[32] = 0;
   out_2603402554270443885[33] = 0;
   out_2603402554270443885[34] = 0;
   out_2603402554270443885[35] = 0;
   out_2603402554270443885[36] = 0;
   out_2603402554270443885[37] = 0;
   out_2603402554270443885[38] = 0;
   out_2603402554270443885[39] = 0;
   out_2603402554270443885[40] = 1;
   out_2603402554270443885[41] = 0;
   out_2603402554270443885[42] = 0;
   out_2603402554270443885[43] = 0;
   out_2603402554270443885[44] = 0;
   out_2603402554270443885[45] = dt*(stiffness_front*(-state[2] - state[3] + state[7])/(mass*state[1]) + (-stiffness_front - stiffness_rear)*state[5]/(mass*state[4]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[6]/(mass*state[4]));
   out_2603402554270443885[46] = -dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*pow(state[1], 2));
   out_2603402554270443885[47] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_2603402554270443885[48] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_2603402554270443885[49] = dt*((-1 - (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*pow(state[4], 2)))*state[6] - (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*pow(state[4], 2)));
   out_2603402554270443885[50] = dt*(-stiffness_front*state[0] - stiffness_rear*state[0])/(mass*state[4]) + 1;
   out_2603402554270443885[51] = dt*(-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]));
   out_2603402554270443885[52] = dt*stiffness_front*state[0]/(mass*state[1]);
   out_2603402554270443885[53] = -9.8100000000000005*dt;
   out_2603402554270443885[54] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front - pow(center_to_rear, 2)*stiffness_rear)*state[6]/(rotational_inertia*state[4]));
   out_2603402554270443885[55] = -center_to_front*dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*pow(state[1], 2));
   out_2603402554270443885[56] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_2603402554270443885[57] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_2603402554270443885[58] = dt*(-(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*pow(state[4], 2)) - (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*pow(state[4], 2)));
   out_2603402554270443885[59] = dt*(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(rotational_inertia*state[4]);
   out_2603402554270443885[60] = dt*(-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])/(rotational_inertia*state[4]) + 1;
   out_2603402554270443885[61] = center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_2603402554270443885[62] = 0;
   out_2603402554270443885[63] = 0;
   out_2603402554270443885[64] = 0;
   out_2603402554270443885[65] = 0;
   out_2603402554270443885[66] = 0;
   out_2603402554270443885[67] = 0;
   out_2603402554270443885[68] = 0;
   out_2603402554270443885[69] = 0;
   out_2603402554270443885[70] = 1;
   out_2603402554270443885[71] = 0;
   out_2603402554270443885[72] = 0;
   out_2603402554270443885[73] = 0;
   out_2603402554270443885[74] = 0;
   out_2603402554270443885[75] = 0;
   out_2603402554270443885[76] = 0;
   out_2603402554270443885[77] = 0;
   out_2603402554270443885[78] = 0;
   out_2603402554270443885[79] = 0;
   out_2603402554270443885[80] = 1;
}
void h_25(double *state, double *unused, double *out_7483142871930603684) {
   out_7483142871930603684[0] = state[6];
}
void H_25(double *state, double *unused, double *out_1208863944137975522) {
   out_1208863944137975522[0] = 0;
   out_1208863944137975522[1] = 0;
   out_1208863944137975522[2] = 0;
   out_1208863944137975522[3] = 0;
   out_1208863944137975522[4] = 0;
   out_1208863944137975522[5] = 0;
   out_1208863944137975522[6] = 1;
   out_1208863944137975522[7] = 0;
   out_1208863944137975522[8] = 0;
}
void h_24(double *state, double *unused, double *out_5607942348347630047) {
   out_5607942348347630047[0] = state[4];
   out_5607942348347630047[1] = state[5];
}
void H_24(double *state, double *unused, double *out_25779713474104338) {
   out_25779713474104338[0] = 0;
   out_25779713474104338[1] = 0;
   out_25779713474104338[2] = 0;
   out_25779713474104338[3] = 0;
   out_25779713474104338[4] = 1;
   out_25779713474104338[5] = 0;
   out_25779713474104338[6] = 0;
   out_25779713474104338[7] = 0;
   out_25779713474104338[8] = 0;
   out_25779713474104338[9] = 0;
   out_25779713474104338[10] = 0;
   out_25779713474104338[11] = 0;
   out_25779713474104338[12] = 0;
   out_25779713474104338[13] = 0;
   out_25779713474104338[14] = 1;
   out_25779713474104338[15] = 0;
   out_25779713474104338[16] = 0;
   out_25779713474104338[17] = 0;
}
void h_30(double *state, double *unused, double *out_3845693343676581334) {
   out_3845693343676581334[0] = state[4];
}
void H_30(double *state, double *unused, double *out_1079524996994735452) {
   out_1079524996994735452[0] = 0;
   out_1079524996994735452[1] = 0;
   out_1079524996994735452[2] = 0;
   out_1079524996994735452[3] = 0;
   out_1079524996994735452[4] = 1;
   out_1079524996994735452[5] = 0;
   out_1079524996994735452[6] = 0;
   out_1079524996994735452[7] = 0;
   out_1079524996994735452[8] = 0;
}
void h_26(double *state, double *unused, double *out_8847366611337426979) {
   out_8847366611337426979[0] = state[7];
}
void H_26(double *state, double *unused, double *out_2532639374736080702) {
   out_2532639374736080702[0] = 0;
   out_2532639374736080702[1] = 0;
   out_2532639374736080702[2] = 0;
   out_2532639374736080702[3] = 0;
   out_2532639374736080702[4] = 0;
   out_2532639374736080702[5] = 0;
   out_2532639374736080702[6] = 0;
   out_2532639374736080702[7] = 1;
   out_2532639374736080702[8] = 0;
}
void h_27(double *state, double *unused, double *out_7323093963955398614) {
   out_7323093963955398614[0] = state[3];
}
void H_27(double *state, double *unused, double *out_1095238314805689459) {
   out_1095238314805689459[0] = 0;
   out_1095238314805689459[1] = 0;
   out_1095238314805689459[2] = 0;
   out_1095238314805689459[3] = 1;
   out_1095238314805689459[4] = 0;
   out_1095238314805689459[5] = 0;
   out_1095238314805689459[6] = 0;
   out_1095238314805689459[7] = 0;
   out_1095238314805689459[8] = 0;
}
void h_29(double *state, double *unused, double *out_1155979923984264311) {
   out_1155979923984264311[0] = state[1];
}
void H_29(double *state, double *unused, double *out_1589756341309127636) {
   out_1589756341309127636[0] = 0;
   out_1589756341309127636[1] = 1;
   out_1589756341309127636[2] = 0;
   out_1589756341309127636[3] = 0;
   out_1589756341309127636[4] = 0;
   out_1589756341309127636[5] = 0;
   out_1589756341309127636[6] = 0;
   out_1589756341309127636[7] = 0;
   out_1589756341309127636[8] = 0;
}
void h_28(double *state, double *unused, double *out_5021130674020958612) {
   out_5021130674020958612[0] = state[0];
}
void H_28(double *state, double *unused, double *out_7891000058744771066) {
   out_7891000058744771066[0] = 1;
   out_7891000058744771066[1] = 0;
   out_7891000058744771066[2] = 0;
   out_7891000058744771066[3] = 0;
   out_7891000058744771066[4] = 0;
   out_7891000058744771066[5] = 0;
   out_7891000058744771066[6] = 0;
   out_7891000058744771066[7] = 0;
   out_7891000058744771066[8] = 0;
}
void h_31(double *state, double *unused, double *out_3082328551024898747) {
   out_3082328551024898747[0] = state[8];
}
void H_31(double *state, double *unused, double *out_1239509906014935950) {
   out_1239509906014935950[0] = 0;
   out_1239509906014935950[1] = 0;
   out_1239509906014935950[2] = 0;
   out_1239509906014935950[3] = 0;
   out_1239509906014935950[4] = 0;
   out_1239509906014935950[5] = 0;
   out_1239509906014935950[6] = 0;
   out_1239509906014935950[7] = 0;
   out_1239509906014935950[8] = 1;
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
void car_err_fun(double *nom_x, double *delta_x, double *out_6455770263676897448) {
  err_fun(nom_x, delta_x, out_6455770263676897448);
}
void car_inv_err_fun(double *nom_x, double *true_x, double *out_3264339508163218326) {
  inv_err_fun(nom_x, true_x, out_3264339508163218326);
}
void car_H_mod_fun(double *state, double *out_2314116705851516155) {
  H_mod_fun(state, out_2314116705851516155);
}
void car_f_fun(double *state, double dt, double *out_3179221506286947540) {
  f_fun(state,  dt, out_3179221506286947540);
}
void car_F_fun(double *state, double dt, double *out_2603402554270443885) {
  F_fun(state,  dt, out_2603402554270443885);
}
void car_h_25(double *state, double *unused, double *out_7483142871930603684) {
  h_25(state, unused, out_7483142871930603684);
}
void car_H_25(double *state, double *unused, double *out_1208863944137975522) {
  H_25(state, unused, out_1208863944137975522);
}
void car_h_24(double *state, double *unused, double *out_5607942348347630047) {
  h_24(state, unused, out_5607942348347630047);
}
void car_H_24(double *state, double *unused, double *out_25779713474104338) {
  H_24(state, unused, out_25779713474104338);
}
void car_h_30(double *state, double *unused, double *out_3845693343676581334) {
  h_30(state, unused, out_3845693343676581334);
}
void car_H_30(double *state, double *unused, double *out_1079524996994735452) {
  H_30(state, unused, out_1079524996994735452);
}
void car_h_26(double *state, double *unused, double *out_8847366611337426979) {
  h_26(state, unused, out_8847366611337426979);
}
void car_H_26(double *state, double *unused, double *out_2532639374736080702) {
  H_26(state, unused, out_2532639374736080702);
}
void car_h_27(double *state, double *unused, double *out_7323093963955398614) {
  h_27(state, unused, out_7323093963955398614);
}
void car_H_27(double *state, double *unused, double *out_1095238314805689459) {
  H_27(state, unused, out_1095238314805689459);
}
void car_h_29(double *state, double *unused, double *out_1155979923984264311) {
  h_29(state, unused, out_1155979923984264311);
}
void car_H_29(double *state, double *unused, double *out_1589756341309127636) {
  H_29(state, unused, out_1589756341309127636);
}
void car_h_28(double *state, double *unused, double *out_5021130674020958612) {
  h_28(state, unused, out_5021130674020958612);
}
void car_H_28(double *state, double *unused, double *out_7891000058744771066) {
  H_28(state, unused, out_7891000058744771066);
}
void car_h_31(double *state, double *unused, double *out_3082328551024898747) {
  h_31(state, unused, out_3082328551024898747);
}
void car_H_31(double *state, double *unused, double *out_1239509906014935950) {
  H_31(state, unused, out_1239509906014935950);
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
