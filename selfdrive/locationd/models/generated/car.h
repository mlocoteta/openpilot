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
void car_err_fun(double *nom_x, double *delta_x, double *out_6251513780499274303);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_1361283985005059007);
void car_H_mod_fun(double *state, double *out_3699562487368274414);
void car_f_fun(double *state, double dt, double *out_1113205683479280207);
void car_F_fun(double *state, double dt, double *out_2198054725359611149);
void car_h_25(double *state, double *unused, double *out_2775617380616102557);
void car_H_25(double *state, double *unused, double *out_5493625738543962823);
void car_h_24(double *state, double *unused, double *out_6646117502185914860);
void car_H_24(double *state, double *unused, double *out_3267917954565094261);
void car_h_30(double *state, double *unused, double *out_6519293463111227465);
void car_H_30(double *state, double *unused, double *out_1423064602947653932);
void car_h_26(double *state, double *unused, double *out_7122609347787704982);
void car_H_26(double *state, double *unused, double *out_9211615016291532569);
void car_h_27(double *state, double *unused, double *out_7737997378297395789);
void car_H_27(double *state, double *unused, double *out_7797727997487627804);
void car_h_29(double *state, double *unused, double *out_3746027739128576800);
void car_H_29(double *state, double *unused, double *out_5112733341372810709);
void car_h_28(double *state, double *unused, double *out_8104341374603458176);
void car_H_28(double *state, double *unused, double *out_3149103069807484458);
void car_h_31(double *state, double *unused, double *out_5721043300647637435);
void car_H_31(double *state, double *unused, double *out_5462979776667002395);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}