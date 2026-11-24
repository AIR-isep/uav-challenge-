// Drone principal — quadriplan VTOL 4 moteurs (2 basculants) — Dassault UAV Challenge, équipe ISEP
// OpenSCAD >= 2021. PART sélectionne la pièce à rendre/exporter (Customizer ou -D PART="troncon_aile").
// Dimensions issues du dimensionnement v3 (scripts/dimensionnement_v3.py) : envergure 1710, corde 244.
// Export STEP : ouvrir ce fichier dans FreeCAD (atelier OpenSCAD, nécessite le binaire openscad), puis Fichier > Exporter > STEP.
// Impression : tronçons d'aile couchés sur le plateau (285 mm < 320 mm), LW-PLA paroi unique ; nacelles, paliers, cadres en PETG-CF.

PART = "assemblage";  // ["assemblage","troncon_aile","nervure","nacelle_tilt","nacelle_fixe","palier_tilt","cadre_fuselage","bras_servo_tilt","loquet_soute","patin"]
TILT = 0;             // [0:90] angle des nacelles avant pour l'assemblage (0 = stationnaire, 90 = croisière)

// ---- dimensions principales (mm)
span = 1710; chord = 244; chord_tip = 0.85 * chord; seg = 285;      // 3 tronçons de 285 par demi-aile
x_le = -180; z_wing = 120;                                            // bord d'attaque 180 mm derrière le nez, aile haute
spar_d = 14; spar_x = 0.30;  rear_spar_d = 8; rear_spar_x = 0.70;     // longerons : positions en fraction de corde
boom_d = 14; boom_y = 320; boom_x0 = -1130; boom_x1 = 90; z_boom = z_wing - 60;
motor_front_x = 60; motor_rear_x = -580; prop_d = 254;
fus_len = 420; fus_w = 140; fus_h = 120;
tail_x = -1060; tail_span = 500; tail_chord = 130; fin_h = 180; fin_chord = 120;
skin = 0.6; wall_cf = 2.0;

// ---- profil NACA 4412 (polygone fermé, corde 1, origine au bord d'attaque, extrados vers +y)
function naca_yt(x, t) = 5*t*(0.2969*sqrt(x) - 0.1260*x - 0.3516*x*x + 0.2843*x*x*x - 0.1036*x*x*x*x);
function naca_yc(x, m, p) = x < p ? m/(p*p)*(2*p*x - x*x) : m/((1-p)*(1-p))*((1-2*p) + 2*p*x - x*x);
function naca_pts(m, p, t, n) = concat(
  [for (i = [n:-1:0]) let(x = i/n, yt = naca_yt(x, t), yc = naca_yc(x, m, p)) [x, yc + yt]],
  [for (i = [1:n-1]) let(x = i/n, yt = naca_yt(x, t), yc = naca_yc(x, m, p)) [x, yc - yt]]);
module airfoil(c, code = [0.04, 0.4, 0.12], n = 40) polygon([for (q = naca_pts(code[0], code[1], code[2], n)) [q[0]*c, q[1]*c]]);

// ---- tronçon d'aile : coque mince + logements des longerons ; nervures aux deux bouts
module troncon_aile(c0 = chord, c1 = chord, L = seg, with_ribs = true) {
  difference() {
    linear_extrude(height = L, scale = c1/c0) airfoil(c0);
    translate([0, 0, -1]) linear_extrude(height = L + 2, scale = c1/c0) offset(delta = -skin) airfoil(c0);
  }
  // nervures d'extrémité percées pour les longerons
  if (with_ribs) for (z = [0, L - 1.6]) translate([0, 0, z]) difference() {
    linear_extrude(height = 1.6) airfoil(c0);
    translate([spar_x*c0, 0.03*c0, -1]) cylinder(d = spar_d + 0.3, h = 4, $fn = 48);
    translate([rear_spar_x*c0, 0.02*c0, -1]) cylinder(d = rear_spar_d + 0.3, h = 4, $fn = 32);
    translate([0.5*c0, 0.01*c0, -1]) cylinder(d = 0.35*c0, h = 4, $fn = 48);   // allègement
  }
}
module nervure(c = chord) difference() {
  linear_extrude(height = 1.6) airfoil(c);
  translate([spar_x*c, 0.03*c, -1]) cylinder(d = spar_d + 0.3, h = 4, $fn = 48);
  translate([rear_spar_x*c, 0.02*c, -1]) cylinder(d = rear_spar_d + 0.3, h = 4, $fn = 32);
  translate([0.5*c, 0.01*c, -1]) cylinder(d = 0.35*c, h = 4, $fn = 48);
}

