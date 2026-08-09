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
void err_fun(double *nom_x, double *delta_x, double *out_6251513780499274303) {
   out_6251513780499274303[0] = delta_x[0] + nom_x[0];
   out_6251513780499274303[1] = delta_x[1] + nom_x[1];
   out_6251513780499274303[2] = delta_x[2] + nom_x[2];
   out_6251513780499274303[3] = delta_x[3] + nom_x[3];
   out_6251513780499274303[4] = delta_x[4] + nom_x[4];
   out_6251513780499274303[5] = delta_x[5] + nom_x[5];
   out_6251513780499274303[6] = delta_x[6] + nom_x[6];
   out_6251513780499274303[7] = delta_x[7] + nom_x[7];
   out_6251513780499274303[8] = delta_x[8] + nom_x[8];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_1361283985005059007) {
   out_1361283985005059007[0] = -nom_x[0] + true_x[0];
   out_1361283985005059007[1] = -nom_x[1] + true_x[1];
   out_1361283985005059007[2] = -nom_x[2] + true_x[2];
   out_1361283985005059007[3] = -nom_x[3] + true_x[3];
   out_1361283985005059007[4] = -nom_x[4] + true_x[4];
   out_1361283985005059007[5] = -nom_x[5] + true_x[5];
   out_1361283985005059007[6] = -nom_x[6] + true_x[6];
   out_1361283985005059007[7] = -nom_x[7] + true_x[7];
   out_1361283985005059007[8] = -nom_x[8] + true_x[8];
}
void H_mod_fun(double *state, double *out_3699562487368274414) {
   out_3699562487368274414[0] = 1.0;
   out_3699562487368274414[1] = 0.0;
   out_3699562487368274414[2] = 0.0;
   out_3699562487368274414[3] = 0.0;
   out_3699562487368274414[4] = 0.0;
   out_3699562487368274414[5] = 0.0;
   out_3699562487368274414[6] = 0.0;
   out_3699562487368274414[7] = 0.0;
   out_3699562487368274414[8] = 0.0;
   out_3699562487368274414[9] = 0.0;
   out_3699562487368274414[10] = 1.0;
   out_3699562487368274414[11] = 0.0;
   out_3699562487368274414[12] = 0.0;
   out_3699562487368274414[13] = 0.0;
   out_3699562487368274414[14] = 0.0;
   out_3699562487368274414[15] = 0.0;
   out_3699562487368274414[16] = 0.0;
   out_3699562487368274414[17] = 0.0;
   out_3699562487368274414[18] = 0.0;
   out_3699562487368274414[19] = 0.0;
   out_3699562487368274414[20] = 1.0;
   out_3699562487368274414[21] = 0.0;
   out_3699562487368274414[22] = 0.0;
   out_3699562487368274414[23] = 0.0;
   out_3699562487368274414[24] = 0.0;
   out_3699562487368274414[25] = 0.0;
   out_3699562487368274414[26] = 0.0;
   out_3699562487368274414[27] = 0.0;
   out_3699562487368274414[28] = 0.0;
   out_3699562487368274414[29] = 0.0;
   out_3699562487368274414[30] = 1.0;
   out_3699562487368274414[31] = 0.0;
   out_3699562487368274414[32] = 0.0;
   out_3699562487368274414[33] = 0.0;
   out_3699562487368274414[34] = 0.0;
   out_3699562487368274414[35] = 0.0;
   out_3699562487368274414[36] = 0.0;
   out_3699562487368274414[37] = 0.0;
   out_3699562487368274414[38] = 0.0;
   out_3699562487368274414[39] = 0.0;
   out_3699562487368274414[40] = 1.0;
   out_3699562487368274414[41] = 0.0;
   out_3699562487368274414[42] = 0.0;
   out_3699562487368274414[43] = 0.0;
   out_3699562487368274414[44] = 0.0;
   out_3699562487368274414[45] = 0.0;
   out_3699562487368274414[46] = 0.0;
   out_3699562487368274414[47] = 0.0;
   out_3699562487368274414[48] = 0.0;
   out_3699562487368274414[49] = 0.0;
   out_3699562487368274414[50] = 1.0;
   out_3699562487368274414[51] = 0.0;
   out_3699562487368274414[52] = 0.0;
   out_3699562487368274414[53] = 0.0;
   out_3699562487368274414[54] = 0.0;
   out_3699562487368274414[55] = 0.0;
   out_3699562487368274414[56] = 0.0;
   out_3699562487368274414[57] = 0.0;
   out_3699562487368274414[58] = 0.0;
   out_3699562487368274414[59] = 0.0;
   out_3699562487368274414[60] = 1.0;
   out_3699562487368274414[61] = 0.0;
   out_3699562487368274414[62] = 0.0;
   out_3699562487368274414[63] = 0.0;
   out_3699562487368274414[64] = 0.0;
   out_3699562487368274414[65] = 0.0;
   out_3699562487368274414[66] = 0.0;
   out_3699562487368274414[67] = 0.0;
   out_3699562487368274414[68] = 0.0;
   out_3699562487368274414[69] = 0.0;
   out_3699562487368274414[70] = 1.0;
   out_3699562487368274414[71] = 0.0;
   out_3699562487368274414[72] = 0.0;
   out_3699562487368274414[73] = 0.0;
   out_3699562487368274414[74] = 0.0;
   out_3699562487368274414[75] = 0.0;
   out_3699562487368274414[76] = 0.0;
   out_3699562487368274414[77] = 0.0;
   out_3699562487368274414[78] = 0.0;
   out_3699562487368274414[79] = 0.0;
   out_3699562487368274414[80] = 1.0;
}
void f_fun(double *state, double dt, double *out_1113205683479280207) {
   out_1113205683479280207[0] = state[0];
   out_1113205683479280207[1] = state[1];
   out_1113205683479280207[2] = state[2];
   out_1113205683479280207[3] = state[3];
   out_1113205683479280207[4] = state[4];
   out_1113205683479280207[5] = dt*((-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]))*state[6] - 9.8100000000000005*state[8] + stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*state[1]) + (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*state[4])) + state[5];
   out_1113205683479280207[6] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*state[4])) + state[6];
   out_1113205683479280207[7] = state[7];
   out_1113205683479280207[8] = state[8];
}
void F_fun(double *state, double dt, double *out_2198054725359611149) {
   out_2198054725359611149[0] = 1;
   out_2198054725359611149[1] = 0;
   out_2198054725359611149[2] = 0;
   out_2198054725359611149[3] = 0;
   out_2198054725359611149[4] = 0;
   out_2198054725359611149[5] = 0;
   out_2198054725359611149[6] = 0;
   out_2198054725359611149[7] = 0;
   out_2198054725359611149[8] = 0;
   out_2198054725359611149[9] = 0;
   out_2198054725359611149[10] = 1;
   out_2198054725359611149[11] = 0;
   out_2198054725359611149[12] = 0;
   out_2198054725359611149[13] = 0;
   out_2198054725359611149[14] = 0;
   out_2198054725359611149[15] = 0;
   out_2198054725359611149[16] = 0;
   out_2198054725359611149[17] = 0;
   out_2198054725359611149[18] = 0;
   out_2198054725359611149[19] = 0;
   out_2198054725359611149[20] = 1;
   out_2198054725359611149[21] = 0;
   out_2198054725359611149[22] = 0;
   out_2198054725359611149[23] = 0;
   out_2198054725359611149[24] = 0;
   out_2198054725359611149[25] = 0;
   out_2198054725359611149[26] = 0;
   out_2198054725359611149[27] = 0;
   out_2198054725359611149[28] = 0;
   out_2198054725359611149[29] = 0;
   out_2198054725359611149[30] = 1;
   out_2198054725359611149[31] = 0;
   out_2198054725359611149[32] = 0;
   out_2198054725359611149[33] = 0;
   out_2198054725359611149[34] = 0;
   out_2198054725359611149[35] = 0;
   out_2198054725359611149[36] = 0;
   out_2198054725359611149[37] = 0;
   out_2198054725359611149[38] = 0;
   out_2198054725359611149[39] = 0;
   out_2198054725359611149[40] = 1;
   out_2198054725359611149[41] = 0;
   out_2198054725359611149[42] = 0;
   out_2198054725359611149[43] = 0;
   out_2198054725359611149[44] = 0;
   out_2198054725359611149[45] = dt*(stiffness_front*(-state[2] - state[3] + state[7])/(mass*state[1]) + (-stiffness_front - stiffness_rear)*state[5]/(mass*state[4]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[6]/(mass*state[4]));
   out_2198054725359611149[46] = -dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*pow(state[1], 2));
   out_2198054725359611149[47] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_2198054725359611149[48] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_2198054725359611149[49] = dt*((-1 - (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*pow(state[4], 2)))*state[6] - (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*pow(state[4], 2)));
   out_2198054725359611149[50] = dt*(-stiffness_front*state[0] - stiffness_rear*state[0])/(mass*state[4]) + 1;
   out_2198054725359611149[51] = dt*(-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]));
   out_2198054725359611149[52] = dt*stiffness_front*state[0]/(mass*state[1]);
   out_2198054725359611149[53] = -9.8100000000000005*dt;
   out_2198054725359611149[54] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front - pow(center_to_rear, 2)*stiffness_rear)*state[6]/(rotational_inertia*state[4]));
   out_2198054725359611149[55] = -center_to_front*dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*pow(state[1], 2));
   out_2198054725359611149[56] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_2198054725359611149[57] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_2198054725359611149[58] = dt*(-(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*pow(state[4], 2)) - (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*pow(state[4], 2)));
   out_2198054725359611149[59] = dt*(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(rotational_inertia*state[4]);
   out_2198054725359611149[60] = dt*(-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])/(rotational_inertia*state[4]) + 1;
   out_2198054725359611149[61] = center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_2198054725359611149[62] = 0;
   out_2198054725359611149[63] = 0;
   out_2198054725359611149[64] = 0;
   out_2198054725359611149[65] = 0;
   out_2198054725359611149[66] = 0;
   out_2198054725359611149[67] = 0;
   out_2198054725359611149[68] = 0;
   out_2198054725359611149[69] = 0;
   out_2198054725359611149[70] = 1;
   out_2198054725359611149[71] = 0;
   out_2198054725359611149[72] = 0;
   out_2198054725359611149[73] = 0;
   out_2198054725359611149[74] = 0;
   out_2198054725359611149[75] = 0;
   out_2198054725359611149[76] = 0;
   out_2198054725359611149[77] = 0;
   out_2198054725359611149[78] = 0;
   out_2198054725359611149[79] = 0;
   out_2198054725359611149[80] = 1;
}
void h_25(double *state, double *unused, double *out_2775617380616102557) {
   out_2775617380616102557[0] = state[6];
}
void H_25(double *state, double *unused, double *out_5493625738543962823) {
   out_5493625738543962823[0] = 0;
   out_5493625738543962823[1] = 0;
   out_5493625738543962823[2] = 0;
   out_5493625738543962823[3] = 0;
   out_5493625738543962823[4] = 0;
   out_5493625738543962823[5] = 0;
   out_5493625738543962823[6] = 1;
   out_5493625738543962823[7] = 0;
   out_5493625738543962823[8] = 0;
}
void h_24(double *state, double *unused, double *out_6646117502185914860) {
   out_6646117502185914860[0] = state[4];
   out_6646117502185914860[1] = state[5];
}
void H_24(double *state, double *unused, double *out_3267917954565094261) {
   out_3267917954565094261[0] = 0;
   out_3267917954565094261[1] = 0;
   out_3267917954565094261[2] = 0;
   out_3267917954565094261[3] = 0;
   out_3267917954565094261[4] = 1;
   out_3267917954565094261[5] = 0;
   out_3267917954565094261[6] = 0;
   out_3267917954565094261[7] = 0;
   out_3267917954565094261[8] = 0;
   out_3267917954565094261[9] = 0;
   out_3267917954565094261[10] = 0;
   out_3267917954565094261[11] = 0;
   out_3267917954565094261[12] = 0;
   out_3267917954565094261[13] = 0;
   out_3267917954565094261[14] = 1;
   out_3267917954565094261[15] = 0;
   out_3267917954565094261[16] = 0;
   out_3267917954565094261[17] = 0;
}
void h_30(double *state, double *unused, double *out_6519293463111227465) {
   out_6519293463111227465[0] = state[4];
}
void H_30(double *state, double *unused, double *out_1423064602947653932) {
   out_1423064602947653932[0] = 0;
   out_1423064602947653932[1] = 0;
   out_1423064602947653932[2] = 0;
   out_1423064602947653932[3] = 0;
   out_1423064602947653932[4] = 1;
   out_1423064602947653932[5] = 0;
   out_1423064602947653932[6] = 0;
   out_1423064602947653932[7] = 0;
   out_1423064602947653932[8] = 0;
}
void h_26(double *state, double *unused, double *out_7122609347787704982) {
   out_7122609347787704982[0] = state[7];
}
void H_26(double *state, double *unused, double *out_9211615016291532569) {
   out_9211615016291532569[0] = 0;
   out_9211615016291532569[1] = 0;
   out_9211615016291532569[2] = 0;
   out_9211615016291532569[3] = 0;
   out_9211615016291532569[4] = 0;
   out_9211615016291532569[5] = 0;
   out_9211615016291532569[6] = 0;
   out_9211615016291532569[7] = 1;
   out_9211615016291532569[8] = 0;
}
void h_27(double *state, double *unused, double *out_7737997378297395789) {
   out_7737997378297395789[0] = state[3];
}
void H_27(double *state, double *unused, double *out_7797727997487627804) {
   out_7797727997487627804[0] = 0;
   out_7797727997487627804[1] = 0;
   out_7797727997487627804[2] = 0;
   out_7797727997487627804[3] = 1;
   out_7797727997487627804[4] = 0;
   out_7797727997487627804[5] = 0;
   out_7797727997487627804[6] = 0;
   out_7797727997487627804[7] = 0;
   out_7797727997487627804[8] = 0;
}
void h_29(double *state, double *unused, double *out_3746027739128576800) {
   out_3746027739128576800[0] = state[1];
}
void H_29(double *state, double *unused, double *out_5112733341372810709) {
   out_5112733341372810709[0] = 0;
   out_5112733341372810709[1] = 1;
   out_5112733341372810709[2] = 0;
   out_5112733341372810709[3] = 0;
   out_5112733341372810709[4] = 0;
   out_5112733341372810709[5] = 0;
   out_5112733341372810709[6] = 0;
   out_5112733341372810709[7] = 0;
   out_5112733341372810709[8] = 0;
}
void h_28(double *state, double *unused, double *out_8104341374603458176) {
   out_8104341374603458176[0] = state[0];
}
void H_28(double *state, double *unused, double *out_3149103069807484458) {
   out_3149103069807484458[0] = 1;
   out_3149103069807484458[1] = 0;
   out_3149103069807484458[2] = 0;
   out_3149103069807484458[3] = 0;
   out_3149103069807484458[4] = 0;
   out_3149103069807484458[5] = 0;
   out_3149103069807484458[6] = 0;
   out_3149103069807484458[7] = 0;
   out_3149103069807484458[8] = 0;
}
void h_31(double *state, double *unused, double *out_5721043300647637435) {
   out_5721043300647637435[0] = state[8];
}
void H_31(double *state, double *unused, double *out_5462979776667002395) {
   out_5462979776667002395[0] = 0;
   out_5462979776667002395[1] = 0;
   out_5462979776667002395[2] = 0;
   out_5462979776667002395[3] = 0;
   out_5462979776667002395[4] = 0;
   out_5462979776667002395[5] = 0;
   out_5462979776667002395[6] = 0;
   out_5462979776667002395[7] = 0;
   out_5462979776667002395[8] = 1;
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
void car_err_fun(double *nom_x, double *delta_x, double *out_6251513780499274303) {
  err_fun(nom_x, delta_x, out_6251513780499274303);
}
void car_inv_err_fun(double *nom_x, double *true_x, double *out_1361283985005059007) {
  inv_err_fun(nom_x, true_x, out_1361283985005059007);
}
void car_H_mod_fun(double *state, double *out_3699562487368274414) {
  H_mod_fun(state, out_3699562487368274414);
}
void car_f_fun(double *state, double dt, double *out_1113205683479280207) {
  f_fun(state,  dt, out_1113205683479280207);
}
void car_F_fun(double *state, double dt, double *out_2198054725359611149) {
  F_fun(state,  dt, out_2198054725359611149);
}
void car_h_25(double *state, double *unused, double *out_2775617380616102557) {
  h_25(state, unused, out_2775617380616102557);
}
void car_H_25(double *state, double *unused, double *out_5493625738543962823) {
  H_25(state, unused, out_5493625738543962823);
}
void car_h_24(double *state, double *unused, double *out_6646117502185914860) {
  h_24(state, unused, out_6646117502185914860);
}
void car_H_24(double *state, double *unused, double *out_3267917954565094261) {
  H_24(state, unused, out_3267917954565094261);
}
void car_h_30(double *state, double *unused, double *out_6519293463111227465) {
  h_30(state, unused, out_6519293463111227465);
}
void car_H_30(double *state, double *unused, double *out_1423064602947653932) {
  H_30(state, unused, out_1423064602947653932);
}
void car_h_26(double *state, double *unused, double *out_7122609347787704982) {
  h_26(state, unused, out_7122609347787704982);
}
void car_H_26(double *state, double *unused, double *out_9211615016291532569) {
  H_26(state, unused, out_9211615016291532569);
}
void car_h_27(double *state, double *unused, double *out_7737997378297395789) {
  h_27(state, unused, out_7737997378297395789);
}
void car_H_27(double *state, double *unused, double *out_7797727997487627804) {
  H_27(state, unused, out_7797727997487627804);
}
void car_h_29(double *state, double *unused, double *out_3746027739128576800) {
  h_29(state, unused, out_3746027739128576800);
}
void car_H_29(double *state, double *unused, double *out_5112733341372810709) {
  H_29(state, unused, out_5112733341372810709);
}
void car_h_28(double *state, double *unused, double *out_8104341374603458176) {
  h_28(state, unused, out_8104341374603458176);
}
void car_H_28(double *state, double *unused, double *out_3149103069807484458) {
  H_28(state, unused, out_3149103069807484458);
}
void car_h_31(double *state, double *unused, double *out_5721043300647637435) {
  h_31(state, unused, out_5721043300647637435);
}
void car_H_31(double *state, double *unused, double *out_5462979776667002395) {
  H_31(state, unused, out_5462979776667002395);
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
