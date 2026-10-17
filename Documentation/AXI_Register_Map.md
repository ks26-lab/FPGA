# Vivado Address Map & AXI Register Specifications

## 1. System Memory Map (Vivado Address Editor)

All scene peripherals are connected to the Processing System Master port `M_AXI_GP0`:

| Scene Peripheral | Module | Base Address | High Address | Size |
|---|---|---|---|---|
| **Underwater Dynamic Probe** | `underwater_probe_top` | `0x43C00000` | `0x43C0FFFF` | 64 KB |
| **Maze Runner Game Engine** | `maze_top` | `0x43C10000` | `0x43C1FFFF` | 64 KB |
| **Mars Space Habitat** | `mars_habitat_top` | `0x43C20000` | `0x43C2FFFF` | 64 KB |
| **Solar Tracking Gimbal** | `solar_gimbal_top` | `0x43C30000` | `0x43C3FFFF` | 64 KB |
| **Smart City Traffic Grid** | `traffic_top` | `0x43C40000` | `0x43C4FFFF` | 64 KB |

*Note: In Strategy A (single bitstream mode), the currently programmed peripheral occupies `0x43C00000`.*

---

## 2. Underwater Dynamic Probe (`0x43C00000`)

| Offset | Name | Type | Reset | Bitfield Description |
|---|---|---|---|---|
| `0x00` | `CONTROL` | W | `0x0` | `[0]` start, `[1]` stop, `[2]` reset, `[3]` disturb_strobe, `[5:4]` disturb_type (1=FISH, 2=GARBAGE, 3=WHALE), `[6]` set_depth_we |
| `0x04` | `DEPTH_CFG` | R/W | `0x032001F4` | `[15:0]` set_depth x10, `[31:16]` target_depth x10 |
| `0x08` | `CURRENT` | R/W | `0x00000014` | `[7:0]` signed water current percentage (-100% to +100%) |
| `0x0C` | `STATUS` | R | `0x0` | `[3:0]` probe_state, `[4]` collision, `[5]` recovery, `[6]` target_reached, `[8:7]` active_obj |
| `0x10` | `POSITION` | R | `0x000001F4` | `[15:0]` current_depth x10, `[23:16]` displacement_x, `[31:24]` velocity_z |
| `0x14` | `COUNTERS` | R | `0x0` | `[15:0]` collision_counter |
| `0x18` | `CYCLES` | R | `0x0` | `[31:0]` sim_cycles (10 Hz hardware tick) |

---

## 3. Maze Runner (`0x43C10000`)

| Offset | Name | Type | Reset | Bitfield Description |
|---|---|---|---|---|
| `0x00` | `CONTROL` | W | `0x0` | `[3:0]` cmd_code (1=START, 2=RESET, 3=UP, 4=DOWN, 5=LEFT, 6=RIGHT), `[7]` strobe |
| `0x04` | `STATUS` | R | `0x0` | `[3:0]` state (0=IDLE, 1=DISPLAY, 2=MEM, 3=GAME, 4=WIN, 5=GAMEOVER), `[4]` collision, `[5]` goal, `[6]` visible |
| `0x08` | `POSITION` | R/W | `0x00770000` | Read: `[3:0]` pl_x, `[7:4]` pl_y, `[11:8]` st_x, `[15:12]` st_y, `[19:16]` gl_x, `[23:20]` gl_y<br>Write: `[11:8]` cfg_st_x, `[15:12]` cfg_st_y, `[19:16]` cfg_gl_x, `[23:20]` cfg_gl_y |
| `0x0C` | `COUNTERS` | R | `0x0` | `[15:0]` total_moves, `[23:16]` valid_moves, `[31:24]` collision_count |
| `0x10` | `TIMER` | R | `0x5` | `[3:0]` countdown_seconds_remaining |
| `0x14` | `MAZE_MEM` | R/W | `0x0` | Write: `[5:0]` rom_addr (0-63)<br>Read: `[5:0]` addr, `[11:8]` wall_bitmask (Up, Rt, Dn, Lt) |

