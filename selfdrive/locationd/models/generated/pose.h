#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void pose_err_fun(double *nom_x, double *delta_x, double *out_2251541010105652257);
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_3400329631105902853);
void pose_H_mod_fun(double *state, double *out_7864672362290258107);
void pose_f_fun(double *state, double dt, double *out_1708698118726409450);
void pose_F_fun(double *state, double dt, double *out_269214026509656143);
void pose_h_4(double *state, double *unused, double *out_6722098375813311917);
void pose_H_4(double *state, double *unused, double *out_4092865152446350535);
void pose_h_10(double *state, double *unused, double *out_5359691896685221629);
void pose_H_10(double *state, double *unused, double *out_5571839411167880879);
void pose_h_13(double *state, double *unused, double *out_1702932630428691594);
void pose_H_13(double *state, double *unused, double *out_3517766055870350394);
void pose_h_14(double *state, double *unused, double *out_4050504407425724528);
void pose_H_14(double *state, double *unused, double *out_129624296106866006);
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt);
}