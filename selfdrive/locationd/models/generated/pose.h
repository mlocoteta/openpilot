#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_3683974983863530851);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_7161705307985060718);
void pose_H_mod_fun(double *state, double *out_8701255044286026870);
void pose_f_fun(double *state, double dt, double *out_3554971931229877212);
void pose_F_fun(double *state, double dt, double *out_4213718004866334225);
void pose_h_4(double *state, double *unused, double *out_8042373158170206990);
void pose_H_4(double *state, double *unused, double *out_7947094042231314263);
void pose_h_10(double *state, double *unused, double *out_6693017902685099821);
void pose_H_10(double *state, double *unused, double *out_2240931588784816648);
void pose_h_13(double *state, double *unused, double *out_4695832005485386494);
void pose_H_13(double *state, double *unused, double *out_4734820216898981462);
void pose_h_14(double *state, double *unused, double *out_5793211794452819883);
void pose_H_14(double *state, double *unused, double *out_3983853185891829734);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}