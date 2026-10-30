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
void car_err_fun(double *nom_x, double *delta_x, double *out_8999648935700225800);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_1037891798927481552);
void car_H_mod_fun(double *state, double *out_2102418200973278943);
void car_f_fun(double *state, double dt, double *out_7837527456128700272);
void car_F_fun(double *state, double dt, double *out_727133835749799749);
void car_h_25(double *state, double *unused, double *out_577890879895288968);
void car_H_25(double *state, double *unused, double *out_6386951471255294300);
void car_h_24(double *state, double *unused, double *out_7629006599360388474);
void car_H_24(double *state, double *unused, double *out_7231948080038989699);
void car_h_30(double *state, double *unused, double *out_1619678494567612724);
void car_H_30(double *state, double *unused, double *out_8905284429762542927);
void car_h_26(double *state, double *unused, double *out_2710552281154473983);
void car_H_26(double *state, double *unused, double *out_2645448152381238076);
void car_h_27(double *state, double *unused, double *out_1112556954840391992);
void car_H_27(double *state, double *unused, double *out_7317865572763065472);
void car_h_29(double *state, double *unused, double *out_1269743623191521137);
void car_H_29(double *state, double *unused, double *out_9031228299632616505);
void car_h_28(double *state, double *unused, double *out_4149343006284724677);
void car_H_28(double *state, double *unused, double *out_4333116757007404537);
void car_h_31(double *state, double *unused, double *out_656605003849113299);
void car_H_31(double *state, double *unused, double *out_2019240050147886600);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}