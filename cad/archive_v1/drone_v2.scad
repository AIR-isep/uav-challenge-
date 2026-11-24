// ============================================================================
// drone_v2.scad — pièces IMPRIMABLES du drone principal v2 (forme cargo)
// Dassault UAV Challenge 2026-27, équipe AIR / ISEP — 5 novembre 2026
// Cotes maîtres : prototype_v1/cao_v2/v2_dimensions.json (envergure 1820, corde 260,
// entraxe rotors 660x660, poutres carénées sur tube Ø14, axe de basculement tube Ø8).
// Chaque pièce est modélisée DANS SON ORIENTATION D'IMPRESSION (z = axe machine).
// Rendu :  openscad -D 'PART="nacelle"' -o nacelle.stl drone_v2.scad
// ============================================================================

PART = "assemblage";  // ["assemblage","ecorche","fuselage_nez","fuselage_soute","fuselage_arriere","fuselage_queue","trappe_dorsale","troncon_centre","troncon_courant","saumon","nervure","nacelle","embout_poutre","bras_servo","cadre_soute","cadre_plein","berceau_second_drone","support_pack","trappe_soute","loquet","support_lidar","peigne_calibration"]

// --- 1. PARAMÈTRES ----------------------------------------------------------
jeu        = 0.25;   // [mm] ajustement glissant H2D — recaler après le peigne
jeu_serre  = 0.10;   // [mm] ajustement serré
corde      = 260;    // [mm] corde d'aile
t_rel      = 0.12;   // épaisseur relative NACA 4412
peau       = 0.60;   // [mm] peau d'aile LW-PLA (paroi unique en vase)
nervure_e  = 1.6;    // [mm] épaisseur des nervures d'extrémité
long_spar_d  = 14;   // [mm] longeron principal (tube carbone 14x12) à 30 % corde
rear_spar_d  = 8;    // [mm] longeron arrière à 70 % corde
tube_poutre  = 14;   // [mm] tube des poutres
tube_axe     = 8;    // [mm] axe de basculement des nacelles
moteur_bc1   = 25;   // [mm] entraxe platine moteur 3115 (trous M3)
moteur_bc2   = 19;   // [mm] second entraxe
fus_w = 210; fus_h = 190;        // [mm] section max du fuselage
soute_w = 170; soute_h = 120;    // [mm] soute interne
pack_l = 130; pack_w = 46; pack_h = 72;  // [mm] 6S2P Samsung 50S (2 rangées de 6) + gaine
sd_l = 162;                      // [mm] intérieur du berceau second drone 3,5" — À MESURER sur le kit réel
m3 = 3.2; m4 = 4.2;              // perçages vis
$fn = 64;
eps = 0.01;

// --- 2. COTES DÉRIVÉES ------------------------------------------------------
x_spar1 = 0.30 * corde;          // 78 mm du bord d'attaque
x_spar2 = 0.70 * corde;          // 182 mm
ep_aile = t_rel * corde;         // 31,2 mm d'épaisseur max
assert(peau >= 0.4, "peau trop fine");
assert(nervure_e >= 1.2, "nervure sous le mini FDM");

// --- 3. PROFILS 2D ----------------------------------------------------------
function naca_yt(x, t) = 5*t*(0.2969*sqrt(x) - 0.1260*x - 0.3516*x*x + 0.2843*x*x*x - 0.1036*x*x*x*x);
function naca_yc(x, m, p) = x < p ? m/(p*p)*(2*p*x - x*x) : m/((1-p)*(1-p))*((1-2*p) + 2*p*x - x*x);
function naca_pts(m, p, t, n) = concat(
  [for (i = [n:-1:0]) let(x = i/n) [x, naca_yc(x,m,p) + naca_yt(x,t)]],
  [for (i = [1:n-1]) let(x = i/n) [x, naca_yc(x,m,p) - naca_yt(x,t)]]);
module profil(c, n = 48) polygon([for (q = naca_pts(0.04, 0.4, t_rel, n)) [q[0]*c, q[1]*c]]);

// --- 4-7. PIÈCES -------------------------------------------------------------

