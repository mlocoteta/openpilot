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
void err_fun(double *nom_x, double *delta_x, double *out_6680589116319572635) {
   out_6680589116319572635[0] = delta_x[0] + nom_x[0];
   out_6680589116319572635[1] = delta_x[1] + nom_x[1];
   out_6680589116319572635[2] = delta_x[2] + nom_x[2];
   out_6680589116319572635[3] = delta_x[3] + nom_x[3];
   out_6680589116319572635[4] = delta_x[4] + nom_x[4];
   out_6680589116319572635[5] = delta_x[5] + nom_x[5];
   out_6680589116319572635[6] = delta_x[6] + nom_x[6];
   out_6680589116319572635[7] = delta_x[7] + nom_x[7];
   out_6680589116319572635[8] = delta_x[8] + nom_x[8];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_1421263034200107343) {
   out_1421263034200107343[0] = -nom_x[0] + true_x[0];
   out_1421263034200107343[1] = -nom_x[1] + true_x[1];
   out_1421263034200107343[2] = -nom_x[2] + true_x[2];
   out_1421263034200107343[3] = -nom_x[3] + true_x[3];
   out_1421263034200107343[4] = -nom_x[4] + true_x[4];
   out_1421263034200107343[5] = -nom_x[5] + true_x[5];
   out_1421263034200107343[6] = -nom_x[6] + true_x[6];
   out_1421263034200107343[7] = -nom_x[7] + true_x[7];
   out_1421263034200107343[8] = -nom_x[8] + true_x[8];
}
void H_mod_fun(double *state, double *out_8968580721052785900) {
   out_8968580721052785900[0] = 1.0;
   out_8968580721052785900[1] = 0.0;
   out_8968580721052785900[2] = 0.0;
   out_8968580721052785900[3] = 0.0;
   out_8968580721052785900[4] = 0.0;
   out_8968580721052785900[5] = 0.0;
   out_8968580721052785900[6] = 0.0;
   out_8968580721052785900[7] = 0.0;
   out_8968580721052785900[8] = 0.0;
   out_8968580721052785900[9] = 0.0;
   out_8968580721052785900[10] = 1.0;
   out_8968580721052785900[11] = 0.0;
   out_8968580721052785900[12] = 0.0;
   out_8968580721052785900[13] = 0.0;
   out_8968580721052785900[14] = 0.0;
   out_8968580721052785900[15] = 0.0;
   out_8968580721052785900[16] = 0.0;
   out_8968580721052785900[17] = 0.0;
   out_8968580721052785900[18] = 0.0;
   out_8968580721052785900[19] = 0.0;
   out_8968580721052785900[20] = 1.0;
   out_8968580721052785900[21] = 0.0;
   out_8968580721052785900[22] = 0.0;
   out_8968580721052785900[23] = 0.0;
   out_8968580721052785900[24] = 0.0;
   out_8968580721052785900[25] = 0.0;
   out_8968580721052785900[26] = 0.0;
   out_8968580721052785900[27] = 0.0;
   out_8968580721052785900[28] = 0.0;
   out_8968580721052785900[29] = 0.0;
   out_8968580721052785900[30] = 1.0;
   out_8968580721052785900[31] = 0.0;
   out_8968580721052785900[32] = 0.0;
   out_8968580721052785900[33] = 0.0;
   out_8968580721052785900[34] = 0.0;
   out_8968580721052785900[35] = 0.0;
   out_8968580721052785900[36] = 0.0;
   out_8968580721052785900[37] = 0.0;
   out_8968580721052785900[38] = 0.0;
   out_8968580721052785900[39] = 0.0;
   out_8968580721052785900[40] = 1.0;
   out_8968580721052785900[41] = 0.0;
   out_8968580721052785900[42] = 0.0;
   out_8968580721052785900[43] = 0.0;
   out_8968580721052785900[44] = 0.0;
   out_8968580721052785900[45] = 0.0;
   out_8968580721052785900[46] = 0.0;
   out_8968580721052785900[47] = 0.0;
   out_8968580721052785900[48] = 0.0;
   out_8968580721052785900[49] = 0.0;
   out_8968580721052785900[50] = 1.0;
   out_8968580721052785900[51] = 0.0;
   out_8968580721052785900[52] = 0.0;
   out_8968580721052785900[53] = 0.0;
   out_8968580721052785900[54] = 0.0;
   out_8968580721052785900[55] = 0.0;
   out_8968580721052785900[56] = 0.0;
   out_8968580721052785900[57] = 0.0;
   out_8968580721052785900[58] = 0.0;
   out_8968580721052785900[59] = 0.0;
   out_8968580721052785900[60] = 1.0;
   out_8968580721052785900[61] = 0.0;
   out_8968580721052785900[62] = 0.0;
   out_8968580721052785900[63] = 0.0;
   out_8968580721052785900[64] = 0.0;
   out_8968580721052785900[65] = 0.0;
   out_8968580721052785900[66] = 0.0;
   out_8968580721052785900[67] = 0.0;
   out_8968580721052785900[68] = 0.0;
   out_8968580721052785900[69] = 0.0;
   out_8968580721052785900[70] = 1.0;
   out_8968580721052785900[71] = 0.0;
   out_8968580721052785900[72] = 0.0;
   out_8968580721052785900[73] = 0.0;
   out_8968580721052785900[74] = 0.0;
   out_8968580721052785900[75] = 0.0;
   out_8968580721052785900[76] = 0.0;
   out_8968580721052785900[77] = 0.0;
   out_8968580721052785900[78] = 0.0;
   out_8968580721052785900[79] = 0.0;
   out_8968580721052785900[80] = 1.0;
}
void f_fun(double *state, double dt, double *out_3852536059217665062) {
   out_3852536059217665062[0] = state[0];
   out_3852536059217665062[1] = state[1];
   out_3852536059217665062[2] = state[2];
   out_3852536059217665062[3] = state[3];
   out_3852536059217665062[4] = state[4];
   out_3852536059217665062[5] = dt*((-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]))*state[6] - 9.8100000000000005*state[8] + stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*state[1]) + (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*state[4])) + state[5];
   out_3852536059217665062[6] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*state[4])) + state[6];
   out_3852536059217665062[7] = state[7];
   out_3852536059217665062[8] = state[8];
}
void F_fun(double *state, double dt, double *out_7217781527381652799) {
   out_7217781527381652799[0] = 1;
   out_7217781527381652799[1] = 0;
   out_7217781527381652799[2] = 0;
   out_7217781527381652799[3] = 0;
   out_7217781527381652799[4] = 0;
   out_7217781527381652799[5] = 0;
   out_7217781527381652799[6] = 0;
   out_7217781527381652799[7] = 0;
   out_7217781527381652799[8] = 0;
   out_7217781527381652799[9] = 0;
   out_7217781527381652799[10] = 1;
   out_7217781527381652799[11] = 0;
   out_7217781527381652799[12] = 0;
   out_7217781527381652799[13] = 0;
   out_7217781527381652799[14] = 0;
   out_7217781527381652799[15] = 0;
   out_7217781527381652799[16] = 0;
   out_7217781527381652799[17] = 0;
   out_7217781527381652799[18] = 0;
   out_7217781527381652799[19] = 0;
   out_7217781527381652799[20] = 1;
   out_7217781527381652799[21] = 0;
   out_7217781527381652799[22] = 0;
   out_7217781527381652799[23] = 0;
   out_7217781527381652799[24] = 0;
   out_7217781527381652799[25] = 0;
   out_7217781527381652799[26] = 0;
   out_7217781527381652799[27] = 0;
   out_7217781527381652799[28] = 0;
   out_7217781527381652799[29] = 0;
   out_7217781527381652799[30] = 1;
   out_7217781527381652799[31] = 0;
   out_7217781527381652799[32] = 0;
   out_7217781527381652799[33] = 0;
   out_7217781527381652799[34] = 0;
   out_7217781527381652799[35] = 0;
   out_7217781527381652799[36] = 0;
   out_7217781527381652799[37] = 0;
   out_7217781527381652799[38] = 0;
   out_7217781527381652799[39] = 0;
   out_7217781527381652799[40] = 1;
   out_7217781527381652799[41] = 0;
   out_7217781527381652799[42] = 0;
   out_7217781527381652799[43] = 0;
   out_7217781527381652799[44] = 0;
   out_7217781527381652799[45] = dt*(stiffness_front*(-state[2] - state[3] + state[7])/(mass*state[1]) + (-stiffness_front - stiffness_rear)*state[5]/(mass*state[4]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[6]/(mass*state[4]));
   out_7217781527381652799[46] = -dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*pow(state[1], 2));
   out_7217781527381652799[47] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_7217781527381652799[48] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_7217781527381652799[49] = dt*((-1 - (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*pow(state[4], 2)))*state[6] - (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*pow(state[4], 2)));
   out_7217781527381652799[50] = dt*(-stiffness_front*state[0] - stiffness_rear*state[0])/(mass*state[4]) + 1;
   out_7217781527381652799[51] = dt*(-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]));
   out_7217781527381652799[52] = dt*stiffness_front*state[0]/(mass*state[1]);
   out_7217781527381652799[53] = -9.8100000000000005*dt;
   out_7217781527381652799[54] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front - pow(center_to_rear, 2)*stiffness_rear)*state[6]/(rotational_inertia*state[4]));
   out_7217781527381652799[55] = -center_to_front*dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*pow(state[1], 2));
   out_7217781527381652799[56] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_7217781527381652799[57] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_7217781527381652799[58] = dt*(-(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*pow(state[4], 2)) - (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*pow(state[4], 2)));
   out_7217781527381652799[59] = dt*(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(rotational_inertia*state[4]);
   out_7217781527381652799[60] = dt*(-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])/(rotational_inertia*state[4]) + 1;
   out_7217781527381652799[61] = center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_7217781527381652799[62] = 0;
   out_7217781527381652799[63] = 0;
   out_7217781527381652799[64] = 0;
   out_7217781527381652799[65] = 0;
   out_7217781527381652799[66] = 0;
   out_7217781527381652799[67] = 0;
   out_7217781527381652799[68] = 0;
   out_7217781527381652799[69] = 0;
   out_7217781527381652799[70] = 1;
   out_7217781527381652799[71] = 0;
   out_7217781527381652799[72] = 0;
   out_7217781527381652799[73] = 0;
   out_7217781527381652799[74] = 0;
   out_7217781527381652799[75] = 0;
   out_7217781527381652799[76] = 0;
   out_7217781527381652799[77] = 0;
   out_7217781527381652799[78] = 0;
   out_7217781527381652799[79] = 0;
   out_7217781527381652799[80] = 1;
}
void h_25(double *state, double *unused, double *out_2838193808077509293) {
   out_2838193808077509293[0] = state[6];
}
void H_25(double *state, double *unused, double *out_4085073539734055094) {
   out_4085073539734055094[0] = 0;
   out_4085073539734055094[1] = 0;
   out_4085073539734055094[2] = 0;
   out_4085073539734055094[3] = 0;
   out_4085073539734055094[4] = 0;
   out_4085073539734055094[5] = 0;
   out_4085073539734055094[6] = 1;
   out_4085073539734055094[7] = 0;
   out_4085073539734055094[8] = 0;
}
void h_24(double *state, double *unused, double *out_7378709950093750440) {
   out_7378709950093750440[0] = state[4];
   out_7378709950093750440[1] = state[5];
}
void H_24(double *state, double *unused, double *out_2001100279119417225) {
   out_2001100279119417225[0] = 0;
   out_2001100279119417225[1] = 0;
   out_2001100279119417225[2] = 0;
   out_2001100279119417225[3] = 0;
   out_2001100279119417225[4] = 1;
   out_2001100279119417225[5] = 0;
   out_2001100279119417225[6] = 0;
   out_2001100279119417225[7] = 0;
   out_2001100279119417225[8] = 0;
   out_2001100279119417225[9] = 0;
   out_2001100279119417225[10] = 0;
   out_2001100279119417225[11] = 0;
   out_2001100279119417225[12] = 0;
   out_2001100279119417225[13] = 0;
   out_2001100279119417225[14] = 1;
   out_2001100279119417225[15] = 0;
   out_2001100279119417225[16] = 0;
   out_2001100279119417225[17] = 0;
}
void h_30(double *state, double *unused, double *out_6475643336331531643) {
   out_6475643336331531643[0] = state[4];
}
void H_30(double *state, double *unused, double *out_4214412486877295164) {
   out_4214412486877295164[0] = 0;
   out_4214412486877295164[1] = 0;
   out_4214412486877295164[2] = 0;
   out_4214412486877295164[3] = 0;
   out_4214412486877295164[4] = 1;
   out_4214412486877295164[5] = 0;
   out_4214412486877295164[6] = 0;
   out_4214412486877295164[7] = 0;
   out_4214412486877295164[8] = 0;
}
void h_26(double *state, double *unused, double *out_8554827447728949957) {
   out_8554827447728949957[0] = state[7];
}
void H_26(double *state, double *unused, double *out_3428219475623743190) {
   out_3428219475623743190[0] = 0;
   out_3428219475623743190[1] = 0;
   out_3428219475623743190[2] = 0;
   out_3428219475623743190[3] = 0;
   out_3428219475623743190[4] = 0;
   out_3428219475623743190[5] = 0;
   out_3428219475623743190[6] = 0;
   out_3428219475623743190[7] = 1;
   out_3428219475623743190[8] = 0;
}
void h_27(double *state, double *unused, double *out_1670450007001367556) {
   out_1670450007001367556[0] = state[3];
}
void H_27(double *state, double *unused, double *out_6389175798677720075) {
   out_6389175798677720075[0] = 0;
   out_6389175798677720075[1] = 0;
   out_6389175798677720075[2] = 0;
   out_6389175798677720075[3] = 1;
   out_6389175798677720075[4] = 0;
   out_6389175798677720075[5] = 0;
   out_6389175798677720075[6] = 0;
   out_6389175798677720075[7] = 0;
   out_6389175798677720075[8] = 0;
}
void h_29(double *state, double *unused, double *out_6969427469717174328) {
   out_6969427469717174328[0] = state[1];
}
void H_29(double *state, double *unused, double *out_3704181142562902980) {
   out_3704181142562902980[0] = 0;
   out_3704181142562902980[1] = 1;
   out_3704181142562902980[2] = 0;
   out_3704181142562902980[3] = 0;
   out_3704181142562902980[4] = 0;
   out_3704181142562902980[5] = 0;
   out_3704181142562902980[6] = 0;
   out_3704181142562902980[7] = 0;
   out_3704181142562902980[8] = 0;
}
void h_28(double *state, double *unused, double *out_1142102096268485827) {
   out_1142102096268485827[0] = state[0];
}
void H_28(double *state, double *unused, double *out_1740550870997576729) {
   out_1740550870997576729[0] = 1;
   out_1740550870997576729[1] = 0;
   out_1740550870997576729[2] = 0;
   out_1740550870997576729[3] = 0;
   out_1740550870997576729[4] = 0;
   out_1740550870997576729[5] = 0;
   out_1740550870997576729[6] = 0;
   out_1740550870997576729[7] = 0;
   out_1740550870997576729[8] = 0;
}
void h_31(double *state, double *unused, double *out_4288825200706392460) {
   out_4288825200706392460[0] = state[8];
}
void H_31(double *state, double *unused, double *out_4054427577857094666) {
   out_4054427577857094666[0] = 0;
   out_4054427577857094666[1] = 0;
   out_4054427577857094666[2] = 0;
   out_4054427577857094666[3] = 0;
   out_4054427577857094666[4] = 0;
   out_4054427577857094666[5] = 0;
   out_4054427577857094666[6] = 0;
   out_4054427577857094666[7] = 0;
   out_4054427577857094666[8] = 1;
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
void car_err_fun(double *nom_x, double *delta_x, double *out_6680589116319572635) {
  err_fun(nom_x, delta_x, out_6680589116319572635);
}
void car_inv_err_fun(double *nom_x, double *true_x, double *out_1421263034200107343) {
  inv_err_fun(nom_x, true_x, out_1421263034200107343);
}
void car_H_mod_fun(double *state, double *out_8968580721052785900) {
  H_mod_fun(state, out_8968580721052785900);
}
void car_f_fun(double *state, double dt, double *out_3852536059217665062) {
  f_fun(state,  dt, out_3852536059217665062);
}
void car_F_fun(double *state, double dt, double *out_7217781527381652799) {
  F_fun(state,  dt, out_7217781527381652799);
}
void car_h_25(double *state, double *unused, double *out_2838193808077509293) {
  h_25(state, unused, out_2838193808077509293);
}
void car_H_25(double *state, double *unused, double *out_4085073539734055094) {
  H_25(state, unused, out_4085073539734055094);
}
void car_h_24(double *state, double *unused, double *out_7378709950093750440) {
  h_24(state, unused, out_7378709950093750440);
}
void car_H_24(double *state, double *unused, double *out_2001100279119417225) {
  H_24(state, unused, out_2001100279119417225);
}
void car_h_30(double *state, double *unused, double *out_6475643336331531643) {
  h_30(state, unused, out_6475643336331531643);
}
void car_H_30(double *state, double *unused, double *out_4214412486877295164) {
  H_30(state, unused, out_4214412486877295164);
}
void car_h_26(double *state, double *unused, double *out_8554827447728949957) {
  h_26(state, unused, out_8554827447728949957);
}
void car_H_26(double *state, double *unused, double *out_3428219475623743190) {
  H_26(state, unused, out_3428219475623743190);
}
void car_h_27(double *state, double *unused, double *out_1670450007001367556) {
  h_27(state, unused, out_1670450007001367556);
}
void car_H_27(double *state, double *unused, double *out_6389175798677720075) {
  H_27(state, unused, out_6389175798677720075);
}
void car_h_29(double *state, double *unused, double *out_6969427469717174328) {
  h_29(state, unused, out_6969427469717174328);
}
void car_H_29(double *state, double *unused, double *out_3704181142562902980) {
  H_29(state, unused, out_3704181142562902980);
}
void car_h_28(double *state, double *unused, double *out_1142102096268485827) {
  h_28(state, unused, out_1142102096268485827);
}
void car_H_28(double *state, double *unused, double *out_1740550870997576729) {
  H_28(state, unused, out_1740550870997576729);
}
void car_h_31(double *state, double *unused, double *out_4288825200706392460) {
  h_31(state, unused, out_4288825200706392460);
}
void car_H_31(double *state, double *unused, double *out_4054427577857094666) {
  H_31(state, unused, out_4054427577857094666);
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
