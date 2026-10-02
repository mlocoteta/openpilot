#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_2493721592867885738);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_7705211639884929019);
void pose_H_mod_fun(double *state, double *out_5366119461374868342);
void pose_f_fun(double *state, double dt, double *out_6027033949105645460);
void pose_F_fun(double *state, double dt, double *out_3018765872118070900);
void pose_h_4(double *state, double *unused, double *out_8360223364191194135);
void pose_H_4(double *state, double *unused, double *out_2834185422598356425);
void pose_h_10(double *state, double *unused, double *out_8320173138289403317);
void pose_H_10(double *state, double *unused, double *out_3734892584971238307);
void pose_h_13(double *state, double *unused, double *out_2356519242840275727);
void pose_H_13(double *state, double *unused, double *out_8001927442794494262);
void pose_h_14(double *state, double *unused, double *out_3701937905252005950);
void pose_H_14(double *state, double *unused, double *out_6797426278937840954);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}