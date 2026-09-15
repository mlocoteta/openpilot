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
void car_err_fun(double *nom_x, double *delta_x, double *out_5579271098234299589);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_8879118943542071452);
void car_H_mod_fun(double *state, double *out_4346759063564356553);
void car_f_fun(double *state, double dt, double *out_8401415236153157083);
void car_F_fun(double *state, double dt, double *out_1973239055632703499);
void car_h_25(double *state, double *unused, double *out_7709444436246576106);
void car_H_25(double *state, double *unused, double *out_4906796784232957826);
void car_h_24(double *state, double *unused, double *out_8161953024412082811);
void car_H_24(double *state, double *unused, double *out_6319825032271366663);
void car_h_30(double *state, double *unused, double *out_8890419815179839294);
void car_H_30(double *state, double *unused, double *out_7425129742740206453);
void car_h_26(double *state, double *unused, double *out_8798474113368893512);
void car_H_26(double *state, double *unused, double *out_1165293465358901602);
void car_h_27(double *state, double *unused, double *out_4672658384802243421);
void car_H_27(double *state, double *unused, double *out_8798020259785401946);
void car_h_29(double *state, double *unused, double *out_4214457022643681759);
void car_H_29(double *state, double *unused, double *out_7935361087054598637);
void car_h_28(double *state, double *unused, double *out_8772412421246462550);
void car_H_28(double *state, double *unused, double *out_2852962069985068063);
void car_h_31(double *state, double *unused, double *out_7434250373962070217);
void car_H_31(double *state, double *unused, double *out_539085363125550126);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}