// ---- nacelle basculante : manchon sur la poutre + palier de tilt (axe tube carbone 8 mm) + plateau moteur 25x25 / 19x19
module nacelle_tilt() {
  difference() {
    union() {
      rotate([0, 90, 0]) cylinder(d = boom_d + 2*wall_cf + 2, h = 70, center = true, $fn = 48);    // manchon poutre
      translate([0, 0, 18]) cylinder(d = 36, h = 30, $fn = 48);                                     // corps
      translate([0, 0, 46]) cylinder(d = 34, h = 5, $fn = 48);                                      // plateau moteur
    }
    rotate([0, 90, 0]) cylinder(d = boom_d + 0.3, h = 80, center = true, $fn = 48);                  // passage poutre
    rotate([90, 0, 0]) cylinder(d = 8.2, h = 60, center = true, $fn = 32);                           // axe de basculement (tube 8 mm)
    for (p = [19, 25]) for (sx = [-1, 1]) for (sy = [-1, 1]) translate([sx*p/2, sy*p/2, 40]) cylinder(d = 3.2, h = 20, $fn = 24);
    translate([0, 0, 40]) cylinder(d = 10, h = 20, $fn = 24);
    translate([0, 0, 10]) cube([20, 60, 20], center = true);                                         // dégagement bielle
  }
}
module nacelle_fixe() difference() {
  union() {
    rotate([0, 90, 0]) cylinder(d = boom_d + 2*wall_cf + 2, h = 70, center = true, $fn = 48);
    translate([0, 0, 10]) cylinder(d1 = 30, d2 = 34, h = 30, $fn = 48);
    translate([0, 0, 40]) cylinder(d = 34, h = 5, $fn = 48);
  }
  rotate([0, 90, 0]) cylinder(d = boom_d + 0.3, h = 80, center = true, $fn = 48);
  for (p = [19, 25]) for (sx = [-1, 1]) for (sy = [-1, 1]) translate([sx*p/2, sy*p/2, 35]) cylinder(d = 3.2, h = 20, $fn = 24);
  translate([0, 0, 35]) cylinder(d = 10, h = 20, $fn = 24);
  for (s = [-1, 1]) translate([s*25, 0, 0]) rotate([90, 0, 0]) cylinder(d = 3.2, h = 40, center = true, $fn = 20);   // serrage sur poutre
}
// palier de tilt : chape fixe sur la poutre, recevant l'axe 8 mm de la nacelle
module palier_tilt() difference() {
  union() { rotate([0, 90, 0]) cylinder(d = boom_d + 2*wall_cf + 2, h = 30, center = true, $fn = 48); translate([-15, -22, 0]) cube([30, 44, 14]); }
  rotate([0, 90, 0]) cylinder(d = boom_d + 0.3, h = 40, center = true, $fn = 48);
  translate([0, 0, 14]) rotate([90, 0, 0]) cylinder(d = 8.2, h = 60, center = true, $fn = 32);
  for (s = [-1, 1]) translate([0, s*16, 10]) rotate([90, 0, 0]) cylinder(d = 3.2, h = 12, center = true, $fn = 20);
}
module bras_servo_tilt() difference() {       // palonnier reliant le servo 30 kg à la nacelle (bielle à rotules M3)
  hull() { cylinder(d = 14, h = 4, $fn = 32); translate([25, 0, 0]) cylinder(d = 8, h = 4, $fn = 24); }
  translate([0, 0, -1]) cylinder(d = 6, h = 6, $fn = 24); translate([25, 0, -1]) cylinder(d = 3.2, h = 6, $fn = 20);
}
module cadre_fuselage(w = fus_w, h = fus_h) difference() {
  scale([w/h, 1, 1]) cylinder(d = h, h = 6, $fn = 64);
  translate([0, 0, -1]) scale([(w - 2*6)/(h - 2*6), 1, 1]) cylinder(d = h - 12, h = 8, $fn = 64);
}
module loquet_soute() difference() {           // loquet rotatif commandé par micro-servo : retient capsule et berceau du second drone
  union() { cylinder(d = 10, h = 30, $fn = 32); translate([0, -4, 20]) cube([22, 8, 6]); }
  translate([0, 0, -1]) cylinder(d = 5.9, h = 12, $fn = 24);
}
module patin() difference() {
  hull() { translate([-20, -6, 0]) cube([40, 12, 4]); translate([-14, -6, -86]) cube([28, 12, 4]); }
  rotate([0, 90, 0]) translate([-boom_d/2 - 2, 0, 0]) cylinder(d = boom_d + 0.3, h = 60, center = true, $fn = 48);
}

