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
void car_err_fun(double *nom_x, double *delta_x, double *out_5552049021186220575);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_590150806491182217);
void car_H_mod_fun(double *state, double *out_462982770310503507);
void car_f_fun(double *state, double dt, double *out_169833714219358489);
void car_F_fun(double *state, double dt, double *out_3869384383894482819);
void car_h_25(double *state, double *unused, double *out_3087348870251025033);
void car_H_25(double *state, double *unused, double *out_8790573077486810872);
void car_h_24(double *state, double *unused, double *out_6915008056190712895);
void car_H_24(double *state, double *unused, double *out_6617923478481311306);
void car_h_30(double *state, double *unused, double *out_3500479056225270130);
void car_H_30(double *state, double *unused, double *out_2739480654731123989);
void car_h_26(double *state, double *unused, double *out_2897163171548792613);
void car_H_26(double *state, double *unused, double *out_5049069758612754648);
void car_h_27(double *state, double *unused, double *out_5691754191059722684);
void car_H_27(double *state, double *unused, double *out_4914243966531548900);
void car_h_29(double *state, double *unused, double *out_8502152323886115775);
void car_H_29(double *state, double *unused, double *out_6627606693401099933);
void car_h_28(double *state, double *unused, double *out_7413122646763798369);
void car_H_28(double *state, double *unused, double *out_6736738363238921109);
void car_h_31(double *state, double *unused, double *out_2930162201899895888);
void car_H_31(double *state, double *unused, double *out_8821219039363771300);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}