---

## 4. Mars Space Habitat (`0x43C20000`)

| Offset | Name | Type | Reset | Bitfield Description |
|---|---|---|---|---|
| `0x00` | `CONTROL` | W | `0x0` | `[0]` attack_strobe, `[1]` reset_strobe |
| `0x04` | `ATTACK` | R/W | `0x00001400` | `[0]` type (0=NORM, 1=BIG), `[2:1]` target (0=ALL, 1=A, 2=B), `[15:8]` meteorite_count |
| `0x08` | `THRESHOLD` | R/W | `0x028A02BC` | `[15:0]` threshold_A x10 (700=70.0), `[31:16]` threshold_B x10 (650=65.0) |
| `0x0C` | `STATUS` | R | `0x0` | `[3:0]` state, `[4]` A_closed, `[5]` B_closed, `[6]` link_closed, `[7]` threshold_crossed, `[9:8]` target |
| `0x10` | `IMPACT` | R | `0x0` | `[15:0]` last_impact x10, `[23:16]` processed_count, `[31:24]` total_requested |
| `0x14` | `COUNTERS` | R | `0x0` | `[15:0]` impacts_A, `[31:16]` impacts_B |
| `0x18` | `TOTAL` | R | `0x0` | `[15:0]` total_impacts |

---

## 5. Solar Tracking Gimbal (`0x43C30000`)

| Offset | Name | Type | Reset | Bitfield Description |
|---|---|---|---|---|
| `0x00` | `CONTROL` | W | `0x0` | `[0]` calc_strobe, `[1]` reset_strobe, `[2]` track_en, `[3]` multi_panel_en, `[4]` opt_power_en |
| `0x04` | `SUN_POS` | R/W | `0x01A40546` | `[15:0]` sun_azimuth x10 (1350=135.0°), `[31:16]` sun_elevation x10 (420=42.0°) |
| `0x08` | `PANEL_POS` | R/W | `0x012C0384` | `[15:0]` panel_azimuth x10 (900=90.0°), `[31:16]` panel_elevation x10 (300=30.0°) |
| `0x0C` | `STATUS` | R | `0x0` | `[3:0]` state (0=IDLE, 1=CALC, 2=LOCKED, 3=SLEWING, 4=DEADBAND, 5=FAULT), `[4]` locked, `[5]` az_dir (0=CCW, 1=CW), `[6]` el_dir (0=DN, 1=UP), `[7]` az_hold, `[8]` el_hold |
| `0x10` | `ERROR` | R | `0x0` | `[15:0]` signed azimuth_error x10 (-1800 to +1800), `[31:16]` signed elevation_error x10 |
| `0x14` | `ACTUATORS` | R | `0x0` | `[15:0]` signed actuator_azimuth x10, `[31:16]` signed actuator_elevation x10 |
| `0x18` | `CYCLES` | R | `0x0` | `[31:0]` cycle_counter |
| `0x1C` | `SUN_VECTOR_X` | R | `0x0` | Q16.16 signed Sun direction vector $S_x$ |
| `0x20` | `SUN_VECTOR_Y` | R | `0x0` | Q16.16 signed Sun direction vector $S_y$ |
| `0x24` | `SUN_VECTOR_Z` | R | `0x0` | Q16.16 signed Sun direction vector $S_z$ |
| `0x28` | `PANEL_NORMAL_X` | R | `0x0` | Q16.16 signed Panel normal vector $N_x$ |
| `0x2C` | `PANEL_NORMAL_Y` | R | `0x0` | Q16.16 signed Panel normal vector $N_y$ |
| `0x30` | `PANEL_NORMAL_Z` | R | `0x0` | Q16.16 signed Panel normal vector $N_z$ |
| `0x34` | `DOT_PRODUCT` | R | `0x0` | Q16.16 signed $N \cdot S = \cos\theta$ |
| `0x38` | `INCIDENT_ANGLE` | R | `0x0` | `[15:0]` incident_angle x10 (0.1°), `[31:16]` cos_incidence x1000 |
| `0x3C` | `ESTIMATED_POWER` | R | `0x0` | `[15:0]` estimated_power (Watts, max 5665 W), `[31:16]` power_efficiency x10 |
| `0x40` | `FILTERED_SUN` | R | `0x0` | `[15:0]` filtered_azimuth x10, `[31:16]` filtered_elevation x10 |
| `0x44` | `PREDICTED_SUN` | R | `0x0` | `[15:0]` predicted_azimuth x10, `[31:16]` predicted_elevation x10 |
| `0x48` | `ANGULAR_VELOCITY` | R | `0x0` | `[15:0]` signed omega_az x10, `[31:16]` signed omega_el x10 |
| `0x4C` | `CONTROL_LIMITS` | R/W | `0x00320032` | `[15:0]` az_deadband x10 (5=0.5°), `[31:16]` el_deadband x10 (5=0.5°) |
| `0x50` | `FAULT_FLAGS` | R | `0x0` | 16-bit hardware safety supervisor fault flags bitmask |
| `0x54` | `VECTOR_CYCLES` | R | `0x00000012` | Vector latency performance counter (18 cycles) |
| `0x58` | `UPDATE_COUNTER` | R | `0x0` | Cumulative authoritative FPGA calculation updates counter |
| `0x5C` | `PANEL0_DATA` | R | `0x0` | `[15:0]` Panel 0 power (W), `[31:16]` Panel 0 incident angle x10 |
| `0x60` | `PANEL1_DATA` | R | `0x0` | `[15:0]` Panel 1 power (W), `[31:16]` Panel 1 incident angle x10 |
| `0x64` | `PANEL2_DATA` | R | `0x0` | `[15:0]` Panel 2 power (W), `[31:16]` Panel 2 incident angle x10 |
| `0x68` | `PANEL3_DATA` | R | `0x0` | `[15:0]` Panel 3 power (W), `[31:16]` Panel 3 incident angle x10 |
| `0x6C` | `TOTAL_ARRAY_POWER` | R | `0x0` | Total 4-panel array generated electrical power (Watts) |
| `0x70` | `PANELS_ACTIVE_MASK`| R | `0x0000000F` | `[3:0]` active panel mask (0x0F = 4 concurrent parallel channels) |

