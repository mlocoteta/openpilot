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
void car_err_fun(double *nom_x, double *delta_x, double *out_6680589116319572635);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_1421263034200107343);
void car_H_mod_fun(double *state, double *out_8968580721052785900);
void car_f_fun(double *state, double dt, double *out_3852536059217665062);
void car_F_fun(double *state, double dt, double *out_7217781527381652799);
void car_h_25(double *state, double *unused, double *out_2838193808077509293);
void car_H_25(double *state, double *unused, double *out_4085073539734055094);
void car_h_24(double *state, double *unused, double *out_7378709950093750440);
void car_H_24(double *state, double *unused, double *out_2001100279119417225);
void car_h_30(double *state, double *unused, double *out_6475643336331531643);
void car_H_30(double *state, double *unused, double *out_4214412486877295164);
void car_h_26(double *state, double *unused, double *out_8554827447728949957);
void car_H_26(double *state, double *unused, double *out_3428219475623743190);
void car_h_27(double *state, double *unused, double *out_1670450007001367556);
void car_H_27(double *state, double *unused, double *out_6389175798677720075);
void car_h_29(double *state, double *unused, double *out_6969427469717174328);
void car_H_29(double *state, double *unused, double *out_3704181142562902980);
void car_h_28(double *state, double *unused, double *out_1142102096268485827);
void car_H_28(double *state, double *unused, double *out_1740550870997576729);
void car_h_31(double *state, double *unused, double *out_4288825200706392460);
void car_H_31(double *state, double *unused, double *out_4054427577857094666);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}