// ---- nervure 2D commune : longerons + allègements oblongs contenus dans l'épaisseur
module allegements(c) {
  for (xc = [0.47, 0.60])
    translate([xc*c, naca_yc(xc, 0.04, 0.4)*c]) scale([2.3, 1]) circle(d = 0.042*c);
}
module rib2d(c) {
  difference() {
    profil(c);
    translate([0.30*c, 0.030*c]) circle(d = long_spar_d + 2*jeu + 0.1);
    translate([0.70*c, 0.015*c]) circle(d = rear_spar_d + 2*jeu + 0.1);
    allegements(c);
    translate([0.30*c + long_spar_d/2 + 4, 0.030*c]) circle(d = 2.5, $fn = 16);  // sortie de colle
  }
}
module nervure(c = corde, e = nervure_e) linear_extrude(e) rib2d(c);

// ---- tronçon d'aile : peau 0,6 + 2 nervures percées, imprimé debout (z = envergure)
module troncon(L, c0 = corde, c1 = corde) {
  union() {
    difference() {                                     // peau
      linear_extrude(L, scale = c1/c0, convexity = 6) profil(c0);
      translate([0,0,-eps]) linear_extrude(L + 2*eps, scale = c1/c0, convexity = 6)
        offset(delta = -peau) profil(c0);
    }
    linear_extrude(nervure_e) rib2d(c0);               // nervure basse
    translate([0, 0, L - nervure_e]) linear_extrude(nervure_e)
      scale([c1/c0, c1/c0]) rib2d(c0);                 // nervure haute (même fraction de corde)
  }
}
module troncon_centre()  troncon(330);
module troncon_courant() troncon(290);
module saumon() {                                      // dernier tronçon : corde réduite au bout
  union() {
    troncon(250, corde, 0.78*corde);
    translate([0,0,250]) difference() {                                   // bout arrondi CREUX (paroi ~1,5)
      linear_extrude(40, scale = 0.45, convexity = 4) offset(delta = -0.01) profil(0.78*corde);
      translate([0,0,-eps]) linear_extrude(38, scale = 0.45, convexity = 4) offset(delta = -1.5) profil(0.78*corde);
    }
  }
}

// ---- nacelle basculante (PETG-CF) : moyeu Ø8,2 + corps + platine moteur percée
nac_d = 38;        // diamètre du corps
nac_h = 30;        // hauteur corps entre moyeu et platine
moyeu_l = 30;      // largeur du moyeu (entre les joues de la chape : 32)
module nacelle() {
  difference() {
    union() {
      rotate([90,0,0]) cylinder(d = 14, h = moyeu_l, center = true);              // moyeu
      translate([0,0,5]) cylinder(d1 = nac_d - 8, d2 = nac_d, h = nac_h - 5);     // corps conique
      translate([0,0,nac_h]) cylinder(d = nac_d + 2, h = 5);                      // platine
      translate([12, -5, 5]) cube([10, 10, 14]);                                   // patte de bielle (ancrée dans le cône)
    }
    rotate([90,0,0]) cylinder(d = tube_axe + 2*jeu_serre, h = moyeu_l + 2*eps, center = true); // axe 8 serré (collé)
    for (p = [moteur_bc1, moteur_bc2], sx = [-1,1], sy = [-1,1])
      translate([sx*p/2, sy*p/2, nac_h - eps]) cylinder(d = m3, h = 6 + 2*eps, $fn = 24);
    translate([0,0,nac_h - eps]) cylinder(d = 10, h = 6 + 2*eps);                 // passage câbles/axe moteur
    translate([0,0,20]) rotate([90,0,0]) cylinder(d = 12, h = nac_d + 4, center = true);     // fenêtre câbles (au-dessus de la patte)
    translate([19,0,12]) rotate([90,0,0]) cylinder(d = m3, h = 14, center = true, $fn = 20);  // trou de bielle M3
  }
}

// ---- embout de poutre : manchon sur tube Ø14 + chape (fourche) pour l'axe Ø8
chape_gap = moyeu_l + 2;     // 32 entre joues
joue_e = 8;                  // épaisseur d'une joue
module embout_poutre() {
  manchon_l = 48;
  difference() {
    union() {
      cylinder(d = tube_poutre + 7, h = manchon_l);                               // manchon (imprimé debout)
      translate([0,0,manchon_l - eps]) cylinder(d1 = tube_poutre + 7, d2 = chape_gap + 2*joue_e, h = 16);
      for (s = [-1,1]) translate([-14, (s < 0 ? -chape_gap/2 - joue_e : chape_gap/2), manchon_l + 16 - eps])
        cube([28, joue_e, 22]);                                                   // joues de la chape
    }
    translate([0,0,-eps]) cylinder(d = tube_poutre + 2*jeu + 0.1, h = manchon_l + eps); // alésage tube + colle
    translate([7.2, 0, -eps]) cylinder(d = 2.5, h = manchon_l, $fn = 16);        // sortie de colle
    for (s = [-1,1]) translate([0, s*(tube_poutre/2 + 2), 14]) rotate([90,0,0])
      cylinder(d = m3, h = 8, center = true, $fn = 20);                           // 2 vis de serrage M3
    translate([0, 0, manchon_l + 16 + 11]) rotate([90,0,0])
      cylinder(d = tube_axe + 2*jeu, h = chape_gap + 2*joue_e + 2*eps, center = true); // palier Ø8,2 traversant
  }
}

