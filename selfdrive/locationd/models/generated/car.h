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
void car_err_fun(double *nom_x, double *delta_x, double *out_2119137591410813881);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_5735328309956152563);
void car_H_mod_fun(double *state, double *out_3140904060152819759);
void car_f_fun(double *state, double dt, double *out_2448396695172844585);
void car_F_fun(double *state, double dt, double *out_4603118210915444160);
void car_h_25(double *state, double *unused, double *out_8073669724445640960);
void car_H_25(double *state, double *unused, double *out_382144578492545389);
void car_h_24(double *state, double *unused, double *out_4820837960587678485);
void car_H_24(double *state, double *unused, double *out_601921292348768279);
void car_h_30(double *state, double *unused, double *out_7654544040434155993);
void car_H_30(double *state, double *unused, double *out_6534545762999071366);
void car_h_26(double *state, double *unused, double *out_4545748975815222155);
void car_H_26(double *state, double *unused, double *out_4123647897366601613);
void car_h_27(double *state, double *unused, double *out_3071996456784795315);
void car_H_27(double *state, double *unused, double *out_4359782451198646455);
void car_h_29(double *state, double *unused, double *out_565453071469227035);
void car_H_29(double *state, double *unused, double *out_7044777107313463550);
void car_h_28(double *state, double *unused, double *out_3741900449895627754);
void car_H_28(double *state, double *unused, double *out_1962378090243932976);
void car_h_31(double *state, double *unused, double *out_6623038331816757793);
void car_H_31(double *state, double *unused, double *out_351498616615584961);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}