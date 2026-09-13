#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_7437794640769795433);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_2037082783356591262);
void pose_H_mod_fun(double *state, double *out_6997830721327979188);
void pose_f_fun(double *state, double dt, double *out_2524658316881090159);
void pose_F_fun(double *state, double dt, double *out_1493803281019954497);
void pose_h_4(double *state, double *unused, double *out_9199116239139928597);
void pose_H_4(double *state, double *unused, double *out_5055826457360484509);
void pose_h_10(double *state, double *unused, double *out_6229114816113941890);
void pose_H_10(double *state, double *unused, double *out_4767454895579609867);
void pose_h_13(double *state, double *unused, double *out_8087901312810249753);
void pose_H_13(double *state, double *unused, double *out_5780286408032366178);
void pose_h_14(double *state, double *unused, double *out_8155013269706044892);
void pose_H_14(double *state, double *unused, double *out_9019067313699969038);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}