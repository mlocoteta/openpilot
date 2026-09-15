#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_5010206230741134473);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_1188067782326305394);
void pose_H_mod_fun(double *state, double *out_7990211645421290333);
void pose_f_fun(double *state, double dt, double *out_2076252175851799438);
void pose_F_fun(double *state, double dt, double *out_5637265960027517094);
void pose_h_4(double *state, double *unused, double *out_4126661282704422428);
void pose_H_4(double *state, double *unused, double *out_7236050643366577726);
void pose_h_10(double *state, double *unused, double *out_8418525422339329003);
void pose_H_10(double *state, double *unused, double *out_7705227448246336422);
void pose_h_13(double *state, double *unused, double *out_1137889379193769762);
void pose_H_13(double *state, double *unused, double *out_4023776818034244925);
void pose_h_14(double *state, double *unused, double *out_3946282764828343143);
void pose_H_14(double *state, double *unused, double *out_3272809787027093197);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}