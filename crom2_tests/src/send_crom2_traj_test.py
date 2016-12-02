#! /usr/bin/env python
'''
	Program to send and test the trajectories 

'''


import roslib; roslib.load_manifest('robotnik_trajectory_control')
import rospy
import actionlib
import time

from actionlib_msgs.msg import *
from trajectory_msgs.msg import *

from control_msgs.msg import *

if __name__ == '__main__':
	rospy.init_node('follow_trajectory_real_test')
	rospy.loginfo('waiting for server')

	client = actionlib.SimpleActionClient('/rt_traj_exe/follow_joint_trajectory', FollowJointTrajectoryAction)
	client.wait_for_server()
	rospy.loginfo('server found')
	option = 9
	
	goal = FollowJointTrajectoryGoal()
	goal.trajectory.header.stamp = rospy.Time.now()
	goal.trajectory.joint_names = ['waist_joint', 'head_pan_joint', 'head_tilt_joint']
	tpoint1 = JointTrajectoryPoint()
	tpoint1.positions = [-0.5, 0.0, 0.5]
	#tpoint1.velocities = [0.1, 0.1, 0.1, 0.1]
	tpoint1.velocities = [0.3,0.3,0.35]
	tpoint1.accelerations = [0.05, 0.1, 0.05]
	tpoint1.time_from_start = rospy.Duration.from_sec(5.0)
	
	tpoint2 = JointTrajectoryPoint()
	tpoint2.positions = [1.5, 0.31, 0.32]
	tpoint2.velocities = [0.1, 0.05, 0.05]
	tpoint2.accelerations = [0.05, 0.11, 0.12]
	tpoint2.time_from_start = rospy.Duration.from_sec(5.0)
	
	
	goal.trajectory.points = [tpoint1, tpoint2]
	
	
	rospy.loginfo('OPTION 1: sending trajectory 1')
	# Fill in the goal here
	client.send_goal(goal)
	rospy.loginfo('waiting for result')
	while not client.wait_for_result(rospy.Duration.from_sec(5.0)) and not rospy.is_shutdown():
		rospy.loginfo('waiting for result. state = %s'%client.get_state())
	
	
		
	print 'Result is %s'%client.get_result()

	

	exit()