---

## 6. Smart City Traffic Grid (`0x43C40000`)

| Offset | Name | Type | Reset | Bitfield Description |
|---|---|---|---|---|
| `0x00` | `CONTROL` | W | `0x0` | `[0]` step, `[1]` reset, `[2]` override_en, `[3]` override_phase, `[4]` auto, `[5]` emg, `[7:6]` emg_dir, `[8]` ped, `[9]` stress |
| `0x04` | `CONFIG` | R/W | `0x00080C01` | `[7:0]` intersection_id (1-4), `[15:8]` queue_ns, `[23:16]` queue_ew, `[31:24]` priority |
| `0x08` | `TIMING_CFG`| R/W | `0x002D000A` | `[15:0]` min_green_s (10s), `[31:16]` max_green_s (45s) |
| `0x0C` | `STATUS` | R | `0x0` | `[3:0]` phase (0=NS_G, 1=NS_Y, 2=ALL_RED, 3=EW_G, 4=EW_Y, 5=PED, 6=EMG), `[4]` alert, `[5]` override, `[15:8]` fsm_code |
| `0x10` | `TELEMETRY` | R | `0x00002814` | `[7:0]` green_rem_s, `[15:8]` congestion_score (0-100%), `[23:16]` clr_ns, `[31:24]` clr_ew |
| `0x14` | `CYCLES` | R | `0x0` | `[31:0]` simulation_ticks |
| `0x18` | `APPROACH_QUEUES_NS` | R | `0x0` | `[7:0]` queue_north, `[23:16]` queue_south |
| `0x1C` | `APPROACH_QUEUES_EW` | R | `0x0` | `[7:0]` queue_east, `[23:16]` queue_west |
| `0x20` | `TOTAL_QUEUES` | R | `0x0` | `[9:0]` queue_total, `[23:16]` queue_ns_sum, `[31:24]` queue_ew_sum |
| `0x24` | `DYNAMIC_SPLITS` | R | `0x0` | `[7:0]` calc_green_ns_s, `[23:16]` calc_green_ew_s |
| `0x28` | `WAIT_TIMES` | R | `0x0` | `[15:0]` ns_wait_time_s, `[31:16]` ew_wait_time_s |
| `0x2C` | `PREDICTED_QUEUES` | R | `0x0` | `[8:0]` pred_queue_ns, `[24:16]` pred_queue_ew |
| `0x30` | `CONGESTION_LEVELS` | R | `0x0` | `[2:0]` n_cong, `[6:4]` s_cong, `[10:8]` e_cong, `[14:12]` w_cong, `[23:16]` score, `[31:24]` global_lvl |
| `0x34` | `EMERGENCY_STATUS` | R | `0x0` | `[0]` emg_req, `[2:1]` emg_dir, `[4]` corridor_active, `[7:5]` curr_node, `[10:8]` next_node, `[15:11]` events |
| `0x38` | `PEDESTRIAN_STATUS` | R | `0x0` | `[0]` ped_walk_active, `[7:1]` ped_time_rem, `[15:8]` ped_serviced_count |
| `0x3C` | `FAULT_FLAGS` | R | `0x0` | 16-bit hardware safety supervisor fault flags bitmask |
| `0x40` | `FAULT_COUNT` | R | `0x0` | `[15:0]` fault_count, `[31:16]` collision_events |
| `0x44` | `VEHICLE_OCCUPANCY` | R | `0x0` | `[15:0]` vehicle_active_mask, `[31:16]` brake_required_mask |
| `0x48` | `VEH_POS_NORTH` | R | `0x0` | `[7:0]=V0`, `[15:8]=V1`, `[23:16]=V2`, `[31:24]=V3` (meters) |
| `0x4C` | `VEH_POS_SOUTH` | R | `0x0` | `[7:0]=V4`, `[15:8]=V5`, `[23:16]=V6`, `[31:24]=V7` (meters) |
| `0x50` | `VEH_POS_EAST` | R | `0x0` | `[7:0]=V8`, `[15:8]=V9`, `[23:16]=V10`, `[31:24]=V11` (meters) |
| `0x54` | `VEH_POS_WEST` | R | `0x0` | `[7:0]=V12`, `[15:8]=V13`, `[23:16]=V14`, `[31:24]=V15` (meters) |
| `0x58` | `VEH_SPEEDS` | R | `0x0` | `[7:0]` avg_v_n, `[15:8]` avg_v_s, `[23:16]` avg_v_e, `[31:24]` avg_v_w (m/s) |
| `0x5C` | `STARVATION_FLAGS` | R/W | `0x002D0000` | `[0]` ns_starving, `[1]` ew_starving, `[31:16]` starvation_limit_s (45s) |
| `0x60` | `FSM_CYCLES` | R | `0x0` | 32-bit FSM execution cycles |
| `0x64` | `QUEUE_CYCLES` | R | `0x0` | 32-bit queue update cycles |
| `0x68` | `VEHICLE_CYCLES` | R | `0x0` | 32-bit parallel vehicle engine cycles (16 channels concurrent) |
| `0x6C` | `OPTIMIZER_CYCLES` | R | `0x0` | 32-bit optimization cycles |
| `0x70` | `UPDATE_COUNTER` | R | `0x0` | 32-bit cumulative authoritative updates |
| `0x74` | `THROUGHPUT` | R | `0x0` | 32-bit throughput metric (updates/sec) |
| `0x78` | `ADAPTIVE_WEIGHTS` | R/W | `0x0A010302` | `[7:0]` w_queue, `[15:8]` w_wait, `[23:16]` w_pred, `[31:24]` w_emg |
