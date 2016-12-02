#!/usr/bin/env python
"""
	Program that publishes the point of the detected crack, making the transformation between the desired frames
"""

import rospy 

from sensor_msgs.msg import JointState	
	
	
def main():

	rospy.init_node("crom2_test_torso_head")
	
	
	
	_node_name = rospy.get_name().replace('/','')
	
	t_sleep = 10.0
	waist_velocity = 0.2
	pan_velocity = 0.2
	tilt_velocity = 0.2
	
	joint_publisher = rospy.Publisher('/joint_commands', JointState, queue_size = 10)
	msg = JointState()
	
	waist_positions = [-1.57, 0.0, 1.57, 0.0]
	pan_positions = [-1.57, 0.0, 1.57, 0.0]
	tilt_positions = [-1, 0.0, 1, 0.0]
	
	number_of_points = len(waist_positions)
	position_index = 1
	
	msg.name = ['waist_joint', 'head_pan_joint', 'head_tilt_joint']
	#msg.position = [0.0, 0.0, 0.0]
	msg.position = [waist_positions[position_index], pan_positions[position_index], tilt_positions[position_index]]
	msg.velocity = [waist_velocity, pan_velocity, tilt_velocity]
	msg.effort = [0.0, 0.0, 0.0]

	rospy.loginfo("%s: starting", _node_name);
	
	init_time = rospy.Time.now()
	
	while not rospy.is_shutdown():
		t = (rospy.Time.now() - init_time).to_sec()
		
		print 'Moving to position %d [%lf,%lf,%lf]. Elapsed time = %d secs'%(position_index, waist_positions[position_index], pan_positions[position_index], tilt_positions[position_index], t)
		
		joint_publisher.publish(msg)
		
		msg.position = [waist_positions[position_index], pan_positions[position_index], tilt_positions[position_index]]
		position_index = (position_index + 1)%number_of_points
			
		try:
			rospy.sleep(t_sleep)
		except rospy.exceptions.ROSInterruptException:
				rospy.loginfo('%s::Main: ROS interrupt exception'%_node_name)
		
	
if __name__ == "__main__":
	main()
