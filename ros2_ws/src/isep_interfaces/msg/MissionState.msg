# État courant de la machine à états de mission (isep_mission)
std_msgs/Header header
string state        # IDLE, UPLOAD_MISSION, ARMING, MISSION, TARGET_FOUND, FAILSAFE, DONE, ABORTED
string detail       # explication lisible du dernier changement