// ---- assemblage de visualisation
module demi_aile(s) translate([x_le, 0, z_wing]) mirror([0, s < 0 ? 1 : 0, 0])
  for (i = [0:2]) let(f0 = i/3, f1 = (i+1)/3, c0 = chord + (chord_tip - chord)*f0, c1 = chord + (chord_tip - chord)*f1)
    translate([0, i*seg, 0]) rotate([90, 0, 180]) translate([0, 0, 0]) color("steelblue") troncon_aile(c0, c1, seg, false);
module fuselage() color("silver") hull() {
  translate([-30, 0, 0]) scale([1, 0.65, 0.55]) sphere(d = 70, $fn = 48);
  translate([-180, 0, 0]) scale([1, fus_w/fus_h, 1]) sphere(d = fus_h, $fn = 48);
  translate([-300, 0, 0]) scale([1, 1.15, 1]) sphere(d = 110, $fn = 48);
  translate([-fus_len, 0, 0]) sphere(d = 24, $fn = 32);
}
module poutre(s) translate([boom_x0, s*boom_y, z_boom]) rotate([0, 90, 0]) color("black") cylinder(d = boom_d, h = boom_x1 - boom_x0, $fn = 32);
module moteur_helice(tilt) rotate([0, tilt, 0]) { color("dimgray") translate([0, 0, 45]) cylinder(d = 32, h = 28, $fn = 32); color("firebrick", 0.7) translate([0, 0, 76]) cylinder(d = prop_d, h = 2, $fn = 64); }
module nacelle_assemblee(x, s, tilt, is_tilt) translate([x, s*boom_y, z_boom]) { if (is_tilt) { color("gray") nacelle_tilt(); moteur_helice(tilt); } else { color("gray") nacelle_fixe(); moteur_helice(0); } }
module empennage() {
  translate([tail_x, 0, z_boom]) rotate([90, 0, 180]) color("steelblue") linear_extrude(height = tail_span, center = true) airfoil(tail_chord, [0, 0, 0.10]);
  for (s = [-1, 1]) translate([tail_x, s*boom_y, z_boom]) rotate([0, 0, 180]) color("steelblue") linear_extrude(height = fin_h, scale = 0.7) airfoil(fin_chord, [0, 0, 0.10]);
}
module assemblage() {
  demi_aile(1); demi_aile(-1); fuselage(); poutre(1); poutre(-1); empennage();
  for (s = [-1, 1]) { nacelle_assemblee(motor_front_x, s, TILT, true); nacelle_assemblee(motor_rear_x, s, 0, false);
    for (x = [motor_front_x, motor_rear_x]) translate([x, s*boom_y, z_boom - boom_d/2]) color("gray") patin(); }
  translate([-260, 0, -62]) color("silver", 0.6) cube([220, 110, 4], center = true);   // trappes de soute
}

if (PART == "assemblage") assemblage();
else if (PART == "troncon_aile") troncon_aile();
else if (PART == "nervure") nervure();
else if (PART == "nacelle_tilt") nacelle_tilt();
else if (PART == "nacelle_fixe") nacelle_fixe();
else if (PART == "palier_tilt") palier_tilt();
else if (PART == "cadre_fuselage") cadre_fuselage();
else if (PART == "bras_servo_tilt") bras_servo_tilt();
else if (PART == "loquet_soute") loquet_soute();
else if (PART == "patin") patin();
