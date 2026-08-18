#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_8714848832990626554);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_5047671582975253903);
void pose_H_mod_fun(double *state, double *out_1709250979764021582);
void pose_f_fun(double *state, double dt, double *out_1316099113648689196);
void pose_F_fun(double *state, double dt, double *out_4732408561172474784);
void pose_h_4(double *state, double *unused, double *out_6918932125970712407);
void pose_H_4(double *state, double *unused, double *out_1564971099026927671);
void pose_h_10(double *state, double *unused, double *out_3027582300414544631);
void pose_H_10(double *state, double *unused, double *out_3487027415066723561);
void pose_h_13(double *state, double *unused, double *out_4493446518496679699);
void pose_H_13(double *state, double *unused, double *out_1647302726305405130);
void pose_h_14(double *state, double *unused, double *out_507113954569858993);
void pose_H_14(double *state, double *unused, double *out_2398269757312556858);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}