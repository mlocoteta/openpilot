#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_5807655181837607214);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_8974761284027602384);
void pose_H_mod_fun(double *state, double *out_7615318893377638193);
void pose_f_fun(double *state, double dt, double *out_4539696263163526019);
void pose_F_fun(double *state, double dt, double *out_2543913590993509263);
void pose_h_4(double *state, double *unused, double *out_8982992753369428231);
void pose_H_4(double *state, double *unused, double *out_1965697165790759737);
void pose_h_10(double *state, double *unused, double *out_8485879645605284392);
void pose_H_10(double *state, double *unused, double *out_7331944868831731257);
void pose_h_13(double *state, double *unused, double *out_2838239477305121349);
void pose_H_13(double *state, double *unused, double *out_5177970991123092538);
void pose_h_14(double *state, double *unused, double *out_3664563598411967491);
void pose_H_14(double *state, double *unused, double *out_5928938022130244266);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}