// Banc d'essai moteur à bras pivotant 3:1 — Dassault UAV Challenge, équipe ISEP
// OpenSCAD >= 2021. Chaque pièce se rend seule avec la variable PART (menu Customizer ou -D PART="bras").
// Impression : PETG ou PETG-CF, 3 parois, 30 % remplissage ; base en 2 moitiés si le plateau < 250 mm.
// Principe : moteur en haut d'un bras pivotant (300 mm au-dessus de l'axe), bas du bras (100 mm sous l'axe)
// en appui sur une cellule de charge barre 20 kg montée verticalement. Force cellule = 3 x poussée.
// Validation : à vérifier avec une masse connue suspendue au plateau moteur par une poulie (voir notice).

PART = "assemblage";   // ["assemblage","base","montant","bras","plateau_moteur","poteau_cellule","bague_axe"]

// ---- paramètres (mm)
base_l = 240; base_w = 140; base_t = 8;
tower_w = 50; tower_t = 8; tower_h = 130; axle_z = 114; axle_d = 4.3;      // axe M4
arm_sec = 20; arm_wall = 2.4; arm_up = 300; arm_down = 100;
plate = 44; plate_t = 6;
cell_l = 80; cell_w = 12.7; cell_h = 12.7; cell_post_x = -46;            // cellule barre standard 80x12.7x12.7
gap = 1.0;                                                               // jeu bras / montants

module hole(d, h) cylinder(d = d, h = h, $fn = 32);

module base() {
  difference() {
    cube([base_l, base_w, base_t], center = false);
    // trous montants (2 x 2 M4), poteau cellule (2 M4), fixation table (4 lumières M6)
    for (s = [-1, 1]) for (x = [-15, 15]) translate([base_l/2 + x, base_w/2 + s*(arm_sec/2 + gap + tower_t/2), -1]) hole(4.3, base_t + 2);
    for (y = [-12, 12]) translate([base_l/2 + cell_post_x - 8 - cell_h/2, base_w/2 + y, -1]) hole(4.3, base_t + 2);
    for (x = [20, base_l - 20]) for (y = [15, base_w - 15]) translate([x, y, -1]) hull() { hole(6.5, base_t + 2); translate([0, 8, 0]) hole(6.5, base_t + 2); }
    // alléger
    for (x = [50, 120, 190]) for (y = [35, 105]) translate([x, y, -1]) hole(18, base_t + 2);
  }
}

module montant() {
  difference() {
    union() {
      cube([tower_w, tower_t, tower_h]);
      translate([0, -6, 0]) cube([tower_w, tower_t + 12, 10]);               // semelle
    }
    translate([tower_w/2, -1, axle_z]) rotate([-90, 0, 0]) hole(axle_d, tower_t + 2);
    for (x = [tower_w/2 - 15, tower_w/2 + 15]) translate([x, tower_t/2, -1]) hole(4.3, 12);
    // bague de palier imprimée en option : logement 8 mm
    translate([tower_w/2, tower_t - 2, axle_z]) rotate([-90, 0, 0]) hole(8.2, 3);
  }
}

module bras() {
  L = arm_up + arm_down;
  difference() {
    union() {
      cube([arm_sec, arm_sec, L]);
      translate([arm_sec, -plate/2 + arm_sec/2, L - plate]) cube([plate_t, plate, plate]);      // plateau moteur vertical, moteur vers +x
    }
    translate([arm_wall, arm_wall, -1]) cube([arm_sec - 2*arm_wall, arm_sec - 2*arm_wall, L - plate - 10]); // creux
    translate([-1, arm_sec/2, arm_down]) rotate([0, 90, 0]) hole(axle_d, arm_sec + 2);          // axe
    // trames moteur sur le plateau : 12x12, 16x16, 19x19, 25x25 (M3) + passage d'axe 8 mm
    for (p = [12, 16, 19, 25]) for (sx = [-1, 1]) for (sy = [-1, 1])
      translate([arm_sec - 1, arm_sec/2 + sx*p/2, L - plate/2 + sy*p/2]) rotate([0, 90, 0]) hole(3.2, plate_t + 2);
    translate([arm_sec - 1, arm_sec/2, L - plate/2]) rotate([0, 90, 0]) hole(8.5, plate_t + 2);
    // vis de contact M4 en bas, vers -x (vers la cellule)
    translate([-1, arm_sec/2, 8]) rotate([0, 90, 0]) hole(3.3, arm_sec + 2);                   // à tarauder M4
  }
}

module poteau_cellule() {
  h = arm_down + cell_l + 10 - 8;   // affleure le haut de la cellule
  difference() {
    union() { cube([16, 40, h]); translate([-10, 0, 0]) cube([36, 40, 8]); }
    // 2 vis M4 de l'extrémité fixe de la cellule (entraxe 15 mm, standard des cellules 80 mm)
    for (z = [h - 10, h - 25]) translate([-1, 20, z]) rotate([0, 90, 0]) hole(4.3, 18);
    for (y = [8, 32]) translate([-4, y, -1]) hole(4.3, 10);
  }
}

module bague_axe() difference() { cylinder(d = 8, h = 8, $fn = 48); translate([0, 0, -1]) cylinder(d = 4.2, h = 10, $fn = 32); }

module assemblage() {
  color("silver") base();
  for (s = [-1, 1]) translate([base_l/2 - tower_w/2, base_w/2 + s*(arm_sec/2 + gap) + (s < 0 ? -tower_t : 0), base_t]) color("silver") montant();
  translate([base_l/2 - arm_sec/2, base_w/2 - arm_sec/2, base_t + axle_z - arm_down]) color("steelblue") bras();
  translate([base_l/2 + cell_post_x - 8 - cell_h, base_w/2 - 20, base_t]) color("silver") poteau_cellule();
  translate([base_l/2 + cell_post_x - cell_h/2, base_w/2 - cell_w/2, base_t + 10]) color("firebrick") cube([cell_h, cell_w, cell_l]);
  translate([base_l/2 + arm_sec/2 + plate_t, base_w/2, base_t + axle_z + arm_up - plate/2]) rotate([0, 90, 0]) color("dimgray") cylinder(d = 31, h = 30, $fn = 48);
  translate([base_l/2 + arm_sec/2 + plate_t + 36, base_w/2, base_t + axle_z + arm_up - plate/2]) rotate([0, 90, 0]) color("gray", 0.5) cylinder(d = 254, h = 2, $fn = 96);
}

if (PART == "assemblage") assemblage();
else if (PART == "base") base();
else if (PART == "montant") montant();
else if (PART == "bras") rotate([0, -90, 0]) bras();          // couché pour l'impression
else if (PART == "plateau_moteur") bras();
else if (PART == "poteau_cellule") poteau_cellule();
else if (PART == "bague_axe") bague_axe();
