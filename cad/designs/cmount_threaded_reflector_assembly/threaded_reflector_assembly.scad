// Two-part C-mount male-male tube plus top-open reflector holder.
// Units: millimetres. The optical axis is X, with the bottom plane at Z = 0.

$fn = 128;

part = "assembly"; // tube | holder | assembly | exploded

// Old 4f design print-fit evidence:
// - Thread camera 24.4 in OpenHI B/C is the printed male root/fit diameter.
// - Thread left 24.8 / Cap thread 24.8 are matching female cutter diameters.
// - The old swept triangle is 0.4 mm high with a 0.8 mm base and 0.8 mm pitch.
nominal_cmount_major_d = 25.4;
printed_male_root_d = 24.4;
holder_female_root_d = 24.8;
thread_pitch = 0.8;
thread_height = 0.4;
thread_tooth_w = 0.8;
thread_overlap = 0.08;
join_overlap = 0.2;

tube_total_length = 50;
tube_thread_length = 15;
tube_body_length = tube_total_length - 2 * tube_thread_length; // 20 mm.
bore_d = 20;

reflector_nominal = 20;
reflector_clearance = 0.4;
reflector_inner = reflector_nominal + reflector_clearance;
wall = 4;
holder_box_inner_x = reflector_inner;
holder_box_outer_x = holder_box_inner_x + wall; // left side is open.
holder_box_outer_y = reflector_inner + 2 * wall;
holder_box_outer_z = reflector_inner + wall; // top is open.

holder_socket_length = 24;
holder_female_thread_length = 20;
holder_socket_outer_d = 34;
holder_female_bore_d = holder_female_root_d;

axis_z = wall + reflector_inner / 2; // 14.2 mm with the current 4 mm holder wall.
tube_body_d = 2 * axis_z; // Keeps the center body bottom flush with the holder bottom.
clearance = 0.05;

module cube_at(x0, y0, z0, dx, dy, dz) {
    translate([x0, y0, z0]) cube([dx, dy, dz]);
}

module x_cylinder(d, h, x0) {
    translate([x0, 0, axis_z])
        rotate([0, 90, 0])
            cylinder(d = d, h = h);
}

module clipped_x_cylinder(d, h, x0, z_min, z_max) {
    intersection() {
        x_cylinder(d, h, x0);
        cube_at(x0 - 0.1, -d / 2 - 0.5, z_min, h + 0.2, d + 1, z_max - z_min);
    }
}

module external_thread_core_x(length, root_d, pitch, height, tooth_w) {
    turns = length / pitch;
    root_r = root_d / 2 - thread_overlap;

    translate([0, 0, axis_z])
        rotate([0, 90, 0])
            linear_extrude(
                height = length,
                twist = 360 * turns,
                slices = max(64, ceil(turns * 40)),
                convexity = 10
            )
                translate([root_r, 0])
                    polygon(points = [
                        [0, -tooth_w / 2],
                        [height + thread_overlap, 0],
                        [0, tooth_w / 2]
                    ]);
}

module external_thread_x(x0, length, root_d, viewed_from_right=false) {
    if (viewed_from_right) {
        // Mirror so the right end is right-hand when viewed from its engaging face.
        translate([x0 + length, 0, 0])
            mirror([1, 0, 0])
                external_thread_core_x(length, root_d, thread_pitch, thread_height, thread_tooth_w);
    } else {
        translate([x0, 0, 0])
            external_thread_core_x(length, root_d, thread_pitch, thread_height, thread_tooth_w);
    }
}

module threaded_bore_cutter_x(x0, length) {
    union() {
        x_cylinder(holder_female_bore_d + clearance, length, x0);
        external_thread_x(x0, holder_female_thread_length, holder_female_root_d, false);
    }
}

module male_male_tube() {
    right_thread_x = tube_total_length - tube_thread_length;

    difference() {
        union() {
            x_cylinder(
                printed_male_root_d,
                tube_thread_length + join_overlap,
                0
            );
            external_thread_x(0, tube_thread_length, printed_male_root_d, false);

            x_cylinder(
                tube_body_d,
                tube_body_length + 2 * join_overlap,
                tube_thread_length - join_overlap
            );

            x_cylinder(
                printed_male_root_d,
                tube_thread_length + join_overlap,
                right_thread_x - join_overlap
            );
            external_thread_x(right_thread_x, tube_thread_length, printed_male_root_d, true);
        }

        x_cylinder(bore_d + clearance, tube_total_length + 2, -1);
    }
}

module top_open_reflector_holder(x0=0) {
    socket_left_x = x0;
    box_left_x = socket_left_x + holder_socket_length;

    difference() {
        union() {
            // Top-open, left-open reflector box.
            cube_at(box_left_x, -holder_box_outer_y / 2, 0,
                holder_box_outer_x, holder_box_outer_y, wall);
            cube_at(box_left_x, -holder_box_outer_y / 2, wall,
                holder_box_outer_x, wall, reflector_inner);
            cube_at(box_left_x, holder_box_outer_y / 2 - wall, wall,
                holder_box_outer_x, wall, reflector_inner);
            cube_at(box_left_x + holder_box_inner_x, -holder_box_outer_y / 2, wall,
                wall, holder_box_outer_y, reflector_inner);

            // Female threaded socket opening from the left side of the holder.
            clipped_x_cylinder(holder_socket_outer_d, holder_socket_length + join_overlap,
                socket_left_x, 0, axis_z + holder_socket_outer_d / 2);

            // Flat reinforcement tying the socket to the holder bottom plane.
            cube_at(socket_left_x, -holder_box_outer_y / 2, 0,
                holder_socket_length + wall, holder_box_outer_y, wall);
        }

        threaded_bore_cutter_x(socket_left_x - 0.5, holder_socket_length + 1);
    }
}

if (part == "tube") {
    male_male_tube();
} else if (part == "holder") {
    top_open_reflector_holder(0);
} else if (part == "exploded") {
    color([0.25, 0.60, 0.95]) male_male_tube();
    color([0.35, 0.85, 0.55]) top_open_reflector_holder(tube_total_length + 10);
} else {
    color([0.25, 0.60, 0.95]) male_male_tube();
    color([0.35, 0.85, 0.55])
        top_open_reflector_holder(tube_total_length - tube_thread_length);
}