// ---- palonnier servo -> bielle M3
module bras_servo() {
  difference() {
    hull() { cylinder(d = 14, h = 4); translate([25,0,0]) cylinder(d = 8, h = 4); }
    translate([0,0,-eps]) cylinder(d = 6, h = 4 + 2*eps);                          // sortie servo (à ajuster)
    translate([25,0,-eps]) cylinder(d = m3, h = 4 + 2*eps, $fn = 20);
  }
}

// ---- section de fuselage : RECTANGLE ARRONDI r45 (une ellipse 210x190 ne loge pas une
// soute de 170 de large : à y = -72 il ne reste que 137 mm). À reporter dans la CAO volumique.
module section_fuselage_2d() offset(r = 45) square([fus_w - 90, fus_h - 90], center = true);

module cadre_soute() {
  e = 6;
  fen_w = soute_w + 4; fen_h = soute_h - 4; fen_cy = -14;
  difference() {
    linear_extrude(e) difference() {
      section_fuselage_2d();
      translate([0, fen_cy]) offset(r = 14) square([fen_w - 28, fen_h - 28], center = true);
    }
    translate([-60, fus_h/2 - 16, -eps]) cube([120, 20, e + 2*eps]);        // ouverture dorsale (trappe)
    translate([-65, -fus_h/2 - 4, -eps]) cube([130, 11, e + 2*eps]);        // ouverture ventrale (largage)
    for (sx = [-1, 1], y = [fen_cy - fen_h/2 - 8, fen_cy + fen_h/2 + 8])    // 4 x M3 : rails du berceau
      translate([sx*(fen_w/2 - 10), y, -eps]) cylinder(d = m3, h = e + 2*eps, $fn = 20);
    for (sx = [-1, 1]) translate([sx*(fus_w/2 - 5), fen_cy, -eps])
      cylinder(d = m3, h = e + 2*eps, $fn = 20);                            // 2 x M3 : couture à la peau
  }
}
module cadre_plein() {           // cadre avant/arrière fermé (hors soute)
  e = 6; bande = 9;
  difference() {
    linear_extrude(e) difference() {
      section_fuselage_2d();
      offset(delta = -bande) section_fuselage_2d();
    }
    for (sx = [-1, 1], y = [-32, 32]) translate([sx*(fus_w/2 - 4.5), y, -eps])
      cylinder(d = m3, h = e + 2*eps, $fn = 20);                            // couture latérale
    for (sy = [-1, 1], x = [-32, 32]) translate([x, sy*(fus_h/2 - 4.5), -eps])
      cylinder(d = m3, h = e + 2*eps, $fn = 20);                            // couture haut/bas
  }
  translate([-20, -fus_h/2 + 7, 0]) cube([40, 4, e]);                       // semelle basse
}

// ---- berceau du second drone (dans la soute, glisse sur les rails)
module berceau_second_drone() {
  w = sd_l + 2*jeu + 5;   // intérieur 162,5 + parois
  difference() {
    union() {
      translate([-(w+5)/2, -(w+5)/2, 0]) cube([w+5, w+5, 2.4]);                   // fond
      for (s = [-1,1]) translate([(s < 0 ? -(w+5)/2 : (w+5)/2 - 2.5), -(w+5)/2, 0])
        cube([2.5, w+5, 24]);                                                     // 2 parois latérales
    }
    translate([0,0,-eps]) cylinder(d = 90, h = 3 + 2*eps);                        // allègement central
    for (sx = [-1,1], sy = [-1,1]) translate([sx*52, sy*52, -eps]) cylinder(d = 28, h = 3 + 2*eps);
    translate([-w/2 - 4, -25, 10]) cube([4 + 8, 50, 20]);                         // passage de doigt
    for (s = [-1,1]) translate([s*60, (w+5)/2 - 10, -eps]) cylinder(d = m3, h = 4, $fn = 20); // vis loquet
  }
}

