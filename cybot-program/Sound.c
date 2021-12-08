/*
 * Sound.c
 *
 *  Created on: Nov 29, 2021
 *      Author: teohys
 */

#include "open_interface.h"
#include "Sound.h"

/**
 * Loads 3 different songs and selects one to play.
 */
void play_sound(int num)
{

    //    oi_t *sensor_data = oi_alloc();
    //    oi_init(sensor_data);
    unsigned char note[15] = {57, 59, 62, 59, 66, 66, 64, 0, 57, 59, 62, 59, 64, 64, 62};
    unsigned char *pointer_note = &note;
    unsigned char duration[15] = {15, 15, 15, 15, 35, 35, 35, 15, 15, 15, 15, 15, 35, 35, 35};
    unsigned char *pointer_duration = &duration;
    oi_loadSong(0, 15, pointer_note, pointer_duration);

    unsigned char note1[7] = {64,64,64,60,64,67,67};
    unsigned char *pointer_note1 = &note;
    unsigned char duration1[7] = {64,64,64,64,64,64,64};
    unsigned char *pointer_duration1 = &duration;
    oi_loadSong(1, 7, pointer_note1, pointer_duration1);

    unsigned char note2[1] = {64};
    unsigned char *pointer_note2 = &note;
    unsigned char duration2[1] = {32};
    unsigned char *pointer_duration2 = &duration;
    oi_loadSong(2, 1, pointer_note2, pointer_duration2);
    oi_play_song(num);
}


