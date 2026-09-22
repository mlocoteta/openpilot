#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_7165967535860238129);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_9032729807193459598);
void pose_H_mod_fun(double *state, double *out_5054599202167139908);
void pose_f_fun(double *state, double dt, double *out_5000035888964044284);
void pose_F_fun(double *state, double dt, double *out_9018422947626896264);
void pose_h_4(double *state, double *unused, double *out_6773718258743003346);
void pose_H_4(double *state, double *unused, double *out_793482604584818813);
void pose_h_10(double *state, double *unused, double *out_3870110240018051215);
void pose_H_10(double *state, double *unused, double *out_3089556940454179292);
void pose_h_13(double *state, double *unused, double *out_7087737251706748874);
void pose_H_13(double *state, double *unused, double *out_2418791220747513988);
void pose_h_14(double *state, double *unused, double *out_8542055892000654086);
void pose_H_14(double *state, double *unused, double *out_3169758251754665716);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}