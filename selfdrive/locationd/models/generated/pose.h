#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_1227579335886564773);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_7708296302708828001);
void pose_H_mod_fun(double *state, double *out_145151651698479708);
void pose_f_fun(double *state, double dt, double *out_6753877240357292479);
void pose_F_fun(double *state, double dt, double *out_48451545294533288);
void pose_h_4(double *state, double *unused, double *out_711207782401779392);
void pose_H_4(double *state, double *unused, double *out_6437019938278623926);
void pose_h_10(double *state, double *unused, double *out_2942660564170460979);
void pose_H_10(double *state, double *unused, double *out_7753365329259358525);
void pose_h_13(double *state, double *unused, double *out_2914132243760424113);
void pose_H_13(double *state, double *unused, double *out_3224746112946291125);
void pose_h_14(double *state, double *unused, double *out_677306400367602538);
void pose_H_14(double *state, double *unused, double *out_2473779081939139397);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}