// ---- support du pack 6S2P : U à sangles, coulisse sur le plancher avant
module support_pack() {
  wall = 2.5; base_l = pack_l + 2*wall + 2*jeu; base_w = pack_w + 2*wall + 2*jeu;
  difference() {
    union() {
      translate([-base_l/2, -base_w/2, 0]) cube([base_l, base_w, 2.4]);
      for (s = [-1,1]) translate([-base_l/2, s*(base_w/2) - (s>0?wall:0), 0]) cube([base_l, wall, 30]);
      for (s = [-1,1]) translate([s*(base_l/2) - (s>0?wall:0), -base_w/2, 0]) cube([wall, base_w, 16]);
    }
    for (x = [-base_l/4, base_l/4], s = [-1,1])                                   // 4 fentes de sangle 12x3
      translate([x - 6, s*(base_w/2 + 1) - 2, -eps]) cube([12, 4, 3.5]);
    translate([0,0,-eps]) cylinder(d = 40, h = 3 + 2*eps);                        // allègement
    for (x = [-base_l/2 + 8, base_l/2 - 8]) translate([x, 0, -eps]) cylinder(d = m4, h = 3 + 2*eps, $fn = 20); // M4 plancher
  }
}

// ---- trappe de soute + loquet quart de tour
module trappe_soute() {
  difference() {
    union() {
      translate([-140, -75, 0]) cube([280, 150, 2.4]);                            // panneau
      difference() {                                                              // lèvre périphérique de recouvrement
        translate([-136, -71, 2.4 - eps]) cube([272, 142, 2]);
        translate([-130, -65, 2.4 - 2*eps]) cube([260, 130, 2 + 4*eps]);
      }
    }
    for (s = [-1,1]) translate([s*120, 0, -eps]) cylinder(d = 10.6, h = 8, $fn = 32); // passages des loquets
  }
}
module loquet() {                                       // quart de tour commandé par micro-servo
  difference() {
    union() { cylinder(d = 10, h = 26); translate([-2.5, -2.5 - 8, 20]) cube([5, 24, 6]); }
    translate([0,0,-eps]) cylinder(d = 5.9, h = 10, $fn = 24);                    // carré de 5,9 du palonnier
  }
}

// ---- support LiDAR RPLidar C1 (dos du nez)
module support_lidar() {
  difference() {
    union() {
      translate([-40, -40, 0]) cube([80, 80, 2.4]);                               // semelle (collée/vissée peau)
      cylinder(d = 57 + 2*jeu + 5, h = 10);                                       // bague
    }
    translate([0,0,2.4]) cylinder(d = 57 + 2*jeu, h = 10, $fn = 96);              // logement C1 Ø57 glissant
    translate([0,0,-eps]) cylinder(d = 40, h = 3 + 2*eps);                        // passage câble
    for (sx = [-1,1], sy = [-1,1]) translate([sx*34, sy*34, -eps]) cylinder(d = m3, h = 3, $fn = 20);
  }
}

// ---- peigne de calibration des jeux : alésages 8 et 14, fentes 0,10 à 0,40
module peigne_calibration() {
  difference() {
    translate([0,0,0]) cube([120, 34, 6]);
    for (i = [0:6]) translate([12 + i*16, 10, -eps]) cylinder(d = 8 + 0.05 + i*0.05, h = 7, $fn = 48);
    translate([12, 24, -eps]) cylinder(d = 14.1, h = 7, $fn = 64);
    translate([34, 24, -eps]) cylinder(d = 14.3, h = 7, $fn = 64);
    translate([56, 24, -eps]) cylinder(d = 14.5, h = 7, $fn = 64);
    for (i = [0:3]) translate([76 + i*10, 18, -eps]) cube([3 + 0, 12, 7]);        // doigts entre fentes
  }
}


// ============================================================================
// FUSELAGE : coque en 4 tronçons imprimables (debout, z machine = x avion)
// Section = rectangle arrondi r<=45 ; peau 0,9 ; collerette de collage à l'arrière de chaque tronçon.
// Stations (x avion, largeur, hauteur, centre z) :
FUS_ST = [[0,10,10,5],[-25,70,74,3],[-60,124,128,1],[-110,170,164,0],[-180,210,190,0],
          [-460,210,190,0],[-560,196,180,2],[-650,160,152,16],[-740,112,108,36],
          [-830,64,64,56],[-885,40,40,66],[-925,14,14,74]];
