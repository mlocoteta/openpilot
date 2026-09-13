#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_3211789106073125283);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_6226563961506943969);
void pose_H_mod_fun(double *state, double *out_5161461913541420634);
void pose_f_fun(double *state, double dt, double *out_3057528827902898560);
void pose_F_fun(double *state, double dt, double *out_2410705301866754520);
void pose_h_4(double *state, double *unused, double *out_9112018432623595899);
void pose_H_4(double *state, double *unused, double *out_5072803088510724449);
void pose_h_10(double *state, double *unused, double *out_1222625076235428622);
void pose_H_10(double *state, double *unused, double *out_6913994360612087924);
void pose_h_13(double *state, double *unused, double *out_5539054079846767747);
void pose_H_13(double *state, double *unused, double *out_5637405008192568553);
void pose_h_14(double *state, double *unused, double *out_4189770429909065638);
void pose_H_14(double *state, double *unused, double *out_1990014656215352153);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}