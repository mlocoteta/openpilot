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
void car_err_fun(double *nom_x, double *delta_x, double *out_1981160884949189432);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_8847679371512298388);
void car_H_mod_fun(double *state, double *out_5601961838873094342);
void car_f_fun(double *state, double dt, double *out_5149707672518823132);
void car_F_fun(double *state, double dt, double *out_6841526781584604245);
void car_h_25(double *state, double *unused, double *out_7458155415496567305);
void car_H_25(double *state, double *unused, double *out_698270013688429502);
void car_h_24(double *state, double *unused, double *out_8762756803592850260);
void car_H_24(double *state, double *unused, double *out_2427133132865743571);
void car_h_30(double *state, double *unused, double *out_434784079387956054);
void car_H_30(double *state, double *unused, double *out_6218420327803187253);
void car_h_26(double *state, double *unused, double *out_8798712813018318160);
void car_H_26(double *state, double *unused, double *out_4439773332562485726);
void car_h_27(double *state, double *unused, double *out_723267455973180046);
void car_H_27(double *state, double *unused, double *out_4043657016002762342);
void car_h_29(double *state, double *unused, double *out_4920797374511219811);
void car_H_29(double *state, double *unused, double *out_2330294289133211309);
void car_h_28(double *state, double *unused, double *out_3477859511150572185);
void car_H_28(double *state, double *unused, double *out_2752104727936319265);
void car_h_31(double *state, double *unused, double *out_4217753431862633375);
void car_H_31(double *state, double *unused, double *out_667624051811469074);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}