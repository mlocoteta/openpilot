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
void err_fun(double *nom_x, double *delta_x, double *out_2836153289419609170) {
   out_2836153289419609170[0] = delta_x[0] + nom_x[0];
   out_2836153289419609170[1] = delta_x[1] + nom_x[1];
   out_2836153289419609170[2] = delta_x[2] + nom_x[2];
   out_2836153289419609170[3] = delta_x[3] + nom_x[3];
   out_2836153289419609170[4] = delta_x[4] + nom_x[4];
   out_2836153289419609170[5] = delta_x[5] + nom_x[5];
   out_2836153289419609170[6] = delta_x[6] + nom_x[6];
   out_2836153289419609170[7] = delta_x[7] + nom_x[7];
   out_2836153289419609170[8] = delta_x[8] + nom_x[8];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_2870208396745160425) {
   out_2870208396745160425[0] = -nom_x[0] + true_x[0];
   out_2870208396745160425[1] = -nom_x[1] + true_x[1];
   out_2870208396745160425[2] = -nom_x[2] + true_x[2];
   out_2870208396745160425[3] = -nom_x[3] + true_x[3];
   out_2870208396745160425[4] = -nom_x[4] + true_x[4];
   out_2870208396745160425[5] = -nom_x[5] + true_x[5];
   out_2870208396745160425[6] = -nom_x[6] + true_x[6];
   out_2870208396745160425[7] = -nom_x[7] + true_x[7];
   out_2870208396745160425[8] = -nom_x[8] + true_x[8];
}
void H_mod_fun(double *state, double *out_8399208845157168096) {
   out_8399208845157168096[0] = 1.0;
   out_8399208845157168096[1] = 0.0;
   out_8399208845157168096[2] = 0.0;
   out_8399208845157168096[3] = 0.0;
   out_8399208845157168096[4] = 0.0;
   out_8399208845157168096[5] = 0.0;
   out_8399208845157168096[6] = 0.0;
   out_8399208845157168096[7] = 0.0;
   out_8399208845157168096[8] = 0.0;
   out_8399208845157168096[9] = 0.0;
   out_8399208845157168096[10] = 1.0;
   out_8399208845157168096[11] = 0.0;
   out_8399208845157168096[12] = 0.0;
   out_8399208845157168096[13] = 0.0;
   out_8399208845157168096[14] = 0.0;
   out_8399208845157168096[15] = 0.0;
   out_8399208845157168096[16] = 0.0;
   out_8399208845157168096[17] = 0.0;
   out_8399208845157168096[18] = 0.0;
   out_8399208845157168096[19] = 0.0;
   out_8399208845157168096[20] = 1.0;
   out_8399208845157168096[21] = 0.0;
   out_8399208845157168096[22] = 0.0;
   out_8399208845157168096[23] = 0.0;
   out_8399208845157168096[24] = 0.0;
   out_8399208845157168096[25] = 0.0;
   out_8399208845157168096[26] = 0.0;
   out_8399208845157168096[27] = 0.0;
   out_8399208845157168096[28] = 0.0;
   out_8399208845157168096[29] = 0.0;
   out_8399208845157168096[30] = 1.0;
   out_8399208845157168096[31] = 0.0;
   out_8399208845157168096[32] = 0.0;
   out_8399208845157168096[33] = 0.0;
   out_8399208845157168096[34] = 0.0;
   out_8399208845157168096[35] = 0.0;
   out_8399208845157168096[36] = 0.0;
   out_8399208845157168096[37] = 0.0;
   out_8399208845157168096[38] = 0.0;
   out_8399208845157168096[39] = 0.0;
   out_8399208845157168096[40] = 1.0;
   out_8399208845157168096[41] = 0.0;
   out_8399208845157168096[42] = 0.0;
   out_8399208845157168096[43] = 0.0;
   out_8399208845157168096[44] = 0.0;
   out_8399208845157168096[45] = 0.0;
   out_8399208845157168096[46] = 0.0;
   out_8399208845157168096[47] = 0.0;
   out_8399208845157168096[48] = 0.0;
   out_8399208845157168096[49] = 0.0;
   out_8399208845157168096[50] = 1.0;
   out_8399208845157168096[51] = 0.0;
   out_8399208845157168096[52] = 0.0;
   out_8399208845157168096[53] = 0.0;
   out_8399208845157168096[54] = 0.0;
   out_8399208845157168096[55] = 0.0;
   out_8399208845157168096[56] = 0.0;
   out_8399208845157168096[57] = 0.0;
   out_8399208845157168096[58] = 0.0;
   out_8399208845157168096[59] = 0.0;
   out_8399208845157168096[60] = 1.0;
   out_8399208845157168096[61] = 0.0;
   out_8399208845157168096[62] = 0.0;
   out_8399208845157168096[63] = 0.0;
   out_8399208845157168096[64] = 0.0;
   out_8399208845157168096[65] = 0.0;
   out_8399208845157168096[66] = 0.0;
   out_8399208845157168096[67] = 0.0;
   out_8399208845157168096[68] = 0.0;
   out_8399208845157168096[69] = 0.0;
   out_8399208845157168096[70] = 1.0;
   out_8399208845157168096[71] = 0.0;
   out_8399208845157168096[72] = 0.0;
   out_8399208845157168096[73] = 0.0;
   out_8399208845157168096[74] = 0.0;
   out_8399208845157168096[75] = 0.0;
   out_8399208845157168096[76] = 0.0;
   out_8399208845157168096[77] = 0.0;
   out_8399208845157168096[78] = 0.0;
   out_8399208845157168096[79] = 0.0;
   out_8399208845157168096[80] = 1.0;
}
void f_fun(double *state, double dt, double *out_7838059991381044613) {
   out_7838059991381044613[0] = state[0];
   out_7838059991381044613[1] = state[1];
   out_7838059991381044613[2] = state[2];
   out_7838059991381044613[3] = state[3];
   out_7838059991381044613[4] = state[4];
   out_7838059991381044613[5] = dt*((-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]))*state[6] - 9.8100000000000005*state[8] + stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*state[1]) + (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*state[4])) + state[5];
   out_7838059991381044613[6] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*state[4])) + state[6];
   out_7838059991381044613[7] = state[7];
   out_7838059991381044613[8] = state[8];
}
void F_fun(double *state, double dt, double *out_8646854028547709212) {
   out_8646854028547709212[0] = 1;
   out_8646854028547709212[1] = 0;
   out_8646854028547709212[2] = 0;
   out_8646854028547709212[3] = 0;
   out_8646854028547709212[4] = 0;
   out_8646854028547709212[5] = 0;
   out_8646854028547709212[6] = 0;
   out_8646854028547709212[7] = 0;
   out_8646854028547709212[8] = 0;
   out_8646854028547709212[9] = 0;
   out_8646854028547709212[10] = 1;
   out_8646854028547709212[11] = 0;
   out_8646854028547709212[12] = 0;
   out_8646854028547709212[13] = 0;
   out_8646854028547709212[14] = 0;
   out_8646854028547709212[15] = 0;
   out_8646854028547709212[16] = 0;
   out_8646854028547709212[17] = 0;
   out_8646854028547709212[18] = 0;
   out_8646854028547709212[19] = 0;
   out_8646854028547709212[20] = 1;
   out_8646854028547709212[21] = 0;
   out_8646854028547709212[22] = 0;
   out_8646854028547709212[23] = 0;
   out_8646854028547709212[24] = 0;
   out_8646854028547709212[25] = 0;
   out_8646854028547709212[26] = 0;
   out_8646854028547709212[27] = 0;
   out_8646854028547709212[28] = 0;
   out_8646854028547709212[29] = 0;
   out_8646854028547709212[30] = 1;
   out_8646854028547709212[31] = 0;
   out_8646854028547709212[32] = 0;
   out_8646854028547709212[33] = 0;
   out_8646854028547709212[34] = 0;
   out_8646854028547709212[35] = 0;
   out_8646854028547709212[36] = 0;
   out_8646854028547709212[37] = 0;
   out_8646854028547709212[38] = 0;
   out_8646854028547709212[39] = 0;
   out_8646854028547709212[40] = 1;
   out_8646854028547709212[41] = 0;
   out_8646854028547709212[42] = 0;
   out_8646854028547709212[43] = 0;
   out_8646854028547709212[44] = 0;
   out_8646854028547709212[45] = dt*(stiffness_front*(-state[2] - state[3] + state[7])/(mass*state[1]) + (-stiffness_front - stiffness_rear)*state[5]/(mass*state[4]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[6]/(mass*state[4]));
   out_8646854028547709212[46] = -dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*pow(state[1], 2));
   out_8646854028547709212[47] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_8646854028547709212[48] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_8646854028547709212[49] = dt*((-1 - (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*pow(state[4], 2)))*state[6] - (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*pow(state[4], 2)));
   out_8646854028547709212[50] = dt*(-stiffness_front*state[0] - stiffness_rear*state[0])/(mass*state[4]) + 1;
   out_8646854028547709212[51] = dt*(-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]));
   out_8646854028547709212[52] = dt*stiffness_front*state[0]/(mass*state[1]);
   out_8646854028547709212[53] = -9.8100000000000005*dt;
   out_8646854028547709212[54] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front - pow(center_to_rear, 2)*stiffness_rear)*state[6]/(rotational_inertia*state[4]));
   out_8646854028547709212[55] = -center_to_front*dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*pow(state[1], 2));
   out_8646854028547709212[56] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_8646854028547709212[57] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_8646854028547709212[58] = dt*(-(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*pow(state[4], 2)) - (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*pow(state[4], 2)));
   out_8646854028547709212[59] = dt*(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(rotational_inertia*state[4]);
   out_8646854028547709212[60] = dt*(-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])/(rotational_inertia*state[4]) + 1;
   out_8646854028547709212[61] = center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_8646854028547709212[62] = 0;
   out_8646854028547709212[63] = 0;
   out_8646854028547709212[64] = 0;
   out_8646854028547709212[65] = 0;
   out_8646854028547709212[66] = 0;
   out_8646854028547709212[67] = 0;
   out_8646854028547709212[68] = 0;
   out_8646854028547709212[69] = 0;
   out_8646854028547709212[70] = 1;
   out_8646854028547709212[71] = 0;
   out_8646854028547709212[72] = 0;
   out_8646854028547709212[73] = 0;
   out_8646854028547709212[74] = 0;
   out_8646854028547709212[75] = 0;
   out_8646854028547709212[76] = 0;
   out_8646854028547709212[77] = 0;
   out_8646854028547709212[78] = 0;
   out_8646854028547709212[79] = 0;
   out_8646854028547709212[80] = 1;
}
void h_25(double *state, double *unused, double *out_2264071304797468914) {
   out_2264071304797468914[0] = state[6];
}
void H_25(double *state, double *unused, double *out_6252049907879787684) {
   out_6252049907879787684[0] = 0;
   out_6252049907879787684[1] = 0;
   out_6252049907879787684[2] = 0;
   out_6252049907879787684[3] = 0;
   out_6252049907879787684[4] = 0;
   out_6252049907879787684[5] = 0;
   out_6252049907879787684[6] = 1;
   out_6252049907879787684[7] = 0;
   out_6252049907879787684[8] = 0;
}
void h_24(double *state, double *unused, double *out_5464496516514981941) {
   out_5464496516514981941[0] = state[4];
   out_5464496516514981941[1] = state[5];
}
void H_24(double *state, double *unused, double *out_1431728403223799421) {
   out_1431728403223799421[0] = 0;
   out_1431728403223799421[1] = 0;
   out_1431728403223799421[2] = 0;
   out_1431728403223799421[3] = 0;
   out_1431728403223799421[4] = 1;
   out_1431728403223799421[5] = 0;
   out_1431728403223799421[6] = 0;
   out_1431728403223799421[7] = 0;
   out_1431728403223799421[8] = 0;
   out_1431728403223799421[9] = 0;
   out_1431728403223799421[10] = 0;
   out_1431728403223799421[11] = 0;
   out_1431728403223799421[12] = 0;
   out_1431728403223799421[13] = 0;
   out_1431728403223799421[14] = 1;
   out_1431728403223799421[15] = 0;
   out_1431728403223799421[16] = 0;
   out_1431728403223799421[17] = 0;
}
void h_30(double *state, double *unused, double *out_8419407512091410261) {
   out_8419407512091410261[0] = state[4];
}
void H_30(double *state, double *unused, double *out_6122710960736547614) {
   out_6122710960736547614[0] = 0;
   out_6122710960736547614[1] = 0;
   out_6122710960736547614[2] = 0;
   out_6122710960736547614[3] = 0;
   out_6122710960736547614[4] = 1;
   out_6122710960736547614[5] = 0;
   out_6122710960736547614[6] = 0;
   out_6122710960736547614[7] = 0;
   out_6122710960736547614[8] = 0;
}
void h_26(double *state, double *unused, double *out_3468805347087309985) {
   out_3468805347087309985[0] = state[7];
}
void H_26(double *state, double *unused, double *out_2510546589005731460) {
   out_2510546589005731460[0] = 0;
   out_2510546589005731460[1] = 0;
   out_2510546589005731460[2] = 0;
   out_2510546589005731460[3] = 0;
   out_2510546589005731460[4] = 0;
   out_2510546589005731460[5] = 0;
   out_2510546589005731460[6] = 0;
   out_2510546589005731460[7] = 1;
   out_2510546589005731460[8] = 0;
}
void h_27(double *state, double *unused, double *out_7057486801450440045) {
   out_7057486801450440045[0] = state[3];
}
void H_27(double *state, double *unused, double *out_3947947648936122703) {
   out_3947947648936122703[0] = 0;
   out_3947947648936122703[1] = 0;
   out_3947947648936122703[2] = 0;
   out_3947947648936122703[3] = 1;
   out_3947947648936122703[4] = 0;
   out_3947947648936122703[5] = 0;
   out_3947947648936122703[6] = 0;
   out_3947947648936122703[7] = 0;
   out_3947947648936122703[8] = 0;
}
void h_29(double *state, double *unused, double *out_4801429345782816408) {
   out_4801429345782816408[0] = state[1];
}
void H_29(double *state, double *unused, double *out_6632942305050939798) {
   out_6632942305050939798[0] = 0;
   out_6632942305050939798[1] = 1;
   out_6632942305050939798[2] = 0;
   out_6632942305050939798[3] = 0;
   out_6632942305050939798[4] = 0;
   out_6632942305050939798[5] = 0;
   out_6632942305050939798[6] = 0;
   out_6632942305050939798[7] = 0;
   out_6632942305050939798[8] = 0;
}
void h_28(double *state, double *unused, double *out_6991305190977482559) {
   out_6991305190977482559[0] = state[0];
}
void H_28(double *state, double *unused, double *out_1550543287981409224) {
   out_1550543287981409224[0] = 1;
   out_1550543287981409224[1] = 0;
   out_1550543287981409224[2] = 0;
   out_1550543287981409224[3] = 0;
   out_1550543287981409224[4] = 0;
   out_1550543287981409224[5] = 0;
   out_1550543287981409224[6] = 0;
   out_1550543287981409224[7] = 0;
   out_1550543287981409224[8] = 0;
}
void h_31(double *state, double *unused, double *out_1805869942638907252) {
   out_1805869942638907252[0] = state[8];
}
void H_31(double *state, double *unused, double *out_6282695869756748112) {
   out_6282695869756748112[0] = 0;
   out_6282695869756748112[1] = 0;
   out_6282695869756748112[2] = 0;
   out_6282695869756748112[3] = 0;
   out_6282695869756748112[4] = 0;
   out_6282695869756748112[5] = 0;
   out_6282695869756748112[6] = 0;
   out_6282695869756748112[7] = 0;
   out_6282695869756748112[8] = 1;
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
void car_err_fun(double *nom_x, double *delta_x, double *out_2836153289419609170) {
  err_fun(nom_x, delta_x, out_2836153289419609170);
}
void car_inv_err_fun(double *nom_x, double *true_x, double *out_2870208396745160425) {
  inv_err_fun(nom_x, true_x, out_2870208396745160425);
}
void car_H_mod_fun(double *state, double *out_8399208845157168096) {
  H_mod_fun(state, out_8399208845157168096);
}
void car_f_fun(double *state, double dt, double *out_7838059991381044613) {
  f_fun(state,  dt, out_7838059991381044613);
}
void car_F_fun(double *state, double dt, double *out_8646854028547709212) {
  F_fun(state,  dt, out_8646854028547709212);
}
void car_h_25(double *state, double *unused, double *out_2264071304797468914) {
  h_25(state, unused, out_2264071304797468914);
}
void car_H_25(double *state, double *unused, double *out_6252049907879787684) {
  H_25(state, unused, out_6252049907879787684);
}
void car_h_24(double *state, double *unused, double *out_5464496516514981941) {
  h_24(state, unused, out_5464496516514981941);
}
void car_H_24(double *state, double *unused, double *out_1431728403223799421) {
  H_24(state, unused, out_1431728403223799421);
}
void car_h_30(double *state, double *unused, double *out_8419407512091410261) {
  h_30(state, unused, out_8419407512091410261);
}
void car_H_30(double *state, double *unused, double *out_6122710960736547614) {
  H_30(state, unused, out_6122710960736547614);
}
void car_h_26(double *state, double *unused, double *out_3468805347087309985) {
  h_26(state, unused, out_3468805347087309985);
}
void car_H_26(double *state, double *unused, double *out_2510546589005731460) {
  H_26(state, unused, out_2510546589005731460);
}
void car_h_27(double *state, double *unused, double *out_7057486801450440045) {
  h_27(state, unused, out_7057486801450440045);
}
void car_H_27(double *state, double *unused, double *out_3947947648936122703) {
  H_27(state, unused, out_3947947648936122703);
}
void car_h_29(double *state, double *unused, double *out_4801429345782816408) {
  h_29(state, unused, out_4801429345782816408);
}
void car_H_29(double *state, double *unused, double *out_6632942305050939798) {
  H_29(state, unused, out_6632942305050939798);
}
void car_h_28(double *state, double *unused, double *out_6991305190977482559) {
  h_28(state, unused, out_6991305190977482559);
}
void car_H_28(double *state, double *unused, double *out_1550543287981409224) {
  H_28(state, unused, out_1550543287981409224);
}
void car_h_31(double *state, double *unused, double *out_1805869942638907252) {
  h_31(state, unused, out_1805869942638907252);
}
void car_H_31(double *state, double *unused, double *out_6282695869756748112) {
  H_31(state, unused, out_6282695869756748112);
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
