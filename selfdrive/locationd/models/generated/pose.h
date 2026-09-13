#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_7911616955151800495);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_7584171002491943517);
void pose_H_mod_fun(double *state, double *out_8208145951121679600);
void pose_f_fun(double *state, double dt, double *out_7339808689618378881);
void pose_F_fun(double *state, double dt, double *out_4299830908048765183);
void pose_h_4(double *state, double *unused, double *out_3838924425177329508);
void pose_H_4(double *state, double *unused, double *out_6964376043796922763);
void pose_h_10(double *state, double *unused, double *out_4478443536349725461);
void pose_H_10(double *state, double *unused, double *out_8208658119783990230);
void pose_h_13(double *state, double *unused, double *out_349204714200215709);
void pose_H_13(double *state, double *unused, double *out_8270094204580296052);
void pose_h_14(double *state, double *unused, double *out_5535558880524166264);
void pose_H_14(double *state, double *unused, double *out_7519127173573144324);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}