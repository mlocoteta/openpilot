#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_8294180210607547219);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_8330596021821018044);
void pose_H_mod_fun(double *state, double *out_534058243187542804);
void pose_f_fun(double *state, double dt, double *out_2535209606058579312);
void pose_F_fun(double *state, double dt, double *out_4915847086962688884);
void pose_h_4(double *state, double *unused, double *out_4566450913648834974);
void pose_H_4(double *state, double *unused, double *out_8478926176726141688);
void pose_h_10(double *state, double *unused, double *out_7539996529410954195);
void pose_H_10(double *state, double *unused, double *out_8508433762584458121);
void pose_h_13(double *state, double *unused, double *out_4338527865886089826);
void pose_H_13(double *state, double *unused, double *out_6755544071651077127);
void pose_h_14(double *state, double *unused, double *out_8691716025455276110);
void pose_H_14(double *state, double *unused, double *out_6004577040643925399);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}