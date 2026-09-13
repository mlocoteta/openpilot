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
void car_err_fun(double *nom_x, double *delta_x, double *out_781655183145825394);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_2912836612698073811);
void car_H_mod_fun(double *state, double *out_6456005511861377664);
void car_f_fun(double *state, double dt, double *out_6006881912496167916);
void car_F_fun(double *state, double dt, double *out_1756382049312448223);
void car_h_25(double *state, double *unused, double *out_2827928331020362404);
void car_H_25(double *state, double *unused, double *out_7087046736663509112);
void car_h_24(double *state, double *unused, double *out_668554717831057533);
void car_H_24(double *state, double *unused, double *out_4909832313056359139);
void car_h_30(double *state, double *unused, double *out_4139386833660670090);
void car_H_30(double *state, double *unused, double *out_6832001006918434306);
void car_h_26(double *state, double *unused, double *out_9101766831341963322);
void car_H_26(double *state, double *unused, double *out_7618194018171986280);
void car_h_27(double *state, double *unused, double *out_2173744936640483241);
void car_H_27(double *state, double *unused, double *out_4657237695118009395);
void car_h_29(double *state, double *unused, double *out_8761572863116778404);
void car_H_29(double *state, double *unused, double *out_7342232351232826490);
void car_h_28(double *state, double *unused, double *out_7175418204301328886);
void car_H_28(double *state, double *unused, double *out_9140881450911398875);
void car_h_31(double *state, double *unused, double *out_6465377859274384754);
void car_H_31(double *state, double *unused, double *out_6991985915938634804);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}