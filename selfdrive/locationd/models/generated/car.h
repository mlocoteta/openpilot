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
void car_err_fun(double *nom_x, double *delta_x, double *out_2836153289419609170);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_2870208396745160425);
void car_H_mod_fun(double *state, double *out_8399208845157168096);
void car_f_fun(double *state, double dt, double *out_7838059991381044613);
void car_F_fun(double *state, double dt, double *out_8646854028547709212);
void car_h_25(double *state, double *unused, double *out_2264071304797468914);
void car_H_25(double *state, double *unused, double *out_6252049907879787684);
void car_h_24(double *state, double *unused, double *out_5464496516514981941);
void car_H_24(double *state, double *unused, double *out_1431728403223799421);
void car_h_30(double *state, double *unused, double *out_8419407512091410261);
void car_H_30(double *state, double *unused, double *out_6122710960736547614);
void car_h_26(double *state, double *unused, double *out_3468805347087309985);
void car_H_26(double *state, double *unused, double *out_2510546589005731460);
void car_h_27(double *state, double *unused, double *out_7057486801450440045);
void car_H_27(double *state, double *unused, double *out_3947947648936122703);
void car_h_29(double *state, double *unused, double *out_4801429345782816408);
void car_H_29(double *state, double *unused, double *out_6632942305050939798);
void car_h_28(double *state, double *unused, double *out_6991305190977482559);
void car_H_28(double *state, double *unused, double *out_1550543287981409224);
void car_h_31(double *state, double *unused, double *out_1805869942638907252);
void car_H_31(double *state, double *unused, double *out_6282695869756748112);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}