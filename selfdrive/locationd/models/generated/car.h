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
void car_err_fun(double *nom_x, double *delta_x, double *out_8548372190097700555);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_6257373597812199292);
void car_H_mod_fun(double *state, double *out_7008429191596952258);
void car_f_fun(double *state, double dt, double *out_211764458208077354);
void car_F_fun(double *state, double dt, double *out_6789911951967766610);
void car_h_25(double *state, double *unused, double *out_7956251239264178232);
void car_H_25(double *state, double *unused, double *out_912908841376907547);
void car_h_24(double *state, double *unused, double *out_7723154835838931558);
void car_H_24(double *state, double *unused, double *out_2501382670766146913);
void car_h_30(double *state, double *unused, double *out_4094567762835676580);
void car_H_30(double *state, double *unused, double *out_3614787488750700651);
void car_h_26(double *state, double *unused, double *out_4086855108634070771);
void car_H_26(double *state, double *unused, double *out_2828594477497148677);
void car_h_27(double *state, double *unused, double *out_3279583348191151873);
void car_H_27(double *state, double *unused, double *out_5789550800551125562);
void car_h_29(double *state, double *unused, double *out_3491251878159199063);
void car_H_29(double *state, double *unused, double *out_3104556144436308467);
void car_h_28(double *state, double *unused, double *out_2111839547115010136);
void car_H_28(double *state, double *unused, double *out_1140925872870982216);
void car_h_31(double *state, double *unused, double *out_271458526840810605);
void car_H_31(double *state, double *unused, double *out_3454802579730500153);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}