peau_fus = 0.9;      // [mm] peau du fuselage (LW-PLA, 2 périmètres fins ou vase renforcé)
function fr(w,h) = min(45, w/2 - 0.6, h/2 - 0.6);
module fus_sect2d(w, h) offset(r = fr(w,h)) square([h - 2*fr(w,h), w - 2*fr(w,h)], center = true);
module fus_station(st, retrait = 0, dx = 0)
  translate([st[0] + dx, 0, st[3]]) rotate([0, 90, 0]) linear_extrude(0.4, center = true)
    offset(delta = -retrait) fus_sect2d(st[1], st[2]);
module fus_coque(i0, i1) {        // coque entre les stations i0..i1 (indices dans FUS_ST)
  difference() {
    for (i = [i0 : i1 - 1]) hull() { fus_station(FUS_ST[i]); fus_station(FUS_ST[i+1]); }
    for (i = [max(i0,1) : i1 - 1]) hull() {
      fus_station(FUS_ST[i], peau_fus, (i == max(i0,1)) ?  2 : 0);
      fus_station(FUS_ST[i+1], peau_fus, (i == i1 - 1) ? -2 : 0);
    }
  }
}
module collerette(i)              // bague de collage au plan de joint de la station i
  difference() {
    hull() { fus_station(FUS_ST[i], peau_fus + jeu, -10); fus_station(FUS_ST[i], peau_fus + jeu, 10); }
    hull() { fus_station(FUS_ST[i], peau_fus + jeu + 1.6, -11); fus_station(FUS_ST[i], peau_fus + jeu + 1.6, 11); }
  }

module fuselage_nez() difference() {       // x 0 -> -180 : LiDAR dessus, caméra dessous
  union() { fus_coque(0, 4); collerette(4); }
  translate([-95, 0, 60]) cylinder(d = 42, h = 60);                      // passage câble LiDAR (dessus)
  translate([-55, 0, -120]) cylinder(d = 22, h = 80);                    // fenêtre caméra (dessous)
  for (sx = [-1,1], sy = [-1,1]) translate([-95 + sx*34, sy*34, 60]) cylinder(d = m3, h = 60, $fn = 20);
}
module fuselage_soute() difference() {     // x -180 -> -460 : ouvertures dorsale et ventrale
  union() { fus_coque(4, 5); collerette(5); }
  translate([-440, -60, 55]) cube([240, 120, 60]);                       // ouverture dorsale 240 x 120
  translate([-457, -71.5, -130]) cube([272, 143, 60]);                   // ouverture ventrale 272 x 143
  for (s = [-1,1]) translate([-320 + s*120, 0, -130]) cylinder(d = 10.6, h = 50, $fn = 32); // axes loquets
}
module fuselage_arriere() union() { fus_coque(5, 7); collerette(7); }    // x -460 -> -650
module fuselage_queue()  fus_coque(7, 11);                               // x -650 -> -925

module trappe_dorsale() difference() {     // panneau dorsal vissé 250 x 130
  union() {
    translate([-125, -65, 0]) cube([250, 130, 2.4]);
    difference() {
      translate([-121, -61, 2.4 - eps]) cube([242, 122, 2]);
      translate([-115, -55, 2.4 - 2*eps]) cube([230, 110, 2 + 4*eps]);
    }
  }
  for (sx = [-1,1], sy = [-1,1]) translate([sx*115, sy*55, -eps]) cylinder(d = m3, h = 6, $fn = 20);
}

// ============================================================================
// ASSEMBLAGE : repère avion (x avant, y gauche, z haut), aile à z = +105
Z_AILE = 105; Z_POUTRE = 67; Y_POUTRE = 330;
module aile_droite()              // demi-aile y <= 0 ... non : rotate(90) envoie l'envergure vers -y
  translate([-200, 0, Z_AILE]) mirror([1, 0, 0]) rotate([90, 0, 0]) union() {
    troncon(330);
    translate([0, 0, 330]) troncon(290);
    translate([0, 0, 620]) saumon();
  }
