#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_7505672412271645129);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_850525553930579209);
void pose_H_mod_fun(double *state, double *out_5142011875417202005);
void pose_f_fun(double *state, double dt, double *out_203013903358445647);
void pose_F_fun(double *state, double dt, double *out_7326468457789213143);
void pose_h_4(double *state, double *unused, double *out_8153824291242181436);
void pose_H_4(double *state, double *unused, double *out_3058293008556022762);
void pose_h_10(double *state, double *unused, double *out_3951144425666594182);
void pose_H_10(double *state, double *unused, double *out_3697294613085597244);
void pose_h_13(double *state, double *unused, double *out_6907487104961603826);
void pose_H_13(double *state, double *unused, double *out_7777819856836827925);
void pose_h_14(double *state, double *unused, double *out_2370415612838457693);
void pose_H_14(double *state, double *unused, double *out_7021533864895507291);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}