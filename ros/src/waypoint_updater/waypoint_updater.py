#!/usr/bin/env python
import numpy as np
from scipy.spatial import KDTree  #kp - for helping in closest waypoint computation
import rospy
from geometry_msgs.msg import PoseStamped
from styx_msgs.msg import Lane, Waypoint

import math

'''
This node will publish waypoints from the car's current position to some `x` distance ahead.

As mentioned in the doc, you should ideally first implement a version which does not care
about traffic lights or obstacles.

Once you have created dbw_node, you will update this node to use the status of traffic lights too.

Please note that our simulator also provides the exact location of traffic lights and their
current status in `/vehicle/traffic_lights` message. You can use this message to build this node
as well as to verify your TL classifier.

TODO (for Yousuf and Aaron): Stopline location for each traffic light.
'''

LOOKAHEAD_WPS = 200 # Number of waypoints we will publish. You can change this number


class WaypointUpdater(object):
	def __init__(self):
		rospy.init_node('waypoint_updater')

		rospy.Subscriber('/current_pose', PoseStamped, self.pose_cb)
		rospy.Subscriber('/base_waypoints', Lane, self.waypoints_cb)

        # TODO: Add a subscriber for /traffic_waypoint and /obstacle_waypoint below

		self.final_waypoints_pub = rospy.Publisher('final_waypoints', Lane, queue_size=1)

        # TODO: Add other member variables you need below
		self.pose = None
		self.base_waypoints = None
		self.waypoints_2d = None
		self.waypoint_tree = None

		self.loop()

        #rospy.spin()

	def loop(self):
		rate = rospy.Rate(50)  # as per classes & Q&A session [30 - 50] range
		while not rospy.is_shutdown():
			if self.pose and self.base_waypoints and self.waypoint_tree:
				# retrive closest way_point ahead
				closest_wpt_idx = self.get_closest_waypoint_id()
				self.publish_waypoints(closest_wpt_idx)
			rate.sleep()
	
	def get_closest_waypoint_id(self):
		x = self.pose.pose.position.x
		y = self.pose.pose.position.y
		
		closest_idx = self.waypoint_tree.query([x,y], 1)[1]
		_,  all_i = self.waypoint_tree.query([(x, y)])
		exp_close_index = all_i[0]
		
	

		#determine whether closest point is ahead of ego vehicle or not
		closest_pt = self.waypoints_2d[closest_idx]
		prev_pt = self.waypoints_2d [closest_idx - 1]
		
		# relevant hyper plane calculations
		closest_v = np.array(closest_pt)
		prev_v	= np.array(prev_pt)
		pos_v = np.array([x, y])

		rospy.loginfo("WU: closest_idx {}, exp {}, position {} ".format(closest_idx,  exp_close_index, pos_v))
		dot_product = np.dot (closest_v-prev_v, pos_v-closest_v)
		
		
		if (dot_product > 0.): # the closest point was behind the ego vehicle; take the next one ahead.
			closest_idx = (closest_idx + 1) % len(self.waypoints_2d)  
		rospy.loginfo("WaypointUpdater: closest_idx {} ".format(closest_idx))
		return (closest_idx)

	def publish_waypoints (self, closest_idx):
		lane = Lane()
		lane.header = self.base_waypoints.header
		lane.waypoints = self.base_waypoints.waypoints[closest_idx:closest_idx+LOOKAHEAD_WPS]
		
		rospy.loginfo("WU: closest index {}, ofinal wpt len {},  base wpt len {} ".format(closest_idx, len(lane.waypoints),  len(self.base_waypoints.waypoints)))
		self.final_waypoints_pub.publish(lane)

	def pose_cb(self, msg):
        # TODO: Implement
		self.pose = msg
		#if self.pose and self.base_waypoints and self.waypoint_tree:
			# retrive closest way_point ahead
			#closest_wpt_idx = self.get_closest_waypoint_id()
			#self.publish_waypoints(closest_wpt_idx)

	def waypoints_cb(self, waypoints):
        # TODO: Implement
		self.base_waypoints = waypoints
		if not self.waypoints_2d:  #not initialized yet
			self.waypoints_2d = [ [wpt.pose.pose.position.x, wpt.pose.pose.position.y] for wpt in waypoints.waypoints]
			self.waypoint_tree = KDTree (self.waypoints_2d)

	def traffic_cb(self, msg):
        # TODO: Callback for /traffic_waypoint message. Implement
		pass

	def obstacle_cb(self, msg):
        # TODO: Callback for /obstacle_waypoint message. We will implement it later
		pass

	def get_waypoint_velocity(self, waypoint):
		return waypoint.twist.twist.linear.x

	def set_waypoint_velocity(self, waypoints, waypoint, velocity):
		waypoints[waypoint].twist.twist.linear.x = velocity

	def distance(self, waypoints, wp1, wp2):
		dist = 0
		dl = lambda a, b: math.sqrt((a.x-b.x)**2 + (a.y-b.y)**2  + (a.z-b.z)**2)
		for i in range(wp1, wp2+1):
			dist += dl(waypoints[wp1].pose.pose.position, waypoints[i].pose.pose.position)
			wp1 = i
		return dist


if __name__ == '__main__':
    try:
        WaypointUpdater()
    except rospy.ROSInterruptException:
        rospy.logerr('Could not start waypoint updater node.')