module poutre_assemblee(side) {
  translate([0, side*Y_POUTRE, Z_POUTRE]) {
    rotate([0, 90, 0]) translate([0, 0, -860]) cylinder(d = tube_poutre, h = 985);       // tube carbone
    hull() { translate([80, 0, 0]) scale([40, 36, 29]) sphere(1, $fn = 24);
             translate([-560, 0, 0]) scale([40, 36, 29]) sphere(1, $fn = 24); }           // carénage
    hull() { translate([-560, 0, 0]) scale([30, 33, 26]) sphere(1, $fn = 24);
             translate([-830, 0, 0]) scale([20, 18, 15]) sphere(1, $fn = 24); }           // fuseau arrière
    for (xm = [MOT_F_AS, MOT_R_AS]) translate([xm, 0, 29]) {
      nacelle();                                                                          // nacelle (tilt 0)
      translate([0, 0, 40]) cylinder(d = 34, h = 26, $fn = 32);                           // moteur
      translate([0, 0, 68]) cylinder(d = 254, h = 2.5, $fn = 72);                         // disque hélice
    }
  }
}
MOT_F_AS = 45; MOT_R_AS = -615;
module vtail_demi() hull() {      // panneau y >= 0, plaque profilée de la poutre vers la queue
  translate([-862, Y_POUTRE, 70])  cube([165, 6, 10], center = true);
  translate([-967, 30, -135])      cube([125, 6, 8],  center = true);
}
module composants() {             // volumes des composants, pour l'écorché
  translate([-300, -pack_w/2, -80]) cube([pack_l, pack_w, pack_h]);                     // pack 6S2P (coulisse)
  translate([-130, -28, -60]) cube([90, 56, 26]);                                        // Pi 5 + BEC
  translate([-120, -18, -25]) cube([52, 36, 16]);                                        // FC + carte alim
  translate([-95, 0, 68]) cylinder(d = 56, h = 32);                                      // LiDAR (dos du nez)
  translate([-67, -13, -92]) cube([26, 26, 22]);                                         // caméra
  translate([-368, -81, -88]) cube([170, 162, 50]);                                      // second drone en soute
  translate([-440, -25, -85]) cube([60, 50, 25]);                                        // charge larguée 250 g
}
module cellule_complete(avec_composants = true) {
  union() {
    fuselage_nez(); fuselage_soute(); fuselage_arriere(); fuselage_queue();
    aile_droite(); mirror([0, 1, 0]) aile_droite();
    poutre_assemblee(1); poutre_assemblee(-1);
    vtail_demi(); mirror([0, 1, 0]) vtail_demi();
    if (avec_composants) composants();
  }
}
module assemblage() cellule_complete(false);
module ecorche() difference() {
  cellule_complete(true);
  translate([-1100, 0, -400]) cube([1500, 1000, 800]);                                   // coupe y > 0
}

// --- SÉLECTION ---------------------------------------------------------------
if (PART == "assemblage") assemblage();
else if (PART == "ecorche") ecorche();
else if (PART == "fuselage_nez") { fuselage_nez(); echo("bbox attendu : 180 x 210 x 190 + collerette"); }
else if (PART == "fuselage_soute") fuselage_soute();
else if (PART == "fuselage_arriere") fuselage_arriere();
else if (PART == "fuselage_queue") fuselage_queue();
else if (PART == "trappe_dorsale") trappe_dorsale();
else if (PART == "troncon_centre")  { troncon_centre();  echo("bbox attendu : 260 x 31 x 330"); }
else if (PART == "troncon_courant") { troncon_courant(); echo("bbox attendu : 260 x 31 x 290"); }
else if (PART == "saumon")     { saumon(); echo("bbox attendu : 260 x 31 x 290"); }
else if (PART == "nervure")    nervure();
else if (PART == "nacelle")    { nacelle(); echo("bbox attendu : 38 x 38 x 35, moyeu 30 de large"); }
else if (PART == "embout_poutre") { embout_poutre(); echo("bbox attendu : ~48 x 48 x 86"); }
else if (PART == "bras_servo") bras_servo();
else if (PART == "cadre_soute") cadre_soute();
else if (PART == "cadre_plein") cadre_plein();
else if (PART == "berceau_second_drone") berceau_second_drone();
else if (PART == "support_pack") support_pack();
else if (PART == "trappe_soute") trappe_soute();
else if (PART == "loquet")     loquet();
else if (PART == "support_lidar") support_lidar();
else if (PART == "peigne_calibration") peigne_calibration();
