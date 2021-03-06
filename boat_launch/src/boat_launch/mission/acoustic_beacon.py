from __future__ import division

import math
import traceback
from txros import util
import random

# we will move the boat based on the info in the processed messages
from hydrophones.msg import ProcessedPing
# we will also subscribe to a simple message that tells us the freq to look fo
from std_msgs.msg import Float64
# we will publish the pingers lat long with a nav_msgs/Odometry message like the /absodom topic. the lat long is under pose.pose.position
from geometry_msgs.msg import Point

import boat_scripting

#SPP the gps methods is exported here only fur testing currently
from rawgps_common import gps

#NOTE: run missions does ros init node for us
    

@util.cancellableInlineCallbacks
def _send_result(ci, course, lat, lon):
    colors = set(['yellow', 'blue', 'black', 'green', 'red'])
    while colors:
        color = random.choice(list(colors))
        try:
            res = yield ci.send_pinger_answer(course, color, lat, lon)
            print res
            if res: return
            if not res: colors.remove(color)
        except:
            traceback.print_exc()
        yield util.sleep(5)

@util.cancellableInlineCallbacks
def main(nh, ci, course, freq):
    freq=27440
    boat = yield boat_scripting.get_boat(nh)
    #float_df = boat.float()
    #yield boat.retract_hydrophone() # why was this here? it shouldn't need this, the hydrophones should be up on start
    
    print "Starting ping mission"
    print "Deploying Hydrophone"
    yield boat.deploy_hydrophone()
    print "Hydrophone Deployed"
    try:
        yield util.wrap_timeout(boat.hydrophone_align(freq), 60*2)
    except Exception:
        traceback.print_exc()
    print "Finished ping mission"
    # Note: /absodom is Earth-Centered,Earth-Fixed (ECEF), so This means that ECEF rotates with the earth and a point fixed on the surface of the earth do not change.
    # See: http://en.wikipedia.org/wiki/ECEF
    msg = yield boat.get_gps_odom()
    temp = gps.latlongheight_from_ecef([msg.pose.pose.position.x,msg.pose.pose.position.y,msg.pose.pose.position.z])
    print "latitude: ", temp[0]," longitude: ", temp[1]
    _send_result(ci, course, math.degrees(temp[0]), math.degrees(temp[1])) # async XXX
    #float_df.cancel()
    print "Retracting Hydrophone"
    yield boat.retract_hydrophone()
    print "Hydrophone Retracted"
    print "Done"
