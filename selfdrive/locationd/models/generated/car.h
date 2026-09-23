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
void car_err_fun(double *nom_x, double *delta_x, double *out_7750065176779719590);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_8753902870006442752);
void car_H_mod_fun(double *state, double *out_7635199098624435267);
void car_f_fun(double *state, double dt, double *out_2250998510373555857);
void car_F_fun(double *state, double dt, double *out_2659791887869057736);
void car_h_25(double *state, double *unused, double *out_4981676432707949210);
void car_H_25(double *state, double *unused, double *out_1538290732018060651);
void car_h_24(double *state, double *unused, double *out_7244510398663534980);
void car_H_24(double *state, double *unused, double *out_634358866987438915);
void car_h_30(double *state, double *unused, double *out_4825190164283060522);
void car_H_30(double *state, double *unused, double *out_4056623690525309278);
void car_h_26(double *state, double *unused, double *out_7861976215727393207);
void car_H_26(double *state, double *unused, double *out_4842816701778861252);
void car_h_27(double *state, double *unused, double *out_7794228535977802593);
void car_H_27(double *state, double *unused, double *out_6280217761709252495);
void car_h_29(double *state, double *unused, double *out_3881680311381398087);
void car_H_29(double *state, double *unused, double *out_4566855034839701462);
void car_h_28(double *state, double *unused, double *out_2792555268316956948);
void car_H_28(double *state, double *unused, double *out_515543982229829112);
void car_h_31(double *state, double *unused, double *out_2703116279715418417);
void car_H_31(double *state, double *unused, double *out_4216608599545509776);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}