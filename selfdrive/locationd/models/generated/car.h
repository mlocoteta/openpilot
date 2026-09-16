#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void car_update_25(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_24(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_30(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_26(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_27(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_29(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_28(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_31(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_err_fun(double *nom_x, double *delta_x, double *out_6314153535178174931);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_7049921009392106379);
void car_H_mod_fun(double *state, double *out_9070114660809295187);
void car_f_fun(double *state, double dt, double *out_7847765386725654972);
void car_F_fun(double *state, double dt, double *out_6490326381461081645);
void car_h_25(double *state, double *unused, double *out_258705256034994534);
void car_H_25(double *state, double *unused, double *out_123073565102942050);
void car_h_24(double *state, double *unused, double *out_5989007342487248666);
void car_H_24(double *state, double *unused, double *out_4869582892069451084);
void car_h_30(double *state, double *unused, double *out_179991132081170203);
void car_H_30(double *state, double *unused, double *out_6793616776388674705);
void car_h_26(double *state, double *unused, double *out_4821682135579675442);
void car_H_26(double *state, double *unused, double *out_3181452404657858551);
void car_h_27(double *state, double *unused, double *out_5260378523695840179);
void car_H_27(double *state, double *unused, double *out_4618853464588249794);
void car_h_29(double *state, double *unused, double *out_5535572585980346068);
void car_H_29(double *state, double *unused, double *out_2905490737718698761);
void car_h_28(double *state, double *unused, double *out_4092634722619698442);
void car_H_28(double *state, double *unused, double *out_2176908279350831813);
void car_h_31(double *state, double *unused, double *out_1709336648663877701);
void car_H_31(double *state, double *unused, double *out_6953601685408875203);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}