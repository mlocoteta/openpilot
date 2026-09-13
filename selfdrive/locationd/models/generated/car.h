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
void car_err_fun(double *nom_x, double *delta_x, double *out_6455770263676897448);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_3264339508163218326);
void car_H_mod_fun(double *state, double *out_2314116705851516155);
void car_f_fun(double *state, double dt, double *out_3179221506286947540);
void car_F_fun(double *state, double dt, double *out_2603402554270443885);
void car_h_25(double *state, double *unused, double *out_7483142871930603684);
void car_H_25(double *state, double *unused, double *out_1208863944137975522);
void car_h_24(double *state, double *unused, double *out_5607942348347630047);
void car_H_24(double *state, double *unused, double *out_25779713474104338);
void car_h_30(double *state, double *unused, double *out_3845693343676581334);
void car_H_30(double *state, double *unused, double *out_1079524996994735452);
void car_h_26(double *state, double *unused, double *out_8847366611337426979);
void car_H_26(double *state, double *unused, double *out_2532639374736080702);
void car_h_27(double *state, double *unused, double *out_7323093963955398614);
void car_H_27(double *state, double *unused, double *out_1095238314805689459);
void car_h_29(double *state, double *unused, double *out_1155979923984264311);
void car_H_29(double *state, double *unused, double *out_1589756341309127636);
void car_h_28(double *state, double *unused, double *out_5021130674020958612);
void car_H_28(double *state, double *unused, double *out_7891000058744771066);
void car_h_31(double *state, double *unused, double *out_3082328551024898747);
void car_H_31(double *state, double *unused, double *out_1239509906014935950);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}